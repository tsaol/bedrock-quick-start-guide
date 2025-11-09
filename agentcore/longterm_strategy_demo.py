"""
AgentCore 长期记忆策略对比Demo
展示四种长期记忆策略的不同效果
"""
import os
import json
import time
from datetime import datetime, timedelta
from bedrock_agentcore.memory import MemoryClient
from botocore.exceptions import ClientError

class LongTermStrategyDemo:
    def __init__(self, region="us-west-2"):
        self.memory_client = MemoryClient(region_name=region)
        self.memory_id = None
        
    def setup_comprehensive_memory(self):
        """创建包含四种长期记忆策略的Memory"""
        memory_name = "LongTermStrategyComparison"
        
        try:
            print(f"\n📝 创建长期记忆策略对比系统: {memory_name}")
            memory = self.memory_client.create_memory_and_wait(
                name=memory_name,
                description="长期记忆策略对比Demo - 展示四种策略效果",
                strategies=[
                    # 1. 语义记忆策略 - 存储事实性知识
                    {
                        "semanticMemoryStrategy": {
                            "name": "UserFacts",
                            "namespaces": ["/facts/{actorId}"]
                        }
                    },
                    # 2. 用户偏好策略 - 存储个性化偏好
                    {
                        "userPreferenceMemoryStrategy": {
                            "name": "UserPreferences", 
                            "namespaces": ["/preferences/{actorId}"]
                        }
                    },
                    # 3. 摘要策略 - 生成会话摘要
                    {
                        "summaryMemoryStrategy": {
                            "name": "SessionSummary",
                            "namespaces": ["/summaries/{actorId}/{sessionId}"]
                        }
                    }
                    # 注意：自定义策略需要额外配置，这里先使用前三种内置策略
                ],
                event_expiry_days=365
            )
            self.memory_id = memory["id"]
            print(f"✅ 长期记忆系统创建成功，ID: {self.memory_id}")
            
        except ClientError as e:
            if "already exists" in str(e):
                print(f"⚠️  记忆系统已存在，获取现有ID")
                memories = self.memory_client.list_memories()
                self.memory_id = next((m['id'] for m in memories if memory_name in m['id']), None)
                print(f"✅ 使用现有记忆ID: {self.memory_id}")
            else:
                raise e
                
        return self.memory_id
    
    def create_event_with_retry(self, memory_id, actor_id, session_id, messages, max_retries=3):
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
                    wait_time = (2 ** attempt) + 1
                    print(f"    ⏳ 限流，等待 {wait_time} 秒后重试...")
                    time.sleep(wait_time)
                else:
                    print(f"    ❌ 创建事件失败: {str(e)}")
                    return False
        return False
    
    def create_user_conversations(self, user_id, user_data):
        """为用户创建对话数据"""
        print(f"\n👤 创建用户 {user_id} 的对话数据...")
        
        session_id = f"session_{user_id}_{datetime.now().strftime('%Y%m%d')}"
        
        # 1. 存储用户基本信息
        profile_msg = f"用户档案：{json.dumps(user_data['profile'], ensure_ascii=False)}"
        success = self.create_event_with_retry(
            self.memory_id, user_id, session_id, [(profile_msg, "USER")]
        )
        if success:
            print(f"  ✅ 用户档案已存储")
        
        time.sleep(1)
        
        # 2. 存储多轮对话
        for i, conversation in enumerate(user_data['conversations'], 1):
            # 用户消息
            user_success = self.create_event_with_retry(
                self.memory_id, user_id, session_id, [(conversation["user"], "USER")]
            )
            
            if user_success:
                time.sleep(0.5)
                # 助手回复
                assistant_success = self.create_event_with_retry(
                    self.memory_id, user_id, session_id, [(conversation["assistant"], "ASSISTANT")]
                )
                
                if assistant_success:
                    print(f"  ✅ 对话 {i}: {conversation['user'][:40]}...")
                else:
                    print(f"  ❌ 对话 {i} 助手回复失败")
            else:
                print(f"  ❌ 对话 {i} 用户消息失败")
            
            time.sleep(1)
        
        # 3. 存储行为数据
        for behavior in user_data.get('behaviors', []):
            behavior_msg = f"用户行为：{json.dumps(behavior, ensure_ascii=False)}"
            success = self.create_event_with_retry(
                self.memory_id, user_id, f"behavior_{user_id}", [(behavior_msg, "USER")]
            )
            if success:
                print(f"  ✅ 行为记录: {behavior['action']}")
            time.sleep(0.5)
        
        print(f"✅ 用户 {user_id} 数据创建完成")
        return session_id
    
    def retrieve_memories_by_strategy(self, user_id, query):
        """按不同策略检索记忆"""
        print(f"\n🔍 检索用户 {user_id} 的记忆: '{query}'")
        print("="*50)
        
        results = {}
        
        # 1. 检索语义记忆（事实性知识）
        print("📚 1. 语义记忆策略 (Semantic Memory)")
        try:
            semantic_memories = self.memory_client.retrieve_memories(
                memory_id=self.memory_id,
                namespace=f"/facts/{user_id}",
                query=query
            )
            
            if semantic_memories:
                print(f"  ✅ 检索到 {len(semantic_memories)} 条语义记忆:")
                for i, memory in enumerate(semantic_memories[:3], 1):
                    content = self.extract_content(memory)
                    print(f"    {i}. {content[:80]}...")
                results['semantic'] = semantic_memories
            else:
                print("  ⚠️ 未找到语义记忆")
                results['semantic'] = []
                
        except Exception as e:
            print(f"  ❌ 语义记忆检索失败: {str(e)}")
            results['semantic'] = []
        
        time.sleep(1)
        
        # 2. 检索用户偏好记忆
        print("\n🎯 2. 用户偏好策略 (User Preference Memory)")
        try:
            preference_memories = self.memory_client.retrieve_memories(
                memory_id=self.memory_id,
                namespace=f"/preferences/{user_id}",
                query=query
            )
            
            if preference_memories:
                print(f"  ✅ 检索到 {len(preference_memories)} 条偏好记忆:")
                for i, memory in enumerate(preference_memories[:3], 1):
                    content = self.extract_content(memory)
                    print(f"    {i}. {content[:80]}...")
                results['preferences'] = preference_memories
            else:
                print("  ⚠️ 未找到偏好记忆")
                results['preferences'] = []
                
        except Exception as e:
            print(f"  ❌ 偏好记忆检索失败: {str(e)}")
            results['preferences'] = []
        
        time.sleep(1)
        
        # 3. 检索摘要记忆
        print("\n📋 3. 摘要策略 (Summary Memory)")
        try:
            # 尝试检索会话摘要
            summary_memories = self.memory_client.retrieve_memories(
                memory_id=self.memory_id,
                namespace=f"/summaries/{user_id}",
                query=query
            )
            
            if summary_memories:
                print(f"  ✅ 检索到 {len(summary_memories)} 条摘要记忆:")
                for i, memory in enumerate(summary_memories[:2], 1):
                    content = self.extract_content(memory)
                    print(f"    {i}. {content[:100]}...")
                results['summaries'] = summary_memories
            else:
                print("  ⚠️ 未找到摘要记忆")
                results['summaries'] = []
                
        except Exception as e:
            print(f"  ❌ 摘要记忆检索失败: {str(e)}")
            results['summaries'] = []
        
        return results
    
    def extract_content(self, memory_record):
        """提取记忆记录的内容"""
        if isinstance(memory_record, dict):
            content = memory_record.get('content', {})
            if isinstance(content, dict):
                return content.get('text', str(memory_record))
            else:
                return str(content)
        else:
            return str(memory_record)
    
    def compare_strategy_results(self, all_results):
        """对比不同策略的检索结果"""
        print(f"\n{'='*60}")
        print("📊 长期记忆策略效果对比")
        print(f"{'='*60}")
        
        strategy_stats = {
            'semantic': {'total': 0, 'users_with_data': 0},
            'preferences': {'total': 0, 'users_with_data': 0},
            'summaries': {'total': 0, 'users_with_data': 0}
        }
        
        for user_id, results in all_results.items():
            print(f"\n👤 用户 {user_id} 记忆分布:")
            
            for strategy, memories in results.items():
                count = len(memories)
                strategy_stats[strategy]['total'] += count
                if count > 0:
                    strategy_stats[strategy]['users_with_data'] += 1
                
                print(f"  {strategy:12}: {count:2d} 条记忆")
        
        print(f"\n📈 策略效果统计:")
        print(f"{'策略类型':<15} {'总记忆数':<8} {'有数据用户':<10} {'平均每用户':<10}")
        print("-" * 50)
        
        total_users = len(all_results)
        for strategy, stats in strategy_stats.items():
            avg_per_user = stats['total'] / total_users if total_users > 0 else 0
            print(f"{strategy:<15} {stats['total']:<8} {stats['users_with_data']:<10} {avg_per_user:<10.1f}")
        
        print(f"\n💡 策略特点分析:")
        print("📚 语义记忆: 存储客观事实，如用户基本信息、行为记录")
        print("🎯 偏好记忆: 学习用户喜好，如品牌偏好、价格敏感度")
        print("📋 摘要记忆: 生成对话要点，便于快速回顾会话内容")


