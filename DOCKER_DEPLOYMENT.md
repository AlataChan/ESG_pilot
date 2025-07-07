# ESG Copilot Docker 统一部署指南

## 概述

本项目现已支持前后端统一的 Docker 部署方案，可以通过一个命令完成整个应用的部署。

## 架构说明

### 服务组件
- **PostgreSQL**: 主数据库 (端口: 5432)
- **ChromaDB**: 向量数据库 (端口: 8001)
- **Backend**: FastAPI 后端服务 (端口: 8000)
- **Frontend**: React 前端应用 (端口: 3000)

### 服务依赖关系
```
Frontend (Nginx) → Backend (FastAPI) → Database (PostgreSQL + ChromaDB)
```

## 快速开始

### 1. 环境准备

确保已安装以下软件：
- Docker (>= 20.10)
- Docker Compose (>= 2.0)

### 2. 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑配置文件
vim .env  # 或使用其他编辑器
```

**必须配置的环境变量：**
```bash
# OpenAI API 密钥
OPENAI_API_KEY="your_openai_api_key_here"

# 数据库密码（建议修改默认密码）
POSTGRES_PASSWORD="your_secure_password"
```

### 3. 一键部署

#### 开发模式（前台运行，显示日志）
```bash
./deploy.sh dev
```

#### 生产模式（后台运行）
```bash
./deploy.sh prod
```

### 4. 访问应用

部署完成后，可以通过以下地址访问：

- **前端应用**: http://localhost:3000
- **后端API**: http://localhost:8000
- **API文档**: http://localhost:8000/docs
- **ChromaDB**: http://localhost:8001

## 手动部署

如果不使用部署脚本，也可以手动执行：

```bash
# 构建并启动所有服务
docker-compose up --build -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

## 管理命令

### 查看服务状态
```bash
docker-compose ps
```

### 查看日志
```bash
# 查看所有服务日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f frontend
docker-compose logs -f backend
docker-compose logs -f db
docker-compose logs -f chroma
```

### 重启服务
```bash
# 重启所有服务
docker-compose restart

# 重启特定服务
docker-compose restart frontend
```

### 停止服务
```bash
# 停止所有服务
docker-compose down

# 停止并删除数据卷（谨慎使用）
docker-compose down -v
```

### 更新代码后重新部署
```bash
# 重新构建并启动
docker-compose up --build -d
```

## 故障排除

### 常见问题

1. **端口冲突**
   - 确保端口 3000, 8000, 8001, 5432 未被其他应用占用
   - 可以在 `docker-compose.yml` 中修改端口映射

2. **环境变量未设置**
   - 检查 `.env` 文件是否存在且配置正确
   - 确保 `OPENAI_API_KEY` 已正确设置

3. **数据库连接失败**
   - 等待数据库完全启动（通常需要 30-60 秒）
   - 检查数据库密码配置

4. **前端无法访问后端**
   - 检查 Nginx 配置中的代理设置
   - 确保后端服务健康检查通过

### 健康检查

```bash
# 检查所有服务健康状态
docker-compose ps

# 测试后端API
curl http://localhost:8000/health

# 测试前端
curl http://localhost:3000

# 测试ChromaDB
curl http://localhost:8001/api/v1/heartbeat
```

### 清理和重置

```bash
# 完全清理（删除容器、镜像、数据卷）
docker-compose down -v --rmi all
docker system prune -f

# 重新部署
./deploy.sh prod
```

## 生产环境建议

### 安全配置
1. **修改默认密码**: 更改数据库和其他服务的默认密码
2. **API密钥管理**: 使用安全的方式管理 OpenAI API 密钥
3. **网络隔离**: 考虑使用 Docker 网络隔离服务
4. **HTTPS配置**: 在生产环境中配置 SSL/TLS

### 性能优化
1. **资源限制**: 在 `docker-compose.yml` 中设置内存和CPU限制
2. **数据持久化**: 确保数据卷正确配置
3. **日志管理**: 配置日志轮转和清理策略

### 监控和备份
1. **健康检查**: 定期检查服务健康状态
2. **数据备份**: 定期备份 PostgreSQL 和 ChromaDB 数据
3. **监控告警**: 配置服务监控和告警机制

## 开发模式

开发模式下，后端代码支持热重载：

```bash
# 开发模式启动
docker-compose up --build

# 修改后端代码后，服务会自动重启
# 修改前端代码需要重新构建镜像
docker-compose build frontend
docker-compose up -d frontend
```

## 技术栈

- **前端**: React + TypeScript + Vite + Tailwind CSS
- **后端**: FastAPI + Python + SQLAlchemy
- **数据库**: PostgreSQL + ChromaDB
- **部署**: Docker + Docker Compose + Nginx

## 支持

如遇到问题，请检查：
1. Docker 和 Docker Compose 版本
2. 环境变量配置
3. 端口占用情况
4. 服务日志输出

更多技术支持，请参考项目文档或提交 Issue。