"""
MamaVillage LangGraph 工作流系统
基于 StateGraph 的 observe → plan → act → reflect 循环
"""

from typing import Dict, List, Optional, Any, Literal
from datetime import datetime
import random

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite import SqliteSaver

from .state import (
    WorkflowState, SimulationState, AgentState, 
    NodeOutput, Observation, Plan, Action, ActionType,
    Memory, MemoryType, Conversation, ConversationType
)
from .agent import MamaVillageAgent
from .agent_profile import AgentProfile, AgentProfileManager


class MamaVillageWorkflow:
    """妈妈村核心工作流系统"""
    
    def __init__(self, profile_manager: AgentProfileManager):
        self.profile_manager = profile_manager
        self.agents: Dict[str, MamaVillageAgent] = {}
        
        # 初始化所有Agent
        for profile in profile_manager.get_all_profiles():
            self.agents[profile.id] = MamaVillageAgent(profile)
        
        # 创建LangGraph StateGraph
        self.graph = self._create_workflow_graph()
        
        # 设置检查点保存器（可选）
        memory = SqliteSaver.from_conn_string(":memory:")
        self.app = self.graph.compile(checkpointer=memory)
    
    def _create_workflow_graph(self) -> StateGraph:
        """创建工作流图"""
        
        # 创建状态图
        workflow = StateGraph(WorkflowState)
        
        # 添加节点
        workflow.add_node("select_agent", self._select_agent_node)
        workflow.add_node("observe", self._observe_node)
        workflow.add_node("plan", self._plan_node)
        workflow.add_node("execute", self._execute_node)
        workflow.add_node("reflect", self._reflect_node)
        workflow.add_node("process_results", self._process_results_node)
        
        # 设置入口点
        workflow.set_entry_point("select_agent")
        
        # 添加边
        workflow.add_edge("select_agent", "observe")
        workflow.add_edge("observe", "plan")
        workflow.add_edge("plan", "execute")
        workflow.add_edge("execute", "reflect")
        workflow.add_edge("reflect", "process_results")
        
        # 条件边：决定是否继续循环
        workflow.add_conditional_edges(
            "process_results",
            self._should_continue,
            {
                "continue": "select_agent",
                "end": END
            }
        )
        
        return workflow
    
    def _select_agent_node(self, state: WorkflowState) -> WorkflowState:
        """选择Agent节点"""
        
        # 获取当前活跃的Agent
        current_hour = datetime.now().hour
        active_profiles = self.profile_manager.get_active_profiles(current_hour)
        
        if not active_profiles:
            # 如果没有活跃的Agent，随机选择一个
            active_profiles = self.profile_manager.get_all_profiles()
        
        # 从活跃Agent中随机选择
        selected_profile = random.choice(active_profiles)
        state.current_agent_id = selected_profile.id
        state.current_node = "select_agent"
        
        # 记录节点输出
        output = NodeOutput(
            success=True,
            data={"selected_agent": selected_profile.id}
        )
        state.add_node_output("select_agent", output)
        
        print(f"   🎯 选择了Agent: {selected_profile.name}")
        
        return state
    
    def _observe_node(self, state: WorkflowState) -> WorkflowState:
        """观察节点"""
        state.current_node = "observe"
        
        if not state.current_agent_id:
            output = NodeOutput(success=False, error="没有选择Agent")
            state.add_node_output("observe", output)
            return state
        
        agent = self.agents[state.current_agent_id]
        
        # 创建观察结果
        observation = self._generate_observation(agent, state.simulation_state)
        
        # 处理观察
        result = agent.process_observation(observation)
        
        # 更新Agent状态
        agent_state = state.simulation_state.get_agent_state(state.current_agent_id)
        if not agent_state:
            agent_state = AgentState(agent_id=state.current_agent_id)
        
        agent_state.current_observation = observation
        state.simulation_state.update_agent_state(state.current_agent_id, agent_state)
        
        output = NodeOutput(
            success=True,
            data={
                "observation": observation.dict(),
                "processing_result": result
            }
        )
        state.add_node_output("observe", output)
        
        print(f"      👁️ {agent.profile.name} 完成了环境观察")
        
        return state
    
    def _plan_node(self, state: WorkflowState) -> WorkflowState:
        """计划节点"""
        state.current_node = "plan"
        
        agent = self.agents[state.current_agent_id]
        
        # 30%概率制定新计划
        should_plan = random.random() < 0.3
        
        if should_plan:
            # 生成计划
            plan = self._generate_plan(agent, state.simulation_state)
            
            # 更新Agent状态
            agent_state = state.simulation_state.get_agent_state(state.current_agent_id)
            agent_state.current_plan = plan
            state.simulation_state.update_agent_state(state.current_agent_id, agent_state)
            
            output = NodeOutput(
                success=True,
                data={"plan": plan.dict(), "new_plan": True}
            )
            
            print(f"      📋 {agent.profile.name} 制定了新计划")
        else:
            # 使用现有计划
            output = NodeOutput(
                success=True,
                data={"new_plan": False}
            )
        
        state.add_node_output("plan", output)
        return state
    
    def _execute_node(self, state: WorkflowState) -> WorkflowState:
        """执行节点"""
        state.current_node = "execute"
        
        agent = self.agents[state.current_agent_id]
        
        # 执行行动
        action_result = agent.take_initiative_action()
        
        # 处理行动结果
        if action_result:
            self._process_action_result(agent, action_result, state.simulation_state)
            
            output = NodeOutput(
                success=True,
                data={"action_result": action_result}
            )
            
            # 显示行动结果
            self._display_action_result(agent.profile.name, action_result)
        else:
            output = NodeOutput(
                success=True,
                data={"action_result": None}
            )
        
        state.add_node_output("execute", output)
        return state
    
    def _reflect_node(self, state: WorkflowState) -> WorkflowState:
        """反思节点"""
        state.current_node = "reflect"
        
        agent = self.agents[state.current_agent_id]
        
        # 20%概率进行反思
        should_reflect = random.random() < 0.2
        
        if should_reflect:
            reflection = self._generate_reflection(agent, state.simulation_state)
            
            # 添加反思记忆
            agent.add_memory(
                content=reflection.content,
                memory_type=MemoryType.REFLECTION,
                importance=reflection.importance
            )
            
            output = NodeOutput(
                success=True,
                data={"reflection": reflection.dict(), "reflected": True}
            )
            
            print(f"      🤔 {agent.profile.name} 进行了反思")
        else:
            output = NodeOutput(
                success=True,
                data={"reflected": False}
            )
        
        state.add_node_output("reflect", output)
        return state
    
    def _process_results_node(self, state: WorkflowState) -> WorkflowState:
        """处理结果节点"""
        state.current_node = "process_results"
        
        # 更新模拟状态
        state.simulation_state.tick_count += 1
        state.simulation_state.current_time = datetime.now()
        
        # 处理全局事件
        self._process_global_events(state.simulation_state)
        
        output = NodeOutput(
            success=True,
            data={"tick_completed": state.simulation_state.tick_count}
        )
        state.add_node_output("process_results", output)
        
        return state
    
    def _should_continue(self, state: WorkflowState) -> Literal["continue", "end"]:
        """决定是否继续工作流"""
        
        # 检查对话限制
        if state.simulation_state.is_conversation_limit_reached():
            print(f"\n🎯 已达到对话轮数限制，停止模拟")
            return "end"
        
        # 检查其他停止条件
        if state.simulation_state.tick_count >= 100:  # 最大tick限制
            print(f"\n⏰ 已达到最大tick数，停止模拟")
            return "end"
        
        return "continue"
    
    def _generate_observation(self, agent: MamaVillageAgent, 
                            simulation_state: SimulationState) -> Observation:
        """生成观察结果"""
        
        # 观察其他Agent的活动
        social_observations = []
        for other_agent_id, other_agent_state in simulation_state.agent_states.items():
            if other_agent_id != agent.profile.id:
                recent_convs = other_agent_state.recent_conversations[-3:]
                if recent_convs:
                    social_observations.append({
                        "agent_id": other_agent_id,
                        "recent_conversations": len(recent_convs),
                        "last_activity": other_agent_state.last_activity.isoformat(),
                        "importance": 3
                    })
        
        # 时间上下文
        current_hour = datetime.now().hour
        time_context = self._get_time_context(current_hour)
        
        # 环境状态
        environment_state = {
            "tick": simulation_state.tick_count,
            "day": simulation_state.simulation_day,
            "time": current_hour,
            "active_agents": len(simulation_state.active_agents)
        }
        
        # 获取最近记忆
        recent_memories = agent.long_term_memories[-5:]
        
        return Observation(
            agent_id=agent.profile.id,
            environment_state=environment_state,
            social_observations=social_observations,
            time_context=time_context,
            recent_memories=recent_memories
        )
    
    def _generate_plan(self, agent: MamaVillageAgent, 
                      simulation_state: SimulationState) -> Plan:
        """生成计划"""
        
        # 根据Agent角色和兴趣生成行动
        possible_actions = []
        
        # 社交行动
        if random.random() < 0.6:
            possible_actions.append(Action(
                action_type=ActionType.CONVERSATION,
                description="与其他妈妈聊天交流",
                priority=random.randint(4, 7)
            ))
        
        # 数字活动
        if random.random() < 0.5:
            possible_actions.append(Action(
                action_type=ActionType.DIGITAL_ACTIVITY,
                description="观看育儿视频或刷手机",
                priority=random.randint(3, 6)
            ))
        
        # 育儿活动
        if agent.profile.children and random.random() < 0.8:
            possible_actions.append(Action(
                action_type=ActionType.CHILDCARE,
                description="照顾孩子日常",
                priority=random.randint(7, 9)
            ))
        
        # 学习活动
        if random.random() < 0.4:
            possible_actions.append(Action(
                action_type=ActionType.LEARNING,
                description="学习新知识",
                priority=random.randint(4, 6)
            ))
        
        return Plan(
            agent_id=agent.profile.id,
            actions=possible_actions
        )
    
    def _generate_reflection(self, agent: MamaVillageAgent, 
                           simulation_state: SimulationState):
        """生成反思"""
        from .state import Reflection
        
        # 简单的反思内容生成
        reflection_topics = [
            "今天和其他妈妈的交流很有帮助",
            "学到了一些新的育儿知识",
            "孩子今天的表现很不错",
            "发现了一些新的问题需要注意",
            "感谢群里妈妈们的分享"
        ]
        
        content = random.choice(reflection_topics)
        
        return Reflection(
            agent_id=agent.profile.id,
            content=content,
            importance=random.randint(3, 6)
        )
    
    def _process_action_result(self, agent: MamaVillageAgent, 
                             action_result: Dict[str, Any],
                             simulation_state: SimulationState):
        """处理行动结果"""
        
        action_type = action_result.get("action_type")
        
        if action_type == ActionType.CONVERSATION:
            # 处理对话结果
            conversation = action_result.get("result")
            if conversation:
                simulation_state.add_conversation(conversation)
        
        elif action_type == ActionType.CHILDCARE:
            # 处理育儿结果
            if action_result.get("needs_help"):
                # 生成求助对话
                help_context = {
                    "type": ConversationType.HELP_REQUEST,
                    "conversation_type": "help_request",
                    "problem": action_result.get("concern", "育儿问题")
                }
                help_conversation = agent.generate_conversation(help_context)
                if help_conversation:
                    simulation_state.add_conversation(help_conversation)
        
        # 记录行动到记忆
        agent.add_memory(
            content=action_result.get("description", "执行了行动"),
            memory_type=MemoryType.ACTION,
            importance=action_result.get("priority", 5)
        )
    
    def _display_action_result(self, agent_name: str, action_result: Dict[str, Any]):
        """显示行动结果"""
        description = action_result.get("description", "未知行动")
        action_type = action_result.get("action_type")
        
        print(f"      🎬 {agent_name}: {description}")
        
        if action_type == ActionType.CONVERSATION:
            conversation = action_result.get("result")
            if conversation:
                message = conversation.message[:50] + "..." if len(conversation.message) > 50 else conversation.message
                print(f"         └─ 💬 说: \"{message}\"")
        
        elif action_type == ActionType.DIGITAL_ACTIVITY:
            topic = action_result.get("topic", "")
            platform = action_result.get("platform", "")
            learned = action_result.get("learned_something", False)
            print(f"         └─ 📱 在{platform}看{topic}视频" + (" ✨学到新知识" if learned else ""))
        
        elif action_type == ActionType.CHILDCARE:
            if action_result.get("needs_help"):
                concern = action_result.get("concern", "")
                print(f"         └─ ⚠️ 育儿担忧: {concern}")
        
        elif action_type == ActionType.LEARNING:
            topic = action_result.get("topic", "")
            print(f"         └─ 📚 学习: {topic}")
    
    def _process_global_events(self, simulation_state: SimulationState):
        """处理全局事件"""
        
        # 添加全局事件处理逻辑
        # 例如：节日、季节变化、社区活动等
        
        # 清理过期的对话记录
        for agent_state in simulation_state.agent_states.values():
            if len(agent_state.recent_conversations) > 20:
                agent_state.recent_conversations = agent_state.recent_conversations[-15:]
    
    def _get_time_context(self, hour: int) -> str:
        """获取时间上下文"""
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
    
    def run_single_cycle(self, state: WorkflowState) -> WorkflowState:
        """运行单个工作流循环"""
        
        # 使用LangGraph执行工作流
        config = {"configurable": {"thread_id": f"simulation_{state.simulation_state.tick_count}"}}
        
        try:
            result = self.app.invoke(state.dict(), config)
            return WorkflowState(**result)
        except Exception as e:
            print(f"❌ 工作流执行失败: {e}")
            return state