def create_demo_users():
    """创建4个演示用户的数据"""
    users = {
        "uid001": {
            "profile": {
                "name": "张三",
                "age": 28,
                "occupation": "软件工程师",
                "location": "北京",
                "interests": ["编程", "游戏", "科技"]
            },
            "conversations": [
                {
                    "user": "我想买一台适合编程的笔记本电脑，预算15000左右",
                    "assistant": "推荐ThinkPad X1 Carbon或MacBook Pro，都很适合编程工作，性能强劲且便携。"
                },
                {
                    "user": "我比较偏好ThinkPad，因为键盘手感好，而且我习惯用Linux系统",
                    "assistant": "ThinkPad确实是程序员的经典选择，键盘手感一流，对Linux支持也很好。"
                },
                {
                    "user": "我平时主要做Python和Java开发，偶尔会跑一些机器学习模型",
                    "assistant": "那建议选择16GB内存以上的配置，机器学习对内存要求较高。"
                },
                {
                    "user": "我不太在意外观，更看重性能和稳定性",
                    "assistant": "理解，ThinkPad的商务系列就是以稳定性著称，很适合你的需求。"
                }
            ],
            "behaviors": [
                {"action": "浏览商品", "item": "ThinkPad X1 Carbon", "duration": "5分钟"},
                {"action": "加入购物车", "item": "ThinkPad X1 Carbon 16GB版本", "price": 14999},
                {"action": "查看评价", "item": "ThinkPad X1 Carbon", "rating": 4.8}
            ]
        },
        
        "uid002": {
            "profile": {
                "name": "李四",
                "age": 25,
                "occupation": "设计师",
                "location": "上海",
                "interests": ["设计", "摄影", "艺术"]
            },
            "conversations": [
                {
                    "user": "我需要一台显示效果好的电脑，主要用于平面设计和视频剪辑",
                    "assistant": "建议选择MacBook Pro或者配置高端显卡的工作站，色彩准确度很重要。"
                },
                {
                    "user": "我比较喜欢苹果的生态系统，iPhone和iPad都在用",
                    "assistant": "那MacBook Pro是最佳选择，与你现有设备无缝协作，工作效率会很高。"
                },
                {
                    "user": "预算大概20000左右，希望能用个3-4年不落后",
                    "assistant": "建议选择M3 Pro芯片的MacBook Pro，性能强劲，未来几年都不会过时。"
                },
                {
                    "user": "我对颜色要求很高，听说苹果的屏幕色彩很准",
                    "assistant": "是的，MacBook Pro的Liquid Retina XDR显示屏支持P3广色域，非常适合专业设计工作。"
                }
            ],
            "behaviors": [
                {"action": "浏览商品", "item": "MacBook Pro M3", "duration": "8分钟"},
                {"action": "对比产品", "items": ["MacBook Pro 14寸", "MacBook Pro 16寸"]},
                {"action": "查看配置", "item": "MacBook Pro M3 Pro 18GB", "price": 19999}
            ]
        },
        
        "uid003": {
            "profile": {
                "name": "王五",
                "age": 22,
                "occupation": "大学生",
                "location": "广州",
                "interests": ["游戏", "动漫", "音乐"]
            },
            "conversations": [
                {
                    "user": "我想要一台能玩游戏的笔记本，但预算不多，大概8000块",
                    "assistant": "可以考虑搭载RTX 4060的游戏本，性价比不错，能流畅运行大部分游戏。"
                },
                {
                    "user": "我主要玩英雄联盟、原神这类游戏，对画质要求不是特别高",
                    "assistant": "这些游戏对配置要求不算太高，GTX 1660Ti或RTX 3050就能很好胜任。"
                },
                {
                    "user": "我比较在意散热，不希望玩游戏时电脑太烫手",
                    "assistant": "建议选择双风扇散热设计的机型，华硕天选、联想拯救者系列散热都不错。"
                },
                {
                    "user": "外观希望炫酷一点，最好有RGB灯效",
                    "assistant": "游戏本通常都有RGB背光键盘，外观设计也比较酷炫，符合你的需求。"
                }
            ],
            "behaviors": [
                {"action": "浏览商品", "item": "华硕天选4", "duration": "10分钟"},
                {"action": "观看评测", "item": "联想拯救者Y7000P", "duration": "15分钟"},
                {"action": "价格对比", "items": ["华硕天选4", "联想拯救者", "惠普暗影精灵"]}
            ]
        },
        
        "uid004": {
            "profile": {
                "name": "赵六",
                "age": 35,
                "occupation": "商务人士",
                "location": "深圳",
                "interests": ["商务", "旅行", "理财"]
            },
            "conversations": [
                {
                    "user": "我需要一台轻薄的商务笔记本，经常出差携带",
                    "assistant": "推荐超极本系列，如Dell XPS、华为MateBook等，重量通常在1.3kg以下。"
                },
                {
                    "user": "续航能力很重要，希望能支撑一整天的会议和办公",
                    "assistant": "建议选择低功耗处理器的机型，续航可达10小时以上，满足全天办公需求。"
                },
                {
                    "user": "我主要用Office办公，偶尔需要视频会议，对性能要求不高",
                    "assistant": "那集成显卡就足够了，重点关注续航、重量和屏幕质量即可。"
                },
                {
                    "user": "预算12000左右，希望外观商务一些，不要太花哨",
                    "user": "预算12000左右，希望外观商务一些，不要太花哨",
                    "assistant": "Dell XPS 13或华为MateBook X Pro都很符合，外观简约商务，品质可靠。"
                }
            ],
            "behaviors": [
                {"action": "浏览商品", "item": "Dell XPS 13", "duration": "6分钟"},
                {"action": "查看参数", "item": "华为MateBook X Pro", "specs": ["重量1.26kg", "续航12小时"]},
                {"action": "咨询客服", "question": "是否支持企业采购和发票"}
            ]
        }
    }
    
    return users


