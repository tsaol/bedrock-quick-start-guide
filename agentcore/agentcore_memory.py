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

# 创建短期记忆函数（处理已存在情况）
def get_or_create_short_term_memory():
    memory_name = "AgentShortTermMemory"
    memory_id = None
    try:
        print("\n2. 创建短期记忆...")
        memory = client.create_memory_and_wait(
            name=memory_name,
            description="Memory for agent shortterm conversations",
            strategies=[],
            event_expiry_days=21,
        )
        memory_id = memory["id"]
        print(f" 短期记忆创建成功，ID: {memory_id}")

    except ClientError as e:
        print(f"创建被取消")
        if e.response['Error']['Code'] == 'ValidationException' and "already exists" in str(e):
            print("短期记忆已存在，尝试获取已有 ID")
            memories = client.list_memories()
            memory_id = next((m['id'] for m in memories if m['id'].startswith(memory_name)), None)
            print(f"Memory already exists. Using existing memory ID: {memory_id}")

            if memory_id:
                print(f"使用已有短期记忆 ID: {memory_id}")
            else:
                raise RuntimeError("找不到已存在的短期记忆 ID")
        else:
            raise e
    return memory_id

# 创建长期记忆函数（处理已存在情况）
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

# 写入事件重试函数，支持指数退避
def create_event_with_retry(client, memory_id, actor_id, session_id, messages, max_retries=5):
    delay = 1  # 初始等待秒数
    for attempt in range(max_retries):
        try:
            client.create_event(
                memory_id=memory_id,
                actor_id=actor_id,
                session_id=session_id,
                messages=messages
            )
            return True
        except Exception as e:
            if "ThrottledException" in str(e):
                print(f"限流，等待 {delay} 秒后重试...（第{attempt+1}次）")
                time.sleep(delay)
                delay *= 2  # 延长等待时间
            else:
                print(f"写入事件失败: {e}")
                return False
    print("重试次数耗尽，写入失败")
    return False

# 执行流程
short_term_id = get_or_create_short_term_memory()
long_term_id = get_or_create_long_term_memory()

print("\n4. 写入短期记忆事件...")
for i in range(10):
    success = create_event_with_retry(
        client,
        memory_id=short_term_id,
        actor_id=actor_id,
        session_id=session_id,
        messages=[(f"Hello from short-term memory message #{i+1}", "USER")]
    )
    if not success:
        break
print("短期记忆事件写入成功")

print("\n5. 写入多条长期记忆事件...")
long_term_msgs = [
    "User likes science fiction movies.",
    "User prefers Python over Java.",
    "User often debugs network issues.",
    "User is exploring AI assistant tools.",
    "User prefers dark UI theme."
]
for msg in long_term_msgs:
    client.create_event(
        memory_id=long_term_id,
        actor_id=actor_id,
        session_id=session_id,
        messages=[(msg, "USER")]
    )
print("长期记忆事件写入成功")

print("\n6. 检索短期记忆最近5条对话...")
recent_short_term = client.get_last_k_turns(
    memory_id=short_term_id,
    actor_id=actor_id,
    session_id=session_id,
    k=5,
)
print("最近的短期记忆:")
print(recent_short_term)

print("\n7. 语义检索长期记忆...")
semantic_results = client.retrieve_memories(
    memory_id=long_term_id,
    namespace=f"/facts/{actor_id}",
    query="science fiction"
)
print("语义搜索结果:")
print(semantic_results)

print("\n over!")
