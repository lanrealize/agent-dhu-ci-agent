#!/usr/bin/env python
"""启动脚本

快速启动 DevOps Agent API 服务。
"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

if __name__ == "__main__":
    import uvicorn
    from src.config import settings

    print("=" * 60)
    print("DevOps Agent API 启动中...")
    print("=" * 60)
    print(f"API 地址: http://{settings.api_host}:{settings.api_port}")
    print(f"API 文档: http://{settings.api_host}:{settings.api_port}/docs")
    print("=" * 60)

    uvicorn.run(
        "src.api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload,
    )
