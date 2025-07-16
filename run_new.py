#!/usr/bin/env python3
"""
妈妈互助小区（MamaVillage）v2.0 主运行文件
基于现代化 LangGraph + LangChain 架构的农村育儿社群模拟系统
"""

import json
import os
import time
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

# 导入核心模块
from core import (
    SimulationState, WorkflowState, AgentProfileManager, 
    MamaVillageWorkflow, MemorySystemManager,
    AgentProfile, AgentRole
)
from config import Config


class MamaVillageSimulation:
    """妈妈村模拟主系统 v2.0"""
    
    def __init__(self):
        print("🏡 初始化妈妈互助小区 v2.0...")
        print("基于 LangGraph + LangChain 的现代化架构")
        
        # 验证配置
        Config.validate()
        
        # 初始化组件
        self.profile_manager = AgentProfileManager()
        self.memory_system = MemorySystemManager()
        
        # 加载Agent配置
        self._load_agent_profiles()
        
        # 初始化工作流
        self.workflow = MamaVillageWorkflow(self.profile_manager)
        
        # 初始化模拟状态
        self.simulation_state = SimulationState()
        
        print(f"✅ 初始化完成，共加载 {len(self.profile_manager.get_all_profiles())} 个Agent")
        
    def _load_agent_profiles(self):
        """加载所有Agent配置文件"""
        agents_dir = Path("agents")
        
        if not agents_dir.exists():
            print("❌ agents目录不存在")
            return
        
        loaded_count = 0
        for agent_file in agents_dir.glob("*.json"):
            try:
                with open(agent_file, 'r', encoding='utf-8') as f:
                    agent_data = json.load(f)
                    
                # 创建AgentProfile对象
                profile = self.profile_manager.load_profile_from_dict(agent_data)
                
                # 注册到系统
                self.profile_manager.add_profile(profile)
                self.memory_system.register_agent(profile)
                
                loaded_count += 1
                print(f"  📝 加载Agent: {profile.name} ({profile.role})")
                
            except Exception as e:
                print(f"  ❌ 加载{agent_file}失败: {e}")
        
        print(f"  ✅ 成功加载 {loaded_count} 个Agent")
    
    def run_simulation(self, max_ticks: int = 20, tick_interval: float = 3.0, 
                      max_conversations: int = None):
        """运行模拟"""
        
        # 设置模拟参数
        self.simulation_state.max_conversations = max_conversations
        
        conversation_info = f", 最大对话轮数: {max_conversations}" if max_conversations else ""
        print(f"\n🚀 开始模拟，最大tick数: {max_ticks}, 间隔: {tick_interval}秒{conversation_info}")
        print("=" * 60)
        
        # 创建工作流状态
        workflow_state = WorkflowState(simulation_state=self.simulation_state)
        
        try:
            for tick in range(max_ticks):
                self.simulation_state.tick_count = tick + 1
                print(f"\n⏰ Tick {self.simulation_state.tick_count} - {datetime.now().strftime('%H:%M:%S')}")
                
                # 检查停止条件
                if self.simulation_state.is_conversation_limit_reached():
                    print(f"\n🎯 已达到对话轮数限制 ({self.simulation_state.conversation_count}/{max_conversations})，停止模拟")
                    break
                
                # 执行一个工作流循环
                workflow_state = self.workflow.run_single_cycle(workflow_state)
                
                # 处理新产生的对话
                self._process_new_conversations(workflow_state)
                
                # 显示进度
                if max_conversations:
                    print(f"   📊 当前对话轮数: {self.simulation_state.conversation_count}/{max_conversations}")
                
                # 等待下一个tick
                if tick < max_ticks - 1:
                    print(f"   ⏳ 等待{tick_interval}秒...")
                    time.sleep(tick_interval)
        
        except KeyboardInterrupt:
            print(f"\n⚠️ 用户中断模拟 (Tick {self.simulation_state.tick_count})")
        
        except Exception as e:
            print(f"\n❌ 模拟出错: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            self._show_simulation_summary()
    
    def _process_new_conversations(self, workflow_state: WorkflowState):
        """处理新产生的对话"""
        
        # 从工作流状态中提取新对话
        execute_output = workflow_state.node_outputs.get("execute")
        if not execute_output or not execute_output.success:
            return
            
        action_result = execute_output.data.get("action_result")
        if not action_result:
            return
            
        # 处理对话类型的行动结果
        if action_result.get("action_type") == "conversation":
            conversation = action_result.get("result")
            if conversation:
                # 添加到记忆系统
                self.memory_system.add_conversation(conversation)
    
    def show_conversation_history(self, limit: int = 50, export_to_file: bool = False):
        """显示对话历史记录"""
        print(f"\n💬 对话历史记录 (最近{limit}条)")
        print("=" * 80)
        
        conversations = self.memory_system.get_conversation_history(limit=limit)
        
        if not conversations:
            print("📭 暂无对话记录")
            return
        
        # 显示对话
        conversation_lines = []
        for i, conv in enumerate(conversations, 1):
            from_agent = self._get_agent_name(conv.from_agent)
            to_agent = self._get_agent_name(conv.to_agent) if conv.to_agent else "群聊"
            timestamp = conv.timestamp.strftime("%m-%d %H:%M")
            
            type_emoji = {
                'group_chat': '💬',
                'private_chat': '📱',
                'help_request': '🆘', 
                'advice': '💡',
                'content_sharing': '📤'
            }.get(conv.conversation_type.value, '💬')
            
            line = f"{i:2d}. [{timestamp}] {type_emoji} {from_agent} → {to_agent}: \"{conv.message}\""
            print(line)
            conversation_lines.append(line)
        
        print(f"\n📊 共显示 {len(conversations)} 条对话")
        
        # 导出到文件
        if export_to_file:
            filename = self.memory_system.export_conversation_history()
            if filename:
                print(f"💾 对话记录已导出到: {filename}")
    
    def show_conversation_stats(self):
        """显示对话统计信息"""
        print(f"\n📊 对话统计信息")
        print("=" * 40)
        
        stats = self.memory_system.get_conversation_stats()
        
        print(f"📈 总对话数: {stats['total_conversations']}")
        print(f"🎯 本次模拟对话数: {self.simulation_state.conversation_count}")
        print(f"⏱️ 模拟时长: {self.simulation_state.tick_count} ticks")
        print(f"🔥 最近1小时活动: {stats['recent_activity']} 条对话")
        print()
        
        # Agent对话统计
        if stats['conversations_by_agent']:
            print("👥 各Agent对话统计:")
            for agent_id, count in sorted(stats['conversations_by_agent'].items(), 
                                        key=lambda x: x[1], reverse=True):
                agent_name = self._get_agent_name(agent_id)
                total = stats['total_conversations']
                percentage = (count / total * 100) if total > 0 else 0
                print(f"  {agent_name}: {count} 条 ({percentage:.1f}%)")
        
        # 对话类型统计
        if stats['conversations_by_type']:
            print("\n📝 对话类型统计:")
            type_names = {
                'group_chat': '群聊',
                'private_chat': '私聊',
                'help_request': '求助',
                'advice': '建议',
                'content_sharing': '内容分享'
            }
            
            for conv_type, count in sorted(stats['conversations_by_type'].items(), 
                                         key=lambda x: x[1], reverse=True):
                type_name = type_names.get(conv_type, conv_type)
                print(f"  {type_name}: {count} 条")
    
    def _get_agent_name(self, agent_id: str) -> str:
        """获取Agent名称"""
        if not agent_id:
            return "未知"
        profile = self.profile_manager.get_profile(agent_id)
        return profile.name if profile else agent_id
    
    def _show_simulation_summary(self):
        """显示模拟总结"""
        print("\n" + "=" * 60)
        print("📊 模拟总结")
        print("=" * 60)
        
        for profile in self.profile_manager.get_all_profiles():
            agent_memory = self.memory_system.get_agent_memory_manager(profile.id)
            recent_memories = agent_memory.get_memories(limit=10)
            
            print(f"\n👤 {profile.name} ({profile.role}):")
            print(f"   年龄: {profile.age}岁, 教育: {profile.education}")
            print(f"   记忆数量: {len(recent_memories)}")
            print(f"   对话摘要: {agent_memory.get_conversation_summary()[:50]}...")
            
            # 显示最近活动
            if recent_memories:
                print("   最近活动:")
                for memory in recent_memories[:3]:
                    memory_type = memory.memory_type.value
                    content = memory.content[:40] + "..." if len(memory.content) > 40 else memory.content
                    print(f"     • [{memory_type}] {content}")
    
    def interactive_mode(self):
        """交互模式"""
        print("\n🎮 进入交互模式 v2.0")
        print("命令：")
        print("  run [ticks] [max_conversations] - 运行指定数量的tick和对话轮数")
        print("  status - 显示当前状态")
        print("  agent [name] - 查看特定agent信息")
        print("  conversations [limit] - 查看对话记录（默认20条）")
        print("  export_conversations [limit] - 导出对话记录到文件")
        print("  stats - 显示对话统计信息")
        print("  cleanup [days] - 清理N天前的旧数据")
        print("  clear - 清空数据库")
        print("  quit - 退出")
        print()
        
        while True:
            try:
                command = input("MamaVillage v2.0> ").strip().split()
                
                if not command:
                    continue
                
                cmd = command[0].lower()
                
                if cmd in ["quit", "exit"]:
                    print("👋 再见！")
                    break
                
                elif cmd == "run":
                    ticks = int(command[1]) if len(command) > 1 else 5
                    max_conversations = int(command[2]) if len(command) > 2 else None
                    self.run_simulation(max_ticks=ticks, tick_interval=2.0, 
                                      max_conversations=max_conversations)
                
                elif cmd == "status":
                    self._show_current_status()
                
                elif cmd == "agent":
                    if len(command) > 1:
                        agent_name = command[1]
                        self._show_agent_details(agent_name)
                    else:
                        print("请指定agent名称")
                
                elif cmd == "conversations":
                    limit = int(command[1]) if len(command) > 1 else 20
                    self.show_conversation_history(limit=limit)
                
                elif cmd == "export_conversations":
                    limit = int(command[1]) if len(command) > 1 else 50
                    self.show_conversation_history(limit=limit, export_to_file=True)
                
                elif cmd == "stats":
                    self.show_conversation_stats()
                
                elif cmd == "cleanup":
                    days = int(command[1]) if len(command) > 1 else 7
                    self.memory_system.cleanup_old_data(days_to_keep=days)
                
                elif cmd == "clear":
                    confirm = input("确定要清空所有数据吗？(y/N): ")
                    if confirm.lower() == 'y':
                        self.memory_system.store.clear_all_data()
                        self.simulation_state.conversation_count = 0
                        print("数据库已清空")
                
                else:
                    print(f"未知命令: {cmd}")
            
            except KeyboardInterrupt:
                print("\n👋 退出交互模式")
                break
            except Exception as e:
                print(f"❌ 命令执行失败: {e}")
    
    def _show_current_status(self):
        """显示当前状态"""
        print(f"\n📊 当前状态 (Tick {self.simulation_state.tick_count}, Day {self.simulation_state.simulation_day})")
        print(f"⏰ 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"👥 Agent数量: {len(self.profile_manager.get_all_profiles())}")
        print(f"💬 总对话数: {self.simulation_state.conversation_count}")
        
        if self.simulation_state.max_conversations:
            progress = (self.simulation_state.conversation_count / self.simulation_state.max_conversations) * 100
            print(f"🎯 对话进度: {self.simulation_state.conversation_count}/{self.simulation_state.max_conversations} ({progress:.1f}%)")
        
        # 显示每个agent的简要信息
        print("\n👤 Agent状态:")
        for profile in self.profile_manager.get_all_profiles():
            agent_memory = self.memory_system.get_agent_memory_manager(profile.id)
            memories = agent_memory.get_memories(limit=5)
            print(f"   • {profile.name}: {len(memories)}条记忆")
    
    def _show_agent_details(self, agent_name: str):
        """显示agent详细信息"""
        # 查找agent
        profile = None
        for p in self.profile_manager.get_all_profiles():
            if p.name == agent_name or p.id == agent_name:
                profile = p
                break
        
        if not profile:
            print(f"未找到agent: {agent_name}")
            return
        
        print(f"\n👤 {profile.name} 详细信息")
        print(f"ID: {profile.id}")
        print(f"年龄: {profile.age}")
        print(f"角色: {profile.role}")
        print(f"教育: {profile.education}")
        print(f"个性特点: {', '.join(profile.personality.traits)}")
        
        # 显示记忆信息
        agent_memory = self.memory_system.get_agent_memory_manager(profile.id)
        memories = agent_memory.get_memories(limit=10)
        
        if memories:
            print(f"\n最近记忆 ({len(memories)}条):")
            for i, memory in enumerate(memories, 1):
                content = memory.content[:50] + "..." if len(memory.content) > 50 else memory.content
                print(f"  {i}. [{memory.memory_type.value}] {content} (重要性:{memory.importance})")
        
        # 显示对话上下文
        conversation_context = agent_memory.get_conversation_context()
        if conversation_context:
            print(f"\n对话上下文: {conversation_context[:100]}...")


def main():
    """主函数"""
    print("🏡 欢迎来到妈妈互助小区 v2.0")
    print("基于 LangGraph + LangChain 的现代化农村育儿社群模拟系统")
    print()
    
    try:
        # 创建模拟实例
        simulation = MamaVillageSimulation()
        
        # 提供选择
        print("\n请选择运行模式:")
        print("1. 自动模拟 (运行20个tick)")
        print("2. 交互模式")
        print("3. 快速演示 (5个tick)")
        print("4. 限制对话轮数模拟 (自定义)")
        
        choice = input("请输入选择 (1-4): ").strip()
        
        if choice == "1":
            simulation.run_simulation(max_ticks=20, tick_interval=3.0)
        elif choice == "2":
            simulation.interactive_mode()
        elif choice == "3":
            simulation.run_simulation(max_ticks=5, tick_interval=1.5)
        elif choice == "4":
            try:
                max_conversations = int(input("请输入最大对话轮数 (推荐20): ") or "20")
                max_ticks = int(input("请输入最大tick数 (推荐50): ") or "50")
                tick_interval = float(input("请输入tick间隔秒数 (推荐2.0): ") or "2.0")
                
                print(f"\n🎯 启动限制对话模拟：最多{max_conversations}轮对话，{max_ticks}个tick")
                simulation.run_simulation(max_ticks=max_ticks, tick_interval=tick_interval, 
                                        max_conversations=max_conversations)
                
                # 模拟结束后显示对话记录
                print("\n🎉 模拟完成！下面是对话记录：")
                simulation.show_conversation_history(limit=max_conversations)
                simulation.show_conversation_stats()
                
            except ValueError:
                print("❌ 输入无效，启动交互模式")
                simulation.interactive_mode()
        else:
            print("无效选择，启动交互模式")
            simulation.interactive_mode()
    
    except Exception as e:
        print(f"❌ 程序运行失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()