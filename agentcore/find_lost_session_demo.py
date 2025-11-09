"""
AgentCore Memory - 找回"丢失"的Session Demo
演示如果忘记了session_id，如何找回短期记忆
"""
import time
from datetime import datetime
from bedrock_agentcore.memory import MemoryClient
from botocore.exceptions import ClientError

class FindLostSessionDemo:
    def __init__(self, region="us-west-2"):
        self.memory_client = MemoryClient(region_name=region)
        # 复用已有Memory
        self.memory_id = "LongTermStrategyComparison-65gG8z6XFf"
        
    def scenario_1_forget_session_id(self):
        """场景1: 忘记了session_id，尝试找回"""
        print(f"\n{'='*60}")
        print("📝 场景1: 忘记了session_id")
        print(f"{'='*60}")
        
        # 1. 写入一些数据（模拟用户对话）
        user_id = "lost_session_user"
        secret_session_id = f"secret_session_{int(time.time())}"
        
        print(f"\n1️⃣ 写入数据到 session: {secret_session_id}")
        messages = [
            "我想买一台游戏本，预算8000元",
            "我喜欢RGB灯效，外观要炫酷",
            "主要玩英雄联盟和原神"
        ]
        
        for i, msg in enumerate(messages, 1):
            try:
                self.memory_client.create_event(
                    memory_id=self.memory_id,
                    actor_id=user_id,
                    session_id=secret_session_id,
                    messages=[(msg, "USER")]
                )
                print(f"  ✅ 消息 {i}: {msg}")
                time.sleep(0.5)
            except Exception as e:
                print(f"  ❌ 消息 {i} 失败: {str(e)}")
        
        # 2. 模拟忘记了session_id
        print(f"\n2️⃣ 😱 糟糕！忘记了session_id...")
        print(f"   只记得 user_id: {user_id}")
        
        # 3. 尝试方法1: 使用错误的session_id
        print(f"\n3️⃣ 尝试用错误的session_id检索:")
        wrong_session = "wrong_session_123"
        try:
            events = self.memory_client.list_events(
                memory_id=self.memory_id,
                actor_id=user_id,
                session_id=wrong_session
            )
            print(f"  ❌ 结果: 找到 {len(events) if events else 0} 条记录")
        except Exception as e:
            print(f"  ❌ 失败: {str(e)}")
        
        # 4. 尝试方法2: 不指定session_id（看API是否支持）
        print(f"\n4️⃣ 尝试不指定session_id检索:")
        print(f"  💡 测试 list_events() 是否支持不传session_id...")
        try:
            # 注意：list_events 需要 session_id，这会失败
            events = self.memory_client.list_events(
                memory_id=self.memory_id,
                actor_id=user_id
                # 不传 session_id
            )
            print(f"  ✅ 成功！找到 {len(events)} 条记录")
        except Exception as e:
            print(f"  ❌ 失败: {str(e)}")
            print(f"  💡 list_events() 必须指定 session_id")
        
        # 5. 解决方案：通过长期记忆找回
        print(f"\n5️⃣ 💡 解决方案: 等待长期记忆生成")
        print(f"  ⏳ 等待60秒让AgentCore生成长期记忆...")
        time.sleep(60)
        
        print(f"\n  🔍 通过长期记忆检索:")
        try:
            memories = self.memory_client.retrieve_memories(
                memory_id=self.memory_id,
                namespace=f"/facts/{user_id}",
                query="游戏本 预算"
            )
            
            if memories:
                print(f"  ✅ 成功！通过长期记忆找到 {len(memories)} 条相关信息:")
                for i, memory in enumerate(memories[:3], 1):
                    content = self.extract_content(memory)
                    print(f"    {i}. {content[:60]}...")
            else:
                print(f"  ⚠️ 长期记忆尚未生成")
        except Exception as e:
            print(f"  ❌ 失败: {str(e)}")
        
        return user_id, secret_session_id
    
    def scenario_2_list_all_sessions(self):
        """场景2: 列出用户的所有session"""
        print(f"\n{'='*60}")
        print("📝 场景2: 如何找到用户的所有session?")
        print(f"{'='*60}")
        
        print(f"\n💡 AgentCore Memory API 的限制:")
        print(f"  ❌ 没有 list_sessions() API")
        print(f"  ❌ 没有 list_events_by_actor() API")
        print(f"  ❌ list_events() 必须同时提供 actor_id 和 session_id")
        
        print(f"\n🔧 可能的解决方案:")
        solutions = """
1️⃣ 应用层管理 Session ID
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   在你的应用数据库中记录 session_id
   
   示例数据库表:
   ┌──────────┬─────────────────────┬─────────────────────┐
   │ user_id  │ session_id          │ created_at          │
   ├──────────┼─────────────────────┼─────────────────────┤
   │ user_001 │ chat_20241107_001   │ 2024-11-07 10:00:00 │
   │ user_001 │ chat_20241107_002   │ 2024-11-07 14:30:00 │
   │ user_002 │ shopping_session_01 │ 2024-11-07 15:00:00 │
   └──────────┴─────────────────────┴─────────────────────┘

2️⃣ 使用固定的 Session ID 模式
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   使用可预测的命名规则
   
   示例:
   session_id = f"{user_id}_chat_{date}"
   session_id = f"{user_id}_order_{order_id}"
   
   这样即使"忘记"，也能重新构造出来

3️⃣ 依赖长期记忆
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   短期记忆丢失后，依靠长期记忆
   
   优点: 长期记忆跨session，不需要session_id
   缺点: 需要等待1-2分钟生成，且不包含完整原始对话

4️⃣ 使用单一 Session ID
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   每个用户只用一个固定的 session_id
   
   示例:
   session_id = f"user_{user_id}_main_session"
   
   优点: 永远不会丢失
   缺点: 无法区分不同的对话会话
        """
        print(solutions)
    
    def scenario_3_best_practices(self):
        """场景3: 最佳实践建议"""
        print(f"\n{'='*60}")
        print("💡 最佳实践建议")
        print(f"{'='*60}")
        
        practices = """
推荐方案: 应用层 + AgentCore 双层管理
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

架构设计:
┌─────────────────────────────────────────────────────────────┐
│ 应用层数据库                                                 │
├─────────────────────────────────────────────────────────────┤
│ • 存储 user_id ↔ session_id 映射                            │
│ • 记录会话元数据（创建时间、状态等）                         │
│ • 提供 session 管理 API                                      │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ AgentCore Memory                                            │
├─────────────────────────────────────────────────────────────┤
│ • 存储实际对话内容                                           │
│ • 短期记忆（需要 session_id）                                │
│ • 长期记忆（不需要 session_id）                              │
└─────────────────────────────────────────────────────────────┘

代码示例:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class SessionManager:
    def __init__(self):
        self.db = Database()  # 你的数据库
        self.memory_client = MemoryClient()
    
    def create_session(self, user_id):
        # 创建新会话
        session_id = f"chat_{user_id}_{int(time.time())}"
        
        # 保存到数据库
        self.db.save_session(user_id, session_id)
        
        return session_id
    
    def get_user_sessions(self, user_id):
        # 从数据库获取用户的所有session
        return self.db.get_sessions(user_id)
    
    def get_session_messages(self, user_id, session_id):
        # 从AgentCore获取对话内容
        return self.memory_client.list_events(
            memory_id=self.memory_id,
            actor_id=user_id,
            session_id=session_id
        )

使用流程:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# 1. 用户开始新对话
session_id = session_manager.create_session(user_id)

# 2. 存储对话到AgentCore
memory_client.create_event(
    memory_id=memory_id,
    actor_id=user_id,
    session_id=session_id,
    messages=[("Hello", "USER")]
)

# 3. 用户回来查看历史
sessions = session_manager.get_user_sessions(user_id)
for session in sessions:
    messages = session_manager.get_session_messages(
        user_id, session.session_id
    )
        """
        print(practices)
    
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
    print("🔍 AgentCore Memory - 找回丢失的Session Demo")
    print("="*60)
    
    demo = FindLostSessionDemo()
    
    # 场景1: 忘记session_id的情况
    user_id, session_id = demo.scenario_1_forget_session_id()
    
    # 场景2: 如何列出所有session
    demo.scenario_2_list_all_sessions()
    
    # 场景3: 最佳实践
    demo.scenario_3_best_practices()
    
    # 总结
    print(f"\n{'='*60}")
    print("📊 总结")
    print(f"{'='*60}")
    
    summary = f"""
问题: 如果忘记了session_id，短期记忆能找回吗？
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

答案: ❌ 不能直接找回

原因:
  • list_events() 必须同时提供 actor_id 和 session_id
  • 没有 API 可以列出某个用户的所有 session
  • 短期记忆严格按 session 隔离

替代方案:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. ✅ 通过长期记忆找回关键信息
   - 长期记忆不需要 session_id
   - 但只包含提取的知识，不是完整对话

2. ✅ 在应用层管理 session_id
   - 在自己的数据库中记录 user_id ↔ session_id 映射
   - 这是推荐的最佳实践

3. ✅ 使用可预测的 session_id 命名
   - 例如: f"{{user_id}}_chat_{{date}}"
   - 即使"忘记"也能重新构造

关键教训:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚠️  Session ID 很重要，必须妥善管理！
✅  在应用层维护 session 元数据
✅  不要完全依赖 AgentCore 来管理 session
✅  长期记忆是备份方案，但不能替代短期记忆

实际发现的session_id: {session_id}
（如果你记下来，现在就可以用它检索短期记忆了！）
    """
    print(summary)
    
    print(f"\n✅ Demo完成！")


if __name__ == "__main__":
    main()
