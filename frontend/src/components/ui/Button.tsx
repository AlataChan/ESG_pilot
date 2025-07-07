/**
 * Button 组件
 * 支持多种变体、尺寸和状态的按钮组件
 */

import React from 'react';
import { clsx } from 'clsx';
import { ButtonVariant, ButtonSize } from '@/types';

/**
 * Button组件属性
 */
export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  /** 按钮变体 */
  variant?: ButtonVariant;
  /** 按钮尺寸 */
  size?: ButtonSize;
  /** 是否为加载状态 */
  loading?: boolean;
  /** 是否占满宽度 */
  fullWidth?: boolean;
  /** 左侧图标 */
  leftIcon?: React.ReactNode;
  /** 右侧图标 */
  rightIcon?: React.ReactNode;
  /** 子元素 */
  children?: React.ReactNode;
}

/**
 * 按钮样式映射
 */
const buttonStyles = {
  variant: {
    primary: 'btn-primary',
    secondary: 'btn-secondary',
    outline: 'btn-outline',
    ghost: 'btn-ghost',
  },
  size: {
    sm: 'px-2 py-1 text-xs',
    small: 'px-3 py-1.5 text-sm',
    medium: 'px-4 py-2 text-base',
    large: 'px-6 py-3 text-lg',
  },
};

/**
 * 加载指示器组件
 */
const LoadingSpinner: React.FC<{ size: ButtonSize }> = ({ size }) => {
  const sizeClass = {
    sm: 'w-3 h-3',
    small: 'w-4 h-4',
    medium: 'w-5 h-5',
    large: 'w-6 h-6',
  }[size];

  return (
    <svg
      className={clsx('animate-spin', sizeClass)}
      xmlns="http://www.w3.org/2000/svg"
      fill="none"
      viewBox="0 0 24 24"
    >
      <circle
        className="opacity-25"
        cx="12"
        cy="12"
        r="10"
        stroke="currentColor"
        strokeWidth="4"
      />
      <path
        className="opacity-75"
        fill="currentColor"
        d="m4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
      />
    </svg>
  );
};

/**
 * Button组件
 */
export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      variant = 'primary',
      size = 'medium',
      loading = false,
      fullWidth = false,
      leftIcon,
      rightIcon,
      children,
      className,
      disabled,
      ...props
    },
    ref
  ) => {
    const isDisabled = disabled || loading;

    return (
      <button
        ref={ref}
        className={clsx(
          // 基础样式
          'btn',
          // 变体样式
          buttonStyles.variant[variant],
          // 尺寸样式
          buttonStyles.size[size],
          // 全宽样式
          fullWidth && 'w-full',
          // 禁用状态
          isDisabled && 'opacity-50 cursor-not-allowed',
          // 自定义类名
          className
        )}
        disabled={isDisabled}
        {...props}
      >
        {/* 左侧图标或加载指示器 */}
        {loading ? (
          <LoadingSpinner size={size} />
        ) : leftIcon ? (
          <span className="mr-2">{leftIcon}</span>
        ) : null}

        {/* 按钮文本 */}
        {children && <span>{children}</span>}

        {/* 右侧图标 */}
        {rightIcon && !loading && <span className="ml-2">{rightIcon}</span>}
      </button>
    );
  }
);

Button.displayName = 'Button';

export default Button;