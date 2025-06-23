from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .config import settings

# 创建数据库引擎
engine = create_engine(
    settings.database_url,
    echo=settings.debug,  # 在调试模式下显示SQL语句
)

# 创建数据库会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建数据库模型基类
Base = declarative_base()


# 数据库会话依赖
def get_db():
    """获取数据库会话的依赖注入函数"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# 创建所有数据表
def create_tables():
    """创建所有数据表"""
    Base.metadata.create_all(bind=engine) 