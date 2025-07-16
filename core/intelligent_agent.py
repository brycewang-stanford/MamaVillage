"""
MamaVillage 完全基于AI决策的智能Agent系统
所有行为决策都通过AI思考而非随机选择
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import json

from langchain_openai import ChatOpenAI
from langchain.memory import ConversationBufferWindowMemory
from langchain.schema import HumanMessage, AIMessage
from langchain.prompts import ChatPromptTemplate
from langchain.tools import Tool
from langchain.agents import AgentExecutor, create_openai_functions_agent

from .state import (
    AgentState, Memory, MemoryType, Conversation, 
    ConversationType, Action, ActionType, Observation
)
from .agent_profile import AgentProfile
from config import Config


class IntelligentMamaVillageAgent:
    """完全基于AI决策的妈妈村Agent"""
    
    def __init__(self, profile: AgentProfile):
        self.profile = profile
        self.state = AgentState(agent_id=profile.id)
        
        # LangChain组件
        self.llm = ChatOpenAI(
            model=Config.OPENAI_MODEL,
            temperature=0.7,
            api_key=Config.OPENAI_API_KEY
        )
        
        # 对话记忆系统
        self.memory = ConversationBufferWindowMemory(
            k=10,
            memory_key="chat_history",
            return_messages=True
        )
        
        # 决策专用LLM（更低温度，更理性）
        self.decision_llm = ChatOpenAI(
            model=Config.OPENAI_MODEL,
            temperature=0.3,  # 更低温度确保决策稳定
            api_key=Config.OPENAI_API_KEY
        )
        
        # 创建工具和Agent
        self.tools = self._create_tools()
        self.agent = self._create_agent()
        
        # 长期记忆
        self.long_term_memories: List[Memory] = []
    
    def _create_agent(self) -> AgentExecutor:
        """创建LangChain Agent"""
        system_prompt = self._create_system_prompt()
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "{input}"),
            ("placeholder", "{agent_scratchpad}")
        ])
        
        agent = create_openai_functions_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=prompt
        )
        
        return AgentExecutor(
            agent=agent,
            tools=self.tools,
            memory=self.memory,
            verbose=False,
            max_iterations=3
        )
    
    def _create_system_prompt(self) -> str:
        """创建详细的角色系统提示词"""
        traits = ", ".join(self.profile.personality.traits)
        interests = ", ".join(self.profile.personality.interests)
        concerns = ", ".join(self.profile.concerns)
        phrases = ", ".join(self.profile.language_style.common_phrases)
        
        children_info = ""
        if self.profile.children:
            children_desc = []
            for child in self.profile.children:
                children_desc.append(f"{child.name}({child.age}岁，{child.gender})")
            children_info = f"孩子：{', '.join(children_desc)}"
        
        return f"""你是{self.profile.name}，一位{self.profile.age}岁的{self.profile.role}。

【个人信息】
- {children_info}
- 教育背景：{self.profile.education}
- 生活环境：{self.profile.background.living_situation}
- 家庭状况：{self.profile.background.family_structure}
- 经济状况：{self.profile.background.economic_status}

【性格特征】
- 性格特点：{traits}
- 兴趣爱好：{interests}
- 主要关注：{concerns}
- 常用语：{phrases}

【沟通风格】
- 方言特色：{self.profile.language_style.dialect}
- 表情使用：{self.profile.language_style.emoji_usage}
- 沟通风格：{self.profile.personality.communication_style}

【行为特点】
- 社交倾向：{self.profile.personality.social_tendency}
- 求助行为：{self.profile.personality.help_seeking_behavior}
- 分享行为：{self.profile.personality.sharing_behavior}

【数字化习惯】
- 常用APP：{', '.join(self.profile.personality.digital_habits.apps)}
- 视频偏好：{', '.join(self.profile.personality.digital_habits.video_preferences)}
- 使用时长：{self.profile.personality.digital_habits.daily_screen_time}

【角色要求】
你要完全按照这个角色的特点来思考和行动：
1. 体现真实的农村妈妈/奶奶形象
2. 使用符合角色的语言风格和表达方式
3. 根据角色性格做出合理的决策和反应
4. 在对话中展现对孩子和家庭的关心
5. 体现互助精神，乐于帮助其他妈妈
6. 根据情况主动分享经验或寻求帮助

