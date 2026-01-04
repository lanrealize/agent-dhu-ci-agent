"""测试覆盖率查询工具

查询项目的代码测试覆盖率信息。
"""

import json
from typing import Any, Dict

from src.config import settings
from src.tools.base import DevOpsBaseTool


class TestCoverageTool(DevOpsBaseTool):
    """测试覆盖率查询工具"""

    name: str = "test_coverage"
    description: str = """查询项目的测试覆盖率信息。

    使用方法: 输入项目名称，例如 "my-project"
    返回: 项目的总覆盖率和模块覆盖率详情
    """

    def _execute(self, query: str) -> Dict[str, Any]:
        """执行覆盖率查询

        Args:
            query: 项目名称

        Returns:
            Dict[str, Any]: 覆盖率数据
        """
        project_name = query.strip()

        # Mock 数据 - 实际应该调用自定义后端 API
        # async with HTTPClient(settings.custom_backend_url) as client:
        #     response = await client.get(f"/api/v1/coverage", params={"project": project_name})
        #     return response.json()

        mock_data = {
            "project": project_name,
            "total_coverage": 75.8,
            "line_coverage": 78.2,
            "branch_coverage": 72.5,
            "modules": [
                {
                    "name": "src/api",
                    "coverage": 85.3,
                    "lines_covered": 1024,
                    "lines_total": 1200,
                },
                {
                    "name": "src/agent",
                    "coverage": 82.1,
                    "lines_covered": 820,
                    "lines_total": 999,
                },
                {
                    "name": "src/tools",
                    "coverage": 68.5,
                    "lines_covered": 548,
                    "lines_total": 800,
                },
                {
                    "name": "src/models",
                    "coverage": 90.2,
                    "lines_covered": 361,
                    "lines_total": 400,
                },
            ],
            "trend": "上升",
            "last_updated": "2026-01-04T10:30:00Z",
        }

        return mock_data
