"""
Demo: 记忆检索方式对比
展示不同的记忆检索方法及其适用场景

运行: python demo_memory_retrieve.py
"""
import time
from memory_utils import (
    get_memory_client,
    get_or_create_memory,
    create_event_with_retry,
    extract_content,
    DEFAULT_ACTOR_ID,
    print_header,
    print_section
)


class RetrievalDemo:
    """记忆检索演示类"""

    def __init__(self):
        self.client = get_memory_client()
        self.memory_id = None
        self.actor_id = DEFAULT_ACTOR_ID
        self.session_id = f"retrieve-demo-{int(time.time())}"

    def setup(self):
        """设置 Memory"""
        self.memory_id = get_or_create_memory(
            name="DemoRetrievalMemory",
            description="检索方式对比 Demo",
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
                }
            ],
            event_expiry_days=90,
            client=self.client
        )
        return self.memory_id

    def write_sample_data(self):
        """写入示例数据"""
        conversations = [
            ("我是一名软件工程师，在北京工作", "USER"),
            ("您好！很高兴为您服务。", "ASSISTANT"),
            ("我想买一台笔记本电脑，预算15000元", "USER"),
            ("好的，这个预算可以选择很多不错的机型。", "ASSISTANT"),
            ("我主要用于编程和机器学习", "USER"),
            ("建议选择16GB以上内存的配置。", "ASSISTANT"),
            ("我比较喜欢ThinkPad，键盘手感好", "USER"),
            ("ThinkPad确实是程序员的经典选择。", "ASSISTANT"),
        ]

        print(f"写入 {len(conversations)} 条消息...")
        for msg, role in conversations:
            create_event_with_retry(
                self.client, self.memory_id,
                self.actor_id, self.session_id,
                [(msg, role)]
            )
            time.sleep(0.3)
        print("[+] 数据写入完成")

    def demo_list_events(self):
        """演示 list_events"""
        print("\n方法: list_events()")
        print("用途: 获取所有原始事件")
        print("-" * 40)

        try:
            events = self.client.list_events(
                memory_id=self.memory_id,
                actor_id=self.actor_id,
                session_id=self.session_id
            )

            if events:
                print(f"[+] 找到 {len(events)} 条事件")
                print("前 3 条:")
                for i, event in enumerate(events[:3], 1):
                    print(f"  {i}. {str(event)[:60]}...")
            else:
                print("[!] 未找到事件")

        except Exception as e:
            print(f"[-] 失败: {e}")

    def demo_get_last_k_turns(self):
        """演示 get_last_k_turns"""
        print("\n方法: get_last_k_turns(k=5)")
        print("用途: 获取最近 K 轮对话")
        print("-" * 40)

        try:
            turns = self.client.get_last_k_turns(
                memory_id=self.memory_id,
                actor_id=self.actor_id,
                session_id=self.session_id,
                k=5
            )

            if turns:
                print(f"[+] 找到 {len(turns)} 轮对话")
                for i, turn in enumerate(turns[:3], 1):
                    print(f"  {i}. {str(turn)[:60]}...")
            else:
                print("[!] 未找到对话")

        except Exception as e:
            print(f"[-] 失败: {e}")

    def demo_retrieve_memories(self, wait_for_longterm=False):
        """演示 retrieve_memories"""
        print("\n方法: retrieve_memories()")
        print("用途: 语义搜索长期记忆")
        print("-" * 40)

        if wait_for_longterm:
            print("[*] 等待长期记忆生成...")
            time.sleep(30)

        queries = ["笔记本电脑", "编程", "品牌偏好"]

        for query in queries:
            print(f"\n查询: '{query}'")
            try:
                # 搜索语义记忆
                facts = self.client.retrieve_memories(
                    memory_id=self.memory_id,
                    namespace=f"/facts/{self.actor_id}",
                    query=query
                )

                # 搜索偏好记忆
                prefs = self.client.retrieve_memories(
                    memory_id=self.memory_id,
                    namespace=f"/preferences/{self.actor_id}",
                    query=query
                )

                fact_count = len(facts) if facts else 0
                pref_count = len(prefs) if prefs else 0

                print(f"  语义记忆: {fact_count} 条, 偏好记忆: {pref_count} 条")

                # 显示语义记忆结果（带 score）
                if facts:
                    for i, fact in enumerate(facts[:2], 1):
                        content = extract_content(fact)
                        score = fact.get('score', 0)
                        print(f"  [{i}] score: {score:.4f} | {content[:40]}...")

            except Exception as e:
                print(f"  [-] 失败: {e}")

    def demo_list_memory_records(self):
        """演示 list_memory_records"""
        print("\n方法: list_memory_records()")
        print("用途: 列出命名空间下所有记忆")
        print("-" * 40)

        namespaces = [
            (f"/facts/{self.actor_id}", "语义记忆"),
            (f"/preferences/{self.actor_id}", "偏好记忆")
        ]

        for namespace, name in namespaces:
            print(f"\n{name} ({namespace}):")
            try:
                records = self.client.list_memory_records(
                    memoryId=self.memory_id,
                    namespace=namespace
                )

                if records:
                    print(f"  [+] 找到 {len(records)} 条记忆")
                    for i, record in enumerate(records[:2], 1):
                        content = extract_content(record)
                        score = record.get('score', 'N/A')
                        score_str = f"{score:.4f}" if isinstance(score, float) else score
                        print(f"    {i}. [score: {score_str}] {content[:40]}...")
                else:
                    print("  [!] 未找到记忆")

            except Exception as e:
                print(f"  [-] 失败: {e}")


def print_comparison():
    """打印对比表格"""
    print("""
┌─────────────────────────────────────────────────────────────────┐
│                      检索方法对比                                │
├──────────────────────┬──────────────────────┬───────────────────┤
│ 方法                  │ 用途                 │ 特点              │
├──────────────────────┼──────────────────────┼───────────────────┤
│ list_events()        │ 获取所有原始事件     │ 完整、按时间排序   │
│ get_last_k_turns()   │ 获取最近K轮对话      │ 快速、适合上下文   │
│ retrieve_memories()  │ 语义搜索相关记忆     │ 智能、带score分数  │
│ list_memory_records()│ 列出所有长期记忆     │ 完整、按命名空间   │
└──────────────────────┴──────────────────────┴───────────────────┘

使用建议:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

 需要完整对话历史？
   -> list_events() 或 get_last_k_turns()

 需要智能推荐/个性化？
   -> retrieve_memories() 语义搜索

 需要用户画像分析？
   -> list_memory_records() 获取所有偏好

 需要实时响应？
   -> 短期记忆方法（立即可用）

 需要跨会话记忆？
   -> 长期记忆方法（retrieve_memories）
""")


def main():
    print_header("记忆检索方式对比 Demo")

    demo = RetrievalDemo()

    # 1. 设置
    print_section("1. 设置 Memory")
    demo.setup()

    # 2. 写入数据
    print_section("2. 写入示例数据")
    demo.write_sample_data()

    # 3. 短期记忆检索（立即可用）
    print_section("3. 短期记忆检索（立即可用）")
    demo.demo_list_events()
    demo.demo_get_last_k_turns()

    # 4. 长期记忆检索（需要等待）
    print_section("4. 长期记忆检索（需要等待生成）")
    print("[*] 等待 30 秒让 AgentCore 生成长期记忆...")
    time.sleep(30)
    demo.demo_retrieve_memories()
    demo.demo_list_memory_records()

    # 5. 对比总结
    print_header("检索方法对比")
    print_comparison()

    print("\n[+] Demo 完成!")


if __name__ == "__main__":
    main()
