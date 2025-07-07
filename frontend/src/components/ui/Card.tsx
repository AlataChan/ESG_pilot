/**
 * Card 组件
 * 卡片容器组件，支持多种变体和样式
 */

import React from 'react';
import { clsx } from 'clsx';
import { CardVariant } from '@/types';

/**
 * Card组件属性
 */
export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: CardVariant;
  hoverable?: boolean;
  padding?: boolean;
  children?: React.ReactNode;
}

/**
 * Card主组件
 */
export const Card = React.forwardRef<HTMLDivElement, CardProps>(
  (
    {
      variant = 'default',
      hoverable = false,
      padding = true,
      children,
      className,
      ...props
    },
    ref
  ) => {
    const variantStyles = {
      default: 'card',
      elevated: 'card card-elevated',
      outlined: 'card border-2',
    };

    return (
      <div
        ref={ref}
        className={clsx(
          variantStyles[variant],
          hoverable && 'card-hover cursor-pointer',
          padding && 'p-6',
          className
        )}
        {...props}
      >
        {children}
      </div>
    );
  }
);

Card.displayName = 'Card';

export default Card; 