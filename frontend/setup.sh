#!/bin/bash

# ESG-Copilot 前端项目快速启动脚本

echo "🚀 ESG-Copilot 前端项目启动脚本"
echo "=================================="

# 检查 Node.js 环境
if ! command -v node &> /dev/null; then
    echo "❌ 错误: 未找到 Node.js，请先安装 Node.js (>=18.0.0)"
    echo "📥 下载地址: https://nodejs.org/"
    exit 1
fi

# 检查 Node.js 版本
NODE_VERSION=$(node -v | cut -d'v' -f2)
REQUIRED_VERSION="18.0.0"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$NODE_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo "❌ 错误: Node.js 版本过低 (当前: $NODE_VERSION, 要求: >= $REQUIRED_VERSION)"
    exit 1
fi

echo "✅ Node.js 版本检查通过: v$NODE_VERSION"

# 检查包管理器
if command -v yarn &> /dev/null; then
    PACKAGE_MANAGER="yarn"
    echo "📦 检测到 Yarn 包管理器"
elif command -v npm &> /dev/null; then
    PACKAGE_MANAGER="npm"
    echo "📦 使用 NPM 包管理器"
else
    echo "❌ 错误: 未找到包管理器"
    exit 1
fi

# 安装依赖
echo ""
echo "📥 正在安装依赖..."
if [ "$PACKAGE_MANAGER" = "yarn" ]; then
    yarn install
else
    npm install
fi

if [ $? -ne 0 ]; then
    echo "❌ 依赖安装失败"
    exit 1
fi

echo "✅ 依赖安装完成"

# 创建环境变量文件
if [ ! -f ".env.local" ]; then
    echo ""
    echo "⚙️  创建环境变量文件..."
    cat > .env.local << EOF
# ESG-Copilot 前端环境变量配置

# API服务器地址
VITE_API_URL=http://localhost:8000

# WebSocket服务器地址  
VITE_WS_URL=ws://localhost:8000

# 应用版本
VITE_APP_VERSION=1.0.0

# 开发模式
VITE_DEV_MODE=true
EOF
    echo "✅ 环境变量文件创建完成: .env.local"
else
    echo "⚙️  环境变量文件已存在: .env.local"
fi

# 显示启动信息
echo ""
echo "🎉 项目设置完成！"
echo ""
echo "📋 可用命令:"
echo "  启动开发服务器:  $PACKAGE_MANAGER run dev"
echo "  构建生产版本:    $PACKAGE_MANAGER run build"
echo "  运行测试:        $PACKAGE_MANAGER run test"
echo "  代码检查:        $PACKAGE_MANAGER run lint"
echo ""

# 询问是否立即启动开发服务器
read -p "🚀 是否立即启动开发服务器? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🌟 启动开发服务器..."
    if [ "$PACKAGE_MANAGER" = "yarn" ]; then
        yarn dev
    else
        npm run dev
    fi
else
    echo "💡 使用 '$PACKAGE_MANAGER run dev' 启动开发服务器"
    echo "📖 查看 README.md 了解更多信息"
fi
 