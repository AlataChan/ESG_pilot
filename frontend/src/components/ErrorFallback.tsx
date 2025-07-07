/**
 * ErrorFallback 组件
 * 用于显示应用错误的回退界面
 */

import React from 'react';

interface ErrorFallbackProps {
  error: Error;
  resetErrorBoundary: () => void;
}

/**
 * 错误回退组件
 */
const ErrorFallback: React.FC<ErrorFallbackProps> = ({
  error,
  resetErrorBoundary,
}) => {
  return (
    <div className="min-h-screen bg-neutral-50 flex items-center justify-center p-4">
      <div className="max-w-md w-full bg-white rounded-lg shadow-lg p-6 text-center">
        <div className="mb-4">
          <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <span className="text-2xl">😵</span>
          </div>
          <h2 className="text-xl font-semibold text-neutral-900 mb-2">
            出现了一些问题
          </h2>
          <p className="text-neutral-600 mb-4">
            应用遇到了意外错误，我们正在努力修复中。
          </p>
        </div>
        
        {process.env.NODE_ENV === 'development' && (
          <details className="mb-4 text-left">
            <summary className="cursor-pointer text-red-600 font-medium mb-2">
              错误详情 (开发模式)
            </summary>
            <pre className="bg-red-50 p-3 rounded text-xs text-red-800 overflow-auto">
              {error.message}
              {error.stack && (
                <>
                  {'\n\n'}
                  {error.stack}
                </>
              )}
            </pre>
          </details>
        )}
        
        <div className="space-y-3">
          <button
            onClick={resetErrorBoundary}
            className="w-full bg-primary-green text-white px-4 py-2 rounded-lg hover:bg-primary-green-dark transition-colors"
          >
            重新加载
          </button>
          
          <button
            onClick={() => window.location.href = '/'}
            className="w-full bg-neutral-200 text-neutral-700 px-4 py-2 rounded-lg hover:bg-neutral-300 transition-colors"
          >
            返回首页
          </button>
        </div>
        
        <p className="text-xs text-neutral-500 mt-4">
          如果问题持续存在，请联系技术支持。
        </p>
      </div>
    </div>
  );
};

export default ErrorFallback; 