import axios, { AxiosError, type AxiosResponse } from 'axios'

// 统一响应格式
export interface ApiResponse<T = unknown> {
  success: boolean
  message: string
  data?: T
  code?: number
}

export interface ApiError {
  success: false
  message: string
  code: number
}

export function getErrorMessage(error: unknown, fallback: string): string {
  if (typeof error === 'object' && error !== null && 'message' in error) {
    const message = (error as { message?: unknown }).message
    if (typeof message === 'string' && message.trim().length > 0) {
      return message
    }
  }

  if (axios.isAxiosError(error)) {
    const axiosError = error as AxiosError<{ message?: string }>
    if (axiosError.response?.data?.message) {
      return axiosError.response.data.message
    }
  }

  return fallback
}

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api/v1',
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
  (error: unknown) => {
    // 统一错误处理
    const axiosError = error as AxiosError<{ message?: string }>
    const errorResponse: ApiError = {
      success: false,
      message: getErrorMessage(error, '网络错误'),
      code: axiosError.response?.status || 500,
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
  port_web_ui?: number
  port_ws?: number
  volume_path: string
  description?: string
  created_at: string
  updated_at: string
}

export interface InstanceLogsPayload {
  logs: string
  instance_id: string
  tail: number
  cursor: number
  next_cursor: number
  full_line_count: number
  has_more: boolean
}

export interface InstanceCreate {
  name: string
  qq_number: string
  protocol?: 'napcat' | 'llonebot' | 'custom'
  description?: string
  // 端口配置
  port_web_ui?: number  // Web UI 端口（可选）
  port_http?: number    // HTTP API 端口（可选，不指定则自动分配）
  port_ws?: number      // WebSocket 端口（可选，不指定则使用 HTTP+1）
  // NapCat 环境变量配置
  napcat_uid?: number   // NAPCAT_UID 用户 ID
  napcat_gid?: number   // NAPCAT_GID 组 ID
}

// 系统初始化相关
export interface DatabaseConfig {
  host: string
  port: number
  database: string
  username: string
  password: string
}

export interface AdminConfig {
  username: string
  email: string
  password: string
}

export interface InitializeRequest {
  database: DatabaseConfig
  admin: AdminConfig
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
 * 系统初始化 API
 */
export const setupApi = {
  /** 获取初始化状态 */
  getStatus: () => api.get<ApiResponse<{ initialized: boolean }>>('/setup/status'),
  
  /** 测试数据库连接 */
  testConnection: (config: DatabaseConfig) => api.post<ApiResponse<{ connected: boolean }>>('/setup/test-db-connection', config),
  
  /** 初始化数据库表 */
  initializeDb: (config: DatabaseConfig) => api.post<ApiResponse<{ initialized: boolean }>>('/setup/initialize-db', config),
  
  /** 创建管理员账号 */
  createAdmin: (data: { admin: { username: string; email: string; password: string; confirm_password: string }; database: DatabaseConfig }) => 
    api.post<ApiResponse<{ initialized: boolean; username: string }>>('/setup/create-admin', data),
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
  logs: (id: string, tail: number = 100, cursor: number = 0) =>
    api.get<ApiResponse<InstanceLogsPayload>>(
      `/instances/${id}/logs`,
      { params: { tail, cursor } }
    ),
}
