#!/usr/bin/env python3
"""
MamaVillage v2.1 - 完全AI驱动版本
所有Agent决策都基于AI思考，不使用随机选择
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
from core.intelligent_agent import IntelligentMamaVillageAgent
from config import Config


class IntelligentMamaVillageSimulation:
    """完全基于AI决策的妈妈村模拟系统"""
    
    def __init__(self):
        print("🧠 初始化智能妈妈互助小区 v2.1...")
        print("🎯 特色：所有Agent决策都基于AI思考")
        
        # 验证配置
        Config.validate()
        
        # 初始化组件
        self.profile_manager = AgentProfileManager()
        self.memory_system = MemorySystemManager()
        
        # 加载Agent配置
        self._load_agent_profiles()
        
        # 创建智能Agent
        self.intelligent_agents: Dict[str, IntelligentMamaVillageAgent] = {}
        for profile in self.profile_manager.get_all_profiles():
            agent = IntelligentMamaVillageAgent(profile)
            self.intelligent_agents[profile.id] = agent
        
        # 初始化模拟状态
        self.simulation_state = SimulationState()
        
        print(f"✅ 初始化完成，共加载 {len(self.intelligent_agents)} 个智能Agent")
    
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
                
                print(f"  📝 加载Agent: {profile.name} ({profile.role})")
                
            except Exception as e:
                print(f"  ❌ 加载{agent_file}失败: {e}")
    
    def run_intelligent_simulation(self, max_ticks: int = 20, 
                                 tick_interval: float = 3.0,
                                 max_conversations: int = None):
        """运行智能模拟"""
        
        self.simulation_state.max_conversations = max_conversations
        
        print(f"\n🚀 开始智能模拟，最大tick数: {max_ticks}")
        print("🧠 特色：每个Agent都会基于AI思考做决策")
        print("=" * 60)
        
        try:
            for tick in range(max_ticks):
                self.simulation_state.tick_count = tick + 1
                print(f"\n⏰ Tick {self.simulation_state.tick_count} - {datetime.now().strftime('%H:%M:%S')}")
                
                # 检查停止条件
                if self.simulation_state.is_conversation_limit_reached():
                    print(f"\n🎯 已达到对话轮数限制，停止模拟")
                    break
                
                # 执行一个智能模拟周期
                self._run_intelligent_tick()
                
                # 显示进度
                if max_conversations:
                    print(f"   📊 当前对话轮数: {self.simulation_state.conversation_count}/{max_conversations}")
                
                # 等待下一个tick
                if tick < max_ticks - 1:
                    print(f"   ⏳ 等待{tick_interval}秒...")
                    time.sleep(tick_interval)
        
        except KeyboardInterrupt:
            print(f"\n⚠️ 用户中断模拟")
        except Exception as e:
            print(f"\n❌ 模拟出错: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self._show_intelligent_summary()
    
    def _run_intelligent_tick(self):
        """执行一个智能tick"""
        
        # 获取当前活跃的Agent
        current_hour = datetime.now().hour
        active_profiles = self.profile_manager.get_active_profiles(current_hour)
        
        if not active_profiles:
            active_profiles = self.profile_manager.get_all_profiles()
        
        # 让每个活跃Agent进行AI决策
        for profile in active_profiles[:3]:  # 限制同时活跃的Agent数量
            agent = self.intelligent_agents[profile.id]
            self._run_intelligent_agent_cycle(agent)
    
    def _run_intelligent_agent_cycle(self, agent: IntelligentMamaVillageAgent):
        """运行单个智能Agent的完整周期"""
        
        agent_name = agent.profile.name
        
        try:
            # 1. 生成观察结果
            observation = self._generate_observation_for_agent(agent)
            
            # 2. AI决策下一步行动
            print(f"      🧠 {agent_name} 正在思考...")
            
            current_context = {
                "tick": self.simulation_state.tick_count,
                "time_period": self._get_current_time_period()
            }
            
            action_result = agent.decide_next_action(observation, current_context)
            
            # 3. 显示和处理AI决策结果
            if action_result:
                self._display_intelligent_action(agent_name, action_result)
                self._process_intelligent_action(agent, action_result)
            else:
                print(f"      😴 {agent_name} 决定休息")
        
        except Exception as e:
            print(f"      ❌ {agent_name} 智能决策失败: {e}")
    
    def _generate_observation_for_agent(self, agent: IntelligentMamaVillageAgent):
        """为Agent生成观察结果"""
        from core.state import Observation
        
        # 观察其他Agent的活动
        social_observations = []
        for other_agent_id, other_agent in self.intelligent_agents.items():
            if other_agent_id != agent.profile.id:
                recent_convs = other_agent.state.recent_conversations[-2:]
                if recent_convs:
                    social_observations.append({
                        "agent_id": other_agent_id,
                        "recent_activity": f"最近有{len(recent_convs)}条对话",
                        "importance": 3
                    })
        
        # 时间上下文
        current_hour = datetime.now().hour
        time_context = self._get_time_context(current_hour)
        
        # 环境状态
        environment_state = {
            "tick": self.simulation_state.tick_count,
            "active_agents": len([a for a in self.intelligent_agents.values() 
                                if a.profile.is_active_at_hour(current_hour)]),
            "total_conversations": self.simulation_state.conversation_count
        }
        
        return Observation(
            agent_id=agent.profile.id,
            environment_state=environment_state,
            social_observations=social_observations,
            time_context=time_context,
            recent_memories=agent.long_term_memories[-5:]
        )
    
    def _display_intelligent_action(self, agent_name: str, action_result: Dict):
        """显示智能行动结果"""
        
        action_type = action_result.get("action_type")
        description = action_result.get("description", "")
        motivation = action_result.get("motivation", "")
        
        print(f"      🎬 {agent_name}: {description}")
        
        if motivation:
            print(f"         💭 想法: {motivation}")
        
        if action_type == "conversation":
            conversation = action_result.get("result")
            if conversation:
                message = conversation.message
                print(f"         💬 说: \"{message}\"")
        
        elif action_type == "digital_activity":
            platform = action_result.get("platform", "")
            topic = action_result.get("topic", "")
            learned = action_result.get("learned_something", False)
            print(f"         📱 在{platform}上{topic}" + (" ✨学到新知识" if learned else ""))
        
        elif action_type == "childcare":
            if action_result.get("needs_help"):
                concern = action_result.get("concern", "")
                print(f"         ⚠️ 担忧: {concern}")
        
        elif action_type == "learning":
            content = action_result.get("content", "")
            print(f"         📚 学习收获: {content}")
    
    def _process_intelligent_action(self, agent: IntelligentMamaVillageAgent, 
                                   action_result: Dict):
        """处理智能行动结果"""
        
        action_type = action_result.get("action_type")
        
        if action_type == "conversation":
            conversation = action_result.get("result")
            if conversation:
                # 添加到记忆系统
                self.memory_system.add_conversation(conversation)
                self.simulation_state.add_conversation(conversation)
        
        elif action_type == "childcare" and action_result.get("needs_help"):
            # Agent需要帮助，生成求助对话
            help_context = {
                "type": "help_request",
                "conversation_type": "help_request",
                "specific_intention": "寻求育儿帮助",
                "motivation": f"担心：{action_result.get('concern', '')}"
            }
            
            help_conversation = agent.generate_conversation(help_context)
            if help_conversation:
                self.memory_system.add_conversation(help_conversation)
                self.simulation_state.add_conversation(help_conversation)
                print(f"         🆘 {agent.profile.name} 在群里求助了")
    
    def _get_current_time_period(self) -> str:
        """获取当前时间段"""
        hour = datetime.now().hour
        if 6 <= hour < 12:
            return "上午"
        elif 12 <= hour < 18:
            return "下午"
        elif 18 <= hour < 22:
            return "晚上"
        else:
            return "夜晚"
    
    def _get_time_context(self, hour: int) -> str:
        """获取详细时间上下文"""
        if 6 <= hour < 9:
            return "早上，准备早餐和送孩子的时间"
        elif 9 <= hour < 12:
            return "上午，比较清闲，可以刷手机学习"
        elif 12 <= hour < 14:
            return "中午，吃饭和午休时间"
        elif 14 <= hour < 17:
            return "下午，孩子午睡，有时间看视频"
        elif 17 <= hour < 20:
            return "傍晚，准备晚饭，比较忙碌"
        elif 20 <= hour < 22:
            return "晚上，一家人在一起，可能会聊天"
        else:
            return "深夜，应该休息了，但可能还在刷手机"
    
    def _show_intelligent_summary(self):
        """显示智能模拟总结"""
        print("\n" + "=" * 60)
        print("🧠 智能模拟总结")
        print("=" * 60)
        
        print(f"📊 模拟统计:")
        print(f"   总tick数: {self.simulation_state.tick_count}")
        print(f"   总对话数: {self.simulation_state.conversation_count}")
        
        # 显示每个Agent的智能行为总结
        for agent_id, agent in self.intelligent_agents.items():
            print(f"\n👤 {agent.profile.name}:")
            print(f"   角色: {agent.profile.role} ({agent.profile.age}岁)")
            print(f"   记忆数量: {len(agent.long_term_memories)}")
            print(f"   对话数量: {len(agent.state.recent_conversations)}")
            
            # 显示最有趣的记忆
            if agent.long_term_memories:
                important_memories = sorted(agent.long_term_memories, 
                                          key=lambda m: m.importance, reverse=True)[:2]
                print("   重要记忆:")
                for memory in important_memories:
                    content = memory.content[:40] + "..." if len(memory.content) > 40 else memory.content
                    print(f"     • {content}")
    
    def show_conversation_history(self, limit: int = 50):
        """显示对话历史"""
        print(f"\n💬 智能Agent对话记录 (最近{limit}条)")
        print("=" * 80)
        
        conversations = self.memory_system.get_conversation_history(limit=limit)
        
        if not conversations:
            print("📭 暂无对话记录")
            return
        
        for i, conv in enumerate(conversations, 1):
            from_agent = self._get_agent_name(conv.from_agent)
            to_agent = self._get_agent_name(conv.to_agent) if conv.to_agent else "群聊"
            timestamp = conv.timestamp.strftime("%m-%d %H:%M")
            
            print(f"{i:2d}. [{timestamp}] 🧠 {from_agent} → {to_agent}: \"{conv.message}\"")
        
        print(f"\n📊 共显示 {len(conversations)} 条AI生成的对话")
    
    def _get_agent_name(self, agent_id: str) -> str:
        """获取Agent名称"""
        if not agent_id:
            return "未知"
        profile = self.profile_manager.get_profile(agent_id)
        return profile.name if profile else agent_id


def main():
    """主函数"""
    print("🧠 欢迎来到妈妈互助小区 v2.1 - 智能AI驱动版本")
    print("🎯 特色：所有Agent的决策都基于AI思考，不使用随机选择")
    print()
    
    try:
        simulation = IntelligentMamaVillageSimulation()
        
        print("\n请选择运行模式:")
        print("1. 智能模拟演示 (5个tick)")
        print("2. 智能对话测试 (限制10轮对话)")
        print("3. 自定义智能模拟")
        
        choice = input("请输入选择 (1-3): ").strip()
        
        if choice == "1":
            print("\n🧠 启动智能模拟演示...")
            simulation.run_intelligent_simulation(max_ticks=5, tick_interval=2.0)
            simulation.show_conversation_history(limit=20)
        
        elif choice == "2":
            print("\n🧠 启动智能对话测试...")
            simulation.run_intelligent_simulation(max_ticks=20, tick_interval=1.5, max_conversations=10)
            simulation.show_conversation_history(limit=10)
        
        elif choice == "3":
            max_conversations = int(input("请输入最大对话轮数 (推荐15): ") or "15")
            max_ticks = int(input("请输入最大tick数 (推荐30): ") or "30")
            
            print(f"\n🧠 启动自定义智能模拟：{max_conversations}轮对话，{max_ticks}个tick")
            simulation.run_intelligent_simulation(max_ticks=max_ticks, tick_interval=2.0, 
                                                max_conversations=max_conversations)
            simulation.show_conversation_history(limit=max_conversations)
        
        else:
            print("无效选择，启动默认智能模拟")
            simulation.run_intelligent_simulation(max_ticks=10, tick_interval=2.0, max_conversations=8)
    
    except Exception as e:
        print(f"❌ 程序运行失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()