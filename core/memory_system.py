"""
MamaVillage 现代化记忆系统
基于 LangChain Memory + SQLite 的持久化记忆管理
"""

import sqlite3
import json
import uuid
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from pathlib import Path

from langchain.memory.chat_memory import BaseChatMemory
from langchain.schema import BaseMessage, HumanMessage, AIMessage
from langchain.memory import ConversationSummaryBufferMemory
from langchain_openai import ChatOpenAI

from .state import Memory, MemoryType, Conversation, ConversationType
from .agent_profile import AgentProfile
from config import Config


class PersistentMemoryStore:
    """持久化记忆存储系统"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or Config.DATABASE_PATH
        self.ensure_database_dir()
        self.init_database()
    
    def ensure_database_dir(self):
        """确保数据库目录存在"""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
    
    def init_database(self):
        """初始化数据库表结构"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Agent基础信息表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS agents (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    profile_data TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 记忆表（使用现代化设计）
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS memories (
                    id TEXT PRIMARY KEY,
                    agent_id TEXT NOT NULL,
                    content TEXT NOT NULL,
                    memory_type TEXT NOT NULL,
                    importance INTEGER DEFAULT 5,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT DEFAULT '{}',
                    embedding_vector TEXT,
                    related_memories TEXT DEFAULT '[]',
                    FOREIGN KEY (agent_id) REFERENCES agents (id)
                )
            ''')
            
            # 对话历史表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS conversations (
                    id TEXT PRIMARY KEY,
                    from_agent TEXT NOT NULL,
                    to_agent TEXT,
                    message TEXT NOT NULL,
                    conversation_type TEXT DEFAULT 'group_chat',
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT DEFAULT '{}',
                    session_id TEXT,
                    FOREIGN KEY (from_agent) REFERENCES agents (id),
                    FOREIGN KEY (to_agent) REFERENCES agents (id)
                )
            ''')
            
            # Agent会话状态表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS agent_sessions (
                    id TEXT PRIMARY KEY,
                    agent_id TEXT NOT NULL,
                    session_data TEXT NOT NULL,
                    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (agent_id) REFERENCES agents (id)
                )
            ''')
            
            # 模拟状态表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS simulation_state (
                    id INTEGER PRIMARY KEY,
                    tick_count INTEGER DEFAULT 0,
                    simulation_day INTEGER DEFAULT 1,
                    conversation_count INTEGER DEFAULT 0,
                    state_data TEXT DEFAULT '{}',
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 创建索引
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_memories_agent_time ON memories (agent_id, timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_memories_type ON memories (memory_type)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_conversations_agents ON conversations (from_agent, to_agent)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_conversations_time ON conversations (timestamp)')
            
            conn.commit()
    
    def save_agent_profile(self, profile: AgentProfile) -> bool:
        """保存Agent配置文件"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO agents (id, name, profile_data, updated_at)
                    VALUES (?, ?, ?, ?)
                ''', (
                    profile.id,
                    profile.name,
                    json.dumps(profile.dict(), ensure_ascii=False),
                    datetime.now().isoformat()
                ))
                conn.commit()
                return True
        except Exception as e:
            print(f"❌ 保存Agent配置失败: {e}")
            return False
    
    def load_agent_profile(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """加载Agent配置文件"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT profile_data FROM agents WHERE id = ?', (agent_id,))
                result = cursor.fetchone()
                if result:
                    return json.loads(result[0])
                return None
        except Exception as e:
            print(f"❌ 加载Agent配置失败: {e}")
            return None
    
    def save_memory(self, memory: Memory) -> bool:
        """保存记忆"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                memory_id = memory.id or str(uuid.uuid4())
                cursor.execute('''
                    INSERT OR REPLACE INTO memories 
                    (id, agent_id, content, memory_type, importance, timestamp, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    memory_id,
                    memory.agent_id,
                    memory.content,
                    memory.memory_type.value,
                    memory.importance,
                    memory.timestamp.isoformat(),
                    json.dumps(memory.metadata or {}, ensure_ascii=False)
                ))
                conn.commit()
                return True
        except Exception as e:
            print(f"❌ 保存记忆失败: {e}")
            return False
    
    def get_memories(self, agent_id: str, limit: int = 50, 
                    memory_type: Optional[MemoryType] = None,
                    since: Optional[datetime] = None) -> List[Memory]:
        """获取记忆"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                query = '''
                    SELECT id, agent_id, content, memory_type, importance, timestamp, metadata
                    FROM memories WHERE agent_id = ?
                '''
                params = [agent_id]
                
                if memory_type:
                    query += ' AND memory_type = ?'
                    params.append(memory_type.value)
                
                if since:
                    query += ' AND timestamp >= ?'
                    params.append(since.isoformat())
                
                query += ' ORDER BY timestamp DESC LIMIT ?'
                params.append(limit)
                
                cursor.execute(query, params)
                
                memories = []
                for row in cursor.fetchall():
                    memory = Memory(
                        id=row[0],
                        agent_id=row[1],
                        content=row[2],
                        memory_type=MemoryType(row[3]),
                        importance=row[4],
                        timestamp=datetime.fromisoformat(row[5]),
                        metadata=json.loads(row[6]) if row[6] else {}
                    )
                    memories.append(memory)
                
                return memories
        except Exception as e:
            print(f"❌ 获取记忆失败: {e}")
            return []
    
    def save_conversation(self, conversation: Conversation) -> bool:
        """保存对话"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                conv_id = conversation.id or str(uuid.uuid4())
                cursor.execute('''
                    INSERT OR REPLACE INTO conversations 
                    (id, from_agent, to_agent, message, conversation_type, timestamp, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    conv_id,
                    conversation.from_agent,
                    conversation.to_agent,
                    conversation.message,
                    conversation.conversation_type.value,
                    conversation.timestamp.isoformat(),
                    json.dumps(conversation.metadata or {}, ensure_ascii=False)
                ))
                conn.commit()
                return True
        except Exception as e:
            print(f"❌ 保存对话失败: {e}")
            return False
    
    def get_conversations(self, agent_id: str = None, limit: int = 50,
                         since: Optional[datetime] = None) -> List[Conversation]:
        """获取对话历史"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                if agent_id:
                    query = '''
                        SELECT id, from_agent, to_agent, message, conversation_type, timestamp, metadata
                        FROM conversations 
                        WHERE from_agent = ? OR to_agent = ? OR to_agent IS NULL
                    '''
                    params = [agent_id, agent_id]
                else:
                    query = '''
                        SELECT id, from_agent, to_agent, message, conversation_type, timestamp, metadata
                        FROM conversations 
                        WHERE 1=1
                    '''
                    params = []
                
                if since:
                    query += ' AND timestamp >= ?'
                    params.append(since.isoformat())
                
                query += ' ORDER BY timestamp DESC LIMIT ?'
                params.append(limit)
                
                cursor.execute(query, params)
                
                conversations = []
                for row in cursor.fetchall():
                    conversation = Conversation(
                        id=row[0],
                        from_agent=row[1],
                        to_agent=row[2],
                        message=row[3],
                        conversation_type=ConversationType(row[4]),
                        timestamp=datetime.fromisoformat(row[5]),
                        metadata=json.loads(row[6]) if row[6] else {}
                    )
                    conversations.append(conversation)
                
                return conversations
        except Exception as e:
            print(f"❌ 获取对话历史失败: {e}")
            return []
    
    def clear_all_data(self):
        """清空所有数据"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM conversations')
                cursor.execute('DELETE FROM memories')
                cursor.execute('DELETE FROM agent_sessions')
                cursor.execute('DELETE FROM simulation_state')
                cursor.execute('DELETE FROM agents')
                conn.commit()
                print("🧹 数据库已清空")
        except Exception as e:
            print(f"❌ 清空数据库失败: {e}")


class AgentMemoryManager:
    """Agent记忆管理器"""
    
    def __init__(self, agent_id: str, store: PersistentMemoryStore):
        self.agent_id = agent_id
        self.store = store
        
        # LangChain记忆组件
        self.llm = ChatOpenAI(
            model=Config.OPENAI_MODEL,
            api_key=Config.OPENAI_API_KEY
        )
        
        # 对话摘要记忆
        self.summary_memory = ConversationSummaryBufferMemory(
            llm=self.llm,
            max_token_limit=1000,
            return_messages=True
        )
        
        # 加载历史对话到记忆中
        self._load_recent_conversations()
    
    def _load_recent_conversations(self):
        """加载最近对话到记忆中"""
        recent_conversations = self.store.get_conversations(
            agent_id=self.agent_id,
            limit=10,
            since=datetime.now() - timedelta(hours=24)
        )
        
        for conv in reversed(recent_conversations):  # 按时间顺序添加
            if conv.from_agent == self.agent_id:
                message = AIMessage(content=conv.message)
            else:
                message = HumanMessage(content=conv.message)
            
            self.summary_memory.chat_memory.add_message(message)
    
    def add_conversation_to_memory(self, conversation: Conversation):
        """添加对话到记忆中"""
        # 保存到持久化存储
        self.store.save_conversation(conversation)
        
        # 添加到LangChain记忆
        if conversation.from_agent == self.agent_id:
            message = AIMessage(content=conversation.message)
        else:
            message = HumanMessage(content=conversation.message)
        
        self.summary_memory.chat_memory.add_message(message)
    
    def add_memory(self, memory: Memory):
        """添加记忆"""
        self.store.save_memory(memory)
    
    def get_memories(self, memory_type: Optional[MemoryType] = None,
                    limit: int = 20) -> List[Memory]:
        """获取记忆"""
        return self.store.get_memories(
            agent_id=self.agent_id,
            memory_type=memory_type,
            limit=limit
        )
    
    def get_relevant_memories(self, query: str, limit: int = 5) -> List[Memory]:
        """获取相关记忆（简单关键词匹配）"""
        all_memories = self.get_memories(limit=100)
        relevant_memories = []
        
        query_keywords = query.lower().split()
        
        for memory in all_memories:
            content_lower = memory.content.lower()
            relevance_score = sum(1 for keyword in query_keywords if keyword in content_lower)
            
            if relevance_score > 0:
                relevant_memories.append((memory, relevance_score))
        
        # 按相关性和重要性排序
        relevant_memories.sort(key=lambda x: (x[1], x[0].importance), reverse=True)
        
        return [memory for memory, _ in relevant_memories[:limit]]
    
    def get_conversation_context(self) -> str:
        """获取对话上下文"""
        return self.summary_memory.buffer
    
    def get_conversation_summary(self) -> str:
        """获取对话摘要"""
        if hasattr(self.summary_memory, 'moving_summary_buffer'):
            return self.summary_memory.moving_summary_buffer
        return ""


class MemorySystemManager:
    """记忆系统管理器"""
    
    def __init__(self, db_path: str = None):
        self.store = PersistentMemoryStore(db_path)
        self.agent_managers: Dict[str, AgentMemoryManager] = {}
    
    def get_agent_memory_manager(self, agent_id: str) -> AgentMemoryManager:
        """获取Agent记忆管理器"""
        if agent_id not in self.agent_managers:
            self.agent_managers[agent_id] = AgentMemoryManager(agent_id, self.store)
        return self.agent_managers[agent_id]
    
    def register_agent(self, profile: AgentProfile):
        """注册Agent"""
        self.store.save_agent_profile(profile)
        # 创建记忆管理器
        self.get_agent_memory_manager(profile.id)
    
    def add_conversation(self, conversation: Conversation):
        """添加对话到系统"""
        # 保存到持久化存储
        self.store.save_conversation(conversation)
        
        # 更新相关Agent的记忆管理器
        from_manager = self.get_agent_memory_manager(conversation.from_agent)
        from_manager.add_conversation_to_memory(conversation)
        
        if conversation.to_agent:
            to_manager = self.get_agent_memory_manager(conversation.to_agent)
            to_manager.add_conversation_to_memory(conversation)
    
    def get_conversation_history(self, limit: int = 50) -> List[Conversation]:
        """获取所有对话历史"""
        return self.store.get_conversations(limit=limit)
    
    def get_conversation_stats(self) -> Dict[str, Any]:
        """获取对话统计信息"""
        all_conversations = self.get_conversation_history(limit=1000)
        
        stats = {
            "total_conversations": len(all_conversations),
            "conversations_by_type": {},
            "conversations_by_agent": {},
            "recent_activity": len([c for c in all_conversations 
                                 if c.timestamp > datetime.now() - timedelta(hours=1)])
        }
        
        for conv in all_conversations:
            # 按类型统计
            conv_type = conv.conversation_type.value
            stats["conversations_by_type"][conv_type] = stats["conversations_by_type"].get(conv_type, 0) + 1
            
            # 按Agent统计
            from_agent = conv.from_agent
            stats["conversations_by_agent"][from_agent] = stats["conversations_by_agent"].get(from_agent, 0) + 1
        
        return stats
    
    def cleanup_old_data(self, days_to_keep: int = 7):
        """清理旧数据"""
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        try:
            with sqlite3.connect(self.store.db_path) as conn:
                cursor = conn.cursor()
                
                # 删除旧对话
                cursor.execute('DELETE FROM conversations WHERE timestamp < ?', (cutoff_date.isoformat(),))
                
                # 删除低重要性的旧记忆
                cursor.execute('''
                    DELETE FROM memories 
                    WHERE timestamp < ? AND importance < 5
                ''', (cutoff_date.isoformat(),))
                
                conn.commit()
                print(f"🧹 已清理 {days_to_keep} 天前的旧数据")
        except Exception as e:
            print(f"❌ 清理数据失败: {e}")
    
    def export_conversation_history(self, filename: str = None) -> str:
        """导出对话历史"""
        if not filename:
            filename = f"conversations_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        conversations = self.get_conversation_history(limit=1000)
        
        export_data = {
            "export_time": datetime.now().isoformat(),
            "total_conversations": len(conversations),
            "conversations": [conv.dict() for conv in conversations]
        }
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2, default=str)
            
            print(f"💾 对话历史已导出到: {filename}")
            return filename
        except Exception as e:
            print(f"❌ 导出失败: {e}")
            return ""