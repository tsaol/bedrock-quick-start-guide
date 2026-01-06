"""
Demo: 短期+长期记忆综合演示
展示如何同时使用短期记忆和长期记忆

运行: python demo_memory_combined.py
"""
import time
from memory_utils import (
    get_memory_client,
    get_or_create_memory,
    create_event_with_retry,
    extract_content,
    DEFAULT_ACTOR_ID,
    DEFAULT_SESSION_ID,
    print_header,
    print_section
)


def main():
    print_header("综合 Demo - 短期+长期记忆")

    # 1. 初始化
    print_section("1. 初始化")
    client = get_memory_client()
    print("[+] Memory 客户端初始化成功")

    actor_id = DEFAULT_ACTOR_ID
    session_id = f"{DEFAULT_SESSION_ID}-combined"

    # 2. 创建包含短期和长期功能的 Memory
    print_section("2. 创建综合 Memory")
    memory_id = get_or_create_memory(
        name="DemoCombinedMemory",
        description="综合 Demo - 同时支持短期和长期记忆",
        strategies=[
            {
                "semanticMemoryStrategy": {
                    "name": "Facts",
                    "namespaces": ["/facts/{actorId}"]
                }
            },
            {
                "userPreferenceMemoryStrategy": {
                    "name": "Preferences",
                    "namespaces": ["/preferences/{actorId}"]
                }
            },
            {
                "summaryMemoryStrategy": {
                    "name": "Summary",
                    "namespaces": ["/summaries/{actorId}/{sessionId}"]
                }
            }
        ],
        event_expiry_days=90,
        client=client
    )

    # 3. 模拟多轮对话
    print_section("3. 模拟用户对话场景")

    conversations = [
        ("你好，我叫小明，是一名数据分析师", "你好小明！很高兴认识你，有什么可以帮你的？"),
        ("我想学习Python数据分析，有什么建议吗？", "建议从Pandas和NumPy开始，这是数据分析的基础库。"),
        ("我之前用过Excel，但数据量大了处理起来很慢", "Python处理大数据量确实更高效，可以试试Dask处理超大数据集。"),
        ("我比较喜欢可视化，Matplotlib好用吗？", "Matplotlib是基础，但推荐也学习Seaborn和Plotly，更美观易用。"),
        ("好的，我先从Pandas开始学习，谢谢！", "不客气！有问题随时问我，祝你学习顺利！")
    ]

    print("写入对话...")
    for i, (user_msg, assistant_msg) in enumerate(conversations, 1):
        success1 = create_event_with_retry(
            client, memory_id, actor_id, session_id,
            [(user_msg, "USER")]
        )
        if success1:
            time.sleep(0.3)
            create_event_with_retry(
                client, memory_id, actor_id, session_id,
                [(assistant_msg, "ASSISTANT")]
            )
            print(f"  [{i}] User: {user_msg[:40]}...")
        time.sleep(0.5)

    print("[+] 对话写入完成")

    # 4. 立即检索短期记忆
    print_section("4. 立即检索短期记忆")
    print("[*] 短期记忆立即可用，无需等待")

    print("\n使用 get_last_k_turns() 获取最近 3 轮:")
    try:
        recent = client.get_last_k_turns(
            memory_id=memory_id,
            actor_id=actor_id,
            session_id=session_id,
            k=3
        )
        if recent:
            for i, turn in enumerate(recent, 1):
                print(f"  {i}. {str(turn)[:70]}...")
        else:
            print("  [!] 未找到记录")
    except Exception as e:
        print(f"  [-] 检索失败: {e}")

    print("\n使用 list_events() 统计事件数:")
    try:
        events = client.list_events(
            memory_id=memory_id,
            actor_id=actor_id,
            session_id=session_id
        )
        print(f"  [+] 共有 {len(events) if events else 0} 条事件")
    except Exception as e:
        print(f"  [-] 统计失败: {e}")

    # 5. 等待长期记忆生成
    print_section("5. 等待长期记忆生成")
    wait_time = 30
    print(f"[*] 等待 {wait_time} 秒让 AgentCore 生成长期记忆...")

    for i in range(wait_time, 0, -10):
        print(f"    剩余 {i} 秒...")
        time.sleep(10)

    # 6. 检索长期记忆
    print_section("6. 检索长期记忆")

    namespaces = [
        (f"/facts/{actor_id}", "语义记忆 (Facts)"),
        (f"/preferences/{actor_id}", "用户偏好 (Preferences)"),
    ]

    queries = ["数据分析", "Python学习", "用户信息"]

    for namespace, ns_name in namespaces:
        print(f"\n{ns_name}:")
        for query in queries:
            try:
                memories = client.retrieve_memories(
                    memory_id=memory_id,
                    namespace=namespace,
                    query=query
                )
                if memories:
                    print(f"  '{query}': {len(memories)} 条")
                    content = extract_content(memories[0])
                    print(f"    -> {content[:50]}...")
            except Exception as e:
                print(f"  '{query}': 检索失败")

    # 7. 对比总结
    print_header("短期记忆 vs 长期记忆")
    print("""
┌────────────────────────────────────────────────────────────┐
│                    短期记忆                                 │
├────────────────────────────────────────────────────────────┤
│ 特点: 立即可用，保存原始事件                                │
│ 用途: 维护对话上下文，获取最近对话                          │
│ API:  get_last_k_turns(), list_events()                    │
└────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────┐
│                    长期记忆                                 │
├────────────────────────────────────────────────────────────┤
│ 特点: 需要等待处理，提取结构化知识                          │
│ 用途: 语义搜索，个性化推荐，用户画像                        │
│ API:  retrieve_memories(), list_memory_records()           │
└────────────────────────────────────────────────────────────┘

使用场景:
  - "刚才说什么？" -> 短期记忆 get_last_k_turns()
  - "用户喜欢什么？" -> 长期记忆 retrieve_memories()
  - "完整对话记录" -> 短期记忆 list_events()
  - "跨会话用户信息" -> 长期记忆 retrieve_memories()
""")


if __name__ == "__main__":
    main()
