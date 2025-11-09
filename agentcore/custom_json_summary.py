"""
使用Custom Memory Strategy强制Summary使用JSON格式
"""
from bedrock_agentcore.memory import MemoryClient
from botocore.exceptions import ClientError
import time

def create_custom_json_summary_memory():
    """创建使用JSON格式的自定义摘要策略"""
    client = MemoryClient(region_name="us-west-2")
    
    # 自定义提取Prompt - 要求输出JSON格式
    CUSTOM_JSON_SUMMARY_PROMPT = """
请分析对话内容并生成JSON格式的摘要。

输出格式要求（必须是有效的JSON）:
{
  "user_info": {
    "name": "用户姓名",
    "age": 年龄,
    "occupation": "职业",
    "location": "地点"
  },
  "requirements": {
    "product_type": "产品类型",
    "budget": "预算范围",
    "key_features": ["特性1", "特性2"]
  },
  "preferences": {
    "brands": ["品牌1", "品牌2"],
    "priorities": ["优先级1", "优先级2"]
  },
  "behaviors": {
    "browsed_products": ["产品1", "产品2"],
    "purchase_intent": "购买意向描述"
  }
}

请严格按照上述JSON格式输出，不要添加任何额外的文本或标记。
"""
    
    memory_name = "CustomJSONSummaryDemo"
    
    try:
        print(f"\n📝 创建自定义JSON摘要策略Memory: {memory_name}")
        memory = client.create_memory_and_wait(
            name=memory_name,
            description="使用JSON格式的自定义摘要策略Demo",
            strategies=[
                # 1. 保留语义记忆（纯文本）
                {
                    "semanticMemoryStrategy": {
                        "name": "UserFacts",
                        "namespaces": ["/facts/{actorId}"]
                    }
                },
                # 2. 保留用户偏好（JSON）
                {
                    "userPreferenceMemoryStrategy": {
                        "name": "UserPreferences",
                        "namespaces": ["/preferences/{actorId}"]
                    }
                },
                # 3. 自定义摘要策略 - 强制使用JSON
                {
                    "customMemoryStrategy": {
                        "name": "JSONSummary",
                        "namespaces": ["/json_summaries/{actorId}/{sessionId}"],
                        "configuration": {
                            "semanticOverride": {
                                "extraction": {
                                    "appendToPrompt": CUSTOM_JSON_SUMMARY_PROMPT,
                                    "modelId": "anthropic.claude-3-sonnet-20240229-v1:0"
                                }
                            }
                        }
                    }
                }
            ],
            event_expiry_days=180
        )
        memory_id = memory["id"]
        print(f"✅ Memory创建成功，ID: {memory_id}")
        return memory_id
        
    except ClientError as e:
        if "already exists" in str(e):
            print(f"⚠️  Memory已存在，获取现有ID")
            memories = client.list_memories()
            memory_id = next((m['id'] for m in memories if memory_name in m['id']), None)
            print(f"✅ 使用现有Memory ID: {memory_id}")
            return memory_id
        else:
            raise e


def test_custom_json_summary():
    """测试自定义JSON摘要策略"""
    client = MemoryClient(region_name="us-west-2")
    
    # 创建Memory
    memory_id = create_custom_json_summary_memory()
    
    # 添加测试对话
    user_id = "test_user_001"
    session_id = f"test_session_{int(time.time())}"
    
    print(f"\n👤 添加测试对话数据...")
    
    conversations = [
        ("我是李明，30岁，在上海做产品经理", "USER"),
        ("您好李明！很高兴为您服务。", "ASSISTANT"),
        ("我想买一台MacBook，预算20000左右，主要用于办公和设计", "USER"),
        ("MacBook是很好的选择！推荐MacBook Pro M3，性能强劲。", "ASSISTANT"),
        ("我比较看重续航和屏幕质量，经常需要外出办公", "USER"),
        ("MacBook Pro的续航可达18小时，Retina显示屏色彩准确，非常适合您。", "ASSISTANT")
    ]
    
    for msg, role in conversations:
        try:
            client.create_event(
                memory_id=memory_id,
                actor_id=user_id,
                session_id=session_id,
                messages=[(msg, role)]
            )
            print(f"  ✅ 添加消息: {msg[:30]}...")
            time.sleep(1)
        except Exception as e:
            print(f"  ❌ 添加失败: {str(e)}")
    
    # 等待长期记忆生成
    print(f"\n⏳ 等待AgentCore生成长期记忆 (60秒)...")
    time.sleep(60)
    
    # 检索并对比不同策略的格式
    print(f"\n🔍 检索不同策略的记忆格式:")
    print("="*60)
    
    # 检索自定义JSON摘要
    print("\n📋 自定义JSON摘要策略:")
    try:
        json_summaries = client.retrieve_memories(
            memory_id=memory_id,
            namespace=f"/json_summaries/{user_id}",
            query="用户信息和需求"
        )
        
        if json_summaries:
            print(f"  ✅ 检索到 {len(json_summaries)} 条记忆")
            for i, memory in enumerate(json_summaries[:1], 1):
                content = memory.get('content', {}).get('text', '')
                print(f"\n  记忆 {i}:")
                print(f"  {content}")
                
                # 检查是否为有效JSON
                import json
                try:
                    parsed = json.loads(content)
                    print(f"\n  ✅ 成功解析为JSON!")
                    print(f"  JSON结构: {list(parsed.keys())}")
                except:
                    print(f"\n  ⚠️ 不是有效的JSON格式")
        else:
            print("  ⚠️ 未找到JSON摘要记忆")
    except Exception as e:
        print(f"  ❌ 检索失败: {str(e)}")
    
    print(f"\n✅ 测试完成！")
    print("\n💡 总结:")
    print("  - 内置策略的格式是固定的（Semantic=文本, Preference=JSON, Summary=XML）")
    print("  - 使用Custom Memory Strategy可以自定义输出格式")
    print("  - 通过自定义Prompt可以强制要求任何格式（JSON/XML/YAML等）")


if __name__ == "__main__":
    test_custom_json_summary()
