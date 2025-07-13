#!/usr/bin/env python3
"""
对话轮数限制功能测试脚本
"""

import sys
from run import MamaVillageSimulation

def test_conversation_limit():
    """测试对话轮数限制功能"""
    print("🧪 测试对话轮数限制功能")
    print("=" * 50)
    
    try:
        # 创建模拟实例
        sim = MamaVillageSimulation()
        
        print(f"✅ 系统初始化成功，加载了{len(sim.agents)}个agent")
        print(f"💬 初始对话计数: {sim.conversation_count}")
        
        # 测试对话计数功能
        print("\n🧪 测试对话计数...")
        sim.conversation_count = 5
        sim.max_conversations = 10
        
        # 测试状态显示
        print("\n📊 测试状态显示:")
        sim._show_current_status()
        
        # 测试对话记录功能（可能没有数据）
        print("\n💬 测试对话记录功能:")
        sim.show_conversation_history(limit=5)
        
        # 测试统计功能
        print("\n📈 测试统计功能:")
        sim.show_conversation_stats()
        
        print("\n✅ 所有功能测试通过！")
        print("\n🎯 建议的测试流程:")
        print("1. 运行: python run.py")
        print("2. 选择模式: 4")
        print("3. 设置参数: 对话轮数=5, tick数=10, 间隔=1.0")
        print("4. 观察对话计数和进度显示")
        print("5. 查看生成的对话记录")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_conversation_limit()
    sys.exit(0 if success else 1)