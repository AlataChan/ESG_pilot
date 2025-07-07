/**
 * ESG看板组件
 * 基于标准ESG框架，展示企业在环境、社会、治理三个维度的表现
 * 采用卡片式布局，支持交互和详细信息展示
 */

import React, { useState, useEffect } from 'react';
import { apiClient } from '../../services/api';

/**
 * ESG指标状态类型
 */
type IndicatorStatus = 'excellent' | 'good' | 'average' | 'needs_improvement' | 'not_assessed';

/**
 * ESG指标接口
 */
interface ESGIndicator {
  id: string;
  code: string;
  title: string;
  description: string;
  status: IndicatorStatus;
  score?: number;
  maxScore?: number;
  recommendation?: string;
}

/**
 * ESG子分类接口
 */
interface ESGSubCategory {
  id: string;
  code: string;
  title: string;
  description: string;
  indicators: ESGIndicator[];
  averageScore?: number;
}

/**
 * ESG主分类接口
 */
interface ESGCategory {
  id: string;
  code: string;
  title: string;
  description: string;
  color: string;
  subCategories: ESGSubCategory[];
  overallScore?: number;
}

/**
 * 获取状态对应的样式
 */
const getStatusStyles = (status: IndicatorStatus) => {
  switch (status) {
    case 'excellent':
      return {
        bg: 'bg-green-50 border-green-200',
        text: 'text-green-800',
        badge: 'bg-green-100 text-green-800',
        icon: '✅',
        label: '优秀'
      };
    case 'good':
      return {
        bg: 'bg-blue-50 border-blue-200',
        text: 'text-blue-800',
        badge: 'bg-blue-100 text-blue-800',
        icon: '👍',
        label: '良好'
      };
    case 'average':
      return {
        bg: 'bg-yellow-50 border-yellow-200',
        text: 'text-yellow-800',
        badge: 'bg-yellow-100 text-yellow-800',
        icon: '⚡',
        label: '一般'
      };
    case 'needs_improvement':
      return {
        bg: 'bg-orange-50 border-orange-200',
        text: 'text-orange-800',
        badge: 'bg-orange-100 text-orange-800',
        icon: '⚠️',
        label: '待改进'
      };
    case 'not_assessed':
      return {
        bg: 'bg-gray-50 border-gray-200',
        text: 'text-gray-600',
        badge: 'bg-gray-100 text-gray-600',
        icon: '❓',
        label: '未评估'
      };
    default:
      return {
        bg: 'bg-gray-50 border-gray-200',
        text: 'text-gray-600',
        badge: 'bg-gray-100 text-gray-600',
        icon: '❓',
        label: '未知'
      };
  }
};

/**
 * ESG指标卡片组件
 */
interface ESGIndicatorCardProps {
  indicator: ESGIndicator;
  onClick?: () => void;
}

const ESGIndicatorCard: React.FC<ESGIndicatorCardProps> = ({ indicator, onClick }) => {
  const styles = getStatusStyles(indicator.status);
  
  return (
    <div
      className={`
        relative p-4 rounded-lg border-2 transition-all duration-200 cursor-pointer
        hover:shadow-md hover:scale-[1.02] ${styles.bg}
      `}
      onClick={onClick}
    >
      {/* 状态标识 */}
      <div className="flex items-center justify-between mb-3">
        <span className="text-xs font-semibold text-gray-500">{indicator.code}</span>
        <div className={`px-2 py-1 rounded-full text-xs font-medium ${styles.badge}`}>
          <span className="mr-1">{styles.icon}</span>
          {styles.label}
        </div>
      </div>
      
      {/* 标题和描述 */}
      <h4 className={`text-sm font-semibold mb-2 ${styles.text}`}>
        {indicator.title}
      </h4>
      <p className="text-xs text-gray-600 line-clamp-2">
        {indicator.description}
      </p>
      
      {/* 评分显示 */}
      {indicator.score !== undefined && indicator.maxScore && (
        <div className="mt-3 flex items-center justify-between">
          <span className="text-xs text-gray-500">得分</span>
          <span className={`text-sm font-bold ${styles.text}`}>
            {indicator.score}/{indicator.maxScore}
          </span>
        </div>
      )}
    </div>
  );
};

