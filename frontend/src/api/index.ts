import axios, { type AxiosResponse } from 'axios'

// 统一响应格式
export interface ApiResponse<T = any> {
  success: boolean
  message: string
  data?: T
  code?: number
}

const api = axios.create({
  baseURL: 'http://127.0.0.1:8000/api/v1',
  timeout: 30000, // 容器操作可能需要更长时间
  headers: {
    'Content-Type': 'application/json',
  },
})

// 响应拦截器 - 统一处理响应格式
api.interceptors.response.use(
  (response: AxiosResponse<ApiResponse>) => {
    // 后端已经返回统一格式，直接返回
    return response
  },
  (error) => {
    // 统一错误处理
    const errorResponse: ApiResponse = {
      success: false,
      message: error.response?.data?.message || error.message || '网络错误',
      code: error.response?.status || 500,
    }
    return Promise.reject(errorResponse)
  }
)

// ============ 数据模型定义 ============

export interface Instance {
  id: string
  name: string
  qq_number: string
  protocol: 'napcat' | 'llonebot' | 'custom'
  status: 'created' | 'running' | 'stopped' | 'error'
  container_name: string
  port: number
  volume_path: string
  description?: string
  created_at: string
  updated_at: string
}

export interface InstanceCreate {
  name: string
  qq_number: string
  protocol?: 'napcat' | 'llonebot' | 'custom'
  description?: string
}

// ============ API 方法 ============

/**
 * 系统管理 API
 */
export const systemApi = {
  /** 健康检查 */
  ping: () => api.get<ApiResponse<{ status: string; message: string }>>('/system/ping'),
  
  /** Docker 状态检查 */
  dockerStatus: () => api.get<ApiResponse<{
    running: boolean
    platform: string
    version: string
    message: string
  }>>('/system/docker'),
  
  /** 数据库状态检查 */
  databaseStatus: () => api.get<ApiResponse<{
    connected: boolean
    database: string
    version: string
    message: string
  }>>('/system/database'),
}

/**
 * Bot 实例管理 API
 */
export const instanceApi = {
  /** 获取所有实例列表 */
  list: () => api.get<ApiResponse<Instance[]>>('/instances/'),
  
  /** 获取单个实例详情 */
  get: (id: string) => api.get<ApiResponse<Instance>>(`/instances/${id}`),
  
  /** 创建新实例 */
  create: (data: InstanceCreate) => api.post<ApiResponse<Instance>>('/instances/', data),
  
  /** 启动实例 */
  start: (id: string) => api.post<ApiResponse<Instance>>(`/instances/${id}/start`),
  
  /** 停止实例 */
  stop: (id: string) => api.post<ApiResponse<Instance>>(`/instances/${id}/stop`),
  
  /** 重启实例 */
  restart: (id: string) => api.post<ApiResponse<Instance>>(`/instances/${id}/restart`),
  
  /** 删除实例 */
  delete: (id: string) => api.delete<ApiResponse<{ id: string }>>(`/instances/${id}`),
  
  /** 获取实例日志 */
  logs: (id: string, tail: number = 100) => api.get<ApiResponse<{ logs: string; instance_id: string; tail: number }>>(`/instances/${id}/logs`, {
    params: { tail }
  }),
}

// 统一导出
export { api }
export default api
