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



def get_or_create_long_term_memory():
    memory_name = "AgentLongTermMemory"
    memory_id = None
    try:
        print("\n3. 创建长期记忆...")
        memory = client.create_memory_and_wait(
            name=memory_name,
            description="long-term memory with semantic strategy",
            strategies=[
                {
                    "semanticMemoryStrategy": {
                        "name": "semanticFacts",
                        "namespaces": [f"/facts/{actor_id}"]
                    }
                }
            ],
        )
        memory_id = memory["id"]
        print(f" 长期记忆创建成功，ID: {memory_id}")

    except ClientError as e:
        print(f"创建long term memory被取消")
        if e.response['Error']['Code'] == 'ValidationException' and "already exists" in str(e):
            print("长期记忆已存在，尝试获取已有 ID")
            memories = client.list_memories()
            memory_id = next((m['id'] for m in memories if m['id'].startswith(memory_name)), None)
            print(f"Long term Memory already exists. Using existing memory ID: {memory_id}")
            if memory_id:
                print(f"使用已有长期记忆 ID: {memory_id}")
            else:
                raise RuntimeError("找不到已存在的长期记忆 ID")
        else:
            raise e
    return memory_id

# 创建长期记忆函数（处理已存在情况）
def get_or_create_long_term_memory():
    memory_name = "AgentLongTermMemory"
    memory_id = None
    try:
        print("\n2. 创建长期记忆...")
        memory = client.create_memory_and_wait(
            name=memory_name,
            description="long-term memory with semantic and personalized strategies",
            strategies=[
                {
                    "semanticMemoryStrategy": {
                        "name": "semanticFacts",
                        "namespaces": [f"/facts/{actor_id}"]
                    }
                },
                {
                    "userPreferenceMemoryStrategy": {
                        "name": "userPreferences",
                        "namespaces": [f"/preferences/{actor_id}"],
                        "description": "Built-in personalized memory strategy"
                    }
                }
            ],
        )
        memory_id = memory["id"]
        print(f" 长期记忆创建成功，ID: {memory_id}")
        return memory_id
    except ClientError as e:
        print(f"创建long term memory被取消")
        if e.response['Error']['Code'] == 'ValidationException' and "already exists" in str(e):
            print("长期记忆已存在，尝试获取已有 ID")
            memories = client.list_memories()
            memory_id = next((m['id'] for m in memories if m['id'].startswith(memory_name)), None)
            print(f"Long term Memory already exists. Using existing memory ID: {memory_id}")
            if memory_id:
                print(f"使用已有长期记忆 ID: {memory_id}")
            else:
                raise RuntimeError("找不到已存在的长期记忆 ID")
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
long_term_id = get_or_create_long_term_memory()


print("\n3. 写入1000条长期记忆事件...")

# 定义基础消息模板
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



# 批量写入1000条记录
total_records = 121
batch_size = 50  # 每批处理50条
success_count = 0
failed_count = 0

print(f"开始写入 {total_records} 条记录，每批 {batch_size} 条...")

for batch_num in range(0, total_records, batch_size):
    batch_end = min(batch_num + batch_size, total_records)
    print(f"\n处理第 {batch_num//batch_size + 1} 批 (记录 {batch_num+1}-{batch_end})...")
    
    for i in range(batch_num, batch_end):
        # 使用自增ID和循环使用基础消息
        message_template = base_messages[i % len(base_messages)]
        unique_message = f"{message_template} - Record #{i+1:04d}"
        
        # 使用不同的actor_id来区分记录
        unique_actor_id = f"{actor_id}-{i+1:04d}"
        unique_session_id = f"{session_id}-batch-{i//batch_size + 1}"
        
        success = create_event_with_fixed_retry(
            client,
            memory_id=long_term_id,
            actor_id=unique_actor_id,
            session_id=unique_session_id,
            messages=[(unique_message, "USER")]
        )
        
        if success:
            success_count += 1
            if (i + 1) % 10 == 0:  # 每10条显示一次进度
                print(f"  已成功写入 {success_count} 条记录")
        else:
            failed_count += 1
            print(f"  记录 #{i+1} 写入失败")
            
        # 添加小延迟避免限流
        # time.sleep(0.1)
    
    # 每批之间稍作停顿
    if batch_end < total_records:
        print(f"  第 {batch_num//batch_size + 1} 批完成，暂停2秒...")
        time.sleep(2)

print(f"\n长期记忆事件写入完成!")
print(f"成功: {success_count} 条")
print(f"失败: {failed_count} 条")
print(f"总计: {success_count + failed_count} 条")


print("\n4. 语义检索长期记忆...")
semantic_results = client.retrieve_memories(
    memory_id=long_term_id,
    namespace=f"/facts/{actor_id}",
    query="science fiction"
)


print("\n10. 检索总数...")
def count_all_events(client, memory_id, actor_id, session_id):
    total_events = 0
    next_token = None
    while True:
        params = {
            "memory_id": memory_id,
            "actor_id": actor_id,
            "session_id": session_id,
            "max_results": 100  # 每页请求100条事件，最大可调整
        }
        events = client.list_events(**params)  # 直接得到事件列表
        # 打印看一下返回的事件数量和内容
        print(f"本次请求获得事件数量: {len(events)}")

        total_events += len(events)

        # 估计SDK用None或空list作为下一页标记，如果无分页字段则跳出
        # 根据你打印，目前没有nextToken分分页参数，故直接退出
        # 如果SDK支持分页，应从events或response中提取下一页token
        next_token = None # 当前SDK不支持分页或无返回该字段
        if not next_token:
            break

    return total_events


# 使用示例
total_events = count_all_events(client, long_term_id, actor_id, session_id)
print(f"Memory 中事件总数: {total_events} 条")
print("\n over!")
