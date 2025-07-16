"""
MamaVillage 核心状态管理系统
基于 Pydantic 的类型安全状态定义
"""

from typing import Dict, List, Optional, Any, Literal, Union
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


class ActionType(str, Enum):
    """行动类型枚举"""
    OBSERVE = "observe"
    PLAN = "plan"
    EXECUTE = "execute"
    REFLECT = "reflect"
    CONVERSATION = "conversation"
    DIGITAL_ACTIVITY = "digital_activity"
    CHILDCARE = "childcare"
    LEARNING = "learning"


class MemoryType(str, Enum):
    """记忆类型枚举"""
    OBSERVATION = "observation"
    PLAN = "plan"
    ACTION = "action"
    REFLECTION = "reflection"
    CONVERSATION = "conversation"
    LEARNING = "learning"
    CONCERN = "concern"


class ConversationType(str, Enum):
    """对话类型枚举"""
    GROUP_CHAT = "group_chat"
    PRIVATE_CHAT = "private_chat"
    HELP_REQUEST = "help_request"
    ADVICE = "advice"
    CONTENT_SHARING = "content_sharing"


class AgentRole(str, Enum):
    """Agent角色枚举"""
    YOUNG_MOTHER = "年轻妈妈"
    EXPERIENCED_MOTHER = "有经验的妈妈"
    GRANDMOTHER = "奶奶"
    SOCIAL_WORKER = "社工"


class Memory(BaseModel):
    """记忆模型"""
    id: Optional[str] = None
    agent_id: str
    content: str
    memory_type: MemoryType
    importance: int = Field(ge=1, le=10)
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Optional[Dict[str, Any]] = None
    embedding: Optional[List[float]] = None  # 为未来语义搜索预留


class Conversation(BaseModel):
    """对话模型"""
    id: Optional[str] = None
    from_agent: str
    to_agent: Optional[str] = None  # None表示群聊
    message: str
    conversation_type: ConversationType = ConversationType.GROUP_CHAT
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Optional[Dict[str, Any]] = None


class Action(BaseModel):
    """行动模型"""
    id: Optional[str] = None
    action_type: ActionType
    description: str
    priority: int = Field(ge=1, le=10, default=5)
    status: Literal["pending", "in_progress", "completed"] = "pending"
    planned_time: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class Observation(BaseModel):
    """观察结果模型"""
    agent_id: str
    environment_state: Dict[str, Any]
    social_observations: List[Dict[str, Any]] = Field(default_factory=list)
    time_context: str
    recent_memories: List[Memory] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.now)


class Plan(BaseModel):
    """计划模型"""
    agent_id: str
    actions: List[Action] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    valid_until: Optional[datetime] = None
    context: Optional[Dict[str, Any]] = None


class Reflection(BaseModel):
    """反思模型"""
    agent_id: str
    content: str
    insights: List[str] = Field(default_factory=list)
    emotional_state: Optional[str] = None
    importance: int = Field(ge=1, le=10, default=5)
    timestamp: datetime = Field(default_factory=datetime.now)


class AgentState(BaseModel):
    """Agent状态模型"""
    agent_id: str
    current_action: Optional[Action] = None
    current_observation: Optional[Observation] = None
    current_plan: Optional[Plan] = None
    recent_conversations: List[Conversation] = Field(default_factory=list)
    active_memories: List[Memory] = Field(default_factory=list)
    emotional_state: str = "平静"
    energy_level: int = Field(ge=1, le=10, default=7)
    last_activity: datetime = Field(default_factory=datetime.now)


class SimulationState(BaseModel):
    """模拟系统全局状态"""
    tick_count: int = 0
    simulation_day: int = 1
    current_time: datetime = Field(default_factory=datetime.now)
    active_agents: List[str] = Field(default_factory=list)
    agent_states: Dict[str, AgentState] = Field(default_factory=dict)
    global_events: List[Dict[str, Any]] = Field(default_factory=list)
    conversation_count: int = 0
    max_conversations: Optional[int] = None
    
    def get_agent_state(self, agent_id: str) -> Optional[AgentState]:
        """获取指定Agent的状态"""
        return self.agent_states.get(agent_id)
    
    def update_agent_state(self, agent_id: str, agent_state: AgentState):
        """更新Agent状态"""
        self.agent_states[agent_id] = agent_state
    
    def add_conversation(self, conversation: Conversation):
        """添加对话并更新计数"""
        self.conversation_count += 1
        # 更新相关Agent状态
        if conversation.from_agent in self.agent_states:
            self.agent_states[conversation.from_agent].recent_conversations.append(conversation)
        if conversation.to_agent and conversation.to_agent in self.agent_states:
            self.agent_states[conversation.to_agent].recent_conversations.append(conversation)
    
    def is_conversation_limit_reached(self) -> bool:
        """检查是否达到对话限制"""
        if self.max_conversations is None:
            return False
        return self.conversation_count >= self.max_conversations


class NodeOutput(BaseModel):
    """节点输出模型"""
    success: bool = True
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    next_action: Optional[str] = None


class WorkflowState(BaseModel):
    """工作流状态模型"""
    simulation_state: SimulationState
    current_agent_id: Optional[str] = None
    current_node: Optional[str] = None
    node_outputs: Dict[str, NodeOutput] = Field(default_factory=dict)
    workflow_metadata: Dict[str, Any] = Field(default_factory=dict)
    
    def get_current_agent_state(self) -> Optional[AgentState]:
        """获取当前Agent状态"""
        if not self.current_agent_id:
            return None
        return self.simulation_state.get_agent_state(self.current_agent_id)
    
    def add_node_output(self, node_name: str, output: NodeOutput):
        """添加节点输出"""
        self.node_outputs[node_name] = output