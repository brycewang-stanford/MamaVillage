from typing import Dict, List, Any, Optional
from datetime import datetime
import json
import random
from memory.database import MemoryDatabase
from openai import OpenAI
from config import Config

class ExecutorNode:
    """执行者节点 - 负责执行agent的具体行动和社交互动"""
    
    def __init__(self, db: MemoryDatabase):
        self.db = db
        self.client = OpenAI(api_key=Config.OPENAI_API_KEY)
    
    def execute_action(self, agent_id: str, action: Dict[str, Any], 
                      agent_profile: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """执行具体行动"""
        
        action_type = self._classify_action(action)
        
        if action_type == "social_interaction":
            return self._execute_social_interaction(agent_id, action, agent_profile, context)
        elif action_type == "digital_activity":
            return self._execute_digital_activity(agent_id, action, agent_profile, context)
        elif action_type == "childcare":
            return self._execute_childcare(agent_id, action, agent_profile, context)
        elif action_type == "learning":
            return self._execute_learning(agent_id, action, agent_profile, context)
        else:
            return self._execute_general_action(agent_id, action, agent_profile, context)
    
    def generate_conversation(self, agent_id: str, agent_profile: Dict[str, Any],
                            conversation_context: Dict[str, Any]) -> Dict[str, Any]:
        """生成对话内容"""
        
        # 获取agent的语言风格和最近记忆
        language_style = agent_profile.get("language_style", {})
        recent_memories = self.db.get_recent_memories(agent_id, limit=5)
        recent_conversations = self.db.get_conversation_history(agent_id, limit=3)
        
        # 构建对话生成提示词
        conversation_prompt = self._create_conversation_prompt(
            agent_profile, conversation_context, recent_memories, recent_conversations
        )
        
        try:
            response = self.client.chat.completions.create(
                model=Config.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": self._get_conversation_system_prompt(language_style)},
                    {"role": "user", "content": conversation_prompt}
                ],
                temperature=0.8,
                max_tokens=200
            )
            
            message_content = response.choices[0].message.content.strip()
            
            # 记录对话到数据库
            conversation_result = {
                "from_agent": agent_id,
                "to_agent": conversation_context.get("to_agent"),
                "message": message_content,
                "conversation_type": conversation_context.get("type", "chat"),
                "timestamp": datetime.now().isoformat(),
                "context": conversation_context
            }
            
            # 保存到数据库
            self.db.add_conversation(
                from_agent=agent_id,
                to_agent=conversation_context.get("to_agent"),
                message=message_content,
                conversation_type=conversation_context.get("type", "chat"),
                metadata=conversation_context
            )
            
            return conversation_result
            
        except Exception as e:
            print(f"❌ 生成对话失败: {e}")
            return self._generate_fallback_conversation(agent_id, conversation_context)
    
    def respond_to_message(self, agent_id: str, agent_profile: Dict[str, Any],
                          incoming_message: Dict[str, Any]) -> Dict[str, Any]:
        """回应收到的消息"""
        
        # 分析收到的消息
        message_analysis = self._analyze_incoming_message(incoming_message)
        
        # 生成回应
        response_context = {
            "type": "response",
            "trigger_message": incoming_message,
            "analysis": message_analysis,
            "to_agent": incoming_message.get("from_agent")
        }
        
        return self.generate_conversation(agent_id, agent_profile, response_context)
    
    def share_content(self, agent_id: str, agent_profile: Dict[str, Any],
                     content_to_share: Dict[str, Any]) -> Dict[str, Any]:
        """分享内容（视频、文章、经验等）"""
        
        sharing_context = {
            "type": "content_sharing",
            "content": content_to_share,
            "motivation": self._determine_sharing_motivation(agent_profile, content_to_share)
        }
        
        # 生成分享消息
        sharing_message = self.generate_conversation(agent_id, agent_profile, sharing_context)
        
        # 记录分享行为
        self.db.add_memory(
            agent_id=agent_id,
            memory_type="action",
            content=f"分享了内容：{content_to_share.get('title', '')}",
            importance=6,
            metadata=sharing_context
        )
        
        return sharing_message
    
    def _execute_social_interaction(self, agent_id: str, action: Dict[str, Any],
                                   agent_profile: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """执行社交互动"""
        
        # 确定互动对象和类型
        interaction_type = random.choice(["group_chat", "private_message", "content_sharing"])
        
        if interaction_type == "group_chat":
            # 群聊互动
            topic = self._generate_chat_topic(agent_profile, context)
            conversation_context = {
                "type": "group_chat",
                "topic": topic,
                "motivation": "日常交流"
            }
            result = self.generate_conversation(agent_id, agent_profile, conversation_context)
            
        elif interaction_type == "private_message":
            # 私信互动
            target_agent = self._select_interaction_target(agent_id)
            if target_agent:
                conversation_context = {
                    "type": "private_chat",
                    "to_agent": target_agent,
                    "motivation": "关心朋友"
                }
                result = self.generate_conversation(agent_id, agent_profile, conversation_context)
            else:
                result = {"status": "no_target_found"}
                
        else:
            # 内容分享
            content = self._select_content_to_share(agent_profile)
            result = self.share_content(agent_id, agent_profile, content)
        
        # 记录行为
        self.db.add_memory(
            agent_id=agent_id,
            memory_type="action",
            content=f"进行了社交互动：{interaction_type}",
            importance=4,
            metadata={"action": action, "result": result}
        )
        
        return result
    
    def _execute_digital_activity(self, agent_id: str, action: Dict[str, Any],
                                 agent_profile: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """执行数字活动（看视频、刷抖音等）"""
        
        digital_habits = agent_profile.get("personality", {}).get("digital_habits", {})
        video_preferences = digital_habits.get("video_preferences", ["育儿知识"])
        
        # 随机选择一个视频主题
        video_topic = random.choice(video_preferences)
        
        # 模拟观看视频
        video_content = {
            "type": "video_watching",
            "topic": video_topic,
            "platform": random.choice(["抖音", "快手", "微信视频号"]),
            "duration": f"{random.randint(5, 30)}分钟",
            "learned_something": random.choice([True, False])
        }
        
        # 判断是否学到有用信息
        if video_content["learned_something"]:
            learning_content = self._generate_learning_content(video_topic, agent_profile)
            
            # 记录学习收获
            self.db.add_memory(
                agent_id=agent_id,
                memory_type="learning",
                content=f"从{video_topic}视频中学到：{learning_content}",
                importance=5,
                metadata=video_content
            )
            
            # 可能会分享学到的内容
            if random.random() < 0.3:  # 30%概率分享
                sharing_result = self.share_content(agent_id, agent_profile, {
                    "title": f"{video_topic}小技巧",
                    "content": learning_content,
                    "source": "视频学习"
                })
                video_content["shared"] = sharing_result
        
        return video_content
    
    def _execute_childcare(self, agent_id: str, action: Dict[str, Any],
                          agent_profile: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """执行育儿相关行动"""
        
        children = agent_profile.get("children", [])
        if not children:
            return {"status": "no_children"}
        
        # 随机生成育儿场景
        childcare_scenarios = [
            "喂奶时间到了",
            "孩子要换尿布",
            "陪孩子玩游戏",
            "给孩子准备辅食",
            "孩子有点不舒服",
            "教孩子新技能",
            "孩子睡觉时间"
        ]
        
        scenario = random.choice(childcare_scenarios)
        
        # 可能遇到问题需要求助
        if "不舒服" in scenario and random.random() < 0.7:
            # 健康问题，需要寻求帮助
            help_request = self._generate_help_request(agent_id, agent_profile, scenario)
            
            # 记录担忧
            self.db.add_memory(
                agent_id=agent_id,
                memory_type="concern",
                content=f"担心孩子：{scenario}",
                importance=8,
                metadata={"scenario": scenario, "help_request": help_request}
            )
            
            return {
                "type": "childcare_with_concern",
                "scenario": scenario,
                "help_request": help_request
            }
        
        else:
            # 正常育儿活动
            self.db.add_memory(
                agent_id=agent_id,
                memory_type="daily_activity",
                content=f"育儿活动：{scenario}",
                importance=3,
                metadata={"scenario": scenario}
            )
            
            return {
                "type": "normal_childcare",
                "scenario": scenario
            }
    
    def _execute_learning(self, agent_id: str, action: Dict[str, Any],
                         agent_profile: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """执行学习行动"""
        
        interests = agent_profile.get("personality", {}).get("interests", ["育儿知识"])
        learning_topic = random.choice(interests)
        
        # 生成学习内容
        learning_content = self._generate_learning_content(learning_topic, agent_profile)
        
        # 记录学习
        self.db.add_memory(
            agent_id=agent_id,
            memory_type="learning",
            content=f"学习了{learning_topic}：{learning_content}",
            importance=5,
            metadata={"topic": learning_topic, "content": learning_content}
        )
        
        return {
            "type": "learning",
            "topic": learning_topic,
            "content": learning_content
        }
    
    def _execute_general_action(self, agent_id: str, action: Dict[str, Any],
                               agent_profile: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """执行一般行动"""
        
        action_description = action.get("action", "未知行动")
        
        # 记录行动
        self.db.add_memory(
            agent_id=agent_id,
            memory_type="action",
            content=f"执行了行动：{action_description}",
            importance=action.get("priority", 3),
            metadata=action
        )
        
        return {
            "type": "general_action",
            "action": action_description,
            "status": "completed"
        }
    
    def _classify_action(self, action: Dict[str, Any]) -> str:
        """分类行动类型"""
        action_text = action.get("action", "").lower()
        
        if any(keyword in action_text for keyword in ["聊天", "群里", "分享", "交流"]):
            return "social_interaction"
        elif any(keyword in action_text for keyword in ["看视频", "抖音", "刷手机", "app"]):
            return "digital_activity"
        elif any(keyword in action_text for keyword in ["孩子", "育儿", "喂奶", "换尿布"]):
            return "childcare"
        elif any(keyword in action_text for keyword in ["学习", "知识", "了解"]):
            return "learning"
        else:
            return "general"
    
    def _create_conversation_prompt(self, agent_profile: Dict[str, Any],
                                   context: Dict[str, Any], memories: List[Dict],
                                   conversations: List[Dict]) -> str:
        """创建对话生成提示词"""
        
        name = agent_profile.get("name", "")
        role = agent_profile.get("role", "")
        personality_traits = agent_profile.get("personality", {}).get("traits", [])
        language_style = agent_profile.get("language_style", {})
        common_phrases = language_style.get("common_phrases", [])
        
        conversation_type = context.get("type", "chat")
        
        # 构建上下文
        memory_context = ""
        if memories:
            recent_concerns = [mem.get("content", "") for mem in memories[:3]]
            memory_context = f"最近关心的事：{', '.join(recent_concerns)}"
        
        prompt = f"""
你是{name}，一个{role}。
性格特点：{', '.join(personality_traits)}
常用语：{', '.join(common_phrases)}

{memory_context}

现在要进行{conversation_type}：
"""
        
        if conversation_type == "group_chat":
            topic = context.get("topic", "")
            prompt += f"""
在妈妈群里聊天，话题是：{topic}
请发一条自然的消息，体现你的性格和语言风格。
"""
        
        elif conversation_type == "response":
            trigger_msg = context.get("trigger_message", {})
            prompt += f"""
收到了消息："{trigger_msg.get('message', '')}"
请回复这条消息，要体现关心和互助的精神。
"""
        
        elif conversation_type == "content_sharing":
            content = context.get("content", {})
            prompt += f"""
想要分享内容：{content.get('title', '')}
请写一条分享消息，说明为什么推荐这个内容。
"""
        
        prompt += """
要求：
- 使用中文对话
- 语言要口语化、生活化
- 体现农村妈妈的说话特点
- 适当使用表情符号
- 长度控制在50字以内
"""
        
        return prompt
    
    def _get_conversation_system_prompt(self, language_style: Dict[str, Any]) -> str:
        """获取对话系统提示词"""
        
        dialect = language_style.get("dialect", "普通话")
        emoji_usage = language_style.get("emoji_usage", "适度使用表情")
        
        return f"""
你是一个中国农村的妈妈或奶奶，在手机上与其他妈妈交流。

语言特点：
- {dialect}
- {emoji_usage}
- 语言亲切、自然、口语化
- 关心孩子和家庭
- 乐于分享经验和互相帮助

请用这种风格回复，展现真实的农村妈妈形象。
"""
    
    def _generate_fallback_conversation(self, agent_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """生成降级对话"""
        
        fallback_messages = [
            "大家好呀😊",
            "今天怎么样？",
            "孩子们都还好吧",
            "有什么新鲜事吗",
            "互相帮助💪"
        ]
        
        message = random.choice(fallback_messages)
        
        return {
            "from_agent": agent_id,
            "to_agent": context.get("to_agent"),
            "message": message,
            "conversation_type": context.get("type", "chat"),
            "timestamp": datetime.now().isoformat(),
            "fallback": True
        }
    
    def _analyze_incoming_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """分析收到的消息"""
        
        content = message.get("message", "").lower()
        
        analysis = {
            "sentiment": "neutral",
            "urgency": "low",
            "topics": [],
            "needs_response": True
        }
        
        # 情感分析
        if any(word in content for word in ["谢谢", "感谢", "好的", "不错"]):
            analysis["sentiment"] = "positive"
        elif any(word in content for word in ["担心", "不好", "生病", "问题"]):
            analysis["sentiment"] = "concerned"
        
        # 紧急程度
        if any(word in content for word in ["急", "紧急", "发烧", "不舒服"]):
            analysis["urgency"] = "high"
        
        # 主题识别
        if any(word in content for word in ["孩子", "宝宝", "育儿"]):
            analysis["topics"].append("育儿")
        if any(word in content for word in ["健康", "生病", "医院"]):
            analysis["topics"].append("健康")
        
        return analysis
    
    def _generate_chat_topic(self, agent_profile: Dict[str, Any], context: Dict[str, Any]) -> str:
        """生成聊天话题"""
        
        concerns = agent_profile.get("concerns", ["孩子健康"])
        interests = agent_profile.get("personality", {}).get("interests", ["育儿"])
        
        all_topics = concerns + interests
        return random.choice(all_topics)
    
    def _select_interaction_target(self, agent_id: str) -> Optional[str]:
        """选择互动对象"""
        
        all_agents = self.db.get_all_agents()
        other_agents = [agent for agent in all_agents if agent["id"] != agent_id]
        
        if other_agents:
            return random.choice(other_agents)["id"]
        return None
    
    def _select_content_to_share(self, agent_profile: Dict[str, Any]) -> Dict[str, Any]:
        """选择要分享的内容"""
        
        interests = agent_profile.get("personality", {}).get("interests", ["育儿知识"])
        topic = random.choice(interests)
        
        return {
            "title": f"{topic}分享",
            "content": f"关于{topic}的有用信息",
            "source": "个人经验"
        }
    
    def _determine_sharing_motivation(self, agent_profile: Dict[str, Any], content: Dict[str, Any]) -> str:
        """确定分享动机"""
        
        traits = agent_profile.get("personality", {}).get("traits", [])
        
        if "热心肠" in traits:
            return "帮助其他妈妈"
        elif "好学" in traits:
            return "分享学习收获"
        else:
            return "日常分享"
    
    def _generate_learning_content(self, topic: str, agent_profile: Dict[str, Any]) -> str:
        """生成学习内容"""
        
        learning_contents = {
            "育儿知识": ["宝宝sleep训练方法", "辅食添加顺序", "宝宝发育里程碑"],
            "健康知识": ["小儿推拿技巧", "预防感冒方法", "营养搭配建议"],
            "传统偏方": ["生姜泡脚的好处", "金银花茶降火", "艾叶洗澡防湿疹"]
        }
        
        content_list = learning_contents.get(topic, ["一些有用的生活小贴士"])
        return random.choice(content_list)
    
    def _generate_help_request(self, agent_id: str, agent_profile: Dict[str, Any], scenario: str) -> Dict[str, Any]:
        """生成求助请求"""
        
        help_context = {
            "type": "help_request",
            "scenario": scenario,
            "urgency": "high" if "不舒服" in scenario else "medium"
        }
        
        return self.generate_conversation(agent_id, agent_profile, help_context)