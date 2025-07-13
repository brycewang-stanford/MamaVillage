#!/usr/bin/env python3
"""
妈妈互助小区（MamaVillage）主运行文件
基于LangGraph + GPT-4o-mini构建的农村育儿社群模拟系统
"""

import json
import os
import time
import random
from datetime import datetime
from typing import Dict, List, Any
from pathlib import Path

# 导入自定义模块
from config import Config
from memory.database import MemoryDatabase
from langgraph.observer import ObserverNode
from langgraph.planner import PlannerNode
from langgraph.executor import ExecutorNode
from langgraph.reflector import ReflectorNode
from prompts.conversation_templates import ConversationTemplates

class MamaVillageSimulation:
    """妈妈村模拟主类"""
    
    def __init__(self):
        print("🏡 初始化妈妈互助小区...")
        
        # 验证配置
        Config.validate()
        
        # 初始化数据库
        self.db = MemoryDatabase()
        
        # 初始化LangGraph节点
        self.observer = ObserverNode(self.db)
        self.planner = PlannerNode(self.db)
        self.executor = ExecutorNode(self.db)
        self.reflector = ReflectorNode(self.db)
        
        # 加载agent配置
        self.agents = self._load_agents()
        self._register_agents()
        
        # 模拟状态
        self.simulation_day = 1
        self.tick_count = 0
        self.conversation_count = 0  # 对话计数器
        self.max_conversations = None  # 最大对话轮数限制
        
        print(f"✅ 初始化完成，共加载{len(self.agents)}个agent")
    
    def _load_agents(self) -> Dict[str, Any]:
        """加载所有agent配置"""
        agents = {}
        agents_dir = Path("agents")
        
        if not agents_dir.exists():
            print("❌ agents目录不存在")
            return {}
        
        for agent_file in agents_dir.glob("*.json"):
            try:
                with open(agent_file, 'r', encoding='utf-8') as f:
                    agent_data = json.load(f)
                    agent_id = agent_data.get("id")
                    if agent_id:
                        agents[agent_id] = agent_data
                        print(f"  📝 加载agent: {agent_data.get('name', agent_id)}")
                    else:
                        print(f"  ⚠️ {agent_file}缺少id字段")
            except Exception as e:
                print(f"  ❌ 加载{agent_file}失败: {e}")
        
        return agents
    
    def _register_agents(self):
        """将agents注册到数据库"""
        for agent_id, agent_data in self.agents.items():
            success = self.db.add_agent(agent_data)
            if success:
                print(f"  ✅ 注册agent: {agent_data.get('name', agent_id)}")
            else:
                print(f"  ❌ 注册agent失败: {agent_id}")
    
    def run_simulation(self, max_ticks: int = 20, tick_interval: float = 3.0, max_conversations: int = None):
        """运行模拟"""
        self.max_conversations = max_conversations
        self.conversation_count = 0
        
        conversation_info = f", 最大对话轮数: {max_conversations}" if max_conversations else ""
        print(f"\n🚀 开始模拟，最大tick数: {max_ticks}, 间隔: {tick_interval}秒{conversation_info}")
        print("=" * 60)
        
        try:
            for tick in range(max_ticks):
                self.tick_count = tick + 1
                print(f"\n⏰ Tick {self.tick_count} - {datetime.now().strftime('%H:%M:%S')}")
                
                # 检查对话轮数限制
                if self.max_conversations and self.conversation_count >= self.max_conversations:
                    print(f"\n🎯 已达到对话轮数限制 ({self.conversation_count}/{self.max_conversations})，停止模拟")
                    break
                
                # 执行一个模拟周期
                self._run_tick()
                
                # 显示当前对话轮数
                if self.max_conversations:
                    print(f"   📊 当前对话轮数: {self.conversation_count}/{self.max_conversations}")
                
                # 等待下一个tick
                if tick < max_ticks - 1:  # 最后一次不等待
                    print(f"   ⏳ 等待{tick_interval}秒...")
                    time.sleep(tick_interval)
        
        except KeyboardInterrupt:
            print(f"\n⚠️ 用户中断模拟 (Tick {self.tick_count})")
        
        except Exception as e:
            print(f"\n❌ 模拟出错: {e}")
        
        finally:
            self._show_simulation_summary()
    
    def _run_tick(self):
        """执行一个tick的模拟"""
        
        # 随机选择1-3个agent进行活动
        active_agents = random.sample(list(self.agents.keys()), 
                                    min(random.randint(1, 3), len(self.agents)))
        
        print(f"   🎯 活跃agent: {[self.agents[aid]['name'] for aid in active_agents]}")
        
        for agent_id in active_agents:
            self._run_agent_cycle(agent_id)
    
    def _run_agent_cycle(self, agent_id: str):
        """运行单个agent的完整周期：观察 → 计划 → 执行 → 反思"""
        
        agent_profile = self.agents[agent_id]
        agent_name = agent_profile.get("name", agent_id)
        
        try:
            # 1. 观察环境
            observation = self.observer.observe_environment(agent_id, {
                "tick": self.tick_count,
                "simulation_day": self.simulation_day
            })
            
            # 2. 制定计划（不是每次都重新制定）
            if random.random() < 0.3:  # 30%概率重新制定计划
                plan = self.planner.generate_daily_plan(agent_id, agent_profile)
                if plan.get("actions"):
                    print(f"      📋 {agent_name} 制定了新计划")
            
            # 3. 执行行动
            action_result = self._execute_agent_action(agent_id, agent_profile)
            
            # 4. 反思（偶尔进行）
            if random.random() < 0.2:  # 20%概率进行反思
                reflection = self.reflector.generate_daily_reflection(agent_id, agent_profile)
                if reflection.get("reflection_content"):
                    print(f"      🤔 {agent_name} 进行了反思")
        
        except Exception as e:
            print(f"      ❌ {agent_name} 执行周期失败: {e}")
    
    def _execute_agent_action(self, agent_id: str, agent_profile: Dict[str, Any]) -> Dict[str, Any]:
        """执行agent行动"""
        
        agent_name = agent_profile.get("name", agent_id)
        
        # 随机选择行动类型
        action_types = ["social_interaction", "digital_activity", "childcare", "learning"]
        action_type = random.choice(action_types)
        
        # 构造行动
        action = {
            "action": self._generate_action_description(action_type, agent_profile),
            "type": action_type,
            "priority": random.randint(3, 8)
        }
        
        # 执行行动
        result = self.executor.execute_action(agent_id, action, agent_profile, {
            "tick": self.tick_count,
            "time_period": self._get_current_time_period()
        })
        
        # 显示结果
        self._display_action_result(agent_name, action, result)
        
        return result
    
    def _generate_action_description(self, action_type: str, agent_profile: Dict[str, Any]) -> str:
        """生成行动描述"""
        
        role = agent_profile.get("role", "妈妈")
        
        action_templates = {
            "social_interaction": [
                "在群里聊天交流",
                "关心其他妈妈", 
                "分享育儿经验",
                "回复朋友消息"
            ],
            "digital_activity": [
                "刷抖音看育儿视频",
                "在微信看文章",
                "搜索育儿知识",
                "看健康养生内容" if "奶奶" in role else "看教育相关视频"
            ],
            "childcare": [
                "照顾孩子日常",
                "准备孩子的食物",
                "陪孩子玩游戏",
                "检查孩子身体状况"
            ],
            "learning": [
                "学习育儿知识",
                "了解健康信息", 
                "学习新的照顾方法",
                "观看教育内容"
            ]
        }
        
        templates = action_templates.get(action_type, ["进行日常活动"])
        return random.choice(templates)
    
    def _display_action_result(self, agent_name: str, action: Dict[str, Any], result: Dict[str, Any]):
        """显示行动结果"""
        
        action_desc = action.get("action", "未知行动")
        result_type = result.get("type", "unknown")
        
        print(f"      🎬 {agent_name}: {action_desc}")
        
        # 根据结果类型显示不同信息
        if result_type == "normal_childcare":
            scenario = result.get("scenario", "")
            print(f"         └─ 育儿: {scenario}")
        
        elif result_type == "childcare_with_concern":
            scenario = result.get("scenario", "")
            print(f"         └─ ⚠️ 育儿担忧: {scenario}")
            help_request = result.get("help_request", {})
            if help_request.get("message"):
                print(f"         └─ 💬 求助: \"{help_request['message']}\"")
                # 增加对话计数
                self.conversation_count += 1
        
        elif "conversation" in result.get("from_agent", ""):
            message = result.get("message", "")
            target = result.get("to_agent", "群聊")
            target_name = "群聊" if not target else self.agents.get(target, {}).get("name", target)
            print(f"         └─ 💬 对{target_name}说: \"{message}\"")
            # 增加对话计数
            self.conversation_count += 1
        
        elif result_type == "video_watching":
            topic = result.get("topic", "")
            platform = result.get("platform", "")
            learned = result.get("learned_something", False)
            print(f"         └─ 📱 在{platform}看{topic}视频" + (" ✨学到新知识" if learned else ""))
        
        elif result_type == "learning":
            topic = result.get("topic", "")
            print(f"         └─ 📚 学习: {topic}")
        
        else:
            # 简单显示结果状态
            status = result.get("status", "completed")
            print(f"         └─ 状态: {status}")
    
    def _get_current_time_period(self) -> str:
        """获取当前时间段"""
        hour = datetime.now().hour
        
        if 6 <= hour < 12:
            return "上午"
        elif 12 <= hour < 18:
            return "下午"
        elif 18 <= hour < 22:
            return "晚上"
        else:
            return "夜晚"
    
    def show_conversation_history(self, limit: int = 50, export_to_file: bool = False):
        """显示对话历史记录"""
        print(f"\n💬 对话历史记录 (最近{limit}条)")
        print("=" * 80)
        
        all_conversations = []
        
        # 收集所有agent的对话
        for agent_id in self.agents.keys():
            conversations = self.db.get_conversation_history(agent_id, limit=limit)
            all_conversations.extend(conversations)
        
        # 按时间排序（最新的在前）
        all_conversations.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        # 去重（避免重复显示同一条对话）
        seen_conversations = set()
        unique_conversations = []
        for conv in all_conversations:
            conv_id = f"{conv.get('from_agent')}_{conv.get('timestamp')}_{conv.get('message', '')[:20]}"
            if conv_id not in seen_conversations:
                seen_conversations.add(conv_id)
                unique_conversations.append(conv)
        
        # 限制显示数量
        display_conversations = unique_conversations[:limit]
        
        if not display_conversations:
            print("📭 暂无对话记录")
            return
        
        # 显示对话
        conversation_text = []
        for i, conv in enumerate(display_conversations, 1):
            from_name = conv.get('from_name', conv.get('from_agent', '未知'))
            to_name = conv.get('to_name', '群聊') if conv.get('to_agent') else '群聊'
            message = conv.get('message', '')
            timestamp = conv.get('timestamp', '')[:16]  # 只显示日期和时间
            conv_type = conv.get('conversation_type', 'chat')
            
            type_emoji = {
                'chat': '💬',
                'help_request': '🆘', 
                'advice': '💡',
                'content_sharing': '📤'
            }.get(conv_type, '💬')
            
            display_line = f"{i:2d}. [{timestamp}] {type_emoji} {from_name} → {to_name}: \"{message}\""
            print(display_line)
            conversation_text.append(display_line)
        
        print(f"\n📊 共显示 {len(display_conversations)} 条对话")
        
        # 导出到文件
        if export_to_file:
            filename = f"conversations_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write("妈妈互助小区 - 对话记录\n")
                    f.write("=" * 50 + "\n\n")
                    for line in conversation_text:
                        f.write(line + "\n")
                    f.write(f"\n导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"总对话数: {len(display_conversations)}\n")
                print(f"💾 对话记录已导出到: {filename}")
            except Exception as e:
                print(f"❌ 导出失败: {e}")
    
    def show_conversation_stats(self):
        """显示对话统计信息"""
        print(f"\n📊 对话统计信息")
        print("=" * 40)
        
        # 统计每个agent的对话数
        agent_stats = {}
        total_conversations = 0
        
        for agent_id, agent_data in self.agents.items():
            agent_name = agent_data.get('name', agent_id)
            conversations = self.db.get_conversation_history(agent_id, limit=1000)
            agent_stats[agent_name] = len(conversations)
            total_conversations += len(conversations)
        
        print(f"📈 总对话数: {total_conversations}")
        print(f"🎯 本次模拟对话数: {self.conversation_count}")
        print(f"⏱️ 模拟时长: {self.tick_count} ticks")
        print()
        
        print("👥 各Agent对话统计:")
        for agent_name, count in sorted(agent_stats.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / total_conversations * 100) if total_conversations > 0 else 0
            print(f"  {agent_name}: {count} 条 ({percentage:.1f}%)")
        
        # 对话类型统计
        conversation_types = {}
        for agent_id in self.agents.keys():
            conversations = self.db.get_conversation_history(agent_id, limit=1000)
            for conv in conversations:
                conv_type = conv.get('conversation_type', 'chat')
                conversation_types[conv_type] = conversation_types.get(conv_type, 0) + 1
        
        if conversation_types:
            print("\n📝 对话类型统计:")
            for conv_type, count in sorted(conversation_types.items(), key=lambda x: x[1], reverse=True):
                type_names = {
                    'chat': '日常聊天',
                    'help_request': '求助',
                    'advice': '建议',
                    'content_sharing': '内容分享'
                }
                type_name = type_names.get(conv_type, conv_type)
                print(f"  {type_name}: {count} 条")

    def _show_simulation_summary(self):
        """显示模拟总结"""
        print("\n" + "=" * 60)
        print("📊 模拟总结")
        print("=" * 60)
        
        for agent_id, agent_data in self.agents.items():
            agent_name = agent_data.get("name", agent_id)
            
            # 获取该agent的记忆统计
            recent_memories = self.db.get_recent_memories(agent_id, limit=50)
            conversations = self.db.get_conversation_history(agent_id, limit=20)
            
            print(f"\n👤 {agent_name} ({agent_data.get('role', '')}):")
            print(f"   记忆数量: {len(recent_memories)}")
            print(f"   对话数量: {len(conversations)}")
            
            # 显示最近的几条记忆
            if recent_memories:
                print("   最近活动:")
                for memory in recent_memories[:3]:
                    content = memory.get("content", "")[:40]
                    memory_type = memory.get("memory_type", "")
                    print(f"     • [{memory_type}] {content}...")
            
            # 显示最近的对话
            if conversations:
                print("   最近对话:")
                for conv in conversations[:2]:
                    message = conv.get("message", "")[:30]
                    from_name = conv.get("from_name", "")
                    print(f"     • {from_name}: \"{message}...\"")
    
    def interactive_mode(self):
        """交互模式"""
        print("\n🎮 进入交互模式")
        print("命令：")
        print("  run [ticks] [max_conversations] - 运行指定数量的tick和对话轮数")
        print("  status - 显示当前状态")
        print("  agent [name] - 查看特定agent信息")
        print("  conversations [limit] - 查看对话记录（默认20条）") 
        print("  export_conversations [limit] - 导出对话记录到文件")
        print("  stats - 显示对话统计信息")
        print("  clear - 清空数据库")
        print("  quit - 退出")
        print()
        
        while True:
            try:
                command = input("MamaVillage> ").strip().split()
                
                if not command:
                    continue
                
                cmd = command[0].lower()
                
                if cmd == "quit" or cmd == "exit":
                    print("👋 再见！")
                    break
                
                elif cmd == "run":
                    ticks = int(command[1]) if len(command) > 1 else 5
                    max_conversations = int(command[2]) if len(command) > 2 else None
                    self.run_simulation(max_ticks=ticks, tick_interval=2.0, max_conversations=max_conversations)
                
                elif cmd == "status":
                    self._show_current_status()
                
                elif cmd == "agent":
                    if len(command) > 1:
                        agent_name = command[1]
                        self._show_agent_details(agent_name)
                    else:
                        print("请指定agent名称")
                
                elif cmd == "conversations":
                    limit = int(command[1]) if len(command) > 1 else 20
                    self.show_conversation_history(limit=limit)
                
                elif cmd == "export_conversations":
                    limit = int(command[1]) if len(command) > 1 else 50
                    self.show_conversation_history(limit=limit, export_to_file=True)
                
                elif cmd == "stats":
                    self.show_conversation_stats()
                
                elif cmd == "clear":
                    confirm = input("确定要清空所有数据吗？(y/N): ")
                    if confirm.lower() == 'y':
                        self.db.clear_all_data()
                        self.conversation_count = 0  # 重置对话计数
                        print("数据库已清空")
                
                else:
                    print(f"未知命令: {cmd}")
            
            except KeyboardInterrupt:
                print("\n👋 退出交互模式")
                break
            except Exception as e:
                print(f"❌ 命令执行失败: {e}")
    
    def _show_current_status(self):
        """显示当前状态"""
        print(f"\n📊 当前状态 (Tick {self.tick_count}, Day {self.simulation_day})")
        print(f"⏰ 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"👥 Agent数量: {len(self.agents)}")
        print(f"💬 本次对话数: {self.conversation_count}")
        
        if self.max_conversations:
            progress = (self.conversation_count / self.max_conversations) * 100
            print(f"🎯 对话进度: {self.conversation_count}/{self.max_conversations} ({progress:.1f}%)")
        
        # 显示每个agent的简要信息
        print("\n👤 Agent状态:")
        for agent_id, agent_data in self.agents.items():
            agent_name = agent_data.get("name", agent_id)
            recent_memories = self.db.get_recent_memories(agent_id, limit=5)
            conversations = self.db.get_conversation_history(agent_id, limit=10)
            print(f"   • {agent_name}: {len(recent_memories)}条记忆, {len(conversations)}条对话")
    
    def _show_agent_details(self, agent_name: str):
        """显示agent详细信息"""
        # 查找agent
        agent_id = None
        agent_data = None
        
        for aid, adata in self.agents.items():
            if adata.get("name", "") == agent_name or aid == agent_name:
                agent_id = aid
                agent_data = adata
                break
        
        if not agent_data:
            print(f"未找到agent: {agent_name}")
            return
        
        print(f"\n👤 {agent_data.get('name', agent_id)} 详细信息")
        print(f"ID: {agent_id}")
        print(f"年龄: {agent_data.get('age', '未知')}")
        print(f"角色: {agent_data.get('role', '未知')}")
        print(f"教育: {agent_data.get('education', '未知')}")
        
        # 显示最近记忆
        recent_memories = self.db.get_recent_memories(agent_id, limit=10)
        if recent_memories:
            print(f"\n最近记忆 ({len(recent_memories)}条):")
            for i, memory in enumerate(recent_memories, 1):
                content = memory.get("content", "")
                memory_type = memory.get("memory_type", "")
                importance = memory.get("importance", 1)
                print(f"  {i}. [{memory_type}] {content} (重要性:{importance})")
        
        # 显示最近对话
        conversations = self.db.get_conversation_history(agent_id, limit=5)
        if conversations:
            print(f"\n最近对话 ({len(conversations)}条):")
            for i, conv in enumerate(conversations, 1):
                message = conv.get("message", "")
                from_name = conv.get("from_name", "")
                to_name = conv.get("to_name", "群聊")
                print(f"  {i}. {from_name} → {to_name}: \"{message}\"")

def main():
    """主函数"""
    print("🏡 欢迎来到妈妈互助小区")
    print("一个基于LangGraph + GPT-4o-mini的农村育儿社群模拟系统")
    print()
    
    try:
        # 创建模拟实例
        simulation = MamaVillageSimulation()
        
        # 提供选择
        print("\n请选择运行模式:")
        print("1. 自动模拟 (运行20个tick)")
        print("2. 交互模式")
        print("3. 快速演示 (5个tick)")
        print("4. 限制对话轮数模拟 (自定义)")
        
        choice = input("请输入选择 (1-4): ").strip()
        
        if choice == "1":
            simulation.run_simulation(max_ticks=20, tick_interval=3.0)
        elif choice == "2":
            simulation.interactive_mode()
        elif choice == "3":
            simulation.run_simulation(max_ticks=5, tick_interval=1.5)
        elif choice == "4":
            try:
                max_conversations = int(input("请输入最大对话轮数 (推荐20): ") or "20")
                max_ticks = int(input("请输入最大tick数 (推荐50): ") or "50")
                tick_interval = float(input("请输入tick间隔秒数 (推荐2.0): ") or "2.0")
                
                print(f"\n🎯 启动限制对话模拟：最多{max_conversations}轮对话，{max_ticks}个tick")
                simulation.run_simulation(max_ticks=max_ticks, tick_interval=tick_interval, max_conversations=max_conversations)
                
                # 模拟结束后显示对话记录
                print("\n" + "🎉 模拟完成！下面是对话记录：")
                simulation.show_conversation_history(limit=max_conversations)
                simulation.show_conversation_stats()
                
            except ValueError:
                print("❌ 输入无效，启动交互模式")
                simulation.interactive_mode()
        else:
            print("无效选择，启动交互模式")
            simulation.interactive_mode()
    
    except Exception as e:
        print(f"❌ 程序运行失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()