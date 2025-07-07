"""
信息提取API - 文档分析、关键信息提取和摘要生成接口
支持智能文档分析和结构化信息输出
"""

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime

from app.services.extraction_service import get_extraction_service, InformationExtractionService
from app.core.response import APIResponse, create_response
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/extraction", tags=["Information Extraction"])


# ========== 请求/响应模型 ==========

class ExtractionRequest(BaseModel):
    """信息提取请求模型"""
    document_id: str = Field(..., description="文档ID")
    user_id: str = Field(..., description="用户ID")
    extraction_types: List[str] = Field(
        ["summary", "entities", "keywords", "key_info"], 
        description="提取类型列表"
    )


class BatchExtractionRequest(BaseModel):
    """批量信息提取请求模型"""
    document_ids: List[str] = Field(..., description="文档ID列表", max_items=10)
    user_id: str = Field(..., description="用户ID")
    extraction_types: List[str] = Field(
        ["summary", "entities", "keywords"], 
        description="提取类型列表"
    )


class DocumentSummaryResponse(BaseModel):
    """文档摘要响应模型"""
    title: str = Field(..., description="文档标题")
    brief_summary: str = Field(..., description="简要摘要")
    detailed_summary: str = Field(..., description="详细摘要")
    key_points: List[str] = Field(..., description="关键要点")
    structure_summary: str = Field(..., description="结构性摘要")
    confidence: float = Field(..., description="摘要质量置信度", ge=0, le=1)


class ExtractedEntityResponse(BaseModel):
    """提取实体响应模型"""
    text: str = Field(..., description="实体文本")
    type: str = Field(..., description="实体类型")
    confidence: float = Field(..., description="置信度", ge=0, le=1)
    context: str = Field(..., description="上下文")
    position: int = Field(..., description="在文档中的位置")


class KeyInformationResponse(BaseModel):
    """关键信息响应模型"""
    content: str = Field(..., description="信息内容")
    importance: float = Field(..., description="重要性评分", ge=0, le=1)
    category: str = Field(..., description="信息类别")
    keywords: List[str] = Field(..., description="关键词")
    source_section: str = Field(..., description="来源章节")


class ExtractionResultResponse(BaseModel):
    """信息提取结果响应模型"""
    document_id: str = Field(..., description="文档ID")
    document_name: str = Field(..., description="文档名称")
    summary: DocumentSummaryResponse = Field(..., description="文档摘要")
    key_information: List[KeyInformationResponse] = Field(..., description="关键信息")
    entities: List[ExtractedEntityResponse] = Field(..., description="提取的实体")
    tags: List[str] = Field(..., description="文档标签")
    word_count: int = Field(..., description="字数统计")
    paragraph_count: int = Field(..., description="段落数量")
    section_count: int = Field(..., description="章节数量")
    extraction_timestamp: str = Field(..., description="提取时间")
    processing_time: float = Field(..., description="处理时间（秒）")


# ========== API接口 ==========

