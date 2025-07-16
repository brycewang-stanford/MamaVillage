"""
MamaVillage Agent 配置文件系统
基于 Pydantic 的类型安全配置模型
"""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, validator
from enum import Enum
from .state import AgentRole


class Education(str, Enum):
    """教育水平枚举"""
    PRIMARY = "小学"
    MIDDLE = "初中"
    HIGH = "高中"
    VOCATIONAL = "职高/中专"
    COLLEGE = "大专"
    BACHELOR = "本科"
    UNKNOWN = "未知"


class Child(BaseModel):
    """孩子信息模型"""
    name: str
    age: int = Field(ge=0, le=20)
    gender: str
    special_needs: Optional[str] = None
    health_status: str = "健康"


class DigitalHabits(BaseModel):
    """数字化习惯模型"""
    apps: List[str] = Field(default_factory=lambda: ["微信", "抖音"])
    video_preferences: List[str] = Field(default_factory=lambda: ["育儿知识"])
    daily_screen_time: str = "2-3小时"
    preferred_platforms: List[str] = Field(default_factory=lambda: ["抖音", "快手"])
    learning_sources: List[str] = Field(default_factory=lambda: ["短视频", "微信文章"])


class Personality(BaseModel):
    """个性特征模型"""
    traits: List[str] = Field(default_factory=list)
    interests: List[str] = Field(default_factory=lambda: ["育儿知识"])
    communication_style: str = "口语化"
    digital_habits: DigitalHabits = Field(default_factory=DigitalHabits)
    social_tendency: str = "积极参与"  # 积极参与, 被动观察, 偶尔互动
    help_seeking_behavior: str = "遇到问题会主动求助"
    sharing_behavior: str = "乐于分享经验"


class LanguageStyle(BaseModel):
    """语言风格模型"""
    dialect: str = "普通话"
    common_phrases: List[str] = Field(default_factory=list)
    emoji_usage: str = "适度使用表情"
    formality_level: str = "非正式"  # 正式, 非正式, 随意
    response_length: str = "简短"  # 简短, 中等, 详细


class BackgroundInfo(BaseModel):
    """背景信息模型"""
    living_situation: str = "农村"
    family_structure: str = "核心家庭"
    economic_status: str = "中等"
    support_network: List[str] = Field(default_factory=lambda: ["家人", "邻居", "网络朋友"])
    challenges: List[str] = Field(default_factory=list)
    strengths: List[str] = Field(default_factory=list)


class AgentProfile(BaseModel):
    """Agent完整配置文件"""
    # 基本信息
    id: str
    name: str
    age: int = Field(ge=15, le=80)
    education: Education = Education.UNKNOWN
    role: AgentRole
    
    # 家庭信息
    children: List[Child] = Field(default_factory=list)
    spouse_status: Optional[str] = None
    extended_family: List[str] = Field(default_factory=list)
    
    # 个性和习惯
    personality: Personality = Field(default_factory=Personality)
    language_style: LanguageStyle = Field(default_factory=LanguageStyle)
    background: BackgroundInfo = Field(default_factory=BackgroundInfo)
    
    # 关注和知识领域
    concerns: List[str] = Field(default_factory=lambda: ["孩子健康"])
    knowledge_areas: List[str] = Field(default_factory=lambda: ["基础育儿"])
    learning_interests: List[str] = Field(default_factory=lambda: ["育儿知识"])
    
    # 社交网络
    social_connections: List[str] = Field(default_factory=list)  # 其他Agent的ID
    group_memberships: List[str] = Field(default_factory=lambda: ["妈妈群"])
    
    # 活动偏好
    preferred_activities: List[str] = Field(default_factory=lambda: ["照顾孩子", "刷手机"])
    active_hours: List[int] = Field(default_factory=lambda: list(range(6, 23)))
    
    # 模拟参数
    response_probability: float = Field(ge=0.0, le=1.0, default=0.7)
    initiative_level: float = Field(ge=0.0, le=1.0, default=0.5)
    help_seeking_threshold: int = Field(ge=1, le=10, default=6)
    
    @validator('active_hours')
    def validate_active_hours(cls, v):
        """验证活跃时间"""
        return [h for h in v if 0 <= h <= 23]
    
    @validator('age')
    def validate_age_role_consistency(cls, v, values):
        """验证年龄和角色的一致性"""
        if 'role' in values:
            role = values['role']
            if role == AgentRole.YOUNG_MOTHER and v > 35:
                raise ValueError("年轻妈妈年龄不应超过35岁")
            elif role == AgentRole.GRANDMOTHER and v < 45:
                raise ValueError("奶奶年龄不应小于45岁")
        return v
    
    def get_personality_summary(self) -> str:
        """获取个性摘要"""
        traits = ", ".join(self.personality.traits[:3])
        return f"{self.name}是一位{self.age}岁的{self.role}，性格{traits}"
    
    def is_active_at_hour(self, hour: int) -> bool:
        """检查在指定时间是否活跃"""
        return hour in self.active_hours
    
    def get_video_preferences(self) -> List[str]:
        """获取视频偏好"""
        return self.personality.digital_habits.video_preferences
    
    def get_common_topics(self) -> List[str]:
        """获取常见聊天话题"""
        return self.concerns + self.personality.interests
    
    def should_respond_to_topic(self, topic: str) -> bool:
        """判断是否应该回应某个话题"""
        relevant_topics = self.get_common_topics()
        return any(keyword in topic for keyword in relevant_topics)


class AgentProfileManager:
    """Agent配置文件管理器"""
    
    def __init__(self):
        self.profiles: Dict[str, AgentProfile] = {}
    
    def load_profile_from_dict(self, profile_data: Dict[str, Any]) -> AgentProfile:
        """从字典加载配置文件"""
        return AgentProfile(**profile_data)
    
    def add_profile(self, profile: AgentProfile):
        """添加配置文件"""
        self.profiles[profile.id] = profile
    
    def get_profile(self, agent_id: str) -> Optional[AgentProfile]:
        """获取配置文件"""
        return self.profiles.get(agent_id)
    
    def get_all_profiles(self) -> List[AgentProfile]:
        """获取所有配置文件"""
        return list(self.profiles.values())
    
    def get_profiles_by_role(self, role: AgentRole) -> List[AgentProfile]:
        """按角色获取配置文件"""
        return [p for p in self.profiles.values() if p.role == role]
    
    def get_active_profiles(self, current_hour: int) -> List[AgentProfile]:
        """获取当前时间活跃的配置文件"""
        return [p for p in self.profiles.values() if p.is_active_at_hour(current_hour)]
    
    def validate_all_profiles(self) -> List[str]:
        """验证所有配置文件，返回错误列表"""
        errors = []
        for profile in self.profiles.values():
            try:
                # Pydantic会自动验证
                profile.dict()
            except Exception as e:
                errors.append(f"配置文件 {profile.id} 验证失败: {e}")
        return errors