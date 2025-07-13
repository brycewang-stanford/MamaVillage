#!/usr/bin/env python3
"""
系统测试脚本 - 验证各个模块的基础功能
"""

import os
import sys
from pathlib import Path

def test_imports():
    """测试模块导入"""
    print("🧪 测试模块导入...")
    
    try:
        from config import Config
        print("  ✅ config模块导入成功")
    except Exception as e:
        print(f"  ❌ config模块导入失败: {e}")
        return False
    
    try:
        from memory.database import MemoryDatabase
        print("  ✅ database模块导入成功")
    except Exception as e:
        print(f"  ❌ database模块导入失败: {e}")
        return False
    
    try:
        from langgraph.observer import ObserverNode
        from langgraph.planner import PlannerNode
        from langgraph.executor import ExecutorNode
        from langgraph.reflector import ReflectorNode
        print("  ✅ LangGraph模块导入成功")
    except Exception as e:
        print(f"  ❌ LangGraph模块导入失败: {e}")
        return False
    
    try:
        from prompts.conversation_templates import ConversationTemplates
        print("  ✅ 对话模板模块导入成功")
    except Exception as e:
        print(f"  ❌ 对话模板模块导入失败: {e}")
        return False
    
    return True

def test_configuration():
    """测试配置"""
    print("\n🧪 测试配置...")
    
    if not os.path.exists(".env"):
        print("  ⚠️ .env文件不存在，使用默认配置")
        return True
    
    try:
        from config import Config
        
        # 检查基本配置项
        api_key = Config.OPENAI_API_KEY
        model = Config.OPENAI_MODEL
        db_path = Config.DATABASE_PATH
        
        print(f"  📝 模型: {model}")
        print(f"  📝 数据库路径: {db_path}")
        
        if api_key and api_key.startswith("sk-"):
            print("  ✅ API密钥格式正确")
        else:
            print("  ⚠️ API密钥未配置或格式不正确")
        
        return True
    except Exception as e:
        print(f"  ❌ 配置测试失败: {e}")
        return False

def test_database():
    """测试数据库功能"""
    print("\n🧪 测试数据库功能...")
    
    try:
        from memory.database import MemoryDatabase
        
        # 创建测试数据库
        db = MemoryDatabase("memory/test.sqlite")
        print("  ✅ 数据库初始化成功")
        
        # 测试添加agent
        test_agent = {
            "id": "test_agent",
            "name": "测试妈妈",
            "age": 30,
            "role": "测试角色"
        }
        
        success = db.add_agent(test_agent)
        if success:
            print("  ✅ Agent添加成功")
        else:
            print("  ❌ Agent添加失败")
            return False
        
        # 测试添加记忆
        success = db.add_memory(
            agent_id="test_agent",
            memory_type="test",
            content="这是一条测试记忆",
            importance=5
        )
        if success:
            print("  ✅ 记忆添加成功")
        else:
            print("  ❌ 记忆添加失败")
            return False
        
        # 测试获取记忆
        memories = db.get_recent_memories("test_agent", limit=5)
        if memories:
            print(f"  ✅ 记忆获取成功 ({len(memories)}条)")
        else:
            print("  ❌ 记忆获取失败")
            return False
        
        # 清理测试数据
        if os.path.exists("memory/test.sqlite"):
            os.remove("memory/test.sqlite")
            print("  🧹 测试数据已清理")
        
        return True
    except Exception as e:
        print(f"  ❌ 数据库测试失败: {e}")
        return False

def test_agents_loading():
    """测试agent配置加载"""
    print("\n🧪 测试Agent配置加载...")
    
    agents_dir = Path("agents")
    if not agents_dir.exists():
        print("  ❌ agents目录不存在")
        return False
    
    agent_files = list(agents_dir.glob("*.json"))
    if not agent_files:
        print("  ❌ 未找到agent配置文件")
        return False
    
    print(f"  📁 找到{len(agent_files)}个agent配置文件")
    
    import json
    loaded_agents = 0
    
    for agent_file in agent_files:
        try:
            with open(agent_file, 'r', encoding='utf-8') as f:
                agent_data = json.load(f)
                
            # 检查必要字段
            required_fields = ["id", "name", "age", "role"]
            missing_fields = [field for field in required_fields if field not in agent_data]
            
            if missing_fields:
                print(f"  ⚠️ {agent_file.name}缺少字段: {missing_fields}")
            else:
                print(f"  ✅ {agent_data['name']} ({agent_data['role']})")
                loaded_agents += 1
                
        except Exception as e:
            print(f"  ❌ 加载{agent_file.name}失败: {e}")
    
    print(f"  📊 成功加载{loaded_agents}个agent")
    return loaded_agents > 0

def test_conversation_templates():
    """测试对话模板"""
    print("\n🧪 测试对话模板...")
    
    try:
        from prompts.conversation_templates import ConversationTemplates
        
        # 测试系统提示词
        system_prompt = ConversationTemplates.get_system_prompt("年轻妈妈")
        if system_prompt:
            print("  ✅ 系统提示词获取成功")
        else:
            print("  ❌ 系统提示词获取失败")
            return False
        
        # 测试对话提示词
        conv_prompt = ConversationTemplates.get_conversation_prompt(
            "daily_chat", 
            time_period="上午"
        )
        if conv_prompt:
            print("  ✅ 对话提示词生成成功")
        else:
            print("  ❌ 对话提示词生成失败")
            return False
        
        # 测试表情符号
        emoji = ConversationTemplates.get_random_emoji("年轻妈妈")
        if emoji:
            print(f"  ✅ 表情符号获取成功: {emoji}")
        else:
            print("  ❌ 表情符号获取失败")
            return False
        
        return True
    except Exception as e:
        print(f"  ❌ 对话模板测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🏡 妈妈互助小区 - 系统测试")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_configuration,
        test_database,
        test_agents_loading,
        test_conversation_templates
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"  ❌ 测试异常: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！系统可以正常运行")
        return True
    else:
        print("⚠️ 部分测试失败，请检查配置")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)