"""
RAG API - 基于文档内容的智能问答接口
支持检索增强生成的精准问答服务
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime

from app.services.rag_service import get_rag_service, RAGService
from app.core.response import APIResponse, create_response
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/rag", tags=["RAG"])


# ========== 请求/响应模型 ==========

class RAGQuestionRequest(BaseModel):
    """RAG问答请求模型"""
    question: str = Field(..., description="用户问题", min_length=1, max_length=500)
    user_id: str = Field(..., description="用户ID")
    document_id: Optional[str] = Field(None, description="特定文档ID（可选）")
    document_type: Optional[str] = Field(None, description="文档类型过滤（可选）")
    max_sources: int = Field(5, description="最大来源数量", ge=1, le=10)


class DocumentQuestionRequest(BaseModel):
    """针对特定文档的问答请求"""
    question: str = Field(..., description="用户问题", min_length=1, max_length=500)
    document_id: str = Field(..., description="文档ID")
    user_id: str = Field(..., description="用户ID")


class RAGAnswerResponse(BaseModel):
    """RAG问答响应模型"""
    question: str = Field(..., description="原始问题")
    answer: str = Field(..., description="生成的答案")
    confidence: float = Field(..., description="置信度 (0-1)", ge=0, le=1)
    reasoning: str = Field(..., description="推理过程说明")
    sources: List[Dict[str, Any]] = Field(..., description="来源文档片段")
    timestamp: str = Field(..., description="生成时间")


class DocumentAnalysisRequest(BaseModel):
    """文档分析请求模型"""
    document_id: str = Field(..., description="文档ID")
    user_id: str = Field(..., description="用户ID")
    analysis_type: str = Field("summary", description="分析类型: summary, keywords, entities")


# ========== API接口 ==========

@router.post("/ask", response_model=APIResponse[RAGAnswerResponse])
async def ask_question(
    request: RAGQuestionRequest,
    rag_service: RAGService = Depends(get_rag_service)
):
    """
    基于知识库回答问题
    
    使用RAG技术从用户的私有知识库中检索相关信息，
    并生成基于文档内容的准确答案。
    """
    try:
        logger.info(f"🤔 RAG Question received: '{request.question}' (user: {request.user_id})")
        
        # 调用RAG服务生成答案
        rag_answer = await rag_service.answer_question(
            question=request.question,
            user_id=request.user_id,
            document_id=request.document_id,
            document_type=request.document_type
        )
        
        # 转换为响应格式
        response = RAGAnswerResponse(
            question=rag_answer.question,
            answer=rag_answer.answer,
            confidence=rag_answer.confidence,
            reasoning=rag_answer.reasoning,
            sources=rag_answer.to_dict()['sources'],
            timestamp=rag_answer.timestamp.isoformat()
        )
        
        logger.info(f"✅ RAG Answer generated (confidence: {rag_answer.confidence:.2%})")
        return create_response(response)
        
    except Exception as e:
        logger.error(f"❌ RAG question failed: {e}")
        raise HTTPException(status_code=500, detail=f"问答处理失败: {str(e)}")


@router.post("/ask-document", response_model=APIResponse[RAGAnswerResponse])
async def ask_document_question(
    request: DocumentQuestionRequest,
    rag_service: RAGService = Depends(get_rag_service)
):
    """
    针对特定文档提问
    
    专门针对某个文档进行问答，可以获得更精准的答案。
    适用于用户想要深入了解某份特定文档内容的场景。
    """
    try:
        logger.info(f"📄 Document Question: '{request.question}' for doc {request.document_id}")
        
        # 调用RAG服务，限定在特定文档
        rag_answer = await rag_service.answer_question(
            question=request.question,
            user_id=request.user_id,
            document_id=request.document_id
        )
        
        # 转换为响应格式
        response = RAGAnswerResponse(
            question=rag_answer.question,
            answer=rag_answer.answer,
            confidence=rag_answer.confidence,
            reasoning=rag_answer.reasoning,
            sources=rag_answer.to_dict()['sources'],
            timestamp=rag_answer.timestamp.isoformat()
        )
        
        logger.info(f"✅ Document Answer generated (confidence: {rag_answer.confidence:.2%})")
        return create_response(response)
        
    except Exception as e:
        logger.error(f"❌ Document question failed: {e}")
        raise HTTPException(status_code=500, detail=f"文档问答处理失败: {str(e)}")


@router.get("/document-insights/{document_id}")
async def get_document_insights(
    document_id: str,
    user_id: str = Query(..., description="用户ID"),
    rag_service: RAGService = Depends(get_rag_service)
):
    """
    获取文档洞察
    
    自动生成文档的关键问题和答案，帮助用户快速了解文档核心内容。
    """
    try:
        logger.info(f"🔍 Generating insights for document: {document_id}")
        
        # 预定义的洞察问题
        insight_questions = [
            "这份文档的主要内容是什么？",
            "文档中提到的关键政策或规定有哪些？",
            "文档中的重要数据或指标是什么？",
            "文档涉及的主要流程或步骤是什么？",
            "文档的核心结论或建议是什么？"
        ]

        # ✅ Week 3: Process all questions in parallel (5x speedup: 25s → 5s)
        import asyncio

        async def process_question(question: str):
            """Process a single insight question"""
            try:
                rag_answer = await rag_service.answer_question(
                    question=question,
                    user_id=user_id,
                    document_id=document_id
                )

                # Only return high-confidence insights
                if rag_answer.confidence >= 0.4:
                    return {
                        "question": question,
                        "answer": rag_answer.answer,
                        "confidence": rag_answer.confidence,
                        "sources_count": len(rag_answer.sources)
                    }
            except Exception as e:
                logger.warning(f"⚠️ Failed to generate insight for question: {question}, error: {e}")
            return None

        # Execute all questions in parallel
        results = await asyncio.gather(
            *[process_question(q) for q in insight_questions],
            return_exceptions=False
        )

        # Filter out None results and exceptions
        insights = [r for r in results if r is not None]
        
        # 按置信度排序
        insights.sort(key=lambda x: x['confidence'], reverse=True)
        
        result = {
            "document_id": document_id,
            "insights": insights,
            "total_insights": len(insights),
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"✅ Generated {len(insights)} insights for document {document_id}")
        return create_response(result)
        
    except Exception as e:
        logger.error(f"❌ Document insights generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"文档洞察生成失败: {str(e)}")


@router.get("/question-suggestions/{user_id}")
async def get_question_suggestions(
    user_id: str,
    document_id: Optional[str] = Query(None, description="特定文档ID（可选）"),
    document_type: Optional[str] = Query(None, description="文档类型过滤（可选）")
):
    """
    获取问题建议
    
    基于用户的文档内容，智能生成相关问题建议，
    帮助用户更好地探索和理解文档内容。
    """
    try:
        # 根据不同场景生成问题建议
        if document_id:
            # 针对特定文档的问题建议
            suggestions = [
                "这份文档的核心内容是什么？",
                "文档中提到的关键信息有哪些？",
                "文档涉及的主要流程或步骤是什么？",
                "文档中的重要数据或指标是什么？",
                "文档的结论或建议是什么？",
                "文档适用的范围或对象是什么？",
                "文档中提到的注意事项有哪些？"
            ]
        elif document_type:
            # 针对特定类型文档的问题建议
            type_specific_suggestions = {
                "pdf": [
                    "这份PDF文档的主要内容是什么？",
                    "文档中的关键政策或规定有哪些？",
                    "文档提到的重要流程是什么？"
                ],
                "docx": [
                    "这份Word文档讲述了什么？",
                    "文档中的主要观点是什么？",
                    "文档的结构和章节安排如何？"
                ],
                "xlsx": [
                    "这份表格数据反映了什么？",
                    "数据中的关键指标有哪些？",
                    "数据趋势如何？"
                ]
            }
            suggestions = type_specific_suggestions.get(document_type.lower(), [
                "这类文档通常包含什么信息？",
                "文档的主要内容是什么？",
                "有哪些关键信息需要关注？"
            ])
        else:
            # 通用问题建议
            suggestions = [
                "我们公司的ESG政策是什么？",
                "环境保护措施有哪些？",
                "公司治理结构是怎样的？",
                "社会责任项目有哪些？",
                "可持续发展目标是什么？",
                "合规管理制度如何运作？",
                "风险管理机制是什么？",
                "员工培训和发展计划如何？",
                "公司的核心价值观是什么？",
                "业务流程和操作规范有哪些？"
            ]
        
        result = {
            "user_id": user_id,
            "document_id": document_id,
            "document_type": document_type,
            "suggestions": suggestions[:8],  # 限制返回8个建议
            "total_suggestions": len(suggestions),
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"✅ Generated {len(suggestions)} question suggestions")
        return create_response(result)
        
    except Exception as e:
        logger.error(f"❌ Question suggestions generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"问题建议生成失败: {str(e)}")


@router.get("/conversation-history/{user_id}")
async def get_conversation_history(
    user_id: str,
    limit: int = Query(20, description="返回记录数量", ge=1, le=100),
    offset: int = Query(0, description="偏移量", ge=0)
):
    """
    获取用户的问答历史
    
    返回用户的历史问答记录，支持分页查询。
    """
    try:
        # 这里应该从数据库查询历史记录
        # 暂时返回示例数据
        history = [
            {
                "id": f"qa_{i}",
                "question": f"示例问题 {i}",
                "answer": f"示例答案 {i}",
                "confidence": 0.8,
                "timestamp": datetime.now().isoformat(),
                "sources_count": 3
            }
            for i in range(offset + 1, offset + limit + 1)
        ]
        
        result = {
            "user_id": user_id,
            "history": history,
            "total": len(history),
            "limit": limit,
            "offset": offset,
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"✅ Retrieved {len(history)} conversation records")
        return create_response(result)
        
    except Exception as e:
        logger.error(f"❌ Conversation history retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=f"对话历史获取失败: {str(e)}")


@router.post("/feedback")
async def submit_feedback(
    question_id: str = Query(..., description="问答ID"),
    rating: int = Query(..., description="评分 (1-5)", ge=1, le=5),
    feedback: Optional[str] = Query(None, description="反馈内容"),
    user_id: str = Query(..., description="用户ID")
):
    """
    提交问答反馈
    
    用户可以对RAG系统生成的答案进行评分和反馈，
    帮助系统持续改进。
    """
    try:
        feedback_data = {
            "question_id": question_id,
            "user_id": user_id,
            "rating": rating,
            "feedback": feedback,
            "timestamp": datetime.now().isoformat()
        }
        
        # 这里应该保存反馈到数据库
        # 暂时只记录日志
        logger.info(f"📝 Feedback received: {feedback_data}")
        
        result = {
            "message": "反馈提交成功",
            "feedback_id": f"feedback_{datetime.now().timestamp()}",
            "timestamp": datetime.now().isoformat()
        }
        
        return create_response(result)
        
    except Exception as e:
        logger.error(f"❌ Feedback submission failed: {e}")
        raise HTTPException(status_code=500, detail=f"反馈提交失败: {str(e)}") 