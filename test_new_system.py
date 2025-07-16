#!/usr/bin/env python3
"""
MamaVillage v2.0 系统集成测试
测试新的 LangGraph + LangChain 架构
"""

import json
import sys
from pathlib import Path

def test_imports():
    """测试核心模块导入"""
    print("🧪 测试模块导入...")
    
    try:
        from core import (
            SimulationState, WorkflowState, AgentProfileManager,
            MamaVillageWorkflow, MemorySystemManager,
            AgentProfile, AgentRole, Education
        )
        print("  ✅ 核心模块导入成功")
        return True
    except Exception as e:
        print(f"  ❌ 核心模块导入失败: {e}")
        return False

def test_config():
    """测试配置"""
    print("🧪 测试配置...")
    
    try:
        from config import Config
        Config.validate()
        print("  ✅ 配置验证成功")
        return True
    except Exception as e:
        print(f"  ❌ 配置验证失败: {e}")
        print("  💡 请确保设置了 OPENAI_API_KEY 环境变量")
        return False

def test_agent_profiles():
    """测试Agent配置文件加载"""
    print("🧪 测试Agent配置文件...")
    
    try:
        from core import AgentProfileManager
        
        profile_manager = AgentProfileManager()
        agents_dir = Path("agents")
        
        if not agents_dir.exists():
            print("  ❌ agents目录不存在")
            return False
        
        loaded_count = 0
        for agent_file in agents_dir.glob("*.json"):
            try:
                with open(agent_file, 'r', encoding='utf-8') as f:
                    agent_data = json.load(f)
                
                profile = profile_manager.load_profile_from_dict(agent_data)
                profile_manager.add_profile(profile)
                loaded_count += 1
                print(f"    ✅ 加载成功: {profile.name}")
                
            except Exception as e:
                print(f"    ❌ 加载失败 {agent_file}: {e}")
                return False
        
        print(f"  ✅ 成功加载 {loaded_count} 个Agent配置")
        return loaded_count > 0
        
    except Exception as e:
        print(f"  ❌ Agent配置测试失败: {e}")
        return False

def test_memory_system():
    """测试记忆系统"""
    print("🧪 测试记忆系统...")
    
    try:
        from core import MemorySystemManager, Memory, MemoryType
        from datetime import datetime
        
        memory_system = MemorySystemManager(":memory:")  # 使用内存数据库测试
        
        # 测试添加记忆
        test_memory = Memory(
            agent_id="test_agent",
            content="测试记忆内容",
            memory_type=MemoryType.OBSERVATION,
            importance=5
        )
        
        memory_system.store.save_memory(test_memory)
        
        # 测试获取记忆
        memories = memory_system.store.get_memories("test_agent", limit=10)
        
        if len(memories) == 1 and memories[0].content == "测试记忆内容":
            print("  ✅ 记忆系统测试成功")
            return True
        else:
            print("  ❌ 记忆系统测试失败：记忆不匹配")
            return False
            
    except Exception as e:
        print(f"  ❌ 记忆系统测试失败: {e}")
        return False

def test_workflow_creation():
    """测试工作流创建"""
    print("🧪 测试工作流创建...")
    
    try:
        from core import AgentProfileManager, MamaVillageWorkflow
        
        # 创建一个简单的测试配置
        profile_manager = AgentProfileManager()
        
        # 尝试创建工作流（不执行）
        workflow = MamaVillageWorkflow(profile_manager)
        
        if workflow.graph and workflow.app:
            print("  ✅ 工作流创建成功")
            return True
        else:
            print("  ❌ 工作流创建失败：缺少组件")
            return False
            
    except Exception as e:
        print(f"  ❌ 工作流创建失败: {e}")
        return False

def test_agent_creation():
    """测试Agent创建"""
    print("🧪 测试Agent创建...")
    
    try:
        from core import AgentProfile, AgentRole, Education, MamaVillageAgent
        
        # 创建测试Agent配置
        test_profile = AgentProfile(
            id="test_mama",
            name="测试妈妈",
            age=28,
            education=Education.HIGH,
            role=AgentRole.YOUNG_MOTHER
        )
        
        # 创建Agent实例
        agent = MamaVillageAgent(test_profile)
        
        if agent.profile and agent.llm and agent.tools:
            print("  ✅ Agent创建成功")
            return True
        else:
            print("  ❌ Agent创建失败：缺少组件")
            return False
            
    except Exception as e:
        print(f"  ❌ Agent创建失败: {e}")
        return False

def run_all_tests():
    """运行所有测试"""
    print("🚀 开始 MamaVillage v2.0 系统集成测试")
    print("=" * 50)
    
    tests = [
        ("模块导入", test_imports),
        ("配置验证", test_config),
        ("Agent配置文件", test_agent_profiles),
        ("记忆系统", test_memory_system),
        ("工作流创建", test_workflow_creation),
        ("Agent创建", test_agent_creation),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"  ❌ 测试异常: {e}")
            results.append((test_name, False))
    
    # 总结结果
    print("\n" + "=" * 50)
    print("📊 测试结果总结")
    print("=" * 50)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"  {test_name}: {status}")
    
    print(f"\n🎯 总体结果: {passed}/{total} 测试通过")
    
    if passed == total:
        print("🎉 所有测试通过！系统就绪")
        return True
    else:
        print("⚠️ 部分测试失败，请检查配置和依赖")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)