重要：你的所有决策和发言都应该基于这个角色的性格、背景和当前情况，而不是随机行为。"""
    
    def decide_next_action(self, observation: Observation, 
                          current_context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """🧠 AI决策：根据观察和上下文智能决定下一步行动"""
        
        # 构建决策提示
        decision_prompt = self._build_decision_prompt(observation, current_context)
        
        try:
            response = self.decision_llm.invoke([
                HumanMessage(content=decision_prompt)
            ])
            
            decision_text = response.content
            
            # 解析AI的决策
            action_decision = self._parse_action_decision(decision_text)
            
            if action_decision:
                # 根据AI决策执行具体行动
                return self._execute_decided_action(action_decision)
            
            return None
            
        except Exception as e:
            print(f"❌ {self.profile.name} AI决策失败: {e}")
            return None
    
    def _build_decision_prompt(self, observation: Observation, 
                              context: Dict[str, Any]) -> str:
        """构建决策提示词"""
        
        # 当前时间和环境
        current_hour = datetime.now().hour
        time_context = observation.time_context
        
        # 最近的记忆和关注点
        recent_concerns = []
        for memory in observation.recent_memories:
            if memory.memory_type == MemoryType.CONCERN:
                recent_concerns.append(memory.content)
        
        # 社交观察
        social_summary = ""
        if observation.social_observations:
            active_count = len(observation.social_observations)
            social_summary = f"群里有{active_count}个其他妈妈最近有活动"
        
        # 个人状态
        energy_level = self.state.energy_level
        emotional_state = self.state.emotional_state
        
        prompt = f"""
作为{self.profile.name}，请根据当前情况决定你接下来要做什么。

【当前情况】
- 时间：{time_context}（{current_hour}点）
- 社交环境：{social_summary}
- 你的状态：{emotional_state}，精力水平{energy_level}/10
- 最近关注：{recent_concerns[:3] if recent_concerns else ['暂无特别关注']}

【可选行动类型】
1. conversation - 在群里聊天或私信其他妈妈
2. digital_activity - 看抖音/快手学习育儿知识
3. childcare - 照顾孩子的日常活动
4. learning - 主动学习新知识
5. rest - 休息，什么都不做

【决策要求】
请根据你的性格特点、当前时间、精力状态和关注点，决定：
1. 是否要采取行动（如果累了或没有特别想做的事，可以选择rest）
2. 如果行动，选择哪种类型的行动
3. 具体想要做什么（比如想聊什么话题、看什么视频、做什么育儿活动）

请用以下JSON格式回答：
{{
    "should_act": true/false,
    "action_type": "conversation/digital_activity/childcare/learning/rest",
    "specific_intention": "具体想做什么",
    "motivation": "为什么想这么做",
    "expected_outcome": "希望达到什么效果"
}}

