"""HTTP 客户端封装模块

封装 httpx 客户端，提供统一的 HTTP 请求接口和错误处理。
"""

from typing import Any, Dict, Optional

import httpx
from httpx import AsyncClient, Response

from src.utils.logger import get_logger

logger = get_logger(__name__)


class HTTPClient:
    """异步 HTTP 客户端封装类"""

    def __init__(
        self,
        base_url: str,
        headers: Optional[Dict[str, str]] = None,
        timeout: float = 30.0,
        auth: Optional[tuple] = None,
    ):
        """初始化 HTTP 客户端

        Args:
            base_url: 基础 URL
            headers: 默认请求头
            timeout: 请求超时时间（秒）
            auth: 基础认证元组 (username, password)
        """
        self.base_url = base_url
        self.headers = headers or {}
        self.timeout = timeout
        self.auth = auth
        self._client: Optional[AsyncClient] = None

    async def __aenter__(self) -> "HTTPClient":
        """异步上下文管理器入口"""
        self._client = AsyncClient(
            base_url=self.base_url,
            headers=self.headers,
            timeout=self.timeout,
            auth=self.auth,
        )
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """异步上下文管理器出口"""
        if self._client:
            await self._client.aclose()

    async def get(
        self,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Response:
        """发送 GET 请求

        Args:
            path: 请求路径
            params: 查询参数
            headers: 额外的请求头

        Returns:
            Response: HTTP 响应对象

        Raises:
            httpx.HTTPError: HTTP 错误
        """
        if not self._client:
            raise RuntimeError("客户端未初始化，请使用 async with 语句")

        try:
            logger.debug(f"GET {path}, params={params}")
            response = await self._client.get(path, params=params, headers=headers)
            response.raise_for_status()
            return response
        except httpx.HTTPError as e:
            logger.error(f"GET 请求失败: {path}, 错误: {str(e)}")
            raise

    async def post(
        self,
        path: str,
        json: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Response:
        """发送 POST 请求

        Args:
            path: 请求路径
            json: JSON 数据
            data: 表单数据
            headers: 额外的请求头

        Returns:
            Response: HTTP 响应对象

        Raises:
            httpx.HTTPError: HTTP 错误
        """
        if not self._client:
            raise RuntimeError("客户端未初始化，请使用 async with 语句")

        try:
            logger.debug(f"POST {path}, json={json}, data={data}")
            response = await self._client.post(
                path, json=json, data=data, headers=headers
            )
            response.raise_for_status()
            return response
        except httpx.HTTPError as e:
            logger.error(f"POST 请求失败: {path}, 错误: {str(e)}")
            raise

    async def put(
        self,
        path: str,
        json: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Response:
        """发送 PUT 请求

        Args:
            path: 请求路径
            json: JSON 数据
            data: 表单数据
            headers: 额外的请求头

        Returns:
            Response: HTTP 响应对象

        Raises:
            httpx.HTTPError: HTTP 错误
        """
        if not self._client:
            raise RuntimeError("客户端未初始化，请使用 async with 语句")

        try:
            logger.debug(f"PUT {path}, json={json}, data={data}")
            response = await self._client.put(
                path, json=json, data=data, headers=headers
            )
            response.raise_for_status()
            return response
        except httpx.HTTPError as e:
            logger.error(f"PUT 请求失败: {path}, 错误: {str(e)}")
            raise

    async def delete(
        self,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Response:
        """发送 DELETE 请求

        Args:
            path: 请求路径
            params: 查询参数
            headers: 额外的请求头

        Returns:
            Response: HTTP 响应对象

        Raises:
            httpx.HTTPError: HTTP 错误
        """
        if not self._client:
            raise RuntimeError("客户端未初始化，请使用 async with 语句")

        try:
            logger.debug(f"DELETE {path}, params={params}")
            response = await self._client.delete(path, params=params, headers=headers)
            response.raise_for_status()
            return response
        except httpx.HTTPError as e:
            logger.error(f"DELETE 请求失败: {path}, 错误: {str(e)}")
            raise
