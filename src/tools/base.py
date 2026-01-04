"""Base Tool 类

所有 DevOps Tools 的基类，提供通用功能。
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from langchain_core.tools import BaseTool as LangChainBaseTool
from langchain_core.callbacks.manager import CallbackManagerForToolRun
from pydantic import BaseModel

from src.utils.http_client import HTTPClient
from src.utils.logger import get_logger

logger = get_logger(__name__)


class DevOpsBaseTool(LangChainBaseTool, ABC):
    """DevOps 工具基类

    继承自 LangChain 的 BaseTool，提供通用的功能和接口。
    """

    # Tool 元数据
    name: str
    description: str

    def _run(
        self,
        query: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """同步执行工具

        Args:
            query: 查询参数
            run_manager: 回调管理器

        Returns:
            str: 执行结果
        """
        logger.info(f"执行工具: {self.name}, 查询: {query}")
        try:
            result = self._execute(query)
            logger.info(f"工具 {self.name} 执行成功")
            return self._format_result(result)
        except Exception as e:
            logger.error(f"工具 {self.name} 执行失败: {str(e)}")
            return self._format_error(str(e))

    @abstractmethod
    def _execute(self, query: str) -> Dict[str, Any]:
        """执行具体的工具逻辑

        子类必须实现此方法。

        Args:
            query: 查询参数

        Returns:
            Dict[str, Any]: 执行结果字典
        """
        pass

    def _format_result(self, result: Dict[str, Any]) -> str:
        """格式化成功结果

        Args:
            result: 结果字典

        Returns:
            str: 格式化后的字符串
        """
        import json

        return json.dumps(result, ensure_ascii=False, indent=2)

    def _format_error(self, error: str) -> str:
        """格式化错误信息

        Args:
            error: 错误信息

        Returns:
            str: 格式化后的错误字符串
        """
        return f"错误: {error}"

    async def _async_run(
        self,
        query: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """异步执行工具

        Args:
            query: 查询参数
            run_manager: 回调管理器

        Returns:
            str: 执行结果
        """
        # 默认调用同步方法
        return self._run(query, run_manager)