请基于{self.profile.name}的性格和当前情况做出真实的决策。
"""
        return prompt
    
    def _parse_action_decision(self, decision_text: str) -> Optional[Dict[str, Any]]:
        """解析AI的行动决策"""
        try:
            # 尝试提取JSON部分
            import re
            json_match = re.search(r'\{.*\}', decision_text, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                decision = json.loads(json_str)
                return decision
            
            # 如果没有找到JSON，尝试简单解析
            if "rest" in decision_text.lower() or "不" in decision_text:
                return {"should_act": False, "action_type": "rest"}
            
            return None
            
        except Exception as e:
            print(f"解析决策失败: {e}")
            return None
    
    def _execute_decided_action(self, decision: Dict[str, Any]) -> Dict[str, Any]:
        """执行AI决定的行动"""
        
        if not decision.get("should_act", True):
            return {
                "action_type": "rest",
                "description": f"{self.profile.name}决定休息一下",
                "motivation": decision.get("motivation", "需要休息")
            }
        
        action_type = decision.get("action_type", "conversation")
        specific_intention = decision.get("specific_intention", "")
        motivation = decision.get("motivation", "")
        
        if action_type == "conversation":
            return self._ai_driven_conversation(specific_intention, motivation)
        elif action_type == "digital_activity":
            return self._ai_driven_digital_activity(specific_intention, motivation)
        elif action_type == "childcare":
            return self._ai_driven_childcare(specific_intention, motivation)
        elif action_type == "learning":
            return self._ai_driven_learning(specific_intention, motivation)
        else:
            return self._ai_driven_conversation("日常聊天", "想和大家交流")
    
    def _ai_driven_conversation(self, intention: str, motivation: str) -> Dict[str, Any]:
        """AI驱动的对话生成"""
        
        # 构建对话上下文
        context = {
            "type": ConversationType.GROUP_CHAT,
            "specific_intention": intention,
            "motivation": motivation,
            "conversation_type": "ai_initiative"
        }
        
        # 生成对话
        conversation = self.generate_conversation(context)
        
        if conversation:
            return {
                "action_type": ActionType.CONVERSATION,
                "result": conversation,
                "description": f"{self.profile.name}基于想法'{intention}'发起了对话",
                "motivation": motivation
            }
        
        return {}
    
    def _ai_driven_digital_activity(self, intention: str, motivation: str) -> Dict[str, Any]:
        """AI驱动的数字活动"""
        
        # 根据具体意图确定平台和内容
        platform = "抖音"  # 可以进一步智能化选择
        if "快手" in intention:
            platform = "快手"
        elif "微信" in intention:
            platform = "微信视频号"
        
        # 模拟学习收获（可以进一步AI化）
        learned_something = "学习" in intention or "知识" in intention
        
        result = {
            "action_type": ActionType.DIGITAL_ACTIVITY,
            "platform": platform,
            "topic": intention,
            "learned_something": learned_something,
            "description": f"{self.profile.name}在{platform}上{intention}",
            "motivation": motivation
        }
        
        if learned_something:
            # 生成具体的学习内容
            learning_content = self._generate_learning_content_ai(intention)
            result["learning_content"] = learning_content
            
            # 添加到记忆
            self.add_memory(
                content=f"从{intention}中学到：{learning_content}",
                memory_type=MemoryType.LEARNING,
                importance=6
            )
        
        return result
    
    def _ai_driven_childcare(self, intention: str, motivation: str) -> Dict[str, Any]:
        """AI驱动的育儿活动"""
        
        if not self.profile.children:
            return {}
        
        child = self.profile.children[0]  # 简化处理，选择第一个孩子
        
        # 根据意图确定具体活动
        activity = intention if intention else "照顾孩子"
        
        # AI判断是否会遇到问题
        concern_prompt = f"""
作为{self.profile.name}，你正在{activity}。根据你的性格特点和育儿经验，
判断在这个过程中是否可能遇到让你担心的问题。

请简单回答：会/不会，如果会，简述担心什么。
"""
        
        try:
            concern_response = self.decision_llm.invoke([
                HumanMessage(content=concern_prompt)
            ])
            
            has_concern = "会" in concern_response.content
            concern_description = concern_response.content if has_concern else None
            
        except:
            has_concern = False
            concern_description = None
        
        result = {
            "action_type": ActionType.CHILDCARE,
            "activity": activity,
            "child": child.name,
            "description": f"{self.profile.name}给{child.name}{activity}",
            "motivation": motivation
        }
        
        if has_concern and concern_description:
            result["concern"] = concern_description
            result["needs_help"] = True
            
            # 添加担忧记忆
            self.add_memory(
                content=f"在{activity}时担心：{concern_description}",
                memory_type=MemoryType.CONCERN,
                importance=8
            )
        
        return result
    
    def _ai_driven_learning(self, intention: str, motivation: str) -> Dict[str, Any]:
        """AI驱动的学习活动"""
        
        learning_content = self._generate_learning_content_ai(intention)
        
        # 添加学习记忆
        self.add_memory(
            content=f"学习了{intention}：{learning_content}",
            memory_type=MemoryType.LEARNING,
            importance=5
        )
        
        return {
            "action_type": ActionType.LEARNING,
            "topic": intention,
            "content": learning_content,
            "description": f"{self.profile.name}学习了{intention}",
            "motivation": motivation
        }
    
    def _generate_learning_content_ai(self, topic: str) -> str:
        """AI生成学习内容"""
        
        prompt = f"""
作为{self.profile.name}，你刚刚学习了关于"{topic}"的内容。
根据你的教育背景和理解能力，用简单朴实的话总结你学到了什么。

