from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    # 数据库配置
    database_url: str = "postgresql://postgres:12345678@divination.cluster-chwuqka62eu2.ap-southeast-2.rds.amazonaws.com:5432/divination_db"
    
    # OpenRouter API 配置
    openrouter_api_key: str = "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"
    
    # JWT 配置
    secret_key: str = "your_secret_key_here_change_in_production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # 应用配置
    app_name: str = "FateWave API"
    debug: bool = True
    cors_origins: str = "http://localhost:3000,https://fatewave.com"
    
    # OpenRouter 配置
    openrouter_referer: str = "http://localhost:3000"
    openrouter_site_name: str = "FateWave"
    
    # 业务配置
    free_usage_limit: int = 50  # 登录用户50次免费
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": False
    }

    @property
    def cors_origins_list(self) -> List[str]:
        """将CORS_ORIGINS字符串转换为列表"""
        return [origin.strip() for origin in self.cors_origins.split(',')]


# 全局配置实例
settings = Settings() 