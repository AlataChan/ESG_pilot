/**
 * ESG-Copilot 首页组件
 * 提供企业画像生成的入口和功能介绍
 * 针对1440*900分辨率优化
 */

import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useConversationActions } from '../stores/appStore';
import { Button } from '../components/ui/Button';

const HomePage: React.FC = () => {
  const navigate = useNavigate();
  const { startConversation } = useConversationActions();
  const [companyName, setCompanyName] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleStartProfile = async () => {
    if (!companyName.trim()) {
      alert('请输入企业名称');
      return;
    }

    setIsLoading(true);
    try {
      const companyInfo = {
        name: companyName.trim(),
      };

      await startConversation({
        user_id: 'current_user',
        company_name: companyInfo.name,
        initial_info: companyInfo,
      });

      navigate('/profile');
    } catch (error) {
      console.error('启动企业画像失败:', error);
      alert('启动企业画像失败，请重试');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="page-container optimized-1440-900">
      <div className="layout-1440 content-wrapper">
        <div className="text-center max-w-6xl mx-auto">
          {/* 主标题区域 - 针对1440*900优化，减少间距 */}
          <div className="mb-8 2xl:mb-10">
            <h1 className="text-4xl 2xl:text-5xl font-bold mb-3 2xl:mb-4">
              <span className="gradient-text">ESG-Copilot</span>
            </h1>
            <p className="text-lg 2xl:text-xl text-neutral-600 mb-2 2xl:mb-3">
              AI驱动的可持续发展管理平台
            </p>
            <p className="text-base 2xl:text-lg text-neutral-500 max-w-3xl mx-auto">
              通过智能对话生成企业画像，获得个性化的ESG评估和改进建议，构建更美好的可持续未来
            </p>
          </div>

          {/* 企业画像生成卡片 - 1440*900优化，减少尺寸 */}
          <div className="bg-white rounded-3xl shadow-strong p-5 2xl:p-6 mb-8 2xl:mb-10 max-w-xl mx-auto">
            <h2 className="text-lg 2xl:text-xl font-semibold mb-3 2xl:mb-4">
              开始企业画像生成
            </h2>
            <p className="text-neutral-600 mb-4 2xl:mb-5 text-sm 2xl:text-base">
              输入您的企业名称，我们的AI助手将通过智能对话为您生成详细的企业画像
            </p>
            
            <div className="max-w-sm mx-auto">
              <div className="mb-3 2xl:mb-4">
                <input
                  type="text"
                  placeholder="请输入企业名称"
                  value={companyName}
                  onChange={(e) => setCompanyName(e.target.value)}
                  className="input text-base"
                  onKeyPress={(e) => e.key === 'Enter' && handleStartProfile()}
                />
              </div>
              
              <Button
                onClick={handleStartProfile}
                disabled={isLoading || !companyName.trim()}
                className="btn btn-primary btn-large w-full"
                loading={isLoading}
              >
                {isLoading ? (
                  <span className="flex items-center justify-center">
                    <div className="animate-spin w-5 h-5 border-2 border-white border-t-transparent rounded-full mr-2"></div>
                    启动中...
                  </span>
                ) : (
                  '开始生成企业画像'
                )}
              </Button>
            </div>
          </div>

          {/* 功能特色 - 紧凑的三列布局 */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 2xl:gap-6 mb-6 2xl:mb-8 max-w-4xl mx-auto">
            <div className="card card-hover p-3 2xl:p-4 text-center">
              <div className="w-10 h-10 2xl:w-12 2xl:h-12 bg-primary-green-light rounded-full flex items-center justify-center mx-auto mb-2 2xl:mb-3">
                <span className="text-lg 2xl:text-xl">🤖</span>
              </div>
              <h3 className="text-sm 2xl:text-base font-semibold mb-1 2xl:mb-2">智能对话</h3>
              <p className="text-neutral-600 text-xs 2xl:text-sm">
                通过自然语言对话，AI助手深入了解您的企业情况
              </p>
            </div>

            <div className="card card-hover p-3 2xl:p-4 text-center">
              <div className="w-10 h-10 2xl:w-12 2xl:h-12 bg-secondary-yellow-light rounded-full flex items-center justify-center mx-auto mb-2 2xl:mb-3">
                <span className="text-lg 2xl:text-xl">📊</span>
              </div>
              <h3 className="text-sm 2xl:text-base font-semibold mb-1 2xl:mb-2">专业评估</h3>
              <p className="text-neutral-600 text-xs 2xl:text-sm">
                基于国际标准的ESG评估体系，提供专业的分析报告
              </p>
            </div>

            <div className="card card-hover p-3 2xl:p-4 text-center">
              <div className="w-10 h-10 2xl:w-12 2xl:h-12 bg-primary-green-light rounded-full flex items-center justify-center mx-auto mb-2 2xl:mb-3">
                <span className="text-lg 2xl:text-xl">🎯</span>
              </div>
              <h3 className="text-sm 2xl:text-base font-semibold mb-1 2xl:mb-2">个性化建议</h3>
              <p className="text-neutral-600 text-xs 2xl:text-sm">
                针对您的企业特点，提供可操作的改进建议和实施路径
              </p>
            </div>
          </div>

          {/* 底部信息 - 1440*900优化，减少间距 */}
          <div className="text-center text-neutral-500">
            <p className="mb-1 text-sm 2xl:text-base">
              由先进的AI技术驱动，确保评估结果的准确性和实用性
            </p>
            <p className="text-xs 2xl:text-sm">
              ✨ 免费使用 • 🔒 数据安全 • 🚀 快速生成
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default HomePage; 