"""ESG评估API - ESG详细评估数据接口
提供ESG三维度详细评估数据、指标分析等
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime
from pydantic import BaseModel, Field

from app.core.response import APIResponse, create_response

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/esg", tags=["ESG Assessment"])


# ========== 请求/响应模型 ==========

class ESGIndicator(BaseModel):
    """ESG指标模型"""
    id: str = Field(..., description="指标ID")
    code: str = Field(..., description="指标代码")
    title: str = Field(..., description="指标标题")
    description: str = Field(..., description="指标描述")
    status: str = Field(..., description="指标状态", pattern="^(excellent|good|average|needs_improvement|not_assessed)$")
    score: Optional[float] = Field(None, description="指标得分")
    max_score: Optional[float] = Field(None, description="最高分")
    recommendation: Optional[str] = Field(None, description="改进建议")

class ESGSubCategory(BaseModel):
    """ESG子类别模型"""
    id: str = Field(..., description="子类别ID")
    code: str = Field(..., description="子类别代码")
    title: str = Field(..., description="子类别标题")
    description: str = Field(..., description="子类别描述")
    indicators: List[ESGIndicator] = Field(..., description="指标列表")
    average_score: Optional[float] = Field(None, description="平均得分")

class ESGCategory(BaseModel):
    """ESG类别模型"""
    id: str = Field(..., description="类别ID")
    code: str = Field(..., description="类别代码")
    title: str = Field(..., description="类别标题")
    description: str = Field(..., description="类别描述")
    color: str = Field(..., description="主题色")
    sub_categories: List[ESGSubCategory] = Field(..., description="子类别列表")
    overall_score: Optional[float] = Field(None, description="总体得分")

class ESGAssessmentData(BaseModel):
    """ESG评估数据模型"""
    categories: List[ESGCategory] = Field(..., description="ESG类别列表")
    overall_score: float = Field(..., description="总体评分")
    last_updated: datetime = Field(..., description="最后更新时间")
    assessment_id: Optional[str] = Field(None, description="评估ID")


# ========== API接口 ==========

@router.get("/assessment", response_model=APIResponse[ESGAssessmentData])
async def get_esg_assessment(
    company_id: Optional[str] = Query(None, description="企业ID"),
    assessment_id: Optional[str] = Query(None, description="评估ID")
) -> APIResponse[ESGAssessmentData]:
    """获取ESG详细评估数据"""
    try:
        logger.info(f"获取ESG评估数据，企业ID: {company_id}，评估ID: {assessment_id}")
        
        # 模拟环境维度数据
        environmental_category = ESGCategory(
            id="environmental",
            code="E",
            title="环境 Environmental",
            description="管理企业及上下游对环境的影响（产品/生产过程/运营消耗）",
            color="#10b981",
            overall_score=85.0,
            sub_categories=[
                ESGSubCategory(
                    id="e1",
                    code="E1",
                    title="碳排放",
                    description="能源消耗、低碳能源使用",
                    average_score=82.0,
                    indicators=[
                        ESGIndicator(
                            id="e1-1",
                            code="E1-1",
                            title="分析产品/运营碳排数据",
                            description="收集产品及企业运营过程中的碳排数据，设定减碳目标和举措，并做量效果",
                            status="good",
                            score=85.0,
                            max_score=100.0,
                            recommendation="建议建立完整的碳排放监测体系，定期更新数据"
                        ),
                        ESGIndicator(
                            id="e1-2",
                            code="E1-2",
                            title="提高能源效率或/和使用可再生能源",
                            description="以更低的能源消耗达成目标，在生产/和日常办公中提高可再生能源的使用比例",
                            status="average",
                            score=75.0,
                            max_score=100.0,
                            recommendation="考虑安装太阳能设备或采购绿色电力"
                        ),
                        ESGIndicator(
                            id="e1-3",
                            code="E1-3",
                            title="促进产业链上下游的低碳转型",
                            description="推出低碳产品；输出技术和资源推动产业链低碳转型",
                            status="needs_improvement",
                            score=60.0,
                            max_score=100.0,
                            recommendation="制定供应商低碳转型激励政策"
                        )
                    ]
                ),
                ESGSubCategory(
                    id="e2",
                    code="E2",
                    title="污染管理",
                    description="关注和减少企业生产运营中产生的各种污染",
                    average_score=88.0,
                    indicators=[
                        ESGIndicator(
                            id="e2-1",
                            code="E2-1",
                            title="管理废弃/有害/污染物",
                            description="最大程度减少排气/液/固体废物的产生，对无法避免的环境污染进行数据监测",
                            status="excellent",
                            score=92.0,
                            max_score=100.0
                        ),
                        ESGIndicator(
                            id="e2-2",
                            code="E2-2",
                            title="使用环境友好的采购标准",
                            description="在供应商的筛选评价标准中加入环境评价，与供应商合作优化供应链的负面环境影响",
                            status="good",
                            score=84.0,
                            max_score=100.0
                        )
                    ]
                ),
                ESGSubCategory(
                    id="e3",
                    code="E3",
                    title="资源利用",
                    description="消耗更少的自然资源，包含节约型，更耐用，可循环等",
                    average_score=79.0,
                    indicators=[
                        ESGIndicator(
                            id="e3-1",
                            code="E3-1",
                            title="节约用水，循环用水",
                            description="如在日常运营中实施节水措施；采用新技术减少生产用水的消耗；用新等",
                            status="good",
                            score=80.0,
                            max_score=100.0
                        ),
                        ESGIndicator(
                            id="e3-2",
                            code="E3-2",
                            title="优化原材料与包装使用",
                            description="如减少原材料采购总量；减少包装，减少塑料等材料；优化设计以提高资源利用率等",
                            status="average",
                            score=75.0,
                            max_score=100.0
                        ),
                        ESGIndicator(
                            id="e3-3",
                            code="E3-3",
                            title="生产及使用更耐用的产品",
                            description="如提升产品器械的选型/维修/保养，提升使用时间和打印机/灯泡等",
                            status="good",
                            score=82.0,
                            max_score=100.0
                        ),
                        ESGIndicator(
                            id="e3-4",
                            code="E3-4",
                            title="利用可回收/可再生资源",
                            description="如以回收/再生材料作为生产原材料，办公环境中使用的材料等",
                            status="average",
                            score=78.0,
                            max_score=100.0
                        ),
                        ESGIndicator(
                            id="e3-5",
                            code="E3-5",
                            title="负责任回收及召回产品",
                            description="回收含有毒有害的产品，召回存在问题的产品，处理或再利用产品",
                            status="needs_improvement",
                            score=65.0,
                            max_score=100.0
                        )
                    ]
                )
            ]
        )
        
        # 模拟社会维度数据
        social_category = ESGCategory(
            id="social",
            code="S",
            title="社会 Social",
            description="管理企业运营过程中对各类利益相关方的影响",
            color="#f97316",
            overall_score=78.0,
            sub_categories=[
                ESGSubCategory(
                    id="s1",
                    code="S1",
                    title="产品与客户",
                    description="为客户提供更好，性价比更高的产品/服务",
                    average_score=85.0,
                    indicators=[
                        ESGIndicator(
                            id="s1-1",
                            code="S1-1",
                            title="保护客户的隐私和数据安全",
                            description="采用有效措施技术，避免客户隐私和数据泄露不正当使用或滥用；建立设备处理机制",
                            status="excellent",
                            score=95.0,
                            max_score=100.0
                        ),
                        ESGIndicator(
                            id="s1-2",
                            code="S1-2",
                            title="提升产品的质量和安全性",
                            description="保证产品质量与安全能持续稳定地达标；采用更高标准提升供应或服务",
                            status="good",
                            score=88.0,
                            max_score=100.0
                        ),
                        ESGIndicator(
                            id="s1-3",
                            code="S1-3",
                            title="提供充分的产品信息",
                            description="确保客户了解产品的正确使用和处置信息；对抗虚假信息保持透明，说明其环境/社会影响等",
                            status="good",
                            score=82.0,
                            max_score=100.0
                        ),
                        ESGIndicator(
                            id="s1-4",
                            code="S1-4",
                            title="提供性价比更高的产品/服务",
                            description="以更能负担的价格向客户提供良好的产品/服务",
                            status="average",
                            score=75.0,
                            max_score=100.0
                        )
                    ]
                )
            ]
        )
        
        # 模拟治理维度数据
        governance_category = ESGCategory(
            id="governance",
            code="G",
            title="治理 Governance",
            description="管理企业内部治理结构、决策流程和合规体系",
            color="#6366f1",
            overall_score=88.0,
            sub_categories=[
                ESGSubCategory(
                    id="g1",
                    code="G1",
                    title="公司治理",
                    description="建立健全的公司治理结构和决策机制",
                    average_score=88.0,
                    indicators=[
                        ESGIndicator(
                            id="g1-1",
                            code="G1-1",
                            title="董事会独立性",
                            description="确保董事会具有足够的独立性和多样性",
                            status="good",
                            score=85.0,
                            max_score=100.0
                        ),
                        ESGIndicator(
                            id="g1-2",
                            code="G1-2",
                            title="透明度和信息披露",
                            description="及时、准确、完整地披露重要信息",
                            status="excellent",
                            score=92.0,
                            max_score=100.0
                        ),
                        ESGIndicator(
                            id="g1-3",
                            code="G1-3",
                            title="风险管理体系",
                            description="建立完善的风险识别、评估和控制机制",
                            status="good",
                            score=87.0,
                            max_score=100.0
                        )
                    ]
                )
            ]
        )
        
        # 构建完整的ESG评估数据
        esg_data = ESGAssessmentData(
            categories=[environmental_category, social_category, governance_category],
            overall_score=83.7,  # 三个维度的加权平均
            last_updated=datetime.now(),
            assessment_id=assessment_id or "default_assessment"
        )
        
        return create_response(
            data=esg_data,
            message="ESG评估数据获取成功"
        )
        
    except Exception as e:
        logger.error(f"获取ESG评估数据失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"获取ESG评估数据失败: {str(e)}"
        )


@router.get("/categories", response_model=APIResponse[List[ESGCategory]])
async def get_esg_categories(
    company_id: Optional[str] = Query(None, description="企业ID")
) -> APIResponse[List[ESGCategory]]:
    """获取ESG类别列表"""
    try:
        logger.info(f"获取ESG类别列表，企业ID: {company_id}")
        
        # 调用完整评估数据接口获取类别
        assessment_response = await get_esg_assessment(company_id=company_id)
        categories = assessment_response.data.categories
        
        return create_response(
            data=categories,
            message="ESG类别列表获取成功"
        )
        
    except Exception as e:
        logger.error(f"获取ESG类别列表失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"获取ESG类别列表失败: {str(e)}"
        )


@router.get("/indicators/{indicator_id}", response_model=APIResponse[ESGIndicator])
async def get_esg_indicator(
    indicator_id: str,
    company_id: Optional[str] = Query(None, description="企业ID")
) -> APIResponse[ESGIndicator]:
    """获取特定ESG指标详情"""
    try:
        logger.info(f"获取ESG指标详情，指标ID: {indicator_id}，企业ID: {company_id}")
        
        # 获取完整评估数据
        assessment_response = await get_esg_assessment(company_id=company_id)
        
        # 查找指定指标
        for category in assessment_response.data.categories:
            for sub_category in category.sub_categories:
                for indicator in sub_category.indicators:
                    if indicator.id == indicator_id:
                        return create_response(
                            data=indicator,
                            message="ESG指标详情获取成功"
                        )
        
        raise HTTPException(
            status_code=404,
            detail=f"未找到指标ID: {indicator_id}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取ESG指标详情失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"获取ESG指标详情失败: {str(e)}"
        )


@router.get("/summary", response_model=APIResponse[Dict[str, Any]])
async def get_esg_summary(
    company_id: Optional[str] = Query(None, description="企业ID")
) -> APIResponse[Dict[str, Any]]:
    """获取ESG评估摘要"""
    try:
        logger.info(f"获取ESG评估摘要，企业ID: {company_id}")
        
        # 获取完整评估数据
        assessment_response = await get_esg_assessment(company_id=company_id)
        assessment_data = assessment_response.data
        
        # 计算摘要统计
        total_indicators = sum(
            len(sub_cat.indicators) 
            for cat in assessment_data.categories 
            for sub_cat in cat.sub_categories
        )
        
        status_counts = {
            "excellent": 0,
            "good": 0,
            "average": 0,
            "needs_improvement": 0,
            "not_assessed": 0
        }
        
        for category in assessment_data.categories:
            for sub_category in category.sub_categories:
                for indicator in sub_category.indicators:
                    status_counts[indicator.status] += 1
        
        summary = {
            "overall_score": assessment_data.overall_score,
            "total_indicators": total_indicators,
            "category_scores": {
                cat.code: cat.overall_score 
                for cat in assessment_data.categories
            },
            "status_distribution": status_counts,
            "last_updated": assessment_data.last_updated,
            "assessment_id": assessment_data.assessment_id
        }
        
        return create_response(
            data=summary,
            message="ESG评估摘要获取成功"
        )
        
    except Exception as e:
        logger.error(f"获取ESG评估摘要失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"获取ESG评估摘要失败: {str(e)}"
        )