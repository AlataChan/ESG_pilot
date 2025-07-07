/**
 * Textarea 文本域组件
 * 支持多行文本输入、自动调整高度和验证状态
 */

import React, { forwardRef } from 'react';
import clsx from 'clsx';

interface TextareaProps extends Omit<React.TextareaHTMLAttributes<HTMLTextAreaElement>, 'size'> {
  /** 文本域标签 */
  label?: string;
  /** 文本域描述 */
  description?: string;
  /** 错误信息 */
  error?: string;
  /** 尺寸 */
  size?: 'small' | 'medium' | 'large';
  /** 变体样式 */
  variant?: 'default' | 'outline' | 'filled';
  /** 是否自动调整高度 */
  autoResize?: boolean;
  /** 是否全宽度 */
  fullWidth?: boolean;
}

/**
 * 文本域组件
 */
export const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(
  (
    {
      label,
      description,
      error,
      size = 'medium',
      variant = 'default',
      autoResize = false,
      fullWidth = false,
      disabled,
      className,
      id,
      onChange,
      ...props
    },
    ref
  ) => {
    const textareaId = id || `textarea-${Math.random().toString(36).substr(2, 9)}`;

    const sizeClasses = {
      small: 'px-3 py-2 text-sm min-h-[80px]',
      medium: 'px-4 py-3 text-base min-h-[100px]',
      large: 'px-5 py-4 text-lg min-h-[120px]',
    };

    const variantClasses = {
      default: 'border-neutral-300 bg-white focus:border-primary-green focus:ring-primary-green',
      outline: 'border-2 border-neutral-300 bg-transparent focus:border-primary-green focus:ring-primary-green',
      filled: 'border-transparent bg-neutral-100 focus:bg-white focus:border-primary-green focus:ring-primary-green',
    };

    const textareaClasses = clsx(
      // 基础样式
      'block w-full rounded-lg border transition-colors duration-200 resize-vertical',
      'focus:outline-none focus:ring-2 focus:ring-opacity-50',
      'placeholder:text-neutral-400',
      
      // 尺寸
      sizeClasses[size],
      
      // 变体
      variantClasses[variant],
      
      // 状态
      {
        'border-red-300 focus:border-red-500 focus:ring-red-500': error,
        'opacity-60 cursor-not-allowed': disabled,
        'resize-none': autoResize,
      },
      
      // 宽度
      fullWidth ? 'w-full' : '',
      
      className
    );

    const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
      if (autoResize) {
        e.target.style.height = 'auto';
        e.target.style.height = `${e.target.scrollHeight}px`;
      }
      
      if (onChange) {
        onChange(e);
      }
    };

    return (
      <div className={clsx('relative', fullWidth ? 'w-full' : '')}>
        {/* 标签 */}
        {label && (
          <label
            htmlFor={textareaId}
            className="block text-sm font-medium text-neutral-700 mb-2"
          >
            {label}
          </label>
        )}

        {/* 描述 */}
        {description && !error && (
          <p className="text-sm text-neutral-600 mb-2">{description}</p>
        )}

        {/* 文本域 */}
        <textarea
          ref={ref}
          id={textareaId}
          disabled={disabled}
          className={textareaClasses}
          onChange={handleChange}
          {...props}
        />

        {/* 错误信息 */}
        {error && (
          <p className="mt-2 text-sm text-red-600">{error}</p>
        )}
      </div>
    );
  }
);

Textarea.displayName = 'Textarea'; 