"""
AgentCore 长期记忆功能学习Demo
演示如何存储和检索用户偏好、对话信息
"""
import os
import json
import time
from datetime import datetime, timedelta
from bedrock_agentcore.memory import MemoryClient
from botocore.exceptions import ClientError

class LongTermMemoryDemo:
    def __init__(self, region="us-west-2"):
        self.memory_client = MemoryClient(region_name=region)
        self.memory_id = None
        
    def setup_long_term_memory(self):
        """创建长期记忆存储，配置多种策略"""
        memory_name = "LongTermMemoryDemo"
        
        try:
            print(f"\n📝 创建长期记忆存储: {memory_name}")
            memory = self.memory_client.create_memory_and_wait(
                name=memory_name,
                description="长期记忆Demo - 存储用户偏好和对话信息",
                strategies=[
                    {
                        "semanticMemoryStrategy": {
                            "name": "userFacts",
                            "namespaces": ["/facts/{actorId}"]
                        }
                    },
                    {
                        "userPreferenceMemoryStrategy": {
                            "name": "userPreferences", 
                            "namespaces": ["/preferences/{actorId}"]
                        }
                    }
                ],
                event_expiry_days=365  # 长期保存
            )
            self.memory_id = memory["id"]
            print(f"✅ 长期记忆创建成功，ID: {self.memory_id}")
            
        except ClientError as e:
            if "already exists" in str(e):
                print(f"⚠️  记忆存储已存在，获取现有ID")
                memories = self.memory_client.list_memories()
                self.memory_id = next((m['id'] for m in memories if memory_name in m['id']), None)
                print(f"✅ 使用现有记忆ID: {self.memory_id}")
            else:
                raise e
                
        return self.memory_id
    
    def create_event_with_retry(self, memory_id, actor_id, session_id, messages, max_retries=5):
        """带重试机制的事件创建"""
        for attempt in range(max_retries):
            try:
                self.memory_client.create_event(
                    memory_id=memory_id,
                    actor_id=actor_id,
                    session_id=session_id,
                    messages=messages
                )
                return True
            except Exception as e:
                if "ThrottledException" in str(e) and attempt < max_retries - 1:
                    wait_time = (2 ** attempt) + 1  # 指数退避
                    print(f"    ⏳ 限流，等待 {wait_time} 秒后重试...")
                    time.sleep(wait_time)
                else:
                    print(f"    ❌ 创建事件失败: {str(e)}")
                    return False
        return False
    
    def create_user_conversations(self, user_id, conversations):
        """为用户创建多轮对话，用于长期记忆提取"""
        print(f"\n👤 为用户 {user_id} 创建对话历史...")
        
        for i, conv in enumerate(conversations, 1):
            session_id = f"session_{user_id}_{i}"
            
            # 存储用户消息
            success1 = self.create_event_with_retry(
                self.memory_id, user_id, session_id, [(conv["user"], "USER")]
            )
            
            if success1:
                time.sleep(1)  # 间隔
                # 存储助手回复
                success2 = self.create_event_with_retry(
                    self.memory_id, user_id, session_id, [(conv["assistant"], "ASSISTANT")]
                )
                
                if success2:
                    print(f"  ✅ 会话 {i}: {conv['user'][:30]}...")
                else:
                    print(f"  ❌ 会话 {i} 助手回复存储失败")
            else:
                print(f"  ❌ 会话 {i} 用户消息存储失败")
            
            time.sleep(2)  # 增加延迟避免限流
            
        print(f"✅ 用户 {user_id} 的对话处理完成")
    
    def store_user_preferences(self, user_id, preferences):
        """直接存储用户偏好信息"""
        print(f"\n💾 存储用户 {user_id} 的偏好信息...")
        
        for category, prefs in preferences.items():
            pref_text = f"{category}偏好: {json.dumps(prefs, ensure_ascii=False)}"
            
            success = self.create_event_with_retry(
                self.memory_id, user_id, f"preferences_{user_id}", [(pref_text, "USER")]
            )
            
            if success:
                print(f"  ✅ {category}偏好已存储")
            else:
                print(f"  ❌ {category}偏好存储失败")
            
            time.sleep(1)  # 避免限流
            
        print(f"✅ 用户 {user_id} 的偏好信息处理完成")
    
    def retrieve_user_memories(self, user_id, query):
        """检索用户的长期记忆"""
        print(f"\n🔍 检索用户 {user_id} 的记忆: '{query}'")
        
        try:
            # 检索语义记忆
            semantic_memories = self.memory_client.retrieve_memories(
                memory_id=self.memory_id,
                namespace=f"/facts/{user_id}",
                query=query
            )
            
            if semantic_memories:
                print(f"  📚 语义记忆检索结果 ({len(semantic_memories)} 条):")
                for i, memory in enumerate(semantic_memories[:3], 1):
                    content = str(memory)[:80] if memory else "N/A"
                    print(f"    {i}. {content}...")
            else:
                print("  ⚠️ 未找到相关语义记忆")
            
            # 检索用户偏好记忆
            preference_memories = self.memory_client.retrieve_memories(
                memory_id=self.memory_id,
                namespace=f"/preferences/{user_id}",
                query=query
            )
            
            if preference_memories:
                print(f"  🎯 偏好记忆检索结果 ({len(preference_memories)} 条):")
                for i, memory in enumerate(preference_memories[:3], 1):
                    content = str(memory)[:80] if memory else "N/A"
                    print(f"    {i}. {content}...")
            else:
                print("  ⚠️ 未找到相关偏好记忆")
                
        except Exception as e:
            print(f"  ❌ 检索失败: {str(e)}")
    
    def get_user_conversation_history(self, user_id, k=5):
        """获取用户最近的对话历史"""
        print(f"\n📖 获取用户 {user_id} 最近 {k} 轮对话...")
        
        try:
            recent_conversations = self.memory_client.get_last_k_turns(
                memory_id=self.memory_id,
                actor_id=user_id,
                session_id=f"session_{user_id}_1",  # 获取第一个会话的历史
                k=k
            )
            
            if recent_conversations:
                print(f"  ✅ 找到 {len(recent_conversations)} 条对话记录:")
                for i, conv in enumerate(recent_conversations[:3], 1):
                    content = str(conv)[:60] if conv else "N/A"
                    print(f"    {i}. {content}...")
            else:
                print("  ⚠️ 未找到对话历史")
                
        except Exception as e:
            print(f"  ❌ 获取对话历史失败: {str(e)}")


