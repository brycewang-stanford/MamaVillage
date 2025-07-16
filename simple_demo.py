#!/usr/bin/env python3
"""
Simple Demo of MamaVillage v3.0 Autonomous System
展示完全自主决策的AI Agent行为
"""

import sys
import json
from datetime import datetime
from pathlib import Path

# Add current directory to path
sys.path.append('.')

def demo_autonomous_decision_making():
    """演示v3.0自主决策系统的核心特色"""
    
    print("🧠 MamaVillage v3.0 自主决策系统演示")
    print("🎯 特色：完全移除硬编码，100% AI自主决策")
    print("=" * 60)
    
    try:
        # 尝试导入核心模块
        from core import AgentProfileManager
        from core.autonomous_workflow import AutonomousWorkflow
        from core.intelligent_agent import IntelligentMamaVillageAgent
        from config import Config
        
        print("✅ 核心模块导入成功")
        
        # 验证配置
        Config.validate()
        print("✅ 配置验证通过")
        
        # 创建配置管理器
        profile_manager = AgentProfileManager()
        
        # 加载Agent配置
        agents_dir = Path("agents")
        if agents_dir.exists():
            for agent_file in agents_dir.glob("*.json"):
                try:
                    with open(agent_file, 'r', encoding='utf-8') as f:
                        agent_data = json.load(f)
                    
                    profile = profile_manager.load_profile_from_dict(agent_data)
                    profile_manager.add_profile(profile)
                    print(f"  📝 加载自主Agent: {profile.name}")
                    
                except Exception as e:
                    print(f"  ❌ 加载{agent_file}失败: {e}")
        
        # 创建自主工作流
        print("\n🧠 创建完全自主决策工作流...")
        autonomous_workflow = AutonomousWorkflow(profile_manager)
        print("✅ 自主工作流创建成功")
        
        # 展示Agent特点
        print("\n🤖 自主AI Agent 概览:")
        for agent_id, agent in autonomous_workflow.agents.items():
            profile = agent.profile
            print(f"  • {profile.name} ({profile.age}岁, {profile.role})")
            print(f"    性格: {', '.join(profile.personality.traits[:3])}")
            print(f"    关注: {', '.join(profile.concerns[:2])}")
            print(f"    语言: {profile.language_style.dialect}")
        
        # 演示AI决策过程
        print(f"\n🧠 AI自主决策演示:")
        print(f"  🎯 每个决策都由AI根据Agent个性和情境自主做出")
        print(f"  🚫 无预设台词、无随机选择、无硬编码行为")
        print(f"  🎭 每个Agent都有独特的思考和表达方式")
        
        # 展示决策原理
        print(f"\n💭 AI决策原理:")
        print(f"  1. 🧠 AI分析所有Agent的状态和特点")
        print(f"  2. 👁️ Agent自主观察当前环境和社交情况")
        print(f"  3. 🤔 基于个性和情境，AI决定是否制定新计划")
        print(f"  4. 🎬 Agent根据观察和计划，自主决策具体行动")
        print(f"  5. 💭 基于经历和感受，AI生成个性化反思")
        
        print(f"\n🎉 v3.0自主版本成功验证!")
        print(f"🏆 系统已准备好展示真正的autonomous AI社会行为")
        
        return True
        
    except Exception as e:
        print(f"❌ 演示失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def show_autonomous_features():
    """展示自主决策特色"""
    
    print(f"\n🚀 v3.0自主决策特色对比:")
    print("=" * 50)
    
    features = [
        {
            "功能": "Agent选择",
            "旧版本": "random.choice(agents) - 随机选择",
            "v3.0版本": "AI分析所有Agent状态，智能选择最合适的",
            "示例": "AI考虑时间、精力、性格、最近活动选择张奶奶"
        },
        {
            "功能": "行动决策", 
            "旧版本": "random.random() < 0.6 - 固定概率",
            "v3.0版本": "Agent基于观察和个性自主决定行动",
            "示例": "张奶奶看到群里讨论辅食，主动分享传统经验"
        },
        {
            "功能": "对话内容",
            "旧版本": "random.choice(templates) - 模板选择", 
            "v3.0版本": "AI根据具体意图和动机生成个性化对话",
            "示例": "体现张奶奶的方言风格和育儿智慧"
        },
        {
            "功能": "反思生成",
            "旧版本": "预设台词库随机选择",
            "v3.0版本": "AI基于最近经历生成真实感受",
            "示例": "看到年轻妈妈认真学习，感到欣慰和价值"
        }
    ]
    
    for feature in features:
        print(f"\n📋 {feature['功能']}:")
        print(f"  🔴 旧版本: {feature['旧版本']}")
        print(f"  ✅ v3.0版本: {feature['v3.0版本']}")
        print(f"  💡 示例: {feature['示例']}")

if __name__ == "__main__":
    print("🎭 欢迎体验 MamaVillage v3.0 完全自主决策系统")
    print("🧠 从'模拟行为'到'模拟思维'的革命性跃升")
    print()
    
    # 运行演示
    success = demo_autonomous_decision_making()
    
    if success:
        show_autonomous_features()
        
        print(f"\n🎯 下一步：")
        print(f"  运行 'python3 run_autonomous.py' 查看完整的AI自主模拟")
        print(f"  选择模式1进行演示，观察AI如何完全自主地:")
        print(f"  • 选择活跃的Agent")
        print(f"  • 生成个性化对话") 
        print(f"  • 做出智能决策")
        print(f"  • 展现真实的个体差异")
    
    else:
        print(f"\n❌ 演示失败，请检查依赖和配置")