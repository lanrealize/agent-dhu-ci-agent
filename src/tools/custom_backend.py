"""自定义后端查询工具

查询用户自定义后端服务的 API。
"""

from typing import Any, Dict

from src.config import settings
from src.tools.base import DevOpsBaseTool


class CustomBackendTool(DevOpsBaseTool):
    """自定义后端查询工具"""

    name: str = "custom_backend"
    description: str = """查询自定义后端服务的 API 数据。

    使用方法: 输入查询参数，格式为 "endpoint:参数"
    例如: "metrics:project=my-project" 或 "health"
    返回: 自定义后端 API 的响应数据
    """

    def _execute(self, query: str) -> Dict[str, Any]:
        """执行自定义后端查询

        Args:
            query: 查询参数，格式为 "endpoint:参数" 或 "endpoint"

        Returns:
            Dict[str, Any]: API 响应数据
        """
        # 解析查询参数
        if ":" in query:
            endpoint, params_str = query.split(":", 1)
            endpoint = endpoint.strip()
            # 简单解析参数 (实际可能需要更复杂的解析)
            params = {}
            if params_str:
                for param in params_str.split(","):
                    if "=" in param:
                        key, value = param.split("=", 1)
                        params[key.strip()] = value.strip()
        else:
            endpoint = query.strip()
            params = {}

        # Mock 数据 - 实际应该调用自定义后端 API
        # headers = {"X-API-Key": settings.custom_backend_api_key}
        # async with HTTPClient(settings.custom_backend_url, headers=headers) as client:
        #     response = await client.get(f"/api/{endpoint}", params=params)
        #     return response.json()

        # 根据不同的 endpoint 返回不同的 mock 数据
        if endpoint == "health":
            mock_data = {
                "status": "healthy",
                "version": "1.0.0",
                "uptime": 86400,
                "timestamp": "2026-01-04T10:30:00Z",
            }
        elif endpoint == "metrics":
            project = params.get("project", "unknown")
            mock_data = {
                "project": project,
                "code_quality": {
                    "bugs": 5,
                    "vulnerabilities": 2,
                    "code_smells": 38,
                    "technical_debt_hours": 12.5,
                    "maintainability_rating": "A",
                    "reliability_rating": "B",
                    "security_rating": "A",
                },
                "performance": {
                    "average_response_time_ms": 125,
                    "p95_response_time_ms": 350,
                    "p99_response_time_ms": 800,
                    "throughput_rps": 450,
                    "error_rate": 0.5,
                },
                "deployment": {
                    "last_deployment": "2026-01-03T18:30:00Z",
                    "deployment_frequency": "每天 2.5 次",
                    "deployment_success_rate": 98.5,
                    "mean_time_to_recovery_hours": 1.2,
                },
            }
        elif endpoint == "alerts":
            mock_data = {
                "active_alerts": 3,
                "alerts": [
                    {
                        "id": "alert-001",
                        "severity": "warning",
                        "title": "高内存使用率",
                        "description": "服务器内存使用率达到 85%",
                        "triggered_at": "2026-01-04T08:15:00Z",
                    },
                    {
                        "id": "alert-002",
                        "severity": "info",
                        "title": "API 响应时间增加",
                        "description": "API 平均响应时间从 120ms 增加到 180ms",
                        "triggered_at": "2026-01-04T07:30:00Z",
                    },
                    {
                        "id": "alert-003",
                        "severity": "critical",
                        "title": "数据库连接池耗尽",
                        "description": "数据库连接池使用率达到 95%",
                        "triggered_at": "2026-01-04T09:45:00Z",
                    },
                ],
            }
        else:
            mock_data = {
                "error": f"未知的 endpoint: {endpoint}",
                "available_endpoints": ["health", "metrics", "alerts"],
            }

        return mock_data
