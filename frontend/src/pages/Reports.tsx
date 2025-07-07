/**
 * Reports 页面组件
 * 展示ESG报告列表和生成功能
 * 针对1440*900分辨率优化
 */

import React from 'react';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';

/**
 * 报告项接口
 */
interface Report {
  id: string;
  title: string;
  type: 'profile' | 'assessment' | 'compliance' | 'sustainability';
  status: 'draft' | 'completed' | 'pending';
  createdAt: string;
  description: string;
  icon: string;
}

/**
 * 示例报告数据
 */
const sampleReports: Report[] = [
  {
    id: '1',
    title: '企业ESG画像报告',
    type: 'profile',
    status: 'completed',
    createdAt: '2024-01-15',
    description: '基于AI对话生成的企业ESG现状分析报告',
    icon: '🏢',
  },
  {
    id: '2',
    title: 'ESG风险评估报告',
    type: 'assessment',
    status: 'completed',
    createdAt: '2024-01-10',
    description: '企业ESG相关风险识别与评估分析',
    icon: '⚠️',
  },
  {
    id: '3',
    title: '合规性检查报告',
    type: 'compliance',
    status: 'pending',
    createdAt: '2024-01-12',
    description: '企业ESG合规性检查与建议',
    icon: '✅',
  },
];

/**
 * 报告卡片组件
 */
const ReportCard: React.FC<{ report: Report }> = ({ report }) => {
  const getStatusColor = (status: Report['status']) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-700';
      case 'pending':
        return 'bg-yellow-100 text-yellow-700';
      case 'draft':
        return 'bg-neutral-100 text-neutral-600';
      default:
        return 'bg-neutral-100 text-neutral-600';
    }
  };

  const getStatusText = (status: Report['status']) => {
    switch (status) {
      case 'completed':
        return '已完成';
      case 'pending':
        return '处理中';
      case 'draft':
        return '草稿';
      default:
        return '未知';
    }
  };

  return (
    <Card className="p-4 2xl:p-5 hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center space-x-3">
          <div className="text-2xl">{report.icon}</div>
          <div>
            <h3 className="text-base 2xl:text-lg font-semibold text-neutral-900 mb-1">
              {report.title}
            </h3>
            <p className="text-xs 2xl:text-sm text-neutral-600">
              {report.description}
            </p>
          </div>
        </div>
        <div className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(report.status)}`}>
          {getStatusText(report.status)}
        </div>
      </div>
      
      <div className="flex items-center justify-between mt-4">
        <span className="text-xs text-neutral-500">
          创建时间: {report.createdAt}
        </span>
        <div className="flex space-x-2">
          <Button variant="outline" size="small">
            查看
          </Button>
          {report.status === 'completed' && (
            <Button variant="primary" size="small">
              下载
            </Button>
          )}
        </div>
      </div>
    </Card>
  );
};

/**
 * Reports 主组件
 */
const ReportsPage: React.FC = () => {
  const handleGenerateReport = (type: string) => {
    console.log(`生成${type}报告`);
    // 这里可以添加具体的报告生成逻辑
  };

  return (
    <div className="page-container optimized-1440-900">
      <div className="layout-1440 content-wrapper">
        {/* 页面标题 - 1440*900优化 */}
        <div className="mb-6 2xl:mb-8">
          <h1 className="text-2xl 2xl:text-3xl font-bold text-neutral-900 mb-2">
            ESG报告中心
          </h1>
          <p className="text-sm 2xl:text-base text-neutral-600">
            查看、管理和生成企业ESG相关报告
          </p>
        </div>

        {/* 快速生成报告 - 1440*900优化 */}
        <div className="mb-6 2xl:mb-8">
          <h2 className="text-lg 2xl:text-xl font-semibold text-neutral-900 mb-3 2xl:mb-4">
            🚀 快速生成报告
          </h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 2xl:gap-4">
            <Card 
              className="p-4 text-center cursor-pointer hover:shadow-md transition-shadow"
              onClick={() => handleGenerateReport('企业画像')}
            >
              <div className="text-2xl mb-2">🏢</div>
              <h3 className="text-sm 2xl:text-base font-medium mb-1">企业画像报告</h3>
              <p className="text-xs text-neutral-600">AI生成企业ESG现状</p>
            </Card>
            
            <Card 
              className="p-4 text-center cursor-pointer hover:shadow-md transition-shadow"
              onClick={() => handleGenerateReport('风险评估')}
            >
              <div className="text-2xl mb-2">⚠️</div>
              <h3 className="text-sm 2xl:text-base font-medium mb-1">风险评估报告</h3>
              <p className="text-xs text-neutral-600">识别ESG相关风险</p>
            </Card>
            
            <Card 
              className="p-4 text-center cursor-pointer hover:shadow-md transition-shadow"
              onClick={() => handleGenerateReport('合规检查')}
            >
              <div className="text-2xl mb-2">✅</div>
              <h3 className="text-sm 2xl:text-base font-medium mb-1">合规检查报告</h3>
              <p className="text-xs text-neutral-600">检查合规性状态</p>
            </Card>
            
            <Card 
              className="p-4 text-center cursor-pointer hover:shadow-md transition-shadow"
              onClick={() => handleGenerateReport('可持续发展')}
            >
              <div className="text-2xl mb-2">🌱</div>
              <h3 className="text-sm 2xl:text-base font-medium mb-1">可持续发展报告</h3>
              <p className="text-xs text-neutral-600">分析可持续发展表现</p>
            </Card>
          </div>
        </div>

        {/* 现有报告列表 */}
        <div>
          <div className="flex items-center justify-between mb-4 2xl:mb-6">
            <h2 className="text-lg 2xl:text-xl font-semibold text-neutral-900">
              📋 现有报告
            </h2>
            <div className="flex space-x-2">
              <Button variant="outline" size="small">
                筛选
              </Button>
              <Button variant="outline" size="small">
                排序
              </Button>
            </div>
          </div>
          
          {sampleReports.length > 0 ? (
            <div className="grid gap-4 2xl:gap-6">
              {sampleReports.map((report) => (
                <ReportCard key={report.id} report={report} />
              ))}
            </div>
          ) : (
            <Card className="p-8 2xl:p-12 text-center">
              <div className="text-4xl mb-4">📄</div>
              <h3 className="text-lg 2xl:text-xl font-semibold text-neutral-900 mb-2">
                暂无报告
              </h3>
              <p className="text-neutral-600 mb-6">
                开始生成您的第一份ESG报告
              </p>
              <Button 
                variant="primary" 
                onClick={() => window.location.href = '/profile'}
              >
                生成企业画像报告
              </Button>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
};

export default ReportsPage; 