/**
 * ESG子分类组件
 */
interface ESGSubCategoryProps {
  subCategory: ESGSubCategory;
  categoryColor: string;
  onIndicatorClick?: (indicator: ESGIndicator) => void;
}

const ESGSubCategorySection: React.FC<ESGSubCategoryProps> = ({ 
  subCategory, 
  categoryColor, 
  onIndicatorClick 
}) => {
  return (
    <div className="mb-8">
      {/* 子分类标题 */}
      <div className={`px-4 py-3 rounded-t-lg text-white`} style={{ backgroundColor: categoryColor }}>
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <span className="text-lg font-bold">{subCategory.code}</span>
            <span className="text-base font-semibold">{subCategory.title}</span>
            <span className="text-sm opacity-90">- {subCategory.description}</span>
          </div>
          {subCategory.averageScore && (
            <div className="flex items-center space-x-2">
              <span className="text-sm opacity-90">平均分:</span>
              <span className="text-lg font-bold">{subCategory.averageScore.toFixed(0)}</span>
            </div>
          )}
        </div>
      </div>
      
      {/* 指标网格 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-4 p-4 bg-white border-l-2 border-r-2 border-b-2 border-gray-200 rounded-b-lg">
        {subCategory.indicators.map((indicator) => (
          <ESGIndicatorCard
            key={indicator.id}
            indicator={indicator}
            onClick={() => onIndicatorClick?.(indicator)}
          />
        ))}
        
        {/* 添加新指标按钮 */}
        <div className="p-4 rounded-lg border-2 border-dashed border-gray-300 flex flex-col items-center justify-center text-gray-400 hover:border-gray-400 hover:text-gray-600 transition-colors cursor-pointer min-h-[120px]">
          <div className="text-2xl mb-2">+</div>
          <span className="text-xs text-center">请添加</span>
        </div>
      </div>
    </div>
  );
};

/**
 * ESG分类组件
 */
interface ESGCategoryProps {
  category: ESGCategory;
  onIndicatorClick?: (indicator: ESGIndicator) => void;
}

const ESGCategorySection: React.FC<ESGCategoryProps> = ({ category, onIndicatorClick }) => {
  return (
    <div className="mb-12">
      {/* 分类标题 */}
      <div className="mb-4">
        <div className={`inline-flex items-center px-4 py-2 rounded-lg text-white text-lg font-semibold shadow-sm`} 
             style={{ backgroundColor: category.color, opacity: 0.9 }}>
          <div className="bg-white bg-opacity-20 rounded-full w-8 h-8 flex items-center justify-center mr-3 text-sm font-bold">
            {category.code}
          </div>
          <span>{category.title}</span>
          {/* 总体评分 */}
          {category.overallScore && (
            <div className="ml-auto flex items-center space-x-2">
              <span className="text-sm opacity-90">总分:</span>
              <span className="bg-white bg-opacity-20 px-2 py-1 rounded text-sm font-bold">
                {category.overallScore.toFixed(0)}
              </span>
            </div>
          )}
        </div>
        <p className="text-gray-600 text-sm mt-2 ml-2">{category.description}</p>
      </div>
      
      {/* 子分类列表 */}
      {category.subCategories.map((subCategory) => (
        <ESGSubCategorySection
          key={subCategory.id}
          subCategory={subCategory}
          categoryColor={category.color}
          onIndicatorClick={onIndicatorClick}
        />
      ))}
    </div>
  );
};

/**
 * 指标详情模态框
 */
interface IndicatorDetailModalProps {
  indicator: ESGIndicator | null;
  isOpen: boolean;
  onClose: () => void;
}

