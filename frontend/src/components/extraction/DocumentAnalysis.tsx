/**
 * DocumentAnalysis 文档分析组件
 * 支持智能文档分析、关键信息提取、实体识别和多层次摘要生成
 */

import React, { useState, useEffect } from 'react';
import clsx from 'clsx';
import { Card } from '../ui/Card';
import { Button } from '../ui/Button';

interface ExtractedEntity {
  text: string;
  type: string;
  confidence: number;
  context: string;
  position: number;
}

interface KeyInformation {
  content: string;
  importance: number;
  category: string;
  keywords: string[];
  source_section: string;
}

interface DocumentSummary {
  title: string;
  brief_summary: string;
  detailed_summary: string;
  key_points: string[];
  structure_summary: string;
  confidence: number;
}

interface ExtractionResult {
  document_id: string;
  document_name: string;
  summary: DocumentSummary;
  key_information: KeyInformation[];
  entities: ExtractedEntity[];
  tags: string[];
  word_count: number;
  paragraph_count: number;
  section_count: number;
  extraction_timestamp: string;
  processing_time: number;
}

interface DocumentAnalysisProps {
  /** 文档ID */
  documentId: string;
  /** 用户ID */
  userId: string;
  /** 自定义类名 */
  className?: string;
  /** 自动开始分析 */
  autoStart?: boolean;
}

/**
 * 文档分析组件
 */
