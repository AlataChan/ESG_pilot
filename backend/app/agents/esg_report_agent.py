"""
ESG报告生成Agent - 智能报告生成和可视化系统

基于LLM的智能ESG报告生成，支持多种标准格式和可视化呈现。
"""

import logging
import asyncio
import json
from typing import Dict, List, Tuple, Any, Optional
from datetime import datetime

from sqlalchemy.orm import Session
from app.agents.base_agent import BaseAgent, AgentProcessingError
from app.bus import A2AMessage, MessageType
from app.core.config import settings
from app.services.report_service import ReportService
from app.models.report import ReportCreate

from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI
from app.core.llm_factory import llm_factory


class ESGReportAgent(BaseAgent):
    """
    ESG报告生成Agent - 智能商业分析师
    
    功能特性:
    - LLM驱动的智能报告生成
    - 数据持久化到数据库
    - 异步处理和状态更新
    - 向上游Agent发送完成通知
    """
    
    def __init__(self, agent_id: str = "ESGReportAgent", message_bus=None, db_session: Session = None):
        """
        初始化ESG报告Agent
        
        Args:
            agent_id: Agent唯一标识符
            message_bus: 消息总线实例
            db_session: 数据库会话实例
        """
        super().__init__(agent_id)
        if message_bus:
            self.message_bus = message_bus
        if db_session:
            self.report_service = ReportService(db_session)

        self.llm: Optional[ChatOpenAI] = None
        self.report_framework: Dict[str, Any] = {}
        self._report_locks: Dict[str, asyncio.Lock] = {}
        
        # 注册核心的消息处理器
        self.register_handler("generate_esg_report", self.handle_generate_report_request)
        logging.info(f"ESGReportAgent {agent_id} instance created. Waiting for initialization.")

    def _get_llm(self) -> ChatOpenAI:
        """延迟初始化并返回LLM实例 - 使用DeepSeek"""
        if self.llm is None:
            self.llm = llm_factory.create_deepseek_llm(
                temperature=0.2,
                request_timeout=60,  # 60秒超时
                max_retries=2       # 最多重试2次
            )
        return self.llm

    async def initialize(self) -> bool:
        """Agent特定的异步初始化逻辑"""
        try:
            self.report_framework = self._initialize_report_framework()
            self._get_llm() # Pre-initialize LLM
            logging.info(f"✅ ESGReportAgent {self.agent_id} initialized successfully")
            return True
        except Exception as e:
            logging.error(f"❌ Failed to initialize ESGReportAgent {self.agent_id}: {e}")
            return False

    async def handle_generate_report_request(self, message: A2AMessage) -> None:
        """
        处理报告生成请求的入口点。
        这是一个启动后台任务的非阻塞方法。
        """
        # 在后台启动实际的报告生成过程，这样就不会阻塞消息总线的处理
        asyncio.create_task(self.generate_report_and_notify(message))

    async def generate_report_and_notify(self, message: A2AMessage) -> None:
        """
        完整的报告生成、持久化和通知流程。
        
        Args:
            message: 包含报告生成参数的原始请求
        """
        company_profile = message.payload.get("company_profile", {})
        conversation_id = message.conversation_id
        
        # 1. 创建数据库记录
        report_create = ReportCreate(
            conversation_id=conversation_id,
            company_name=company_profile.get("company_name", "Unknown Company"),
            company_profile=company_profile,
            standard=message.payload.get("standard", "GRI")
        )
        db_report = self.report_service.create_report(report_create)
        report_id = db_report.id
        logging.info(f"[{report_id}] New report record created. Status: generating.")

        # 2. 生成报告内容
        try:
            report_content = await self._generate_report_content(
                company_profile, 
                message.payload.get("assessment_results", {}), 
                report_create.standard
            )
            
            # 3. 更新数据库记录
            self.report_service.update_report_content(report_id, report_content)
            logging.info(f"[{report_id}] Report content generated and saved to DB. Status: completed.")
            
            # 4. 发送成功通知
            completion_message = A2AMessage(
                sender_id=self.agent_id,
                conversation_id=conversation_id,
                message_type=MessageType.AGENT_RESPONSE,
                payload={
                    "status": "completed",
                    "report_id": report_id,
                    "message": f"ESG report for {report_create.company_name} has been successfully generated.",
                    "company_profile": company_profile, # 将原始画像传回，以便后续Agent使用
                },
                action="report_generated_success" # 清晰的成功动作
            )
            await self.send_message(completion_message)
            logging.info(f"[{report_id}] Sent 'report_generated_success' notification.")

        except Exception as e:
            logging.exception(f"[{report_id}] Error during report generation for conversation {conversation_id}.")
            # 5. 更新数据库为失败状态
            self.report_service.update_report_status(report_id, "failed", str(e))
            
            # 6. 发送失败通知
            error_message = A2AMessage(
                sender_id=self.agent_id,
                conversation_id=conversation_id,
                message_type=MessageType.ERROR,
                payload={
                    "status": "failed",
                    "report_id": report_id,
                    "error": "An internal error occurred while generating the report.",
                    "details": str(e)
                },
                action="report_generated_failed" # 清晰的失败动作
            )
            await self.send_message(error_message)
            logging.warning(f"[{report_id}] Sent 'report_generated_failed' notification.")

    async def _generate_report_content(self, company_profile: Dict[str, Any], 
                                     assessment_results: Dict[str, Any],
                                     standard: str) -> Dict[str, Any]:
        """
        使用LLM生成报告的核心内容 (保持不变)
        """
        # ... (此部分逻辑与您原有的基本一致, 主要是调用LLM)
        standard_info = self.report_framework["report_standards"].get(standard, {})
        system_prompt = f"""你是专业的ESG报告撰写专家... (内容同前)"""
        user_prompt = f"""企业信息：{company_profile}... (内容同前)"""
        
        messages = [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]
        llm = self._get_llm()
        response = await llm.ainvoke(messages)
        
        try:
            return json.loads(response.content.strip())
        except json.JSONDecodeError:
            logging.warning("Failed to parse LLM response as JSON. Returning basic structure.")
            return self._generate_basic_report_structure(company_profile, assessment_results)

    def _generate_basic_report_structure(self, company_profile, assessment_results):
        # ... (内容同前)
        return {"executive_summary": "...", "company_overview": company_profile}


    def _initialize_report_framework(self) -> Dict[str, Any]:
        """
        初始化报告生成框架
        """
        return {
            "report_standards": {
                "GRI": {
                    "name": "Global Reporting Initiative",
                    "version": "GRI Standards 2021",
                    "categories": ["Economic", "Environmental", "Social"]
                },
                "SASB": {
                    "name": "Sustainability Accounting Standards Board",
                    "version": "SASB Standards 2023",
                    "categories": ["Environment", "Social Capital", "Human Capital", "Business Model", "Leadership"]
                },
                "TCFD": {
                    "name": "Task Force on Climate-related Financial Disclosures",
                    "version": "TCFD 2023",
                    "categories": ["Governance", "Strategy", "Risk Management", "Metrics and Targets"]
                }
            },
            "report_sections": [
                "executive_summary",
                "company_overview", 
                "esg_strategy",
                "environmental_performance",
                "social_performance",
                "governance_performance",
                "risk_management",
                "future_outlook",
                "appendix"
            ],
            "visualization_types": [
                "charts",
                "tables", 
                "infographics",
                "dashboards"
            ]
        }

    # 其他辅助函数 handle_create_dashboard 等可以暂时保留或移除，因为当前核心是 generate_report
    # 为了保持Agent的职责单一，我们暂时只关注核心的报告生成流程。

    async def cleanup(self) -> None:
        """Agent特定的清理逻辑"""
        try:
            self._report_locks.clear()
            logging.info(f"✅ ESGReportAgent {self.agent_id} cleaned up successfully")
        except Exception as e:
            logging.error(f"❌ Error during ESGReportAgent cleanup: {e}")