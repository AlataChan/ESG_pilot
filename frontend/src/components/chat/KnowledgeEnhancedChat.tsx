/**
 * KnowledgeEnhancedChat 知识库增强聊天组件
 * 集成私有知识库搜索，提供基于文档内容的智能对话
 */

import React, { useState, useEffect, useRef } from 'react';
import clsx from 'clsx';
import { ChatInput } from './ChatInput';
import { MessageBubble } from './MessageBubble';
import { Button } from '../ui/Button';
import type { ChatMessage } from '../../types';

interface ChatResponse {
  message: string;
  conversation_id: string;
  has_knowledge_context: boolean;
  knowledge_sources: string[];
  suggestions: string[];
  timestamp: string;
}

interface KnowledgeEnhancedChatProps {
  /** 用户ID */
  userId: string;
  /** 是否启用知识库搜索 */
  enableKnowledgeSearch?: boolean;
  /** 聊天窗口高度 */
  height?: string;
  /** 自定义类名 */
  className?: string;
  /** 初始欢迎消息 */
  welcomeMessage?: string;
}

/**
 * 知识库增强聊天组件
 */
export const KnowledgeEnhancedChat: React.FC<KnowledgeEnhancedChatProps> = ({
  userId,
  enableKnowledgeSearch = true,
  height = "600px",
  className,
  welcomeMessage
}) => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [conversationId, setConversationId] = useState<string>('');
  const [isLoading, setIsLoading] = useState(false);
  const [knowledgeEnabled, setKnowledgeEnabled] = useState(enableKnowledgeSearch);
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [currentKnowledgeSources, setCurrentKnowledgeSources] = useState<string[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // 自动滚动到最新消息
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // 初始化聊天
  useEffect(() => {
    if (welcomeMessage || !conversationId) {
      const welcome: ChatMessage = {
        id: 'welcome_' + Date.now(),
        type: 'ai',
        content: welcomeMessage || `👋 您好！我是您的智能助手。

🔍 **知识库搜索已启用** - 我可以搜索您的私有文档来回答问题
📚 包括：公司政策、报告、流程文档等
🎯 提问技巧：具体提及文档、政策或您想了解的主题

💡 您可以问我关于公司的任何问题，我会尽力从您的知识库中找到准确答案！`,
        timestamp: new Date().toISOString(),
        status: 'delivered',
        avatar: '🤖'
      };
      
      setMessages([welcome]);
      setConversationId(`chat_${Date.now()}_${userId}`);
      
      // 获取聊天建议
      fetchChatSuggestions();
    }
  }, [userId, welcomeMessage]);

  // 获取聊天建议
  const fetchChatSuggestions = async () => {
    try {
      const response = await fetch(`/api/v1/chat/suggestions/${userId}`);
      if (response.ok) {
        const data = await response.json();
        setSuggestions(data.data?.suggestions || []);
      }
    } catch (error) {
      console.error('获取聊天建议失败:', error);
    }
  };

  // 发送消息
  const handleSendMessage = async (content: string) => {
    if (!content.trim() || isLoading) return;

    // 添加用户消息
    const userMessage: ChatMessage = {
      id: 'user_' + Date.now(),
      type: 'user',
      content: content.trim(),
      timestamp: new Date().toISOString(),
      status: 'sending'
    };

    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);

    try {
      // 调用聊天API
      const response = await fetch('/api/v1/chat/send', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: content,
          conversation_id: conversationId,
          user_id: userId,
          use_knowledge: knowledgeEnabled,
          knowledge_filters: {}
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const result = await response.json();
      const chatResponse: ChatResponse = result.data;

      // 更新用户消息状态
      setMessages(prev => prev.map(msg => 
        msg.id === userMessage.id 
          ? { ...msg, status: 'delivered' as const }
          : msg
      ));

      // 添加AI回复
      const aiMessage: ChatMessage = {
        id: 'ai_' + Date.now(),
        type: 'ai',
        content: chatResponse.message,
        timestamp: chatResponse.timestamp,
        status: 'delivered',
        avatar: chatResponse.has_knowledge_context ? '📚' : '🤖',
        metadata: {
          has_knowledge_context: chatResponse.has_knowledge_context,
          knowledge_sources: chatResponse.knowledge_sources
        }
      };

      setMessages(prev => [...prev, aiMessage]);
      
      // 更新建议和知识来源
      setSuggestions(chatResponse.suggestions);
      setCurrentKnowledgeSources(chatResponse.knowledge_sources);

    } catch (error) {
      console.error('发送消息失败:', error);
      
      // 更新用户消息为错误状态
      setMessages(prev => prev.map(msg => 
        msg.id === userMessage.id 
          ? { ...msg, status: 'error' as const }
          : msg
      ));

      // 添加错误消息
      const errorMessage: ChatMessage = {
        id: 'error_' + Date.now(),
        type: 'ai',
        content: `抱歉，发送消息时遇到错误：${error instanceof Error ? error.message : '未知错误'}`,
        timestamp: new Date().toISOString(),
        status: 'delivered',
        avatar: '⚠️'
      };
      
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };



  // 使用建议问题
  const handleSuggestionClick = (suggestion: string) => {
    handleSendMessage(suggestion);
  };

  // 清空对话
  const handleClearChat = () => {
    setMessages([]);
    setConversationId(`chat_${Date.now()}_${userId}`);
    setCurrentKnowledgeSources([]);
    
    // 重新添加欢迎消息
    setTimeout(() => {
      const welcome: ChatMessage = {
        id: 'welcome_' + Date.now(),
        type: 'ai',
        content: '对话已清空。有什么可以帮助您的吗？',
        timestamp: new Date().toISOString(),
        status: 'delivered',
        avatar: '🤖'
      };
      setMessages([welcome]);
    }, 100);
  };

  return (
    <div className={clsx('flex flex-col bg-gray-50', className)} style={{ height }}>
      {/* 聊天头部 */}
      <div className="flex-shrink-0 bg-white border-b border-gray-200 px-4 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-primary-green rounded-full flex items-center justify-center">
              <span className="text-white text-lg">🤖</span>
            </div>
            <div>
              <h3 className="text-lg font-semibold text-gray-900">
                智能助手
                {knowledgeEnabled && (
                  <span className="ml-2 inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800">
                    📚 知识库已启用
                  </span>
                )}
              </h3>
              <p className="text-sm text-gray-500">
                基于您的私有知识库提供智能回答
              </p>
            </div>
          </div>
          
          <div className="flex items-center space-x-2">
            <Button
              variant="outline"
              size="small"
              onClick={() => setKnowledgeEnabled(!knowledgeEnabled)}
              className={clsx(
                'text-sm',
                knowledgeEnabled ? 'bg-green-50 text-green-700 border-green-300' : ''
              )}
            >
              {knowledgeEnabled ? '🔍 知识库开启' : '🔍 知识库关闭'}
            </Button>
            
            <Button
              variant="outline"
              size="small"
              onClick={handleClearChat}
              className="text-sm"
            >
              🗑️ 清空对话
            </Button>
          </div>
        </div>
      </div>

      {/* 消息列表 */}
      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4">
        {messages.map((message) => (
          <MessageBubble key={message.id} message={message} />
        ))}
        
        {/* 加载指示器 */}
        {isLoading && (
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 bg-primary-green rounded-full flex items-center justify-center">
              <span className="text-white text-sm">🤖</span>
            </div>
            <div className="bg-white px-4 py-3 rounded-2xl border border-gray-200 shadow-sm">
              <div className="flex items-center space-x-1">
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
              </div>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      {/* 知识来源显示 */}
      {currentKnowledgeSources.length > 0 && (
        <div className="flex-shrink-0 bg-blue-50 border-t border-blue-200 px-4 py-2">
          <div className="flex items-center space-x-2 text-sm text-blue-700">
            <span className="font-medium">📚 参考来源:</span>
            <span>{currentKnowledgeSources.join(', ')}</span>
          </div>
        </div>
      )}

      {/* 建议问题 */}
      {suggestions.length > 0 && messages.length <= 1 && (
        <div className="flex-shrink-0 bg-gray-50 border-t border-gray-200 px-4 py-3">
          <div className="mb-2">
            <span className="text-sm font-medium text-gray-700">💡 您可以试试这些问题：</span>
          </div>
          <div className="flex flex-wrap gap-2">
            {suggestions.slice(0, 3).map((suggestion, index) => (
              <button
                key={index}
                onClick={() => handleSuggestionClick(suggestion)}
                className="px-3 py-1 text-sm text-gray-600 bg-white rounded-full border border-gray-300 hover:bg-gray-50 hover:border-gray-400 transition-colors"
                disabled={isLoading}
              >
                {suggestion}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* 输入区域 */}
      <div className="flex-shrink-0 bg-white border-t border-gray-200 px-4 py-4">
        <ChatInput
          onSendMessage={handleSendMessage}
          disabled={isLoading}
          placeholder={
            knowledgeEnabled 
              ? "询问关于您的文档、政策或任何问题..." 
              : "输入您的问题..."
          }
          maxLength={2000}
        />
        
        {/* 功能提示 */}
        <div className="mt-2 flex items-center justify-between text-xs text-gray-500">
          <div className="flex items-center space-x-4">
            <span>💡 支持文档内容搜索</span>
            <span>🎯 可询问具体政策或流程</span>
            <span>📚 自动引用相关来源</span>
          </div>
          <div>
            按 Enter 发送，Shift + Enter 换行
          </div>
        </div>
      </div>
    </div>
  );
};