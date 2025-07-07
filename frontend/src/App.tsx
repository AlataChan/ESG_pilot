/**
 * ESG-Copilot 主应用组件
 * 包含路由配置、错误边界和全局状态管理
 * 针对1440*900分辨率优化
 */

import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { ErrorBoundary } from 'react-error-boundary';

// Pages
import HomePage from './pages/Home';
import ProfilePage from './pages/Profile';
import KnowledgeManagementPage from './pages/KnowledgeManagement';
import DashboardPage from './pages/Dashboard';
import ReportsPage from './pages/Reports';
import ResultsPage from './pages/Results';

// Components
import ErrorFallback from './components/ErrorFallback';
import { Header } from './components/layout/Header';

/**
 * 错误处理函数
 */
const handleError = (error: Error, errorInfo: any) => {
  console.error('Application error:', error, errorInfo);
  // 这里可以添加错误上报逻辑
};

/**
 * 主应用组件
 */
const App: React.FC = () => {
  return (
    <ErrorBoundary
      FallbackComponent={ErrorFallback}
      onError={handleError}
    >
      <div className="min-h-screen bg-gradient-hero optimized-1440-900">
        {/* 全局头部导航 - 1440*900优化 */}
        <Header />
        
        {/* 主要内容区域 - 适配1440*900 */}
        <main className="layout-1440">
          <Routes>
            {/* 首页 */}
            <Route path="/" element={<HomePage />} />
            
            {/* 企业画像页面 */}
            <Route path="/profile" element={<ProfilePage />} />
            
            {/* 知识库管理页面 */}
            <Route path="/knowledge" element={<KnowledgeManagementPage />} />
            
            {/* 仪表板页面 */}
            <Route path="/dashboard" element={<DashboardPage />} />
            
            {/* 报告页面 */}
            <Route path="/reports" element={<ReportsPage />} />
            
            {/* 结果页面 */}
            <Route path="/results" element={<ResultsPage />} />
          </Routes>
        </main>
      </div>
    </ErrorBoundary>
  );
};

export default App;