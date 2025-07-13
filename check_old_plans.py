#!/usr/bin/env python3
"""
检查之前模拟中的计划数据（保存在memories表中）
"""

from memory.database import MemoryDatabase
import json

def check_old_plans():
    """检查旧的计划数据"""
    print("🔍 检查之前模拟中的计划数据")
    print("=" * 60)
    
    db = MemoryDatabase()
    
    # Agent信息
    agents = {
        'mama_xiaoli': '小李',
        'mama_wangfang': '王芳', 
        'grandma_zhang': '张奶奶',
        'mama_xiaochen': '小陈'
    }
    
    total_plans = 0
    
    for agent_id, agent_name in agents.items():
        # 获取plan类型的记忆
        plan_memories = db.get_recent_memories(agent_id, limit=100, memory_type='plan')
        
        if plan_memories:
            print(f"\n👤 {agent_name} ({agent_id}) - {len(plan_memories)} 条计划:")
            total_plans += len(plan_memories)
            
            # 显示最近5条计划
            for i, memory in enumerate(plan_memories[:5], 1):
                timestamp = memory.get('timestamp', '')[:16]
                content = memory.get('content', '')
                importance = memory.get('importance', 1)
                
                # 尝试解析metadata
                metadata_info = ""
                try:
                    if memory.get('metadata'):
                        metadata = json.loads(memory['metadata'])
                        planned_time = metadata.get('planned_time', '')
                        priority = metadata.get('priority', importance)
                        if planned_time:
                            metadata_info = f" (时间: {planned_time}, 优先级: {priority})"
                except:
                    pass
                
                print(f"  {i}. [{timestamp}] {content}{metadata_info}")
            
            if len(plan_memories) > 5:
                print(f"     ... 还有 {len(plan_memories) - 5} 条计划")
        else:
            print(f"\n👤 {agent_name} ({agent_id}) - 无计划记录")
    
    print(f"\n📊 总计发现 {total_plans} 条计划记录（保存在memories表中）")
    
    # 检查daily_plans表
    print(f"\n📋 检查daily_plans表:")
    try:
        # 简单查询daily_plans表
        import sqlite3
        conn = sqlite3.connect(db.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM daily_plans")
        daily_plans_count = cursor.fetchone()[0]
        conn.close()
        
        print(f"   daily_plans表中有 {daily_plans_count} 条记录")
        
        if daily_plans_count == 0 and total_plans > 0:
            print("   💡 这解释了为什么您看不到daily_plans记录！")
            print("   ✅ 计划数据实际保存在memories表中，类型为'plan'")
    except Exception as e:
        print(f"   ❌ 检查daily_plans表失败: {e}")
    
    print(f"\n🔧 解决方案:")
    print("1. 您的计划数据没有丢失，只是保存在了memories表中")
    print("2. 已修复代码，新的模拟将正确保存到daily_plans表")
    print("3. 可以使用以下命令查看您的计划数据：")
    print("   python check_database.py --search '计划行动'")
    print("   python check_database.py --table memories --limit 50")

if __name__ == "__main__":
    check_old_plans()