@router.post("/analyze", response_model=APIResponse[ExtractionResultResponse])
async def analyze_document(
    request: ExtractionRequest,
    extraction_service: InformationExtractionService = Depends(get_extraction_service)
):
    """
    分析单个文档并提取信息
    
    对指定文档进行全面分析，包括：
    - 生成多层次摘要
    - 提取关键信息点
    - 识别重要实体
    - 生成智能标签
    """
    try:
        logger.info(f"📊 Starting document analysis: {request.document_id} (user: {request.user_id})")
        
        # 执行信息提取
        extraction_result = await extraction_service.extract_information(
            document_id=request.document_id,
            user_id=request.user_id
        )
        
        # 转换为响应格式
        response = ExtractionResultResponse(
            document_id=extraction_result.document_id,
            document_name=extraction_result.document_name,
            summary=DocumentSummaryResponse(
                title=extraction_result.summary.title,
                brief_summary=extraction_result.summary.brief_summary,
                detailed_summary=extraction_result.summary.detailed_summary,
                key_points=extraction_result.summary.key_points,
                structure_summary=extraction_result.summary.structure_summary,
                confidence=extraction_result.summary.confidence
            ),
            key_information=[
                KeyInformationResponse(
                    content=info.content,
                    importance=info.importance,
                    category=info.category,
                    keywords=info.keywords,
                    source_section=info.source_section
                )
                for info in extraction_result.key_information
            ],
            entities=[
                ExtractedEntityResponse(
                    text=entity.text,
                    type=entity.type,
                    confidence=entity.confidence,
                    context=entity.context,
                    position=entity.position
                )
                for entity in extraction_result.entities
            ],
            tags=extraction_result.tags,
            word_count=extraction_result.word_count,
            paragraph_count=extraction_result.paragraph_count,
            section_count=extraction_result.section_count,
            extraction_timestamp=extraction_result.extraction_timestamp.isoformat(),
            processing_time=extraction_result.processing_time
        )
        
        logger.info(f"✅ Document analysis completed in {extraction_result.processing_time:.2f}s")
        return create_response(response)
        
    except Exception as e:
        logger.error(f"❌ Document analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"文档分析失败: {str(e)}")


@router.get("/summary/{document_id}", response_model=APIResponse[DocumentSummaryResponse])
async def get_document_summary(
    document_id: str,
    user_id: str = Query(..., description="用户ID"),
    extraction_service: InformationExtractionService = Depends(get_extraction_service)
):
    """
    获取文档摘要
    
    快速生成文档的多层次摘要，包括简要摘要、详细摘要和关键要点。
    """
    try:
        logger.info(f"📝 Generating summary for document: {document_id}")
        
        # 执行信息提取（仅摘要部分）
        extraction_result = await extraction_service.extract_information(
            document_id=document_id,
            user_id=user_id
        )
        
        # 返回摘要信息
        summary_response = DocumentSummaryResponse(
            title=extraction_result.summary.title,
            brief_summary=extraction_result.summary.brief_summary,
            detailed_summary=extraction_result.summary.detailed_summary,
            key_points=extraction_result.summary.key_points,
            structure_summary=extraction_result.summary.structure_summary,
            confidence=extraction_result.summary.confidence
        )
        
        logger.info(f"✅ Summary generated (confidence: {extraction_result.summary.confidence:.2%})")
        return create_response(summary_response)
        
    except Exception as e:
        logger.error(f"❌ Summary generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"摘要生成失败: {str(e)}")


@router.get("/entities/{document_id}", response_model=APIResponse[List[ExtractedEntityResponse]])
async def get_document_entities(
    document_id: str,
    user_id: str = Query(..., description="用户ID"),
    entity_type: Optional[str] = Query(None, description="实体类型过滤"),
    min_confidence: float = Query(0.5, description="最小置信度", ge=0, le=1),
    extraction_service: InformationExtractionService = Depends(get_extraction_service)
):
    """
    获取文档实体
    
    提取文档中的重要实体，如组织机构、人员职位、财务数据等。
    """
    try:
        logger.info(f"🏷️ Extracting entities for document: {document_id}")
        
        # 执行信息提取
        extraction_result = await extraction_service.extract_information(
            document_id=document_id,
            user_id=user_id
        )
        
        # 过滤实体
        entities = extraction_result.entities
        
        if entity_type:
            entities = [e for e in entities if e.type == entity_type]
        
        if min_confidence > 0:
            entities = [e for e in entities if e.confidence >= min_confidence]
        
        # 转换为响应格式
        entity_responses = [
            ExtractedEntityResponse(
                text=entity.text,
                type=entity.type,
                confidence=entity.confidence,
                context=entity.context,
                position=entity.position
            )
            for entity in entities
        ]
        
        logger.info(f"✅ Extracted {len(entity_responses)} entities")
        return create_response(entity_responses)
        
    except Exception as e:
        logger.error(f"❌ Entity extraction failed: {e}")
        raise HTTPException(status_code=500, detail=f"实体提取失败: {str(e)}")


@router.get("/key-information/{document_id}", response_model=APIResponse[List[KeyInformationResponse]])
async def get_key_information(
    document_id: str,
    user_id: str = Query(..., description="用户ID"),
    category: Optional[str] = Query(None, description="信息类别过滤"),
    min_importance: float = Query(0.5, description="最小重要性", ge=0, le=1),
    limit: int = Query(10, description="返回数量限制", ge=1, le=50),
    extraction_service: InformationExtractionService = Depends(get_extraction_service)
):
    """
    获取关键信息
    
    提取文档中的关键信息点，按重要性排序。
    """
    try:
        logger.info(f"🔑 Extracting key information for document: {document_id}")
        
        # 执行信息提取
        extraction_result = await extraction_service.extract_information(
            document_id=document_id,
            user_id=user_id
        )
        
        # 过滤关键信息
        key_info = extraction_result.key_information
        
        if category:
            key_info = [info for info in key_info if info.category == category]
        
        if min_importance > 0:
            key_info = [info for info in key_info if info.importance >= min_importance]
        
        # 限制数量
        key_info = key_info[:limit]
        
        # 转换为响应格式
        key_info_responses = [
            KeyInformationResponse(
                content=info.content,
                importance=info.importance,
                category=info.category,
                keywords=info.keywords,
                source_section=info.source_section
            )
            for info in key_info
        ]
        
        logger.info(f"✅ Extracted {len(key_info_responses)} key information points")
        return create_response(key_info_responses)
        
    except Exception as e:
        logger.error(f"❌ Key information extraction failed: {e}")
        raise HTTPException(status_code=500, detail=f"关键信息提取失败: {str(e)}")


@router.get("/tags/{document_id}")
async def get_document_tags(
    document_id: str,
    user_id: str = Query(..., description="用户ID"),
    extraction_service: InformationExtractionService = Depends(get_extraction_service)
):
    """
    获取文档标签
    
    基于文档内容自动生成智能标签。
    """
    try:
        logger.info(f"🏷️ Generating tags for document: {document_id}")
        
        # 执行信息提取
        extraction_result = await extraction_service.extract_information(
            document_id=document_id,
            user_id=user_id
        )
        
        result = {
            "document_id": document_id,
            "tags": extraction_result.tags,
            "tag_count": len(extraction_result.tags),
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"✅ Generated {len(extraction_result.tags)} tags")
        return create_response(result)
        
    except Exception as e:
        logger.error(f"❌ Tag generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"标签生成失败: {str(e)}")


@router.post("/batch-analyze")
async def batch_analyze_documents(
    request: BatchExtractionRequest,
    background_tasks: BackgroundTasks,
    extraction_service: InformationExtractionService = Depends(get_extraction_service)
):
    """
    批量分析文档
    
    对多个文档进行批量信息提取，适用于大量文档的批处理场景。
    """
    try:
        logger.info(f"📊 Starting batch analysis for {len(request.document_ids)} documents")
        
        # 创建批处理任务
        task_id = f"batch_{datetime.now().timestamp()}"
        
        # 添加后台任务
        background_tasks.add_task(
            _process_batch_extraction,
            task_id,
            request.document_ids,
            request.user_id,
            request.extraction_types,
            extraction_service
        )
        
        result = {
            "task_id": task_id,
            "document_count": len(request.document_ids),
            "status": "processing",
            "message": f"批量分析任务已启动，正在处理 {len(request.document_ids)} 个文档",
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"✅ Batch analysis task created: {task_id}")
        return create_response(result)
        
    except Exception as e:
        logger.error(f"❌ Batch analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"批量分析失败: {str(e)}")


@router.get("/batch-status/{task_id}")
async def get_batch_status(task_id: str):
    """
    获取批量任务状态
    
    查询批量分析任务的执行状态和进度。
    """
    try:
        # 这里应该从数据库或缓存中查询任务状态
        # 暂时返回示例状态
        result = {
            "task_id": task_id,
            "status": "completed",  # processing, completed, failed
            "progress": 100,  # 0-100
            "processed_count": 5,
            "total_count": 5,
            "results": [
                {
                    "document_id": f"doc_{i}",
                    "status": "success",
                    "extraction_time": 2.5
                }
                for i in range(1, 6)
            ],
            "timestamp": datetime.now().isoformat()
        }
        
        return create_response(result)
        
    except Exception as e:
        logger.error(f"❌ Batch status query failed: {e}")
        raise HTTPException(status_code=500, detail=f"任务状态查询失败: {str(e)}")


@router.get("/statistics/{user_id}")
async def get_extraction_statistics(
    user_id: str,
    days: int = Query(30, description="统计天数", ge=1, le=365)
):
    """
    获取提取统计信息
    
    返回用户的文档分析统计数据，包括处理文档数量、提取信息统计等。
    """
    try:
        # 这里应该从数据库查询统计数据
        # 暂时返回示例数据
        stats = {
            "user_id": user_id,
            "period_days": days,
            "total_documents": 25,
            "total_extractions": 45,
            "avg_processing_time": 3.2,
            "entity_types": {
                "组织机构": 120,
                "财务数据": 85,
                "政策法规": 65,
                "人员职位": 45,
                "时间日期": 95,
                "ESG指标": 35
            },
            "information_categories": {
                "核心业务": 30,
                "财务状况": 25,
                "风险管理": 20,
                "治理结构": 15,
                "ESG表现": 18,
                "战略规划": 12
            },
            "recent_activity": [
                {
                    "date": "2024-01-15",
                    "documents_processed": 3,
                    "extractions_count": 8
                },
                {
                    "date": "2024-01-14", 
                    "documents_processed": 2,
                    "extractions_count": 5
                }
            ],
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"✅ Retrieved extraction statistics for user: {user_id}")
        return create_response(stats)
        
    except Exception as e:
        logger.error(f"❌ Statistics retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=f"统计信息获取失败: {str(e)}")


# ========== 后台任务函数 ==========

async def _process_batch_extraction(
    task_id: str,
    document_ids: List[str],
    user_id: str,
    extraction_types: List[str],
    extraction_service: InformationExtractionService
):
    """处理批量提取任务"""
    try:
        logger.info(f"🔄 Processing batch extraction task: {task_id}")
        
        results = []
        for i, doc_id in enumerate(document_ids):
            try:
                # 执行单个文档提取
                extraction_result = await extraction_service.extract_information(
                    document_id=doc_id,
                    user_id=user_id
                )
                
                results.append({
                    "document_id": doc_id,
                    "status": "success",
                    "extraction_time": extraction_result.processing_time
                })
                
                logger.info(f"✅ Batch progress: {i+1}/{len(document_ids)} completed")
                
            except Exception as e:
                logger.error(f"❌ Failed to process document {doc_id}: {e}")
                results.append({
                    "document_id": doc_id,
                    "status": "failed",
                    "error": str(e)
                })
        
        # 这里应该将结果保存到数据库或缓存
        logger.info(f"✅ Batch extraction task completed: {task_id}")
        
    except Exception as e:
        logger.error(f"❌ Batch extraction task failed: {task_id}, error: {e}") 