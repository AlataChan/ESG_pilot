# ESG Pilot - 企业ESG评估与管理系统

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104.1-009688.svg?style=flat&logo=FastAPI)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18.2.0-61DAFB.svg?style=flat&logo=React)](https://reactjs.org)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0.2-3178C6.svg?style=flat&logo=TypeScript)](https://www.typescriptlang.org)
[![Python](https://img.shields.io/badge/Python-3.12-3776AB.svg?style=flat&logo=Python)](https://www.python.org)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED)](https://www.docker.com)

## 📖 项目简介

ESG Pilot 是一个基于人工智能的企业环境、社会和治理（ESG）评估与管理系统。通过集成先进的AI技术，为企业提供智能化的ESG数据分析、报告生成、企业档案构建和决策支持服务。

### 🌟 核心功能

- **🤖 智能分析**: 基于DeepSeek AI的ESG数据分析和洞察
- **📚 知识库管理**: 文档上传、分类和智能检索
- **🔍 智能问答**: RAG技术驱动的专业ESG咨询
- **🏢 企业档案**: 自动化企业ESG档案生成和管理
- **📊 ESG评估**: 全面的ESG表现评估和可视化
- **📋 报告生成**: 自动化ESG报告和合规文档生成
- **💬 对话式交互**: 自然语言交互的ESG管理助手
- **📈 实时监控**: ESG指标实时监控和预警

## 🏗️ 技术架构

### 后端技术栈
- **框架**: FastAPI + Uvicorn
- **数据库**: PostgreSQL + ChromaDB (向量数据库)
- **AI集成**: DeepSeek Reasoner + OpenAI Embeddings + LangChain
- **ORM**: SQLAlchemy + Alembic
- **文档处理**: PyPDF + ReportLab + python-docx + openpyxl

### 前端技术栈
- **框架**: React 18 + TypeScript
- **构建工具**: Vite
- **状态管理**: Zustand
- **UI框架**: Tailwind CSS + Headless UI
- **路由**: React Router v6
- **HTTP客户端**: Axios + SWR

### 开发工具
- **容器化**: Docker + Docker Compose
- **代码质量**: ESLint + Prettier
- **测试**: Pytest + Vitest
- **API文档**: OpenAPI/Swagger

## 📁 项目结构

```
ESG_pilot/
├── backend/                    # 后端服务
│   ├── app/
│   │   ├── api/v1/            # API路由 (v1版本)
│   │   ├── services/          # 业务逻辑层
│   │   ├── models/            # 数据模型
│   │   ├── core/             # 核心配置
│   │   ├── agents/           # AI Agent
│   │   ├── vector_store/     # 向量数据库
│   │   └── main.py           # 应用入口
│   ├── alembic/              # 数据库迁移
│   ├── requirements.txt      # Python依赖
│   └── logs/                 # 日志文件
├── frontend/                  # 前端应用
│   ├── src/
│   │   ├── components/       # React组件
│   │   ├── pages/           # 页面组件
│   │   ├── types/           # TypeScript类型
│   │   ├── services/        # API服务
│   │   └── App.tsx          # 应用入口
│   ├── package.json         # Node.js依赖
│   └── vite.config.ts       # Vite配置
├── tests/                    # 测试文件
├── docs/                     # 项目文档
├── docker-compose.yml        # Docker编排
├── LICENSE                   # Apache 2.0许可证
└── README.md                # 项目说明
```

## 🚀 快速开始

### 环境要求

- **Python**: 3.12+
- **Node.js**: 16+
- **Docker**: 20+ (推荐)

### 1. 克隆项目

```bash
git clone <repository-url>
cd ESG_pilot
```

### 2. 环境配置

创建环境配置文件：

```bash
cp .env.example .env
```

编辑 `.env` 文件，配置必要的环境变量：

```env
# DeepSeek AI配置
DEEPSEEK_API_KEY=your_deepseek_api_key_here
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-reasoner

# OpenAI配置（用于Embedding）
OPENAI_API_KEY=your_openai_api_key_here

# 数据库配置
POSTGRES_SERVER=localhost
POSTGRES_PORT=5432
POSTGRES_USER=esg_user
POSTGRES_PASSWORD=esg_password
POSTGRES_DB=esg_db

# ChromaDB配置
CHROMA_DB_HOST=localhost
CHROMA_DB_PORT=8000

# 系统配置
LOG_LEVEL=INFO
DEBUG=True
```

### 3. 使用Docker快速启动（推荐）

```bash
# 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

服务访问地址：
- **前端应用**: http://localhost:3000
- **后端API**: http://localhost:8000
- **API文档**: http://localhost:8000/docs

### 4. 手动启动（开发环境）

#### 启动后端

```bash
cd backend

# 安装依赖
pip install -r requirements.txt

# 启动服务
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### 启动前端

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

## 📚 API文档

### 主要API端点

#### 知识库管理
```http
GET    /api/v1/categories              # 获取分类列表
POST   /api/v1/categories              # 创建新分类
GET    /api/v1/documents               # 获取文档列表
POST   /api/v1/documents/upload        # 上传文档
DELETE /api/v1/documents/{document_id} # 删除文档
```

#### RAG问答系统
```http
POST   /api/v1/rag/ask                 # 通用问答
POST   /api/v1/rag/ask-document        # 基于特定文档问答
GET    /api/v1/rag/conversation-history/{user_id} # 获取对话历史
GET    /api/v1/rag/question-suggestions/{user_id} # 获取问题建议
```

#### 企业档案系统
```http
POST   /api/v1/agents/profile/start    # 开始企业档案生成
POST   /api/v1/agents/profile/message  # 发送消息
GET    /api/v1/agents/profile/status   # 获取档案状态
```

#### ESG评估系统
```http
POST   /api/v1/assessment/start        # 开始ESG评估
GET    /api/v1/assessment/report       # 获取评估报告
GET    /api/v1/assessment/dashboard    # 获取Dashboard数据
```

### API响应格式

所有API响应遵循统一格式：

```json
{
  "success": true,
  "data": {
    // 实际数据
  },
  "message": "操作成功",
  "code": 200
}
```

## 🔧 开发指南

### 本地开发

1. **环境准备**
   - 安装Python 3.12+
   - 安装Node.js 16+
   - 安装PostgreSQL
   - 配置环境变量

2. **数据库迁移**
   ```bash
   cd backend
   alembic upgrade head
   ```

3. **启动开发服务器**
   ```bash
   # 后端
   uvicorn app.main:app --reload
   
   # 前端
   cd frontend && npm run dev
   ```

### 部署生产环境

请参考 `DOCKER_DEPLOYMENT.md` 文件中的详细部署说明。

## 🧪 测试

### 运行后端测试

```bash
cd backend
python -m pytest tests/ -v
```

### 运行前端测试

```bash
cd frontend
npm run test
```

## 📄 许可证

本项目采用 Apache License 2.0 许可证 - 详情请参阅 [LICENSE](LICENSE) 文件。

## 🤝 贡献

欢迎提交 Issues 和 Pull Requests！

1. Fork 本项目
2. 创建您的特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交您的更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开一个 Pull Request

## 📞 联系我们

如果您有任何问题或建议，请通过以下方式联系我们：

- 项目Issues: [GitHub Issues](https://github.com/your-username/ESG_pilot/issues)
- 邮箱: your-email@example.com

## 🔄 更新日志

### v1.0.0 (2025-01-25)
- ✨ 基于DeepSeek AI的ESG评估系统
- 🏢 企业档案自动生成功能
- 📊 ESG Dashboard和可视化
- 🤖 智能问答和RAG系统
- 📋 自动化报告生成
- 🐳 Docker容器化部署
- 🔒 Apache 2.0开源许可证

---

**ESG Pilot** - 让企业ESG管理更智能、更高效！ 