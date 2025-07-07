/**
 * DocumentQA 文档问答组件
 * 支持基于特定文档内容的智能问答，实现RAG功能
 */

import React, { useState, useEffect } from 'react';
import clsx from 'clsx';
import { Card } from '../ui/Card';
import { Button } from '../ui/Button';
import { ChatInput } from '../chat/ChatInput';
import type { Document } from '../../types';

interface QASource {
  content: string;
  document_id: string;
  page_number: number;
  chunk_index: number;
  similarity_score: number;
  metadata: Record<string, any>;
}

interface QAResult {
  question: string;
  answer: string;
  confidence: number;
  reasoning: string;
  sources: QASource[];
  timestamp: string;
}

interface DocumentQAProps {
  /** 文档信息 */
  document: Document;
  /** 用户ID */
  userId: string;
  /** 自定义类名 */
  className?: string;
  /** 是否显示文档信息 */
  showDocumentInfo?: boolean;
}

/**
 * 文档问答组件
 */
export const DocumentQA: React.FC<DocumentQAProps> = ({
  document,
  userId,
  className,
  showDocumentInfo = true
}) => {
  const [qaHistory, setQAHistory] = useState<QAResult[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [currentQuestion, setCurrentQuestion] = useState('');
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [insights, setInsights] = useState<any[]>([]);
  const [showInsights, setShowInsights] = useState(false);

  // 获取文档洞察
  const fetchDocumentInsights = async () => {
    try {
      setIsLoading(true);
      const response = await fetch(
        `/api/v1/rag/document-insights/${document.id}?user_id=${userId}`
      );
      
      if (response.ok) {
        const data = await response.json();
        setInsights(data.data?.insights || []);
      }
    } catch (error) {
      console.error('获取文档洞察失败:', error);
    } finally {
      setIsLoading(false);
    }
  };

  // 获取问题建议
  const fetchQuestionSuggestions = async () => {
    try {
      const response = await fetch(
        `/api/v1/rag/question-suggestions/${userId}?document_id=${document.id}`
      );
      
      if (response.ok) {
        const data = await response.json();
        setSuggestions(data.data?.suggestions || []);
      }
    } catch (error) {
      console.error('获取问题建议失败:', error);
    }
  };

  // 初始化
  useEffect(() => {
    fetchQuestionSuggestions();
  }, [document.id, userId]);

  // 提交问题
  const handleAskQuestion = async (question: string) => {
    if (!question.trim() || isLoading) return;

    setIsLoading(true);
    setCurrentQuestion(question);

    try {
      const response = await fetch('/api/v1/rag/ask-document', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          question: question.trim(),
          document_id: document.id,
          user_id: userId
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const result = await response.json();
      const qaResult: QAResult = result.data;

      setQAHistory(prev => [qaResult, ...prev]);
      setCurrentQuestion('');

    } catch (error) {
      console.error('问答失败:', error);
      
      // 添加错误结果
      const errorResult: QAResult = {
        question: question,
        answer: `抱歉，处理您的问题时遇到错误：${error instanceof Error ? error.message : '未知错误'}`,
        confidence: 0,
        reasoning: '系统错误',
        sources: [],
        timestamp: new Date().toISOString()
      };
      
      setQAHistory(prev => [errorResult, ...prev]);
    } finally {
      setIsLoading(false);
    }
  };

  // 使用建议问题
  const handleSuggestionClick = (suggestion: string) => {
    handleAskQuestion(suggestion);
  };

  // 置信度颜色
  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'text-green-600 bg-green-100';
    if (confidence >= 0.6) return 'text-yellow-600 bg-yellow-100';
    if (confidence >= 0.4) return 'text-orange-600 bg-orange-100';
    return 'text-red-600 bg-red-100';
  };

  // 置信度文本
  const getConfidenceText = (confidence: number) => {
    if (confidence >= 0.8) return '高置信度';
    if (confidence >= 0.6) return '中等置信度';
    if (confidence >= 0.4) return '低置信度';
    return '极低置信度';
  };

  return (
    <div className={clsx('space-y-6', className)}>
      {/* 文档信息 */}
      {showDocumentInfo && (
        <Card className="p-4">
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                📄 {document.name}
              </h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm text-gray-600">
                <div>
                  <span className="font-medium">类型:</span> {document.type?.toUpperCase()}
                </div>
                <div>
                  <span className="font-medium">大小:</span> {document.size ? `${(document.size / 1024 / 1024).toFixed(2)} MB` : 'N/A'}
                </div>
                <div>
                  <span className="font-medium">状态:</span> 
                  <span className={clsx(
                    'ml-1 px-2 py-0.5 rounded text-xs',
                    document.status === 'completed' ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'
                  )}>
                    {document.status === 'completed' ? '已处理' : '处理中'}
                  </span>
                </div>
                <div>
                  <span className="font-medium">上传时间:</span> {new Date(document.uploadedAt).toLocaleDateString()}
                </div>
              </div>
            </div>
            
            <div className="flex items-center space-x-2 ml-4">
              <Button
                variant="outline"
                size="small"
                onClick={() => {
                  setShowInsights(!showInsights);
                  if (!showInsights && insights.length === 0) {
                    fetchDocumentInsights();
                  }
                }}
                disabled={isLoading}
              >
                {showInsights ? '隐藏洞察' : '📊 文档洞察'}
              </Button>
            </div>
          </div>
        </Card>
      )}

      {/* 文档洞察 */}
      {showInsights && (
        <Card className="p-4">
          <h4 className="text-md font-semibold text-gray-900 mb-4">📊 文档洞察</h4>
          {insights.length > 0 ? (
            <div className="space-y-4">
              {insights.slice(0, 3).map((insight, index) => (
                <div key={index} className="border-l-4 border-blue-500 pl-4">
                  <div className="flex items-center justify-between mb-2">
                    <h5 className="font-medium text-gray-900">{insight.question}</h5>
                    <span className={clsx(
                      'px-2 py-1 rounded text-xs font-medium',
                      getConfidenceColor(insight.confidence)
                    )}>
                      {getConfidenceText(insight.confidence)}
                    </span>
                  </div>
                  <p className="text-gray-700 text-sm">{insight.answer}</p>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center text-gray-500 py-4">
              {isLoading ? '正在生成文档洞察...' : '暂无洞察信息'}
            </div>
          )}
        </Card>
      )}

      {/* 问答历史 */}
      {qaHistory.length > 0 && (
        <div className="space-y-4">
          <h4 className="text-lg font-semibold text-gray-900">💬 问答记录</h4>
          
          {qaHistory.map((qa, index) => (
            <Card key={index} className="p-4">
              {/* 问题 */}
              <div className="mb-4">
                <div className="flex items-center space-x-2 mb-2">
                  <span className="text-blue-600 font-medium">🤔 问题:</span>
                  <span className="text-sm text-gray-500">
                    {new Date(qa.timestamp).toLocaleString()}
                  </span>
                </div>
                <p className="text-gray-900 bg-blue-50 p-3 rounded-lg">{qa.question}</p>
              </div>

              {/* 答案 */}
              <div className="mb-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-green-600 font-medium">💡 答案:</span>
                  <div className="flex items-center space-x-2">
                    <span className={clsx(
                      'px-2 py-1 rounded text-xs font-medium',
                      getConfidenceColor(qa.confidence)
                    )}>
                      {getConfidenceText(qa.confidence)} ({(qa.confidence * 100).toFixed(0)}%)
                    </span>
                  </div>
                </div>
                <div className="text-gray-900 bg-green-50 p-3 rounded-lg whitespace-pre-wrap">
                  {qa.answer}
                </div>
              </div>

              {/* 来源信息 */}
              {qa.sources.length > 0 && (
                <div className="mb-4">
                  <span className="text-purple-600 font-medium mb-2 block">📚 参考来源:</span>
                  <div className="space-y-2">
                    {qa.sources.map((source, sourceIndex) => (
                      <div key={sourceIndex} className="bg-purple-50 p-3 rounded-lg border-l-4 border-purple-500">
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-sm font-medium text-purple-700">
                            来源 {sourceIndex + 1}
                            {source.page_number && ` - 第${source.page_number}页`}
                          </span>
                          <span className="text-xs text-purple-600">
                            相关度: {(source.similarity_score * 100).toFixed(0)}%
                          </span>
                        </div>
                        <p className="text-sm text-gray-700">
                          {source.content.length > 200 
                            ? `${source.content.substring(0, 200)}...` 
                            : source.content
                          }
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* 推理过程 */}
              {qa.reasoning && (
                <div className="text-sm text-gray-600 bg-gray-50 p-3 rounded-lg">
                  <span className="font-medium">🧠 推理过程:</span> {qa.reasoning}
                </div>
              )}
            </Card>
          ))}
        </div>
      )}

      {/* 问题建议 */}
      {qaHistory.length === 0 && suggestions.length > 0 && (
        <Card className="p-4">
          <h4 className="text-md font-semibold text-gray-900 mb-4">💡 建议问题</h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {suggestions.slice(0, 6).map((suggestion, index) => (
              <button
                key={index}
                onClick={() => handleSuggestionClick(suggestion)}
                disabled={isLoading}
                className="text-left p-3 bg-blue-50 hover:bg-blue-100 rounded-lg border border-blue-200 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <span className="text-sm text-blue-700">{suggestion}</span>
              </button>
            ))}
          </div>
        </Card>
      )}

      {/* 问题输入 */}
      <Card className="p-4">
        <div className="mb-4">
          <h4 className="text-md font-semibold text-gray-900 mb-2">🤔 向文档提问</h4>
          <p className="text-sm text-gray-600">
            您可以就此文档的内容提出任何问题，我会基于文档内容为您提供准确答案。
          </p>
        </div>
        
        <ChatInput
          onSendMessage={handleAskQuestion}
          disabled={isLoading || document.status !== 'completed'}
          placeholder={
            document.status !== 'completed' 
              ? "文档正在处理中，请稍后再试..." 
              : "询问关于此文档的任何问题..."
          }
          maxLength={500}
        />
        
        {/* 加载状态 */}
        {isLoading && (
          <div className="mt-4 flex items-center justify-center py-4">
            <div className="flex items-center space-x-3">
              <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary-green"></div>
              <span className="text-gray-600">
                {currentQuestion ? '正在分析问题并生成答案...' : '正在处理...'}
              </span>
            </div>
          </div>
        )}
        
        {/* 功能说明 */}
        <div className="mt-4 text-xs text-gray-500 space-y-1">
          <div>💡 <strong>智能问答</strong>：基于文档内容精准回答问题</div>
          <div>📊 <strong>置信度评估</strong>：显示答案的可信度评分</div>
          <div>📚 <strong>来源追溯</strong>：标注答案来源的具体段落</div>
          <div>🧠 <strong>推理透明</strong>：展示AI的推理过程</div>
        </div>
      </Card>
    </div>
  );
};