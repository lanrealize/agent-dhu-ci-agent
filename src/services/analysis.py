"""项目分析服务

提供项目分析的业务逻辑。
"""

from datetime import datetime
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from src.models.orm import AnalysisRecord
from src.utils.logger import get_logger

logger = get_logger(__name__)


class AnalysisService:
    """项目分析服务类"""

    def __init__(self, db: Session):
        """初始化服务

        Args:
            db: 数据库会话
        """
        self.db = db

    def save_analysis_record(
        self,
        project_name: str,
        metric_type: str,
        metric_value: float,
        metric_data: Optional[str] = None,
    ) -> AnalysisRecord:
        """保存分析记录

        Args:
            project_name: 项目名称
            metric_type: 指标类型
            metric_value: 指标值
            metric_data: 指标详细数据 (JSON 字符串)

        Returns:
            AnalysisRecord: 保存的记录
        """
        try:
            record = AnalysisRecord(
                project_name=project_name,
                metric_type=metric_type,
                metric_value=metric_value,
                metric_data=metric_data,
            )
            self.db.add(record)
            self.db.commit()
            self.db.refresh(record)

            logger.info(
                f"保存分析记录成功: 项目={project_name}, 指标={metric_type}, 值={metric_value}"
            )
            return record

        except Exception as e:
            logger.error(f"保存分析记录失败: {str(e)}")
            self.db.rollback()
            raise

    def get_latest_metrics(
        self, project_name: str, metric_types: Optional[List[str]] = None
    ) -> Dict[str, float]:
        """获取最新的指标数据

        Args:
            project_name: 项目名称
            metric_types: 指标类型列表，为 None 则获取所有类型

        Returns:
            Dict[str, float]: 指标类型到值的映射
        """
        query = self.db.query(AnalysisRecord).filter(
            AnalysisRecord.project_name == project_name
        )

        if metric_types:
            query = query.filter(AnalysisRecord.metric_type.in_(metric_types))

        # 获取每个指标类型的最新记录
        metrics = {}
        for metric_type in metric_types or []:
            record = (
                query.filter(AnalysisRecord.metric_type == metric_type)
                .order_by(AnalysisRecord.timestamp.desc())
                .first()
            )
            if record:
                metrics[metric_type] = record.metric_value

        return metrics

    def calculate_trend(
        self, project_name: str, metric_type: str, days: int = 30
    ) -> Dict:
        """计算指标趋势

        Args:
            project_name: 项目名称
            metric_type: 指标类型
            days: 天数

        Returns:
            Dict: 趋势数据
        """
        from datetime import timedelta

        start_date = datetime.now() - timedelta(days=days)

        records = (
            self.db.query(AnalysisRecord)
            .filter(
                AnalysisRecord.project_name == project_name,
                AnalysisRecord.metric_type == metric_type,
                AnalysisRecord.timestamp >= start_date,
            )
            .order_by(AnalysisRecord.timestamp)
            .all()
        )

        if not records:
            return {"trend": "no_data", "change_percent": 0, "data_points": []}

        # 计算变化百分比
        first_value = records[0].metric_value
        last_value = records[-1].metric_value
        change_percent = (
            ((last_value - first_value) / first_value * 100) if first_value != 0 else 0
        )

        # 判断趋势
        if change_percent > 5:
            trend = "上升"
        elif change_percent < -5:
            trend = "下降"
        else:
            trend = "稳定"

        return {
            "trend": trend,
            "change_percent": round(change_percent, 2),
            "first_value": first_value,
            "last_value": last_value,
            "data_points": len(records),
        }