def create_demo_users():
    """创建演示用户数据"""
    users = {
        "alice_programmer": {
            "name": "Alice - 程序员",
            "conversations": [
                {
                    "user": "我是一名Python开发者，想学习机器学习",
                    "assistant": "很好！Python是机器学习的热门语言。建议从scikit-learn开始，然后学习TensorFlow或PyTorch。"
                },
                {
                    "user": "我比较喜欢深度学习，有什么好的GPU推荐吗？",
                    "assistant": "对于深度学习，推荐NVIDIA RTX 4090或A100。RTX 4090性价比高，适合个人开发者。"
                },
                {
                    "user": "我的预算有限，有便宜一些的选择吗？",
                    "assistant": "可以考虑RTX 3060 Ti或者使用云服务如AWS EC2 P3实例，按需付费更经济。"
                },
                {
                    "user": "我平时喜欢用Jupyter Notebook开发",
                    "assistant": "Jupyter很适合机器学习实验！建议配合JupyterLab和一些扩展插件提高效率。"
                }
            ],
            "preferences": {
                "技术栈": ["Python", "机器学习", "深度学习"],
                "工具": ["Jupyter Notebook", "JupyterLab"],
                "硬件": ["NVIDIA GPU", "RTX系列"],
                "预算": "有限，偏好性价比",
                "学习方向": "从scikit-learn到深度学习"
            }
        },
        
        "bob_designer": {
            "name": "Bob - 设计师", 
            "conversations": [
                {
                    "user": "我是UI/UX设计师，想了解最新的设计趋势",
                    "assistant": "2024年的设计趋势包括极简主义、暗色模式、微交互和AI辅助设计。"
                },
                {
                    "user": "我主要用Figma和Adobe XD，哪个更好？",
                    "assistant": "Figma在协作和云端同步方面更强，Adobe XD在Adobe生态系统集成更好。推荐Figma。"
                },
                {
                    "user": "我想学习一些前端开发，从哪里开始？",
                    "assistant": "建议从HTML/CSS开始，然后学习JavaScript。作为设计师，重点关注CSS动画和响应式设计。"
                },
                {
                    "user": "我喜欢苹果的设计风格，简洁优雅",
                    "assistant": "苹果的设计哲学确实值得学习！重点是留白、层次感和一致性。可以研究Human Interface Guidelines。"
                }
            ],
            "preferences": {
                "职业": "UI/UX设计师",
                "工具": ["Figma", "Adobe XD", "Adobe Creative Suite"],
                "设计风格": ["极简主义", "苹果风格", "简洁优雅"],
                "技术兴趣": ["前端开发", "CSS动画", "响应式设计"],
                "关注趋势": ["暗色模式", "微交互", "AI辅助设计"]
            }
        },
        
        "carol_student": {
            "name": "Carol - 学生",
            "conversations": [
                {
                    "user": "我是计算机科学专业的大三学生，在准备实习",
                    "assistant": "很好！建议重点准备算法和数据结构，同时完善GitHub项目展示。"
                },
                {
                    "user": "我对人工智能很感兴趣，但数学基础一般",
                    "assistant": "AI确实需要数学基础。建议先补强线性代数、概率论和微积分，可以通过在线课程学习。"
                },
                {
                    "user": "我比较内向，担心面试表现不好",
                    "assistant": "面试技巧可以练习！建议多做模拟面试，准备常见问题，展示你的项目经验。"
                },
                {
                    "user": "我希望将来能在大厂工作，比如Google或微软",
                    "assistant": "大厂竞争激烈但机会很好！重点提升编程能力，参与开源项目，保持学习热情。"
                }
            ],
            "preferences": {
                "身份": "计算机科学专业大三学生",
                "目标": ["准备实习", "大厂工作", "Google", "微软"],
                "兴趣领域": ["人工智能", "算法", "数据结构"],
                "学习需求": ["数学基础", "线性代数", "概率论", "微积分"],
                "性格": "内向，需要面试技巧指导",
                "发展方向": ["开源项目", "编程能力提升"]
            }
        }
    }
    
    return users


