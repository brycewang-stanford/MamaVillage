import sqlite3
import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from config import Config

class MemoryDatabase:
    """妈妈村记忆数据库管理类"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or Config.DATABASE_PATH
        self.ensure_database_dir()
        self.init_database()
    
    def ensure_database_dir(self):
        """确保数据库目录存在"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
    
    def init_database(self):
        """初始化数据库表结构"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 创建agent基础信息表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS agents (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    age INTEGER,
                    education TEXT,
                    role TEXT,
                    personality TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 创建记忆表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS memories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_id TEXT NOT NULL,
                    memory_type TEXT NOT NULL,  -- 'observation', 'reflection', 'conversation'
                    content TEXT NOT NULL,
                    importance INTEGER DEFAULT 1,  -- 1-10 重要性评分
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT,  -- JSON格式的额外信息
                    FOREIGN KEY (agent_id) REFERENCES agents (id)
                )
            ''')
            
            # 创建对话历史表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    from_agent TEXT NOT NULL,
                    to_agent TEXT,  -- NULL表示群聊
                    message TEXT NOT NULL,
                    conversation_type TEXT DEFAULT 'chat',  -- 'chat', 'video_share', 'advice'
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT,
                    FOREIGN KEY (from_agent) REFERENCES agents (id),
                    FOREIGN KEY (to_agent) REFERENCES agents (id)
                )
            ''')
            
            # 创建行为计划表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS daily_plans (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_id TEXT NOT NULL,
                    planned_action TEXT NOT NULL,
                    priority INTEGER DEFAULT 1,
                    status TEXT DEFAULT 'pending',  -- 'pending', 'in_progress', 'completed'
                    planned_time TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (agent_id) REFERENCES agents (id)
                )
            ''')
            
            conn.commit()
    
    def add_agent(self, agent_data: Dict[str, Any]) -> bool:
        """添加新agent"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO agents (id, name, age, education, role, personality)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    agent_data['id'],
                    agent_data['name'],
                    agent_data.get('age'),
                    agent_data.get('education'),
                    agent_data.get('role'),
                    json.dumps(agent_data.get('personality', {}), ensure_ascii=False)
                ))
                conn.commit()
                return True
        except Exception as e:
            print(f"❌ 添加agent失败: {e}")
            return False
    
    def add_memory(self, agent_id: str, memory_type: str, content: str, 
                   importance: int = 1, metadata: Dict = None) -> bool:
        """添加记忆"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO memories (agent_id, memory_type, content, importance, metadata)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    agent_id,
                    memory_type,
                    content,
                    importance,
                    json.dumps(metadata or {}, ensure_ascii=False)
                ))
                conn.commit()
                return True
        except Exception as e:
            print(f"❌ 添加记忆失败: {e}")
            return False
    
    def get_recent_memories(self, agent_id: str, limit: int = 10, 
                           memory_type: str = None) -> List[Dict]:
        """获取最近的记忆"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                if memory_type:
                    cursor.execute('''
                        SELECT * FROM memories 
                        WHERE agent_id = ? AND memory_type = ?
                        ORDER BY timestamp DESC LIMIT ?
                    ''', (agent_id, memory_type, limit))
                else:
                    cursor.execute('''
                        SELECT * FROM memories 
                        WHERE agent_id = ?
                        ORDER BY timestamp DESC LIMIT ?
                    ''', (agent_id, limit))
                
                columns = [description[0] for description in cursor.description]
                memories = []
                for row in cursor.fetchall():
                    memory = dict(zip(columns, row))
                    if memory['metadata']:
                        memory['metadata'] = json.loads(memory['metadata'])
                    memories.append(memory)
                
                return memories
        except Exception as e:
            print(f"❌ 获取记忆失败: {e}")
            return []
    
    def add_conversation(self, from_agent: str, message: str, to_agent: str = None,
                        conversation_type: str = 'chat', metadata: Dict = None) -> bool:
        """添加对话记录"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO conversations (from_agent, to_agent, message, conversation_type, metadata)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    from_agent,
                    to_agent,
                    message,
                    conversation_type,
                    json.dumps(metadata or {}, ensure_ascii=False)
                ))
                conn.commit()
                return True
        except Exception as e:
            print(f"❌ 添加对话失败: {e}")
            return False
    
    def get_conversation_history(self, agent_id: str, limit: int = 20) -> List[Dict]:
        """获取对话历史"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT c.*, a1.name as from_name, a2.name as to_name
                    FROM conversations c
                    LEFT JOIN agents a1 ON c.from_agent = a1.id
                    LEFT JOIN agents a2 ON c.to_agent = a2.id
                    WHERE c.from_agent = ? OR c.to_agent = ? OR c.to_agent IS NULL
                    ORDER BY c.timestamp DESC LIMIT ?
                ''', (agent_id, agent_id, limit))
                
                columns = [description[0] for description in cursor.description]
                conversations = []
                for row in cursor.fetchall():
                    conv = dict(zip(columns, row))
                    if conv['metadata']:
                        conv['metadata'] = json.loads(conv['metadata'])
                    conversations.append(conv)
                
                return conversations
        except Exception as e:
            print(f"❌ 获取对话历史失败: {e}")
            return []
    
    def get_all_agents(self) -> List[Dict]:
        """获取所有agent信息"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM agents')
                
                columns = [description[0] for description in cursor.description]
                agents = []
                for row in cursor.fetchall():
                    agent = dict(zip(columns, row))
                    if agent['personality']:
                        agent['personality'] = json.loads(agent['personality'])
                    agents.append(agent)
                
                return agents
        except Exception as e:
            print(f"❌ 获取agents失败: {e}")
            return []
    
    def add_daily_plan(self, agent_id: str, planned_action: str, priority: int = 1,
                      planned_time: str = None, status: str = 'pending') -> bool:
        """添加日常计划"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO daily_plans (agent_id, planned_action, priority, planned_time, status)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    agent_id,
                    planned_action,
                    priority,
                    planned_time,
                    status
                ))
                conn.commit()
                return True
        except Exception as e:
            print(f"❌ 添加计划失败: {e}")
            return False
    
    def get_daily_plans(self, agent_id: str, limit: int = 10, status: str = None) -> List[Dict]:
        """获取日常计划"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                if status:
                    cursor.execute('''
                        SELECT * FROM daily_plans 
                        WHERE agent_id = ? AND status = ?
                        ORDER BY created_at DESC LIMIT ?
                    ''', (agent_id, status, limit))
                else:
                    cursor.execute('''
                        SELECT * FROM daily_plans 
                        WHERE agent_id = ?
                        ORDER BY created_at DESC LIMIT ?
                    ''', (agent_id, limit))
                
                columns = [description[0] for description in cursor.description]
                plans = []
                for row in cursor.fetchall():
                    plan = dict(zip(columns, row))
                    plans.append(plan)
                
                return plans
        except Exception as e:
            print(f"❌ 获取计划失败: {e}")
            return []
    
    def update_plan_status(self, plan_id: int, status: str) -> bool:
        """更新计划状态"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE daily_plans SET status = ? WHERE id = ?
                ''', (status, plan_id))
                conn.commit()
                return True
        except Exception as e:
            print(f"❌ 更新计划状态失败: {e}")
            return False

    def clear_all_data(self):
        """清空所有数据（测试用）"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM conversations')
            cursor.execute('DELETE FROM memories')
            cursor.execute('DELETE FROM daily_plans')
            cursor.execute('DELETE FROM agents')
            conn.commit()
            print("🧹 数据库已清空")