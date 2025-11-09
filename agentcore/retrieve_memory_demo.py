"""
AgentCore Memory 检索方式对比Demo
展示如何从短期记忆和长期记忆中检索数据
"""
import time
from datetime import datetime
from bedrock_agentcore.memory import MemoryClient
from botocore.exceptions import ClientError

class MemoryRetrievalDemo:
    def __init__(self, region="us-west-2"):
        self.memory_client = MemoryClient(region_name=region)
        self.memory_id = None
        
    def setup_memory(self, use_existing=True):
        """设置Memory - 可以复用已有的"""
        
        if use_existing:
            # 复用之前创建的Memory
            print(f"\n📝 复用已有Memory...")
            # 使用之前创建的 LongTermStrategyComparison
            self.memory_id = "LongTermStrategyComparison-65gG8z6XFf"
            print(f"✅ 使用Memory ID: {self.memory_id}")
            return self.memory_id
        
        # 如果需要创建新的
        memory_name = "MemoryRetrievalDemo"
        
        try:
            print(f"\n📝 创建新Memory: {memory_name}")
            memory = self.memory_client.create_memory_and_wait(
                name=memory_name,
                description="演示短期和长期记忆检索",
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
                event_expiry_days=90
            )
            self.memory_id = memory["id"]
            print(f"✅ Memory创建成功，ID: {self.memory_id}")
            
        except ClientError as e:
            if "already exists" in str(e):
                print(f"⚠️  Memory已存在，获取现有ID")
                memories = self.memory_client.list_memories()
                self.memory_id = next((m['id'] for m in memories if memory_name in m['id']), None)
                print(f"✅ 使用现有Memory ID: {self.memory_id}")
            else:
                raise e
                
        return self.memory_id
    
    def write_sample_data(self, user_id, session_id):
        """写入示例数据"""
        print(f"\n📝 写入示例对话数据...")
        
        conversations = [
            ("我是张三，28岁，在北京做软件工程师", "USER"),
            ("您好张三！很高兴认识您。", "ASSISTANT"),
            ("我想买一台笔记本电脑，预算15000元左右", "USER"),
            ("好的，15000元预算可以选择很多不错的笔记本。您主要用途是什么？", "ASSISTANT"),
            ("主要用于编程开发，偶尔会跑一些机器学习模型", "USER"),
            ("那建议选择16GB内存以上的配置。您对品牌有偏好吗？", "ASSISTANT"),
            ("我比较喜欢ThinkPad，键盘手感好，而且我习惯用Linux", "USER"),
            ("ThinkPad确实是程序员的经典选择！推荐X1 Carbon系列。", "ASSISTANT"),
            ("好的，我去看看。另外我不太在意外观，更看重性能和稳定性", "USER"),
            ("理解，ThinkPad商务系列正是以稳定性著称，很适合您。", "ASSISTANT")
        ]
        
        for i, (msg, role) in enumerate(conversations, 1):
            try:
                self.memory_client.create_event(
                    memory_id=self.memory_id,
                    actor_id=user_id,
                    session_id=session_id,
                    messages=[(msg, role)]
                )
                print(f"  ✅ 消息 {i}: {msg[:40]}...")
                time.sleep(0.5)
            except Exception as e:
                print(f"  ❌ 消息 {i} 失败: {str(e)}")
        
        print(f"✅ 数据写入完成")
    
    def retrieve_short_term_memory(self, user_id, session_id):
        """检索短期记忆（原始事件）"""
        print(f"\n{'='*60}")
        print("📖 方法1: 检索短期记忆（原始事件）")
        print(f"{'='*60}")
        
        # 方法1: list_events - 列出所有事件
        print("\n🔍 1.1 使用 list_events() 获取所有事件:")
        try:
            events = self.memory_client.list_events(
                memory_id=self.memory_id,
                actor_id=user_id,
                session_id=session_id
            )
            
            if events:
                print(f"  ✅ 找到 {len(events)} 条原始事件")
                print(f"\n  前3条事件内容:")
                for i, event in enumerate(events[:3], 1):
                    print(f"    {i}. {str(event)[:80]}...")
            else:
                print(f"  ⚠️ 未找到事件")
        except Exception as e:
            print(f"  ❌ 检索失败: {str(e)}")
        
        # 方法2: get_last_k_turns - 获取最近K轮对话
        print("\n🔍 1.2 使用 get_last_k_turns() 获取最近5轮对话:")
        try:
            recent_turns = self.memory_client.get_last_k_turns(
                memory_id=self.memory_id,
                actor_id=user_id,
                session_id=session_id,
                k=5
            )
            
            if recent_turns:
                print(f"  ✅ 找到 {len(recent_turns)} 轮对话")
                print(f"\n  最近的对话:")
                for i, turn in enumerate(recent_turns[:3], 1):
                    print(f"    {i}. {str(turn)[:80]}...")
            else:
                print(f"  ⚠️ 未找到对话")
        except Exception as e:
            print(f"  ❌ 检索失败: {str(e)}")
        
        # 方法3: get_event - 获取特定事件（需要event_id）
        print("\n🔍 1.3 使用 get_event() 获取特定事件:")
        print("  💡 需要知道具体的 event_id")
        print("  💡 通常先用 list_events() 获取 event_id，再用此方法")
    
    def retrieve_long_term_memory(self, user_id):
        """检索长期记忆"""
        print(f"\n{'='*60}")
        print("🧠 方法2: 检索长期记忆（提取的知识）")
        print(f"{'='*60}")
        
        # 方法1: retrieve_memories - 语义搜索
        print("\n🔍 2.1 使用 retrieve_memories() 语义搜索:")
        
        queries = [
            ("用户基本信息", "/facts"),
            ("笔记本电脑偏好", "/preferences"),
            ("对话摘要", "/summaries")
        ]
        
        for query, namespace_suffix in queries:
            print(f"\n  查询: '{query}' (namespace: {namespace_suffix})")
            try:
                memories = self.memory_client.retrieve_memories(
                    memory_id=self.memory_id,
                    namespace=f"{namespace_suffix}/{user_id}",
                    query=query
                )
                
                if memories:
                    print(f"    ✅ 找到 {len(memories)} 条记忆")
                    for i, memory in enumerate(memories[:2], 1):
                        content = self.extract_content(memory)
                        print(f"      {i}. {content[:60]}...")
                else:
                    print(f"    ⚠️ 未找到相关记忆")
            except Exception as e:
                print(f"    ❌ 检索失败: {str(e)}")
        
        # 方法2: list_memory_records - 列出命名空间下的所有记忆
        print("\n🔍 2.2 使用 list_memory_records() 列出所有长期记忆:")
        try:
            memory_records = self.memory_client.list_memory_records(
                memory_id=self.memory_id,
                namespace=f"/facts/{user_id}"
            )
            
            if memory_records:
                print(f"  ✅ 找到 {len(memory_records)} 条语义记忆")
                for i, record in enumerate(memory_records[:3], 1):
                    content = self.extract_content(record)
                    print(f"    {i}. {content[:60]}...")
            else:
                print(f"  ⚠️ 未找到记忆记录")
        except Exception as e:
            print(f"  ❌ 检索失败: {str(e)}")
    
    def compare_retrieval_methods(self, user_id, session_id):
        """对比不同检索方法"""
        print(f"\n{'='*60}")
        print("📊 检索方法对比")
        print(f"{'='*60}")
        
        comparison = """
┌─────────────────────────────────────────────────────────────┐
│ 短期记忆检索（原始事件）                                      │
├─────────────────────────────────────────────────────────────┤
│ 方法                    │ 用途                │ 特点          │
├─────────────────────────┼────────────────────┼──────────────┤
│ list_events()          │ 获取所有原始事件     │ 完整、按时间排序│
│ get_last_k_turns()     │ 获取最近K轮对话     │ 快速、适合上下文│
│ get_event(event_id)    │ 获取特定事件        │ 精确、需要ID   │
└─────────────────────────┴────────────────────┴──────────────┘

┌─────────────────────────────────────────────────────────────┐
│ 长期记忆检索（提取的知识）                                    │
├─────────────────────────────────────────────────────────────┤
│ 方法                    │ 用途                │ 特点          │
├─────────────────────────┼────────────────────┼──────────────┤
│ retrieve_memories()    │ 语义搜索相关记忆     │ 智能、相关性排序│
│ list_memory_records()  │ 列出命名空间所有记忆 │ 完整、按类型   │
└─────────────────────────┴────────────────────┴──────────────┘

使用场景建议:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📖 需要完整对话历史？
   → 使用 list_events() 或 get_last_k_turns()
   → 获取原始对话内容，保持完整性

🧠 需要智能推荐/个性化？
   → 使用 retrieve_memories() 
   → 基于查询语义匹配相关记忆

📊 需要用户画像分析？
   → 使用 list_memory_records()
   → 获取所有提取的偏好和事实

⚡ 需要实时响应？
   → 短期记忆立即可用
   → 长期记忆需要等待1-2分钟生成

💾 需要跨会话记忆？
   → 使用长期记忆
   → 短期记忆按session隔离
        """
        print(comparison)
    
    def extract_content(self, memory_record):
        """提取记忆内容"""
        if isinstance(memory_record, dict):
            content = memory_record.get('content', {})
            if isinstance(content, dict):
                return content.get('text', str(memory_record))
            else:
                return str(content)
        else:
            return str(memory_record)


