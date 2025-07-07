"""Dashboard API - ESG仪表板数据接口
提供ESG评分、关键指标、系统状态等数据
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime, timedelta
from pydantic import BaseModel, Field

from app.core.response import APIResponse, create_response

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


# ========== 请求/响应模型 ==========

class ESGScore(BaseModel):
    """ESG评分模型"""
    overall: float = Field(..., description="综合评分")
    environmental: float = Field(..., description="环境评分")
    social: float = Field(..., description="社会评分")
    governance: float = Field(..., description="治理评分")
    last_updated: datetime = Field(..., description="最后更新时间")

class MetricCard(BaseModel):
    """指标卡片模型"""
    title: str = Field(..., description="指标标题")
    value: str = Field(..., description="指标值")
    change: Optional[str] = Field(None, description="变化值")
    trend: Optional[str] = Field(None, description="趋势方向", pattern="^(up|down|stable)$")
    value_change: Optional[str] = Field(None, description="数值变化")
    color: str = Field(..., description="颜色主题", pattern="^(green|yellow|blue|red)$")

class SystemStatus(BaseModel):
    """系统状态模型"""
    service_name: str = Field(..., description="服务名称")
    status: str = Field(..., description="状态", pattern="^(healthy|warning|error)$")
    response_time: Optional[float] = Field(None, description="响应时间(ms)")
    last_check: datetime = Field(..., description="最后检查时间")
    details: Optional[str] = Field(None, description="详细信息")

class RecentActivity(BaseModel):
    """最近活动模型"""
    id: str = Field(..., description="活动ID")
    type: str = Field(..., description="活动类型")
    title: str = Field(..., description="活动标题")
    description: str = Field(..., description="活动描述")
    timestamp: datetime = Field(..., description="时间戳")
    status: str = Field(..., description="状态")
    icon: str = Field(..., description="图标")

class DashboardData(BaseModel):
    """仪表板数据模型"""
    esg_scores: ESGScore = Field(..., description="ESG评分")
    key_metrics: List[MetricCard] = Field(..., description="关键指标")
    system_status: List[SystemStatus] = Field(..., description="系统状态")
    recent_activities: List[RecentActivity] = Field(..., description="最近活动")
    last_updated: datetime = Field(..., description="数据最后更新时间")


# ========== API接口 ==========

@router.get("/overview", response_model=APIResponse[DashboardData])
async def get_dashboard_overview(
    company_id: Optional[str] = Query(None, description="企业ID")
) -> APIResponse[DashboardData]:
    """获取仪表板概览数据"""
    try:
        logger.info(f"获取仪表板数据，企业ID: {company_id}")
        
        # 模拟ESG评分数据（后续可从数据库获取）
        esg_scores = ESGScore(
            overall=85.0,
            environmental=87.0,
            social=82.0,
            governance=88.0,
            last_updated=datetime.now()
        )
        
        # 模拟关键指标数据
        key_metrics = [
            MetricCard(
                title="ESG综合评分",
                value="85",
                change="+5分",
                trend="up",
                icon="🎯",
                color="green"
            ),
            MetricCard(
                title="环境表现",
                value="A-",
                change="提升1级",
                trend="up",
                icon="🌱",
                color="green"
            ),
            MetricCard(
                title="社会责任",
                value="82",
                change="+3分",
                trend="up",
                icon="👥",
                color="blue"
            ),
            MetricCard(
                title="公司治理",
                value="88",
                change="持平",
                trend="stable",
                icon="⚖️",
                color="yellow"
            ),
            MetricCard(
                title="风险等级",
                value="中低",
                change="降低",
                trend="up",
                icon="🛡️",
                color="green"
            ),
            MetricCard(
                title="合规状态",
                value="100%",
                change="满分",
                trend="stable",
                icon="✅",
                color="green"
            )
        ]
        
        # 模拟系统状态数据
        system_status = [
            SystemStatus(
                service_name="AI Agent服务",
                status="healthy",
                response_time=150.0,
                last_check=datetime.now(),
                details="正常运行"
            ),
            SystemStatus(
                service_name="数据库连接",
                status="healthy",
                response_time=50.0,
                last_check=datetime.now(),
                details="连接正常"
            ),
            SystemStatus(
                service_name="API响应时间",
                status="healthy",
                response_time=180.0,
                last_check=datetime.now(),
                details="< 200ms"
            )
        ]
        
        # 模拟最近活动数据
        recent_activities = [
            RecentActivity(
                id="activity_1",
                type="profile_generation",
                title="企业画像生成",
                description="已完成基础信息收集，正在进行ESG风险评估...",
                timestamp=datetime.now() - timedelta(hours=2),
                status="in_progress",
                icon="🤖"
            ),
            RecentActivity(
                id="activity_2",
                type="report_analysis",
                title="ESG报告分析",
                description="环境指标表现良好，建议加强社会责任投入...",
                timestamp=datetime.now() - timedelta(days=1),
                status="completed",
                icon="📊"
            )
        ]
        
        dashboard_data = DashboardData(
            esg_scores=esg_scores,
            key_metrics=key_metrics,
            system_status=system_status,
            recent_activities=recent_activities,
            last_updated=datetime.now()
        )
        
        return create_response(
            data=dashboard_data,
            message="仪表板数据获取成功"
        )
        
    except Exception as e:
        logger.error(f"获取仪表板数据失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"获取仪表板数据失败: {str(e)}"
        )


@router.get("/esg-scores", response_model=APIResponse[ESGScore])
async def get_esg_scores(
    company_id: Optional[str] = Query(None, description="企业ID")
) -> APIResponse[ESGScore]:
    """获取ESG评分数据"""
    try:
        logger.info(f"获取ESG评分，企业ID: {company_id}")
        
        # 模拟ESG评分数据（后续可从数据库获取）
        esg_scores = ESGScore(
            overall=85.0,
            environmental=87.0,
            social=82.0,
            governance=88.0,
            last_updated=datetime.now()
        )
        
        return create_response(
            data=esg_scores,
            message="ESG评分获取成功"
        )
        
    except Exception as e:
        logger.error(f"获取ESG评分失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"获取ESG评分失败: {str(e)}"
        )


@router.get("/metrics", response_model=APIResponse[List[MetricCard]])
async def get_key_metrics(
    company_id: Optional[str] = Query(None, description="企业ID")
) -> APIResponse[List[MetricCard]]:
    """获取关键指标数据"""
    try:
        logger.info(f"获取关键指标，企业ID: {company_id}")
        
        # 模拟关键指标数据
        metrics = [
            MetricCard(
                title="ESG综合评分",
                value="85",
                change="+5分",
                trend="up",
                icon="🎯",
                color="green"
            ),
            MetricCard(
                title="环境表现",
                value="A-",
                change="提升1级",
                trend="up",
                icon="🌱",
                color="green"
            ),
            MetricCard(
                title="社会责任",
                value="82",
                change="+3分",
                trend="up",
                icon="👥",
                color="blue"
            ),
            MetricCard(
                title="公司治理",
                value="88",
                change="持平",
                trend="stable",
                icon="⚖️",
                color="yellow"
            ),
            MetricCard(
                title="风险等级",
                value="中低",
                change="降低",
                trend="up",
                icon="🛡️",
                color="green"
            ),
            MetricCard(
                title="合规状态",
                value="100%",
                change="满分",
                trend="stable",
                icon="✅",
                color="green"
            )
        ]
        
        return create_response(
            data=metrics,
            message="关键指标获取成功"
        )
        
    except Exception as e:
        logger.error(f"获取关键指标失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"获取关键指标失败: {str(e)}"
        )


@router.get("/system-status", response_model=APIResponse[List[SystemStatus]])
async def get_system_status() -> APIResponse[List[SystemStatus]]:
    """获取系统状态"""
    try:
        logger.info("获取系统状态")
        
        # 模拟系统状态数据
        status_list = [
            SystemStatus(
                service_name="AI Agent服务",
                status="healthy",
                response_time=150.0,
                last_check=datetime.now(),
                details="正常运行"
            ),
            SystemStatus(
                service_name="数据库连接",
                status="healthy",
                response_time=50.0,
                last_check=datetime.now(),
                details="连接正常"
            ),
            SystemStatus(
                service_name="API响应时间",
                status="healthy",
                response_time=180.0,
                last_check=datetime.now(),
                details="< 200ms"
            ),
            SystemStatus(
                service_name="向量数据库",
                status="healthy",
                response_time=120.0,
                last_check=datetime.now(),
                details="ChromaDB正常"
            )
        ]
        
        return create_response(
            data=status_list,
            message="系统状态获取成功"
        )
        
    except Exception as e:
        logger.error(f"获取系统状态失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"获取系统状态失败: {str(e)}"
        )


@router.get("/activities", response_model=APIResponse[List[RecentActivity]])
async def get_recent_activities(
    limit: int = Query(10, description="返回数量限制"),
    company_id: Optional[str] = Query(None, description="企业ID")
) -> APIResponse[List[RecentActivity]]:
    """获取最近活动"""
    try:
        logger.info(f"获取最近活动，限制: {limit}，企业ID: {company_id}")
        
        # 模拟最近活动数据
        activities = [
            RecentActivity(
                id="activity_1",
                type="profile_generation",
                title="企业画像生成",
                description="已完成基础信息收集，正在进行ESG风险评估...",
                timestamp=datetime.now() - timedelta(hours=2),
                status="in_progress",
                icon="🤖"
            ),
            RecentActivity(
                id="activity_2",
                type="report_analysis",
                title="ESG报告分析",
                description="环境指标表现良好，建议加强社会责任投入...",
                timestamp=datetime.now() - timedelta(days=1),
                status="completed",
                icon="📊"
            ),
            RecentActivity(
                id="activity_3",
                type="compliance_check",
                title="合规性检查",
                description="完成GRI标准合规性检查，发现3个改进点...",
                timestamp=datetime.now() - timedelta(days=2),
                status="completed",
                icon="✅"
            ),
            RecentActivity(
                id="activity_4",
                type="risk_assessment",
                title="风险评估",
                description="识别出2个高风险项目，已生成改进建议...",
                timestamp=datetime.now() - timedelta(days=3),
                status="completed",
                icon="⚠️"
            )
        ]
        
        # 应用限制
        limited_activities = activities[:limit]
        
        return create_response(
            data=limited_activities,
            message="最近活动获取成功"
        )
        
    except Exception as e:
        logger.error(f"获取最近活动失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"获取最近活动失败: {str(e)}"
        )