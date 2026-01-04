"""测试 Tools 模块"""

import pytest

from src.tools.test_coverage import TestCoverageTool
from src.tools.test_cases import TestCasesTool


def test_test_coverage_tool():
    """测试测试覆盖率工具"""
    tool = TestCoverageTool()
    result = tool._run("test-project")

    # 验证返回的 JSON 可以解析
    import json
    data = json.loads(result)

    assert "project" in data
    assert data["project"] == "test-project"
    assert "total_coverage" in data
    assert isinstance(data["total_coverage"], (int, float))


def test_test_cases_tool():
    """测试测试用例工具"""
    tool = TestCasesTool()
    result = tool._run("test-project")

    # 验证返回的 JSON 可以解析
    import json
    data = json.loads(result)

    assert "project" in data
    assert data["project"] == "test-project"
    assert "total_cases" in data
    assert "passed" in data
    assert "failed" in data