def main():
    print("🔍 AgentCore Memory 检索方式对比Demo")
    print("="*60)
    
    demo = MemoryRetrievalDemo()
    
    # 1. 设置Memory（复用已有的）
    demo.setup_memory(use_existing=True)
    
    # 2. 写入示例数据
    user_id = "demo_user_retrieval"
    session_id = f"demo_session_{int(time.time())}"
    
    # demo.write_sample_data(user_id, session_id)
    
    # 3. 立即检索短期记忆
    print(f"\n{'#'*60}")
    print("# 立即检索短期记忆（写入后立即可用）")
    print(f"{'#'*60}")
    
    demo.retrieve_short_term_memory(user_id, session_id)
    
    # 4. 等待长期记忆生成
    print(f"\n{'#'*60}")
    print("# 等待长期记忆生成")
    print(f"{'#'*60}")
    print("\n⏳ 等待60秒让AgentCore生成长期记忆...")
    time.sleep(60)
    
    # 5. 检索长期记忆
    print(f"\n{'#'*60}")
    print("# 检索长期记忆（需要等待生成）")
    print(f"{'#'*60}")
    
    demo.retrieve_long_term_memory(user_id)
    
    # 6. 对比总结
    demo.compare_retrieval_methods(user_id, session_id)
    
    # 7. 实际应用示例
    print(f"\n{'='*60}")
    print("💡 实际应用示例")
    print(f"{'='*60}")
    
    examples = """
场景1: 聊天机器人维护对话上下文
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
用户: "我刚才说的预算是多少？"
系统: 使用 get_last_k_turns(k=10) 获取最近对话
     → 找到 "预算15000元左右"
     → 回答: "您刚才提到预算是15000元左右"

场景2: 电商个性化推荐
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
用户: "推荐一款笔记本"
系统: 使用 retrieve_memories(query="笔记本偏好")
     → 找到 "偏好ThinkPad"、"预算15000"、"重视性能"
     → 推荐: "根据您的偏好，推荐ThinkPad X1 Carbon..."

场景3: 客服系统查询历史
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
客服: "查看用户历史咨询"
系统: 使用 list_events() 获取所有历史事件
     → 显示完整对话记录
     → 便于客服了解用户问题

场景4: 用户画像分析
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
分析师: "分析用户偏好"
系统: 使用 list_memory_records(namespace="/preferences/user")
     → 获取所有偏好记忆
     → 生成用户画像报告
    """
    print(examples)
    
    print(f"\n✅ Demo完成！")
    print("\n💡 关键要点:")
    print("  1. 短期记忆（原始事件）立即可用，适合对话上下文")
    print("  2. 长期记忆（提取知识）需要等待，适合个性化和分析")
    print("  3. 两种记忆互补，根据场景选择合适的检索方法")
    print("  4. 短期记忆保留原始完整信息，长期记忆提供结构化知识")


if __name__ == "__main__":
    main()