const IndicatorDetailModal: React.FC<IndicatorDetailModalProps> = ({ 
  indicator, 
  isOpen, 
  onClose 
}) => {
  if (!isOpen || !indicator) return null;
  
  const styles = getStatusStyles(indicator.status);
  
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black bg-opacity-50">
      <div className="bg-white rounded-lg max-w-2xl w-full max-h-[80vh] overflow-y-auto">
        <div className="p-6">
          {/* 头部 */}
          <div className="flex items-start justify-between mb-4">
            <div className="flex-1">
              <div className="flex items-center space-x-3 mb-2">
                <span className="text-sm font-semibold text-gray-500">{indicator.code}</span>
                <div className={`px-3 py-1 rounded-full text-sm font-medium ${styles.badge}`}>
                  <span className="mr-1">{styles.icon}</span>
                  {styles.label}
                </div>
              </div>
              <h2 className="text-xl font-bold text-gray-900 mb-2">{indicator.title}</h2>
              <p className="text-gray-600">{indicator.description}</p>
            </div>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 text-2xl"
            >
              ×
            </button>
          </div>
          
          {/* 评分信息 */}
          {indicator.score !== undefined && indicator.maxScore && (
            <div className="mb-6 p-4 bg-gray-50 rounded-lg">
              <h3 className="text-lg font-semibold mb-2">评分详情</h3>
              <div className="flex items-center justify-between">
                <span>当前得分</span>
                <span className="text-2xl font-bold text-blue-600">
                  {indicator.score}/{indicator.maxScore}
                </span>
              </div>
              <div className="mt-2 w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-blue-500 h-2 rounded-full"
                  style={{ width: `${(indicator.score / indicator.maxScore) * 100}%` }}
                ></div>
              </div>
            </div>
          )}
          
          {/* 改进建议 */}
          {indicator.recommendation && (
            <div className="mb-6">
              <h3 className="text-lg font-semibold mb-2">改进建议</h3>
              <div className="p-4 bg-blue-50 rounded-lg border-l-4 border-blue-400">
                <p className="text-gray-700">{indicator.recommendation}</p>
              </div>
            </div>
          )}
          
          {/* 操作按钮 */}
          <div className="flex justify-end space-x-3">
            <button 
              className="px-4 py-2 text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500"
              onClick={onClose}
            >
              关闭
            </button>
            <button className="px-4 py-2 text-white bg-blue-600 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500">
              查看详细报告
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

/**
 * ESG看板主组件
 */
export const ESGDashboard: React.FC = () => {
  const [selectedIndicator, setSelectedIndicator] = useState<ESGIndicator | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [esgData, setEsgData] = useState<ESGCategory[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // 数据转换函数：将后端返回的数据转换为前端期望的格式
  const transformApiData = (apiData: any): ESGCategory[] => {
    if (!apiData || !Array.isArray(apiData)) {
      return [];
    }
    
    return apiData.map((category: any) => ({
      id: category.id,
      code: category.code,
      title: category.title,
      description: category.description,
      color: category.color,
      overallScore: category.overall_score,
      subCategories: category.sub_categories?.map((subCategory: any) => ({
        id: subCategory.id,
        code: subCategory.code,
        title: subCategory.title,
        description: subCategory.description,
        averageScore: subCategory.average_score,
        indicators: subCategory.indicators?.map((indicator: any) => ({
          id: indicator.id,
          code: indicator.code,
          title: indicator.title,
          description: indicator.description,
          status: indicator.status,
          score: indicator.score,
          maxScore: indicator.max_score,
          recommendation: indicator.recommendation
        })) || []
      })) || []
    }));
  };

  // 获取ESG评估数据
  useEffect(() => {
    const fetchESGData = async () => {
      try {
        setLoading(true);
        setError(null);
        const response = await apiClient.getESGAssessment();
        console.log('API Response:', response);
        
        // 检查响应结构并提取数据
        let rawData = null;
        if (response && response.data) {
          // 如果有 categories 字段，使用它
          if (response.data.categories) {
            rawData = response.data.categories;
          } else {
            // 否则使用整个 data 对象
            rawData = response.data;
          }
        } else {
          // 如果没有嵌套的 data 结构，直接使用响应
          rawData = response;
        }
        
        // 转换数据格式
        const transformedData = transformApiData(rawData);
        setEsgData(transformedData);
      } catch (err) {
        console.error('Failed to fetch ESG data:', err);
        setError('获取ESG数据失败，请稍后重试');
        // 使用模拟数据作为后备
        setEsgData(mockESGData);
      } finally {
        setLoading(false);
      }
    };

    fetchESGData();
  }, []);

  // 模拟ESG数据（作为后备）
  const mockESGData: ESGCategory[] = [
    {
      id: 'environmental',
      code: 'E',
      title: '环境 Environmental',
      description: '管理企业及上下游对环境的影响（产品/生产过程/运营消耗）',
      color: '#10b981', // emerald-500 - 更柔和的绿色
      overallScore: 85,
      subCategories: [
        {
          id: 'e1',
          code: 'E1',
          title: '碳排放',
          description: '能源消耗、低碳能源使用',
          averageScore: 82,
          indicators: [
            {
              id: 'e1-1',
              code: 'E1-1',
              title: '分析产品/运营碳排数据',
              description: '收集产品及企业运营过程中的碳排数据，设定减碳目标和举措，并做量效果',
              status: 'good',
              score: 85,
              maxScore: 100,
              recommendation: '建议建立完整的碳排放监测体系，定期更新数据'
            },
            {
              id: 'e1-2',
              code: 'E1-2',
              title: '提高能源效率或/和使用可再生能源',
              description: '以更低的能源消耗达成目标，在生产/和日常办公中提高可再生能源的使用比例',
              status: 'average',
              score: 75,
              maxScore: 100,
              recommendation: '考虑安装太阳能设备或采购绿色电力'
            },
            {
              id: 'e1-3',
              code: 'E1-3',
              title: '促进产业链上下游的低碳转型',
              description: '推出低碳产品；输出技术和资源推动产业链低碳转型',
              status: 'needs_improvement',
              score: 60,
              maxScore: 100,
              recommendation: '制定供应商低碳转型激励政策'
            }
          ]
        },
        {
          id: 'e2',
          code: 'E2',
          title: '污染管理',
          description: '关注和减少企业生产运营中产生的各种污染',
          averageScore: 88,
          indicators: [
            {
              id: 'e2-1',
              code: 'E2-1',
              title: '管理废弃/有害/污染物',
              description: '最大程度减少排气/液/固体废物的产生，对无法避免的环境污染进行数据监测',
              status: 'excellent',
              score: 92,
              maxScore: 100
            },
            {
              id: 'e2-2',
              code: 'E2-2',
              title: '使用环境友好的采购标准',
              description: '在供应商的筛选评价标准中加入环境评价，与供应商合作优化供应链的负面环境影响',
              status: 'good',
              score: 84,
              maxScore: 100
            }
          ]
        },
        {
          id: 'e3',
          code: 'E3',
          title: '资源利用',
          description: '消耗更少的自然资源，包含节约型，更耐用，可循环等',
          averageScore: 79,
          indicators: [
            {
              id: 'e3-1',
              code: 'E3-1',
              title: '节约用水，循环用水',
              description: '如在日常运营中实施节水措施；采用新技术减少生产用水的消耗；用新等',
              status: 'good',
              score: 80,
              maxScore: 100
            },
            {
              id: 'e3-2',
              code: 'E3-2',
              title: '优化原材料与包装使用',
              description: '如减少原材料采购总量；减少包装，减少塑料等材料；优化设计以提高资源利用率等',
              status: 'average',
              score: 75,
              maxScore: 100
            },
            {
              id: 'e3-3',
              code: 'E3-3',
              title: '生产及使用更耐用的产品',
              description: '如提升产品器械的选型/维修/保养，提升使用时间和打印机/灯泡等',
              status: 'good',
              score: 82,
              maxScore: 100
            },
            {
              id: 'e3-4',
              code: 'E3-4',
              title: '利用可回收/可再生资源',
              description: '如以回收/再生材料作为生产原材料，办公环境中使用的材料等',
              status: 'average',
              score: 78,
              maxScore: 100
            },
            {
              id: 'e3-5',
              code: 'E3-5',
              title: '负责任回收及召回产品',
              description: '回收含有毒有害的产品，召回存在问题的产品，处理或再利用产品',
              status: 'needs_improvement',
              score: 65,
              maxScore: 100
            }
          ]
        }
      ]
    },
    {
      id: 'social',
      code: 'S',
      title: '社会 Social',
      description: '管理企业运营过程中对各类利益相关方的影响',
      color: '#f97316', // orange-500 - 更柔和的橙色
      overallScore: 78,
      subCategories: [
        {
          id: 's1',
          code: 'S1',
          title: '产品与客户',
          description: '为客户提供更好，性价比更高的产品/服务',
          averageScore: 85,
          indicators: [
            {
              id: 's1-1',
              code: 'S1-1',
              title: '保护客户的隐私和数据安全',
              description: '采用有效措施技术，避免客户隐私和数据泄露不正当使用或滥用；建立设备处理机制',
              status: 'excellent',
              score: 95,
              maxScore: 100
            },
            {
              id: 's1-2',
              code: 'S1-2',
              title: '提升产品的质量和安全性',
              description: '保证产品质量与安全能持续稳定地达标；采用更高标准提升供应或服务',
              status: 'good',
              score: 88,
              maxScore: 100
            },
            {
              id: 's1-3',
              code: 'S1-3',
              title: '提供充分的产品信息',
              description: '确保客户了解产品的正确使用和处置信息；对抗虚假信息保持透明，说明其环境/社会影响等',
              status: 'good',
              score: 82,
              maxScore: 100
            },
            {
              id: 's1-4',
              code: 'S1-4',
              title: '提供性价比更高的产品/服务',
              description: '以更能负担的价格向客户提供良好的产品/服务',
              status: 'average',
              score: 75,
              maxScore: 100
            },
            {
              id: 's1-5',
              code: 'S1-5',
              title: '服务于未被充分服务人群',
              description: '让低收入人群或弱势人群（如老人/身障/儿童等）能接触到产品/服务，平等受益',
              status: 'needs_improvement',
              score: 65,
              maxScore: 100
            }
          ]
        }
        // 可以继续添加 S2, S3, S4 等子分类...
      ]
    },
    {
      id: 'governance',
      code: 'G',
      title: '治理 Governance',
      description: '为公司长期、稳定发展制定政策，并创新治理方式以激活组织绩效',
      color: '#3b82f6', // blue-500 - 更柔和的蓝色
      overallScore: 92,
      subCategories: [
        {
          id: 'g1',
          code: 'G1',
          title: '战略与使命',
          description: '按照企业使命中的商業重點並加以战略表達',
          averageScore: 90,
          indicators: [
            {
              id: 'g1-1',
              code: 'G1-1',
              title: '企业战略包含积极的社会影响',
              description: '按照企业使命中的商業重點並加以战略表達',
              status: 'excellent',
              score: 90,
              maxScore: 100
            }
          ]
        }
        // 可以继续添加 G2, G3 等子分类...
      ]
    }
  ];
  
  const handleIndicatorClick = (indicator: ESGIndicator) => {
    setSelectedIndicator(indicator);
    setIsModalOpen(true);
  };
  
  const handleCloseModal = () => {
    setIsModalOpen(false);
    setSelectedIndicator(null);
  };
  
  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">正在加载ESG数据...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 py-8">
        {/* 页面标题 */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            ESG企业看板
          </h1>
          <p className="text-gray-600">
            基于AI分析的企业ESG表现全景展示，涵盖环境、社会、治理三大维度
          </p>
          {error && (
            <div className="mt-4 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
              <p className="text-yellow-800">{error}</p>
            </div>
          )}
        </div>
        
        {/* ESG分类展示 */}
        {esgData && Array.isArray(esgData) && esgData.length > 0 ? (
          esgData.map((category) => (
          <ESGCategorySection
            key={category.id}
            category={category}
            onIndicatorClick={handleIndicatorClick}
          />
          ))
        ) : (
          <div className="text-center py-8">
            <p className="text-gray-500">暂无ESG数据</p>
          </div>
        )}
        
        {/* 指标详情模态框 */}
        <IndicatorDetailModal
          indicator={selectedIndicator}
          isOpen={isModalOpen}
          onClose={handleCloseModal}
        />
      </div>
    </div>
  );
};

export default ESGDashboard;