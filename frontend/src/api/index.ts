import axios from 'axios'

const apiClient = axios.create({
  baseURL: '/api/v1',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
})

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error)
    return Promise.reject(error)
  }
)

export interface InstanceResponse {
  id: string
  name: string
  qq_number: string
  protocol: string
  status: string
  container_name: string
  port: number
  volume_path: string
  description: string | null
  created_at: string
  updated_at: string
}

export interface InstanceCreate {
  name: string
  qq_number: string
  protocol?: string
  description?: string
}

export const instanceApi = {
  list: () => apiClient.get<InstanceResponse[]>('/instances/'),
  
  get: (id: string) => apiClient.get<InstanceResponse>(`/instances/${id}`),
  
  create: (data: InstanceCreate) => 
    apiClient.post<InstanceResponse>('/instances/', data),
  
  start: (id: string) => 
    apiClient.post<InstanceResponse>(`/instances/${id}/start`),
  
  stop: (id: string) => 
    apiClient.post<InstanceResponse>(`/instances/${id}/stop`),
  
  restart: (id: string) => 
    apiClient.post<InstanceResponse>(`/instances/${id}/restart`),
  
  delete: (id: string) => 
    apiClient.delete(`/instances/${id}`),
  
  logs: (id: string, tail: number = 100) => 
    apiClient.get<{ logs: string }>(`/instances/${id}/logs`, { params: { tail } }),
}

export default apiClient
