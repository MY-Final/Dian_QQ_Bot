import axios, { AxiosError, type AxiosResponse } from 'axios'

const ACCESS_TOKEN_KEY = 'dian_access_token'
const CURRENT_USER_KEY = 'dian_current_user'

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

export interface AuthUser {
  id: string
  username: string
  email: string
  role: string
}

export interface LoginPayload {
  access_token: string
  refresh_token: string
  token_type: string
  user: AuthUser
}

export function getAccessToken(): string | null {
  return localStorage.getItem(ACCESS_TOKEN_KEY)
}

export function setAuthSession(loginPayload: LoginPayload): void {
  localStorage.setItem(ACCESS_TOKEN_KEY, loginPayload.access_token)
  localStorage.setItem(CURRENT_USER_KEY, JSON.stringify(loginPayload.user))
}

export function clearAuthSession(): void {
  localStorage.removeItem(ACCESS_TOKEN_KEY)
  localStorage.removeItem(CURRENT_USER_KEY)
}

export function getCurrentUserFromStorage(): AuthUser | null {
  const rawUser = localStorage.getItem(CURRENT_USER_KEY)
  if (!rawUser) {
    return null
  }

  try {
    return JSON.parse(rawUser) as AuthUser
  } catch {
    return null
  }
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
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api/v1',
  timeout: 30000, // 容器操作可能需要更长时间
  headers: {
    'Content-Type': 'application/json',
  },
})

api.interceptors.request.use((config) => {
  const token = getAccessToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
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
    if (axiosError.response?.status === 401) {
      clearAuthSession()
    }
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
  image_repo: string
  image_tag: string
  image_digest?: string
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
  image_registry?: string
  image_repo?: string
  image_tag?: string
}

export interface InstanceImageUpdate {
  image_registry?: string
  image_repo: string
  image_tag: string
  auto_pull?: boolean
}

export interface ImageRepositoryResult {
  name: string
  description: string
  registry: string
  is_official: boolean
  star_count: number
}

export interface LocalImageResult {
  id: string
  tags: string[]
  digests: string[]
  size: number
  created: string
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

  /** 获取内置数据库默认配置 */
  getDefaultDbConfig: () => api.get<ApiResponse<DatabaseConfig>>('/setup/default-db-config'),
  
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

  /** 更新实例镜像 */
  updateImage: (id: string, data: InstanceImageUpdate) =>
    api.patch<ApiResponse<Instance>>(`/instances/${id}/image`, data),

  /** 按当前镜像重建实例 */
  recreate: (id: string, autoPull: boolean = false) =>
    api.post<ApiResponse<Instance>>(`/instances/${id}/recreate`, null, { params: { auto_pull: autoPull } }),
  
  /** 获取实例日志 */
  logs: (id: string, tail: number = 100, cursor: number = 0) =>
    api.get<ApiResponse<InstanceLogsPayload>>(
      `/instances/${id}/logs`,
      { params: { tail, cursor } }
    ),
}

/**
 * 镜像管理 API
 */
export const imageApi = {
  /** 搜索仓库 */
  search: (query: string, registry?: string) =>
    api.get<ApiResponse<ImageRepositoryResult[]>>('/images/search', {
      params: { query, registry },
    }),

  /** 获取仓库标签 */
  tags: (repository: string, registry?: string) =>
    api.get<ApiResponse<{ tags: string[] }>>('/images/tags', {
      params: { repository, registry },
    }),

  /** 拉取镜像 */
  pull: (repository: string, tag: string, registry?: string) =>
    api.post<ApiResponse<{ image_ref: string; id: string; digest?: string }>>('/images/pull', {
      repository,
      tag,
      registry,
    }),

  /** 检查镜像可用 */
  ensure: (repository: string, tag: string, registry?: string, allowPull: boolean = false) =>
    api.post<ApiResponse<{ image_ref: string; available: boolean; pulled: boolean; digest?: string }>>(
      '/images/ensure',
      {
        repository,
        tag,
        registry,
        allow_pull: allowPull,
      },
    ),

  /** 本地镜像列表 */
  local: () => api.get<ApiResponse<LocalImageResult[]>>('/images/local'),

  /** 删除本地镜像 */
  removeLocal: (imageRef: string, force: boolean = false) =>
    api.delete<ApiResponse<{ image_ref: string; removed: boolean; force: boolean }>>(
      '/images/local',
      {
        params: { image_ref: imageRef, force },
      },
    ),
}

/**
 * 认证 API
 */
export const authApi = {
  /** 用户登录 */
  login: (username: string, password: string) =>
    api.post<ApiResponse<LoginPayload>>('/auth/login', { username, password }),

  /** 获取当前用户 */
  me: () => api.get<ApiResponse<AuthUser>>('/auth/me'),
}
