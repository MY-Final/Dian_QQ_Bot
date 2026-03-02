import axios from 'axios'

const api = axios.create({
  baseURL: 'http://127.0.0.1:8000/api/v1',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
})

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

export const instanceApi = {
  list: () => api.get<Instance[]>('/instances/'),
  
  get: (id: string) => api.get<Instance>(`/instances/${id}`),
  
  create: (data: InstanceCreate) => api.post<Instance>('/instances/', data),
  
  start: (id: string) => api.post<Instance>(`/instances/${id}/start`),
  
  stop: (id: string) => api.post<Instance>(`/instances/${id}/stop`),
  
  restart: (id: string) => api.post<Instance>(`/instances/${id}/restart`),
  
  delete: (id: string) => api.delete(`/instances/${id}`),
  
  logs: (id: string, tail: number = 100) => api.get<{ logs: string }>(`/instances/${id}/logs`, { params: { tail } }),
}

export default api
