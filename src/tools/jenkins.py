"""Jenkins 查询工具

查询 Jenkins 构建状态和历史信息。
"""

from typing import Any, Dict

from src.config import settings
from src.tools.base import DevOpsBaseTool


class JenkinsTool(DevOpsBaseTool):
    """Jenkins 查询工具"""

    name: str = "jenkins"
    description: str = """查询 Jenkins 构建状态和历史信息。

    使用方法: 输入 Job 名称，例如 "my-project-build"
    返回: 构建状态、成功率、失败任务等信息
    """

    def _execute(self, query: str) -> Dict[str, Any]:
        """执行 Jenkins 查询

        Args:
            query: Job 名称

        Returns:
            Dict[str, Any]: Jenkins 构建数据
        """
        job_name = query.strip()

        # Mock 数据 - 实际应该调用 Jenkins REST API
        # Example: GET /job/{job_name}/api/json
        # async with HTTPClient(
        #     settings.jenkins_url,
        #     auth=(settings.jenkins_user, settings.jenkins_token)
        # ) as client:
        #     response = await client.get(f"/job/{job_name}/api/json")
        #     return response.json()

        mock_data = {
            "job_name": job_name,
            "last_build": {
                "number": 245,
                "status": "SUCCESS",
                "duration": 420000,  # ms
                "timestamp": "2026-01-04T09:30:00Z",
                "url": f"{settings.jenkins_url}/job/{job_name}/245/",
            },
            "summary": {
                "total_builds": 245,
                "success_count": 230,
                "failure_count": 12,
                "aborted_count": 3,
                "success_rate": 93.9,
            },
            "recent_builds": [
                {
                    "number": 245,
                    "status": "SUCCESS",
                    "duration": 420000,
                    "timestamp": "2026-01-04T09:30:00Z",
                },
                {
                    "number": 244,
                    "status": "SUCCESS",
                    "duration": 415000,
                    "timestamp": "2026-01-03T18:20:00Z",
                },
                {
                    "number": 243,
                    "status": "FAILURE",
                    "duration": 125000,
                    "timestamp": "2026-01-03T14:10:00Z",
                    "failure_reason": "Test failures: 3 tests failed",
                },
            ],
            "failed_builds": [
                {
                    "number": 243,
                    "timestamp": "2026-01-03T14:10:00Z",
                    "failure_reason": "Test failures: 3 tests failed",
                },
                {
                    "number": 238,
                    "timestamp": "2026-01-02T11:45:00Z",
                    "failure_reason": "Build timeout after 60 minutes",
                },
            ],
            "health_score": 95,
        }

        return mock_data