def main():
    print("🧠 AgentCore 长期记忆策略对比Demo")
    print("="*60)
    
    # 初始化Demo
    demo = LongTermStrategyDemo()
    
    # 1. 设置长期记忆系统
    demo.setup_comprehensive_memory()
    
    # 2. 创建4个用户数据
    users = create_demo_users()
    
    # 3. 为每个用户创建对话数据
    for user_id, user_data in users.items():
        print(f"\n{'='*60}")
        print(f"🔄 处理用户: {user_data['profile']['name']} ({user_id})")
        print(f"{'='*60}")
        
        demo.create_user_conversations(user_id, user_data)
        
        print("⏳ 等待数据处理...")
        time.sleep(2)
    
    # 4. 等待长期记忆生成
    print(f"\n{'='*60}")
    print("⏳ 等待AgentCore生成长期记忆 (60秒)...")
    print("💡 AgentCore需要时间分析对话并提取不同类型的记忆")
    print(f"{'='*60}")
    time.sleep(60)
    
    # 5. 测试不同策略的检索效果
    test_queries = [
        "笔记本电脑推荐",
        "用户偏好和需求",
        "购买意向和预算"
    ]
    
    all_results = {}
    
    for query in test_queries:
        print(f"\n{'='*80}")
        print(f"🔍 测试查询: '{query}'")
        print(f"{'='*80}")
        
        for user_id in users.keys():
            results = demo.retrieve_memories_by_strategy(user_id, query)
            if user_id not in all_results:
                all_results[user_id] = {'semantic': [], 'preferences': [], 'summaries': []}
            
            # 合并结果
            for strategy, memories in results.items():
                all_results[user_id][strategy].extend(memories)
            
            time.sleep(2)
    
    # 6. 对比分析
    demo.compare_strategy_results(all_results)
    
    print(f"\n✅ 长期记忆策略对比Demo完成！")
    print("💡 不同策略提取的记忆类型和内容各有特点，可根据应用场景选择合适的策略组合")


if __name__ == "__main__":
    main()