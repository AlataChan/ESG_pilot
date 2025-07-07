/**
 * Modal 模态框组件
 * 支持多种尺寸、动画效果和无障碍访问
 */

import React, { useEffect, useRef } from 'react';
import { createPortal } from 'react-dom';
import clsx from 'clsx';

interface ModalProps {
  /** 是否显示模态框 */
  isOpen: boolean;
  /** 关闭模态框的回调 */
  onClose: () => void;
  /** 模态框标题 */
  title?: string;
  /** 模态框内容 */
  children: React.ReactNode;
  /** 尺寸 */
  size?: 'small' | 'medium' | 'large' | 'full';
  /** 是否可以通过点击背景关闭 */
  closeOnBackdrop?: boolean;
  /** 是否可以通过ESC键关闭 */
  closeOnEscape?: boolean;
  /** 是否显示关闭按钮 */
  showCloseButton?: boolean;
  /** 自定义类名 */
  className?: string;
}

/**
 * 模态框组件
 */
export const Modal: React.FC<ModalProps> = ({
  isOpen,
  onClose,
  title,
  children,
  size = 'medium',
  closeOnBackdrop = true,
  closeOnEscape = true,
  showCloseButton = true,
  className,
}) => {
  const modalRef = useRef<HTMLDivElement>(null);
  const previousFocusRef = useRef<HTMLElement | null>(null);

  const sizeClasses = {
    small: 'max-w-md',
    medium: 'max-w-lg',
    large: 'max-w-2xl',
    full: 'max-w-full mx-4',
  };

  // 处理ESC键关闭
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && closeOnEscape) {
        onClose();
      }
    };

    if (isOpen) {
      document.addEventListener('keydown', handleEscape);
      // 保存当前焦点元素
      previousFocusRef.current = document.activeElement as HTMLElement;
      
      // 阻止背景滚动
      document.body.style.overflow = 'hidden';
      
      // 将焦点移到模态框
      setTimeout(() => {
        modalRef.current?.focus();
      }, 0);
    }

    return () => {
      document.removeEventListener('keydown', handleEscape);
      if (isOpen) {
        document.body.style.overflow = '';
        // 恢复之前的焦点
        previousFocusRef.current?.focus();
      }
    };
  }, [isOpen, closeOnEscape, onClose]);

  // 处理背景点击关闭
  const handleBackdropClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget && closeOnBackdrop) {
      onClose();
    }
  };

  if (!isOpen) return null;

  const modal = (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby={title ? 'modal-title' : undefined}
    >
      {/* 背景遮罩 */}
      <div
        className="fixed inset-0 bg-black bg-opacity-50 transition-opacity duration-300"
        onClick={handleBackdropClick}
        aria-hidden="true"
      />

      {/* 模态框内容 */}
      <div
        ref={modalRef}
        className={clsx(
          'relative bg-white rounded-lg shadow-xl transform transition-all duration-300',
          'w-full',
          sizeClasses[size],
          className
        )}
        tabIndex={-1}
      >
        {/* 标题栏 */}
        {(title || showCloseButton) && (
          <div className="flex items-center justify-between p-6 border-b border-neutral-200">
            {title && (
              <h2 id="modal-title" className="text-xl font-semibold text-neutral-900">
                {title}
              </h2>
            )}
            
            {showCloseButton && (
              <button
                onClick={onClose}
                className="p-2 text-neutral-400 hover:text-neutral-600 rounded-lg hover:bg-neutral-100 transition-colors"
                aria-label="关闭模态框"
              >
                <svg
                  className="w-5 h-5"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M6 18L18 6M6 6l12 12"
                  />
                </svg>
              </button>
            )}
          </div>
        )}

        {/* 模态框内容 */}
        <div className="p-6">
          {children}
        </div>
      </div>
    </div>
  );

  // 使用 Portal 渲染到 body
  return createPortal(modal, document.body);
};

Modal.displayName = 'Modal'; 