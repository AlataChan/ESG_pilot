/**
 * Results 页面组件 - ESG看板
 * 展示企业ESG表现的可视化看板
 * 基于标准ESG框架，提供详细的指标分析和改进建议
 */

import React from 'react';
import ESGDashboard from '../components/esg/ESGDashboard';

/**
 * Results 主组件 - 现在作为ESG看板页面
 */
const ResultsPage: React.FC = () => {
  return <ESGDashboard />;
};

export default ResultsPage; 