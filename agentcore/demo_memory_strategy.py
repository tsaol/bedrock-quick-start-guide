"""
Demo: 长期记忆策略对比
展示 4 种长期记忆策略的不同效果

运行: python demo_memory_strategy.py
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


class StrategyDemo:
    """记忆策略演示类"""

    def __init__(self):
        self.client = get_memory_client()
        self.memory_id = None
        self.actor_id = DEFAULT_ACTOR_ID
        self.session_id = f"strategy-demo-{int(time.time())}"

    def setup(self):
        """创建包含所有策略的 Memory"""
        self.memory_id = get_or_create_memory(
            name="DemoStrategyMemory",
            description="策略对比 Demo - 展示 4 种策略效果",
            strategies=[
                # 1. 语义记忆策略 - 提取事实
                {
                    "semanticMemoryStrategy": {
                        "name": "Facts",
                        "namespaces": ["/facts/{actorId}"]
                    }
                },
                # 2. 用户偏好策略 - 提取喜好
                {
                    "userPreferenceMemoryStrategy": {
                        "name": "Preferences",
                        "namespaces": ["/preferences/{actorId}"]
                    }
                },
                # 3. 摘要策略 - 生成会话摘要
                {
                    "summaryMemoryStrategy": {
                        "name": "Summary",
                        "namespaces": ["/summaries/{actorId}/{sessionId}"]
                    }
                }
            ],
            event_expiry_days=90,
            client=self.client
        )
        return self.memory_id

    def write_sample_conversations(self):
        """写入示例对话"""
        conversations = [
            # 包含事实信息
            ("你好，我是李明，今年 30 岁，在上海做产品经理", "USER"),
            ("你好李明！很高兴认识您，有什么可以帮您的？", "ASSISTANT"),

            # 包含偏好信息
            ("我想买一台新手机，预算 8000 元左右", "USER"),
            ("8000 元预算可以选择很多旗舰机型，您有品牌偏好吗？", "ASSISTANT"),
            ("我比较喜欢苹果，用惯了 iOS 系统", "USER"),
            ("iPhone 15 Pro 很适合您，系统流畅，拍照也很好。", "ASSISTANT"),

            # 更多偏好
            ("我不太喜欢大屏手机，单手操作方便更重要", "USER"),
            ("那推荐 iPhone 15 Pro，6.1 寸屏幕比较适中。", "ASSISTANT"),
            ("我主要用手机拍照和看视频，游戏玩得少", "USER"),
            ("iPhone 的影像系统很强，非常适合您的需求。", "ASSISTANT"),

            # 总结性对话
            ("好的，我考虑一下 iPhone 15 Pro，谢谢推荐！", "USER"),
            ("不客气！有其他问题随时问我。", "ASSISTANT"),
        ]

        print(f"写入 {len(conversations)} 条对话...")
        for msg, role in conversations:
            create_event_with_retry(
                self.client, self.memory_id,
                self.actor_id, self.session_id,
                [(msg, role)]
            )
            time.sleep(0.3)
        print("[+] 对话写入完成")

    def retrieve_by_strategy(self, strategy_name, namespace, queries):
        """按策略检索记忆"""
        print(f"\n{strategy_name}:")
        print("-" * 50)

        for query in queries:
            print(f"\n  查询: '{query}'")
            try:
                results = self.client.retrieve_memories(
                    memory_id=self.memory_id,
                    namespace=namespace,
                    query=query,
                    top_k=3
                )

                if results:
                    print(f"  找到 {len(results)} 条记忆:")
                    for i, r in enumerate(results[:2], 1):
                        content = extract_content(r)
                        score = r.get('score', 0)
                        print(f"    [{i}] score: {score:.4f} | {content[:45]}...")
                else:
                    print("  [!] 未找到记忆")

            except Exception as e:
                print(f"  [-] 检索失败: {e}")

    def compare_strategies(self):
        """对比不同策略的检索结果"""
        print_section("策略对比检索")

        # 1. 语义记忆 - 事实查询
        self.retrieve_by_strategy(
            "📚 语义记忆 (semanticMemoryStrategy)",
            f"/facts/{self.actor_id}",
            ["用户基本信息", "手机预算", "职业"]
        )

        # 2. 用户偏好 - 偏好查询
        self.retrieve_by_strategy(
            "🎯 用户偏好 (userPreferenceMemoryStrategy)",
            f"/preferences/{self.actor_id}",
            ["品牌偏好", "屏幕大小", "使用习惯"]
        )

        # 3. 摘要 - 会话摘要
        self.retrieve_by_strategy(
            "📋 会话摘要 (summaryMemoryStrategy)",
            f"/summaries/{self.actor_id}/{self.session_id}",
            ["对话总结", "购买意向"]
        )


def print_strategy_comparison():
    """打印策略对比表"""
    print("""
┌────────────────────────────────────────────────────────────────────┐
│                    长期记忆策略对比                                  │
├─────────────────────┬──────────────────┬───────────────────────────┤
│ 策略                 │ 提取内容          │ 适用场景                   │
├─────────────────────┼──────────────────┼───────────────────────────┤
│ semanticMemory      │ 事实性知识        │ 用户画像、基本信息          │
│ userPreference      │ 偏好习惯          │ 个性化推荐、定制服务        │
│ summary             │ 会话摘要          │ 快速回顾、上下文理解        │
│ customSemantic      │ 自定义提取        │ 特定领域、复杂逻辑          │
└─────────────────────┴──────────────────┴───────────────────────────┘

策略选择建议:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

 📚 语义记忆 (semanticMemory)
    - 提取客观事实：姓名、年龄、职业、地点
    - 适合构建用户档案
    - 例如："用户是产品经理，在上海工作"

 🎯 用户偏好 (userPreference)
    - 提取主观偏好：喜欢/不喜欢、习惯、倾向
    - 适合个性化推荐
    - 例如："用户喜欢苹果品牌，偏好小屏手机"

 📋 会话摘要 (summary)
    - 生成对话要点和总结
    - 适合快速了解历史交互
    - 例如："用户咨询手机购买，推荐了 iPhone 15 Pro"

 🔧 自定义语义 (customSemantic)
    - 自定义 prompt 控制提取逻辑
    - 适合特定领域需求
    - 需要配置 extraction_config 和 consolidation_config
""")


def main():
    print_header("长期记忆策略对比 Demo")

    demo = StrategyDemo()

    # 1. 设置 Memory（包含多种策略）
    print_section("1. 创建 Memory（含 3 种策略）")
    demo.setup()

    print("\n已配置的策略:")
    print("  - semanticMemoryStrategy (语义记忆)")
    print("  - userPreferenceMemoryStrategy (用户偏好)")
    print("  - summaryMemoryStrategy (会话摘要)")

    # 2. 写入对话
    print_section("2. 写入示例对话")
    demo.write_sample_conversations()

    # 3. 等待长期记忆生成
    print_section("3. 等待长期记忆生成")
    wait_time = 60
    print(f"[*] AgentCore 需要时间分析对话并提取不同类型的记忆...")
    print(f"[*] 等待 {wait_time} 秒...")

    for i in range(wait_time, 0, -15):
        print(f"    剩余 {i} 秒...")
        time.sleep(15)

    # 4. 对比不同策略
    print_section("4. 对比不同策略的检索结果")
    demo.compare_strategies()

    # 5. 策略对比表
    print_header("策略选择指南")
    print_strategy_comparison()

    print("\n[+] Demo 完成!")


if __name__ == "__main__":
    main()
