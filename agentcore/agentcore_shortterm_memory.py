import os
import time
from botocore.exceptions import ClientError
from bedrock_agentcore.memory import MemoryClient

print(" AgentCore Memory Memory \n")

# 初始化Memory客户端
print("1. 初始化 Memory 客户端...")
client = MemoryClient(region_name="us-west-2")
print(" Memory 客户端初始化成功")

actor_id = "agent-actor"
session_id = "agent-session"

def get_or_create_short_term_memory():
    memory_name = "AgentShortTermMemory"
    memory_id = None
    try:
        print("\n2. 创建短期记忆...")
        memory = client.create_memory_and_wait(
            name=memory_name,
            description="short-term memory for agent conversations",
            strategies=[],  # 短期记忆一般无策略
            event_expiry_days=90,  # 短期记忆有效期示例
        )
        memory_id = memory["id"]
        print(f" 短期记忆创建成功，ID: {memory_id}")
    except ClientError as e:
        print(f"创建短期记忆被取消")
        if e.response['Error']['Code'] == 'ValidationException' and "already exists" in str(e):
            print("短期记忆已存在，尝试获取已有 ID")
            memories = client.list_memories()
            memory_id = next((m['id'] for m in memories if m['id'].startswith(memory_name)), None)
            print(f"Short term Memory already exists. Using existing memory ID: {memory_id}")
            if memory_id:
                print(f"使用已有短期记忆 ID: {memory_id}")
            else:
                raise RuntimeError("找不到已存在的短期记忆 ID")
        else:
            raise e
    return memory_id

# 写入事件固定重试函数，最多尝试 max_attempts 次，每次遇限流等待1秒
def create_event_with_fixed_retry(client, memory_id, actor_id, session_id, messages, max_attempts=100):
    attempt = 0
    while attempt < max_attempts:
        print(f"尝试写入事件: 第 {attempt + 1} 次，内容: {messages}")
        try:
            client.create_event(
                memory_id=memory_id,
                actor_id=actor_id,
                session_id=session_id,
                messages=messages
            )
            print(f"写入事件成功（第{attempt+1}次尝试）")
            return True
        except Exception as e:
            if "ThrottledException" in str(e):
                print(f"限流，等待1秒后重试...（第{attempt+1}次）")
                time.sleep(1)
            else:
                print(f"写入事件失败: {e}")
                return False
        attempt += 1
    print("达到最大尝试次数，写入失败")
    return False

# 执行流程
short_term_id = get_or_create_short_term_memory()

print("\n3. 写入1000条短期记忆事件...")

base_messages = [
    "User likes science fiction movies",
    "User prefers Python over Java",
    "User often debugs network issues",
    "User is exploring AI assistant tools",
    "User prefers dark UI theme",
    "User enjoys reading technical documentation",
    "User works with cloud infrastructure",
    "User uses machine learning frameworks",
    "User develops web applications",
    "User manages database systems"
]

total_records = 124173
batch_size = 50  # 每批处理50条
success_count = 0
failed_count = 0

print(f"开始写入 {total_records} 条记录，每批 {batch_size} 条...")

for batch_num in range(0, total_records, batch_size):
    batch_end = min(batch_num + batch_size, total_records)
    print(f"\n处理第 {batch_num//batch_size + 1} 批 (记录 {batch_num+1}-{batch_end})...")
    
    for i in range(batch_num, batch_end):
        message_template = base_messages[i % len(base_messages)]
        unique_message = f"{message_template} - Record #{i+1:04d}"
        
        unique_actor_id = f"{actor_id}-{i+1:04d}"
        unique_session_id = f"{session_id}-batch-{i//batch_size + 1}"
        
        success = create_event_with_fixed_retry(
            client,
            memory_id=short_term_id,
            actor_id=unique_actor_id,
            session_id=unique_session_id,
            messages=[(unique_message, "USER")]
        )
        
        if success:
            success_count += 1
            if (i + 1) % 10 == 0:
                print(f"  已成功写入 {success_count} 条记录")
        else:
            failed_count += 1
            print(f"  记录 #{i+1} 写入失败")
    
    if batch_end < total_records:
        print(f"  第 {batch_num//batch_size + 1} 批完成，暂停2秒...")
        time.sleep(2)

print(f"\n短期记忆事件写入完成!")
print(f"成功: {success_count} 条")
print(f"失败: {failed_count} 条")
print(f"总计: {success_count + failed_count} 条")


print("\n10. 检索总数...")

def count_all_events(client, memory_id, actor_id, session_id):
    total_events = 0
    next_token = None
    while True:
        params = {
            "memory_id": memory_id,
            "actor_id": actor_id,
            "session_id": session_id,
        }
        if next_token:
            params["nextToken"] = next_token
        
        events = client.list_events(**params)
        print(f"本次请求获得事件数量: {len(events)}")

        total_events += len(events)
        next_token = None  # 当前SDK无分页token，直接退出
        if not next_token:
            break
    return total_events

total_events = count_all_events(client, short_term_id, actor_id, session_id)
print(f"Memory 中事件总数: {total_events} 条")

print("\n over!")
