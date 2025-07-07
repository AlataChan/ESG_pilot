# ESG-Copilot 前端应用

ESG-Copilot 的前端应用，基于 React 18 + TypeScript + Vite 构建的现代化 Web 应用。

## 🚀 快速开始

### 环境要求

- Node.js >= 18.0.0
- npm >= 8.0.0 或 yarn >= 1.22.0

### 安装依赖

```bash
# 使用 npm
npm install

# 或使用 yarn
yarn install
```

### 启动开发服务器

```bash
# 使用 npm
npm run dev

# 或使用 yarn  
yarn dev
```

应用将在 `http://localhost:3000` 启动。

### 构建生产版本

```bash
# 使用 npm
npm run build

# 或使用 yarn
yarn build
```

## 📁 项目结构

```
frontend/
├── src/
│   ├── components/          # 可复用组件
│   │   ├── ui/             # UI基础组件
│   │   ├── chat/           # 聊天相关组件
│   │   └── layout/         # 布局组件
│   ├── pages/              # 页面组件
│   │   ├── Home.tsx        # 首页
│   │   ├── Profile.tsx     # 企业画像页面
│   │   ├── Dashboard.tsx   # 仪表板页面
│   │   └── Results.tsx     # 结果页面
│   ├── services/           # API服务层
│   │   └── api.ts          # API客户端
│   ├── stores/             # 状态管理
│   │   └── appStore.ts     # 应用状态
│   ├── types/              # TypeScript类型定义
│   │   └── index.ts        # 类型导出
│   ├── styles/             # 样式文件
│   │   └── globals.css     # 全局样式
│   ├── main.tsx            # 应用入口
│   └── App.tsx             # 根组件
├── public/                 # 静态资源
├── package.json            # 项目配置
├── tsconfig.json           # TypeScript配置
├── vite.config.ts          # Vite配置
├── tailwind.config.js      # Tailwind CSS配置
└── postcss.config.js       # PostCSS配置
```

## 🛠 技术栈

### 核心框架
- **React 18** - 前端框架
- **TypeScript** - 类型安全
- **Vite** - 构建工具

### 路由和状态管理
- **React Router v6** - 路由管理
- **Zustand** - 状态管理

### UI和样式
- **Tailwind CSS** - 样式框架
- **Headless UI** - 无样式UI组件
- **Heroicons** - 图标库
- **Framer Motion** - 动画库

### 数据获取
- **Axios** - HTTP客户端
- **SWR** - 数据获取和缓存

### 可视化
- **Recharts** - 图表库

### 开发工具
- **ESLint** - 代码检查
- **Prettier** - 代码格式化
- **Vitest** - 单元测试

## 🎨 设计系统

### 主题色彩

- **主色调 (绿色系)**: 可持续发展主题
  - Primary Green: `#00D084`
  - Green Dark: `#00B574`
  - Green Light: `#E8F8F3`

- **辅助色 (黄色系)**: 希望与活力
  - Secondary Yellow: `#FFD60A`
  - Yellow Dark: `#FFC300`
  - Yellow Light: `#FFF8E1`

### 组件规范

所有UI组件遵循统一的设计规范：
- 使用 Tailwind CSS 类名
- 支持暗色模式
- 响应式设计
- 无障碍支持

## 🔧 开发指南

### 代码规范

- 使用 TypeScript 严格模式
- 组件使用函数式组件 + Hooks
- 遵循 React 最佳实践
- 使用 JSDoc 注释

### 状态管理

使用 Zustand 进行状态管理：
- 全局状态：用户信息、主题、UI状态
- 局部状态：组件内部状态
- 异步状态：API请求状态

### API集成

- 统一的API客户端
- 错误处理
- 请求/响应拦截器
- 类型安全的接口定义

## 🧪 测试

```bash
# 运行测试
npm run test

# 运行测试并生成覆盖率报告
npm run test:coverage

# 启动测试UI
npm run test:ui
```

## 📦 部署

### 构建

```bash
npm run build
```

构建产物将生成在 `dist/` 目录中。

### 环境变量

创建 `.env.local` 文件配置环境变量：

```env
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
```

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支：`git checkout -b feature/new-feature`
3. 提交更改：`git commit -m 'Add new feature'`
4. 推送分支：`git push origin feature/new-feature`
5. 提交 Pull Request

## 📄 许可证

本项目采用 MIT 许可证。 