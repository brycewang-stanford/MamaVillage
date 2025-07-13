#!/usr/bin/env python3
"""
SQLite数据库检查脚本
用于查看和分析memory.sqlite中的所有数据
"""

import sqlite3
import json
import os
from datetime import datetime
from typing import Dict, List, Any
import argparse

class DatabaseChecker:
    """数据库检查器"""
    
    def __init__(self, db_path: str = "memory/memory.sqlite"):
        self.db_path = db_path
        self.conn = None
        
    def connect(self):
        """连接数据库"""
        if not os.path.exists(self.db_path):
            print(f"❌ 数据库文件不存在: {self.db_path}")
            return False
        
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row  # 使结果可以按列名访问
            print(f"✅ 成功连接数据库: {self.db_path}")
            return True
        except Exception as e:
            print(f"❌ 连接数据库失败: {e}")
            return False
    
    def close(self):
        """关闭连接"""
        if self.conn:
            self.conn.close()
    
    def get_table_info(self):
        """获取数据库表信息"""
        print("\n📊 数据库表结构信息")
        print("=" * 80)
        
        cursor = self.conn.cursor()
        
        # 获取所有表名
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        if not tables:
            print("📭 数据库中没有表")
            return
        
        for table in tables:
            table_name = table[0]
            print(f"\n📋 表名: {table_name}")
            
            # 获取表结构
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = cursor.fetchall()
            
            print("   列信息:")
            for col in columns:
                col_id, name, col_type, not_null, default, pk = col
                pk_info = " (主键)" if pk else ""
                null_info = " NOT NULL" if not_null else ""
                default_info = f" DEFAULT {default}" if default else ""
                print(f"     • {name}: {col_type}{pk_info}{null_info}{default_info}")
            
            # 获取记录数
            cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
            count = cursor.fetchone()[0]
            print(f"   📈 记录数: {count}")
    
    def check_agents(self, show_details: bool = True):
        """检查agents表"""
        print("\n👥 Agents表数据")
        print("=" * 80)
        
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM agents ORDER BY created_at;")
        agents = cursor.fetchall()
        
        if not agents:
            print("📭 agents表中没有数据")
            return
        
        print(f"📊 总共 {len(agents)} 个agent")
        
        if show_details:
            for i, agent in enumerate(agents, 1):
                print(f"\n{i}. Agent详细信息:")
                print(f"   ID: {agent['id']}")
                print(f"   姓名: {agent['name']}")
                print(f"   年龄: {agent['age']}")
                print(f"   教育: {agent['education']}")
                print(f"   角色: {agent['role']}")
                print(f"   创建时间: {agent['created_at']}")
                
                if agent['personality']:
                    try:
                        personality = json.loads(agent['personality'])
                        print(f"   性格特点: {personality.get('traits', [])}")
                        print(f"   兴趣爱好: {personality.get('interests', [])}")
                    except json.JSONDecodeError:
                        print(f"   性格信息: {agent['personality']}")
        else:
            for i, agent in enumerate(agents, 1):
                print(f"{i:2d}. {agent['name']} ({agent['role']}, {agent['age']}岁)")
    
    def check_memories(self, limit: int = 20, agent_id: str = None):
        """检查memories表"""
        print(f"\n🧠 Memories表数据 (最近{limit}条)")
        print("=" * 80)
        
        cursor = self.conn.cursor()
        
        if agent_id:
            cursor.execute("""
                SELECT m.*, a.name as agent_name 
                FROM memories m 
                LEFT JOIN agents a ON m.agent_id = a.id 
                WHERE m.agent_id = ? 
                ORDER BY m.timestamp DESC 
                LIMIT ?
            """, (agent_id, limit))
        else:
            cursor.execute("""
                SELECT m.*, a.name as agent_name 
                FROM memories m 
                LEFT JOIN agents a ON m.agent_id = a.id 
                ORDER BY m.timestamp DESC 
                LIMIT ?
            """, (limit,))
        
        memories = cursor.fetchall()
        
        if not memories:
            print("📭 memories表中没有数据")
            return
        
        # 统计信息
        cursor.execute("SELECT COUNT(*) FROM memories;")
        total_count = cursor.fetchone()[0]
        print(f"📊 总记忆数: {total_count}, 显示最近 {len(memories)} 条")
        
        # 按类型统计
        cursor.execute("SELECT memory_type, COUNT(*) FROM memories GROUP BY memory_type;")
        type_stats = cursor.fetchall()
        print("\n📈 记忆类型统计:")
        for memory_type, count in type_stats:
            print(f"   {memory_type}: {count} 条")
        
        print(f"\n📝 记忆详情:")
        for i, memory in enumerate(memories, 1):
            agent_name = memory['agent_name'] or memory['agent_id']
            timestamp = memory['timestamp'][:16] if memory['timestamp'] else "未知时间"
            content = memory['content'][:60] + "..." if len(memory['content']) > 60 else memory['content']
            
            print(f"{i:2d}. [{timestamp}] {agent_name} ({memory['memory_type']}):")
            print(f"    {content}")
            print(f"    重要性: {memory['importance']}")
            
            if memory['metadata']:
                try:
                    metadata = json.loads(memory['metadata'])
                    if metadata:
                        print(f"    元数据: {list(metadata.keys())}")
                except json.JSONDecodeError:
                    pass
    
    def check_conversations(self, limit: int = 20, agent_id: str = None):
        """检查conversations表"""
        print(f"\n💬 Conversations表数据 (最近{limit}条)")
        print("=" * 80)
        
        cursor = self.conn.cursor()
        
        if agent_id:
            cursor.execute("""
                SELECT c.*, 
                       a1.name as from_name, 
                       a2.name as to_name 
                FROM conversations c 
                LEFT JOIN agents a1 ON c.from_agent = a1.id 
                LEFT JOIN agents a2 ON c.to_agent = a2.id 
                WHERE c.from_agent = ? OR c.to_agent = ?
                ORDER BY c.timestamp DESC 
                LIMIT ?
            """, (agent_id, agent_id, limit))
        else:
            cursor.execute("""
                SELECT c.*, 
                       a1.name as from_name, 
                       a2.name as to_name 
                FROM conversations c 
                LEFT JOIN agents a1 ON c.from_agent = a1.id 
                LEFT JOIN agents a2 ON c.to_agent = a2.id 
                ORDER BY c.timestamp DESC 
                LIMIT ?
            """, (limit,))
        
        conversations = cursor.fetchall()
        
        if not conversations:
            print("📭 conversations表中没有数据")
            return
        
        # 统计信息
        cursor.execute("SELECT COUNT(*) FROM conversations;")
        total_count = cursor.fetchone()[0]
        print(f"📊 总对话数: {total_count}, 显示最近 {len(conversations)} 条")
        
        # 按类型统计
        cursor.execute("SELECT conversation_type, COUNT(*) FROM conversations GROUP BY conversation_type;")
        type_stats = cursor.fetchall()
        print("\n📈 对话类型统计:")
        for conv_type, count in type_stats:
            print(f"   {conv_type}: {count} 条")
        
        # 按agent统计
        cursor.execute("""
            SELECT a.name, COUNT(*) as count
            FROM conversations c 
            LEFT JOIN agents a ON c.from_agent = a.id 
            GROUP BY c.from_agent, a.name 
            ORDER BY count DESC
        """)
        agent_stats = cursor.fetchall()
        print("\n👥 发言统计:")
        for name, count in agent_stats:
            agent_name = name or "未知用户"
            print(f"   {agent_name}: {count} 条")
        
        print(f"\n💬 对话详情:")
        for i, conv in enumerate(conversations, 1):
            from_name = conv['from_name'] or conv['from_agent']
            to_name = conv['to_name'] if conv['to_agent'] else "群聊"
            timestamp = conv['timestamp'][:16] if conv['timestamp'] else "未知时间"
            message = conv['message']
            
            type_emoji = {
                'chat': '💬',
                'help_request': '🆘',
                'advice': '💡',
                'content_sharing': '📤'
            }.get(conv['conversation_type'], '💬')
            
            print(f"{i:2d}. [{timestamp}] {type_emoji} {from_name} → {to_name}:")
            print(f"    \"{message}\"")
    
    def check_daily_plans(self, limit: int = 20):
        """检查daily_plans表"""
        print(f"\n📅 Daily Plans表数据 (最近{limit}条)")
        print("=" * 80)
        
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT dp.*, a.name as agent_name 
            FROM daily_plans dp 
            LEFT JOIN agents a ON dp.agent_id = a.id 
            ORDER BY dp.created_at DESC 
            LIMIT ?
        """, (limit,))
        
        plans = cursor.fetchall()
        
        if not plans:
            print("📭 daily_plans表中没有数据")
            return
        
        # 统计信息
        cursor.execute("SELECT COUNT(*) FROM daily_plans;")
        total_count = cursor.fetchone()[0]
        print(f"📊 总计划数: {total_count}, 显示最近 {len(plans)} 条")
        
        # 按状态统计
        cursor.execute("SELECT status, COUNT(*) FROM daily_plans GROUP BY status;")
        status_stats = cursor.fetchall()
        print("\n📈 计划状态统计:")
        for status, count in status_stats:
            print(f"   {status}: {count} 条")
        
        print(f"\n📋 计划详情:")
        for i, plan in enumerate(plans, 1):
            agent_name = plan['agent_name'] or plan['agent_id']
            action = plan['planned_action']
            status = plan['status']
            priority = plan['priority']
            planned_time = plan['planned_time'] or "未指定"
            
            status_emoji = {
                'pending': '⏳',
                'in_progress': '🔄',
                'completed': '✅'
            }.get(status, '❓')
            
            print(f"{i:2d}. {status_emoji} {agent_name} (优先级: {priority}):")
            print(f"    行动: {action}")
            print(f"    时间: {planned_time}")
    
    def search_data(self, keyword: str, table: str = None):
        """搜索数据"""
        print(f"\n🔍 搜索关键词: '{keyword}'")
        print("=" * 80)
        
        cursor = self.conn.cursor()
        
        # 搜索conversations
        if not table or table == 'conversations':
            print("\n💬 对话中的搜索结果:")
            cursor.execute("""
                SELECT c.*, a1.name as from_name, a2.name as to_name 
                FROM conversations c 
                LEFT JOIN agents a1 ON c.from_agent = a1.id 
                LEFT JOIN agents a2 ON c.to_agent = a2.id 
                WHERE c.message LIKE ? 
                ORDER BY c.timestamp DESC
            """, (f'%{keyword}%',))
            
            results = cursor.fetchall()
            if results:
                for i, conv in enumerate(results, 1):
                    from_name = conv['from_name'] or conv['from_agent']
                    to_name = conv['to_name'] if conv['to_agent'] else "群聊"
                    timestamp = conv['timestamp'][:16]
                    message = conv['message']
                    print(f"{i:2d}. [{timestamp}] {from_name} → {to_name}: \"{message}\"")
            else:
                print("   📭 未找到相关对话")
        
        # 搜索memories
        if not table or table == 'memories':
            print("\n🧠 记忆中的搜索结果:")
            cursor.execute("""
                SELECT m.*, a.name as agent_name 
                FROM memories m 
                LEFT JOIN agents a ON m.agent_id = a.id 
                WHERE m.content LIKE ? 
                ORDER BY m.timestamp DESC
            """, (f'%{keyword}%',))
            
            results = cursor.fetchall()
            if results:
                for i, memory in enumerate(results, 1):
                    agent_name = memory['agent_name'] or memory['agent_id']
                    timestamp = memory['timestamp'][:16]
                    content = memory['content'][:80] + "..." if len(memory['content']) > 80 else memory['content']
                    print(f"{i:2d}. [{timestamp}] {agent_name} ({memory['memory_type']}): {content}")
            else:
                print("   📭 未找到相关记忆")
    
    def export_data(self, output_file: str = None):
        """导出数据到文件"""
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"database_export_{timestamp}.txt"
        
        print(f"\n💾 导出数据到文件: {output_file}")
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write("妈妈互助小区 - 数据库导出报告\n")
                f.write("=" * 50 + "\n")
                f.write(f"导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"数据库文件: {self.db_path}\n\n")
                
                # 导出agents
                cursor = self.conn.cursor()
                cursor.execute("SELECT * FROM agents ORDER BY created_at;")
                agents = cursor.fetchall()
                
                f.write("👥 AGENTS 信息\n")
                f.write("-" * 30 + "\n")
                for agent in agents:
                    f.write(f"ID: {agent['id']}\n")
                    f.write(f"姓名: {agent['name']}\n")
                    f.write(f"年龄: {agent['age']}\n")
                    f.write(f"角色: {agent['role']}\n")
                    f.write(f"教育: {agent['education']}\n\n")
                
                # 导出conversations
                cursor.execute("""
                    SELECT c.*, a1.name as from_name, a2.name as to_name 
                    FROM conversations c 
                    LEFT JOIN agents a1 ON c.from_agent = a1.id 
                    LEFT JOIN agents a2 ON c.to_agent = a2.id 
                    ORDER BY c.timestamp
                """)
                conversations = cursor.fetchall()
                
                f.write(f"\n💬 对话记录 ({len(conversations)}条)\n")
                f.write("-" * 30 + "\n")
                for conv in conversations:
                    from_name = conv['from_name'] or conv['from_agent']
                    to_name = conv['to_name'] if conv['to_agent'] else "群聊"
                    timestamp = conv['timestamp']
                    message = conv['message']
                    f.write(f"[{timestamp}] {from_name} → {to_name}: \"{message}\"\n")
                
                # 导出memories统计
                cursor.execute("SELECT memory_type, COUNT(*) FROM memories GROUP BY memory_type;")
                memory_stats = cursor.fetchall()
                
                f.write(f"\n🧠 记忆统计\n")
                f.write("-" * 30 + "\n")
                for memory_type, count in memory_stats:
                    f.write(f"{memory_type}: {count} 条\n")
            
            print(f"✅ 数据导出完成: {output_file}")
            
        except Exception as e:
            print(f"❌ 导出失败: {e}")
    
    def show_summary(self):
        """显示数据库概要"""
        print("\n📊 数据库概要统计")
        print("=" * 80)
        
        cursor = self.conn.cursor()
        
        # 基本统计
        stats = {}
        
        # Agents统计
        cursor.execute("SELECT COUNT(*) FROM agents;")
        stats['agents'] = cursor.fetchone()[0]
        
        # Memories统计
        cursor.execute("SELECT COUNT(*) FROM memories;")
        stats['memories'] = cursor.fetchone()[0]
        
        # Conversations统计
        cursor.execute("SELECT COUNT(*) FROM conversations;")
        stats['conversations'] = cursor.fetchone()[0]
        
        # Daily plans统计
        cursor.execute("SELECT COUNT(*) FROM daily_plans;")
        stats['daily_plans'] = cursor.fetchone()[0]
        
        print(f"👥 Agents: {stats['agents']} 个")
        print(f"🧠 Memories: {stats['memories']} 条")
        print(f"💬 Conversations: {stats['conversations']} 条")
        print(f"📅 Daily Plans: {stats['daily_plans']} 条")
        
        # 时间范围
        cursor.execute("SELECT MIN(timestamp), MAX(timestamp) FROM conversations;")
        time_range = cursor.fetchone()
        if time_range[0]:
            print(f"⏰ 对话时间范围: {time_range[0][:16]} 至 {time_range[1][:16]}")
        
        # 最活跃的agent
        cursor.execute("""
            SELECT a.name, COUNT(*) as count
            FROM conversations c 
            LEFT JOIN agents a ON c.from_agent = a.id 
            GROUP BY c.from_agent, a.name 
            ORDER BY count DESC 
            LIMIT 1
        """)
        most_active = cursor.fetchone()
        if most_active:
            print(f"🎯 最活跃Agent: {most_active[0]} ({most_active[1]} 条对话)")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="检查妈妈互助小区数据库")
    parser.add_argument("--db", default="memory/memory.sqlite", help="数据库文件路径")
    parser.add_argument("--table", choices=['agents', 'memories', 'conversations', 'daily_plans'], help="指定检查的表")
    parser.add_argument("--agent", help="指定agent ID或名称")
    parser.add_argument("--limit", type=int, default=20, help="限制显示的记录数")
    parser.add_argument("--search", help="搜索关键词")
    parser.add_argument("--export", help="导出数据到文件")
    parser.add_argument("--summary", action="store_true", help="只显示概要统计")
    parser.add_argument("--no-details", action="store_true", help="不显示详细信息")
    
    args = parser.parse_args()
    
    print("🔍 妈妈互助小区数据库检查工具")
    print("=" * 80)
    
    # 创建检查器
    checker = DatabaseChecker(args.db)
    
    if not checker.connect():
        return 1
    
    try:
        # 显示概要
        if args.summary:
            checker.show_summary()
            return 0
        
        # 搜索功能
        if args.search:
            checker.search_data(args.search, args.table)
            return 0
        
        # 导出功能
        if args.export:
            checker.export_data(args.export)
            return 0
        
        # 显示表信息
        checker.get_table_info()
        
        # 显示概要统计
        checker.show_summary()
        
        # 根据指定表显示数据
        if args.table == 'agents' or not args.table:
            checker.check_agents(show_details=not args.no_details)
        
        if args.table == 'memories' or not args.table:
            agent_id = None
            if args.agent:
                # 查找agent ID
                cursor = checker.conn.cursor()
                cursor.execute("SELECT id FROM agents WHERE id = ? OR name = ?", (args.agent, args.agent))
                result = cursor.fetchone()
                if result:
                    agent_id = result[0]
            checker.check_memories(args.limit, agent_id)
        
        if args.table == 'conversations' or not args.table:
            agent_id = None
            if args.agent:
                cursor = checker.conn.cursor()
                cursor.execute("SELECT id FROM agents WHERE id = ? OR name = ?", (args.agent, args.agent))
                result = cursor.fetchone()
                if result:
                    agent_id = result[0]
            checker.check_conversations(args.limit, agent_id)
        
        if args.table == 'daily_plans' or not args.table:
            checker.check_daily_plans(args.limit)
        
        return 0
        
    except KeyboardInterrupt:
        print("\n⚠️ 用户中断")
        return 1
    except Exception as e:
        print(f"\n❌ 检查过程中出错: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        checker.close()

if __name__ == "__main__":
    exit(main())