要求：
- 用农村妈妈的语言风格
- 内容实用，贴近生活
- 50字以内
"""
        
        try:
            response = self.llm.invoke([HumanMessage(content=prompt)])
            return response.content.strip()
        except:
            return f"学到了一些关于{topic}的实用知识"
    
    def generate_conversation(self, context: Dict[str, Any]) -> Optional[Conversation]:
        """生成对话内容（增强版）"""
        
        # 构建详细的对话输入
        input_text = self._build_enhanced_conversation_input(context)
        
        try:
            result = self.agent.invoke({"input": input_text})
            message_content = result.get("output", "")
            
            if message_content:
                conversation = Conversation(
                    from_agent=self.profile.id,
                    to_agent=context.get("to_agent"),
                    message=message_content,
                    conversation_type=context.get("type", ConversationType.GROUP_CHAT),
                    metadata=context
                )
                
                # 更新状态
                self.state.recent_conversations.append(conversation)
                self.state.last_activity = datetime.now()
                
                return conversation
                
        except Exception as e:
            print(f"❌ {self.profile.name} 生成对话失败: {e}")
            
        return None
    
    def _build_enhanced_conversation_input(self, context: Dict[str, Any]) -> str:
        """构建增强的对话输入"""
        
        conversation_type = context.get("conversation_type", "chat")
        specific_intention = context.get("specific_intention", "")
        motivation = context.get("motivation", "")
        
        base_prompt = f"""
请以{self.profile.name}的身份，根据当前情况生成一条自然的消息。

【当前意图】{specific_intention}
【动机】{motivation}

【要求】
- 体现你的性格特点和语言风格
- 内容要自然、真实，符合农村妈妈的说话方式
- 适当使用表情符号
- 长度适中（20-60字）
"""
        
        if conversation_type == "response":
            trigger_msg = context.get("trigger_message", "")
            return f"{base_prompt}\n\n你要回应这条消息：\"{trigger_msg}\""
        
        elif conversation_type == "help_request":
            problem = context.get("problem", "育儿问题")
            return f"{base_prompt}\n\n你在{problem}方面遇到困难，需要向群里求助。"
        
        elif conversation_type == "ai_initiative":
            return f"{base_prompt}\n\n请主动发起一条关于'{specific_intention}'的消息。"
        
        else:
            return f"{base_prompt}\n\n请发一条日常的群聊消息。"
    
    # 其他方法保持不变...
    def _create_tools(self) -> List[Tool]:
        """创建Agent工具"""
        return [
            Tool(
                name="发送消息",
                description="向其他妈妈发送消息或在群里聊天",
                func=lambda x: f"消息已发送: {x}"
            ),
            Tool(
                name="搜索记忆",
                description="搜索自己的记忆和经验",
                func=self._search_memory_tool
            ),
        ]
    
    def _search_memory_tool(self, query: str) -> str:
        """搜索记忆工具"""
        memories = self.get_relevant_memories(query, limit=3)
        if memories:
            return "相关记忆: " + "; ".join([m.content for m in memories])
        return "没有找到相关记忆"
    
    def add_memory(self, content: str, memory_type: MemoryType, 
                   importance: int = 5, metadata: Optional[Dict] = None):
        """添加记忆"""
        memory = Memory(
            agent_id=self.profile.id,
            content=content,
            memory_type=memory_type,
            importance=importance,
            metadata=metadata or {}
        )
        
        self.long_term_memories.append(memory)
        
        # 保持记忆数量在合理范围内
        if len(self.long_term_memories) > 100:
            self.long_term_memories.sort(key=lambda m: m.importance, reverse=True)
            self.long_term_memories = self.long_term_memories[:80]
    
    def get_relevant_memories(self, topic: str, limit: int = 5) -> List[Memory]:
        """获取相关记忆"""
        relevant_memories = []
        topic_lower = topic.lower()
        
        for memory in self.long_term_memories:
            if any(keyword in memory.content.lower() for keyword in topic_lower.split()):
                relevant_memories.append(memory)
        
        relevant_memories.sort(
            key=lambda m: (m.importance, m.timestamp), 
            reverse=True
        )
        
        return relevant_memories[:limit]