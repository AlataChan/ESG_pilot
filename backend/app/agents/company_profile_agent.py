"""
企业画像智能Agent - LLM驱动的动态对话系统

完全替代硬编码的CompanyProfileGenerator，实现真正的AI-first企业画像生成。
现在支持对话状态持久化，解决服务重启和页面刷新的状态丢失问题。
经过多次重构，解决了对话循环、幻觉和状态管理的核心问题。
最终版：基于用户提供的权威CKGSB ESG框架，并修复了所有已知bug。
"""

import logging
import asyncio
from typing import Dict, List, Tuple, Any, Optional
from datetime import datetime
import json

from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_chroma import Chroma

from app.core.config import settings
from app.core.llm_factory import llm_factory
from app.agents.base_agent import BaseAgent, AgentProcessingError
from app.bus import A2AMessage, MessageType
from app.utils import parse_llm_json_response
from app.models.conversation_state import ConversationState
from app.services.conversation_service import ConversationService
from app.db.session import SessionLocal
from app.vector_store.chroma_db import get_chroma_manager
from app.services.report_service import ReportService
from app.models.report import ReportCreate


logger = logging.getLogger(__name__)

class CompanyProfileAgent(BaseAgent):
    """
    一个AI Agent，通过动态的多轮对话来全面了解一家公司的ESG画像。
    核心逻辑基于用户提供的权威CKGSB ESG框架重构，确保对话流程清晰、有序、不重复。
    现在采用混合模式，兼顾智能对话与系统稳定性。
    """
    def __init__(self, agent_id: str):
        try:
            super().__init__(agent_id)
            self.agent_type = "CompanyProfileAgent"
            
            # 延迟初始化资源
            self.llm: Optional[ChatOpenAI] = None
            self.embeddings: Optional[OpenAIEmbeddings] = None
            self.vector_store: Optional[Chroma] = None
            self.retriever: Optional[Any] = None # as_retriever 的返回类型复杂，用Any
            
            # 初始化画像蓝图
            self.profile_framework = self._initialize_profile_framework()
            self._conversation_locks: Dict[str, asyncio.Lock] = {}

            # 初始化数据库会话和对话服务
            self.db_session = SessionLocal()
            self.conversation_service = ConversationService(self.db_session)
            self.report_service = ReportService(self.db_session)

            # 注册消息处理器
            self.register_handler("start_profile_generation", self.handle_start_profile_generation)
            self.register_handler("continue_conversation", self.handle_continue_conversation)
            self.register_handler("continue_profile_conversation", self.handle_continue_conversation)

        except Exception as e:
            raise AgentProcessingError(f"Failed to initialize CompanyProfileAgent: {e}", recoverable=False)

    # --- 资源延迟初始化方法 ---

    def _get_llm(self) -> ChatOpenAI:
        """延迟初始化并返回LLM实例 - 使用DeepSeek"""
        if self.llm is None:
            self.llm = llm_factory.create_deepseek_llm(
                temperature=0.2, 
                request_timeout=30,  # 30秒超时
                max_retries=1       # 最多重试1次
            )
        return self.llm

    def _get_embeddings(self) -> OpenAIEmbeddings:
        """延迟初始化并返回Embeddings实例 - 使用OpenAI embedding"""
        if self.embeddings is None:
            self.embeddings = llm_factory.create_embedding_model()
        return self.embeddings
        
    def _get_vector_store(self) -> Chroma:
        """延迟初始化并返回Vector Store实例"""
        if self.vector_store is None:
            chroma_manager = get_chroma_manager()
            self.vector_store = Chroma(
                client=chroma_manager.client,
                collection_name=chroma_manager.collection.name,
                embedding_function=self._get_embeddings(),
            )
        return self.vector_store

    def _get_retriever(self) -> Any:
        """延迟初始化并返回Retriever实例"""
        if self.retriever is None:
            self.retriever = self._get_vector_store().as_retriever(search_kwargs={"k": 3})
        return self.retriever

    # --- 核心处理逻辑 ---

    async def handle_start_profile_generation(self, message: A2AMessage) -> Dict[str, Any]:
        """处理开始画像生成的请求"""
        user_context = message.payload.get("user_context", {})
        company_name = user_context.get("company_name")
        initial_info = user_context.get("initial_info", {})
        conversation_id = message.conversation_id
        
        logger.info(f"开始为公司 '{company_name}' 生成画像, conversation_id: {conversation_id}")

        # 检查是否已存在对话
        conversation_state = await self._load_conversation_state(conversation_id)
        
        if not conversation_state:
            # 创建新的对话状态
            conversation_state = {
                "id": conversation_id,
                "conversation_id": conversation_id,
                "user_context": user_context,
                "status": "active",
                "stage": "initial",
                "extracted_info": initial_info,
                "messages": [],
                "final_report": None,
                "last_updated": datetime.now()
            }
            logger.info(f"为 {conversation_id} 创建了新的对话状态")

        # 添加用户初始信息到对话历史
        initial_message = f"你好，我想了解关于'{company_name}'的ESG情况。"
        if initial_info:
            initial_message += f" 已知信息：{initial_info}"
        
        conversation_state["messages"].append({
            "role": "user",
            "content": initial_message,
            "timestamp": datetime.now().isoformat(),
            "stage": "initial"
        })

        # 生成第一个问题
        next_question_data = await self._generate_next_question(conversation_state)
        
        if next_question_data and next_question_data.get("question"):
            ai_question = next_question_data["question"]
            conversation_state["stage"] = next_question_data.get("field_key", "initial")
            conversation_state["messages"].append({
                "role": "assistant",
                "content": ai_question,
                "timestamp": datetime.now().isoformat(),
                "stage": conversation_state["stage"]
            })
            await self._save_conversation_state(conversation_state)
            
            return {
                "type": "question",
                "question": ai_question,
                "conversation_id": conversation_id,
                "stage": conversation_state["stage"],
                "progress": self._calculate_progress(conversation_state),
                "next_action": "回答问题以继续"
            }
        
        # 如果无法生成第一个问题，则返回错误
        return {
            "type": "error",
            "conversation_id": conversation_id or "unknown",
            "question": None,
            "company_profile": None,
            "progress": "0%",
            "stage": "初始化错误",
            "next_action": "请重新尝试开始对话"
        }

    async def handle_continue_conversation(self, message: A2AMessage) -> Dict[str, Any]:
        """处理用户的连续回答 (混合模式)"""
        conversation_id = message.conversation_id
        user_response = message.payload.get("response", "")
        
        async with self._get_conversation_lock(conversation_id):
            conversation_state = await self._load_conversation_state(conversation_id)
            if not conversation_state:
                return {
                    "type": "error", "conversation_id": conversation_id or "unknown",
                    "question": None, "company_profile": None, "progress": "0%",
                    "stage": "对话不存在", "next_action": "请重新开始对话"
                }

            # 记录用户回答
            conversation_state["messages"].append({
                "role": "user", "content": user_response,
                "timestamp": datetime.now().isoformat(),
                "stage": conversation_state.get("stage", "unknown")
            })
            conversation_state["last_updated"] = datetime.now()
            
            # 获取上一轮AI提出的问题，以提供给信息提取模块上下文
            last_question_data = await self._get_last_question_data(conversation_state)
            
            # 2. 轻量级信息提取
            # 注意：这里我们只把当前问题和回答传给LLM，避免上下文过长
            last_question = conversation_state["messages"][-2][
                "content"
            ]  # 上上一条消息是Agent的问题
            
            fields_to_extract = self._get_fields_for_question(last_question_data["field_key"])
            
            extracted_data = await self._extract_information_with_llm(
                last_question, user_response, fields_to_extract
            )
            
            # 3. 更新提取到的信息
            if extracted_data:
                conversation_state["extracted_info"].update(extracted_data)

            # 4. 智能生成下一个问题或结束对话
            next_question_data = await self._generate_next_question(conversation_state)

            if not next_question_data.get("question"):
                logger.info(f"对话完成，准备触发报告生成流程: {conversation_id}")
                conversation_state["status"] = "completed"
                await self._save_conversation_state(conversation_state)

                # 1. 直接创建报告记录，拿到 report_id
                company_profile = conversation_state.get("extracted_info", {})
                company_name = company_profile.get("company_name", "Unknown Company")
                report_create = ReportCreate(
                    conversation_id=conversation_id,
                    company_name=company_name,
                    company_profile=company_profile
                )
                
                try:
                    db_report = self.report_service.create_report(report_create)
                    report_id = db_report.id
                    logger.info(f"为对话 {conversation_id} 创建了报告记录，ID: {report_id}")
                except Exception as e:
                    logger.error(f"创建报告记录失败: {e}")
                    # 返回错误，让前端知道报告流程未能启动
                    return {
                        "type": "error", "stage": "report_creation_failed",
                        "message": "无法创建报告记录，请联系管理员。"
                    }

                # 2. 向ESGReportAgent发送带有report_id的任务
                event_message = A2AMessage(
                    conversation_id=conversation_id,
                    from_agent=self.agent_id,
                    to_agent="ESGReportAgent",
                    message_type=MessageType.REQUEST,
                    action="generate_esg_report",
                    payload={
                        "report_id": report_id,
                        "company_profile": company_profile,
                        "assessment_results": company_profile 
                    }
                )
                await self.send_message(event_message)
                logger.info(f"已向 ESGReportAgent 发送生成报告任务，report_id: {report_id}")
                
                # 3. 向前端返回包含 report_id 的最终响应
                return {
                    "type": "completion", # 使用 'completion' 类型表示对话结束
                    "conversation_id": conversation_id,
                    "progress": "100%", 
                    "stage": "generating_report", # 新的状态，告诉前端下一步是等待报告
                    "message": "信息收集完毕，报告生成任务已启动。",
                    "report_id": report_id # <-- 将 report_id 返回给客户端！
                }

            # 需要继续提问
            ai_question = next_question_data["question"]
            conversation_state["stage"] = next_question_data.get("field_key", "synthesis")
            conversation_state["messages"].append({
                "role": "assistant", "content": ai_question, 
                "timestamp": datetime.now().isoformat(), "stage": conversation_state["stage"]
            })
            await self._save_conversation_state(conversation_state)

            return {
                "type": "question", "question": ai_question, "conversation_id": conversation_id,
                "stage": conversation_state["stage"], "progress": self._calculate_progress(conversation_state),
                "next_action": "回答问题以继续"
            }

    async def _get_last_question_data(self, conversation_state: Dict[str, Any]) -> Dict[str, str]:
        """从对话历史中找到最后一个AI提出的问题及其对应的field_key"""
        for msg in reversed(conversation_state["messages"]):
            if msg.get("role") == "assistant":
                return {
                    "question": msg.get("content", ""),
                    "field_key": msg.get("stage", "") # 我们用stage来记录field_key
                }
        return {}

    async def generate_and_save_profile(self, conversation_id: str):
        """后台任务实际执行体：加载状态、生成报告、保存报告"""
        logger.info(f"后台任务开始: 为 {conversation_id} 生成最终报告")
        
        async with self._get_conversation_lock(conversation_id):
            state_dict = await self._load_conversation_state(conversation_id)
            if not state_dict:
                logger.error(f"后台任务错误: 无法加载 {conversation_id} 的状态")
                return

            try:
                final_report = await self._generate_final_report_with_llm(state_dict)
                state_dict["final_report"] = final_report
                state_dict["status"] = "completed"
                state_dict["stage"] = "completed"
                logger.info(f"成功为 {conversation_id} 生成报告")
            except Exception as e:
                logger.error(f"Error generating report for {conversation_id}: {e}")
                state_dict["status"] = "error"
                state_dict["final_report"] = f"生成报告时发生错误: {e}"
            finally:
                await self._save_conversation_state(state_dict)

    async def _save_conversation_state(self, conversation_state: Dict[str, Any]):
        """使用ConversationService将当前对话状态持久化到数据库。"""
        logger.debug(f"Attempting to save state for conversation {conversation_state['conversation_id']}")
        try:
            self.conversation_service.save_state(conversation_state)
            logger.info(f"Successfully saved state for conversation {conversation_state['conversation_id']}")
        except Exception as e:
            logger.error(f"Failed to save conversation state for {conversation_state['conversation_id']}: {e}", exc_info=True)
            
    async def _load_conversation_state(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """使用ConversationService从数据库加载对话状态。"""
        logger.debug(f"Attempting to load state for conversation {conversation_id}")
        try:
            state = self.conversation_service.load_state(conversation_id)
            if state:
                logger.info(f"Successfully loaded state for conversation {conversation_id}")
                return state
            else:
                logger.warning(f"No state found in DB for conversation {conversation_id}")
                return None
        except Exception as e:
            logger.error(f"Failed to load conversation state for {conversation_id}: {e}", exc_info=True)
            return None

    def _initialize_profile_framework(self) -> Dict[str, Any]:
        """
        初始化企业画像的统一蓝图 (schema)。
        这是整个对话和信息收集的核心依据，严格按照用户提供的CKGSB ESG评估框架。
        """
        schema = {
            "E": {
                "description": "环境",
                "fields": {
                    "E1-1": "环境管理体系认证情况 (如ISO 14001)",
                    "E1-2": "年度环保总投入及占总收入比例",
                    "E1-3": "近三年环境相关的行政处罚记录",
                    "E2-1": "温室气体盘查与减排目标/行动",
                    "E2-2": "能源消耗总量及可再生能源使用比例",
                    "E3-1": "水资源消耗总量及循环利用/节水措施",
                    "E3-2": "废弃物产生总量及回收利用/减量化措施",
                    "E3-3": "污染物排放总量 (废水, 废气等) 及处理措施",
                }
            },
            "S": {
                "description": "社会",
                "fields": {
                    "S1-1": "员工健康与安全管理体系认证 (如ISO 45001)",
                    "S1-2": "近三年工伤事故发生情况 (如千人负伤率)",
                    "S1-3": "员工培训总时长和人均时长",
                    "S2-1": "供应链ESG准则及供应商筛选/审核机制",
                    "S2-2": "本地采购比例",
                    "S2-3": "关键供应商ESG风险评估情况",
                    "S3-1": "产品质量管理体系认证 (如ISO 9001)",
                    "S3-2": "客户投诉数量及处理满意度",
                    "S4-1": "年度公益捐赠总额",
                    "S4-2": "员工志愿服务总时长",
                }
            },
            "G": {
                "description": "治理",
                "fields": {
                    "G1-1": "股权结构特点 (如第一大股东持股比例, 是否有实际控制人)",
                    "G1-2": "董事会成员构成 (独立董事比例, 女性董事比例)",
                    "G1-3": "董事会下设委员会情况 (如审计, 薪酬, 提名委员会)",
                    "G2-1": "反腐败/反商业贿赂制度及培训情况",
                    "G2-2": "内部举报机制及处理流程",
                    "G3-1": "信息安全管理体系认证 (如ISO 27001)",
                    "G3-2": "数据隐私保护政策及用户数据安全措施",
                }
            }
        }
        
        all_fields = []
        for _, category_data in schema.items():
            fields = category_data.get("fields", {})
            for field_key, field_desc in fields.items():
                all_fields.append({"key": field_key, "description": field_desc})

        return {"schema": schema, "all_fields": all_fields}

    def _get_fields_for_question(self, field_key: str) -> List[Dict[str, str]]:
        """
        根据给定的field_key，从框架中查找并返回对应的字段信息。
        """
        for field in self.profile_framework.get("all_fields", []):
            if field.get("key") == field_key:
                return [field]  # 返回一个列表，因为_extract_information_with_llm期望的是列表
        return []

    async def _extract_information_with_llm(self, last_question: str, user_response: str, fields_to_extract: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        混合模式：轻量级信息提取。
        只基于"上一个问题"和"当前回答"进行提取，但会尝试关联到整个ESG框架，以捕获用户"顺便"提供的信息。
        """
        prompt = f"""
        **任务**: 从用户的回答中，精准提取与给定ESG指标相关的一个或多个关键信息。

        **上下文**:
        - 我刚刚问了用户关于: "{last_question}"
        - 这个问题主要关联以下ESG指标:
          ```json
          {json.dumps(fields_to_extract, indent=2, ensure_ascii=False)}
          ```
        - 用户的回答是: "{user_response}"

        **你的职责**:
        1.  仔细阅读用户的回答。
        2.  根据回答内容，填充你认为已经被回答的指标的值。
        3.  **【关键规则】如果用户的回答没有提供有效信息、明确表示否定、或说"没有"、"不知道"，请将对应指标的值设为 `null` 或 `'N/A'`。不要留空！**
        4.  检查用户的回答是否"顺便"提供了其他相关指标的信息。如果有，也一并提取。
        5.  以严格的JSON格式返回结果，key为指标ID，value为提取到的信息。如果提取不到任何信息，则返回一个空JSON对象 `{{}}`。

        **输出格式示例**:
        ```json
        {{
          "E1-1": "已通过ISO 14001认证",
          "E1-2": "年度环保投入约500万元"
        }}
        ```
        """
        try:
            llm = self._get_llm()
            response = await llm.ainvoke([SystemMessage(content=prompt)])
            return parse_llm_json_response(response.content)
        except Exception as e:
            logger.error(f"Error extracting information with hybrid model: {e}")
            return {}

    async def _generate_next_question(self, conversation_state: Dict[str, Any]) -> Dict[str, str]:
        """
        混合模式：智能生成下一个问题。
        基于已提取的"信息摘要"，而不是完整的对话历史。
        """
        extracted_info = conversation_state.get("extracted_info", {})
        all_fields = self.profile_framework["all_fields"]

        # 找到第一个未被覆盖的字段
        next_field = None
        for field in all_fields:
            if field["key"] not in extracted_info:
                next_field = field
                break
        
        if not next_field:
            return {} # 所有信息已收集完毕

        next_field_key = next_field["key"]
        next_field_description = next_field["description"]

        # 找到这个字段属于哪个大类 (E, S, G)
        dimension_description = ""
        for dim, cat in self.profile_framework["schema"].items():
            if next_field_key in cat["fields"]:
                dimension_description = cat["description"]
                break

        # 用简洁的摘要作为上下文
        summary_context = f"目前已了解到的信息摘要：{extracted_info}"

        prompt = f"""
        **任务**: 基于已有的信息摘要，为下一个ESG评估指标生成一个清晰、自然、承上启下的问题。

        **上下文**:
        - 我正在与用户对话了解其公司的ESG情况。
        - {summary_context}
        - 我需要了解的下一个具体指标是: `{next_field_key}` - {next_field_description}
        - 这个指标属于大的分类: {dimension_description}
        
        **你的职责**:
        1.  基于需要了解的新指标 (`{next_field_key}`)，构思一个问题。
        2.  问题应自然、易于理解，并且最好能与已知信息摘要建立联系，实现流畅的过渡。
        3.  不要重复提问摘要中已有的信息。
        4.  返回一个只包含问题的JSON对象。

        **输出格式**: `"{{"question": "你的问题"}}"`

        **示例**:
        - 摘要: `{{"E1-1": "无", "E1-2": "年度环保总投入500万"}}`
        - 下一个指标: `E1-3`
        """
        try:
            llm = self._get_llm()
            response = await llm.ainvoke([SystemMessage(content=prompt)])
            result = parse_llm_json_response(response.content)
            
            # 确保返回格式正确
            if isinstance(result, dict) and "question" in result:
                return {
                    "question": result["question"],
                    "field_key": next_field_key
                }
            else:
                # 如果LLM返回格式不正确，生成一个默认问题
                return {
                    "question": f"请介绍一下您公司的{next_field_description}情况。",
                    "field_key": next_field_key
                }
        except Exception as e:
            logger.error(f"Error generating next question: {e}")
            # 返回一个默认问题
            return {
                "question": f"请介绍一下您公司的{next_field_description}情况。",
                "field_key": next_field_key
            }

    def _calculate_progress(self, conversation_state: Dict[str, Any]) -> str:
        """根据已提取信息的字段数量计算进度。"""
        extracted_info = conversation_state.get("extracted_info", {})
        all_fields_count = len(self.profile_framework.get("all_fields", []))
        if all_fields_count == 0:
            return "0%"
        
        covered_fields_count = len(extracted_info)
        progress = (covered_fields_count / all_fields_count) * 100
        return f"{int(progress)}%"

    async def _generate_final_report_with_llm(self, conversation_state: Dict[str, Any]) -> str:
        """
        使用LLM基于收集到的所有信息生成最终的ESG画像报告。
        """
        company_name = conversation_state.get("user_context", {}).get("company_name", "该公司")
        extracted_info = conversation_state.get("extracted_info", {})
        
        prompt = f"""
        **任务**: 基于以下收集到的关于 '{company_name}' 的ESG信息，撰写一份专业、结构清晰的初步ESG画像报告。

        **信息清单**:
        ```json
        {json.dumps(extracted_info, indent=2, ensure_ascii=False)}
        ```

        **报告要求**:
        1.  **结构化**: 报告必须分为"环境(E)"、"社会(S)"、"治理(G)"三大章节。
        2.  **专业性**: 使用专业、客观的商业报告语言。
        3.  **完整性**: 报告应覆盖信息清单中的所有要点。对于值为"无"或"不适用"的项，也应在报告中恰当提及，以体现评估的全面性。
        4.  **可读性**: 使用Markdown格式，包括标题、列表等，以增强可读性。
        5.  **总结与建议**: 在报告结尾，给出一个简短的总体评估，并可以提出1-2个初步的、高层次的改进建议。

        **输出格式**: 直接输出Markdown格式的报告全文。
        """
        llm = self._get_llm()
        response = await llm.ainvoke([SystemMessage(content=prompt)])
        return response.content

    def _get_conversation_lock(self, conversation_id: str) -> asyncio.Lock:
        """获取或创建特定对话的锁，防止并发访问问题。"""
        if conversation_id not in self._conversation_locks:
            self._conversation_locks[conversation_id] = asyncio.Lock()
        return self._conversation_locks[conversation_id]

    async def initialize(self) -> bool:
        """
        初始化Agent - BaseAgent要求的抽象方法实现
        """
        # ... (implementation)
        return True

    async def cleanup(self) -> None:
        """
        清理Agent资源 - BaseAgent要求的抽象方法实现
        """
        # ... (implementation)
        pass