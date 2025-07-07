/**
 * Profile 页面组件
 * 企业画像生成页面，多Agent协作的智能对话界面
 * 针对1440*900分辨率优化
 */

import React, { useState, useRef, useEffect } from 'react';
import { useCurrentConversation, useConversationActions, useLoading } from '../stores/appStore';
import { MessageBubble } from '../components/chat/MessageBubble';
import { ChatInput } from '../components/chat/ChatInput';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import type { ChatMessage } from '../types';

/**
 * Agent状态显示组件
 */
interface AgentStatus {
  id: string;
  name: string;
  status: 'idle' | 'thinking' | 'working' | 'completed';
  currentTask?: string;
  icon: string;
}

const AgentStatusCard: React.FC<{ agent: AgentStatus }> = ({ agent }) => {
  const getStatusColor = (status: AgentStatus['status']) => {
    switch (status) {
      case 'idle': return 'bg-neutral-100 text-neutral-600';
      case 'thinking': return 'bg-blue-100 text-blue-700';
      case 'working': return 'bg-primary-green text-white';
      case 'completed': return 'bg-green-100 text-green-700';
      default: return 'bg-neutral-100 text-neutral-600';
    }
  };

  const getStatusText = (status: AgentStatus['status']) => {
    switch (status) {
      case 'idle': return '待命中';
      case 'thinking': return '分析中';
      case 'working': return '处理中';
      case 'completed': return '已完成';
      default: return '未知';
    }
  };

  return (
    <div className="bg-white border border-neutral-200 rounded-lg p-3 space-y-2">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <span className="text-lg">{agent.icon}</span>
          <span className="font-medium text-sm text-neutral-900">{agent.name}</span>
        </div>
        <div className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(agent.status)}`}>
          {getStatusText(agent.status)}
        </div>
      </div>
      {agent.currentTask && (
        <p className="text-xs text-neutral-600 line-clamp-2">{agent.currentTask}</p>
      )}
    </div>
  );
};

/**
 * 企业画像页面组件
 */
const ProfilePage: React.FC = () => {
  const currentConversation = useCurrentConversation();
  const { sendMessage, resetCurrentConversation } = useConversationActions();
  const loading = useLoading();
  
  // Agent状态管理
  const [agents, setAgents] = useState<AgentStatus[]>([
    {
      id: 'consultant',
      name: 'ESG智能助手',
      status: 'working',
      currentTask: '引导用户完成企业画像信息收集',
      icon: '🤖'
    },
    {
      id: 'assessment',
      name: '评估分析Agent',
      status: 'idle',
      icon: '📊'
    },
    {
      id: 'data',
      name: '数据处理Agent',
      status: 'idle',
      icon: '🔍'
    },
    {
      id: 'report',
      name: '报告生成Agent',
      status: 'idle',
      icon: '📝'
    }
  ]);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  // 自动滚动到最新消息
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [currentConversation?.messages]);

  // 处理发送消息
  const handleSendMessage = async (content: string) => {
    if (!currentConversation || loading) return;

    try {
      // 更新Agent状态
      setAgents(prev => prev.map(agent => 
        agent.id === 'consultant' 
          ? { ...agent, status: 'thinking', currentTask: '处理用户消息并分析下一步行动' }
          : agent
      ));

      // 调用真实API
      await sendMessage(content);

      // 根据对话进度更新Agent状态
      const progress = currentConversation.progress || 0;
      updateAgentStatusByProgress(progress);

    } catch (error) {
      console.error('发送消息失败:', error);
      // 重置Agent状态
      setAgents(prev => prev.map(agent => 
        agent.id === 'consultant' 
          ? { ...agent, status: 'idle', currentTask: undefined }
          : agent
      ));
    }
  };

  // 根据进度更新Agent状态
  const updateAgentStatusByProgress = (progress: number) => {
    setAgents(prev => prev.map(agent => {
      switch (agent.id) {
        case 'consultant':
          return {
            ...agent,
            status: progress < 100 ? 'working' : 'completed',
            currentTask: progress < 100 ? '继续收集企业信息' : '信息收集完成'
          };
        case 'assessment':
          return {
            ...agent,
            status: progress > 30 ? (progress < 100 ? 'working' : 'completed') : 'idle',
            currentTask: progress > 30 ? '分析企业ESG风险和机会' : undefined
          };
        case 'data':
          return {
            ...agent,
            status: progress > 60 ? (progress < 100 ? 'working' : 'completed') : 'idle',
            currentTask: progress > 60 ? '处理和验证企业数据' : undefined
          };
        case 'report':
          return {
            ...agent,
            status: progress > 80 ? (progress < 100 ? 'working' : 'completed') : 'idle',
            currentTask: progress > 80 ? '生成ESG画像报告' : undefined
          };
        default:
          return agent;
      }
    }));
  };

  if (!currentConversation) {
    return (
      <div className="chat-container bg-neutral-50 flex items-center justify-center optimized-1440-900">
        <Card className="max-w-md mx-auto text-center p-6">
          <h2 className="text-lg font-semibold text-neutral-900 mb-3">
            没有活跃的对话
          </h2>
          <p className="text-neutral-600 mb-4">
            请先在首页启动企业画像生成
          </p>
          <Button 
            onClick={() => window.location.href = '/'}
            variant="primary"
          >
            返回首页
          </Button>
        </Card>
      </div>
    );
  }

  return (
    <div className="chat-container bg-neutral-50 flex flex-col layout-1440 optimized-1440-900">
      {/* 页面头部 - 1440*900优化 */}
      <div className="bg-white border-b border-neutral-200 px-4 2xl:px-6 py-3 2xl:py-4 flex-shrink-0">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-lg 2xl:text-xl font-semibold text-neutral-900">
              企业ESG画像生成
            </h1>
            <div className="flex items-center space-x-3 2xl:space-x-4 mt-1">
              <p className="text-xs 2xl:text-sm text-neutral-600">
                多Agent协作智能分析
              </p>
              <div className="text-xs 2xl:text-sm text-primary-green font-medium">
                进度: {currentConversation.progress || 0}/100
              </div>
              <div className="text-xs 2xl:text-sm text-neutral-500">
                阶段: {currentConversation.stage || '初始化'}
              </div>
            </div>
          </div>
          
          <div className="flex items-center space-x-3">
            <Button
              variant="outline"
              size="small"
              onClick={() => {
                resetCurrentConversation();
                // 重置Agent状态
                setAgents(prev => prev.map(agent => ({
                  ...agent,
                  status: agent.id === 'consultant' ? 'working' : 'idle',
                  currentTask: agent.id === 'consultant' ? '等待用户开始对话' : undefined
                })));
              }}
              disabled={loading}
            >
              🗑️ 清空对话
            </Button>
            <Button
              variant="outline"
              size="small"
              onClick={() => window.location.reload()}
              disabled={loading}
            >
              🔄 重新开始
            </Button>
            <Button
              variant="ghost"
              size="small"
              onClick={() => {
                console.log('当前对话状态:', currentConversation);
                console.log('消息数量:', currentConversation.messages.length);
                console.log('最后5条消息:', currentConversation.messages.slice(-5));
                
                // 导出对话历史到剪贴板
                const conversationData = {
                  id: currentConversation.id,
                  progress: currentConversation.progress,
                  stage: currentConversation.stage,
                  status: currentConversation.status,
                  messages: currentConversation.messages.map(m => ({
                    type: m.type,
                    content: m.content,
                    timestamp: m.timestamp,
                    status: m.status
                  }))
                };
                
                navigator.clipboard.writeText(JSON.stringify(conversationData, null, 2))
                  .then(() => alert('对话数据已复制到剪贴板'))
                  .catch(() => console.log('复制失败'));
              }}
            >
              🔍 调试信息
            </Button>
          </div>
        </div>
      </div>

      {/* 主要内容区域 */}
      <div className="flex-1 flex overflow-hidden">
        {/* 聊天区域 */}
        <div className="flex-1 flex flex-col min-w-0">
          {/* 消息列表 - 可滚动，修复滚动问题 */}
          <div className="flex-1 overflow-y-auto px-4 2xl:px-6 py-3 2xl:py-4">
            <div className="space-y-3 2xl:space-y-4">
              {currentConversation.messages.map((message: ChatMessage) => (
                <MessageBubble
                  key={message.id}
                  message={message}
                />
              ))}
              
              {/* AI输入指示器 */}
              {loading && (
                <div className="flex items-center space-x-3">
                  <div className="w-8 h-8 bg-primary-green rounded-full flex items-center justify-center">
                    <span className="text-white text-sm">🤖</span>
                  </div>
                  <div className="bg-white px-4 py-3 rounded-2xl border border-neutral-200 shadow-sm">
                    <div className="flex items-center space-x-1">
                      <div className="w-2 h-2 bg-neutral-400 rounded-full animate-bounce"></div>
                      <div className="w-2 h-2 bg-neutral-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                      <div className="w-2 h-2 bg-neutral-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                    </div>
                  </div>
                </div>
              )}
              
              <div ref={messagesEndRef} />
            </div>
          </div>

          {/* 输入区域 - 固定底部 */}
          <div className="border-t border-neutral-200 bg-white px-4 2xl:px-6 py-3 2xl:py-4 flex-shrink-0">
            <ChatInput
              onSendMessage={handleSendMessage}
              disabled={loading}
              placeholder="详细描述您公司的ESG相关信息..."
              maxLength={2000}
            />
          </div>
        </div>

        {/* Agent状态侧边栏 */}
        <div className="w-64 2xl:w-80 bg-white border-l border-neutral-200 p-3 2xl:p-4 flex-shrink-0 overflow-y-auto">
          <div className="space-y-3 2xl:space-y-4">
            <h3 className="font-semibold text-neutral-900 text-sm">Agent协作状态</h3>
            
            {agents.map((agent) => (
              <AgentStatusCard key={agent.id} agent={agent} />
            ))}

            {/* 对话提示 */}
            <div className="mt-4 2xl:mt-6 p-3 2xl:p-4 bg-neutral-50 rounded-lg">
              <h4 className="font-medium text-neutral-800 text-sm mb-2">💡 对话提示</h4>
              <ul className="text-xs text-neutral-600 space-y-1">
                <li>• 详细描述公司在各方面的具体做法</li>
                <li>• 包含环境、社会、治理三个维度</li>
                <li>• 提供具体数据和案例更有助于分析</li>
                <li>• 可以分多次回答，逐步完善信息</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProfilePage; 