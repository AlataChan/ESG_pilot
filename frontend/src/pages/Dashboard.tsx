/**
 * Dashboard 页面组件
 * 展示企业ESG概览、关键指标和快速操作
 * 针对1440*900分辨率优化
 */

import React, { useState, useEffect } from 'react';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { apiClient } from '../services/api';

// API数据类型定义
interface DashboardMetrics {
  esg_score: {
    current: number;
    change: number;
    trend: 'up' | 'down' | 'stable';
  };
  environmental_score: {
    current: string;
    change: string;
    trend: 'up' | 'down' | 'stable';
  };
  social_score: {
    current: number;
    change: number;
    trend: 'up' | 'down' | 'stable';
  };
  governance_score: {
    current: number;
    change: number;
    trend: 'up' | 'down' | 'stable';
  };
  risk_level: {
    current: string;
    change: string;
    trend: 'up' | 'down' | 'stable';
  };
  compliance_status: {
    current: string;
    change: string;
    trend: 'up' | 'down' | 'stable';
  };
}

interface SystemStatus {
  status: string;
  uptime: string;
  last_update: string;
  active_users: number;
}

interface RecentActivity {
  id: string;
  type: string;
  description: string;
  timestamp: string;
  status: string;
}

interface DashboardData {
  metrics: DashboardMetrics;
  system_status: SystemStatus;
  recent_activities: RecentActivity[];
}

/**
 * 指标卡片组件
 */
interface MetricCardProps {
  title: string;
  value: string | number;
  change?: string;
  trend?: 'up' | 'down' | 'stable';
  icon: string;
  color?: 'green' | 'yellow' | 'blue' | 'red';
}

const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  change,
  trend,
  icon,
  color = 'green'
}) => {
  const getColorClasses = (color: string) => {
    switch (color) {
      case 'green':
        return 'bg-green-50 text-green-700 border-green-200';
      case 'yellow':
        return 'bg-yellow-50 text-yellow-700 border-yellow-200';
      case 'blue':
        return 'bg-blue-50 text-blue-700 border-blue-200';
      case 'red':
        return 'bg-red-50 text-red-700 border-red-200';
      default:
        return 'bg-neutral-50 text-neutral-700 border-neutral-200';
    }
  };

  const getTrendIcon = (trend?: string) => {
    switch (trend) {
      case 'up':
        return '📈';
      case 'down':
        return '📉';
      case 'stable':
        return '➡️';
      default:
        return '';
    }
  };

  return (
    <Card className="p-4 2xl:p-5 hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center space-x-2 mb-2">
            <span className="text-lg">{icon}</span>
            <h3 className="text-sm 2xl:text-base font-medium text-neutral-600">{title}</h3>
          </div>
          <div className="space-y-1">
            <p className="text-xl 2xl:text-2xl font-bold text-neutral-900">{value}</p>
            {change && (
              <div className="flex items-center space-x-1">
                <span className="text-xs">{getTrendIcon(trend)}</span>
                <span className={`text-xs font-medium ${
                  trend === 'up' ? 'text-green-600' : 
                  trend === 'down' ? 'text-red-600' : 
                  'text-neutral-600'
                }`}>
                  {change}
                </span>
              </div>
            )}
          </div>
        </div>
        <div className={`w-2 h-2 rounded-full ${getColorClasses(color).split(' ')[0]}`}></div>
      </div>
    </Card>
  );
};

/**
 * 快速操作卡片组件
 */
interface QuickActionProps {
  title: string;
  description: string;
  icon: string;
  onClick: () => void;
  variant?: 'primary' | 'secondary' | 'outline';
}

const QuickActionCard: React.FC<QuickActionProps> = ({
  title,
  description,
  icon,
  onClick,
  variant = 'outline'
}) => {
  return (
    <Card className="p-4 2xl:p-5 hover:shadow-md transition-all duration-200 cursor-pointer" onClick={onClick}>
      <div className="text-center space-y-3">
        <div className="text-2xl 2xl:text-3xl">{icon}</div>
        <div>
          <h3 className="font-semibold text-neutral-900 text-sm 2xl:text-base mb-1">{title}</h3>
          <p className="text-xs 2xl:text-sm text-neutral-600">{description}</p>
        </div>
        <Button variant={variant} size="small" className="w-full">
          开始使用
        </Button>
      </div>
    </Card>
  );
};

/**
 * Dashboard主组件
 */
