from typing import Dict, List, Any, Optional
from datetime import datetime
import json
import os
from memory.database import MemoryDatabase

class ObserverNode:
    """观察者节点 - 负责感知环境、记录事件和生成观察记录"""
    
    def __init__(self, db: MemoryDatabase):
        self.db = db
    
    def observe_environment(self, agent_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """观察环境变化和社区动态"""
        observations = []
        
        # 观察其他agent的最新对话
        recent_conversations = self.db.get_conversation_history(agent_id, limit=5)
        if recent_conversations:
            observations.append({
                "type": "social_activity",
                "content": f"观察到最近社区里有{len(recent_conversations)}条新消息",
                "details": recent_conversations[:3]  # 只保留最近3条作为细节
            })
        
        # 观察时间背景
        current_hour = datetime.now().hour
        time_context = self._get_time_context(current_hour)
        observations.append({
            "type": "time_context",
            "content": time_context,
            "hour": current_hour
        })
        
        # 观察自己的状态和需求
        recent_memories = self.db.get_recent_memories(agent_id, limit=3)
        if recent_memories:
            observations.append({
                "type": "self_state",
                "content": "回顾自己最近关注的事情",
                "recent_concerns": [mem['content'] for mem in recent_memories]
            })
        
        return {
            "agent_id": agent_id,
            "timestamp": datetime.now().isoformat(),
            "observations": observations,
            "environment_state": context
        }
    
    def observe_conversation(self, agent_id: str, conversation_data: Dict[str, Any]) -> Dict[str, Any]:
        """观察并记录对话事件"""
        observation = {
            "type": "conversation_observation",
            "agent_id": agent_id,
            "timestamp": datetime.now().isoformat(),
            "conversation": conversation_data
        }
        
        # 分析对话的重要性
        importance = self._assess_conversation_importance(conversation_data)
        observation["importance"] = importance
        
        # 提取关键信息
        key_info = self._extract_key_information(conversation_data)
        if key_info:
            observation["key_information"] = key_info
        
        # 记录到数据库
        self.db.add_memory(
            agent_id=agent_id,
            memory_type="observation",
            content=f"对话观察：{conversation_data.get('message', '')}",
            importance=importance,
            metadata=observation
        )
        
        return observation
    
    def observe_digital_activity(self, agent_id: str, activity: Dict[str, Any]) -> Dict[str, Any]:
        """观察数字活动（如看视频、收到消息等）"""
        observation = {
            "type": "digital_activity",
            "agent_id": agent_id,
            "timestamp": datetime.now().isoformat(),
            "activity": activity
        }
        
        # 判断活动类型和重要性
        activity_type = activity.get("type", "unknown")
        importance = 1
        
        if activity_type == "watch_video":
            importance = 3 if "育儿" in activity.get("content", "") else 2
            observation["learning_opportunity"] = True
        elif activity_type == "receive_message":
            importance = 4 if activity.get("urgent", False) else 2
        elif activity_type == "share_content":
            importance = 3
            observation["social_behavior"] = True
        
        observation["importance"] = importance
        
        # 记录观察
        self.db.add_memory(
            agent_id=agent_id,
            memory_type="observation",
            content=f"数字活动：{activity_type} - {activity.get('description', '')}",
            importance=importance,
            metadata=observation
        )
        
        return observation
    
    def observe_child_event(self, agent_id: str, child_event: Dict[str, Any]) -> Dict[str, Any]:
        """观察孩子相关事件"""
        observation = {
            "type": "child_event",
            "agent_id": agent_id,
            "timestamp": datetime.now().isoformat(),
            "event": child_event
        }
        
        # 孩子事件通常重要性较高
        event_type = child_event.get("type", "general")
        importance_map = {
            "health_concern": 8,
            "milestone": 6,
            "behavior_issue": 5,
            "learning": 4,
            "general": 3
        }
        
        importance = importance_map.get(event_type, 3)
        observation["importance"] = importance
        
        # 如果是健康问题，标记为需要寻求帮助
        if event_type == "health_concern":
            observation["needs_help"] = True
            observation["urgency"] = "high"
        
        # 记录观察
        self.db.add_memory(
            agent_id=agent_id,
            memory_type="observation",
            content=f"孩子事件：{child_event.get('description', '')}",
            importance=importance,
            metadata=observation
        )
        
        return observation
    
    def _get_time_context(self, hour: int) -> str:
        """根据时间生成上下文描述"""
        if 6 <= hour < 9:
            return "早上，该准备早餐和送孩子的时间"
        elif 9 <= hour < 12:
            return "上午，比较清闲的时间，可以刷手机学习"
        elif 12 <= hour < 14:
            return "中午，吃饭和午休时间"
        elif 14 <= hour < 17:
            return "下午，孩子可能要午睡，有时间看视频"
        elif 17 <= hour < 20:
            return "傍晚，准备晚饭，比较忙碌"
        elif 20 <= hour < 22:
            return "晚上，一家人在一起，可能会聊天或看手机"
        else:
            return "深夜，应该休息了，但可能还在刷手机"
    
    def _assess_conversation_importance(self, conversation: Dict[str, Any]) -> int:
        """评估对话的重要性 (1-10)"""
        message = conversation.get("message", "").lower()
        
        # 健康相关 - 高重要性
        if any(keyword in message for keyword in ["发烧", "生病", "医院", "不舒服", "咳嗽"]):
            return 8
        
        # 育儿知识分享 - 中高重要性  
        if any(keyword in message for keyword in ["经验", "方法", "建议", "推荐"]):
            return 6
        
        # 日常关怀 - 中等重要性
        if any(keyword in message for keyword in ["怎么样", "好吗", "辛苦"]):
            return 4
        
        # 普通聊天 - 低重要性
        return 2
    
    def _extract_key_information(self, conversation: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """从对话中提取关键信息"""
        message = conversation.get("message", "")
        
        key_info = {}
        
        # 健康相关信息
        if any(keyword in message for keyword in ["发烧", "生病", "医院"]):
            key_info["category"] = "health"
            key_info["urgency"] = "high"
        
        # 产品推荐信息
        if any(keyword in message for keyword in ["推荐", "好用", "链接"]):
            key_info["category"] = "recommendation"
            key_info["actionable"] = True
        
        # 经验分享信息
        if any(keyword in message for keyword in ["经验", "方法", "技巧"]):
            key_info["category"] = "knowledge_sharing"
            key_info["learning_value"] = True
        
        return key_info if key_info else None