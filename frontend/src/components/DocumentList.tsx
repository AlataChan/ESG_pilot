import React, { useState } from 'react';
import { Button } from './ui/Button';

/**
 * 文档状态颜色映射
 */
const statusColors = {
  'uploading': 'bg-blue-100 text-blue-800',
  'processing': 'bg-orange-100 text-orange-800',
  'completed': 'bg-green-100 text-green-800',
  'failed': 'bg-red-100 text-red-800',
  'deleted': 'bg-gray-100 text-gray-800'
};

/**
 * 文档状态中文名称映射
 */
const statusNames = {
  'uploading': '上传中',
  'processing': '处理中',
  'completed': '已完成',
  'failed': '处理失败',
  'deleted': '已删除'
};

/**
 * 文档类型图标映射
 */
const typeIcons = {
  'pdf': '📄',
  'docx': '📝',
  'doc': '📝',
  'xlsx': '📊',
  'xls': '📊',
  'pptx': '📈',
  'ppt': '📈',
  'txt': '📃',
  'md': '📋',
  'csv': '📑',
  'json': '🔧',
  'xml': '🔧',
  'html': '🌐',
  'png': '🖼️',
  'jpg': '🖼️',
  'jpeg': '🖼️',
  'gif': '🖼️'
} as const;

interface Document {
  id: string;
  filename: string;
  original_filename: string;
  file_type: string;
  file_size: number;
  status: keyof typeof statusNames;
  category?: {
    id: string;
    name: string;
    color: string;
  };
  created_at: string;
  updated_at: string;
  chunk_count?: number;
  processing_error?: string;
}

interface Category {
  id: string;
  name: string;
  color: string;
}

interface DocumentListProps {
  documents: Document[];
  categories: Category[];
  loading?: boolean;
  onDelete: (id: string) => void;
  onRefresh: () => void;
  onSearch?: (query: string, filters?: any) => void;
}

const DocumentList: React.FC<DocumentListProps> = ({
  documents,
  categories,
  loading = false,
  onDelete,
  onRefresh,
  onSearch
}) => {

  const [searchQuery, setSearchQuery] = useState('');
  const [filterCategory, setFilterCategory] = useState<string>('');
  const [filterStatus, setFilterStatus] = useState<string>('');
  const [filterFileType, setFilterFileType] = useState<string>('');

  // 格式化文件大小
  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  // 格式化日期
  const formatDate = (dateString: string): string => {
    return new Date(dateString).toLocaleDateString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  // 处理搜索和过滤
  const handleSearch = () => {
    if (onSearch) {
      const filters = {
        category_id: filterCategory || undefined,
        status: filterStatus || undefined,
        file_type: filterFileType || undefined
      };
      onSearch(searchQuery, filters);
    }
  };

  // 重置过滤条件
  const handleResetFilters = () => {
    setSearchQuery('');
    setFilterCategory('');
    setFilterStatus('');
    setFilterFileType('');
    if (onSearch) {
      onSearch('', {});
    }
  };

  // 获取文档类型图标
  const getTypeIcon = (fileType: string): string => {
    return typeIcons[fileType as keyof typeof typeIcons] || '📄';
  };

  // 获取状态样式
  const getStatusStyle = (status: string): string => {
    return statusColors[status as keyof typeof statusColors] || 'bg-gray-100 text-gray-800';
  };

  // 获取状态名称
  const getStatusName = (status: string): string => {
    return statusNames[status as keyof typeof statusNames] || status;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-green"></div>
        <span className="ml-2 text-gray-600">加载中...</span>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* 搜索和过滤区域 */}
      <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">搜索文档</label>
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="输入文档名称..."
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-green focus:border-transparent"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">分类</label>
            <select
              value={filterCategory}
              onChange={(e) => setFilterCategory(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-green focus:border-transparent"
            >
              <option value="">全部分类</option>
              {categories.map((category) => (
                <option key={category.id} value={category.id}>
                  {category.name}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">状态</label>
            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-green focus:border-transparent"
            >
              <option value="">全部状态</option>
              {Object.entries(statusNames).map(([key, value]) => (
                <option key={key} value={key}>
                  {value}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">文件类型</label>
            <select
              value={filterFileType}
              onChange={(e) => setFilterFileType(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-green focus:border-transparent"
            >
              <option value="">全部类型</option>
              <option value="pdf">PDF</option>
              <option value="docx">Word</option>
              <option value="xlsx">Excel</option>
              <option value="pptx">PowerPoint</option>
              <option value="txt">文本</option>
            </select>
          </div>
        </div>
        <div className="flex space-x-2">
          <Button onClick={handleSearch} variant="primary" size="small">
            🔍 搜索
          </Button>
          <Button onClick={handleResetFilters} variant="outline" size="small">
            🔄 重置
          </Button>
          <Button onClick={onRefresh} variant="outline" size="small">
            ↻ 刷新
          </Button>
        </div>
      </div>

      {/* 文档列表 */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
        {documents.length === 0 ? (
          <div className="text-center py-12">
            <div className="text-gray-400 text-6xl mb-4">📄</div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">暂无文档</h3>
            <p className="text-gray-500">还没有上传任何文档</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    文档
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    类型
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    大小
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    状态
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    分块数
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    上传时间
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    操作
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {documents.map((doc) => (
                  <tr key={doc.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <span className="text-2xl mr-3">{getTypeIcon(doc.file_type)}</span>
                        <div>
                          <div className="text-sm font-medium text-gray-900">
                            {doc.original_filename}
                          </div>
                          {doc.category && (
                            <div className="text-xs text-gray-500">
                              分类: {doc.category.name}
                            </div>
                          )}
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {doc.file_type.toUpperCase()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {formatFileSize(doc.file_size)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusStyle(doc.status)}`}>
                        {getStatusName(doc.status)}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {doc.chunk_count || 0}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {formatDate(doc.created_at)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      <div className="flex space-x-2">
                        <button
                          onClick={() => onDelete(doc.id)}
                          className="text-red-600 hover:text-red-900 transition-colors"
                          title="删除"
                        >
                          🗑️
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* 分页信息 */}
      {documents.length > 0 && (
        <div className="bg-white px-4 py-3 border border-gray-200 rounded-lg">
          <div className="flex items-center justify-between">
            <div className="text-sm text-gray-700">
              共 {documents.length} 个文档
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default DocumentList;