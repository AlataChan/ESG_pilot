/**
 * 知识库管理页面
 * 提供文档上传、管理和分类功能
 */

import React, { useState, useEffect } from 'react';
import { Button } from '../components/ui/Button';

interface Category {
  id: string;
  name: string;
  description?: string;
  color: string;
  user_id: string;
  created_at: string;
  updated_at: string;
}

interface Document {
  id: string;
  user_id: string;
  filename: string;
  original_filename: string;
  file_path: string;
  file_type: string;
  file_size: number;
  category_id?: string;
  status: 'uploading' | 'processing' | 'completed' | 'failed' | 'deleted';
  vector_indexed: boolean;
  chunk_count: number;
  processing_error?: string;
  created_at: string;
  updated_at: string;
  category?: Category;
}

const KnowledgeManagementPage: React.FC = () => {
  const [categories, setCategories] = useState<Category[]>([]);
  const [documents, setDocuments] = useState<Document[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<string>('');
  const [uploading, setUploading] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // 获取分类列表
  const fetchCategories = async () => {
    try {
      const apiUrl = (import.meta as any).env?.VITE_API_URL || 'http://localhost:8000';
      const response = await fetch(`${apiUrl}/api/v1/knowledge/categories`);
      if (!response.ok) {
        throw new Error('获取分类列表失败');
      }
      const data = await response.json();
      setCategories(data);
    } catch (err) {
      console.error('获取分类失败:', err);
      setError('获取分类列表失败');
    }
  };

  // 获取文档列表
  const fetchDocuments = async () => {
    try {
      const apiUrl = (import.meta as any).env?.VITE_API_URL || 'http://localhost:8000';
      const response = await fetch(`${apiUrl}/api/v1/knowledge/documents`);
      if (!response.ok) {
        throw new Error('获取文档列表失败');
      }
      const data = await response.json();
      setDocuments(data);
    } catch (err) {
      console.error('获取文档失败:', err);
      setError('获取文档列表失败');
    }
  };

  // 页面加载时获取数据
  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      await Promise.all([
        fetchCategories(),
        fetchDocuments()
      ]);
      setLoading(false);
    };
    
    loadData();
  }, []);

  // 文件上传处理
  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    // 检查文件类型
    const allowedTypes = ['pdf', 'doc', 'docx', 'xls', 'xlsx', 'txt', 'md', 'json'];
    const fileExtension = file.name.split('.').pop()?.toLowerCase();
    
    if (!fileExtension || !allowedTypes.includes(fileExtension)) {
      alert(`不支持的文件类型。支持的类型: ${allowedTypes.join(', ')}`);
      return;
    }

    // 检查文件大小 (50MB)
    if (file.size > 50 * 1024 * 1024) {
      alert('文件大小不能超过 50MB');
      return;
    }

    setUploading(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append('file', file);
      if (selectedCategory) {
        formData.append('category_id', selectedCategory);
      }

      const apiUrl = (import.meta as any).env?.VITE_API_URL || 'http://localhost:8000';
      const response = await fetch(`${apiUrl}/api/v1/knowledge/documents/upload`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || '上传失败');
      }

      const result = await response.json();
      alert(`文档上传成功: ${result.message}`);
      
      // 刷新文档列表
      await fetchDocuments();
      
    } catch (err) {
      console.error('上传失败:', err);
      setError(err instanceof Error ? err.message : '上传失败');
    } finally {
      setUploading(false);
      // 清空文件输入
      event.target.value = '';
    }
  };

  // 删除文档
  const handleDeleteDocument = async (documentId: string) => {
    if (!confirm('确定要删除这个文档吗？此操作不可撤销。')) {
      return;
    }

    try {
      const apiUrl = (import.meta as any).env?.VITE_API_URL || 'http://localhost:8000';
      const response = await fetch(`${apiUrl}/api/v1/knowledge/documents/${documentId}`, {
        method: 'DELETE',
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || '删除失败');
      }

      alert('文档删除成功');
      await fetchDocuments();
      
    } catch (err) {
      console.error('删除失败:', err);
      alert(err instanceof Error ? err.message : '删除失败');
    }
  };

  // 格式化文件大小
  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  // 获取状态显示文本和颜色
  const getStatusDisplay = (status: string) => {
    const statusMap = {
      uploading: { text: '上传中', color: 'text-blue-600' },
      processing: { text: '处理中', color: 'text-yellow-600' },
      completed: { text: '已完成', color: 'text-green-600' },
      failed: { text: '失败', color: 'text-red-600' },
      deleted: { text: '已删除', color: 'text-gray-600' }
    };
    return statusMap[status as keyof typeof statusMap] || { text: status, color: 'text-gray-600' };
  };

  if (loading) {
    return (
      <div className="page-container optimized-1440-900">
        <div className="layout-1440 content-wrapper">
          <div className="flex items-center justify-center h-64">
            <div className="animate-spin w-8 h-8 border-4 border-primary-green border-t-transparent rounded-full"></div>
            <span className="ml-3 text-lg">加载中...</span>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="page-container optimized-1440-900">
      <div className="layout-1440 content-wrapper">
        <div className="max-w-6xl mx-auto">
          {/* 页面标题 */}
          <div className="mb-6 2xl:mb-8">
            <h1 className="text-2xl 2xl:text-3xl font-bold mb-2">
              <span className="gradient-text">知识库管理</span>
            </h1>
            <p className="text-neutral-600">
              上传和管理您的ESG相关文档，构建专属知识库
            </p>
          </div>

          {/* 错误提示 */}
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
              <div className="flex">
                <span className="text-red-600 mr-2">⚠️</span>
                <span className="text-red-700">{error}</span>
              </div>
            </div>
          )}

          {/* 文件上传区域 */}
          <div className="bg-white rounded-3xl shadow-strong p-5 2xl:p-6 mb-6 2xl:mb-8">
            <h2 className="text-lg 2xl:text-xl font-semibold mb-4">文档上传</h2>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
              {/* 分类选择 */}
              <div>
                <label className="block text-sm font-medium text-neutral-700 mb-2">
                  选择分类（可选）
                </label>
                <select
                  value={selectedCategory}
                  onChange={(e) => setSelectedCategory(e.target.value)}
                  className="input"
                >
                  <option value="">默认分类</option>
                  {categories.map((category) => (
                    <option key={category.id} value={category.id}>
                      {category.name}
                    </option>
                  ))}
                </select>
              </div>

              {/* 文件选择 */}
              <div>
                <label className="block text-sm font-medium text-neutral-700 mb-2">
                  选择文件
                </label>
                <input
                  type="file"
                  onChange={handleFileUpload}
                  disabled={uploading}
                  accept=".pdf,.doc,.docx,.xls,.xlsx,.txt,.md,.json"
                  className="block w-full text-sm text-neutral-500
                           file:mr-4 file:py-2 file:px-4
                           file:rounded-lg file:border-0
                           file:text-sm file:font-medium
                           file:bg-primary-green file:text-white
                           hover:file:bg-primary-green-dark
                           disabled:file:bg-neutral-300"
                />
              </div>
            </div>

            <div className="text-sm text-neutral-500">
              <p>• 支持格式：PDF, Word, Excel, 文本文件</p>
              <p>• 最大文件大小：50MB</p>
              <p>• 上传后文档将自动进行向量化处理</p>
            </div>

            {uploading && (
              <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
                <div className="flex items-center">
                  <div className="animate-spin w-5 h-5 border-2 border-blue-600 border-t-transparent rounded-full mr-3"></div>
                  <span className="text-blue-700">文档上传中，请稍候...</span>
                </div>
              </div>
            )}
          </div>

          {/* 文档列表 */}
          <div className="bg-white rounded-3xl shadow-strong p-5 2xl:p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg 2xl:text-xl font-semibold">文档列表</h2>
              <span className="text-sm text-neutral-500">
                共 {documents.length} 个文档
              </span>
            </div>

            {documents.length === 0 ? (
              <div className="text-center py-8">
                <div className="text-6xl mb-4">📄</div>
                <p className="text-neutral-500">暂无文档，请上传第一个文档</p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-neutral-200">
                      <th className="text-left py-3 px-2 font-medium text-neutral-700">文件名</th>
                      <th className="text-left py-3 px-2 font-medium text-neutral-700">分类</th>
                      <th className="text-left py-3 px-2 font-medium text-neutral-700">大小</th>
                      <th className="text-left py-3 px-2 font-medium text-neutral-700">状态</th>
                      <th className="text-left py-3 px-2 font-medium text-neutral-700">上传时间</th>
                      <th className="text-left py-3 px-2 font-medium text-neutral-700">操作</th>
                    </tr>
                  </thead>
                  <tbody>
                    {documents.map((doc) => {
                      const statusDisplay = getStatusDisplay(doc.status);
                      return (
                        <tr key={doc.id} className="border-b border-neutral-100 hover:bg-neutral-50">
                          <td className="py-3 px-2">
                            <div className="flex items-center">
                              <span className="text-lg mr-2">📄</span>
                              <div>
                                <div className="font-medium text-neutral-900">{doc.original_filename}</div>
                                <div className="text-sm text-neutral-500">{doc.file_type.toUpperCase()}</div>
                              </div>
                            </div>
                          </td>
                          <td className="py-3 px-2">
                            <span className="inline-block px-2 py-1 bg-neutral-100 text-neutral-700 text-xs rounded">
                              {doc.category?.name || '默认'}
                            </span>
                          </td>
                          <td className="py-3 px-2 text-neutral-600">
                            {formatFileSize(doc.file_size)}
                          </td>
                          <td className="py-3 px-2">
                            <span className={`font-medium ${statusDisplay.color}`}>
                              {statusDisplay.text}
                            </span>
                            {doc.vector_indexed && (
                              <span className="ml-2 text-xs text-green-600">✓ 已索引</span>
                            )}
                          </td>
                          <td className="py-3 px-2 text-neutral-600">
                            {new Date(doc.created_at).toLocaleDateString()}
                          </td>
                          <td className="py-3 px-2">
                            <Button
                              onClick={() => handleDeleteDocument(doc.id)}
                              className="text-red-600 hover:text-red-800 text-sm"
                              variant="ghost"
                              size="sm"
                            >
                              删除
                            </Button>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default KnowledgeManagementPage;