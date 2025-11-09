"""
检查AgentCore Memory不同策略返回的实际数据格式
"""
import json
from bedrock_agentcore.memory import MemoryClient

def inspect_memory_formats():
    """检查不同策略的返回格式"""
    client = MemoryClient(region_name="us-west-2")
    
    # 使用之前创建的Memory
    memory_id = "LongTermStrategyComparison-65gG8z6XFf"
    user_id = "uid001"
    
    print("🔍 检查AgentCore Memory返回的数据格式")
    print("="*60)
    
    # 1. 检查语义记忆格式
    print("\n📚 1. Semantic Memory 返回格式:")
    print("-"*60)
    try:
        semantic_memories = client.retrieve_memories(
            memory_id=memory_id,
            namespace=f"/facts/{user_id}",
            query="笔记本电脑"
        )
        
        if semantic_memories:
            print(f"✅ 检索到 {len(semantic_memories)} 条记忆")
            print("\n第一条记忆的原始结构:")
            print(semantic_memories[0])
            
            print("\n数据类型分析:")
            print(f"  - 返回类型: {type(semantic_memories)}")
            print(f"  - 单条记忆类型: {type(semantic_memories[0])}")
            
            if isinstance(semantic_memories[0], dict):
                print(f"  - 包含的键: {list(semantic_memories[0].keys())}")
                
                content = semantic_memories[0].get('content', {})
                print(f"  - content类型: {type(content)}")
                if isinstance(content, dict):
                    print(f"  - content的键: {list(content.keys())}")
                    text = content.get('text', '')
                    print(f"  - text内容: {text[:100]}...")
                    print(f"  - text是否为JSON: {is_json(text)}")
        else:
            print("⚠️ 未找到语义记忆")
    except Exception as e:
        print(f"❌ 检索失败: {str(e)}")
    
    # 2. 检查用户偏好记忆格式
    print("\n🎯 2. User Preference Memory 返回格式:")
    print("-"*60)
    try:
        preference_memories = client.retrieve_memories(
            memory_id=memory_id,
            namespace=f"/preferences/{user_id}",
            query="用户偏好"
        )
        
        if preference_memories:
            print(f"✅ 检索到 {len(preference_memories)} 条记忆")
            print("\n第一条记忆的原始结构:")
            print(preference_memories[0])
            
            if isinstance(preference_memories[0], dict):
                content = preference_memories[0].get('content', {})
                if isinstance(content, dict):
                    text = content.get('text', '')
                    print(f"\n  - text内容: {text[:200]}...")
                    print(f"  - text是否为JSON: {is_json(text)}")
                    
                    if is_json(text):
                        parsed = json.loads(text)
                        print(f"  - 解析后的JSON结构: {list(parsed.keys())}")
        else:
            print("⚠️ 未找到偏好记忆")
    except Exception as e:
        print(f"❌ 检索失败: {str(e)}")
    
    # 3. 检查摘要记忆格式
    print("\n📋 3. Summary Memory 返回格式:")
    print("-"*60)
    try:
        summary_memories = client.retrieve_memories(
            memory_id=memory_id,
            namespace=f"/summaries/{user_id}",
            query="用户信息"
        )
        
        if summary_memories:
            print(f"✅ 检索到 {len(summary_memories)} 条记忆")
            print("\n第一条记忆的原始结构:")
            print(summary_memories[0])
            
            if isinstance(summary_memories[0], dict):
                content = summary_memories[0].get('content', {})
                if isinstance(content, dict):
                    text = content.get('text', '')
                    print(f"\n  - text内容: {text[:200]}...")
                    print(f"  - text是否为XML: {is_xml(text)}")
                    print(f"  - text是否为JSON: {is_json(text)}")
        else:
            print("⚠️ 未找到摘要记忆")
    except Exception as e:
        print(f"❌ 检索失败: {str(e)}")
    
    # 4. 总结
    print("\n" + "="*60)
    print("📊 格式总结:")
    print("="*60)
    print("所有策略返回的数据结构都是:")
    print("  {")
    print("    'memoryRecordId': 'xxx',")
    print("    'content': {")
    print("      'text': '实际内容（格式因策略而异）'")
    print("    },")
    print("    'score': 0.xxx")
    print("  }")
    print("\n关键区别在于 content.text 的内容格式:")
    print("  - Semantic Memory: 纯文本")
    print("  - User Preference: JSON字符串")
    print("  - Summary Memory: XML字符串")


def is_json(text):
    """检查字符串是否为有效JSON"""
    try:
        json.loads(text)
        return True
    except:
        return False


def is_xml(text):
    """检查字符串是否包含XML标签"""
    return '<' in text and '>' in text and '</' in text


if __name__ == "__main__":
    inspect_memory_formats()
