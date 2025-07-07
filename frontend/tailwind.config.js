/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    // 重新定义屏幕断点以适配1440*900分辨率
    screens: {
      'sm': '640px',
      'md': '768px',
      'lg': '1024px',
      'xl': '1280px',
      '2xl': '1440px', // 主要目标分辨率
      '3xl': '1600px',
    },
    extend: {
      // "Brighter Future"主题色彩系统
      colors: {
        // 绿色系 - 可持续发展
        primary: {
          green: '#00D084',
          'green-dark': '#00B574',
          'green-light': '#E8F8F3',
          'green-accent': '#00F295',
        },
        // 黄色系 - 希望与活力
        secondary: {
          yellow: '#FFD60A',
          'yellow-dark': '#FFC300',
          'yellow-light': '#FFF8E1',
          'yellow-accent': '#FFED4E',
        },
        // 中性色 - 苹果风格
        neutral: {
          50: '#F9FAFB',
          100: '#F3F4F6',
          200: '#E5E7EB',
          600: '#4B5563',
          900: '#111827',
        },
      },
      // 渐变色
      backgroundImage: {
        'gradient-primary': 'linear-gradient(135deg, #00D084 0%, #FFD60A 100%)',
        'gradient-card': 'linear-gradient(145deg, #FFFFFF 0%, #F9FAFB 100%)',
        'gradient-hero': 'linear-gradient(135deg, #E8F8F3 0%, #FFF8E1 50%, #F0F9FF 100%)',
      },
      // 字体系统 - 针对1440*900优化
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      fontSize: {
        'xs': ['0.75rem', { lineHeight: '1rem' }],
        'sm': ['0.875rem', { lineHeight: '1.25rem' }],
        'base': ['1rem', { lineHeight: '1.5rem' }],
        'lg': ['1.125rem', { lineHeight: '1.75rem' }],
        'xl': ['1.25rem', { lineHeight: '1.75rem' }],
        '2xl': ['1.5rem', { lineHeight: '2rem' }],
        '3xl': ['1.875rem', { lineHeight: '2.25rem' }],
        '4xl': ['2.25rem', { lineHeight: '2.5rem' }],
        '5xl': ['3rem', { lineHeight: '3.5rem' }],
        '6xl': ['3.75rem', { lineHeight: '4rem' }],
      },
      // 间距系统 - 为1440*900优化
      spacing: {
        '18': '4.5rem',
        '88': '22rem',
        '128': '32rem',
        '144': '36rem',
      },
      // 容器最大宽度 - 适配1440*900
      maxWidth: {
        '8xl': '88rem',   // 1408px - 为1440px屏幕优化
        '9xl': '96rem',   // 1536px
        'screen-2xl': '1440px', // 精确匹配目标分辨率
      },
      // 高度设置 - 适配900px高度
      height: {
        'screen-90': '90vh',
        'screen-95': '95vh',
        '900': '900px',
      },
      minHeight: {
        'screen-90': '90vh',
        'screen-95': '95vh',
        '900': '900px',
      },
      // 阴影系统
      boxShadow: {
        'soft': '0 2px 8px 0 rgba(0, 0, 0, 0.08)',
        'medium': '0 4px 16px 0 rgba(0, 0, 0, 0.12)',
        'strong': '0 8px 32px 0 rgba(0, 0, 0, 0.16)',
        'card': '0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)',
        'card-hover': '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
      },
      // 边框圆角
      borderRadius: {
        'xl': '0.75rem',
        '2xl': '1rem',
        '3xl': '1.5rem',
      },
      // 动画
      animation: {
        'fade-in': 'fadeIn 0.5s ease-out',
        'slide-up': 'slideUp 0.5s ease-out',
        'pulse-soft': 'pulseSoft 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0', transform: 'translateY(20px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        slideUp: {
          '0%': { opacity: '0', transform: 'translateY(50px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        pulseSoft: {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0.8' },
        },
      },
    },
  },
  plugins: [],
} 