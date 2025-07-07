/**
 * ESG-Copilot API服务层
 * 负责与后端API的通信，包括企业画像、对话、评估等功能
 */

import React from 'react';
import axios, { AxiosInstance, AxiosResponse, AxiosError } from 'axios';
import {
  ApiResponse,
  ProfileStartRequest,
  ProfileStartResponse,
  MessageRequest,
  MessageResponse,
  ProfileStatus,
  CompanyInfo,
  ESGAssessment,
} from '@/types';

/**
 * API客户端配置
 */
class ESGApiClient {
  private client: AxiosInstance;
  private baseURL: string;

  constructor() {
    // 在生产环境中使用相对路径，开发环境中使用完整URL
    this.baseURL = (import.meta as any).env?.VITE_API_URL || 
                   ((import.meta as any).env?.MODE === 'production' ? '' : 'http://localhost:8000');
    
    this.client = axios.create({
      baseURL: this.baseURL,
      timeout: 180000, // 180秒超时，用于AI API调用
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
    });

    // 请求拦截器
    this.client.interceptors.request.use(
      (config) => {
        // 添加认证token (如果有)
        const token = localStorage.getItem('auth_token');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        
        console.log(`[API] ${config.method?.toUpperCase()} ${config.url}`, {
          data: config.data,
          params: config.params,
        });
        
        return config;
      },
      (error) => {
        console.error('[API] Request error:', error);
        return Promise.reject(error);
      }
    );

    // 响应拦截器
    this.client.interceptors.response.use(
      (response: AxiosResponse) => {
        console.log(`[API] Response ${response.config.url}:`, response.data);
        return response;
      },
      (error: AxiosError) => {
        console.error('[API] Response error:', {
          url: error.config?.url,
          status: error.response?.status,
          data: error.response?.data,
        });
        
        // 统一错误处理
        return Promise.reject(this.handleError(error));
      }
    );
  }

  /**
   * 错误处理
   */
  private handleError(error: AxiosError): Error {
    if (!error.response) {
      return new Error('网络连接失败，请检查网络设置');
    }

    const { status, data } = error.response;
    
    switch (status) {
      case 400:
        return new Error((data as any)?.message || '请求参数错误');
      case 401:
        return new Error('未授权访问，请重新登录');
      case 403:
        return new Error('权限不足');
      case 404:
        return new Error('请求的资源不存在');
      case 500:
        return new Error('服务器内部错误，请稍后重试');
      case 503:
        return new Error('服务暂时不可用，请稍后重试');
      default:
        return new Error((data as any)?.message || `请求失败 (${status})`);
    }
  }

  /**
   * 通用请求方法
   */
  private async request<T>(
    method: 'GET' | 'POST' | 'PUT' | 'DELETE',
    url: string,
    data?: any,
    params?: any
  ): Promise<T> {
    try {
      console.log(`[API] ${method} ${url}`, data || params || '');
      
      const response = await this.client.request<ApiResponse<T>>({
        method,
        url,
        data,
        params,
      });

      console.log(`[API] Response ${url}:`, response.data);
      
      // 检查响应是否成功
      if (response.data && typeof response.data === 'object' && 'error' in response.data) {
        throw new Error(response.data.message || '请求失败');
      }

      return response.data as T;
    } catch (error) {
      console.error(`[API] Response error:`, error);
      throw this.handleError(error as AxiosError);
    }
  }

  // ========== 系统接口 ==========

  /**
   * 健康检查
   */
  async healthCheck(): Promise<{ status: string; version: string }> {
    return this.request('GET', '/health');
  }

  /**
   * 获取系统信息
   */
  async getSystemInfo(): Promise<any> {
    return this.request('GET', '/system/info');
  }

  // ========== Agent接口 ==========

  /**
   * 获取所有Agent状态
   */
  async getAgentsStatus(): Promise<any> {
    return this.request('GET', '/api/v1/agents/status');
  }

  /**
   * Agent健康检查
   */
  async getAgentsHealth(): Promise<any> {
    return this.request('GET', '/api/v1/agents/health');
  }

  // ========== 企业画像接口 ==========

  /**
   * 启动企业画像生成
   */
  async startProfileGeneration(request: ProfileStartRequest): Promise<ProfileStartResponse> {
    return this.request('POST', '/api/v1/agents/profile/start', request);
  }

  /**
   * 发送对话消息
   */
  async sendMessage(request: MessageRequest): Promise<MessageResponse> {
    return this.request('POST', '/api/v1/agents/profile/message', request);
  }

  /**
   * 获取企业画像状态
   */
  async getProfileStatus(conversationId: string): Promise<ProfileStatus> {
    return this.request('GET', `/api/v1/agents/profile/${conversationId}/status`);
  }

  /**
   * 重置企业画像对话
   */
  async resetProfile(conversationId: string): Promise<ApiResponse> {
    return this.request('POST', `/api/v1/agents/profile/${conversationId}/reset`);
  }

  // ========== 企业管理接口 ==========

  /**
   * 获取企业列表
   */
  async getCompanies(params?: {
    page?: number;
    limit?: number;
    search?: string;
  }): Promise<ApiResponse<any[]>> {
    return this.request('GET', '/companies', undefined, params);
  }

  /**
   * 获取企业详情
   */
  async getCompany(companyId: string): Promise<ApiResponse<CompanyInfo>> {
    return this.request('GET', `/companies/${companyId}`);
  }

