"""
Demo: 短期记忆演示
展示如何创建、写入和读取短期记忆（原始事件）

运行: python demo_shortterm_memory.py
"""
import time
from memory_utils import (
    get_memory_client,
    get_short_term_memory,
    create_event_with_retry,
    SAMPLE_MESSAGES,
    DEFAULT_ACTOR_ID,
    DEFAULT_SESSION_ID,
    print_header,
    print_section
)


def main():
    print_header("短期记忆 Demo - Short Term Memory")

    # 1. 初始化客户端
    print_section("1. 初始化 Memory 客户端")
    client = get_memory_client()
    print("[+] Memory 客户端初始化成功")

    actor_id = DEFAULT_ACTOR_ID
    session_id = f"{DEFAULT_SESSION_ID}-shortterm"

    # 2. 创建短期记忆
    print_section("2. 创建短期记忆")
    memory_id = get_short_term_memory(name="DemoShortTermMemory", client=client)

    # 3. 写入事件
    print_section("3. 写入短期记忆事件")
    print(f"写入 {len(SAMPLE_MESSAGES)} 条消息...")

    success_count = 0
    for i, msg in enumerate(SAMPLE_MESSAGES, 1):
        success = create_event_with_retry(
            client=client,
            memory_id=memory_id,
            actor_id=actor_id,
            session_id=session_id,
            messages=[(msg, "USER")]
        )
        if success:
            success_count += 1
            print(f"  [{i}] {msg[:50]}...")
        else:
            print(f"  [{i}] 写入失败: {msg[:30]}...")
        time.sleep(0.5)

    print(f"\n[+] 写入完成: {success_count}/{len(SAMPLE_MESSAGES)} 条成功")

    # 4. 读取最近对话
    print_section("4. 读取最近 5 轮对话")
    try:
        recent_turns = client.get_last_k_turns(
            memory_id=memory_id,
            actor_id=actor_id,
            session_id=session_id,
            k=5
        )

        if recent_turns:
            print(f"[+] 找到 {len(recent_turns)} 条记录:")
            for i, turn in enumerate(recent_turns, 1):
                content = str(turn)[:80]
                print(f"  {i}. {content}...")
        else:
            print("[!] 未找到记录")

    except Exception as e:
        print(f"[-] 读取失败: {e}")

    # 5. 列出所有事件
    print_section("5. 列出所有事件")
    try:
        events = client.list_events(
            memory_id=memory_id,
            actor_id=actor_id,
            session_id=session_id
        )

        if events:
            print(f"[+] 共有 {len(events)} 条事件")
            print("\n前 3 条事件:")
            for i, event in enumerate(events[:3], 1):
                print(f"  {i}. {str(event)[:80]}...")
        else:
            print("[!] 未找到事件")

    except Exception as e:
        print(f"[-] 列出事件失败: {e}")

    # 6. 总结
    print_header("Demo 完成")
    print("""
短期记忆特点:
  - 立即可用，无需等待处理
  - 保存原始对话事件
  - 按 session 隔离
  - 适合维护对话上下文

常用 API:
  - create_event()      写入事件
  - get_last_k_turns()  获取最近 K 轮对话
  - list_events()       列出所有事件
""")


if __name__ == "__main__":
    main()
