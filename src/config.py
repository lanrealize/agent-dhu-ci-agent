"""配置管理模块

使用 Pydantic Settings 管理应用配置，支持从环境变量和 .env 文件加载配置。
"""

from functools import lru_cache
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置类"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # LLM 配置
    deepseek_api_key: str = Field(..., description="Deepseek API Key")
    deepseek_base_url: str = Field(
        default="https://api.deepseek.com/v1",
        description="Deepseek API Base URL",
    )
    deepseek_model: str = Field(
        default="deepseek-chat",
        description="Deepseek Model Name",
    )

    # 数据库配置
    database_url: str = Field(
        default="sqlite:///./devops_agent.db",
        description="SQL 数据库连接 URL（保留用于兼容）",
    )

    # MongoDB 配置
    mongodb_url: str = Field(
        default="mongodb://localhost:27017",
        description="MongoDB 连接 URL（无用户名密码）",
    )
    mongodb_database: str = Field(
        default="dhuci_agent_db",
        description="MongoDB 数据库名称",
    )

    # API 配置
    api_host: str = Field(default="0.0.0.0", description="API 服务监听地址")
    api_port: int = Field(default=8000, description="API 服务端口")
    api_reload: bool = Field(default=False, description="开发模式自动重载")

    # Jenkins 配置
    jenkins_url: str = Field(
        default="http://mock-jenkins:8080",
        description="Jenkins 服务地址",
    )
    jenkins_user: Optional[str] = Field(
        default="admin",
        description="Jenkins 用户名",
    )
    jenkins_token: Optional[str] = Field(
        default="mock_jenkins_token",
        description="Jenkins API Token",
    )

    # Gerrit 配置
    gerrit_url: str = Field(
        default="http://mock-gerrit:8080",
        description="Gerrit 服务地址",
    )
    gerrit_user: Optional[str] = Field(
        default="admin",
        description="Gerrit 用户名",
    )
    gerrit_password: Optional[str] = Field(
        default="mock_gerrit_password",
        description="Gerrit 密码",
    )

    # Artifactory 配置
    artifactory_url: str = Field(
        default="http://mock-artifactory:8081",
        description="Artifactory 服务地址",
    )
    artifactory_user: Optional[str] = Field(
        default="admin",
        description="Artifactory 用户名",
    )
    artifactory_password: Optional[str] = Field(
        default="mock_artifactory_password",
        description="Artifactory 密码",
    )
    artifactory_api_key: Optional[str] = Field(
        default="mock_artifactory_api_key",
        description="Artifactory API Key",
    )

    # 自定义后端配置
    custom_backend_url: str = Field(
        default="http://mock-backend:3000",
        description="自定义后端服务地址",
    )
    custom_backend_api_key: Optional[str] = Field(
        default="mock_backend_api_key",
        description="自定义后端 API Key",
    )

    # 日志配置
    log_level: str = Field(default="INFO", description="日志级别")
    log_format: str = Field(default="default", description="日志格式 (default/json)")

    # 安全配置
    secret_key: str = Field(
        default="your_secret_key_here_change_in_production",
        description="JWT 密钥",
    )
    algorithm: str = Field(default="HS256", description="JWT 算法")
    access_token_expire_minutes: int = Field(
        default=30,
        description="访问令牌过期时间（分钟）",
    )


@lru_cache()
def get_settings() -> Settings:
    """获取配置单例

    使用 lru_cache 确保配置只加载一次。

    Returns:
        Settings: 配置对象
    """
    return Settings()


# 导出配置实例
settings = get_settings()
