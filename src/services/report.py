"""报告生成服务

提供报告生成的业务逻辑。
"""

from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from src.models.orm import Report
from src.utils.logger import get_logger

logger = get_logger(__name__)


class ReportService:
    """报告生成服务类"""

    def __init__(self, db: Session):
        """初始化服务

        Args:
            db: 数据库会话
        """
        self.db = db

    def save_report(
        self,
        project_name: str,
        report_type: str,
        content: str,
        summary: Optional[str] = None,
    ) -> Report:
        """保存报告

        Args:
            project_name: 项目名称
            report_type: 报告类型
            content: 报告内容
            summary: 报告摘要

        Returns:
            Report: 保存的报告
        """
        try:
            report = Report(
                project_name=project_name,
                report_type=report_type,
                content=content,
                summary=summary or self._generate_summary(content),
            )
            self.db.add(report)
            self.db.commit()
            self.db.refresh(report)

            logger.info(
                f"保存报告成功: 项目={project_name}, 类型={report_type}, ID={report.id}"
            )
            return report

        except Exception as e:
            logger.error(f"保存报告失败: {str(e)}")
            self.db.rollback()
            raise

    def get_report(self, report_id: int) -> Optional[Report]:
        """获取报告

        Args:
            report_id: 报告 ID

        Returns:
            Optional[Report]: 报告对象，不存在则返回 None
        """
        return self.db.query(Report).filter(Report.id == report_id).first()

    def get_latest_report(
        self, project_name: str, report_type: Optional[str] = None
    ) -> Optional[Report]:
        """获取最新报告

        Args:
            project_name: 项目名称
            report_type: 报告类型，为 None 则获取所有类型中最新的

        Returns:
            Optional[Report]: 报告对象，不存在则返回 None
        """
        query = self.db.query(Report).filter(Report.project_name == project_name)

        if report_type:
            query = query.filter(Report.report_type == report_type)

        return query.order_by(Report.created_at.desc()).first()

    def _generate_summary(self, content: str, max_length: int = 200) -> str:
        """生成报告摘要

        Args:
            content: 报告内容
            max_length: 最大长度

        Returns:
            str: 摘要
        """
        # 简单实现：取前 max_length 个字符
        # 实际可以使用 LLM 生成更智能的摘要
        if len(content) <= max_length:
            return content

        return content[:max_length] + "..."
