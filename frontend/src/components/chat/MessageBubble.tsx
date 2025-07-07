/**
 * MessageBubble 消息气泡组件
 * 用于显示聊天对话中的消息，支持用户和AI消息区分
 */

import React from 'react';
import clsx from 'clsx';
import type { ChatMessage } from '../../types';

interface MessageBubbleProps {
  /** 消息对象 */
  message: ChatMessage;
  /** 是否显示头像 */
  showAvatar?: boolean;
  /** 是否显示时间 */
  showTimestamp?: boolean;
  /** 自定义类名 */
  className?: string;
  /** 消息反应回调 */
  onReaction?: (messageId: string, reaction: string) => void;
}

/**
 * 消息气泡组件
 */
export const MessageBubble: React.FC<MessageBubbleProps> = ({
  message,
  showAvatar = true,
  showTimestamp = true,
  className,
  onReaction: _onReaction,
}) => {
  const { content, type, timestamp, status = 'delivered', avatar } = message;
  const isUser = type === 'user';
  const isAI = type === 'ai';

  const bubbleClasses = clsx(
    'max-w-xs lg:max-w-md xl:max-w-lg px-4 py-3 rounded-2xl shadow-sm',
    'break-words whitespace-pre-wrap',
    {
      // 用户消息样式
      'bg-primary-green text-white ml-auto': isUser,
      
      // AI助手消息样式
      'bg-white text-neutral-900 border border-neutral-200': isAI,
    },
    className
  );

  const containerClasses = clsx(
    'flex gap-3 mb-4',
    {
      'justify-end': isUser,
      'justify-start': isAI,
    }
  );

  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('zh-CN', {
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <div className={containerClasses}>
      {/* AI助手头像 */}
      {!isUser && showAvatar && (
        <div className="flex-shrink-0">
          <div className="w-8 h-8 bg-primary-green rounded-full flex items-center justify-center">
            <span className="text-white text-sm">{avatar || '🤖'}</span>
          </div>
        </div>
      )}

      {/* 消息内容区域 */}
      <div className="flex flex-col max-w-xs lg:max-w-md xl:max-w-lg">
        {/* 消息气泡 */}
        <div className={bubbleClasses}>
          {content}
          
          {/* 发送状态指示器 */}
          {isUser && status === 'sending' && (
            <div className="flex items-center mt-2 text-xs opacity-75">
              <div className="animate-spin w-3 h-3 border border-white border-t-transparent rounded-full mr-2"></div>
              发送中...
            </div>
          )}
          
          {isUser && status === 'error' && (
            <div className="flex items-center mt-2 text-xs text-red-200">
              <span className="mr-1">⚠️</span>
              发送失败
            </div>
          )}
        </div>

        {/* 时间戳 */}
        {showTimestamp && timestamp && (
          <div className={clsx(
            'text-xs text-neutral-500 mt-1',
            {
              'text-right': isUser,
              'text-left': !isUser,
            }
          )}>
            {formatTime(timestamp)}
          </div>
        )}
      </div>

      {/* 用户头像 */}
      {isUser && showAvatar && (
        <div className="flex-shrink-0">
          <div className="w-8 h-8 bg-neutral-300 rounded-full flex items-center justify-center">
            <span className="text-neutral-700 text-sm">👤</span>
          </div>
        </div>
      )}
    </div>
  );
}; 