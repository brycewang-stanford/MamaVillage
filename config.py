import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """配置管理类"""
    
    # OpenAI API 配置
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    
    # 数据库配置
    DATABASE_PATH = os.getenv("DATABASE_PATH", "memory/memory.sqlite")
    
    # 日志配置
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    
    @classmethod
    def validate(cls):
        """验证必要的配置是否存在"""
        if not cls.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY 环境变量未设置，请检查 .env 文件")
        
        print(f"✅ 配置加载成功")
        print(f"   模型: {cls.OPENAI_MODEL}")
        print(f"   数据库: {cls.DATABASE_PATH}")
        print(f"   日志级别: {cls.LOG_LEVEL}")