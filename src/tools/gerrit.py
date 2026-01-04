"""Gerrit 查询工具

查询 Gerrit 代码审查和 Patchset 信息。
"""

from typing import Any, Dict

from src.config import settings
from src.tools.base import DevOpsBaseTool


class GerritTool(DevOpsBaseTool):
    """Gerrit 查询工具"""

    name: str = "gerrit"
    description: str = """查询 Gerrit 代码审查和 Patchset 合并情况。

    使用方法: 输入项目名称，例如 "my-project"
    返回: Patchset 合并统计、待审核列表等信息
    """

    def _execute(self, query: str) -> Dict[str, Any]:
        """执行 Gerrit 查询

        Args:
            query: 项目名称或查询参数

        Returns:
            Dict[str, Any]: Gerrit 数据
        """
        project_name = query.strip()

        # Mock 数据 - 实际应该调用 Gerrit REST API
        # Example: GET /changes/?q=project:{project_name}+status:open
        # import base64
        # auth = base64.b64encode(f"{settings.gerrit_user}:{settings.gerrit_password}".encode()).decode()
        # async with HTTPClient(settings.gerrit_url, headers={"Authorization": f"Basic {auth}"}) as client:
        #     response = await client.get(f"/changes/", params={"q": f"project:{project_name}"})
        #     return response.json()

        mock_data = {
            "project": project_name,
            "summary": {
                "merged_this_week": 23,
                "merged_this_month": 89,
                "open_changes": 12,
                "pending_review": 8,
                "average_merge_time_hours": 18.5,
            },
            "open_changes": [
                {
                    "change_id": "I1234567890abcdef",
                    "subject": "Fix: Resolve database connection timeout issue",
                    "owner": "developer@example.com",
                    "status": "NEW",
                    "created": "2026-01-03T14:20:00Z",
                    "updated": "2026-01-04T08:45:00Z",
                    "reviewers": ["reviewer1@example.com", "reviewer2@example.com"],
                    "code_review_score": "+1",
                },
                {
                    "change_id": "Iabcdef1234567890",
                    "subject": "Feature: Add new API endpoint for metrics",
                    "owner": "developer2@example.com",
                    "status": "NEW",
                    "created": "2026-01-02T10:15:00Z",
                    "updated": "2026-01-03T16:30:00Z",
                    "reviewers": ["reviewer1@example.com"],
                    "code_review_score": "0",
                },
            ],
            "recent_merged": [
                {
                    "change_id": "Ixyz123",
                    "subject": "Refactor: Improve tool execution performance",
                    "owner": "developer3@example.com",
                    "merged": "2026-01-03T22:10:00Z",
                },
            ],
        }

        return mock_data
