"""日志配置模块

配置应用日志系统，支持多种日志格式和输出。
"""

import logging
import logging.config
import os
from pathlib import Path
from typing import Optional

import yaml

from src.config import settings


def setup_logging(config_path: Optional[str] = None) -> None:
    """配置日志系统

    Args:
        config_path: 日志配置文件路径，默认使用 configs/logging.yaml
    """
    if config_path is None:
        config_path = "configs/logging.yaml"

    # 确保日志目录存在
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)

    # 加载日志配置
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
            logging.config.dictConfig(config)
    else:
        # 如果配置文件不存在，使用默认配置
        logging.basicConfig(
            level=getattr(logging, settings.log_level.upper()),
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    logger = logging.getLogger(__name__)
    logger.info("日志系统初始化完成")


def get_logger(name: str) -> logging.Logger:
    """获取指定名称的 Logger

    Args:
        name: Logger 名称

    Returns:
        logging.Logger: Logger 对象
    """
    return logging.getLogger(name)
