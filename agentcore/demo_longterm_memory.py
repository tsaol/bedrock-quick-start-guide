"""
Demo: 长期记忆演示
展示如何创建、写入和检索长期记忆（语义记忆 + 用户偏好）

运行: python demo_longterm_memory.py
"""
import time
from memory_utils import (
    get_memory_client,
    get_or_create_memory,
    create_event_with_retry,
    extract_content,
    SAMPLE_CONVERSATIONS_CN,
    DEFAULT_ACTOR_ID,
    DEFAULT_SESSION_ID,
    print_header,
    print_section
)


def main():
    print_header("长期记忆 Demo - Long Term Memory")

    # 1. 初始化客户端
    print_section("1. 初始化 Memory 客户端")
    client = get_memory_client()
    print("[+] Memory 客户端初始化成功")

    actor_id = DEFAULT_ACTOR_ID
    session_id = f"{DEFAULT_SESSION_ID}-longterm"

    # 2. 创建长期记忆（带策略）
    print_section("2. 创建长期记忆（带策略）")
    memory_id = get_or_create_memory(
        name="DemoLongTermMemory",
        description="长期记忆 Demo - 语义记忆和用户偏好",
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
                    "namespaces": [f"/preferences/{actor_id}"]
                }
            }
        ],
        event_expiry_days=365,
        client=client
    )

    print("\n策略说明:")
    print("  - semanticMemoryStrategy: 提取事实性知识")
    print("  - userPreferenceMemoryStrategy: 学习用户偏好")

    # 3. 写入对话数据
    print_section("3. 写入对话数据")
    print(f"写入 {len(SAMPLE_CONVERSATIONS_CN)} 轮对话...")

    for i, conv in enumerate(SAMPLE_CONVERSATIONS_CN, 1):
        # 用户消息
        success1 = create_event_with_retry(
            client, memory_id, actor_id, session_id,
            [(conv["user"], "USER")]
        )

        if success1:
            time.sleep(0.5)
            # 助手回复
            success2 = create_event_with_retry(
                client, memory_id, actor_id, session_id,
                [(conv["assistant"], "ASSISTANT")]
            )

            if success2:
                print(f"  [{i}] {conv['user'][:40]}...")
            else:
                print(f"  [{i}] 助手回复写入失败")
        else:
            print(f"  [{i}] 用户消息写入失败")

        time.sleep(1)

    print("\n[+] 对话写入完成")

    # 4. 等待长期记忆生成
    print_section("4. 等待长期记忆生成")
    wait_time = 30
    print(f"[*] AgentCore 需要时间从对话中提取长期记忆...")
    print(f"[*] 等待 {wait_time} 秒...")

    for i in range(wait_time, 0, -10):
        print(f"    剩余 {i} 秒...")
        time.sleep(10)

    # 5. 检索语义记忆
    print_section("5. 检索语义记忆 (Semantic Memory)")

    queries = ["笔记本电脑", "编程开发", "用户信息"]

    for query in queries:
        print(f"\n查询: '{query}'")
        try:
            memories = client.retrieve_memories(
                memory_id=memory_id,
                namespace=f"/facts/{actor_id}",
                query=query
            )

            if memories:
                print(f"  [+] 找到 {len(memories)} 条记忆:")
                for i, memory in enumerate(memories[:3], 1):
                    content = extract_content(memory)
                    print(f"      {i}. {content[:60]}...")
            else:
                print("  [!] 未找到相关记忆")

        except Exception as e:
            print(f"  [-] 检索失败: {e}")

    # 6. 检索用户偏好
    print_section("6. 检索用户偏好 (User Preferences)")

    preference_queries = ["品牌偏好", "使用习惯"]

    for query in preference_queries:
        print(f"\n查询: '{query}'")
        try:
            memories = client.retrieve_memories(
                memory_id=memory_id,
                namespace=f"/preferences/{actor_id}",
                query=query
            )

            if memories:
                print(f"  [+] 找到 {len(memories)} 条偏好:")
                for i, memory in enumerate(memories[:3], 1):
                    content = extract_content(memory)
                    print(f"      {i}. {content[:60]}...")
            else:
                print("  [!] 未找到相关偏好")

        except Exception as e:
            print(f"  [-] 检索失败: {e}")

    # 7. 总结
    print_header("Demo 完成")
    print("""
长期记忆特点:
  - 需要等待 AgentCore 处理（约 1-2 分钟）
  - 自动提取事实性知识和用户偏好
  - 支持语义搜索
  - 跨会话持久化

策略类型:
  - semanticMemoryStrategy    语义记忆，存储事实
  - userPreferenceMemoryStrategy  用户偏好
  - summaryMemoryStrategy     会话摘要

常用 API:
  - retrieve_memories()       语义搜索
  - list_memory_records()     列出所有记忆
""")


if __name__ == "__main__":
    main()
