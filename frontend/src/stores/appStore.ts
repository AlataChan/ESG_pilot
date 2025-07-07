/**
 * ESG-Copilot 应用状态管理
 * 使用Zustand管理全局状态，包括用户、对话、UI状态等
 */

import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';
import { immer } from 'zustand/middleware/immer';
// import type { StateCreator } from 'zustand';
import {
  AppState,
  AppActions,
  User,
  Conversation,
  ChatMessage,
  ProfileStartRequest,
  ProfileStartResponse,
  MessageResponse,
  UserPreferences,
} from '../types';
import { apiClient } from '../services/api';

/**
 * 应用状态和动作的组合接口
 */
interface AppStore extends AppState, AppActions {}

/**
 * 状态创建器类型
 */
// type AppStateCreator = StateCreator<
//   AppStore,
//   [['zustand/devtools', never], ['zustand/persist', unknown], ['zustand/immer', never]],
//   [],
//   AppStore
// >;

/**
 * 创建应用状态管理器
 */
export const useAppStore = create<AppStore>()(
  devtools(
    persist(
      immer<AppStore>((set, get) => ({
        // ========== 初始状态 ==========
        
        // 用户状态
        user: null,
        
        // 对话状态
        currentConversation: null,
        conversations: [],
        
        // UI状态
        theme: 'light',
        sidebarOpen: false,
        loading: false,
        error: null,
        
        // 企业画像状态
        profileGeneration: {
          isActive: false,
          progress: 0,
          stage: '',
          conversationId: null,
        },

        // ========== 用户动作 ==========
        
        setUser: (user: User | null) => {
          set((state) => {
            state.user = user;
          });
        },

        updateUserPreferences: (preferences: Partial<UserPreferences>) => {
          set((state) => {
            if (state.user) {
              state.user.preferences = {
                ...state.user.preferences,
                ...preferences,
              };
            }
          });
        },

        // ========== 对话动作 ==========
        
        startConversation: async (request: ProfileStartRequest) => {
          set((state) => {
            state.loading = true;
            state.error = null;
          });

          try {
            const response: ProfileStartResponse = await apiClient.startProfileGeneration(request);
            
            // 创建新的对话
            const newConversation: Conversation = {
              id: response.conversation_id,
              title: `${request.company_name} 企业画像`,
              messages: [
                {
                  id: `msg_${Date.now()}`,
                  type: 'ai',
                  content: response.question || '您好！我是ESG智能助手，让我们开始企业画像生成吧！',
                  timestamp: new Date().toISOString(),
                  status: 'delivered',
                  avatar: '🤖',
                },
              ],
              status: 'active',
              progress: parseInt(response.progress?.split('/')[0] || '0'),
              stage: response.stage || '初始化',
              createdAt: new Date().toISOString(),
              updatedAt: new Date().toISOString(),
            };

            set((state) => {
              state.currentConversation = newConversation;
              state.conversations.unshift(newConversation);
              state.profileGeneration = {
                isActive: true,
                progress: newConversation.progress,
                stage: newConversation.stage,
                conversationId: response.conversation_id,
              };
              state.loading = false;
            });

          } catch (error) {
            const errorMessage = error instanceof Error ? error.message : '启动对话失败';
            set((state) => {
              state.error = errorMessage;
              state.loading = false;
            });
            throw error;
          }
        },

        sendMessage: async (message: string) => {
          const { currentConversation, loading } = get();
          
          if (!currentConversation) {
            throw new Error('没有活跃的对话');
          }

          // 防重复提交
          if (loading) {
            console.log('🔄 正在发送消息，忽略重复请求');
            return;
          }

          // 添加用户消息
          const userMessage: ChatMessage = {
            id: `msg_${Date.now()}_user`,
            type: 'user',
            content: message,
            timestamp: new Date().toISOString(),
            status: 'sending',
          };

          set((state) => {
            if (state.currentConversation) {
              state.currentConversation.messages.push(userMessage);
            }
            state.loading = true;
            state.error = null;
          });

          try {
            const response: MessageResponse = await apiClient.sendMessage({
              conversation_id: currentConversation.id,
              user_id: 'current_user',
              response: message,
              context: {},
            });

            // 更新用户消息状态
            set((state) => {
              if (state.currentConversation) {
                const lastMessage = state.currentConversation.messages[state.currentConversation.messages.length - 1];
                if (lastMessage && lastMessage.id === userMessage.id) {
                  lastMessage.status = 'delivered';
                }
              }
            });

            // 添加AI回复
            if (response.type === 'question' && response.question) {
              const aiMessage: ChatMessage = {
                id: `msg_${Date.now()}_ai`,
                type: 'ai',
                content: response.question,
                timestamp: new Date().toISOString(),
                status: 'delivered',
                avatar: '🤖',
              };

              set((state) => {
                if (state.currentConversation) {
                  // 检查是否是重复消息
                  const lastAiMessage = state.currentConversation.messages
                    .filter(m => m.type === 'ai')
                    .pop();
                  
                  const isDuplicate = lastAiMessage && lastAiMessage.content === response.question;
                  
                  if (isDuplicate) {
                    console.warn('🔄 检测到重复的AI回复:', response.question);
                    // 添加调试信息到消息中
                    aiMessage.content = `⚠️ **检测到重复问题**\n\n${response.question}\n\n📋 **可能的原因：**\n• 后端Agent状态管理异常\n• 对话上下文丢失\n\n🛠️ **建议操作：**\n• 点击"🔄 重新开始"按钮\n• 或点击"🔍 调试信息"查看详情`;
                  }
                  
                  state.currentConversation.messages.push(aiMessage);
                  state.currentConversation.progress = parseInt(response.progress?.split('/')[0] || '0');
                  state.currentConversation.stage = response.stage || '';
                  state.currentConversation.updatedAt = new Date().toISOString();
                  
                  // 更新企业画像进度
                  state.profileGeneration.progress = state.currentConversation.progress;
                  state.profileGeneration.stage = state.currentConversation.stage;
                }
                state.loading = false;
              });
            } else if (response.type === 'completion') {
              // 对话完成
              set((state) => {
                if (state.currentConversation) {
                  state.currentConversation.status = 'completed';
                  state.currentConversation.updatedAt = new Date().toISOString();
                }
                state.profileGeneration.isActive = false;
                state.loading = false;
              });
            }

          } catch (error) {
            // 更新用户消息为错误状态
            set((state) => {
              if (state.currentConversation) {
                const lastMessage = state.currentConversation.messages[state.currentConversation.messages.length - 1];
                if (lastMessage && lastMessage.id === userMessage.id) {
                  lastMessage.status = 'error';
                }
              }
              state.error = error instanceof Error ? error.message : '发送消息失败';
              state.loading = false;
            });
            throw error;
          }
        },

        loadConversations: async () => {
          set((state) => {
            state.loading = true;
            state.error = null;
          });

          try {
            // TODO: 实现从API加载对话历史
            // const conversations = await apiClient.getConversations();
            
            set((state) => {
              // state.conversations = conversations;
              state.loading = false;
            });

          } catch (error) {
            set((state) => {
              state.error = error instanceof Error ? error.message : '加载对话失败';
              state.loading = false;
            });
          }
        },

        selectConversation: (conversationId: string) => {
          const { conversations } = get();
          const conversation = conversations.find(c => c.id === conversationId);
          
          set((state) => {
            state.currentConversation = conversation || null;
          });
        },

        deleteConversation: async (conversationId: string) => {
          try {
            // TODO: 实现API删除
            // await apiClient.deleteConversation(conversationId);
            
            set((state) => {
              state.conversations = state.conversations.filter(c => c.id !== conversationId);
              if (state.currentConversation?.id === conversationId) {
                state.currentConversation = null;
              }
            });

          } catch (error) {
            set((state) => {
              state.error = error instanceof Error ? error.message : '删除对话失败';
            });
            throw error;
          }
        },

        // ========== UI动作 ==========
        
        setTheme: (theme: 'light' | 'dark') => {
          set((state) => {
            state.theme = theme;
          });
        },

        toggleSidebar: () => {
          set((state) => {
            state.sidebarOpen = !state.sidebarOpen;
          });
        },

        setSidebarOpen: (open: boolean) => {
          set((state) => {
            state.sidebarOpen = open;
          });
        },

        setLoading: (loading: boolean) => {
          set((state) => {
            state.loading = loading;
          });
        },

        setError: (error: string | null) => {
          set((state) => {
            state.error = error;
          });
        },

        clearError: () => {
          set((state) => {
            state.error = null;
          });
        },

        // 重置当前对话
        resetCurrentConversation: () => {
          set((state) => {
            if (state.currentConversation) {
              // 保留基本信息，清空消息历史
              state.currentConversation.messages = [];
              state.currentConversation.progress = 0;
              state.currentConversation.stage = '准备重新开始';
              state.currentConversation.status = 'active';
              state.currentConversation.updatedAt = new Date().toISOString();
            }
            state.loading = false;
            state.error = null;
          });
        },
      })),
      {
        name: 'esg-copilot-store',
        partialize: (state) => ({
          user: state.user,
          conversations: state.conversations,
          theme: state.theme,
        }),
      }
    ),
    {
      name: 'esg-copilot',
    }
  )
);

