#!/usr/bin/env python3
"""
测试AWS RDS PostgreSQL数据库连接
"""

import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

def test_database_connection():
    """测试数据库连接"""
    
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ 未找到 DATABASE_URL 环境变量")
        return False
    
    print(f"🔗 正在连接数据库...")
    print(f"   URL: {database_url.replace(':12345678@', ':****@')}")  # 隐藏密码
    
    try:
        # 创建数据库引擎
        engine = create_engine(database_url)
        
        # 测试连接
        with engine.connect() as connection:
            # 执行简单查询
            result = connection.execute(text("SELECT version();"))
            version = result.fetchone()[0]
            
            print("✅ 数据库连接成功!")
            print(f"   PostgreSQL版本: {version}")
            
            # 检查数据库信息
            result = connection.execute(text("SELECT current_database(), current_user;"))
            db_info = result.fetchone()
            
            print(f"   当前数据库: {db_info[0]}")
            print(f"   当前用户: {db_info[1]}")
            
            # 检查现有表
            result = connection.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name;
            """))
            
            tables = result.fetchall()
            if tables:
                print(f"   现有表: {', '.join([table[0] for table in tables])}")
            else:
                print("   📝 数据库中暂无表（首次运行时正常）")
            
            return True
            
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        return False

def create_tables():
    """创建数据表"""
    print("\n🏗️  正在创建数据表...")
    
    try:
        # 导入必要的模块
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        from app.database import create_tables as db_create_tables
        
        db_create_tables()
        print("✅ 数据表创建成功!")
        
    except Exception as e:
        print(f"❌ 数据表创建失败: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("🚀 开始数据库连接测试")
    print("=" * 50)
    
    # 测试连接
    if test_database_connection():
        print("\n" + "=" * 50)
        
        # 询问是否创建表
        create_tables_choice = input("\n是否创建数据表? (y/n): ").lower().strip()
        if create_tables_choice in ['y', 'yes']:
            create_tables()
        
        print(f"\n🎉 数据库设置完成!")
        print(f"💡 提示: 现在可以启动FastAPI应用了")
        print(f"   python main.py")
        
    else:
        print("\n❌ 请检查数据库配置和网络连接")
        print("💡 常见问题:")
        print("   1. 检查AWS RDS安全组是否允许您的IP访问")
        print("   2. 检查数据库用户名和密码是否正确")
        print("   3. 检查网络连接是否正常")