  /**
   * 创建企业
   */
  async createCompany(company: Partial<CompanyInfo>): Promise<ApiResponse<CompanyInfo>> {
    return this.request('POST', '/companies', company);
  }

  /**
   * 更新企业信息
   */
  async updateCompany(companyId: string, company: Partial<CompanyInfo>): Promise<ApiResponse<CompanyInfo>> {
    return this.request('PUT', `/companies/${companyId}`, company);
  }

  // ========== ESG评估接口 ==========

  /**
   * 获取ESG评估
   */
  async getESGAssessment(companyId?: string): Promise<any> {
    if (companyId) {
      return this.request('GET', `/api/v1/companies/${companyId}/esg`);
    }
    return this.request('GET', '/api/v1/esg/assessment');
  }

  /**
   * 创建ESG评估
   */
  async createESGAssessment(companyId: string, data: any): Promise<ApiResponse<ESGAssessment>> {
    return this.request('POST', `/api/v1/companies/${companyId}/esg`, data);
  }

  // ========== Dashboard接口 ==========

  /**
   * 获取Dashboard概览数据
   */
  async getDashboardOverview(): Promise<any> {
    return this.request('GET', '/api/v1/dashboard/overview');
  }

  /**
   * 获取系统状态
   */
  async getSystemStatus(): Promise<any> {
    return this.request('GET', '/api/v1/dashboard/system-status');
  }

  /**
   * 获取最近活动
   */
  async getRecentActivities(): Promise<any> {
    return this.request('GET', '/api/v1/dashboard/recent-activities');
  }

  // ========== 报告接口 ==========

  /**
   * 获取报告列表
   */
  async getReports(params?: {
    page?: number;
    limit?: number;
    type?: string;
    status?: string;
  }): Promise<any> {
    return this.request('GET', '/api/v1/reports', undefined, params);
  }

  /**
   * 获取报告详情
   */
  async getReport(reportId: string): Promise<any> {
    return this.request('GET', `/api/v1/reports/${reportId}`);
  }

  /**
   * 生成报告
   */
  async generateReport(data: any): Promise<any> {
    return this.request('POST', '/api/v1/reports/generate', data);
  }

  /**
   * 获取报告状态
   */
  async getReportStatus(reportId: string): Promise<any> {
    return this.request('GET', `/api/v1/reports/${reportId}/status`);
  }

  /**
   * 删除报告
   */
  async deleteReport(reportId: string): Promise<any> {
    return this.request('DELETE', `/api/v1/reports/${reportId}`);
  }

  /**
   * 获取报告类型
   */
  async getReportTypes(): Promise<any> {
    return this.request('GET', '/api/v1/reports/types');
  }

  // ========== 文件上传接口 ==========

  /**
   * 上传文件
   */
  async uploadFile(file: File, options?: {
    onUploadProgress?: (progress: number) => void;
  }): Promise<ApiResponse<{ url: string; filename: string }>> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await this.client.post('/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        if (options?.onUploadProgress && progressEvent.total) {
          const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          options.onUploadProgress(progress);
        }
      },
    });

    return response.data;
  }

  // ========== WebSocket连接 ==========

  /**
   * 创建WebSocket连接
   */
  createWebSocket(userId: string): WebSocket {
    const wsUrl = this.baseURL.replace('http', 'ws') + `/ws/${userId}`;
    return new WebSocket(wsUrl);
  }
}

// 创建全局API客户端实例
export const apiClient = new ESGApiClient();

// ========== React Hook封装 ==========

/**
 * 企业画像生成Hook
 */
export const useProfileGeneration = () => {
  const [state, setState] = React.useState({
    conversation: null as ProfileStartResponse | null,
    loading: false,
    error: null as string | null,
  });

  const startProfile = async (companyInfo: CompanyInfo) => {
    setState(prev => ({ ...prev, loading: true, error: null }));
    
    try {
      const request: ProfileStartRequest = {
        user_id: 'current_user', // 临时用户ID
        company_name: companyInfo.name,
        initial_info: companyInfo,
      };
      
      const response = await apiClient.startProfileGeneration(request);
      setState(prev => ({ ...prev, conversation: response, loading: false }));
      
      return response;
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : '启动企业画像失败';
      setState(prev => ({ ...prev, error: errorMessage, loading: false }));
      throw error;
    }
  };

  const sendMessage = async (message: string, conversationId: string) => {
    setState(prev => ({ ...prev, loading: true, error: null }));
    
    try {
      const request: MessageRequest = {
        conversation_id: conversationId,
        user_id: 'current_user',
        response: message,
        context: {},
      };
      
      const response = await apiClient.sendMessage(request);
      setState(prev => ({ ...prev, loading: false }));
      
      return response;
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : '发送消息失败';
      setState(prev => ({ ...prev, error: errorMessage, loading: false }));
      throw error;
    }
  };

  return {
    ...state,
    startProfile,
    sendMessage,
  };
};

/**
 * 系统状态Hook
 */
export const useSystemStatus = () => {
  const [status, setStatus] = React.useState({
    healthy: false,
    loading: true,
    error: null as string | null,
  });

  React.useEffect(() => {
    const checkHealth = async () => {
      try {
        await apiClient.healthCheck();
        setStatus({ healthy: true, loading: false, error: null });
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : '系统健康检查失败';
        setStatus({ healthy: false, loading: false, error: errorMessage });
      }
    };

    checkHealth();
    
    // 每30秒检查一次
    const interval = setInterval(checkHealth, 30000);
    return () => clearInterval(interval);
  }, []);

  return status;
};

export default apiClient;