// ========== 选择器钩子 ==========

/**
 * 获取当前用户
 */
export const useCurrentUser = () => useAppStore((state) => state.user);

/**
 * 获取当前对话
 */
export const useCurrentConversation = () => useAppStore((state) => state.currentConversation);

/**
 * 获取加载状态
 */
export const useLoading = () => useAppStore((state) => state.loading);

/**
 * 获取错误状态
 */
export const useError = () => useAppStore((state) => state.error);

/**
 * 获取企业画像生成状态
 */
export const useProfileGeneration = () => useAppStore((state) => state.profileGeneration);

/**
 * 获取主题
 */
export const useTheme = () => useAppStore((state) => state.theme);

/**
 * 获取侧边栏状态
 */
export const useSidebar = () => useAppStore((state) => state.sidebarOpen);

/**
 * 对话相关动作
 */
export const useConversationActions = () => useAppStore((state) => ({
  startConversation: state.startConversation,
  sendMessage: state.sendMessage,
  loadConversations: state.loadConversations,
  selectConversation: state.selectConversation,
  deleteConversation: state.deleteConversation,
  resetCurrentConversation: state.resetCurrentConversation,
}));

/**
 * UI相关动作
 */
export const useUIActions = () => useAppStore((state) => ({
  setTheme: state.setTheme,
  toggleSidebar: state.toggleSidebar,
  setSidebarOpen: state.setSidebarOpen,
  setLoading: state.setLoading,
  setError: state.setError,
  clearError: state.clearError,
}));

/**
 * 用户相关动作
 */
export const useUserActions = () => useAppStore((state) => ({
  setUser: state.setUser,
  updateUserPreferences: state.updateUserPreferences,
}));

export default useAppStore; 