import logging
import asyncio
from typing import Dict, List, Tuple, Any, Optional
from datetime import datetime

from app.agents.base_agent import BaseAgent, AgentProcessingError
from app.bus import A2AMessage, MessageType
from app.core.config import settings
from app.vector_store.chroma_db import get_chroma_manager

from langchain_openai import ChatOpenAI
from langchain.chains import ConversationalRetrievalChain
from app.core.llm_factory import llm_factory
from langchain.prompts import PromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate, ChatPromptTemplate
from langchain_community.vectorstores import Chroma
from langchain.memory import ConversationBufferWindowMemory
from langchain.schema import BaseRetriever
from langchain.callbacks.base import BaseCallbackHandler

class ESGQueryError(AgentProcessingError):
    """ESG 查询专用异常"""
    def __init__(self, message: str, query: str = "", recoverable: bool = True):
        super().__init__(message, recoverable)
        self.query = query

class ESGAssessmentEngine:
    """
    ESG 评估引擎 - 智能评估和风险分析专家
    
    功能特性:
    - 基于企业画像的智能评估
    - 4D评估模型：发现、诊断、设计、交付
    - 行业基准对比分析
    - 风险机会识别
    - 可操作的改进建议
    """
    
    def __init__(self):
        self.assessment_framework = {
            "环境维度": {
                "climate_change": {"name": "气候变化", "indicators": ["碳足迹", "能源效率", "气候风险适应"]},
                "resource_management": {"name": "资源管理", "indicators": ["水资源", "废物管理", "循环经济"]},
                "biodiversity": {"name": "生物多样性", "indicators": ["生态影响", "自然资本保护"]},
                "pollution_control": {"name": "污染防控", "indicators": ["排放管理", "化学品安全"]}
            },
            "社会维度": {
                "employee_rights": {"name": "员工权益", "indicators": ["劳工标准", "多样性包容", "健康安全"]},
                "community_relations": {"name": "社区关系", "indicators": ["社区投资", "当地就业", "文化尊重"]},
                "customer_responsibility": {"name": "客户责任", "indicators": ["产品安全", "数据隐私", "负责任营销"]},
                "supply_chain": {"name": "供应链管理", "indicators": ["供应商ESG标准", "人权尽职调查"]}
            },
            "治理维度": {
                "corporate_governance": {"name": "公司治理", "indicators": ["董事会独立性", "透明度", "问责制"]},
                "business_ethics": {"name": "商业伦理", "indicators": ["反腐败", "反贿赂", "公平竞争"]},
                "risk_management": {"name": "风险管理", "indicators": ["ESG风险识别", "管理体系", "应急响应"]},
                "stakeholder_engagement": {"name": "利益相关方参与", "indicators": ["沟通机制", "反馈处理", "参与决策"]}
            }
        }
        
        # 行业基准数据（简化版本）
        self.industry_benchmarks = {
            "制造业": {
                "environmental_score": 6.5,
                "social_score": 7.0,
                "governance_score": 7.5,
                "key_challenges": ["碳减排", "供应链管理", "员工安全"]
            },
            "金融业": {
                "environmental_score": 7.5,
                "social_score": 8.0,
                "governance_score": 8.5,
                "key_challenges": ["负责任投资", "数据安全", "金融包容性"]
            },
            "服务业": {
                "environmental_score": 7.0,
                "social_score": 7.5,
                "governance_score": 7.8,
                "key_challenges": ["数据隐私", "员工福利", "客户权益"]
            },
            "科技业": {
                "environmental_score": 7.2,
                "social_score": 7.8,
                "governance_score": 8.0,
                "key_challenges": ["算法伦理", "数字鸿沟", "数据安全"]
            }
        }

    def conduct_4d_assessment(self, company_profile: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行4D评估模型：发现、诊断、设计、交付
        
        Args:
            company_profile: 企业画像
            
        Returns:
            完整的ESG评估报告
        """
        # Step 1: Discover - 发现关键议题和风险点
        key_issues = self._discover_key_issues(company_profile)
        
        # Step 2: Diagnose - 诊断当前ESG管理成熟度
        maturity_diagnosis = self._diagnose_maturity(company_profile, key_issues)
        
        # Step 3: Design - 设计改进方案
        improvement_design = self._design_improvements(company_profile, maturity_diagnosis)
        
        # Step 4: Deliver - 交付可执行路径
        execution_plan = self._deliver_execution_plan(improvement_design)
        
        return {
            "assessment_summary": {
                "overall_score": self._calculate_overall_score(maturity_diagnosis),
                "maturity_level": self._determine_maturity_level(maturity_diagnosis),
                "top_risks": key_issues["high_risk_issues"][:3],
                "top_opportunities": key_issues["opportunities"][:3]
            },
            "detailed_assessment": {
                "key_issues_identified": key_issues,
                "maturity_diagnosis": maturity_diagnosis,
                "benchmark_comparison": self._compare_with_benchmarks(company_profile, maturity_diagnosis),
                "risk_opportunity_analysis": self._analyze_risks_opportunities(company_profile, key_issues)
            },
            "improvement_roadmap": {
                "improvement_design": improvement_design,
                "execution_plan": execution_plan,
                "quick_wins": execution_plan["quick_wins"],
                "medium_term": execution_plan["medium_term"],
                "long_term": execution_plan["long_term"]
            },
            "assessment_metadata": {
                "assessment_date": datetime.now().isoformat(),
                "assessment_framework": "4D模型",
                "industry_context": company_profile.get("basic_profile", {}).get("industry_category", "未知"),
                "data_completeness": company_profile.get("data_completeness", 0)
            }
        }

    def _discover_key_issues(self, company_profile: Dict[str, Any]) -> Dict[str, Any]:
        """发现关键ESG议题和风险点"""
        industry = company_profile.get("basic_profile", {}).get("industry_category", "")
        risk_mapping = company_profile.get("esg_risk_mapping", {})
        
        high_risk_issues = []
        medium_risk_issues = []
        opportunities = []
        
        # 分析环境风险
        env_risks = risk_mapping.get("environmental_risks", {})
        if env_risks.get("level") == "高":
            high_risk_issues.extend(env_risks.get("specific_risks", []))
        elif env_risks.get("level") == "中":
            medium_risk_issues.extend(env_risks.get("specific_risks", []))
        
        # 分析社会风险
        social_risks = risk_mapping.get("social_risks", {})
        if social_risks.get("level") == "高":
            high_risk_issues.extend(social_risks.get("specific_risks", []))
        elif social_risks.get("level") == "中":
            medium_risk_issues.extend(social_risks.get("specific_risks", []))
        
        # 分析治理风险
        gov_risks = risk_mapping.get("governance_risks", {})
        if gov_risks.get("level") == "高":
            high_risk_issues.extend(gov_risks.get("specific_risks", []))
        elif gov_risks.get("level") == "中":
            medium_risk_issues.extend(gov_risks.get("specific_risks", []))
        
        # 识别机会
        maturity = company_profile.get("esg_maturity_assessment", {})
        if maturity.get("improvement_potential") == "高":
            opportunities.extend([
                "建立ESG管理体系",
                "制定可持续发展战略",
                "提升ESG披露透明度"
            ])
        
        return {
            "high_risk_issues": high_risk_issues,
            "medium_risk_issues": medium_risk_issues,
            "opportunities": opportunities,
            "materiality_matrix": self._create_materiality_matrix(company_profile)
        }

    def _diagnose_maturity(self, company_profile: Dict[str, Any], key_issues: Dict[str, Any]) -> Dict[str, Any]:
        """诊断ESG管理成熟度"""
        maturity_assessment = company_profile.get("esg_maturity_assessment", {})
        
        # 基于现有成熟度评估扩展
        current_stage = maturity_assessment.get("maturity_stage", "起步阶段")
        
        # 各维度成熟度评分（0-4分）
        environmental_maturity = self._assess_dimension_maturity("环境", company_profile)
        social_maturity = self._assess_dimension_maturity("社会", company_profile)
        governance_maturity = self._assess_dimension_maturity("治理", company_profile)
        
        return {
            "overall_maturity": current_stage,
            "dimension_scores": {
                "environmental": environmental_maturity,
                "social": social_maturity,
                "governance": governance_maturity
            },
            "strengths": self._identify_strengths(company_profile),
            "gaps": self._identify_gaps(company_profile, key_issues),
            "improvement_priorities": self._prioritize_improvements(environmental_maturity, social_maturity, governance_maturity)
        }

    def _assess_dimension_maturity(self, dimension: str, company_profile: Dict[str, Any]) -> Dict[str, Any]:
        """评估单个维度的成熟度"""
        # 简化的成熟度评估逻辑
        maturity_indicators = company_profile.get("esg_maturity_assessment", {}).get("supporting_evidence", [])
        
        score = 1  # 基础分
        if any("政策" in evidence for evidence in maturity_indicators):
            score += 1
        if any("实施" in evidence for evidence in maturity_indicators):
            score += 1
        if any("监控" in evidence for evidence in maturity_indicators):
            score += 1
        
        levels = ["无意识", "初步意识", "系统化管理", "整合管理", "领先实践"]
        
        return {
            "score": min(score, 4),
            "level": levels[min(score, 4)],
            "description": f"{dimension}维度处于{levels[min(score, 4)]}阶段"
        }

    def _create_materiality_matrix(self, company_profile: Dict[str, Any]) -> Dict[str, Any]:
        """创建重要性议题矩阵"""
        industry = company_profile.get("basic_profile", {}).get("industry_category", "")
        
        # 基于行业特点设定议题重要性
        if industry == "制造业":
            high_impact_issues = ["碳排放管理", "供应链管理", "员工健康安全"]
            medium_impact_issues = ["水资源管理", "社区关系", "公司治理"]
        elif industry == "金融业":
            high_impact_issues = ["负责任投资", "数据安全", "公司治理"]
            medium_impact_issues = ["员工多样性", "客户隐私", "气候风险"]
        else:
            high_impact_issues = ["合规管理", "员工权益", "环境影响"]
            medium_impact_issues = ["客户关系", "供应商管理", "社区参与"]
        
        return {
            "high_impact_high_concern": high_impact_issues,
            "medium_impact_medium_concern": medium_impact_issues,
            "matrix_explanation": "基于行业特点和利益相关方关注度生成的重要性矩阵"
        }

    def _compare_with_benchmarks(self, company_profile: Dict[str, Any], maturity_diagnosis: Dict[str, Any]) -> Dict[str, Any]:
        """与行业基准对比"""
        industry = company_profile.get("basic_profile", {}).get("industry_category", "")
        benchmark = self.industry_benchmarks.get(industry, self.industry_benchmarks["服务业"])
        
        current_scores = maturity_diagnosis["dimension_scores"]
        
        return {
            "industry_benchmark": benchmark,
            "performance_gaps": {
                "environmental": benchmark["environmental_score"] - current_scores["environmental"]["score"],
                "social": benchmark["social_score"] - current_scores["social"]["score"],
                "governance": benchmark["governance_score"] - current_scores["governance"]["score"]
            },
            "relative_position": "需要改进" if any(gap > 1 for gap in [
                benchmark["environmental_score"] - current_scores["environmental"]["score"],
                benchmark["social_score"] - current_scores["social"]["score"],
                benchmark["governance_score"] - current_scores["governance"]["score"]
            ]) else "接近行业平均水平"
        }

    def _analyze_risks_opportunities(self, company_profile: Dict[str, Any], key_issues: Dict[str, Any]) -> Dict[str, Any]:
        """分析风险和机会"""
        risks = []
        opportunities = []
        
        # 短期风险（1年内）
        for risk in key_issues["high_risk_issues"]:
            risks.append({
                "risk": risk,
                "timeframe": "短期",
                "impact": "高",
                "likelihood": "中",
                "mitigation": f"建立{risk}管理制度"
            })
        
        # 机会识别
        for opp in key_issues["opportunities"]:
            opportunities.append({
                "opportunity": opp,
                "value_potential": "中",
                "timeframe": "中期",
                "implementation_difficulty": "中"
            })
        
        return {
            "risk_register": risks,
            "opportunity_register": opportunities,
            "risk_heat_map": "高风险议题需要优先关注",
            "opportunity_value_assessment": "中等价值创造潜力"
        }

    def _design_improvements(self, company_profile: Dict[str, Any], maturity_diagnosis: Dict[str, Any]) -> Dict[str, Any]:
        """设计改进方案"""
        priorities = maturity_diagnosis["improvement_priorities"]
        gaps = maturity_diagnosis["gaps"]
        
        return {
            "strategic_recommendations": [
                "建立ESG治理架构",
                "制定ESG政策体系",
                "建立ESG绩效监测机制"
            ],
            "operational_improvements": [
                "开展ESG培训",
                "建立数据收集系统",
                "制定ESG报告流程"
            ],
            "capability_building": [
                "建立ESG专业团队",
                "引入ESG管理工具",
                "建立利益相关方沟通机制"
            ]
        }

    def _deliver_execution_plan(self, improvement_design: Dict[str, Any]) -> Dict[str, Any]:
        """交付执行计划"""
        return {
            "quick_wins": [
                {"action": "制定ESG政策声明", "timeline": "1个月", "resource": "低", "impact": "中"},
                {"action": "开展ESG现状调研", "timeline": "2个月", "resource": "中", "impact": "高"},
                {"action": "建立ESG工作小组", "timeline": "1个月", "resource": "低", "impact": "中"}
            ],
            "medium_term": [
                {"action": "建立ESG管理体系", "timeline": "6个月", "resource": "高", "impact": "高"},
                {"action": "开展ESG培训项目", "timeline": "3个月", "resource": "中", "impact": "中"},
                {"action": "建立ESG数据系统", "timeline": "4个月", "resource": "高", "impact": "高"}
            ],
            "long_term": [
                {"action": "发布ESG报告", "timeline": "12个月", "resource": "高", "impact": "高"},
                {"action": "获得ESG认证", "timeline": "18个月", "resource": "高", "impact": "中"},
                {"action": "建立ESG文化", "timeline": "24个月", "resource": "中", "impact": "高"}
            ]
        }

    def _calculate_overall_score(self, maturity_diagnosis: Dict[str, Any]) -> float:
        """计算总体ESG得分"""
        scores = maturity_diagnosis["dimension_scores"]
        env_score = scores["environmental"]["score"]
        social_score = scores["social"]["score"]
        gov_score = scores["governance"]["score"]
        
        # 加权平均（可根据行业调整权重）
        return round((env_score + social_score + gov_score) / 3 * 2.5, 1)  # 转换为10分制

    def _determine_maturity_level(self, maturity_diagnosis: Dict[str, Any]) -> str:
        """确定整体成熟度水平"""
        return maturity_diagnosis["overall_maturity"]

    def _identify_strengths(self, company_profile: Dict[str, Any]) -> List[str]:
        """识别优势"""
        return ["有ESG意识", "愿意改进", "具备基础条件"]

    def _identify_gaps(self, company_profile: Dict[str, Any], key_issues: Dict[str, Any]) -> List[str]:
        """识别差距"""
        return key_issues["high_risk_issues"] + key_issues["medium_risk_issues"]

    def _prioritize_improvements(self, env_maturity: Dict, social_maturity: Dict, governance_maturity: Dict) -> List[str]:
        """优先级排序"""
        scores = [
            ("环境", env_maturity["score"]),
            ("社会", social_maturity["score"]),
            ("治理", governance_maturity["score"])
        ]
        
        # 按得分从低到高排序，得分低的优先改进
        sorted_scores = sorted(scores, key=lambda x: x[1])
        return [dimension for dimension, score in sorted_scores]

class ESGConsultantAgent(BaseAgent):
    """
    ESG 专业咨询 Agent - 主协调器
    
    功能特性:
    - 专业的 ESG 知识问答
    - 上下文感知的对话管理
    - 多层次检索策略
    - 智能答案质量控制
    - 详细的引用和来源追踪
    - 智能ESG评估和风险分析
    - 基于企业画像的个性化建议
    """
    
    def __init__(self, agent_id: str = "ESGConsultantAgent", message_bus=None):
        """
        初始化 ESG 咨询 Agent
        
        Args:
            agent_id: Agent 唯一标识符
            message_bus: 消息总线实例
        """
        super().__init__(agent_id)
        if message_bus:
            self.message_bus = message_bus
            
        try:
            self.chroma_manager = get_chroma_manager()
            self.qa_chain = self._init_enhanced_qa_chain()
            
            # ESG评估引擎
            self.assessment_engine = ESGAssessmentEngine()
            
            # 对话管理
            self.conversations: Dict[str, List[Tuple[str, str]]] = {}
            self.conversation_contexts: Dict[str, Dict[str, Any]] = {}
            
            # 查询统计
            self.query_stats = {
                "total_queries": 0,
                "successful_queries": 0,
                "failed_queries": 0,
                "average_response_time": 0.0
            }
            
            # 评估统计
            self.assessment_stats = {
                "total_assessments": 0,
                "completed_assessments": 0,
                "average_assessment_time": 0.0
            }
            
            # 注册处理器
            self.register_handler("ping", self.handle_ping)
            self.register_handler("user_query", self.handle_user_query)
            self.register_handler("esg_assessment", self.handle_esg_assessment)
            self.register_handler("profile_based_query", self.handle_profile_based_query)
            
            logging.info(f"ESGConsultantAgent {agent_id} initialized with enhanced capabilities and assessment engine")
            
        except Exception as e:
            raise AgentProcessingError(f"Failed to initialize ESGConsultantAgent: {e}", recoverable=False)

    def _init_enhanced_qa_chain(self):
        """初始化增强的 LangChain 对话检索链"""
        try:
            # 配置 LLM - 使用DeepSeek
            llm = llm_factory.create_deepseek_llm(
                temperature=0.1,  # 低温度确保回答准确性
                max_tokens=1000,  # 控制回答长度
                request_timeout=30  # 设置超时
            )
            
            # 配置向量存储
            vector_store = Chroma(
                client=self.chroma_manager.client,
                collection_name=self.chroma_manager.collection.name,
                embedding_function=self.chroma_manager.embedding_function
            )
            
            # 增强的检索器配置
            retriever = vector_store.as_retriever(
                search_type="mmr",  # 使用 MMR (Maximal Marginal Relevance) 减少冗余
                search_kwargs={
                    "k": 5,  # 增加检索文档数量
                    "lambda_mult": 0.7,  # MMR 多样性参数
                    "fetch_k": 10  # 初始检索更多候选
                }
            )
            
            # 专业的 ESG 咨询提示词模板
            system_template = """你是一位资深的 ESG（环境、社会、治理）专业咨询顾问，拥有丰富的可持续发展和企业责任管理经验。

**你的专业领域包括：**
- 环境管理：碳排放、水资源管理、废物处理、生物多样性保护
- 社会责任：员工权益、社区关系、供应链管理、人权保护
- 公司治理：董事会结构、风险管理、合规性、透明度

**回答指导原则：**
1. **准确性优先**：仅基于提供的上下文信息回答，不要编造或推测
2. **专业性**：使用准确的 ESG 术语和行业标准
3. **实用性**：提供可操作的建议和具体的实施步骤
4. **结构化**：使用清晰的段落和要点组织回答
5. **引用来源**：明确指出信息来源，增强可信度

**回答格式要求：**
- 如果上下文包含相关信息，请提供详细、专业的回答
- 如果上下文信息不足，请明确说明并建议需要哪些额外信息
- 对于复杂问题，请分步骤或分类别进行回答
- 在适当时候提供相关的 ESG 框架或标准参考

**上下文信息：**
{context}

**历史对话：**
{chat_history}

请基于以上信息专业地回答用户的问题。"""

            human_template = """**用户问题：**
{question}

**请提供专业的 ESG 咨询建议：**"""

            # 创建对话提示模板
            messages = [
                SystemMessagePromptTemplate.from_template(system_template),
                HumanMessagePromptTemplate.from_template(human_template)
            ]
            qa_prompt = ChatPromptTemplate.from_messages(messages)

            # 创建增强的对话检索链
            qa_chain = ConversationalRetrievalChain.from_llm(
                llm=llm,
                retriever=retriever,
                return_source_documents=True,
                combine_docs_chain_kwargs={"prompt": qa_prompt},
                max_tokens_limit=3000,  # 控制上下文长度
                verbose=False  # 生产环境关闭详细日志
            )
            
            logging.info("Enhanced QA chain initialized successfully")
            return qa_chain
            
        except Exception as e:
            raise AgentProcessingError(f"Failed to initialize QA chain: {e}", recoverable=False)

    async def handle_ping(self, message: A2AMessage) -> Dict[str, Any]:
        """
        健康检查处理器
        
        Args:
            message: Ping 消息
            
        Returns:
            健康状态响应
        """
        logging.info(f"Received ping from {message.from_agent}")
        
        # 执行健康检查
        health_info = {
            "status": "pong",
            "original_sender": message.from_agent,
            "agent_health": self.get_health_status(),
            "qa_chain_ready": self.qa_chain is not None,
            "vector_store_ready": self.chroma_manager is not None,
            "active_conversations": len(self.conversations),
            "query_stats": self.query_stats
        }
        
        return health_info

    async def handle_user_query(self, message: A2AMessage) -> Dict[str, Any]:
        """
        处理用户查询 - 增强版本
        
        Args:
            message: 包含用户查询的消息
            
        Returns:
            查询结果和相关信息
        """
        start_time = asyncio.get_event_loop().time()
        query_text = message.payload.get("query", "").strip()
        conversation_id = message.conversation_id
        
        # 更新查询统计
        self.query_stats["total_queries"] += 1
        
        try:
            # 输入验证
            self._validate_query_input(query_text, conversation_id)
            
            logging.info(f"Processing ESG query for conversation '{conversation_id}': '{query_text[:100]}...'")
            
            # 获取或初始化对话上下文
            conversation_context = self._get_conversation_context(conversation_id)
            chat_history = self.conversations.get(conversation_id, [])
            
            # 增强查询处理
            result = await self._process_enhanced_query(
                query_text, 
                chat_history, 
                conversation_context
            )
            
            # 更新对话历史和上下文
            self._update_conversation_history(conversation_id, query_text, result["answer"])
            self._update_conversation_context(conversation_id, query_text, result)
            
            # 计算响应时间
            response_time = asyncio.get_event_loop().time() - start_time
            self._update_query_stats(response_time, success=True)
            
            # 构建增强响应
            enhanced_response = self._build_enhanced_response(result, response_time, conversation_id)
            
            logging.info(f"ESG query processed successfully in {response_time:.2f}s")
            return enhanced_response
            
        except ESGQueryError as e:
            self._update_query_stats(asyncio.get_event_loop().time() - start_time, success=False)
            raise e
        except Exception as e:
            self._update_query_stats(asyncio.get_event_loop().time() - start_time, success=False)
            raise ESGQueryError(
                f"Unexpected error processing ESG query: {e}",
                query=query_text,
                recoverable=True
            )

    def _validate_query_input(self, query_text: str, conversation_id: str):
        """验证查询输入"""
        if not query_text:
            raise ESGQueryError("查询内容不能为空", recoverable=False)
        
        if len(query_text) > 1000:
            raise ESGQueryError("查询内容过长，请控制在1000字符以内", recoverable=False)
        
        if not conversation_id:
            raise ESGQueryError("对话ID不能为空", recoverable=False)

    def _get_conversation_context(self, conversation_id: str) -> Dict[str, Any]:
        """获取对话上下文"""
        if conversation_id not in self.conversation_contexts:
            self.conversation_contexts[conversation_id] = {
                "created_at": datetime.now(),
                "query_count": 0,
                "topics": set(),
                "user_interests": [],
                "last_query_time": None
            }
        return self.conversation_contexts[conversation_id]

    async def _process_enhanced_query(self, query_text: str, chat_history: List[Tuple[str, str]], context: Dict[str, Any]) -> Dict[str, Any]:
        """增强的查询处理"""
        try:
            # 在执行器中运行 LangChain 调用以避免阻塞
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: self.qa_chain.invoke({
                    "question": query_text,
                    "chat_history": chat_history
                })
            )
            
            # 验证结果质量
            self._validate_query_result(result, query_text)
            
            return result
            
        except Exception as e:
            raise ESGQueryError(f"查询处理失败: {e}", query=query_text, recoverable=True)

    def _validate_query_result(self, result: Dict[str, Any], query_text: str):
        """验证查询结果质量"""
        if not result:
            raise ESGQueryError("查询返回空结果", query=query_text, recoverable=True)
        
        answer = result.get("answer", "").strip()
        if not answer:
            raise ESGQueryError("查询未返回有效答案", query=query_text, recoverable=True)
        
        # 检查答案质量指标
        if len(answer) < 20:
            logging.warning(f"Query answer seems too short: {len(answer)} characters")
        
        source_docs = result.get("source_documents", [])
        if not source_docs:
            logging.warning("Query returned no source documents")

    def _update_conversation_history(self, conversation_id: str, query: str, answer: str):
        """更新对话历史"""
        if conversation_id not in self.conversations:
            self.conversations[conversation_id] = []
        
        self.conversations[conversation_id].append((query, answer))
        
        # 限制历史长度以控制内存使用
        max_history = 10
        if len(self.conversations[conversation_id]) > max_history:
            self.conversations[conversation_id] = self.conversations[conversation_id][-max_history:]

    def _update_conversation_context(self, conversation_id: str, query: str, result: Dict[str, Any]):
        """更新对话上下文"""
        context = self.conversation_contexts[conversation_id]
        context["query_count"] += 1
        context["last_query_time"] = datetime.now()
        
        # 简单的主题提取（可以后续用 NLP 增强）
        esg_keywords = {
            "环境": ["环境", "碳排放", "气候", "能源", "水资源", "废物", "污染"],
            "社会": ["社会", "员工", "社区", "人权", "供应链", "多样性"],
            "治理": ["治理", "董事会", "合规", "风险", "透明度", "审计"]
        }
        
        query_lower = query.lower()
        for topic, keywords in esg_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                context["topics"].add(topic)

    def _update_query_stats(self, response_time: float, success: bool):
        """更新查询统计"""
        if success:
            self.query_stats["successful_queries"] += 1
        else:
            self.query_stats["failed_queries"] += 1
        
        # 更新平均响应时间
        total_queries = self.query_stats["total_queries"]
        current_avg = self.query_stats["average_response_time"]
        self.query_stats["average_response_time"] = (
            (current_avg * (total_queries - 1) + response_time) / total_queries
        )

    def _build_enhanced_response(self, result: Dict[str, Any], response_time: float, conversation_id: str) -> Dict[str, Any]:
        """构建增强的响应"""
        answer = result.get("answer", "")
        source_docs = result.get("source_documents", [])
        
        # 处理来源文档
        processed_sources = []
        for i, doc in enumerate(source_docs):
            if hasattr(doc, 'page_content') and hasattr(doc, 'metadata'):
                source_info = {
                    "content_preview": doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content,
                    "metadata": doc.metadata,
                    "relevance_rank": i + 1
                }
                processed_sources.append(source_info)
        
        # 构建完整响应
        enhanced_response = {
            "answer": answer,
            "source_documents": processed_sources,
            "response_metadata": {
                "response_time": round(response_time, 3),
                "conversation_id": conversation_id,
                "sources_count": len(processed_sources),
                "answer_length": len(answer),
                "query_timestamp": datetime.now().isoformat(),
                "agent_id": self.agent_id
            },
            "conversation_context": {
                "total_queries": self.conversation_contexts[conversation_id]["query_count"],
                "identified_topics": list(self.conversation_contexts[conversation_id]["topics"])
            }
        }
        
        return enhanced_response

    def get_esg_stats(self) -> Dict[str, Any]:
        """获取 ESG 咨询统计信息"""
        base_stats = self.get_health_status()
        
        esg_specific_stats = {
            **base_stats,
            "query_statistics": self.query_stats,
            "active_conversations": len(self.conversations),
            "total_conversation_contexts": len(self.conversation_contexts),
            "qa_chain_status": "ready" if self.qa_chain else "not_ready",
            "vector_store_status": "connected" if self.chroma_manager else "disconnected"
        }
        
        return esg_specific_stats

    def reset_conversation(self, conversation_id: str) -> bool:
        """重置指定对话的历史和上下文"""
        try:
            if conversation_id in self.conversations:
                del self.conversations[conversation_id]
            if conversation_id in self.conversation_contexts:
                del self.conversation_contexts[conversation_id]
            
            logging.info(f"Conversation {conversation_id} reset successfully")
            return True
        except Exception as e:
            logging.error(f"Failed to reset conversation {conversation_id}: {e}")
            return False

    def get_conversation_summary(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """获取对话摘要"""
        if conversation_id not in self.conversations:
            return None
        
        conversation = self.conversations[conversation_id]
        context = self.conversation_contexts.get(conversation_id, {})
        
        summary = {
            "conversation_id": conversation_id,
            "total_exchanges": len(conversation),
            "created_at": context.get("created_at"),
            "last_query_time": context.get("last_query_time"),
            "identified_topics": list(context.get("topics", [])),
            "recent_queries": [q for q, _ in conversation[-3:]]  # 最近3个查询
        }
        
        return summary

    async def handle_esg_assessment(self, message: A2AMessage) -> Dict[str, Any]:
        """
        处理ESG评估请求
        
        Args:
            message: 包含企业画像的评估请求
            
        Returns:
            完整的ESG评估报告
        """
        start_time = asyncio.get_event_loop().time()
        company_profile = message.payload.get("company_profile", {})
        conversation_id = message.conversation_id
        
        # 更新评估统计
        self.assessment_stats["total_assessments"] += 1
        
        try:
            logging.info(f"Starting ESG assessment for conversation '{conversation_id}'")
            
            # 验证企业画像数据
            if not company_profile:
                raise ESGQueryError("企业画像数据不能为空", recoverable=False)
            
            # 执行4D评估
            assessment_result = self.assessment_engine.conduct_4d_assessment(company_profile)
            
            # 计算评估时间
            assessment_time = asyncio.get_event_loop().time() - start_time
            self._update_assessment_stats(assessment_time, success=True)
            
            # 构建增强响应
            enhanced_response = {
                "assessment_report": assessment_result,
                "assessment_metadata": {
                    "assessment_time": round(assessment_time, 3),
                    "conversation_id": conversation_id,
                    "assessment_timestamp": datetime.now().isoformat(),
                    "agent_id": self.agent_id,
                    "company_profile_completeness": company_profile.get("data_completeness", 0)
                },
                "next_steps": {
                    "recommended_actions": assessment_result["improvement_roadmap"]["quick_wins"],
                    "follow_up_available": True,
                    "consultation_available": True
                }
            }
            
            logging.info(f"ESG assessment completed successfully in {assessment_time:.2f}s")
            return enhanced_response
            
        except Exception as e:
            self._update_assessment_stats(asyncio.get_event_loop().time() - start_time, success=False)
            raise ESGQueryError(f"ESG评估失败: {e}", recoverable=True)

    async def handle_profile_based_query(self, message: A2AMessage) -> Dict[str, Any]:
        """
        处理基于企业画像的个性化查询
        
        Args:
            message: 包含查询和企业画像的消息
            
        Returns:
            个性化的查询结果
        """
        start_time = asyncio.get_event_loop().time()
        query_text = message.payload.get("query", "").strip()
        company_profile = message.payload.get("company_profile", {})
        conversation_id = message.conversation_id
        
        # 更新查询统计
        self.query_stats["total_queries"] += 1
        
        try:
            # 输入验证
            self._validate_query_input(query_text, conversation_id)
            
            if not company_profile:
                logging.warning("No company profile provided, falling back to general query")
                return await self.handle_user_query(message)
            
            logging.info(f"Processing profile-based ESG query for conversation '{conversation_id}': '{query_text[:100]}...'")
            
            # 获取或初始化对话上下文
            conversation_context = self._get_conversation_context(conversation_id)
            conversation_context["company_profile"] = company_profile
            
            # 构建个性化上下文
            personalized_context = self._build_personalized_context(query_text, company_profile)
            
            # 增强查询处理（结合企业画像）
            chat_history = self.conversations.get(conversation_id, [])
            enhanced_query = f"{personalized_context}\n\n用户问题: {query_text}"
            
            result = await self._process_enhanced_query(
                enhanced_query, 
                chat_history, 
                conversation_context
            )
            
            # 更新对话历史和上下文
            self._update_conversation_history(conversation_id, query_text, result["answer"])
            self._update_conversation_context(conversation_id, query_text, result)
            
            # 计算响应时间
            response_time = asyncio.get_event_loop().time() - start_time
            self._update_query_stats(response_time, success=True)
            
            # 构建个性化响应
            enhanced_response = self._build_personalized_response(
                result, response_time, conversation_id, company_profile
            )
            
            logging.info(f"Profile-based ESG query processed successfully in {response_time:.2f}s")
            return enhanced_response
            
        except ESGQueryError as e:
            self._update_query_stats(asyncio.get_event_loop().time() - start_time, success=False)
            raise e
        except Exception as e:
            self._update_query_stats(asyncio.get_event_loop().time() - start_time, success=False)
            raise ESGQueryError(
                f"个性化查询处理失败: {e}",
                query=query_text,
                recoverable=True
            )

    def _build_personalized_context(self, query: str, company_profile: Dict[str, Any]) -> str:
        """构建个性化上下文"""
        basic_info = company_profile.get("basic_profile", {})
        risk_mapping = company_profile.get("esg_risk_mapping", {})
        maturity = company_profile.get("esg_maturity_assessment", {})
        
        context_parts = [
            "**企业背景信息：**",
            f"- 行业类别: {basic_info.get('industry_category', '未知')}",
            f"- 企业规模: {basic_info.get('business_scale', '未知')}",
            f"- ESG成熟度: {maturity.get('maturity_stage', '未评估')}",
            "",
            "**主要ESG风险：**"
        ]
        
        # 添加风险信息
        for risk_type, risk_info in risk_mapping.items():
            if isinstance(risk_info, dict) and risk_info.get("specific_risks"):
                context_parts.append(f"- {risk_type}: {', '.join(risk_info['specific_risks'])}")
        
        context_parts.extend([
            "",
            "请基于以上企业特定背景，提供针对性的ESG建议和指导。"
        ])
        
        return "\n".join(context_parts)

    def _build_personalized_response(self, result: Dict[str, Any], response_time: float, 
                                   conversation_id: str, company_profile: Dict[str, Any]) -> Dict[str, Any]:
        """构建个性化响应"""
        base_response = self._build_enhanced_response(result, response_time, conversation_id)
        
        # 添加个性化元素
        industry = company_profile.get("basic_profile", {}).get("industry_category", "")
        maturity = company_profile.get("esg_maturity_assessment", {}).get("maturity_stage", "")
        
        base_response["personalization"] = {
            "industry_context": industry,
            "maturity_context": maturity,
            "tailored_recommendations": self._generate_tailored_recommendations(
                result["answer"], company_profile
            ),
            "relevant_frameworks": self._suggest_relevant_frameworks(industry),
            "next_steps": self._suggest_next_steps(company_profile)
        }
        
        return base_response

    def _generate_tailored_recommendations(self, answer: str, company_profile: Dict[str, Any]) -> List[str]:
        """生成定制化建议"""
        industry = company_profile.get("basic_profile", {}).get("industry_category", "")
        maturity = company_profile.get("esg_maturity_assessment", {}).get("maturity_stage", "")
        
        recommendations = []
        
        if maturity == "起步阶段":
            recommendations.extend([
                "建议先建立ESG基础管理制度",
                "开展ESG现状评估和差距分析",
                "制定ESG发展路线图"
            ])
        elif maturity == "发展阶段":
            recommendations.extend([
                "完善ESG管理体系和流程",
                "建立ESG绩效监测机制",
                "加强ESG信息披露"
            ])
        
        if industry == "制造业":
            recommendations.append("重点关注碳排放管理和供应链ESG风险")
        elif industry == "金融业":
            recommendations.append("重点关注负责任投资和ESG风险整合")
        
        return recommendations[:3]  # 限制数量

    def _suggest_relevant_frameworks(self, industry: str) -> List[str]:
        """建议相关框架"""
        common_frameworks = ["GRI标准", "SASB标准", "TCFD框架"]
        
        if industry == "制造业":
            common_frameworks.append("ISO 14001环境管理体系")
        elif industry == "金融业":
            common_frameworks.extend(["UNEP FI原则", "赤道原则"])
        
        return common_frameworks

    def _suggest_next_steps(self, company_profile: Dict[str, Any]) -> List[str]:
        """建议下一步行动"""
        maturity = company_profile.get("esg_maturity_assessment", {}).get("maturity_stage", "")
        
        if maturity == "起步阶段":
            return [
                "开展ESG培训提升意识",
                "建立ESG工作小组",
                "制定ESG政策声明"
            ]
        else:
            return [
                "完善ESG数据收集系统",
                "开展利益相关方沟通",
                "准备ESG报告披露"
            ]

    def _update_assessment_stats(self, assessment_time: float, success: bool):
        """更新评估统计"""
        if success:
            self.assessment_stats["completed_assessments"] += 1
        
        # 更新平均评估时间
        total_assessments = self.assessment_stats["total_assessments"]
        current_avg = self.assessment_stats["average_assessment_time"]
        self.assessment_stats["average_assessment_time"] = (
            (current_avg * (total_assessments - 1) + assessment_time) / total_assessments
        )

    def get_comprehensive_stats(self) -> Dict[str, Any]:
        """获取综合统计信息"""
        base_stats = self.get_esg_stats()
        
        comprehensive_stats = {
            **base_stats,
            "assessment_statistics": self.assessment_stats,
            "total_operations": (
                self.query_stats["total_queries"] + 
                self.assessment_stats["total_assessments"]
            ),
            "success_rate": self._calculate_success_rate()
        }
        
        return comprehensive_stats

    def _calculate_success_rate(self) -> float:
        """计算成功率"""
        total_queries = self.query_stats["total_queries"]
        total_assessments = self.assessment_stats["total_assessments"]
        
        if total_queries + total_assessments == 0:
            return 0.0
        
        successful_operations = (
            self.query_stats["successful_queries"] + 
            self.assessment_stats["completed_assessments"]
        )
        
        return round(successful_operations / (total_queries + total_assessments) * 100, 1)