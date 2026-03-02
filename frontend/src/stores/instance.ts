import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { 
  instanceApi, 
  systemApi,
  type Instance, 
  type InstanceCreate,
  type ApiResponse 
} from '../api'

// 系统状态
export const useSystemStore = defineStore('system', () => {
  const dockerStatus = ref<{
    running: boolean
    platform: string
    version: string
    message: string
  } | null>(null)
  
  const databaseStatus = ref<{
    connected: boolean
    database: string
    version: string
    message: string
  } | null>(null)
  
  const loading = ref(false)
  const error = ref<string | null>(null)

  // 检查 Docker 状态
  async function checkDocker() {
    loading.value = true
    error.value = null
    try {
      const response = await systemApi.dockerStatus()
      dockerStatus.value = response.data.data
      return response.data.success
    } catch (e: any) {
      error.value = e.message || '检查 Docker 状态失败'
      dockerStatus.value = {
        running: false,
        platform: 'unknown',
        version: '',
        message: '无法连接到 Docker'
      }
      return false
    } finally {
      loading.value = false
    }
  }

  // 检查数据库状态
  async function checkDatabase() {
    loading.value = true
    error.value = null
    try {
      const response = await systemApi.databaseStatus()
      databaseStatus.value = response.data.data
      return response.data.success
    } catch (e: any) {
      error.value = e.message || '检查数据库状态失败'
      databaseStatus.value = {
        connected: false,
        database: 'PostgreSQL',
        version: '',
        message: '无法连接到数据库'
      }
      return false
    } finally {
      loading.value = false
    }
  }

  // 检查所有系统状态
  async function checkAll() {
    await Promise.all([checkDocker(), checkDatabase()])
  }

  // 计算属性：系统是否就绪
  const isSystemReady = computed(() => {
    return dockerStatus.value?.running && databaseStatus.value?.connected
  })

  return {
    dockerStatus,
    databaseStatus,
    loading,
    error,
    isSystemReady,
    checkDocker,
    checkDatabase,
    checkAll
  }
})

// 实例管理 Store
export const useInstanceStore = defineStore('instances', () => {
  const instances = ref<Instance[]>([])
  const currentInstance = ref<Instance | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  // 获取实例列表
  async function fetchInstances() {
    loading.value = true
    error.value = null
    try {
      const response = await instanceApi.list()
      if (response.data.success) {
        instances.value = response.data.data || []
      } else {
        error.value = response.data.message
      }
    } catch (e: any) {
      error.value = e.message || '获取实例列表失败'
    } finally {
      loading.value = false
    }
  }

  // 获取单个实例详情
  async function fetchInstance(id: string) {
    loading.value = true
    error.value = null
    try {
      const response = await instanceApi.get(id)
      if (response.data.success) {
        currentInstance.value = response.data.data
        return response.data.data
      } else {
        error.value = response.data.message
        return null
      }
    } catch (e: any) {
      error.value = e.message || '获取实例详情失败'
      return null
    } finally {
      loading.value = false
    }
  }

  // 创建实例
  async function createInstance(data: InstanceCreate): Promise<Instance | null> {
    loading.value = true
    error.value = null
    try {
      const response = await instanceApi.create(data)
      if (response.data.success && response.data.data) {
        const newInstance = response.data.data
        instances.value.push(newInstance)
        return newInstance
      } else {
        error.value = response.data.message || '创建失败'
        return null
      }
    } catch (e: any) {
      error.value = e.message || '创建实例失败'
      return null
    } finally {
      loading.value = false
    }
  }

  // 启动实例
  async function startInstance(id: string) {
    loading.value = true
    error.value = null
    try {
      const response = await instanceApi.start(id)
      if (response.data.success && response.data.data) {
        updateInstanceInList(response.data.data)
        return true
      } else {
        error.value = response.data.message
        return false
      }
    } catch (e: any) {
      error.value = e.message || '启动实例失败'
      return false
    } finally {
      loading.value = false
    }
  }

  // 停止实例
  async function stopInstance(id: string) {
    loading.value = true
    error.value = null
    try {
      const response = await instanceApi.stop(id)
      if (response.data.success && response.data.data) {
        updateInstanceInList(response.data.data)
        return true
      } else {
        error.value = response.data.message
        return false
      }
    } catch (e: any) {
      error.value = e.message || '停止实例失败'
      return false
    } finally {
      loading.value = false
    }
  }

  // 重启实例
  async function restartInstance(id: string) {
    loading.value = true
    error.value = null
    try {
      const response = await instanceApi.restart(id)
      if (response.data.success && response.data.data) {
        updateInstanceInList(response.data.data)
        return true
      } else {
        error.value = response.data.message
        return false
      }
    } catch (e: any) {
      error.value = e.message || '重启实例失败'
      return false
    } finally {
      loading.value = false
    }
  }

  // 删除实例
  async function deleteInstance(id: string) {
    loading.value = true
    error.value = null
    try {
      const response = await instanceApi.delete(id)
      if (response.data.success) {
        instances.value = instances.value.filter(i => i.id !== id)
        if (currentInstance.value?.id === id) {
          currentInstance.value = null
        }
        return true
      } else {
        error.value = response.data.message
        return false
      }
    } catch (e: any) {
      error.value = e.message || '删除实例失败'
      return false
    } finally {
      loading.value = false
    }
  }

  // 获取实例日志
  async function fetchInstanceLogs(id: string, tail: number = 100) {
    loading.value = true
    error.value = null
    try {
      const response = await instanceApi.logs(id, tail)
      if (response.data.success) {
        return response.data.data?.logs || ''
      } else {
        error.value = response.data.message
        return ''
      }
    } catch (e: any) {
      error.value = e.message || '获取日志失败'
      return ''
    } finally {
      loading.value = false
    }
  }

  // 辅助函数：更新列表中的实例
  function updateInstanceInList(updatedInstance: Instance) {
    const index = instances.value.findIndex(i => i.id === updatedInstance.id)
    if (index !== -1) {
      instances.value[index] = updatedInstance
    }
    if (currentInstance.value?.id === updatedInstance.id) {
      currentInstance.value = updatedInstance
    }
  }

  return {
    // 状态
    instances,
    currentInstance,
    loading,
    error,
    
    // 方法
    fetchInstances,
    fetchInstance,
    createInstance,
    startInstance,
    stopInstance,
    restartInstance,
    deleteInstance,
    fetchInstanceLogs,
  }
})

export default useInstanceStore
