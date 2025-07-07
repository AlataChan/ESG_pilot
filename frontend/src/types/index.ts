/**
 * ESG-Copilot 前端类型定义
 * 包含API接口、组件属性、状态管理等相关类型
 */

// ========== 基础类型 ==========

/**
 * API响应基础类型
 */
export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  message?: string;
  error?: string;
}

/**
 * 分页数据类型
 */
export interface PaginationData<T = any> {
  items: T[];
  total: number;
  page: number;
  limit: number;
  hasNext: boolean;
  hasPrev: boolean;
}

// ========== 企业画像相关类型 ==========

/**
 * 企业基础信息
 */
export interface CompanyInfo {
  name: string;
  industry?: string;
  employeeCount?: number;
  location?: string;
  website?: string;
  description?: string;
  [key: string]: any;
}

/**
 * 企业画像启动请求
 */
export interface ProfileStartRequest {
  user_id: string;
  company_name: string;
  initial_info: CompanyInfo;
}

/**
 * 企业画像启动响应
 */
export interface ProfileStartResponse {
  type: 'question' | 'completion' | 'error';
  conversation_id: string;
  question?: string;
  progress?: string;
  stage?: string;
  next_action?: string;
  data?: any;
}

/**
 * 消息请求
 */
export interface MessageRequest {
  conversation_id: string;
  user_id: string;
  response: string;
  context?: Record<string, any>;
}

/**
 * 对话消息响应
 */
export interface MessageResponse {
  type: 'question' | 'completion' | 'error';
  conversation_id: string;
  question?: string;
  progress?: string;
  stage?: string;
  next_action?: string;
  data?: any;
}

/**
 * 企业画像状态
 */
export interface ProfileStatus {
  conversation_id: string;
  status: 'active' | 'completed' | 'error';
  progress: number;
  current_stage: string;
  total_stages: number;
  created_at: string;
  updated_at: string;
}

// ========== 聊天相关类型 ==========

/**
 * 消息类型
 */
export type MessageType = 'user' | 'ai';

/**
 * 消息状态
 */
export type MessageStatus = 'sending' | 'sent' | 'delivered' | 'read' | 'error';

/**
 * 聊天消息
 */
export interface ChatMessage {
  id: string;
  type: MessageType;
  content: string;
  timestamp: string;
  status: MessageStatus;
  avatar?: string;
  reactions?: string[];
  metadata?: Record<string, any>;
}

/**
 * 对话会话
 */
export interface Conversation {
  id: string;
  title: string;
  messages: ChatMessage[];
  status: 'active' | 'completed' | 'paused';
  progress: number;
  stage: string;
  createdAt: string;
  updatedAt: string;
}

// ========== ESG评估相关类型 ==========

/**
 * ESG评分
 */
export interface ESGScore {
  environment: number;
  social: number;
  governance: number;
  overall: number;
}

/**
 * ESG评估详情
 */
export interface ESGAssessment {
  id: string;
  companyId: string;
  scores: ESGScore;
  details: {
    environment: ESGCategoryDetail;
    social: ESGCategoryDetail;
    governance: ESGCategoryDetail;
  };
  recommendations: Recommendation[];
  trend: TrendData[];
  createdAt: string;
}

/**
 * ESG分类详情
 */
export interface ESGCategoryDetail {
  score: number;
  trend: number;
  items: {
    label: string;
    score: number;
    weight: number;
  }[];
}

/**
 * 改进建议
 */
export interface Recommendation {
  id: string;
  priority: 'high' | 'medium' | 'low';
  category: 'environment' | 'social' | 'governance';
  title: string;
  description: string;
  timeline: string;
  impact: 'high' | 'medium' | 'low';
  actionItems: string[];
}

/**
 * 趋势数据
 */
export interface TrendData {
  date: string;
  environment: number;
  social: number;
  governance: number;
  overall: number;
}

// ========== 文档相关类型 ==========

/**
 * 文档类型
 */
export interface Document {
  id: string;
  name: string;
  type: string;
  size: number;
  url?: string;
  uploadedAt: string;
  status: 'uploading' | 'processing' | 'completed' | 'error';
  metadata?: Record<string, any>;
}

// ========== 用户相关类型 ==========

/**
 * 用户信息
 */
export interface User {
  id: string;
  name: string;
  email: string;
  avatar?: string;
  role: 'admin' | 'user' | 'viewer';
  preferences: UserPreferences;
  createdAt: string;
}

/**
 * 用户偏好设置
 */
export interface UserPreferences {
  theme: 'light' | 'dark' | 'auto';
  language: 'zh-CN' | 'en-US';
  notifications: boolean;
  autoSave: boolean;
}

// ========== UI组件相关类型 ==========

/**
 * 按钮变体
 */
export type ButtonVariant = 'primary' | 'secondary' | 'outline' | 'ghost';

/**
 * 按钮尺寸类型
 */
export type ButtonSize = 'sm' | 'small' | 'medium' | 'large';

/**
 * 卡片变体
 */
export type CardVariant = 'default' | 'elevated' | 'outlined';

/**
 * 输入框状态
 */
export type InputStatus = 'default' | 'success' | 'warning' | 'error';

/**
 * 进度环属性
 */
export interface ProgressRingProps {
  progress: number;
  size?: 'small' | 'medium' | 'large';
  strokeWidth?: number;
  color?: string;
  animated?: boolean;
  children?: React.ReactNode;
}

/**
 * 消息气泡属性
 */
export interface MessageBubbleProps {
  message: ChatMessage;
  onReaction?: (messageId: string, reaction: string) => void;
}

// ========== 状态管理相关类型 ==========

/**
 * 应用状态
 */
export interface AppState {
  // 用户状态
  user: User | null;
  
  // 对话状态
  currentConversation: Conversation | null;
  conversations: Conversation[];
  
  // UI状态
  theme: 'light' | 'dark';
  sidebarOpen: boolean;
  loading: boolean;
  error: string | null;
  
  // 企业画像状态
  profileGeneration: {
    isActive: boolean;
    progress: number;
    stage: string;
    conversationId: string | null;
  };
}

/**
 * 应用动作接口
 */
export interface AppActions {
  // 用户动作
  setUser: (user: User | null) => void;
  updateUserPreferences: (preferences: Partial<UserPreferences>) => void;
  
  // 对话动作
  startConversation: (request: ProfileStartRequest) => Promise<void>;
  sendMessage: (message: string) => Promise<void>;
  loadConversations: () => Promise<void>;
  selectConversation: (conversationId: string) => void;
  deleteConversation: (conversationId: string) => Promise<void>;
  resetCurrentConversation: () => void;
  
  // UI动作
  setTheme: (theme: 'light' | 'dark') => void;
  toggleSidebar: () => void;
  setSidebarOpen: (open: boolean) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  clearError: () => void;
}

// ========== 工具类型 ==========

/**
 * 异步状态
 */
export interface AsyncState<T = any> {
  data: T | null;
  loading: boolean;
  error: string | null;
}

/**
 * 事件处理器类型
 */
export type EventHandler<T = any> = (event: T) => void;

/**
 * 可选的回调函数
 */
export type OptionalCallback<T = void> = T extends void ? () => void : (data: T) => void;