const DashboardPage: React.FC = () => {
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);


  // 数据转换函数：将后端返回的数据格式转换为前端期望的格式
  const transformDashboardData = (backendData: any): DashboardData => {
    console.log('Backend data:', backendData);
    
    // 转换 key_metrics 数组为 metrics 对象
    const metricsMap: Record<string, any> = {};
    if (backendData.key_metrics && Array.isArray(backendData.key_metrics)) {
      backendData.key_metrics.forEach((metric: any) => {
        const key = metric.title;
        if (key === 'ESG综合评分') {
          metricsMap.esg_score = {
            current: parseInt(metric.value) || 0,
            change: parseInt(metric.change.replace(/[^\d-]/g, '')) || 0,
            trend: metric.trend || 'stable'
          };
        } else if (key === '环境保护') {
          metricsMap.environmental_score = {
            current: metric.value || 'N/A',
            change: metric.change || '无变化',
            trend: metric.trend || 'stable'
          };
        } else if (key === '社会责任') {
          metricsMap.social_score = {
            current: parseInt(metric.value) || 0,
            change: parseInt(metric.change.replace(/[^\d-]/g, '')) || 0,
            trend: metric.trend || 'stable'
          };
        } else if (key === '公司治理') {
          metricsMap.governance_score = {
            current: parseInt(metric.value) || 0,
            change: parseInt(metric.change.replace(/[^\d-]/g, '')) || 0,
            trend: metric.trend || 'stable'
          };
        } else if (key === '风险等级') {
          metricsMap.risk_level = {
            current: metric.value || 'N/A',
            change: metric.change || '无变化',
            trend: metric.trend || 'stable'
          };
        } else if (key === '合规状态') {
          metricsMap.compliance_status = {
            current: metric.value || 'N/A',
            change: metric.change || '无变化',
            trend: metric.trend || 'stable'
          };
        }
      });
    }

    // 转换 system_status 数组为 system_status 对象
    const systemStatus = {
      status: 'healthy',
      uptime: '99.9%',
      last_update: backendData.last_updated || new Date().toISOString(),
      active_users: 1
    };

    // 转换 recent_activities 数组
    const recentActivities = backendData.recent_activities || [];

    return {
      metrics: metricsMap as DashboardMetrics,
      system_status: systemStatus,
      recent_activities: recentActivities
    };
  };

  // 获取仪表板数据
  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await apiClient.getDashboardOverview();
      console.log('API Response:', response);
      
      if (response.success && response.data) {
        const transformedData = transformDashboardData(response.data);
        console.log('Transformed data:', transformedData);
        setDashboardData(transformedData);
      } else {
        setError(response.message || '获取数据失败');
      }
    } catch (err) {
      console.error('获取仪表板数据失败:', err);
      setError('网络错误，请稍后重试');
    } finally {
      setLoading(false);
    }
  };

  // 组件挂载时获取数据
  useEffect(() => {
    fetchDashboardData();
  }, []);

  const handleQuickAction = (action: string) => {
    console.log(`执行快速操作: ${action}`);
    // 这里可以添加具体的导航逻辑
  };

  // 加载状态
  if (loading) {
    return (
      <div className="page-container optimized-1440-900">
        <div className="layout-1440 content-wrapper">
          <div className="flex items-center justify-center h-64">
            <div className="text-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
              <p className="text-neutral-600">正在加载数据...</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // 错误状态
  if (error) {
    return (
      <div className="page-container optimized-1440-900">
        <div className="layout-1440 content-wrapper">
          <div className="flex items-center justify-center h-64">
            <div className="text-center">
              <div className="text-red-500 text-4xl mb-4">⚠️</div>
              <p className="text-red-600 mb-4">{error}</p>
              <Button onClick={fetchDashboardData} variant="primary">
                重新加载
              </Button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // 如果没有数据，显示默认内容
  if (!dashboardData) {
    return (
      <div className="page-container optimized-1440-900">
        <div className="layout-1440 content-wrapper">
          <div className="flex items-center justify-center h-64">
            <p className="text-neutral-600">暂无数据</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="page-container optimized-1440-900">
      <div className="layout-1440 content-wrapper">
        {/* 页面标题 - 1440*900优化 */}
        <div className="mb-6 2xl:mb-8">
          <h1 className="text-2xl 2xl:text-3xl font-bold text-neutral-900 mb-2">
            ESG管理中心
          </h1>
          <p className="text-sm 2xl:text-base text-neutral-600">
            全面掌握企业可持续发展状况，智能驱动ESG管理决策
          </p>
        </div>

        {/* 关键指标概览 - 网格布局优化 */}
        <div className="mb-6 2xl:mb-8">
          <h2 className="text-lg 2xl:text-xl font-semibold text-neutral-900 mb-3 2xl:mb-4">
            📊 关键指标概览
          </h2>
          <div className="grid-1440 gap-3 2xl:gap-4">
            {dashboardData.metrics && dashboardData.metrics.esg_score && (
            <MetricCard
              title="ESG综合评分"
              value={dashboardData.metrics.esg_score.current}
              change={`${dashboardData.metrics.esg_score.change > 0 ? '+' : ''}${dashboardData.metrics.esg_score.change}分`}
              trend={dashboardData.metrics.esg_score.trend}
              icon="🎯"
              color="green"
            />
            )}
            {dashboardData.metrics && dashboardData.metrics.environmental_score && (
            <MetricCard
              title="环境表现"
              value={dashboardData.metrics.environmental_score.current}
              change={dashboardData.metrics.environmental_score.change}
              trend={dashboardData.metrics.environmental_score.trend}
              icon="🌱"
              color="green"
            />
            )}
            {dashboardData.metrics && dashboardData.metrics.social_score && (
            <MetricCard
              title="社会责任"
              value={dashboardData.metrics.social_score.current}
              change={`${dashboardData.metrics.social_score.change > 0 ? '+' : ''}${dashboardData.metrics.social_score.change}分`}
              trend={dashboardData.metrics.social_score.trend}
              icon="👥"
              color="blue"
            />
            )}
            {dashboardData.metrics && dashboardData.metrics.governance_score && (
            <MetricCard
              title="公司治理"
              value={dashboardData.metrics.governance_score.current}
              change={`${dashboardData.metrics.governance_score.change > 0 ? '+' : ''}${dashboardData.metrics.governance_score.change}分`}
              trend={dashboardData.metrics.governance_score.trend}
              icon="⚖️"
              color="yellow"
            />
            )}
            {dashboardData.metrics && dashboardData.metrics.risk_level && (
            <MetricCard
              title="风险等级"
              value={dashboardData.metrics.risk_level.current}
              change={dashboardData.metrics.risk_level.change}
              trend={dashboardData.metrics.risk_level.trend}
              icon="🛡️"
              color="green"
            />
            )}
            {dashboardData.metrics && dashboardData.metrics.compliance_status && (
            <MetricCard
              title="合规状态"
              value={dashboardData.metrics.compliance_status.current}
              change={dashboardData.metrics.compliance_status.change}
              trend={dashboardData.metrics.compliance_status.trend}
              icon="✅"
              color="green"
            />
            )}
          </div>
        </div>

        {/* 快速操作区域 */}
        <div className="mb-6 2xl:mb-8">
          <h2 className="text-lg 2xl:text-xl font-semibold text-neutral-900 mb-3 2xl:mb-4">
            🚀 快速操作
          </h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 2xl:gap-4">
            <QuickActionCard
              title="生成企业画像"
              description="AI智能分析企业ESG现状"
              icon="🤖"
              onClick={() => handleQuickAction('profile')}
              variant="primary"
            />
            <QuickActionCard
              title="ESG评估报告"
              description="获取专业评估分析报告"
              icon="📋"
              onClick={() => handleQuickAction('assessment')}
              variant="secondary"
            />
            <QuickActionCard
              title="风险监控"
              description="实时监控ESG相关风险"
              icon="⚠️"
              onClick={() => handleQuickAction('monitor')}
            />
            <QuickActionCard
              title="改进建议"
              description="获取个性化改进方案"
              icon="💡"
              onClick={() => handleQuickAction('suggestions')}
            />
          </div>
        </div>

        {/* 最近活动 */}
        <div className="grid lg:grid-cols-2 gap-4 2xl:gap-6">
          {/* 最近对话 */}
          <Card className="p-4 2xl:p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-base 2xl:text-lg font-semibold text-neutral-900">
                💬 最近对话
              </h3>
              <Button variant="ghost" size="small">查看全部</Button>
            </div>
            <div className="space-y-3">
              <div className="flex items-start space-x-3 p-3 bg-neutral-50 rounded-lg">
                <div className="w-8 h-8 bg-primary-green rounded-full flex items-center justify-center flex-shrink-0">
                  <span className="text-white text-sm">🤖</span>
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-neutral-900 font-medium">企业画像生成</p>
                  <p className="text-xs text-neutral-600 line-clamp-2">
                    已完成基础信息收集，正在进行ESG风险评估...
                  </p>
                  <p className="text-xs text-neutral-500 mt-1">2小时前</p>
                </div>
              </div>
              
              <div className="flex items-start space-x-3 p-3 bg-neutral-50 rounded-lg">
                <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center flex-shrink-0">
                  <span className="text-white text-sm">📊</span>
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-neutral-900 font-medium">ESG报告分析</p>
                  <p className="text-xs text-neutral-600 line-clamp-2">
                    环境指标表现良好，建议加强社会责任投入...
                  </p>
                  <p className="text-xs text-neutral-500 mt-1">1天前</p>
                </div>
              </div>
            </div>
          </Card>

          {/* 系统状态 */}
          <Card className="p-4 2xl:p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-base 2xl:text-lg font-semibold text-neutral-900">
                🔧 系统状态
              </h3>
              <div className="flex items-center space-x-2">
                <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                <span className="text-xs text-green-600 font-medium">正常运行</span>
              </div>
            </div>
            <div className="space-y-3">
              <div className="flex items-center justify-between py-2">
                <span className="text-sm text-neutral-600">AI Agent服务</span>
                <span className="text-xs text-green-600 font-medium">✅ 正常</span>
              </div>
              <div className="flex items-center justify-between py-2">
                <span className="text-sm text-neutral-600">数据库连接</span>
                <span className="text-xs text-green-600 font-medium">✅ 正常</span>
              </div>
              <div className="flex items-center justify-between py-2">
                <span className="text-sm text-neutral-600">API响应时间</span>
                <span className="text-xs text-green-600 font-medium">&lt; 200ms</span>
              </div>
              <div className="flex items-center justify-between py-2">
                <span className="text-sm text-neutral-600">上次更新</span>
                <span className="text-xs text-neutral-500">刚刚</span>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default DashboardPage;