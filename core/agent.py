"""
MamaVillage 核心 Agent 系统
基于 LangChain 的现代化 Agent 实现
"""

from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
import json
import random

from langchain_openai import ChatOpenAI
from langchain.memory import ConversationBufferWindowMemory
from langchain.schema import BaseMessage, HumanMessage, AIMessage
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.tools import Tool
from langchain.agents import AgentExecutor, create_openai_functions_agent

from .state import (
    AgentState, Memory, MemoryType, Conversation, 
    ConversationType, Action, ActionType, Observation
)
from .agent_profile import AgentProfile
from config import Config


class MamaVillageAgent:
    """妈妈村Agent核心类"""
    
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
            k=10,  # 保留最近10轮对话
            memory_key="chat_history",
            return_messages=True
        )
        
        # 创建工具
        self.tools = self._create_tools()
        
        # 创建Agent
        self.agent = self._create_agent()
        
        # 长期记忆存储
        self.long_term_memories: List[Memory] = []
        
    def _create_tools(self) -> List[Tool]:
        """创建Agent可用的工具"""
        tools = [
            Tool(
                name="发送消息",
                description="向其他妈妈发送消息或在群里聊天",
                func=self._send_message_tool
            ),
            Tool(
                name="搜索记忆",
                description="搜索自己的记忆和经验",
                func=self._search_memory_tool
            ),
            Tool(
                name="观看视频",
                description="观看抖音或其他平台的育儿视频",
                func=self._watch_video_tool
            ),
            Tool(
                name="寻求帮助",
                description="当遇到育儿问题时向群里求助",
                func=self._seek_help_tool
            ),
            Tool(
                name="分享经验",
                description="分享自己的育儿经验或有用信息",
                func=self._share_experience_tool
            )
        ]
        return tools
    
    def _create_agent(self) -> AgentExecutor:
        """创建LangChain Agent"""
        
        # 系统提示词
        system_prompt = self._create_system_prompt()
        
        # 创建提示模板
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ])
        
        # 创建OpenAI Functions Agent
        agent = create_openai_functions_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=prompt
        )
        
        # 创建Agent执行器
        agent_executor = AgentExecutor(
            agent=agent,
            tools=self.tools,
            memory=self.memory,
            verbose=True,
            max_iterations=3
        )
        
        return agent_executor
    
    def _create_system_prompt(self) -> str:
        """创建系统提示词"""
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

个人信息：
- {children_info}
- 教育背景：{self.profile.education}
- 生活背景：{self.profile.background.living_situation}

性格特点：{traits}
兴趣爱好：{interests}
主要关注：{concerns}
常用语：{phrases}

语言风格：
- 方言：{self.profile.language_style.dialect}
- 表情符号：{self.profile.language_style.emoji_usage}
- 交流风格：{self.profile.personality.communication_style}

你要模拟这个角色的行为和对话方式，体现：
1. 真实的农村妈妈形象
2. 对孩子和家庭的关心
3. 积极的互助精神
4. 自然的口语化表达
5. 适度使用表情符号

