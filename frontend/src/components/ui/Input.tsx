/**
 * Input 输入组件
 * 支持多种类型、验证状态和自定义样式
 */

import React, { forwardRef } from 'react';
import clsx from 'clsx';

interface InputProps extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'size'> {
  /** 输入框标签 */
  label?: string;
  /** 输入框描述 */
  description?: string;
  /** 错误信息 */
  error?: string;
  /** 尺寸 */
  size?: 'small' | 'medium' | 'large';
  /** 变体样式 */
  variant?: 'default' | 'outline' | 'filled';
  /** 左侧图标 */
  leftIcon?: React.ReactNode;
  /** 右侧图标 */
  rightIcon?: React.ReactNode;
  /** 是否全宽度 */
  fullWidth?: boolean;
}

/**
 * 输入组件
 */
export const Input = forwardRef<HTMLInputElement, InputProps>(
  (
    {
      label,
      description,
      error,
      size = 'medium',
      variant = 'default',
      leftIcon,
      rightIcon,
      fullWidth = false,
      disabled,
      className,
      id,
      ...props
    },
    ref
  ) => {
    const inputId = id || `input-${Math.random().toString(36).substr(2, 9)}`;

    const sizeClasses = {
      small: 'px-3 py-2 text-sm',
      medium: 'px-4 py-3 text-base',
      large: 'px-5 py-4 text-lg',
    };

    const variantClasses = {
      default: 'border-neutral-300 bg-white focus:border-primary-green focus:ring-primary-green',
      outline: 'border-2 border-neutral-300 bg-transparent focus:border-primary-green focus:ring-primary-green',
      filled: 'border-transparent bg-neutral-100 focus:bg-white focus:border-primary-green focus:ring-primary-green',
    };

    const inputClasses = clsx(
      // 基础样式
      'block w-full rounded-lg border transition-colors duration-200',
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
        'pl-12': leftIcon && size === 'large',
        'pl-11': leftIcon && size === 'medium',
        'pl-10': leftIcon && size === 'small',
        'pr-12': rightIcon && size === 'large',
        'pr-11': rightIcon && size === 'medium',
        'pr-10': rightIcon && size === 'small',
      },
      
      // 宽度
      fullWidth ? 'w-full' : '',
      
      className
    );

    const iconSizeClasses = {
      small: 'w-4 h-4',
      medium: 'w-5 h-5',
      large: 'w-6 h-6',
    };

    const leftIconPositionClasses = {
      small: 'left-3',
      medium: 'left-3',
      large: 'left-4',
    };

    const rightIconPositionClasses = {
      small: 'right-3',
      medium: 'right-3',
      large: 'right-4',
    };

    return (
      <div className={clsx('relative', fullWidth ? 'w-full' : '')}>
        {/* 标签 */}
        {label && (
          <label
            htmlFor={inputId}
            className="block text-sm font-medium text-neutral-700 mb-2"
          >
            {label}
          </label>
        )}

        {/* 描述 */}
        {description && !error && (
          <p className="text-sm text-neutral-600 mb-2">{description}</p>
        )}

        {/* 输入框容器 */}
        <div className="relative">
          {/* 左侧图标 */}
          {leftIcon && (
            <div
              className={clsx(
                'absolute top-1/2 transform -translate-y-1/2 text-neutral-400',
                iconSizeClasses[size],
                leftIconPositionClasses[size]
              )}
            >
              {leftIcon}
            </div>
          )}

          {/* 输入框 */}
          <input
            ref={ref}
            id={inputId}
            disabled={disabled}
            className={inputClasses}
            {...props}
          />

          {/* 右侧图标 */}
          {rightIcon && (
            <div
              className={clsx(
                'absolute top-1/2 transform -translate-y-1/2 text-neutral-400',
                iconSizeClasses[size],
                rightIconPositionClasses[size]
              )}
            >
              {rightIcon}
            </div>
          )}
        </div>

        {/* 错误信息 */}
        {error && (
          <p className="mt-2 text-sm text-red-600">{error}</p>
        )}
      </div>
    );
  }
);

Input.displayName = 'Input'; 