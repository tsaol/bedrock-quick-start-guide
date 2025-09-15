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
        return
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


print("\n3. 写入多条长期记忆事件...")
long_term_msgs = [
    "User likes science fiction movies.",
    "User prefers Python over Java.",
    "User often debugs network issues.",
    "User is exploring AI assistant tools.",
    "User prefers dark UI theme."
]
for msg in long_term_msgs:
    success = create_event_with_fixed_retry(
        client,
        memory_id=long_term_id,
        actor_id=actor_id,
        session_id=session_id,
        messages=[(msg, "USER")]
    )
    if not success:
        break
print("长期记忆事件写入成功")


print("\n4. 语义检索长期记忆...")
semantic_results = client.retrieve_memories(
    memory_id=long_term_id,
    namespace=f"/facts/{actor_id}",
    query="science fiction"
)

print("语义搜索结果:")
print(semantic_results)


print("\n over!")