export const DocumentAnalysis: React.FC<DocumentAnalysisProps> = ({
  documentId,
  userId,
  className,
  autoStart = false
}) => {
  const [analysisResult, setAnalysisResult] = useState<ExtractionResult | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [activeTab, setActiveTab] = useState<'summary' | 'entities' | 'key_info' | 'tags' | 'stats'>('summary');
  const [error, setError] = useState<string | null>(null);

  // 自动开始分析
  useEffect(() => {
    if (autoStart && documentId && userId) {
      handleStartAnalysis();
    }
  }, [autoStart, documentId, userId]);

  // 开始文档分析
  const handleStartAnalysis = async () => {
    if (!documentId || !userId || isAnalyzing) return;

    setIsAnalyzing(true);
    setError(null);

    try {
      const response = await fetch('/api/v1/extraction/analyze', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          document_id: documentId,
          user_id: userId,
          extraction_types: ['summary', 'entities', 'keywords', 'key_info']
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const result = await response.json();
      setAnalysisResult(result.data);

    } catch (error) {
      console.error('文档分析失败:', error);
      setError(error instanceof Error ? error.message : '分析失败');
    } finally {
      setIsAnalyzing(false);
    }
  };

  // 获取实体类型颜色
  const getEntityTypeColor = (type: string) => {
    const colors: Record<string, string> = {
      '组织机构': 'bg-blue-100 text-blue-800 border-blue-200',
      '人员职位': 'bg-green-100 text-green-800 border-green-200',
      '政策法规': 'bg-purple-100 text-purple-800 border-purple-200',
      '财务数据': 'bg-yellow-100 text-yellow-800 border-yellow-200',
      '时间日期': 'bg-gray-100 text-gray-800 border-gray-200',
      'ESG指标': 'bg-emerald-100 text-emerald-800 border-emerald-200'
    };
    return colors[type] || 'bg-gray-100 text-gray-800 border-gray-200';
  };

  // 获取信息类别颜色
  const getCategoryColor = (category: string) => {
    const colors: Record<string, string> = {
      '核心业务': 'bg-blue-100 text-blue-700',
      '财务状况': 'bg-green-100 text-green-700',
      '风险管理': 'bg-red-100 text-red-700',
      '治理结构': 'bg-purple-100 text-purple-700',
      'ESG表现': 'bg-emerald-100 text-emerald-700',
      '战略规划': 'bg-orange-100 text-orange-700'
    };
    return colors[category] || 'bg-gray-100 text-gray-700';
  };

  // 获取重要性指示器
  const getImportanceIndicator = (importance: number) => {
    if (importance >= 0.8) return { text: '高', color: 'bg-red-500' };
    if (importance >= 0.6) return { text: '中', color: 'bg-yellow-500' };
    return { text: '低', color: 'bg-gray-500' };
  };

  // 获取置信度指示器
  const getConfidenceIndicator = (confidence: number) => {
    if (confidence >= 0.8) return { text: '高置信度', color: 'text-green-600' };
    if (confidence >= 0.6) return { text: '中等置信度', color: 'text-yellow-600' };
    if (confidence >= 0.4) return { text: '低置信度', color: 'text-orange-600' };
    return { text: '极低置信度', color: 'text-red-600' };
  };

  return (
    <div className={clsx('space-y-6', className)}>
      {/* 分析控制 */}
      <Card className="p-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">📊 智能文档分析</h3>
            <p className="text-sm text-gray-600">
              对文档进行深度分析，提取关键信息、识别重要实体并生成智能摘要
            </p>
          </div>
          
          <div className="flex items-center space-x-3">
            {analysisResult && (
              <div className="text-sm text-gray-500">
                分析完成时间: {new Date(analysisResult.extraction_timestamp).toLocaleString()}
              </div>
            )}
            
            <Button
              onClick={handleStartAnalysis}
              disabled={isAnalyzing}
              className="min-w-[120px]"
            >
              {isAnalyzing ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  分析中...
                </>
              ) : (
                analysisResult ? '重新分析' : '🚀 开始分析'
              )}
            </Button>
          </div>
        </div>

        {/* 错误提示 */}
        {error && (
          <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-red-700 text-sm">❌ {error}</p>
          </div>
        )}

        {/* 分析进度 */}
        {isAnalyzing && (
          <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
            <div className="flex items-center space-x-3">
              <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
              <div>
                <p className="text-blue-800 font-medium">正在进行智能分析...</p>
                <p className="text-blue-600 text-sm">提取关键信息、识别实体、生成摘要</p>
              </div>
            </div>
          </div>
        )}
      </Card>

      {/* 分析结果 */}
      {analysisResult && (
        <>
          {/* 统计概览 */}
          <Card className="p-4">
            <h4 className="text-md font-semibold text-gray-900 mb-4">📈 分析概览</h4>
            <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
              <div className="text-center p-3 bg-blue-50 rounded-lg">
                <div className="text-2xl font-bold text-blue-600">{analysisResult.word_count.toLocaleString()}</div>
                <div className="text-sm text-blue-700">字数</div>
              </div>
              <div className="text-center p-3 bg-green-50 rounded-lg">
                <div className="text-2xl font-bold text-green-600">{analysisResult.paragraph_count}</div>
                <div className="text-sm text-green-700">段落数</div>
              </div>
              <div className="text-center p-3 bg-purple-50 rounded-lg">
                <div className="text-2xl font-bold text-purple-600">{analysisResult.section_count}</div>
                <div className="text-sm text-purple-700">章节数</div>
              </div>
              <div className="text-center p-3 bg-yellow-50 rounded-lg">
                <div className="text-2xl font-bold text-yellow-600">{analysisResult.entities.length}</div>
                <div className="text-sm text-yellow-700">识别实体</div>
              </div>
              <div className="text-center p-3 bg-red-50 rounded-lg">
                <div className="text-2xl font-bold text-red-600">{analysisResult.key_information.length}</div>
                <div className="text-sm text-red-700">关键信息</div>
              </div>
              <div className="text-center p-3 bg-gray-50 rounded-lg">
                <div className="text-2xl font-bold text-gray-600">{analysisResult.processing_time.toFixed(1)}s</div>
                <div className="text-sm text-gray-700">处理时间</div>
              </div>
            </div>
          </Card>

          {/* 标签云 */}
          <Card className="p-4">
            <h4 className="text-md font-semibold text-gray-900 mb-4">🏷️ 智能标签</h4>
            <div className="flex flex-wrap gap-2">
              {analysisResult.tags.map((tag, index) => (
                <span
                  key={index}
                  className="px-3 py-1 bg-indigo-100 text-indigo-800 rounded-full text-sm font-medium border border-indigo-200"
                >
                  {tag}
                </span>
              ))}
            </div>
          </Card>

          {/* 选项卡导航 */}
          <div className="border-b border-gray-200">
            <nav className="-mb-px flex space-x-8">
              {[
                { key: 'summary', label: '📝 文档摘要', count: analysisResult.summary.key_points.length },
                { key: 'entities', label: '🏷️ 实体识别', count: analysisResult.entities.length },
                { key: 'key_info', label: '🔑 关键信息', count: analysisResult.key_information.length },
                { key: 'tags', label: '📋 标签分析', count: analysisResult.tags.length },
                { key: 'stats', label: '📊 详细统计', count: 0 }
              ].map((tab) => (
                <button
                  key={tab.key}
                  onClick={() => setActiveTab(tab.key as any)}
                  className={clsx(
                    'py-2 px-1 border-b-2 font-medium text-sm whitespace-nowrap',
                    activeTab === tab.key
                      ? 'border-primary-green text-primary-green'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  )}
                >
                  {tab.label}
                  {tab.count > 0 && (
                    <span className="ml-2 bg-gray-100 text-gray-600 py-0.5 px-2 rounded-full text-xs">
                      {tab.count}
                    </span>
                  )}
                </button>
              ))}
            </nav>
          </div>

          {/* 选项卡内容 */}
          <div className="space-y-4">
            {/* 文档摘要 */}
            {activeTab === 'summary' && (
              <div className="space-y-4">
                {/* 简要摘要 */}
                <Card className="p-4">
                  <div className="flex items-center justify-between mb-3">
                    <h5 className="font-semibold text-gray-900">💡 简要摘要</h5>
                    <span className={clsx('text-sm font-medium', getConfidenceIndicator(analysisResult.summary.confidence).color)}>
                      {getConfidenceIndicator(analysisResult.summary.confidence).text}
                    </span>
                  </div>
                  <p className="text-gray-700 leading-relaxed">{analysisResult.summary.brief_summary}</p>
                </Card>

                {/* 详细摘要 */}
                <Card className="p-4">
                  <h5 className="font-semibold text-gray-900 mb-3">📄 详细摘要</h5>
                  <p className="text-gray-700 leading-relaxed whitespace-pre-wrap">{analysisResult.summary.detailed_summary}</p>
                </Card>

                {/* 关键要点 */}
                {analysisResult.summary.key_points.length > 0 && (
                  <Card className="p-4">
                    <h5 className="font-semibold text-gray-900 mb-3">⭐ 关键要点</h5>
                    <ul className="space-y-2">
                      {analysisResult.summary.key_points.map((point, index) => (
                        <li key={index} className="flex items-start space-x-2">
                          <span className="flex-shrink-0 w-6 h-6 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-sm font-medium">
                            {index + 1}
                          </span>
                          <span className="text-gray-700">{point}</span>
                        </li>
                      ))}
                    </ul>
                  </Card>
                )}

                {/* 结构摘要 */}
                <Card className="p-4">
                  <h5 className="font-semibold text-gray-900 mb-3">🏗️ 结构分析</h5>
                  <p className="text-gray-700">{analysisResult.summary.structure_summary}</p>
                </Card>
              </div>
            )}

            {/* 实体识别 */}
            {activeTab === 'entities' && (
              <div className="space-y-4">
                {analysisResult.entities.length > 0 ? (
                  <div className="grid gap-4">
                    {analysisResult.entities.map((entity, index) => (
                      <Card key={index} className="p-4">
                        <div className="flex items-start justify-between mb-2">
                          <div className="flex items-center space-x-2">
                            <span className={clsx('px-2 py-1 rounded text-xs font-medium border', getEntityTypeColor(entity.type))}>
                              {entity.type}
                            </span>
                            <span className="font-medium text-gray-900">{entity.text}</span>
                          </div>
                          <div className="flex items-center space-x-2">
                            <span className="text-xs text-gray-500">置信度: {(entity.confidence * 100).toFixed(0)}%</span>
                            <div className={clsx('w-2 h-2 rounded-full', entity.confidence >= 0.8 ? 'bg-green-500' : entity.confidence >= 0.6 ? 'bg-yellow-500' : 'bg-red-500')}></div>
                          </div>
                        </div>
                        <div className="text-sm text-gray-600 bg-gray-50 p-2 rounded">
                          <strong>上下文:</strong> {entity.context}
                        </div>
                      </Card>
                    ))}
                  </div>
                ) : (
                  <Card className="p-8 text-center">
                    <p className="text-gray-500">未识别到实体信息</p>
                  </Card>
                )}
              </div>
            )}

            {/* 关键信息 */}
            {activeTab === 'key_info' && (
              <div className="space-y-4">
                {analysisResult.key_information.length > 0 ? (
                  <div className="space-y-4">
                    {analysisResult.key_information.map((info, index) => {
                      const importance = getImportanceIndicator(info.importance);
                      return (
                        <Card key={index} className="p-4">
                          <div className="flex items-start justify-between mb-3">
                            <div className="flex items-center space-x-2">
                              <span className={clsx('px-2 py-1 rounded text-xs font-medium', getCategoryColor(info.category))}>
                                {info.category}
                              </span>
                              <span className="text-xs text-gray-500">{info.source_section}</span>
                            </div>
                            <div className="flex items-center space-x-2">
                              <span className="text-xs text-gray-500">重要性:</span>
                              <div className={clsx('w-2 h-2 rounded-full', importance.color)}></div>
                              <span className="text-xs text-gray-500">{importance.text}</span>
                            </div>
                          </div>
                          
                          <p className="text-gray-900 mb-3 leading-relaxed">{info.content}</p>
                          
                          {info.keywords.length > 0 && (
                            <div className="flex flex-wrap gap-1">
                              <span className="text-xs text-gray-500 mr-2">关键词:</span>
                              {info.keywords.map((keyword, keywordIndex) => (
                                <span
                                  key={keywordIndex}
                                  className="px-2 py-0.5 bg-blue-100 text-blue-700 rounded text-xs"
                                >
                                  {keyword}
                                </span>
                              ))}
                            </div>
                          )}
                        </Card>
                      );
                    })}
                  </div>
                ) : (
                  <Card className="p-8 text-center">
                    <p className="text-gray-500">未提取到关键信息</p>
                  </Card>
                )}
              </div>
            )}

            {/* 标签分析 */}
            {activeTab === 'tags' && (
              <Card className="p-4">
                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
                  {analysisResult.tags.map((tag, index) => (
                    <div
                      key={index}
                      className="p-3 bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-lg text-center"
                    >
                      <div className="font-medium text-blue-800">{tag}</div>
                    </div>
                  ))}
                </div>
              </Card>
            )}

            {/* 详细统计 */}
            {activeTab === 'stats' && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <Card className="p-4">
                  <h5 className="font-semibold text-gray-900 mb-4">📊 文档统计</h5>
                  <div className="space-y-3">
                    <div className="flex justify-between">
                      <span className="text-gray-600">总字数:</span>
                      <span className="font-medium">{analysisResult.word_count.toLocaleString()}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">段落数:</span>
                      <span className="font-medium">{analysisResult.paragraph_count}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">章节数:</span>
                      <span className="font-medium">{analysisResult.section_count}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">处理时间:</span>
                      <span className="font-medium">{analysisResult.processing_time.toFixed(2)}秒</span>
                    </div>
                  </div>
                </Card>

                <Card className="p-4">
                  <h5 className="font-semibold text-gray-900 mb-4">🎯 提取统计</h5>
                  <div className="space-y-3">
                    <div className="flex justify-between">
                      <span className="text-gray-600">识别实体:</span>
                      <span className="font-medium">{analysisResult.entities.length} 个</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">关键信息:</span>
                      <span className="font-medium">{analysisResult.key_information.length} 条</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">生成标签:</span>
                      <span className="font-medium">{analysisResult.tags.length} 个</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">摘要置信度:</span>
                      <span className="font-medium">{(analysisResult.summary.confidence * 100).toFixed(0)}%</span>
                    </div>
                  </div>
                </Card>
              </div>
            )}
          </div>
        </>
      )}

      {/* 功能说明 */}
      {!analysisResult && !isAnalyzing && (
        <Card className="p-4 bg-gradient-to-r from-blue-50 to-indigo-50 border-blue-200">
          <h4 className="text-md font-semibold text-blue-900 mb-3">🚀 智能文档分析功能</h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
            <div className="space-y-2">
              <div className="flex items-center space-x-2">
                <span className="text-blue-600">📝</span>
                <span className="text-blue-800"><strong>多层次摘要</strong>：生成简要、详细和结构化摘要</span>
              </div>
              <div className="flex items-center space-x-2">
                <span className="text-blue-600">🏷️</span>
                <span className="text-blue-800"><strong>实体识别</strong>：识别组织、人员、财务数据等关键实体</span>
              </div>
              <div className="flex items-center space-x-2">
                <span className="text-blue-600">🔑</span>
                <span className="text-blue-800"><strong>关键信息</strong>：提取重要信息点并按重要性排序</span>
              </div>
            </div>
            <div className="space-y-2">
              <div className="flex items-center space-x-2">
                <span className="text-blue-600">📋</span>
                <span className="text-blue-800"><strong>智能标签</strong>：基于内容自动生成分类标签</span>
              </div>
              <div className="flex items-center space-x-2">
                <span className="text-blue-600">📊</span>
                <span className="text-blue-800"><strong>统计分析</strong>：文档结构和内容统计</span>
              </div>
              <div className="flex items-center space-x-2">
                <span className="text-blue-600">🎯</span>
                <span className="text-blue-800"><strong>置信度评估</strong>：分析结果可信度评分</span>
              </div>
            </div>
          </div>
        </Card>
      )}
    </div>
  );
}; 