import { ref } from 'vue'
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

  return {
    dockerStatus,
    loading,
    fetchDockerStatus,
  }
}
