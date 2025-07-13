from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import json
import random
from memory.database import MemoryDatabase
from openai import OpenAI
from config import Config

class PlannerNode:
    """计划者节点 - 负责制定agent的每日行为计划"""
    
    def __init__(self, db: MemoryDatabase):
        self.db = db
        self.client = OpenAI(api_key=Config.OPENAI_API_KEY)
    
    def generate_daily_plan(self, agent_id: str, agent_profile: Dict[str, Any]) -> Dict[str, Any]:
        """为agent生成每日行为计划"""
        
        # 获取agent的基本信息和最近记忆
        recent_memories = self.db.get_recent_memories(agent_id, limit=10)
        recent_conversations = self.db.get_conversation_history(agent_id, limit=5)
        
        # 生成计划提示词
        planning_prompt = self._create_planning_prompt(
            agent_profile, recent_memories, recent_conversations
        )
        
        try:
            # 调用GPT生成计划
            response = self.client.chat.completions.create(
                model=Config.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "你是一个专门为中国农村妈妈制定日常计划的AI助手。请根据她们的生活背景和当前情况，制定符合实际的日常活动计划。"},
                    {"role": "user", "content": planning_prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            
            plan_text = response.choices[0].message.content
            daily_plan = self._parse_plan_response(plan_text, agent_id)
            
            # 保存计划到数据库
            self._save_plan_to_database(agent_id, daily_plan)
            
            return daily_plan
            
        except Exception as e:
            print(f"❌ 生成计划失败: {e}")
            # 降级到默认计划
            return self._generate_fallback_plan(agent_id, agent_profile)
    
    def update_plan_based_on_events(self, agent_id: str, event: Dict[str, Any]) -> Dict[str, Any]:
        """根据突发事件更新计划"""
        current_plans = self._get_current_plans(agent_id)
        
        # 分析事件类型和紧急程度
        event_type = event.get("type", "general")
        urgency = event.get("urgency", "low")
        
        updated_plan = {"updated_actions": []}
        
        if event_type == "child_health_emergency":
            # 健康紧急事件 - 重新排列优先级
            urgent_action = {
                "action": "寻求医疗建议或帮助",
                "priority": 10,
                "description": f"处理孩子健康问题：{event.get('description', '')}",
                "planned_time": "立即"
            }
            updated_plan["updated_actions"].append(urgent_action)
            
        elif event_type == "social_opportunity":
            # 社交机会 - 可能加入计划
            if urgency == "high":
                social_action = {
                    "action": "参与社区讨论",
                    "priority": 6,
                    "description": f"回应社区话题：{event.get('topic', '')}",
                    "planned_time": "有时间时"
                }
                updated_plan["updated_actions"].append(social_action)
        
        elif event_type == "learning_opportunity":
            # 学习机会
            learning_action = {
                "action": "观看学习内容",
                "priority": 4,
                "description": f"学习新知识：{event.get('content', '')}",
                "planned_time": "空闲时间"
            }
            updated_plan["updated_actions"].append(learning_action)
        
        # 保存更新的计划
        if updated_plan["updated_actions"]:
            self._save_plan_updates(agent_id, updated_plan)
        
        return updated_plan
    
    def _create_planning_prompt(self, agent_profile: Dict[str, Any], 
                               memories: List[Dict], conversations: List[Dict]) -> str:
        """创建计划生成的提示词"""
        
        # 基本信息
        name = agent_profile.get("name", "")
        age = agent_profile.get("age", "")
        role = agent_profile.get("role", "")
        children = agent_profile.get("children", [])
        concerns = agent_profile.get("concerns", [])
        
        # 最近的关注点
        recent_concerns = []
        for memory in memories[:5]:
            if memory.get("memory_type") == "observation":
                recent_concerns.append(memory.get("content", ""))
        
        # 最近的对话主题
        recent_topics = []
        for conv in conversations[:3]:
            recent_topics.append(conv.get("message", ""))
        
        current_hour = datetime.now().hour
        time_period = self._get_time_period(current_hour)
        
        prompt = f"""
请为{name}（{age}岁，{role}）制定今天的活动计划。

个人背景：
- 孩子情况：{children}
- 主要关注：{concerns}
- 最近关心的事：{recent_concerns[:3]}
- 最近聊天内容：{recent_topics}

当前时间：{time_period}

请生成3-5个具体的行动计划，格式如下：
1. 行动：[具体行动]
   优先级：[1-10]
   描述：[详细描述为什么要做这件事]
   计划时间：[什么时候做]

要求：
- 符合农村妈妈的实际生活节奏
- 考虑孩子的需求和时间安排
- 包含适当的数字活动（刷手机、看视频等）
- 体现她的性格特点和关注点
- 语言要自然口语化
"""
        
        return prompt
    
    def _parse_plan_response(self, plan_text: str, agent_id: str) -> Dict[str, Any]:
        """解析GPT返回的计划文本"""
        
        actions = []
        lines = plan_text.strip().split('\n')
        
        current_action = {}
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            if line.startswith(('1.', '2.', '3.', '4.', '5.')):
                # 保存前一个行动
                if current_action.get("action"):
                    actions.append(current_action.copy())
                
                # 开始新行动
                current_action = {
                    "action": line.split('：', 1)[-1] if '：' in line else line,
                    "priority": 5,  # 默认优先级
                    "description": "",
                    "planned_time": "待定",
                    "status": "pending"
                }
            
            elif "优先级" in line:
                try:
                    priority = int(''.join(filter(str.isdigit, line)))
                    current_action["priority"] = min(10, max(1, priority))
                except:
                    current_action["priority"] = 5
            
            elif "描述" in line:
                current_action["description"] = line.split('：', 1)[-1] if '：' in line else line
            
            elif "计划时间" in line or "时间" in line:
                current_action["planned_time"] = line.split('：', 1)[-1] if '：' in line else line
        
        # 添加最后一个行动
        if current_action.get("action"):
            actions.append(current_action)
        
        return {
            "agent_id": agent_id,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "timestamp": datetime.now().isoformat(),
            "actions": actions,
            "total_actions": len(actions)
        }
    
    def _generate_fallback_plan(self, agent_id: str, agent_profile: Dict[str, Any]) -> Dict[str, Any]:
        """生成降级的默认计划"""
        role = agent_profile.get("role", "妈妈")
        
        # 根据角色生成不同的默认计划
        if "奶奶" in role:
            default_actions = [
                {"action": "关心孙辈情况", "priority": 8, "description": "询问孩子们的近况", "planned_time": "上午"},
                {"action": "看抖音养生视频", "priority": 4, "description": "学习健康知识", "planned_time": "下午"},
                {"action": "在群里分享经验", "priority": 6, "description": "帮助其他妈妈", "planned_time": "有时间时"}
            ]
        else:
            default_actions = [
                {"action": "照顾孩子日常", "priority": 9, "description": "喂奶、换尿布、陪玩", "planned_time": "全天"},
                {"action": "刷抖音学育儿", "priority": 5, "description": "看育儿知识视频", "planned_time": "孩子睡觉时"},
                {"action": "在群里聊天", "priority": 3, "description": "和其他妈妈交流", "planned_time": "晚上"}
            ]
        
        return {
            "agent_id": agent_id,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "timestamp": datetime.now().isoformat(),
            "actions": default_actions,
            "total_actions": len(default_actions),
            "fallback": True
        }
    
    def _save_plan_to_database(self, agent_id: str, plan: Dict[str, Any]):
        """保存计划到数据库"""
        for action in plan.get("actions", []):
            # 保存到daily_plans表
            success = self.db.add_daily_plan(
                agent_id=agent_id,
                planned_action=action.get('action', ''),
                priority=action.get('priority', 5),
                planned_time=action.get('planned_time', ''),
                status='pending'
            )
            
            if success:
                print(f"  📋 已保存计划: {action.get('action', '')[:30]}...")
            
            # 同时也保存到memories作为备份
            self.db.add_memory(
                agent_id=agent_id,
                memory_type="plan",
                content=f"计划行动：{action['action']}",
                importance=action.get("priority", 5),
                metadata=action
            )
    
    def _save_plan_updates(self, agent_id: str, updated_plan: Dict[str, Any]):
        """保存计划更新"""
        for action in updated_plan.get("updated_actions", []):
            # 保存到daily_plans表
            success = self.db.add_daily_plan(
                agent_id=agent_id,
                planned_action=action.get('action', ''),
                priority=action.get('priority', 5),
                planned_time=action.get('planned_time', ''),
                status='pending'
            )
            
            if success:
                print(f"  📋 已保存更新计划: {action.get('action', '')[:30]}...")
            
            # 同时保存到memories
            self.db.add_memory(
                agent_id=agent_id,
                memory_type="plan_update",
                content=f"更新计划：{action['action']}",
                importance=action.get("priority", 5),
                metadata=action
            )
    
    def _get_current_plans(self, agent_id: str) -> List[Dict]:
        """获取当前计划"""
        return self.db.get_recent_memories(agent_id, limit=10, memory_type="plan")
    
    def _get_time_period(self, hour: int) -> str:
        """获取时间段描述"""
        if 6 <= hour < 12:
            return "上午"
        elif 12 <= hour < 18:
            return "下午"
        elif 18 <= hour < 22:
            return "晚上"
        else:
            return "夜晚"