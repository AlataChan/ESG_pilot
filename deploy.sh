#!/bin/bash

# ESG Copilot 一键部署脚本
# 使用方法: ./deploy.sh [dev|prod]

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查环境
check_requirements() {
    print_info "检查部署环境..."
    
    # 检查Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker 未安装，请先安装 Docker"
        exit 1
    fi
    
    # 检查Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose 未安装，请先安装 Docker Compose"
        exit 1
    fi
    
    # 检查.env文件
    if [ ! -f ".env" ]; then
        print_warning ".env 文件不存在，正在从 .env.example 创建..."
        if [ -f ".env.example" ]; then
            cp .env.example .env
            print_warning "请编辑 .env 文件，填入正确的配置信息"
            print_warning "特别注意：请设置正确的 OPENAI_API_KEY 和数据库密码"
            read -p "按回车键继续部署，或按 Ctrl+C 退出编辑配置..."
        else
            print_error ".env.example 文件不存在，无法创建配置文件"
            exit 1
        fi
    fi
    
    print_success "环境检查完成"
}

# 清理旧容器和镜像
cleanup() {
    print_info "清理旧的容器和镜像..."
    
    # 停止并删除容器
    docker-compose down --remove-orphans 2>/dev/null || true
    
    # 删除悬空镜像
    docker image prune -f 2>/dev/null || true
    
    print_success "清理完成"
}

# 构建和启动服务
deploy() {
    local mode=${1:-"dev"}
    
    print_info "开始部署 ESG Copilot (模式: $mode)..."
    
    if [ "$mode" = "prod" ]; then
        print_info "生产模式部署..."
        docker-compose up --build -d
    else
        print_info "开发模式部署..."
        docker-compose up --build
    fi
}

# 检查服务状态
check_services() {
    print_info "检查服务状态..."
    
    sleep 10  # 等待服务启动
    
    # 检查数据库
    if docker-compose exec -T db pg_isready -U esg_user -d esg_db &>/dev/null; then
        print_success "PostgreSQL 数据库运行正常"
    else
        print_error "PostgreSQL 数据库连接失败"
    fi
    
    # 检查ChromaDB
    if curl -f http://localhost:8001/api/v1/heartbeat &>/dev/null; then
        print_success "ChromaDB 运行正常"
    else
        print_error "ChromaDB 连接失败"
    fi
    
    # 检查后端API
    if curl -f http://localhost:8000/health &>/dev/null; then
        print_success "后端API 运行正常"
    else
        print_error "后端API 连接失败"
    fi
    
    # 检查前端
    if curl -f http://localhost:3000 &>/dev/null; then
        print_success "前端应用运行正常"
    else
        print_error "前端应用连接失败"
    fi
}

# 显示访问信息
show_access_info() {
    print_success "=== ESG Copilot 部署完成 ==="
    echo
    print_info "访问地址:"
    echo "  前端应用: http://localhost:3000"
    echo "  后端API:  http://localhost:8000"
    echo "  API文档:  http://localhost:8000/docs"
    echo "  ChromaDB: http://localhost:8001"
    echo
    print_info "管理命令:"
    echo "  查看日志: docker-compose logs -f"
    echo "  停止服务: docker-compose down"
    echo "  重启服务: docker-compose restart"
    echo
}

# 主函数
main() {
    local mode=${1:-"dev"}
    
    if [ "$mode" != "dev" ] && [ "$mode" != "prod" ]; then
        print_error "无效的部署模式: $mode"
        echo "使用方法: $0 [dev|prod]"
        exit 1
    fi
    
    print_info "开始 ESG Copilot 部署流程..."
    
    check_requirements
    cleanup
    deploy "$mode"
    
    if [ "$mode" = "prod" ]; then
        check_services
        show_access_info
    fi
    
    print_success "部署流程完成！"
}

# 执行主函数
main "$@"