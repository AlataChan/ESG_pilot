"""
ESG评估分析Agent - 专业风险评估和合规检查系统

基于LLM的智能ESG风险评估，提供专业的合规建议和风险预警。
"""

import logging
import asyncio
from typing import Dict, List, Tuple, Any, Optional
from datetime import datetime

from app.agents.base_agent import BaseAgent, AgentProcessingError
from app.bus import A2AMessage, MessageType
from app.core.config import settings
from app.vector_store.chroma_db import get_chroma_manager

from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from app.core.llm_factory import llm_factory
from langchain.schema import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_community.vectorstores import Chroma
from langchain.callbacks.base import BaseCallbackHandler

class ESGAssessmentAgent(BaseAgent):
    """
    ESG评估分析Agent - 专业风险评估专家
    
    功能特性:
    - LLM驱动的智能风险评估
    - 基于知识库的合规检查
    - 行业基准对比分析
    - 个性化风险预警
    - 改进建议生成
    """
    
    def __init__(self, agent_id: str = "ESGAssessmentAgent", message_bus=None):
        """
        初始化ESG评估Agent
        
        Args:
            agent_id: Agent唯一标识符
            message_bus: 消息总线实例
        """
        super().__init__(agent_id)
        if message_bus:
            self.message_bus = message_bus
            
        try:
            # 初始化LLM - 使用DeepSeek
            self.llm = llm_factory.create_deepseek_llm(
                temperature=0.1,  # 低温度确保评估准确性
                request_timeout=60,
                max_retries=2
            )
            
            # 初始化知识库连接
            self.chroma_manager = get_chroma_manager()
            self.vector_store = Chroma(
                client=self.chroma_manager.client,
                collection_name=self.chroma_manager.collection.name,
                embedding_function=self.chroma_manager.embedding_function
            )
            
            # 评估框架
            self.assessment_framework = self._initialize_assessment_framework()
            
            # 评估状态管理
            self.active_assessments: Dict[str, Dict[str, Any]] = {}
            self._assessment_locks: Dict[str, asyncio.Lock] = {}
            
            # 注册消息处理器
            self.register_handler("start_esg_assessment", self.handle_start_assessment)
            self.register_handler("conduct_risk_analysis", self.handle_risk_analysis)
            self.register_handler("compliance_check", self.handle_compliance_check)
            self.register_handler("benchmark_comparison", self.handle_benchmark_comparison)
            self.register_handler("generate_recommendations", self.handle_generate_recommendations)
            
            logging.info(f"ESGAssessmentAgent {agent_id} initialized with LLM-driven assessment system")
            
        except Exception as e:
            raise AgentProcessingError(f"Failed to initialize ESGAssessmentAgent: {e}", recoverable=False)

    def _initialize_assessment_framework(self) -> Dict[str, Any]:
        """
        初始化ESG评估框架
        
        Returns:
            评估框架配置
        """
        return {
            "assessment_dimensions": {
                "environmental": {
                    "categories": ["碳排放", "资源使用", "废物管理", "生物多样性", "水资源"],
                    "weight": 0.4
                },
                "social": {
                    "categories": ["员工权益", "社区关系", "产品责任", "供应链管理", "人权保护"],
                    "weight": 0.35
                },
                "governance": {
                    "categories": ["董事会结构", "透明度", "风险管理", "合规性", "利益相关方参与"],
                    "weight": 0.25
                }
            },
            "risk_levels": {
                "critical": {"score": 8.0, "color": "red", "action": "immediate"},
                "high": {"score": 6.0, "color": "orange", "action": "urgent"},
                "medium": {"score": 4.0, "color": "yellow", "action": "planned"},
                "low": {"score": 2.0, "color": "green", "action": "monitor"}
            },
            "compliance_standards": [
                "CSDDD", "TCFD", "GRI", "SASB", "UN Global Compact",
                "ISO 14001", "ISO 26000", "CDP"
            ]
        }

    async def handle_start_assessment(self, message: A2AMessage) -> Dict[str, Any]:
        """
        处理开始ESG评估请求
        
        Args:
            message: 包含企业信息的评估请求
            
        Returns:
            评估启动确认和初步分析
        """
        try:
            assessment_id = message.payload.get("assessment_id")
            if not assessment_id or not isinstance(assessment_id, str):
                raise AgentProcessingError("评估ID（assessment_id）缺失或无效", recoverable=False)
                
            company_profile = message.payload.get("company_profile", {})
            assessment_scope = message.payload.get("scope", "comprehensive")
            
            # 创建评估锁
            if assessment_id not in self._assessment_locks:
                self._assessment_locks[assessment_id] = asyncio.Lock()
            
            async with self._assessment_locks[assessment_id]:
                # 初始化评估状态
                assessment_state = {
                    "assessment_id": assessment_id,
                    "company_profile": company_profile,
                    "scope": assessment_scope,
                    "status": "initiated",
                    "results": {},
                    "created_at": datetime.now(),
                    "last_updated": datetime.now()
                }
                
                self.active_assessments[assessment_id] = assessment_state
                
                # 生成初步风险分析
                initial_analysis = await self._conduct_initial_analysis(company_profile)
                assessment_state["results"]["initial_analysis"] = initial_analysis
                
                logging.info(f"Started ESG assessment {assessment_id}")
                
                return {
                    "type": "assessment_started",
                    "assessment_id": assessment_id,
                    "status": "initiated",
                    "initial_analysis": initial_analysis,
                    "next_steps": ["risk_analysis", "compliance_check", "benchmark_comparison"]
                }
                
        except Exception as e:
            logging.error(f"Error starting ESG assessment: {e}")
            raise AgentProcessingError(f"Failed to start ESG assessment: {e}")

    async def _conduct_initial_analysis(self, company_profile: Dict[str, Any]) -> Dict[str, Any]:
        """
        进行初步的ESG风险分析
        
        Args:
            company_profile: 企业画像信息
            
        Returns:
            初步分析结果
        """
        try:
            # 构建分析提示
            system_prompt = """你是一位资深的ESG风险评估专家。基于企业画像信息，进行初步的ESG风险识别和分析。

分析维度：
1. 环境风险（Environmental）- 40%权重
2. 社会风险（Social）- 35%权重  
3. 治理风险（Governance）- 25%权重

对每个维度，请：
- 识别主要风险点
- 评估风险等级（critical/high/medium/low）
- 提供简要说明
- 建议优先关注领域

请以JSON格式返回分析结果。"""

            user_prompt = f"""企业画像信息：{company_profile}

请基于以上信息进行初步ESG风险分析，重点关注：
1. 行业特定的ESG风险
2. 企业规模相关的风险
3. 地理位置带来的风险
4. 治理结构的风险

请提供结构化的风险分析报告。"""

            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]
            
            response = await self.llm.ainvoke(messages)
            
            # 解析分析结果
            import json
            try:
                analysis_result = json.loads(response.content.strip())
                logging.info("Generated initial ESG analysis")
                return analysis_result
            except json.JSONDecodeError:
                # 如果解析失败，返回基础分析
                return self._generate_basic_analysis(company_profile)
                
        except Exception as e:
            logging.error(f"Error in initial analysis: {e}")
            return self._generate_basic_analysis(company_profile)

    def _generate_basic_analysis(self, company_profile: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成基础分析结果
        
        Args:
            company_profile: 企业画像
            
        Returns:
            基础分析结果
        """
        return {
            "environmental_risks": ["需要详细评估环境影响"],
            "social_risks": ["需要评估员工和社区关系"],
            "governance_risks": ["需要分析治理结构"],
            "overall_risk_level": "medium",
            "priority_areas": ["环境管理", "社会责任", "治理透明度"]
        }

    async def handle_risk_analysis(self, message: A2AMessage) -> Dict[str, Any]:
        """
        处理深度风险分析请求
        
        Args:
            message: 风险分析请求
            
        Returns:
            详细风险分析结果
        """
        try:
            assessment_id = message.payload.get("assessment_id")
            focus_area = message.payload.get("focus_area", "comprehensive")
            
            if assessment_id not in self.active_assessments:
                raise AgentProcessingError(f"Assessment {assessment_id} not found")
            
            assessment_state = self.active_assessments[assessment_id]
            company_profile = assessment_state["company_profile"]
            
            # 基于知识库进行深度分析
            risk_analysis = await self._conduct_deep_risk_analysis(company_profile, focus_area)
            
            assessment_state["results"]["risk_analysis"] = risk_analysis
            assessment_state["last_updated"] = datetime.now()
            
            return {
                "type": "risk_analysis_completed",
                "assessment_id": assessment_id,
                "risk_analysis": risk_analysis,
                "focus_area": focus_area
            }
            
        except Exception as e:
            logging.error(f"Error in risk analysis: {e}")
            raise AgentProcessingError(f"Failed to conduct risk analysis: {e}")

    async def _conduct_deep_risk_analysis(self, company_profile: Dict[str, Any], focus_area: str) -> Dict[str, Any]:
        """
        进行深度风险分析
        
        Args:
            company_profile: 企业画像
            focus_area: 关注领域
            
        Returns:
            深度风险分析结果
        """
        try:
            # 从知识库检索相关信息
            industry = company_profile.get("industry_sector", "通用")
            search_query = f"{industry} ESG风险 {focus_area}"
            
            # 检索相关知识
            retriever = self.vector_store.as_retriever(
                search_type="mmr",
                search_kwargs={"k": 5, "lambda_mult": 0.7}
            )
            
            relevant_docs = await retriever.aget_relevant_documents(search_query)
            
            # 构建深度分析提示
            system_prompt = """你是ESG风险评估专家，基于企业信息和行业知识进行深度风险分析。

分析要求：
1. 识别具体风险点及其影响程度
2. 评估风险发生概率和影响程度
3. 提供风险缓解建议
4. 识别监管合规要求
5. 建议关键绩效指标(KPIs)

请提供详细、专业的风险分析报告。"""

            knowledge_context = "\n".join([doc.page_content for doc in relevant_docs])
            
            user_prompt = f"""企业信息：{company_profile}

关注领域：{focus_area}

相关知识：{knowledge_context}

请进行深度ESG风险分析，重点关注：
1. 具体风险识别
2. 风险等级评估
3. 潜在影响分析
4. 缓解措施建议
5. 监控指标推荐"""

            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]
            
            response = await self.llm.ainvoke(messages)
            
            # 解析分析结果
            import json
            try:
                risk_analysis = json.loads(response.content.strip())
                return risk_analysis
            except json.JSONDecodeError:
                # 如果解析失败，返回文本分析
                return {"analysis": response.content, "format": "text"}
                
        except Exception as e:
            logging.error(f"Error in deep risk analysis: {e}")
            return {"error": str(e), "status": "analysis_failed"}

    async def handle_compliance_check(self, message: A2AMessage) -> Dict[str, Any]:
        """
        处理合规检查请求
        
        Args:
            message: 合规检查请求
            
        Returns:
            合规检查结果
        """
        try:
            assessment_id = message.payload.get("assessment_id")
            standards = message.payload.get("standards", self.assessment_framework["compliance_standards"])
            
            if assessment_id not in self.active_assessments:
                raise AgentProcessingError(f"Assessment {assessment_id} not found")
            
            assessment_state = self.active_assessments[assessment_id]
            company_profile = assessment_state["company_profile"]
            
            # 进行合规检查
            compliance_results = await self._conduct_compliance_check(company_profile, standards)
            
            assessment_state["results"]["compliance_check"] = compliance_results
            assessment_state["last_updated"] = datetime.now()
            
            return {
                "type": "compliance_check_completed",
                "assessment_id": assessment_id,
                "compliance_results": compliance_results,
                "standards_checked": standards
            }
            
        except Exception as e:
            logging.error(f"Error in compliance check: {e}")
            raise AgentProcessingError(f"Failed to conduct compliance check: {e}")

    async def _conduct_compliance_check(self, company_profile: Dict[str, Any], standards: List[str]) -> Dict[str, Any]:
        """
        进行合规检查
        
        Args:
            company_profile: 企业画像
            standards: 检查标准列表
            
        Returns:
            合规检查结果
        """
        try:
            # 构建合规检查提示
            system_prompt = f"""你是ESG合规专家，负责检查企业是否符合各项ESG标准和法规。

需要检查的标准：{standards}

对每个标准，请评估：
1. 当前合规状态（compliant/partial/non-compliant/unknown）
2. 主要合规要求
3. 发现的合规差距
4. 改进建议
5. 优先级（high/medium/low）

请以JSON格式返回详细的合规检查报告。"""

            user_prompt = f"""企业信息：{company_profile}

请基于企业信息对照各项ESG标准进行合规检查，重点关注：
1. 强制性披露要求
2. 环境管理体系
3. 社会责任履行
4. 治理结构完善性
5. 利益相关方参与"""

            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]
            
            response = await self.llm.ainvoke(messages)
            
            # 解析合规结果
            import json
            try:
                compliance_results = json.loads(response.content.strip())
                return compliance_results
            except json.JSONDecodeError:
                return {"analysis": response.content, "format": "text"}
                
        except Exception as e:
            logging.error(f"Error in compliance check: {e}")
            return {"error": str(e), "status": "check_failed"}

    async def handle_benchmark_comparison(self, message: A2AMessage) -> Dict[str, Any]:
        """
        处理基准对比分析请求
        
        Args:
            message: 基准对比请求
            
        Returns:
            基准对比结果
        """
        try:
            assessment_id = message.payload.get("assessment_id")
            
            if assessment_id not in self.active_assessments:
                raise AgentProcessingError(f"Assessment {assessment_id} not found")
            
            assessment_state = self.active_assessments[assessment_id]
            company_profile = assessment_state["company_profile"]
            
            # 进行基准对比
            benchmark_results = await self._conduct_benchmark_comparison(company_profile)
            
            assessment_state["results"]["benchmark_comparison"] = benchmark_results
            assessment_state["last_updated"] = datetime.now()
            
            return {
                "type": "benchmark_comparison_completed",
                "assessment_id": assessment_id,
                "benchmark_results": benchmark_results
            }
            
        except Exception as e:
            logging.error(f"Error in benchmark comparison: {e}")
            raise AgentProcessingError(f"Failed to conduct benchmark comparison: {e}")

    async def _conduct_benchmark_comparison(self, company_profile: Dict[str, Any]) -> Dict[str, Any]:
        """
        进行行业基准对比
        
        Args:
            company_profile: 企业画像
            
        Returns:
            基准对比结果
        """
        try:
            industry = company_profile.get("industry_sector", "通用")
            company_scale = company_profile.get("company_scale", "中型企业")
            
            # 从知识库检索行业基准数据
            search_query = f"{industry} ESG基准 行业平均 最佳实践"
            
            retriever = self.vector_store.as_retriever(
                search_type="mmr",
                search_kwargs={"k": 3, "lambda_mult": 0.8}
            )
            
            benchmark_docs = await retriever.aget_relevant_documents(search_query)
            
            # 构建基准对比提示
            system_prompt = """你是ESG基准分析专家，负责将企业表现与行业基准进行对比。

对比维度：
1. 环境绩效指标
2. 社会责任指标
3. 治理水平指标
4. 整体ESG评分

对每个维度，请提供：
- 行业平均水平
- 最佳实践标准
- 企业当前位置
- 改进空间分析
- 具体提升建议

请以JSON格式返回对比分析结果。"""

            benchmark_context = "\n".join([doc.page_content for doc in benchmark_docs])
            
            user_prompt = f"""企业信息：{company_profile}

行业基准信息：{benchmark_context}

请进行详细的ESG基准对比分析，包括：
1. 与行业平均水平的对比
2. 与最佳实践的差距分析
3. 同规模企业的比较
4. 改进优先级建议
5. 具体提升路径"""

            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]
            
            response = await self.llm.ainvoke(messages)
            
            # 解析对比结果
            import json
            try:
                benchmark_results = json.loads(response.content.strip())
                return benchmark_results
            except json.JSONDecodeError:
                return {"analysis": response.content, "format": "text"}
                
        except Exception as e:
            logging.error(f"Error in benchmark comparison: {e}")
            return {"error": str(e), "status": "comparison_failed"}

    async def handle_generate_recommendations(self, message: A2AMessage) -> Dict[str, Any]:
        """
        处理生成改进建议请求
        
        Args:
            message: 建议生成请求
            
        Returns:
            改进建议报告
        """
        try:
            assessment_id = message.payload.get("assessment_id")
            
            if assessment_id not in self.active_assessments:
                raise AgentProcessingError(f"Assessment {assessment_id} not found")
            
            assessment_state = self.active_assessments[assessment_id]
            
            # 生成综合改进建议
            recommendations = await self._generate_comprehensive_recommendations(assessment_state)
            
            assessment_state["results"]["recommendations"] = recommendations
            assessment_state["status"] = "completed"
            assessment_state["last_updated"] = datetime.now()
            
            return {
                "type": "recommendations_generated",
                "assessment_id": assessment_id,
                "recommendations": recommendations,
                "status": "completed"
            }
            
        except Exception as e:
            logging.error(f"Error generating recommendations: {e}")
            raise AgentProcessingError(f"Failed to generate recommendations: {e}")

    async def _generate_comprehensive_recommendations(self, assessment_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成综合改进建议
        
        Args:
            assessment_state: 评估状态
            
        Returns:
            综合改进建议
        """
        try:
            results = assessment_state["results"]
            company_profile = assessment_state["company_profile"]
            
            # 构建建议生成提示
            system_prompt = """你是资深的ESG顾问，基于完整的评估结果为企业提供综合改进建议。

建议应包含：
1. 执行优先级（高/中/低）
2. 具体行动计划
3. 时间框架
4. 资源需求
5. 预期效果
6. 关键成功指标

请提供实用、可执行的改进建议。"""

            user_prompt = f"""企业画像：{company_profile}

评估结果：{results}

请基于完整的评估结果，生成综合性的ESG改进建议，包括：
1. 短期行动计划（3-6个月）
2. 中期发展目标（6-18个月）
3. 长期战略规划（18个月以上）
4. 具体实施步骤
5. 预算和资源配置建议
6. 风险缓解措施"""

            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]
            
            response = await self.llm.ainvoke(messages)
            
            # 解析建议结果
            import json
            try:
                recommendations = json.loads(response.content.strip())
                return recommendations
            except json.JSONDecodeError:
                return {"recommendations": response.content, "format": "text"}
                
        except Exception as e:
            logging.error(f"Error generating recommendations: {e}")
            return {"error": str(e), "status": "generation_failed"}

    def get_health_status(self) -> Dict[str, Any]:
        """
        获取Agent健康状态
        
        Returns:
            健康状态信息
        """
        base_status = super().get_health_status()
        base_status.update({
                            "llm_model": "gpt-4.1",
            "active_assessments": len(self.active_assessments),
            "vector_store_connected": self.vector_store is not None,
            "assessment_locks": len(self._assessment_locks)
        })
        return base_status

    async def initialize(self) -> bool:
        """
        Agent特定的初始化逻辑
        
        Returns:
            初始化是否成功
        """
        try:
            # 初始化评估框架
            self.assessment_framework = self._initialize_assessment_framework()
            
            # 注册消息处理器
            self.register_handler("start_assessment", self.handle_start_assessment)
            self.register_handler("risk_analysis", self.handle_risk_analysis)
            self.register_handler("compliance_check", self.handle_compliance_check)
            self.register_handler("benchmark_comparison", self.handle_benchmark_comparison)
            self.register_handler("generate_recommendations", self.handle_generate_recommendations)
            
            logging.info(f"✅ ESGAssessmentAgent {self.agent_id} initialized successfully")
            return True
            
        except Exception as e:
            logging.error(f"❌ Failed to initialize ESGAssessmentAgent {self.agent_id}: {e}")
            return False

    async def cleanup(self) -> None:
        """
        Agent特定的清理逻辑
        """
        try:
            # 清理活跃评估
            self.active_assessments.clear()
            
            # 清理框架数据
            self.assessment_framework = {}
            
            # 清理锁
            self._assessment_locks.clear()
            
            logging.info(f"✅ ESGAssessmentAgent {self.agent_id} cleaned up successfully")
            
        except Exception as e:
            logging.error(f"❌ Error during ESGAssessmentAgent cleanup: {e}") 