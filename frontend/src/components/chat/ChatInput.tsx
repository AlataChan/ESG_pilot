/**
 * ChatInput 聊天输入组件
 * 用于发送消息的输入框，支持快捷键和多行输入
 */

import React, { useState, useRef, useEffect } from 'react';
import clsx from 'clsx';
import { Button } from '../ui/Button';

interface ChatInputProps {
  /** 发送消息的回调 */
  onSendMessage: (message: string) => void;
  /** 是否正在发送 */
  isSending?: boolean;
  /** 占位符文本 */
  placeholder?: string;
  /** 是否禁用 */
  disabled?: boolean;
  /** 最大字符数 */
  maxLength?: number;
  /** 自定义类名 */
  className?: string;
}

/**
 * 聊天输入组件
 */
export const ChatInput: React.FC<ChatInputProps> = ({
  onSendMessage,
  isSending = false,
  placeholder = '输入您的问题...',
  disabled = false,
  maxLength = 1000,
  className,
}) => {
  const [message, setMessage] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // 自动调整文本域高度
  const adjustTextareaHeight = () => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = 'auto';
      const newHeight = Math.min(textarea.scrollHeight, 120); // 最大高度120px
      textarea.style.height = `${newHeight}px`;
    }
  };

  // 处理输入变化
  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const newMessage = e.target.value;
    if (newMessage.length <= maxLength) {
      setMessage(newMessage);
      adjustTextareaHeight();
    }
  };

  // 处理发送消息
  const handleSendMessage = () => {
    const trimmedMessage = message.trim();
    if (trimmedMessage && !isSending && !disabled) {
      onSendMessage(trimmedMessage);
      setMessage('');
      
      // 重置文本域高度
      setTimeout(() => {
        if (textareaRef.current) {
          textareaRef.current.style.height = 'auto';
        }
      }, 0);
    }
  };

  // 处理键盘事件
  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    // Ctrl/Cmd + Enter 发送消息
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      e.preventDefault();
      handleSendMessage();
    }
    
    // 单独的 Enter 键换行 (默认行为)
    if (e.key === 'Enter' && !e.shiftKey && !e.ctrlKey && !e.metaKey) {
      // 如果消息不为空，则发送；否则换行
      const trimmedMessage = message.trim();
      if (trimmedMessage) {
        e.preventDefault();
        handleSendMessage();
      }
    }
  };

  // 初始化高度
  useEffect(() => {
    adjustTextareaHeight();
  }, []);

  const canSend = message.trim().length > 0 && !isSending && !disabled;

  return (
    <div className={clsx('flex flex-col space-y-3', className)}>
      {/* 字符计数器 */}
      {maxLength && (
        <div className="flex justify-between items-center text-sm text-neutral-500">
          <div className="text-xs">
            💡 按 Enter 发送，Shift + Enter 换行
          </div>
          <div className={clsx(
            'text-xs',
            {
              'text-red-500': message.length > maxLength * 0.9,
              'text-neutral-500': message.length <= maxLength * 0.9,
            }
          )}>
            {message.length}/{maxLength}
          </div>
        </div>
      )}

      {/* 输入区域 */}
      <div className="flex items-end space-x-3 p-4 bg-white rounded-lg border border-neutral-200 shadow-sm">
        {/* 文本输入框 */}
        <div className="flex-1 relative">
          <textarea
            ref={textareaRef}
            value={message}
            onChange={handleInputChange}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
            disabled={disabled || isSending}
            rows={1}
            className={clsx(
              'w-full px-0 py-2 text-base text-neutral-900 placeholder:text-neutral-400',
              'border-none outline-none resize-none',
              'min-h-[40px] max-h-[120px] leading-6',
              {
                'opacity-60 cursor-not-allowed': disabled || isSending,
              }
            )}
            style={{
              lineHeight: '1.5',
            }}
          />
        </div>

        {/* 发送按钮 */}
        <Button
          variant={canSend ? 'primary' : 'ghost'}
          size="medium"
          onClick={handleSendMessage}
          disabled={!canSend}
          loading={isSending}
          className="flex-shrink-0 rounded-lg min-w-[100px]"
        >
          {isSending ? (
            <>
              <div className="animate-spin w-4 h-4 border border-white border-t-transparent rounded-full mr-2"></div>
              发送中
            </>
          ) : (
            <>
              <svg
                className="w-4 h-4 mr-2"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"
                />
              </svg>
              发送
            </>
          )}
        </Button>
      </div>

      {/* 快捷提示 */}
      {message.trim().length === 0 && (
        <div className="flex flex-wrap gap-2">
          {[
            '请介绍一下您公司的基本情况',
            '我们想了解ESG评估的流程',
            '有哪些改进建议？',
          ].map((suggestion, index) => (
            <button
              key={index}
              onClick={() => setMessage(suggestion)}
              className={clsx(
                'px-3 py-1 text-sm text-neutral-600 bg-neutral-100 rounded-full',
                'hover:bg-neutral-200 transition-colors duration-200',
                'disabled:opacity-60 disabled:cursor-not-allowed'
              )}
              disabled={disabled || isSending}
            >
              {suggestion}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}; 