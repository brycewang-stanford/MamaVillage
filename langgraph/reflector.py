from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import json
from memory.database import MemoryDatabase
from openai import OpenAI
from config import Config

class ReflectorNode:
    """反思者节点 - 负责生成抽象反思记忆和经验总结"""
    
    def __init__(self, db: MemoryDatabase):
        self.db = db
        self.client = OpenAI(api_key=Config.OPENAI_API_KEY)
    
    def generate_daily_reflection(self, agent_id: str, agent_profile: Dict[str, Any]) -> Dict[str, Any]:
        """生成每日反思"""
        
        # 获取今天的所有记忆
        today_memories = self._get_today_memories(agent_id)
        
        if not today_memories:
            return {"status": "no_memories_to_reflect"}
        
        # 构建反思提示词
        reflection_prompt = self._create_reflection_prompt(agent_profile, today_memories)
        
        try:
            response = self.client.chat.completions.create(
                model=Config.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "你是一个中国农村妈妈的内心声音，帮助她反思今天的经历和感受。"},
                    {"role": "user", "content": reflection_prompt}
                ],
                temperature=0.6,
                max_tokens=500
            )
            
            reflection_content = response.choices[0].message.content.strip()
            
            # 解析反思内容
            reflection_data = self._parse_reflection_content(reflection_content)
            
            # 保存反思到数据库
            self.db.add_memory(
                agent_id=agent_id,
                memory_type="reflection",
                content=reflection_content,
                importance=7,  # 反思通常比较重要
                metadata={
                    "reflection_date": datetime.now().strftime("%Y-%m-%d"),
                    "memories_count": len(today_memories),
                    "themes": reflection_data.get("themes", []),
                    "emotions": reflection_data.get("emotions", []),
                    "lessons": reflection_data.get("lessons", [])
                }
            )
            
            return {
                "agent_id": agent_id,
                "reflection_content": reflection_content,
                "reflection_data": reflection_data,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"❌ 生成反思失败: {e}")
            return self._generate_simple_reflection(agent_id, today_memories)
    
    def generate_experience_summary(self, agent_id: str, agent_profile: Dict[str, Any],
                                   experience_type: str = "parenting") -> Dict[str, Any]:
        """生成经验总结"""
        
        # 获取相关的学习和经验记忆
        relevant_memories = self._get_experience_memories(agent_id, experience_type)
        
        if len(relevant_memories) < 3:
            return {"status": "insufficient_experience"}
        
        # 构建经验总结提示词
        summary_prompt = self._create_experience_summary_prompt(
            agent_profile, relevant_memories, experience_type
        )
        
        try:
            response = self.client.chat.completions.create(
                model=Config.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": f"你是一个有经验的农村妈妈，要总结自己在{experience_type}方面的心得体会。"},
                    {"role": "user", "content": summary_prompt}
                ],
                temperature=0.5,
                max_tokens=400
            )
            
            summary_content = response.choices[0].message.content.strip()
            
            # 保存经验总结
            self.db.add_memory(
                agent_id=agent_id,
                memory_type="experience_summary",
                content=summary_content,
                importance=8,  # 经验总结很重要
                metadata={
                    "experience_type": experience_type,
                    "based_on_memories": len(relevant_memories),
                    "summary_date": datetime.now().strftime("%Y-%m-%d")
                }
            )
            
            return {
                "agent_id": agent_id,
                "experience_type": experience_type,
                "summary_content": summary_content,
                "based_on_memories": len(relevant_memories)
            }
            
        except Exception as e:
            print(f"❌ 生成经验总结失败: {e}")
            return {"status": "generation_failed", "error": str(e)}
    
    def reflect_on_conversation(self, agent_id: str, agent_profile: Dict[str, Any],
                               conversation_data: Dict[str, Any]) -> Dict[str, Any]:
        """对特定对话进行反思"""
        
        conversation_content = conversation_data.get("message", "")
        conversation_type = conversation_data.get("conversation_type", "chat")
        
        # 如果是重要对话才进行反思
        if not self._is_conversation_worth_reflecting(conversation_data):
            return {"status": "not_worth_reflecting"}
        
        reflection_prompt = f"""
作为{agent_profile.get('name', '')}，请反思刚才的对话：

对话内容："{conversation_content}"
对话类型：{conversation_type}

请思考：
1. 这次对话给你带来了什么感受？
2. 学到了什么新知识或经验？
3. 对以后的育儿有什么启发？
4. 是否要分享给其他妈妈？

请用简单朴实的语言回答，50字以内。
"""
        
        try:
            response = self.client.chat.completions.create(
                model=Config.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "你是一个农村妈妈，刚和其他妈妈聊过天，现在在心里想想这次聊天的收获。"},
                    {"role": "user", "content": reflection_prompt}
                ],
                temperature=0.7,
                max_tokens=150
            )
            
            reflection_content = response.choices[0].message.content.strip()
            
            # 保存对话反思
            self.db.add_memory(
                agent_id=agent_id,
                memory_type="conversation_reflection",
                content=reflection_content,
                importance=5,
                metadata={
                    "original_conversation": conversation_data,
                    "reflection_date": datetime.now().isoformat()
                }
            )
            
            return {
                "agent_id": agent_id,
                "reflection_content": reflection_content,
                "conversation_id": conversation_data.get("id")
            }
            
        except Exception as e:
            print(f"❌ 对话反思失败: {e}")
            return {"status": "reflection_failed"}
    
    def generate_wisdom_sharing(self, agent_id: str, agent_profile: Dict[str, Any]) -> Dict[str, Any]:
        """生成智慧分享（适合资深妈妈/奶奶）"""
        
        role = agent_profile.get("role", "")
        if "奶奶" not in role and agent_profile.get("age", 0) < 35:
            return {"status": "not_experienced_enough"}
        
        # 获取所有经验总结和重要记忆
        wisdom_memories = self._get_wisdom_memories(agent_id)
        
        if len(wisdom_memories) < 5:
            return {"status": "insufficient_wisdom"}
        
        wisdom_prompt = f"""
作为{agent_profile.get('name', '')}，一个有经验的{role}，请分享一个育儿智慧。

基于你的经验：
{chr(10).join([mem.get('content', '')[:50] + '...' for mem in wisdom_memories[:5]])}

请分享一条实用的育儿建议，要求：
- 语言朴实易懂
- 基于实际经验
- 对年轻妈妈有帮助
- 体现传统智慧
- 30-50字

开头可以用"我跟你们说啊"或"奶奶的经验是"这样的话。
"""
        
        try:
            response = self.client.chat.completions.create(
                model=Config.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "你是一个有丰富育儿经验的农村奶奶，要给年轻妈妈们分享实用的育儿智慧。"},
                    {"role": "user", "content": wisdom_prompt}
                ],
                temperature=0.6,
                max_tokens=200
            )
            
            wisdom_content = response.choices[0].message.content.strip()
            
            # 保存智慧分享
            self.db.add_memory(
                agent_id=agent_id,
                memory_type="wisdom_sharing",
                content=wisdom_content,
                importance=9,  # 智慧分享很有价值
                metadata={
                    "sharing_date": datetime.now().strftime("%Y-%m-%d"),
                    "based_on_experiences": len(wisdom_memories)
                }
            )
            
            return {
                "agent_id": agent_id,
                "wisdom_content": wisdom_content,
                "sharing_value": "high"
            }
            
        except Exception as e:
            print(f"❌ 生成智慧分享失败: {e}")
            return {"status": "generation_failed"}
    
    def _get_today_memories(self, agent_id: str) -> List[Dict]:
        """获取今天的记忆"""
        today = datetime.now().strftime("%Y-%m-%d")
        all_memories = self.db.get_recent_memories(agent_id, limit=50)
        
        today_memories = []
        for memory in all_memories:
            memory_date = memory.get("timestamp", "")[:10]  # 取日期部分
            if memory_date == today:
                today_memories.append(memory)
        
        return today_memories
    
    def _get_experience_memories(self, agent_id: str, experience_type: str) -> List[Dict]:
        """获取特定类型的经验记忆"""
        all_memories = self.db.get_recent_memories(agent_id, limit=100)
        
        relevant_memories = []
        keywords = {
            "parenting": ["育儿", "孩子", "宝宝", "喂奶", "教育"],
            "health": ["健康", "生病", "医院", "推拿", "偏方"],
            "cooking": ["做饭", "辅食", "营养", "食谱"],
            "social": ["聊天", "分享", "群里", "邻居"]
        }
        
        search_keywords = keywords.get(experience_type, ["育儿"])
        
        for memory in all_memories:
            content = memory.get("content", "").lower()
            if any(keyword in content for keyword in search_keywords):
                relevant_memories.append(memory)
        
        return relevant_memories
    
    def _get_wisdom_memories(self, agent_id: str) -> List[Dict]:
        """获取智慧相关的记忆"""
        all_memories = self.db.get_recent_memories(agent_id, limit=200)
        
        # 筛选高重要性和经验类记忆
        wisdom_memories = []
        for memory in all_memories:
            importance = memory.get("importance", 1)
            memory_type = memory.get("memory_type", "")
            
            if importance >= 6 or memory_type in ["learning", "experience_summary", "reflection"]:
                wisdom_memories.append(memory)
        
        return wisdom_memories
    
    def _create_reflection_prompt(self, agent_profile: Dict[str, Any], memories: List[Dict]) -> str:
        """创建反思提示词"""
        
        name = agent_profile.get("name", "")
        role = agent_profile.get("role", "")
        personality_traits = agent_profile.get("personality", {}).get("traits", [])
        
        memory_summary = ""
        for i, memory in enumerate(memories[:10], 1):
            memory_summary += f"{i}. {memory.get('content', '')}\n"
        
        prompt = f"""
你是{name}，一个{role}。
性格：{', '.join(personality_traits)}

今天发生的事情：
{memory_summary}

请作为{name}，用第一人称反思今天的经历。思考：
1. 今天最重要的事情是什么？
2. 有什么收获或学到的东西？
3. 有什么担心或需要注意的？
4. 明天想要做什么？

要求：
- 用自然的中文表达
- 体现农村妈妈的语言特点
- 100字以内
- 真实朴素的情感
"""
        
        return prompt
    
    def _create_experience_summary_prompt(self, agent_profile: Dict[str, Any],
                                        memories: List[Dict], experience_type: str) -> str:
        """创建经验总结提示词"""
        
        name = agent_profile.get("name", "")
        
        experience_details = ""
        for i, memory in enumerate(memories[:8], 1):
            experience_details += f"{i}. {memory.get('content', '')}\n"
        
        prompt = f"""
你是{name}，基于这些经历：

{experience_details}

请总结你在{experience_type}方面的经验心得：
1. 最重要的几点经验
2. 什么方法最有效
3. 新手容易犯什么错误
4. 给其他妈妈的建议

用朴实的语言，80字以内，体现实用性。
"""
        
        return prompt
    
    def _parse_reflection_content(self, content: str) -> Dict[str, Any]:
        """解析反思内容，提取主题和情感"""
        
        # 简单的关键词分析
        themes = []
        emotions = []
        lessons = []
        
        content_lower = content.lower()
        
        # 主题识别
        if any(word in content_lower for word in ["孩子", "宝宝", "育儿"]):
            themes.append("育儿")
        if any(word in content_lower for word in ["健康", "生病", "医院"]):
            themes.append("健康")
        if any(word in content_lower for word in ["学习", "知识", "经验"]):
            themes.append("学习")
        
        # 情感识别
        if any(word in content_lower for word in ["开心", "高兴", "满意"]):
            emotions.append("开心")
        if any(word in content_lower for word in ["担心", "焦虑", "紧张"]):
            emotions.append("担心")
        if any(word in content_lower for word in ["感谢", "感激", "帮助"]):
            emotions.append("感激")
        
        # 教训识别
        if any(word in content_lower for word in ["学到", "明白", "懂得"]):
            lessons.append("获得新知识")
        if any(word in content_lower for word in ["注意", "小心", "预防"]):
            lessons.append("注意事项")
        
        return {
            "themes": themes,
            "emotions": emotions,
            "lessons": lessons
        }
    
    def _generate_simple_reflection(self, agent_id: str, memories: List[Dict]) -> Dict[str, Any]:
        """生成简单的降级反思"""
        
        if not memories:
            reflection_content = "今天又是平凡的一天，好好照顾孩子就是最重要的事。"
        else:
            activity_count = len(memories)
            reflection_content = f"今天做了{activity_count}件事，每一件都是为了家庭和孩子。继续努力💪"
        
        # 保存简单反思
        self.db.add_memory(
            agent_id=agent_id,
            memory_type="reflection",
            content=reflection_content,
            importance=5,
            metadata={
                "reflection_date": datetime.now().strftime("%Y-%m-%d"),
                "memories_count": len(memories),
                "type": "simple_reflection"
            }
        )
        
        return {
            "agent_id": agent_id,
            "reflection_content": reflection_content,
            "type": "simple",
            "timestamp": datetime.now().isoformat()
        }
    
    def _is_conversation_worth_reflecting(self, conversation_data: Dict[str, Any]) -> bool:
        """判断对话是否值得反思"""
        
        message = conversation_data.get("message", "").lower()
        conversation_type = conversation_data.get("conversation_type", "")
        
        # 健康相关对话值得反思
        if any(keyword in message for keyword in ["生病", "发烧", "医院", "健康"]):
            return True
        
        # 经验分享对话值得反思
        if any(keyword in message for keyword in ["经验", "方法", "建议", "推荐"]):
            return True
        
        # 重要的对话类型
        if conversation_type in ["advice", "help_request", "knowledge_sharing"]:
            return True
        
        # 长对话可能值得反思
        if len(message) > 30:
            return True
        
        return False