"""测试用例查询工具

查询项目的测试用例执行情况。
"""

from typing import Any, Dict

from src.config import settings
from src.tools.base import DevOpsBaseTool


class TestCasesTool(DevOpsBaseTool):
    """测试用例查询工具"""

    name: str = "test_cases"
    description: str = """查询项目的测试用例执行情况。

    使用方法: 输入项目名称，例如 "my-project"
    返回: 测试用例通过率、失败用例列表等信息
    """

    def _execute(self, query: str) -> Dict[str, Any]:
        """执行测试用例查询

        Args:
            query: 项目名称

        Returns:
            Dict[str, Any]: 测试用例数据
        """
        project_name = query.strip()

        # Mock 数据 - 实际应该调用自定义后端 API
        # async with HTTPClient(settings.custom_backend_url) as client:
        #     response = await client.get(f"/api/v1/test-cases", params={"project": project_name})
        #     return response.json()

        mock_data = {
            "project": project_name,
            "total_cases": 856,
            "passed": 821,
            "failed": 15,
            "skipped": 20,
            "pass_rate": 95.9,
            "failed_cases": [
                {
                    "name": "test_api_endpoint_validation",
                    "module": "tests.test_api.test_routes",
                    "error": "AssertionError: Expected 200, got 404",
                    "duration": 0.35,
                },
                {
                    "name": "test_agent_tool_execution",
                    "module": "tests.test_agent.test_executor",
                    "error": "TimeoutError: Tool execution timeout after 30s",
                    "duration": 30.0,
                },
                {
                    "name": "test_database_connection",
                    "module": "tests.test_models.test_db",
                    "error": "ConnectionError: Database connection refused",
                    "duration": 5.2,
                },
            ],
            "duration": 245.6,
            "last_run": "2026-01-04T09:15:00Z",
        }

        return mock_data
