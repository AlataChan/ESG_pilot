/**
 * Header 导航组件
 * 提供全局导航、用户状态显示和快速操作
 * 针对1440*900分辨率优化
 */

import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Button } from '../ui/Button';

/**
 * 导航项接口
 */
interface NavItem {
  path: string;
  label: string;
  icon: string;
}

/**
 * 导航项配置
 */
const navItems: NavItem[] = [
  { path: '/', label: '首页', icon: '🏠' },
  { path: '/dashboard', label: '控制台', icon: '📊' },
  { path: '/profile', label: '企业画像', icon: '🤖' },
  { path: '/knowledge', label: '知识库', icon: '📚' },
  { path: '/reports', label: '报告', icon: '📋' },
  { path: '/results', label: 'ESG看板', icon: '📈' },
];

/**
 * Header 组件
 */
export const Header: React.FC = () => {
  const location = useLocation();

  const isActivePath = (path: string) => {
    if (path === '/') {
      return location.pathname === '/';
    }
    return location.pathname.startsWith(path);
  };

  return (
    <header className="bg-white border-b border-neutral-200 sticky top-0 z-50 optimized-1440-900">
      <div className="layout-1440">
        <div className="flex items-center justify-between h-14 2xl:h-16 px-4 2xl:px-6">
          {/* Logo 和品牌 - 1440*900优化 */}
          <div className="flex items-center space-x-3 2xl:space-x-4">
            <Link 
              to="/" 
              className="flex items-center space-x-2 2xl:space-x-3 hover:opacity-80 transition-opacity"
            >
              <div className="w-8 h-8 2xl:w-10 2xl:h-10 bg-gradient-primary rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-sm 2xl:text-base">ESG</span>
              </div>
              <div>
                <h1 className="text-lg 2xl:text-xl font-bold text-neutral-900">
                  ESG-Copilot
                </h1>
                <p className="text-xs text-neutral-500 hidden sm:block">
                  智能可持续发展管理
                </p>
              </div>
            </Link>
          </div>

          {/* 导航菜单 - 1440*900优化 */}
          <nav className="hidden md:flex items-center space-x-1 2xl:space-x-2">
            {navItems.map((item) => (
              <Link
                key={item.path}
                to={item.path}
                className={`
                  flex items-center space-x-2 px-3 2xl:px-4 py-2 rounded-lg text-sm 2xl:text-base font-medium transition-all duration-200
                  ${isActivePath(item.path)
                    ? 'bg-primary-green text-white shadow-sm'
                    : 'text-neutral-600 hover:text-neutral-900 hover:bg-neutral-50'
                  }
                `}
              >
                <span className="text-sm 2xl:text-base">{item.icon}</span>
                <span>{item.label}</span>
              </Link>
            ))}
          </nav>

          {/* 右侧操作区 - 1440*900优化 */}
          <div className="flex items-center space-x-2 2xl:space-x-3">
            {/* 系统状态指示器 */}
            <div className="hidden lg:flex items-center space-x-2 px-3 py-1.5 bg-green-50 rounded-full">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
              <span className="text-xs 2xl:text-sm text-green-700 font-medium">系统正常</span>
            </div>

            {/* 快速操作按钮 */}
            <Button
              variant="outline"
              size="small"
              onClick={() => window.location.href = '/profile'}
              className="hidden sm:flex"
            >
              <span className="mr-1 2xl:mr-2">🚀</span>
              <span className="text-xs 2xl:text-sm">开始画像</span>
            </Button>

            {/* 移动端菜单按钮 */}
            <button className="md:hidden p-2 text-neutral-600 hover:text-neutral-900 hover:bg-neutral-50 rounded-lg transition-colors">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            </button>
          </div>
        </div>

        {/* 移动端导航菜单 (隐藏状态) */}
        <div className="md:hidden border-t border-neutral-200 bg-white">
          <nav className="px-4 py-2 space-y-1">
            {navItems.map((item) => (
              <Link
                key={item.path}
                to={item.path}
                className={`
                  flex items-center space-x-3 px-3 py-2 rounded-lg text-sm font-medium transition-all duration-200
                  ${isActivePath(item.path)
                    ? 'bg-primary-green text-white'
                    : 'text-neutral-600 hover:text-neutral-900 hover:bg-neutral-50'
                  }
                `}
              >
                <span>{item.icon}</span>
                <span>{item.label}</span>
              </Link>
            ))}
          </nav>
        </div>
      </div>
    </header>
  );
}; 