"""DevOps Agent 核心实现

基于 LangChain 构建的智能 DevOps 分析 Agent。
"""

import uuid
from typing import List, Optional

from langchain_classic.agents import AgentExecutor, create_react_agent
from langchain_openai import ChatOpenAI

from src.agent.mongodb_memory import MongoDBConversationMemory
from src.agent.prompts import AGENT_PROMPT
from src.config import settings
from src.tools.artifactory import ArtifactoryTool
from src.tools.custom_backend import CustomBackendTool
from src.tools.gerrit import GerritTool
from src.tools.jenkins import JenkinsTool
from src.tools.test_cases import TestCasesTool
from src.tools.test_coverage import TestCoverageTool
from src.utils.logger import get_logger

logger = get_logger(__name__)


class DevOpsAgent:
    """DevOps 项目分析 Agent

    集成多种 DevOps 工具，提供智能项目分析能力。
    """

    def __init__(self):
        """初始化 Agent"""
        # 初始化 LLM (使用 Deepseek R1，兼容 OpenAI API)
        # 启用流式输出以实现实时响应
        self.llm = ChatOpenAI(
            model=settings.deepseek_model,
            api_key=settings.deepseek_api_key,
            base_url=settings.deepseek_base_url,
            temperature=0.7,
            max_tokens=2000,
            streaming=True,  # 🔥 关键：启用流式输出
        )

        # 初始化所有工具
        self.tools = [
            TestCoverageTool(),
            TestCasesTool(),
            GerritTool(),
            JenkinsTool(),
            ArtifactoryTool(),
            CustomBackendTool(),
        ]

        # 创建 Agent
        self.agent = create_react_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=AGENT_PROMPT,
        )

        logger.info("DevOps Agent 初始化完成")

    def create_executor(
        self, session_id: Optional[str] = None, max_iterations: int = 3
    ) -> tuple[AgentExecutor, str, MongoDBConversationMemory]:
        """创建 Agent 执行器

        Args:
            session_id: 会话 ID，如果为 None 则生成新的
            max_iterations: 最大迭代次数（默认 3 次，避免无限循环）

        Returns:
            tuple: (执行器, 会话ID, 记忆对象)
        """
        # 生成或使用现有 session_id
        if session_id is None:
            session_id = str(uuid.uuid4())

        # 创建 MongoDB 持久化记忆
        memory = MongoDBConversationMemory(session_id=session_id)

        # 创建执行器（不使用 memory 参数，因为与 ReAct agent 不兼容）
        executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            verbose=True,
            max_iterations=max_iterations,
            handle_parsing_errors=True,
        )

        logger.info(f"创建 Agent 执行器，会话 ID: {session_id}")
        return executor, session_id, memory

    def chat(self, message: str, session_id: Optional[str] = None) -> dict:
        """对话接口

        Args:
            message: 用户消息
            session_id: 会话 ID

        Returns:
            dict: 包含响应和会话 ID
        """
        logger.info(f"收到用户消息: {message}, 会话 ID: {session_id}")

        try:
            # 创建执行器
            executor, session_id, memory = self.create_executor(session_id)

            # 执行查询
            response = executor.invoke({"input": message})

            # 提取响应
            agent_response = response.get("output", "抱歉，我无法处理这个请求。")

            # 提取中间步骤（包含所有 Thought/Action/Observation）
            intermediate_steps = response.get("intermediate_steps", [])

            # 转换为 AgentStep 格式
            from src.models.mongodb_models import AgentStep
            agent_steps = []
            for i, (action, observation) in enumerate(intermediate_steps, 1):
                agent_steps.append(
                    AgentStep(
                        step_number=i,
                        thought=action.log,
                        action=action.tool,
                        action_input=action.tool_input if isinstance(action.tool_input, dict) else {"input": action.tool_input},
                        observation=observation,
                    )
                )

            # 保存对话（包含完整的执行步骤）
            memory.add_turn(
                user_input=message,
                final_response=agent_response,
                agent_steps=agent_steps,
            )

            logger.info(f"Agent 响应生成成功，会话 ID: {session_id}")

            return {
                "response": agent_response,
                "session_id": session_id,
                "success": True,
            }

        except Exception as e:
            logger.error(f"Agent 执行失败: {str(e)}")
            return {
                "response": f"抱歉，处理您的请求时出现错误: {str(e)}",
                "session_id": session_id,
                "success": False,
                "error": str(e),
            }

    def analyze_project(self, project_name: str) -> dict:
        """分析项目整体状况

        Args:
            project_name: 项目名称

        Returns:
            dict: 分析结果
        """
        analysis_prompt = f"""请对项目 "{project_name}" 进行全面分析，包括：

1. 测试覆盖率情况
2. 测试用例执行情况
3. 代码审查和合并情况 (Gerrit)
4. 构建状态 (Jenkins)
5. 制品版本情况 (Artifactory)
6. 其他关键指标

请提供一个综合性的项目健康报告。
"""

        return self.chat(analysis_prompt)

    def get_tool_list(self) -> List[dict]:
        """获取可用工具列表

        Returns:
            List[dict]: 工具列表
        """
        return [
            {
                "name": tool.name,
                "description": tool.description,
            }
            for tool in self.tools
        ]
