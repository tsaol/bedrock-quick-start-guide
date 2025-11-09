"""
AgentCore Memory 数据写入流程演示
展示短期记忆和长期记忆的生成时间差
"""
import time
from datetime import datetime
from bedrock_agentcore.memory import MemoryClient
from botocore.exceptions import ClientError

class MemoryWriteProcessDemo:
    def __init__(self, region="us-west-2"):
        self.memory_client = MemoryClient(region_name=region)
        self.memory_id = None
        
    def setup_memory(self):
        """创建Memory"""
        memory_name = "MemoryWriteProcessDemo"
        
        try:
            print(f"\n📝 创建Memory: {memory_name}")
            memory = self.memory_client.create_memory_and_wait(
                name=memory_name,
                description="演示Memory写入流程",
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
    
    def write_event_and_track(self, user_id, session_id, message):
        """写入事件并追踪处理过程"""
        print(f"\n{'='*60}")
        print(f"📝 写入事件: {message[:50]}...")
        print(f"{'='*60}")
        
        # 记录写入时间
        write_time = datetime.now()
        print(f"⏰ 写入时间: {write_time.strftime('%H:%M:%S')}")
        
        # 写入事件
        try:
            self.memory_client.create_event(
                memory_id=self.memory_id,
                actor_id=user_id,
                session_id=session_id,
                messages=[(message, "USER")]
            )
            print(f"✅ 事件写入成功")
        except Exception as e:
            print(f"❌ 写入失败: {str(e)}")
            return
        
        # 立即检查短期记忆
        print(f"\n🔍 阶段1: 立即检查短期记忆（原始事件）")
        self.check_short_term_memory(user_id, session_id, "立即")
        
        # 等待并检查长期记忆生成
        check_intervals = [10, 30, 60, 90, 120]  # 秒
        
        for interval in check_intervals:
            print(f"\n⏳ 等待 {interval} 秒...")
            time.sleep(interval if interval == 10 else interval - sum([i for i in check_intervals if i < interval]))
            
            elapsed = (datetime.now() - write_time).total_seconds()
            print(f"\n🔍 阶段2: 检查长期记忆（已过 {int(elapsed)} 秒）")
            
            has_semantic = self.check_long_term_memory(user_id, "semantic", message[:20])
            has_preference = self.check_long_term_memory(user_id, "preference", message[:20])
            
            if has_semantic and has_preference:
                print(f"\n✅ 长期记忆已生成！总耗时: {int(elapsed)} 秒")
                break
    
    def check_short_term_memory(self, user_id, session_id, stage):
        """检查短期记忆（原始事件）"""
        try:
            events = self.memory_client.list_events(
                memory_id=self.memory_id,
                actor_id=user_id,
                session_id=session_id
            )
            
            if events:
                print(f"  ✅ 短期记忆 ({stage}): 找到 {len(events)} 条原始事件")
                if events:
                    latest = events[-1] if isinstance(events, list) else events
                    print(f"    最新事件: {str(latest)[:80]}...")
                return True
            else:
                print(f"  ⚠️ 短期记忆 ({stage}): 未找到事件")
                return False
                
        except Exception as e:
            print(f"  ❌ 检查短期记忆失败: {str(e)}")
            return False
    
    def check_long_term_memory(self, user_id, memory_type, query):
        """检查长期记忆"""
        try:
            if memory_type == "semantic":
                namespace = f"/facts/{user_id}"
                label = "语义记忆"
            else:
                namespace = f"/preferences/{user_id}"
                label = "偏好记忆"
            
            memories = self.memory_client.retrieve_memories(
                memory_id=self.memory_id,
                namespace=namespace,
                query=query
            )
            
            if memories:
                print(f"  ✅ {label}: 找到 {len(memories)} 条记忆")
                if memories:
                    content = self.extract_content(memories[0])
                    print(f"    内容: {content[:60]}...")
                return True
            else:
                print(f"  ⚠️ {label}: 尚未生成")
                return False
                
        except Exception as e:
            print(f"  ❌ 检查{label}失败: {str(e)}")
            return False
    
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
    
    def demonstrate_batch_write(self):
        """演示批量写入的处理"""
        print(f"\n{'='*60}")
        print("📦 演示批量写入")
        print(f"{'='*60}")
        
        user_id = "batch_user"
        session_id = f"batch_session_{int(time.time())}"
        
        messages = [
            "我是一名数据科学家，需要高性能计算设备",
            "我的预算是30000元，主要用于深度学习训练",
            "我偏好NVIDIA GPU，最好是RTX 4090或更高",
            "我需要至少64GB内存和2TB SSD存储"
        ]
        
        print(f"\n📝 批量写入 {len(messages)} 条消息...")
        write_start = datetime.now()
        
        for i, msg in enumerate(messages, 1):
            try:
                self.memory_client.create_event(
                    memory_id=self.memory_id,
                    actor_id=user_id,
                    session_id=session_id,
                    messages=[(msg, "USER")]
                )
                print(f"  ✅ 消息 {i}: {msg[:40]}...")
                time.sleep(1)  # 避免限流
            except Exception as e:
                print(f"  ❌ 消息 {i} 写入失败: {str(e)}")
        
        write_duration = (datetime.now() - write_start).total_seconds()
        print(f"\n✅ 批量写入完成，耗时: {int(write_duration)} 秒")
        
        # 立即检查短期记忆
        print(f"\n🔍 立即检查短期记忆:")
        self.check_short_term_memory(user_id, session_id, "批量写入后")
        
        # 等待长期记忆生成
        print(f"\n⏳ 等待60秒后检查长期记忆...")
        time.sleep(60)
        
        print(f"\n🔍 检查长期记忆:")
        self.check_long_term_memory(user_id, "semantic", "数据科学家")
        self.check_long_term_memory(user_id, "preference", "GPU偏好")


def main():
    print("🔄 AgentCore Memory 数据写入流程演示")
    print("="*60)
    
    demo = MemoryWriteProcessDemo()
    
    # 1. 设置Memory
    demo.setup_memory()
    
    # 2. 演示单条写入的完整流程
    print(f"\n{'#'*60}")
    print("# 场景1: 单条消息写入流程追踪")
    print(f"{'#'*60}")
    
    user_id = "demo_user_001"
    session_id = f"demo_session_{int(time.time())}"
    message = "我是一名软件工程师，想买一台MacBook Pro用于开发，预算20000元"
    
    demo.write_event_and_track(user_id, session_id, message)
    
    # 3. 演示批量写入
    print(f"\n{'#'*60}")
    print("# 场景2: 批量消息写入")
    print(f"{'#'*60}")
    
    demo.demonstrate_batch_write()
    
    # 4. 总结
    print(f"\n{'='*60}")
    print("📊 写入流程总结")
    print(f"{'='*60}")
    print("""
AgentCore Memory 的数据写入是分阶段的：

阶段1: 立即写入（<1秒）
  ✅ create_event() 调用后立即完成
  ✅ 数据存储为短期记忆（原始事件）
  ✅ 可以立即通过 list_events() 或 get_last_k_turns() 读取

阶段2: 异步处理（1-2分钟）
  ⏳ AgentCore 后台分析事件内容
  ⏳ 根据配置的策略提取关键信息
  ⏳ 调用LLM进行语义分析和结构化

阶段3: 长期记忆生成（完成）
  ✅ 生成语义记忆（事实性知识）
  ✅ 生成偏好记忆（用户偏好）
  ✅ 生成摘要记忆（会话摘要）
  ✅ 可以通过 retrieve_memories() 检索

关键特点：
  📝 写入是同步的（短期记忆）
  🧠 提取是异步的（长期记忆）
  ⚡ 短期记忆立即可用
  ⏰ 长期记忆需要等待1-2分钟
    """)
    
    print(f"\n✅ Demo完成！")


if __name__ == "__main__":
    main()
