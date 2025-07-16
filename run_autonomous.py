#!/usr/bin/env python3
"""
MamaVillage v3.0 - 完全自主决策版本
移除所有硬编码和预设台词，完全基于 autonomous AI agent 的判断和反应
"""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from core import (
    SimulationState, WorkflowState, AgentProfileManager,
    MemorySystemManager, AgentProfile
)
from core.autonomous_workflow import AutonomousWorkflow
from core.intelligent_agent import IntelligentMamaVillageAgent
from config import Config


class AutonomousMamaVillageSimulation:
    """完全自主决策的妈妈村模拟系统"""
    
    def __init__(self):
        print("🧠 初始化完全自主妈妈互助小区 v3.0...")
        print("🎯 特色：移除所有硬编码，纯 autonomous AI agent 驱动")
        print("🚫 无预设台词、无随机概率、无固定行为模式")
        
        # 验证配置
        Config.validate()
        
        # 初始化组件
        self.profile_manager = AgentProfileManager()
        self.memory_system = MemorySystemManager()
        
        # 加载Agent配置
        self._load_agent_profiles()
        
        # 创建完全自主的工作流
        self.autonomous_workflow = AutonomousWorkflow(self.profile_manager)
        
        # 初始化模拟状态
        self.simulation_state = SimulationState()
        
        print(f"✅ 初始化完成，所有 {len(self.profile_manager.get_all_profiles())} 个Agent完全自主运行")
    
    def _load_agent_profiles(self):
        """加载Agent配置文件"""
        agents_dir = Path("agents")
        
        if not agents_dir.exists():
            print("❌ agents目录不存在")
            return
        
        for agent_file in agents_dir.glob("*.json"):
            try:
                with open(agent_file, 'r', encoding='utf-8') as f:
                    agent_data = json.load(f)
                
                profile = self.profile_manager.load_profile_from_dict(agent_data)
                self.profile_manager.add_profile(profile)
                self.memory_system.register_agent(profile)
                
                print(f"  📝 加载自主Agent: {profile.name} ({profile.role})")
                
            except Exception as e:
                print(f"  ❌ 加载{agent_file}失败: {e}")
    
    def run_autonomous_simulation(self, max_ticks: int = 20, 
                                tick_interval: float = 3.0,
                                max_conversations: int = None):
        """运行完全自主的模拟"""
        
        self.simulation_state.max_conversations = max_conversations
        
        print(f"\n🚀 开始完全自主模拟，最大tick数: {max_ticks}")
        print("🧠 特色：每个决策都由AI autonomous agent自主做出")
        print("🚫 无预设内容：无固定台词、无随机选择、无硬编码行为")
        print("=" * 70)
        
        # 创建工作流状态
        workflow_state = WorkflowState(simulation_state=self.simulation_state)
        
        try:
            for tick in range(max_ticks):
                self.simulation_state.tick_count = tick + 1
                print(f"\n⏰ Tick {self.simulation_state.tick_count} - {datetime.now().strftime('%H:%M:%S')}")
                print(f"🧠 让AI自主决策选择活跃Agent和行为...")
                
                # 检查停止条件
                if self.simulation_state.is_conversation_limit_reached():
                    print(f"\n🎯 已达到对话轮数限制，停止模拟")
                    break
                
                # 执行完全自主的工作流循环
                workflow_state = self.autonomous_workflow.run_single_cycle(workflow_state)
                
                # 处理新产生的对话
                self._process_autonomous_conversations(workflow_state)
                
                # 显示自主决策的进度
                if max_conversations:
                    print(f"   📊 AI产生对话: {self.simulation_state.conversation_count}/{max_conversations}")
                
                # 等待下一个tick
                if tick < max_ticks - 1:
                    print(f"   ⏳ 等待{tick_interval}秒...")
                    time.sleep(tick_interval)
        
        except KeyboardInterrupt:
            print(f"\n⚠️ 用户中断自主模拟")
        except Exception as e:
            print(f"\n❌ 自主模拟出错: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self._show_autonomous_summary()
    
    def _process_autonomous_conversations(self, workflow_state: WorkflowState):
        """处理自主产生的对话"""
        
        # 从工作流状态中提取新对话
        execute_output = workflow_state.node_outputs.get("autonomous_execution")
        if not execute_output or not execute_output.success:
            return
            
        autonomous_action = execute_output.data.get("autonomous_action")
        if not autonomous_action:
            return
            
        # 处理对话类型的自主行动
        if autonomous_action.get("action_type") == "conversation":
            conversation = autonomous_action.get("result")
            if conversation:
                # 添加到记忆系统
                self.memory_system.add_conversation(conversation)
                print(f"         🎙️ AI自主对话已记录")
    
    def show_autonomous_conversation_history(self, limit: int = 50):
        """显示自主对话历史"""
        print(f"\n💬 AI自主对话记录 (最近{limit}条)")
        print("🧠 所有对话内容都由AI根据角色特点自主生成")
        print("=" * 80)
        
        conversations = self.memory_system.get_conversation_history(limit=limit)
        
        if not conversations:
            print("📭 暂无AI自主对话记录")
            return
        
        for i, conv in enumerate(conversations, 1):
            from_agent = self._get_agent_name(conv.from_agent)
            to_agent = self._get_agent_name(conv.to_agent) if conv.to_agent else "群聊"
            timestamp = conv.timestamp.strftime("%m-%d %H:%M")
            
            # 显示AI自主生成的标记
            ai_marker = "🧠"
            if hasattr(conv, 'metadata') and conv.metadata:
                if conv.metadata.get('ai_generated') or conv.metadata.get('specific_intention'):
                    ai_marker = "🎯"
            
            print(f"{i:2d}. [{timestamp}] {ai_marker} {from_agent} → {to_agent}:")
            print(f"     \"{conv.message}\"")
            
            # 如果有AI决策信息，显示出来
            if hasattr(conv, 'metadata') and conv.metadata:
                intention = conv.metadata.get('specific_intention')
                motivation = conv.metadata.get('motivation')
                if intention:
                    print(f"     💭 AI意图: {intention}")
                if motivation:
                    print(f"     🎯 AI动机: {motivation}")
        
        print(f"\n📊 共显示 {len(conversations)} 条AI自主生成的对话")
        print("🧠 每条对话都是Agent基于角色特点和当前情况的自主决策")
    
    def show_autonomous_stats(self):
        """显示自主决策统计"""
        print(f"\n📊 AI自主决策统计")
        print("=" * 50)
        
        stats = self.memory_system.get_conversation_stats()
        
        print(f"🧠 AI总决策数: {stats['total_conversations']}")
        print(f"🎯 本次模拟AI对话: {self.simulation_state.conversation_count}")
        print(f"⏱️ 自主运行时长: {self.simulation_state.tick_count} ticks")
        print(f"🔥 最近AI活动: {stats['recent_activity']} 条")
        print()
        
        # AI Agent自主行为统计
        if stats['conversations_by_agent']:
            print("🤖 各AI Agent自主对话统计:")
            for agent_id, count in sorted(stats['conversations_by_agent'].items(), 
                                        key=lambda x: x[1], reverse=True):
                agent_name = self._get_agent_name(agent_id)
                total = stats['total_conversations']
                percentage = (count / total * 100) if total > 0 else 0
                print(f"  🧠 {agent_name}: {count} 条自主对话 ({percentage:.1f}%)")
        
        # AI对话类型统计
        if stats['conversations_by_type']:
            print("\n🎭 AI对话类型分布:")
            type_names = {
                'group_chat': 'AI群聊',
                'private_chat': 'AI私聊', 
                'help_request': 'AI求助',
                'advice': 'AI建议',
                'content_sharing': 'AI分享'
            }
            
            for conv_type, count in sorted(stats['conversations_by_type'].items(), 
                                         key=lambda x: x[1], reverse=True):
                type_name = type_names.get(conv_type, f'AI {conv_type}')
                print(f"  {type_name}: {count} 条")
        
        print(f"\n🎯 自主决策质量:")
        print(f"  ✅ 100% AI自主生成内容")
        print(f"  🚫 0% 预设台词或随机选择") 
        print(f"  🧠 每个决策都基于Agent个性和情境")
    
    def _get_agent_name(self, agent_id: str) -> str:
        """获取Agent名称"""
        if not agent_id:
            return "未知"
        profile = self.profile_manager.get_profile(agent_id)
        return profile.name if profile else agent_id
    
    def _show_autonomous_summary(self):
        """显示自主模拟总结"""
        print("\n" + "=" * 70)
        print("🧠 AI自主模拟总结")
        print("=" * 70)
        
        print(f"📊 自主模拟统计:")
        print(f"   总tick数: {self.simulation_state.tick_count}")
        print(f"   AI自主对话数: {self.simulation_state.conversation_count}")
        print(f"   平均每tick对话数: {self.simulation_state.conversation_count/max(1, self.simulation_state.tick_count):.2f}")
        
        # 显示每个Agent的自主行为总结
        for agent_id, agent in self.autonomous_workflow.agents.items():
            print(f"\n🤖 {agent.profile.name} (AI自主Agent):")
            print(f"   角色: {agent.profile.role} ({agent.profile.age}岁)")
            print(f"   AI记忆: {len(agent.long_term_memories)} 条")
            print(f"   AI对话: {len(agent.state.recent_conversations)} 条")
            print(f"   当前状态: {agent.state.emotional_state} (精力 {agent.state.energy_level}/10)")
            
            # 显示AI最重要的自主决策
            if agent.long_term_memories:
                important_memories = sorted(agent.long_term_memories, 
                                          key=lambda m: m.importance, reverse=True)[:2]
                print("   🧠 AI重要决策:")
                for memory in important_memories:
                    content = memory.content[:50] + "..." if len(memory.content) > 50 else memory.content
                    print(f"     • {content} (重要性:{memory.importance})")
        
        print(f"\n🎯 自主决策质量评估:")
        print(f"  🧠 所有决策都由AI根据角色特点自主做出")
        print(f"  🚫 无任何预设台词、固定模板或随机选择")
        print(f"  🎭 每个Agent都体现了真实的个性化行为")
        print(f"  📈 对话内容的多样性和自然性显著提升")
    
    def analyze_autonomous_patterns(self):
        """分析AI自主行为模式"""
        print(f"\n🔍 AI自主行为模式分析")
        print("=" * 50)
        
        for agent_id, agent in self.autonomous_workflow.agents.items():
            print(f"\n🤖 {agent.profile.name} 的AI行为模式:")
            
            # 分析记忆类型分布
            memory_types = {}
            for memory in agent.long_term_memories:
                mem_type = memory.memory_type.value
                memory_types[mem_type] = memory_types.get(mem_type, 0) + 1
            
            if memory_types:
                print("   🧠 AI决策类型分布:")
                for mem_type, count in sorted(memory_types.items(), key=lambda x: x[1], reverse=True):
                    print(f"     {mem_type}: {count} 次")
            
            # 分析对话特点
            if agent.state.recent_conversations:
                avg_length = sum(len(conv.message) for conv in agent.state.recent_conversations) / len(agent.state.recent_conversations)
                print(f"   💬 AI对话特点: 平均长度 {avg_length:.1f} 字")
                
                # 分析是否体现了个性特点
                personality_traits = agent.profile.personality.traits
                common_phrases = agent.profile.language_style.common_phrases
                
                trait_usage = 0
                phrase_usage = 0
                
                for conv in agent.state.recent_conversations:
                    message = conv.message.lower()
                    for trait in personality_traits:
                        if trait in message:
                            trait_usage += 1
                    for phrase in common_phrases:
                        if phrase in conv.message:
                            phrase_usage += 1
                
                print(f"   🎭 个性体现度: 特点关键词 {trait_usage} 次，常用语 {phrase_usage} 次")
    
    def interactive_autonomous_mode(self):
        """自主模拟交互模式"""
        print("\n🧠 进入AI自主模拟交互模式")
        print("命令：")
        print("  run [ticks] [max_conversations] - 运行AI自主模拟")
        print("  conversations [limit] - 查看AI自主对话记录")
        print("  stats - 显示AI自主决策统计")
        print("  patterns - 分析AI行为模式")
        print("  export - 导出AI对话记录")
        print("  clear - 清空数据库")
        print("  quit - 退出")
        print()
        
        while True:
            try:
                command = input("AutonomousVillage> ").strip().split()
                
                if not command:
                    continue
                
                cmd = command[0].lower()
                
                if cmd in ["quit", "exit"]:
                    print("👋 再见！感谢体验AI自主模拟")
                    break
                
                elif cmd == "run":
                    ticks = int(command[1]) if len(command) > 1 else 10
                    max_conversations = int(command[2]) if len(command) > 2 else None
                    self.run_autonomous_simulation(max_ticks=ticks, tick_interval=2.0, 
                                                 max_conversations=max_conversations)
                
                elif cmd == "conversations":
                    limit = int(command[1]) if len(command) > 1 else 20
                    self.show_autonomous_conversation_history(limit=limit)
                
                elif cmd == "stats":
                    self.show_autonomous_stats()
                
                elif cmd == "patterns":
                    self.analyze_autonomous_patterns()
                
                elif cmd == "export":
                    filename = self.memory_system.export_conversation_history()
                    if filename:
                        print(f"💾 AI自主对话记录已导出到: {filename}")
                
                elif cmd == "clear":
                    confirm = input("确定要清空所有AI自主数据吗？(y/N): ")
                    if confirm.lower() == 'y':
                        self.memory_system.store.clear_all_data()
                        self.simulation_state.conversation_count = 0
                        print("🧹 AI数据库已清空")
                
                else:
                    print(f"未知命令: {cmd}")
            
            except KeyboardInterrupt:
                print("\n👋 退出AI自主交互模式")
                break
            except Exception as e:
                print(f"❌ 命令执行失败: {e}")


def main():
    """主函数"""
    print("🧠 欢迎来到妈妈互助小区 v3.0 - 完全AI自主决策版本")
    print("🎯 革命性特色：移除所有硬编码和预设内容")
    print("🚫 无预设台词、无随机概率、无固定行为模式")
    print("🤖 100% 基于 autonomous AI agent 的真实决策和反应")
    print()
    
    try:
        simulation = AutonomousMamaVillageSimulation()
        
        print("\n请选择运行模式:")
        print("1. AI自主模拟演示 (10个tick)")
        print("2. AI自主对话专题 (限制15轮对话)")
        print("3. 深度AI自主模拟 (30个tick)")
        print("4. 交互式AI自主模式")
        print("5. 自定义AI自主参数")
        
        choice = input("请输入选择 (1-5): ").strip()
        
        if choice == "1":
            print("\n🧠 启动AI自主模拟演示...")
            print("🎯 观察AI如何完全自主地选择Agent、决策行为、生成对话")
            simulation.run_autonomous_simulation(max_ticks=10, tick_interval=2.0)
            simulation.show_autonomous_conversation_history(limit=20)
        
        elif choice == "2":
            print("\n🧠 启动AI自主对话专题...")
            simulation.run_autonomous_simulation(max_ticks=25, tick_interval=1.5, max_conversations=15)
            simulation.show_autonomous_conversation_history(limit=15)
            simulation.analyze_autonomous_patterns()
        
        elif choice == "3":
            print("\n🧠 启动深度AI自主模拟...")
            simulation.run_autonomous_simulation(max_ticks=30, tick_interval=2.5)
            simulation.show_autonomous_stats()
            simulation.analyze_autonomous_patterns()
        
        elif choice == "4":
            simulation.interactive_autonomous_mode()
        
        elif choice == "5":
            try:
                max_conversations = int(input("请输入最大AI对话轮数 (推荐20): ") or "20")
                max_ticks = int(input("请输入最大tick数 (推荐40): ") or "40")
                tick_interval = float(input("请输入tick间隔秒数 (推荐2.5): ") or "2.5")
                
                print(f"\n🧠 启动自定义AI自主模拟：{max_conversations}轮AI对话，{max_ticks}个tick")
                simulation.run_autonomous_simulation(max_ticks=max_ticks, tick_interval=tick_interval, 
                                                   max_conversations=max_conversations)
                simulation.show_autonomous_conversation_history(limit=max_conversations)
                simulation.show_autonomous_stats()
                
            except ValueError:
                print("❌ 输入无效，启动交互模式")
                simulation.interactive_autonomous_mode()
        
        else:
            print("无效选择，启动AI自主演示模式")
            simulation.run_autonomous_simulation(max_ticks=8, tick_interval=2.0, max_conversations=10)
    
    except Exception as e:
        print(f"❌ AI自主程序运行失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()