在对话中要：
- 使用符合角色的语言风格
- 体现对育儿和家庭的关注
- 乐于帮助其他妈妈
- 分享自己的经验和知识
- 在遇到问题时主动寻求帮助"""
    
    def process_observation(self, observation: Observation) -> Dict[str, Any]:
        """处理观察结果"""
        self.state.current_observation = observation
        
        # 更新活跃记忆
        self.state.active_memories.extend(observation.recent_memories)
        
        # 如果观察到重要信息，可能会触发行动
        important_observations = [
            obs for obs in observation.social_observations 
            if obs.get("importance", 0) > 6
        ]
        
        response = {"observations_processed": len(observation.social_observations)}
        
        if important_observations:
            response["important_observations"] = important_observations
            response["should_take_action"] = True
            
        return response
    
    def generate_conversation(self, context: Dict[str, Any]) -> Optional[Conversation]:
        """生成对话内容"""
        conversation_type = context.get("type", ConversationType.GROUP_CHAT)
        
        # 构建输入
        input_text = self._build_conversation_input(context)
        
        try:
            # 使用Agent生成回应
            result = self.agent.invoke({"input": input_text})
            message_content = result.get("output", "")
            
            if message_content:
                conversation = Conversation(
                    from_agent=self.profile.id,
                    to_agent=context.get("to_agent"),
                    message=message_content,
                    conversation_type=conversation_type,
                    metadata=context
                )
                
                # 更新状态
                self.state.recent_conversations.append(conversation)
                self.state.last_activity = datetime.now()
                
                return conversation
                
        except Exception as e:
            print(f"❌ {self.profile.name} 生成对话失败: {e}")
            
        return None
    
    def respond_to_message(self, incoming_message: Conversation) -> Optional[Conversation]:
        """回应收到的消息"""
        
        # 判断是否应该回应
        if not self._should_respond_to_message(incoming_message):
            return None
            
        # 构建回应上下文
        context = {
            "type": ConversationType.PRIVATE_CHAT if incoming_message.to_agent else ConversationType.GROUP_CHAT,
            "to_agent": incoming_message.from_agent if incoming_message.to_agent else None,
            "trigger_message": incoming_message.message,
            "conversation_type": "response"
        }
        
        return self.generate_conversation(context)
    
    def take_initiative_action(self) -> Optional[Dict[str, Any]]:
        """主动发起行动"""
        
        # 根据个性和当前状态决定是否主动行动
        if random.random() > self.profile.initiative_level:
            return None
            
        # 选择行动类型
        possible_actions = [
            ActionType.CONVERSATION,
            ActionType.DIGITAL_ACTIVITY,
            ActionType.CHILDCARE,
            ActionType.LEARNING
        ]
        
        action_type = random.choice(possible_actions)
        
        if action_type == ActionType.CONVERSATION:
            return self._initiate_conversation()
        elif action_type == ActionType.DIGITAL_ACTIVITY:
            return self._watch_video()
        elif action_type == ActionType.CHILDCARE:
            return self._perform_childcare()
        elif action_type == ActionType.LEARNING:
            return self._learn_something()
            
        return None
    
    def add_memory(self, content: str, memory_type: MemoryType, 
                   importance: int = 5, metadata: Optional[Dict] = None):
        """添加长期记忆"""
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
            # 移除重要性最低的记忆
            self.long_term_memories.sort(key=lambda m: m.importance, reverse=True)
            self.long_term_memories = self.long_term_memories[:80]
    
    def get_relevant_memories(self, topic: str, limit: int = 5) -> List[Memory]:
        """获取相关记忆"""
        relevant_memories = []
        topic_lower = topic.lower()
        
        for memory in self.long_term_memories:
            if any(keyword in memory.content.lower() for keyword in topic_lower.split()):
                relevant_memories.append(memory)
        
        # 按重要性和时间排序
        relevant_memories.sort(
            key=lambda m: (m.importance, m.timestamp), 
            reverse=True
        )
        
        return relevant_memories[:limit]
    
    def _build_conversation_input(self, context: Dict[str, Any]) -> str:
        """构建对话输入"""
        conversation_type = context.get("conversation_type", "chat")
        
        if conversation_type == "response":
            trigger_msg = context.get("trigger_message", "")
            return f"有人在群里说：\"{trigger_msg}\"。请回应这条消息。"
            
        elif conversation_type == "help_request":
            problem = context.get("problem", "育儿问题")
            return f"我在{problem}方面遇到了困难，需要向群里的妈妈们求助。"
            
        elif conversation_type == "share_experience":
            topic = context.get("topic", "育儿经验")
            return f"想要分享一些关于{topic}的经验给群里的妈妈们。"
            
        else:
            # 日常聊天
            topics = self.profile.get_common_topics()
            topic = random.choice(topics)
            return f"想要在群里聊聊{topic}相关的话题。"
    
    def _should_respond_to_message(self, message: Conversation) -> bool:
        """判断是否应该回应消息"""
        # 基础回应概率
        if random.random() > self.profile.response_probability:
            return False
            
        # 如果是直接发给自己的消息，回应概率更高
        if message.to_agent == self.profile.id:
            return random.random() < 0.9
            
        # 如果消息与自己的兴趣相关，更可能回应
        return self.profile.should_respond_to_topic(message.message)
    
    def _initiate_conversation(self) -> Dict[str, Any]:
        """发起对话"""
        context = {
            "type": ConversationType.GROUP_CHAT,
            "conversation_type": "initiative"
        }
        
        conversation = self.generate_conversation(context)
        if conversation:
            return {
                "action_type": ActionType.CONVERSATION,
                "result": conversation,
                "description": f"{self.profile.name}在群里发起了聊天"
            }
        return {}
    
    def _watch_video(self) -> Dict[str, Any]:
        """观看视频"""
        video_prefs = self.profile.get_video_preferences()
        topic = random.choice(video_prefs)
        platform = random.choice(self.profile.personality.digital_habits.preferred_platforms)
        
        # 模拟学习收获
        learned_something = random.random() < 0.4
        
        result = {
            "action_type": ActionType.DIGITAL_ACTIVITY,
            "topic": topic,
            "platform": platform,
            "learned_something": learned_something,
            "description": f"{self.profile.name}在{platform}看了{topic}视频"
        }
        
        if learned_something:
            learning_content = f"从{topic}视频中学到了新知识"
            self.add_memory(learning_content, MemoryType.LEARNING, importance=6)
            result["learning_content"] = learning_content
            
        return result
    
    def _perform_childcare(self) -> Dict[str, Any]:
        """执行育儿活动"""
        if not self.profile.children:
            return {}
            
        childcare_activities = [
            "喂奶", "换尿布", "陪孩子玩", "给孩子准备食物",
            "检查孩子状况", "教孩子新技能", "哄孩子睡觉"
        ]
        
        activity = random.choice(childcare_activities)
        child = random.choice(self.profile.children)
        
        # 可能遇到问题
        has_concern = random.random() < 0.2
        
        result = {
            "action_type": ActionType.CHILDCARE,
            "activity": activity,
            "child": child.name,
            "description": f"{self.profile.name}给{child.name}{activity}"
        }
        
        if has_concern:
            concern = f"{child.name}在{activity}时有些不太对劲"
            self.add_memory(concern, MemoryType.CONCERN, importance=8)
            result["concern"] = concern
            result["needs_help"] = True
            
        return result
    
    def _learn_something(self) -> Dict[str, Any]:
        """学习新知识"""
        learning_topics = self.profile.learning_interests
        topic = random.choice(learning_topics)
        
        learning_content = f"学习了关于{topic}的新知识"
        self.add_memory(learning_content, MemoryType.LEARNING, importance=5)
        
        return {
            "action_type": ActionType.LEARNING,
            "topic": topic,
            "content": learning_content,
            "description": f"{self.profile.name}学习了{topic}"
        }
    
    # 工具函数实现
    def _send_message_tool(self, recipient_and_message: str) -> str:
        """发送消息工具"""
        # 这里会由外部系统处理实际的消息发送
        return f"消息已发送: {recipient_and_message}"
    
    def _search_memory_tool(self, query: str) -> str:
        """搜索记忆工具"""
        memories = self.get_relevant_memories(query, limit=3)
        if memories:
            return "相关记忆: " + "; ".join([m.content for m in memories])
        return "没有找到相关记忆"
    
    def _watch_video_tool(self, topic: str) -> str:
        """观看视频工具"""
        result = self._watch_video()
        return f"观看了{topic}相关视频"
    
    def _seek_help_tool(self, problem: str) -> str:
        """寻求帮助工具"""
        return f"在群里寻求关于{problem}的帮助"
    
    def _share_experience_tool(self, experience: str) -> str:
        """分享经验工具"""
        return f"分享了经验: {experience}"