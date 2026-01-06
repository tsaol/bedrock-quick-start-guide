"""
AgentCore Memory 公共工具模块
提供共享的配置、工具函数和示例数据
"""
import time
import json
from botocore.exceptions import ClientError
from bedrock_agentcore.memory import MemoryClient


# ============================================================
# 默认配置
# ============================================================
DEFAULT_REGION = "us-west-2"
DEFAULT_ACTOR_ID = "agent-actor"
DEFAULT_SESSION_ID = "agent-session"


# ============================================================
# 客户端管理
# ============================================================
_client_instance = None

def get_memory_client(region=None):
    """获取 MemoryClient 单例"""
    global _client_instance
    if _client_instance is None:
        _client_instance = MemoryClient(region_name=region or DEFAULT_REGION)
    return _client_instance


def reset_client():
    """重置客户端（用于测试）"""
    global _client_instance
    _client_instance = None


# ============================================================
# Memory 创建与获取
# ============================================================
def get_or_create_memory(name, description, strategies=None, event_expiry_days=90, client=None):
    """
    创建或获取已存在的 Memory

    Args:
        name: Memory 名称
        description: Memory 描述
        strategies: 长期记忆策略列表（可选）
        event_expiry_days: 事件过期天数
        client: MemoryClient 实例（可选，默认使用单例）

    Returns:
        memory_id: Memory ID
    """
    if client is None:
        client = get_memory_client()

    memory_id = None

    try:
        print(f"\n[*] 创建 Memory: {name}")
        memory = client.create_memory_and_wait(
            name=name,
            description=description,
            strategies=strategies or [],
            event_expiry_days=event_expiry_days,
        )
        memory_id = memory["id"]
        print(f"[+] Memory 创建成功，ID: {memory_id}")

    except ClientError as e:
        if e.response['Error']['Code'] == 'ValidationException' and "already exists" in str(e):
            print(f"[!] Memory 已存在，尝试获取已有 ID")
            memories = client.list_memories()
            memory_id = next((m['id'] for m in memories if m['id'].startswith(name)), None)

            if memory_id:
                print(f"[+] 使用已有 Memory ID: {memory_id}")
            else:
                raise RuntimeError(f"找不到已存在的 Memory: {name}")
        else:
            raise e

    return memory_id


def get_short_term_memory(name="ShortTermMemory", client=None):
    """创建或获取短期记忆（无策略）"""
    return get_or_create_memory(
        name=name,
        description="短期记忆 - 存储原始对话事件",
        strategies=[],
        event_expiry_days=21,
        client=client
    )


def get_long_term_memory(name="LongTermMemory", actor_id=None, client=None):
    """创建或获取长期记忆（带语义策略）"""
    actor = actor_id or DEFAULT_ACTOR_ID
    return get_or_create_memory(
        name=name,
        description="长期记忆 - 带语义和偏好策略",
        strategies=[
            {
                "semanticMemoryStrategy": {
                    "name": "semanticFacts",
                    "namespaces": [f"/facts/{actor}"]
                }
            },
            {
                "userPreferenceMemoryStrategy": {
                    "name": "userPreferences",
                    "namespaces": [f"/preferences/{actor}"]
                }
            }
        ],
        event_expiry_days=365,
        client=client
    )


# ============================================================
# 事件写入
# ============================================================
def create_event_with_retry(client, memory_id, actor_id, session_id, messages,
                            max_retries=5, use_exponential_backoff=True):
    """
    带重试机制的事件写入

    Args:
        client: MemoryClient 实例
        memory_id: Memory ID
        actor_id: 用户 ID
        session_id: 会话 ID
        messages: 消息列表，格式 [("内容", "USER"/"ASSISTANT")]
        max_retries: 最大重试次数
        use_exponential_backoff: 是否使用指数退避

    Returns:
        bool: 是否成功
    """
    delay = 1

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
                if attempt < max_retries - 1:
                    print(f"    [!] 限流，等待 {delay} 秒后重试...（第{attempt+1}次）")
                    time.sleep(delay)
                    if use_exponential_backoff:
                        delay *= 2
                else:
                    print(f"    [-] 重试次数耗尽，写入失败")
                    return False
            else:
                print(f"    [-] 写入事件失败: {e}")
                return False

    return False


