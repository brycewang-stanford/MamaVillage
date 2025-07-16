"""
MamaVillage 完全自主决策工作流系统
移除所有硬编码，全部基于 AI autonomous agent 的判断和反应
"""

from typing import Dict, List, Optional, Any, Literal
from datetime import datetime

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite import SqliteSaver
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage

from .state import (
    WorkflowState, SimulationState, AgentState, 
    NodeOutput, Observation, Plan, Action, ActionType,
    Memory, MemoryType, Conversation, ConversationType
)
from .intelligent_agent import IntelligentMamaVillageAgent
from .agent_profile import AgentProfile, AgentProfileManager
from config import Config


class AutonomousWorkflow:
    """完全自主决策的工作流系统"""
    
    def __init__(self, profile_manager: AgentProfileManager):
        self.profile_manager = profile_manager
        self.agents: Dict[str, IntelligentMamaVillageAgent] = {}
        
        # 用于系统级决策的LLM
        self.system_llm = ChatOpenAI(
            model=Config.OPENAI_MODEL,
            temperature=0.3,
            api_key=Config.OPENAI_API_KEY
        )
        
        # 初始化所有智能Agent
        for profile in profile_manager.get_all_profiles():
            self.agents[profile.id] = IntelligentMamaVillageAgent(profile)
        
        # 创建LangGraph StateGraph
        self.graph = self._create_autonomous_workflow()
        
        # 设置检查点保存器
        memory = SqliteSaver.from_conn_string(":memory:")
        self.app = self.graph.compile(checkpointer=memory)
    
    def _create_autonomous_workflow(self) -> StateGraph:
        """创建自主决策工作流图"""
        
        workflow = StateGraph(WorkflowState)
        
        # 添加节点 - 每个节点都基于AI决策
        workflow.add_node("autonomous_agent_selection", self._autonomous_agent_selection)
        workflow.add_node("autonomous_observation", self._autonomous_observation)
        workflow.add_node("autonomous_planning", self._autonomous_planning)
        workflow.add_node("autonomous_execution", self._autonomous_execution)
        workflow.add_node("autonomous_reflection", self._autonomous_reflection)
        workflow.add_node("autonomous_continuation", self._autonomous_continuation)
        
        # 设置入口点
        workflow.set_entry_point("autonomous_agent_selection")
        
        # 添加边
        workflow.add_edge("autonomous_agent_selection", "autonomous_observation")
        workflow.add_edge("autonomous_observation", "autonomous_planning")
        workflow.add_edge("autonomous_planning", "autonomous_execution")
        workflow.add_edge("autonomous_execution", "autonomous_reflection")
        workflow.add_edge("autonomous_reflection", "autonomous_continuation")
        
        # 条件边：基于AI决策是否继续
        workflow.add_conditional_edges(
            "autonomous_continuation",
            self._ai_should_continue,
            {
                "continue": "autonomous_agent_selection",
                "end": END
            }
        )
        
        return workflow
    
    def _autonomous_agent_selection(self, state: WorkflowState) -> WorkflowState:
        """🧠 AI自主选择下一个活跃的Agent"""
        state.current_node = "autonomous_agent_selection"
        
        # 构建Agent选择的AI提示
        selection_prompt = self._build_agent_selection_prompt(state.simulation_state)
        
        try:
            response = self.system_llm.invoke([HumanMessage(content=selection_prompt)])
            decision_text = response.content
            
            # 解析AI的Agent选择决策
            selected_agent_id = self._parse_agent_selection(decision_text, state.simulation_state)
            
            if selected_agent_id:
                state.current_agent_id = selected_agent_id
                agent_name = self.agents[selected_agent_id].profile.name
                
                output = NodeOutput(
                    success=True,
                    data={
                        "selected_agent": selected_agent_id,
                        "selection_reason": decision_text[:100]
                    }
                )
                print(f"   🧠 AI选择了Agent: {agent_name}")
            else:
                # 如果AI选择失败，智能降级选择
                available_agents = list(self.agents.keys())
                if available_agents:
                    state.current_agent_id = available_agents[0]
                    output = NodeOutput(success=True, data={"fallback_selection": True})
                else:
                    output = NodeOutput(success=False, error="没有可用的Agent")
            
            state.add_node_output("autonomous_agent_selection", output)
            return state
            
        except Exception as e:
            print(f"❌ AI Agent选择失败: {e}")
            # 降级处理
            if self.agents:
                state.current_agent_id = list(self.agents.keys())[0]
                output = NodeOutput(success=True, data={"error_fallback": True})
                state.add_node_output("autonomous_agent_selection", output)
            return state
    
    def _build_agent_selection_prompt(self, simulation_state: SimulationState) -> str:
        """构建Agent选择的AI提示"""
        
        current_hour = datetime.now().hour
        time_context = self._get_natural_time_context(current_hour)
        
        # 获取所有Agent的当前状态摘要
        agent_summaries = []
        for agent_id, agent in self.agents.items():
            profile = agent.profile
            recent_activity = len(agent.state.recent_conversations)
            energy = agent.state.energy_level
            last_active = agent.state.last_activity
            
            # 计算上次活动的时间间隔
            time_since_active = (datetime.now() - last_active).total_seconds() / 60  # 分钟
            
            summary = f"""
            - {profile.name} ({profile.role}, {profile.age}岁):
              性格: {', '.join(profile.personality.traits[:3])}
              精力: {energy}/10
              最近活动: {recent_activity}条对话
              上次活动: {time_since_active:.0f}分钟前
              活跃时间: {profile.active_hours}
            """
            agent_summaries.append(summary)
        
        prompt = f"""
你是一个智能的社群模拟系统。现在需要选择下一个应该活跃的Agent（农村妈妈/奶奶）。

【当前环境】
- 时间: {time_context} ({current_hour}点)
- 模拟进行到第 {simulation_state.tick_count} 轮
- 已有对话: {simulation_state.conversation_count} 轮

【可选择的Agent】
{''.join(agent_summaries)}

【选择原则】
1. 考虑当前时间，选择在这个时间点最可能活跃的Agent
2. 考虑Agent的性格特点和社交倾向
3. 平衡不同Agent的活跃度，避免某个Agent过于频繁
4. 考虑精力水平，疲劳的Agent不太可能主动活跃
5. 考虑最近是否有未回应的对话或事件

请选择最合适的Agent，并简要说明原因。

回答格式：选择 [Agent名字]，原因：[简要说明]
"""
        return prompt
    
    def _parse_agent_selection(self, decision_text: str, simulation_state: SimulationState) -> Optional[str]:
        """解析AI的Agent选择决策"""
        
        # 查找Agent名字
        for agent_id, agent in self.agents.items():
            agent_name = agent.profile.name
            if agent_name in decision_text:
                return agent_id
        
        # 如果没有找到明确的名字，尝试解析ID
        for agent_id in self.agents.keys():
            if agent_id in decision_text:
                return agent_id
        
        return None
    
    def _autonomous_observation(self, state: WorkflowState) -> WorkflowState:
        """🧠 AI自主观察环境"""
        state.current_node = "autonomous_observation"
        
        if not state.current_agent_id:
            output = NodeOutput(success=False, error="没有选择Agent")
            state.add_node_output("autonomous_observation", output)
            return state
        
        agent = self.agents[state.current_agent_id]
        
        # 生成详细的环境观察
        observation = self._generate_autonomous_observation(agent, state.simulation_state)
        
        # Agent自主处理观察结果
        observation_result = agent.process_observation(observation)
        
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
                "agent_processing": observation_result
            }
        )
        state.add_node_output("autonomous_observation", output)
        
        print(f"      👁️ {agent.profile.name} 自主观察了环境")
        return state
    
    def _autonomous_planning(self, state: WorkflowState) -> WorkflowState:
        """🧠 AI自主制定计划"""
        state.current_node = "autonomous_planning"
        
        agent = self.agents[state.current_agent_id]
        
        # Agent基于当前观察和状态自主决定是否需要制定新计划
        planning_decision = self._ai_planning_decision(agent, state.simulation_state)
        
        if planning_decision.get("should_plan", False):
            # AI生成详细计划
            plan = self._ai_generate_plan(agent, state.simulation_state, planning_decision)
            
            # 更新Agent状态
            agent_state = state.simulation_state.get_agent_state(state.current_agent_id)
            agent_state.current_plan = plan
            state.simulation_state.update_agent_state(state.current_agent_id, agent_state)
            
            output = NodeOutput(
                success=True,
                data={
                    "plan": plan.dict(),
                    "planning_reason": planning_decision.get("reason", "")
                }
            )
            print(f"      📋 {agent.profile.name} 自主制定了新计划")
        else:
            output = NodeOutput(
                success=True,
                data={
                    "planning_decision": "no_new_plan_needed",
                    "reason": planning_decision.get("reason", "当前计划仍然适用")
                }
            )
        
        state.add_node_output("autonomous_planning", output)
        return state
    
    def _autonomous_execution(self, state: WorkflowState) -> WorkflowState:
        """🧠 AI自主执行行动"""
        state.current_node = "autonomous_execution"
        
        agent = self.agents[state.current_agent_id]
        
        # Agent完全自主决定下一步行动
        current_context = {
            "tick": state.simulation_state.tick_count,
            "time_period": self._get_natural_time_context(datetime.now().hour),
            "simulation_state": state.simulation_state
        }
        
        # 获取Agent当前观察
        agent_state = state.simulation_state.get_agent_state(state.current_agent_id)
        current_observation = agent_state.current_observation if agent_state else None
        
        # Agent自主决策行动
        action_result = agent.decide_next_action(current_observation, current_context)
        
        if action_result:
            # 处理行动结果
            self._process_autonomous_action(agent, action_result, state.simulation_state)
            
            output = NodeOutput(
                success=True,
                data={"autonomous_action": action_result}
            )
            
            self._display_autonomous_action(agent.profile.name, action_result)
        else:
            output = NodeOutput(
                success=True,
                data={"autonomous_action": None, "agent_decision": "rest"}
            )
            print(f"      😴 {agent.profile.name} 自主决定休息")
        
        state.add_node_output("autonomous_execution", output)
        return state
    
    def _autonomous_reflection(self, state: WorkflowState) -> WorkflowState:
        """🧠 AI自主反思"""
        state.current_node = "autonomous_reflection"
        
        agent = self.agents[state.current_agent_id]
        
        # Agent自主决定是否需要反思
        reflection_decision = self._ai_reflection_decision(agent, state.simulation_state)
        
        if reflection_decision.get("should_reflect", False):
            # AI生成个性化反思内容
            reflection_content = self._ai_generate_reflection(agent, state.simulation_state, reflection_decision)
            
            # 添加反思记忆
            agent.add_memory(
                content=reflection_content,
                memory_type=MemoryType.REFLECTION,
                importance=reflection_decision.get("importance", 5)
            )
            
            output = NodeOutput(
                success=True,
                data={
                    "reflection": reflection_content,
                    "reflection_reason": reflection_decision.get("reason", "")
                }
            )
            print(f"      🤔 {agent.profile.name} 进行了自主反思")
        else:
            output = NodeOutput(
                success=True,
                data={
                    "reflection_decision": "no_reflection_needed",
                    "reason": reflection_decision.get("reason", "当前不需要特别反思")
                }
            )
        
        state.add_node_output("autonomous_reflection", output)
        return state
    
    def _autonomous_continuation(self, state: WorkflowState) -> WorkflowState:
        """处理模拟状态更新"""
        state.current_node = "autonomous_continuation"
        
        # 更新模拟状态
        state.simulation_state.tick_count += 1
        state.simulation_state.current_time = datetime.now()
        
        # 处理全局事件（也基于AI判断）
        self._process_autonomous_global_events(state.simulation_state)
        
        output = NodeOutput(
            success=True,
            data={"tick_completed": state.simulation_state.tick_count}
        )
        state.add_node_output("autonomous_continuation", output)
        return state
    
    def _ai_should_continue(self, state: WorkflowState) -> Literal["continue", "end"]:
        """🧠 AI决定是否继续模拟"""
        
        # 检查硬性限制条件
        if state.simulation_state.is_conversation_limit_reached():
            print(f"\n🎯 已达到对话轮数限制，停止模拟")
            return "end"
        
        if state.simulation_state.tick_count >= 100:
            print(f"\n⏰ 已达到最大tick数，停止模拟")
            return "end"
        
        # AI判断是否应该继续（基于系统状态）
        continuation_prompt = f"""
        当前模拟状态：
        - 进行了 {state.simulation_state.tick_count} 轮
        - 产生了 {state.simulation_state.conversation_count} 次对话
        - 当前时间：{datetime.now().strftime('%H:%M')}
        
        从社群活跃度和自然性角度，是否应该继续模拟？
        
        回答：continue 或 end，并简要说明原因。
        """
        
        try:
            response = self.system_llm.invoke([HumanMessage(content=continuation_prompt)])
            decision = response.content.lower()
            
            if "end" in decision:
                print(f"\n🧠 AI决定结束模拟：{response.content}")
                return "end"
            else:
                return "continue"
                
        except Exception as e:
            print(f"AI决策失败，继续模拟: {e}")
            return "continue"
    
    # AI决策辅助方法
    def _ai_planning_decision(self, agent: IntelligentMamaVillageAgent, 
                            simulation_state: SimulationState) -> Dict[str, Any]:
        """AI决定是否需要制定新计划"""
        
        prompt = f"""
        作为{agent.profile.name}，分析当前情况，决定是否需要制定新的行动计划。
        
        当前状态：
        - 精力水平：{agent.state.energy_level}/10
        - 情绪状态：{agent.state.emotional_state}
        - 最近记忆：{len(agent.long_term_memories)}条
        - 最近对话：{len(agent.state.recent_conversations)}条
        
        请判断：是否需要制定新计划？
        
        回答JSON格式：
        {{"should_plan": true/false, "reason": "原因"}}
        """
        
        try:
            response = agent.decision_llm.invoke([HumanMessage(content=prompt)])
            return self._parse_json_response(response.content, {"should_plan": False, "reason": "默认不制定新计划"})
        except:
            return {"should_plan": False, "reason": "AI决策失败"}
    
    def _ai_generate_plan(self, agent: IntelligentMamaVillageAgent,
                         simulation_state: SimulationState,
                         planning_decision: Dict[str, Any]) -> Plan:
        """AI生成详细的个性化计划"""
        
        prompt = f"""
        作为{agent.profile.name}，根据你的性格特点和当前情况，制定接下来的行动计划。
        
        你的特点：
        - 性格：{', '.join(agent.profile.personality.traits)}
        - 兴趣：{', '.join(agent.profile.personality.interests)}
        - 关注点：{', '.join(agent.profile.concerns)}
        
        制定原因：{planning_decision.get('reason', '')}
        
        请制定2-4个具体的行动计划，每个行动包括：
        - 行动类型：conversation/digital_activity/childcare/learning
        - 具体描述：你想做什么
        - 优先级：1-10
        
        用自然语言描述你的计划，不需要严格格式。
        """
        
        try:
            response = agent.llm.invoke([HumanMessage(content=prompt)])
            plan_text = response.content
            
            # 解析AI生成的计划
            actions = self._parse_ai_plan(plan_text, agent)
            
            return Plan(
                agent_id=agent.profile.id,
                actions=actions,
                context={"ai_generated": True, "planning_reason": planning_decision.get("reason")}
            )
            
        except Exception as e:
            print(f"AI计划生成失败: {e}")
            # 降级到简单计划
            return Plan(
                agent_id=agent.profile.id,
                actions=[],
                context={"fallback": True}
            )
    
    def _ai_reflection_decision(self, agent: IntelligentMamaVillageAgent,
                              simulation_state: SimulationState) -> Dict[str, Any]:
        """AI决定是否需要反思"""
        
        recent_actions = len([m for m in agent.long_term_memories[-10:] if m.memory_type == MemoryType.ACTION])
        recent_conversations = len(agent.state.recent_conversations)
        
        prompt = f"""
        作为{agent.profile.name}，分析是否需要对最近的经历进行反思。
        
        最近活动：
        - 执行了 {recent_actions} 个行动
        - 参与了 {recent_conversations} 次对话
        - 当前情绪：{agent.state.emotional_state}
        
        基于你的性格特点，是否需要停下来思考反思一下？
        
        回答JSON格式：
        {{"should_reflect": true/false, "reason": "原因", "importance": 1-10}}
        """
        
        try:
            response = agent.decision_llm.invoke([HumanMessage(content=prompt)])
            return self._parse_json_response(response.content, {
                "should_reflect": False, 
                "reason": "暂时不需要反思",
                "importance": 3
            })
        except:
            return {"should_reflect": False, "reason": "AI决策失败", "importance": 3}
    
    def _ai_generate_reflection(self, agent: IntelligentMamaVillageAgent,
                              simulation_state: SimulationState,
                              reflection_decision: Dict[str, Any]) -> str:
        """AI生成个性化反思内容"""
        
        recent_memories = agent.long_term_memories[-5:]
        memory_summary = "; ".join([m.content for m in recent_memories])
        
        prompt = f"""
        作为{agent.profile.name}，对最近的经历进行反思。
        
        反思原因：{reflection_decision.get('reason', '')}
        
        最近的经历：
        {memory_summary}
        
        请用你的语言风格，表达你的感受、想法和收获。
        要求：
        - 体现你的性格特点
        - 使用自然的表达方式
        - 50字以内
        - 不要用"我反思"这样的词
        """
        
        try:
            response = agent.llm.invoke([HumanMessage(content=prompt)])
            return response.content.strip()
        except Exception as e:
            return f"想了想最近发生的事情，有些感触"
    
    # 辅助方法
    def _generate_autonomous_observation(self, agent: IntelligentMamaVillageAgent,
                                       simulation_state: SimulationState) -> Observation:
        """生成详细的环境观察"""
        
        # 观察其他Agent的活动
        social_observations = []
        for other_agent_id, other_agent in self.agents.items():
            if other_agent_id != agent.profile.id:
                recent_convs = other_agent.state.recent_conversations[-3:]
                if recent_convs:
                    other_name = other_agent.profile.name
                    social_observations.append({
                        "agent_id": other_agent_id,
                        "agent_name": other_name,
                        "recent_activity": f"{other_name}最近有{len(recent_convs)}条对话",
                        "last_message": recent_convs[-1].message if recent_convs else "",
                        "importance": 4
                    })
        
        # 环境状态
        environment_state = {
            "current_time": datetime.now().isoformat(),
            "tick": simulation_state.tick_count,
            "total_conversations": simulation_state.conversation_count,
            "active_agents_count": len([a for a in self.agents.values() 
                                      if (datetime.now() - a.state.last_activity).seconds < 3600])
        }
        
        return Observation(
            agent_id=agent.profile.id,
            environment_state=environment_state,
            social_observations=social_observations,
            time_context=self._get_natural_time_context(datetime.now().hour),
            recent_memories=agent.long_term_memories[-7:]
        )
    
    def _process_autonomous_action(self, agent: IntelligentMamaVillageAgent,
                                 action_result: Dict[str, Any],
                                 simulation_state: SimulationState):
        """处理自主行动结果"""
        
        action_type = action_result.get("action_type")
        
        if action_type == "conversation":
            conversation = action_result.get("result")
            if conversation:
                simulation_state.add_conversation(conversation)
        
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
                simulation_state.add_conversation(help_conversation)
    
    def _display_autonomous_action(self, agent_name: str, action_result: Dict[str, Any]):
        """显示自主行动结果"""
        
        action_type = action_result.get("action_type")
        description = action_result.get("description", "")
        motivation = action_result.get("motivation", "")
        
        print(f"      🧠 {agent_name}: {description}")
        
        if motivation:
            print(f"         💭 AI动机: {motivation}")
        
        if action_type == "conversation":
            conversation = action_result.get("result")
            if conversation:
                print(f"         💬 AI生成: \"{conversation.message}\"")
        
        elif action_type == "digital_activity":
            platform = action_result.get("platform", "")
            topic = action_result.get("topic", "")
            learned = action_result.get("learned_something", False)
            print(f"         📱 AI决定在{platform}上{topic}" + (" ✨AI学习" if learned else ""))
        
        elif action_type == "childcare":
            if action_result.get("needs_help"):
                concern = action_result.get("concern", "")
                print(f"         ⚠️ AI判断担忧: {concern}")
        
        elif action_type == "learning":
            content = action_result.get("content", "")
            print(f"         📚 AI学习: {content}")
    
    def _process_autonomous_global_events(self, simulation_state: SimulationState):
        """基于AI的全局事件处理"""
        
        # AI判断是否需要全局事件
        if simulation_state.tick_count % 10 == 0:  # 每10轮检查一次
            event_prompt = f"""
            社群模拟进行了{simulation_state.tick_count}轮，是否需要引入一些自然的全局事件？
            比如：天气变化、节日、社区活动等。
            
            简单回答：需要/不需要
            """
            
            try:
                response = self.system_llm.invoke([HumanMessage(content=event_prompt)])
                if "需要" in response.content:
                    print(f"      🌍 AI建议引入全局事件: {response.content}")
            except:
                pass
    
    def _get_natural_time_context(self, hour: int) -> str:
        """获取自然的时间上下文描述"""
        if 5 <= hour < 7:
            return "清晨，天刚亮，准备开始新的一天"
        elif 7 <= hour < 9:
            return "早上，忙着准备早餐和送孩子"
        elif 9 <= hour < 11:
            return "上午，相对清闲，可以刷手机聊天"
        elif 11 <= hour < 13:
            return "临近中午，准备午饭时间"
        elif 13 <= hour < 15:
            return "下午，午休后的安静时光"
        elif 15 <= hour < 17:
            return "下午茶时间，孩子们可能在午睡"
        elif 17 <= hour < 19:
            return "傍晚，准备晚饭，家庭活动时间"
        elif 19 <= hour < 21:
            return "晚上，一家人团聚，轻松聊天"
        elif 21 <= hour < 23:
            return "夜晚，孩子睡了，大人的自由时间"
        else:
            return "深夜，应该休息了，但可能还在刷手机"
    
    def _parse_ai_plan(self, plan_text: str, agent: IntelligentMamaVillageAgent) -> List[Action]:
        """解析AI生成的计划文本"""
        
        actions = []
        lines = plan_text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line or len(line) < 10:
                continue
                
            # 尝试识别行动类型
            action_type = ActionType.CONVERSATION  # 默认
            if any(word in line.lower() for word in ['看', '视频', '抖音', '手机']):
                action_type = ActionType.DIGITAL_ACTIVITY
            elif any(word in line.lower() for word in ['孩子', '育儿', '照顾']):
                action_type = ActionType.CHILDCARE
            elif any(word in line.lower() for word in ['学习', '了解', '知识']):
                action_type = ActionType.LEARNING
            
            # 创建行动
            action = Action(
                action_type=action_type,
                description=line,
                priority=5,  # 默认优先级
                metadata={"ai_generated": True}
            )
            actions.append(action)
            
            # 限制行动数量
            if len(actions) >= 4:
                break
        
        return actions
    
    def _parse_json_response(self, response_text: str, default: Dict[str, Any]) -> Dict[str, Any]:
        """解析JSON响应，失败时返回默认值"""
        try:
            import re
            import json
            
            # 尝试提取JSON
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            
            return default
        except:
            return default
    
    def run_single_cycle(self, state: WorkflowState) -> WorkflowState:
        """运行单个自主工作流循环"""
        
        config = {"configurable": {"thread_id": f"autonomous_{state.simulation_state.tick_count}"}}
        
        try:
            result = self.app.invoke(state.dict(), config)
            return WorkflowState(**result)
        except Exception as e:
            print(f"❌ 自主工作流执行失败: {e}")
            return state