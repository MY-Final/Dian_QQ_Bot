import { ref, computed } from 'vue'
import { getErrorMessage, systemApi } from '../api'

export interface DockerStatus {
  running: boolean
  platform: string
  version: string
  message: string
}

export function useDockerStatus() {
  const dockerStatus = ref<DockerStatus>({
    running: false,
    platform: '',
    version: '',
    message: '检查中...',
  })
  const loading = ref(false)

  // 获取 Docker 状态
  async function fetchDockerStatus() {
    loading.value = true
    try {
      const response = await systemApi.dockerStatus()
      
      // 后端返回格式：{ success: true, message: "...", data: { running: true, ... } }
      const responseData = response.data
      if (responseData.success && responseData.data) {
        dockerStatus.value = responseData.data
      } else {
        dockerStatus.value = {
          running: false,
          platform: 'unknown',
          version: '',
          message: responseData.message || 'Docker 状态检查失败',
        }
      }
    } catch (error) {
      dockerStatus.value = {
        running: false,
        platform: 'unknown',
        version: '',
        message: getErrorMessage(error, '无法连接到后端服务'),
      }
    } finally {
      loading.value = false
    }
  }

  // Docker 状态文本
  const statusText = computed(() => {
    if (loading.value) return '检查中...'
    return dockerStatus.value.running ? 'Docker 已连接' : 'Docker 未连接'
  })

  // Docker 状态样式
  const statusClass = computed(() => {
    if (loading.value) return 'text-gray-500'
    return dockerStatus.value.running ? 'text-green-600' : 'text-red-600'
  })

  // Docker 状态圆点样式
  const dotClass = computed(() => {
    if (loading.value) return 'bg-gray-400 animate-pulse'
    return dockerStatus.value.running ? 'bg-green-500' : 'bg-red-500'
  })

  return {
    dockerStatus,
    loading,
    statusText,
    statusClass,
    dotClass,
    fetchDockerStatus,
  }
}