def write_conversation(client, memory_id, actor_id, session_id, user_msg, assistant_msg=None):
    """
    写入一轮对话

    Args:
        client: MemoryClient 实例
        memory_id: Memory ID
        actor_id: 用户 ID
        session_id: 会话 ID
        user_msg: 用户消息
        assistant_msg: 助手回复（可选）

    Returns:
        bool: 是否成功
    """
    # 写入用户消息
    success = create_event_with_retry(
        client, memory_id, actor_id, session_id,
        [(user_msg, "USER")]
    )

    if not success:
        return False

    # 写入助手回复
    if assistant_msg:
        time.sleep(0.5)
        success = create_event_with_retry(
            client, memory_id, actor_id, session_id,
            [(assistant_msg, "ASSISTANT")]
        )

    return success


# ============================================================
# 记忆检索
# ============================================================
def extract_content(memory_record):
    """从记忆记录中提取内容文本"""
    if isinstance(memory_record, dict):
        content = memory_record.get('content', {})
        if isinstance(content, dict):
            return content.get('text', str(memory_record))
        return str(content)
    return str(memory_record)


def count_events(client, memory_id, actor_id, session_id, max_results=100):
    """
    统计事件总数

    注意：当前 SDK 可能不支持分页，此函数返回单次查询的结果数
    """
    try:
        events = client.list_events(
            memory_id=memory_id,
            actor_id=actor_id,
            session_id=session_id,
            max_results=max_results
        )
        return len(events) if events else 0
    except Exception as e:
        print(f"[-] 统计事件失败: {e}")
        return 0


# ============================================================
# 示例数据
# ============================================================
SAMPLE_MESSAGES = [
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

SAMPLE_CONVERSATIONS_CN = [
    {
        "user": "我是张三，28岁，在北京做软件工程师",
        "assistant": "您好张三！很高兴认识您。"
    },
    {
        "user": "我想买一台笔记本电脑，预算15000元左右",
        "assistant": "好的，15000元预算可以选择很多不错的笔记本。您主要用途是什么？"
    },
    {
        "user": "主要用于编程开发，偶尔会跑一些机器学习模型",
        "assistant": "那建议选择16GB内存以上的配置。您对品牌有偏好吗？"
    },
    {
        "user": "我比较喜欢ThinkPad，键盘手感好，而且我习惯用Linux",
        "assistant": "ThinkPad确实是程序员的经典选择！推荐X1 Carbon系列。"
    },
    {
        "user": "好的，我去看看。另外我不太在意外观，更看重性能和稳定性",
        "assistant": "理解，ThinkPad商务系列正是以稳定性著称，很适合您。"
    }
]

SAMPLE_USERS = {
    "alice_programmer": {
        "name": "Alice - 程序员",
        "profile": {"occupation": "软件工程师", "interests": ["Python", "机器学习"]},
        "conversations": [
            {"user": "我是一名Python开发者，想学习机器学习", "assistant": "建议从scikit-learn开始"},
            {"user": "我比较喜欢深度学习，有什么好的GPU推荐吗？", "assistant": "推荐NVIDIA RTX 4090"},
        ]
    },
    "bob_designer": {
        "name": "Bob - 设计师",
        "profile": {"occupation": "UI设计师", "interests": ["Figma", "设计"]},
        "conversations": [
            {"user": "我是UI/UX设计师，想了解最新的设计趋势", "assistant": "2024年趋势包括极简主义"},
            {"user": "我主要用Figma，协作功能很好", "assistant": "Figma确实在协作方面很强"},
        ]
    }
}


# ============================================================
# 打印辅助
# ============================================================
def print_header(title, char="=", width=60):
    """打印标题"""
    print(f"\n{char * width}")
    print(f" {title}")
    print(f"{char * width}")


def print_section(title, char="-", width=50):
    """打印小节标题"""
    print(f"\n{char * width}")
    print(f" {title}")
    print(f"{char * width}")