def main():
    print("🚀 AgentCore 长期记忆功能学习Demo")
    print("="*60)
    
    # 初始化Demo
    demo = LongTermMemoryDemo()
    
    # 1. 设置长期记忆存储
    demo.setup_long_term_memory()
    
    # 2. 创建演示用户
    users = create_demo_users()
    
    # 3. 为每个用户存储对话和偏好
    for user_id, user_data in users.items():
        print(f"\n{'='*60}")
        print(f"🔄 处理用户: {user_data['name']}")
        print(f"{'='*60}")
        
        # 存储对话历史
        demo.create_user_conversations(user_id, user_data["conversations"])
        
        # 存储用户偏好
        demo.store_user_preferences(user_id, user_data["preferences"])
        
        # 等待一段时间让AgentCore处理数据
        print("⏳ 等待AgentCore处理数据...")
        time.sleep(3)
    
    # 4. 等待长期记忆生成
    print(f"\n{'='*60}")
    print("⏳ 等待AgentCore生成长期记忆 (30秒)...")
    print("💡 AgentCore需要时间从对话中提取关键信息到长期记忆")
    print(f"{'='*60}")
    time.sleep(30)
    
    # 5. 测试记忆检索
    print(f"\n{'='*60}")
    print("🔍 测试长期记忆检索功能")
    print(f"{'='*60}")
    
    test_queries = [
        ("alice_programmer", "机器学习"),
        ("alice_programmer", "GPU推荐"),
        ("bob_designer", "设计工具"),
        ("bob_designer", "苹果设计"),
        ("carol_student", "面试准备"),
        ("carol_student", "人工智能学习")
    ]
    
    for user_id, query in test_queries:
        demo.retrieve_user_memories(user_id, query)
        time.sleep(2)
    
    # 6. 测试对话历史检索
    print(f"\n{'='*60}")
    print("📚 测试对话历史检索")
    print(f"{'='*60}")
    
    for user_id in users.keys():
        demo.get_user_conversation_history(user_id, k=3)
        time.sleep(1)
    
    print(f"\n✅ 长期记忆功能Demo完成！")
    print("💡 长期记忆需要时间积累，多次运行可以看到更好的效果")


if __name__ == "__main__":
    main()