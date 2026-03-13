import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { 
  instanceApi, 
  systemApi,
  getErrorMessage,
  type Instance, 
  type InstanceCreate,
} from '../api'

// ============ 系统状态 Store ============
export const useSystemStore = defineStore('system', () => {
  // State
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
  const lastCheckTime = ref<Date | null>(null)

  // Getters
  const isSystemReady = computed(() => {
    return dockerStatus.value?.running && databaseStatus.value?.connected
  })

  const statusSummary = computed(() => {
    if (!dockerStatus.value || !databaseStatus.value) {
      return '未检查'
    }
    if (isSystemReady.value) {
      return '运行正常'
    }
    const issues = []
    if (!dockerStatus.value.running) issues.push('Docker 未运行')
    if (!databaseStatus.value.connected) issues.push('数据库未连接')
    return issues.join('、')
  })

  // Actions
  async function checkDocker() {
    loading.value = true
    error.value = null
    try {
      const response = await systemApi.dockerStatus()
      dockerStatus.value = response.data.data || null
      return response.data.success
    } catch (err) {
      error.value = getErrorMessage(err, '检查 Docker 状态失败')
      dockerStatus.value = {
        running: false,
        platform: 'unknown',
        version: '',
        message: '无法连接到 Docker'
      }
      return false
    } finally {
      loading.value = false
      lastCheckTime.value = new Date()
    }
  }

  async function checkDatabase() {
    loading.value = true
    error.value = null
    try {
      const response = await systemApi.databaseStatus()
      databaseStatus.value = response.data.data || null
      return response.data.success
    } catch (err) {
      error.value = getErrorMessage(err, '检查数据库状态失败')
      databaseStatus.value = {
        connected: false,
        database: 'PostgreSQL',
        version: '',
        message: '无法连接到数据库'
      }
      return false
    } finally {
      loading.value = false
      lastCheckTime.value = new Date()
    }
  }

  async function checkAll() {
    await Promise.all([checkDocker(), checkDatabase()])
  }

  function reset() {
    dockerStatus.value = null
    databaseStatus.value = null
    loading.value = false
    error.value = null
    lastCheckTime.value = null
  }

  return {
    // State
    dockerStatus,
    databaseStatus,
    loading,
    error,
    lastCheckTime,
    // Getters
    isSystemReady,
    statusSummary,
    // Actions
    checkDocker,
    checkDatabase,
    checkAll,
    reset
  }
})

// ============ 实例管理 Store ============
export const useInstanceStore = defineStore('instances', () => {
  // State
  const instances = ref<Instance[]>([])
  const currentInstance = ref<Instance | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)
  const lastFetchTime = ref<Date | null>(null)
  const actionInstance = ref<string | null>(null) // 正在操作的实例 ID

  // Getters
  const runningInstances = computed(() => 
    instances.value.filter(i => i.status === 'running')
  )

  const stoppedInstances = computed(() => 
    instances.value.filter(i => i.status === 'stopped')
  )

  const errorInstances = computed(() => 
    instances.value.filter(i => i.status === 'error')
  )

  const instanceCount = computed(() => instances.value.length)

  // Actions
  async function fetchInstances(force = false) {
    // 如果数据很新（5秒内）且不强制刷新，则跳过
    if (!force && lastFetchTime.value) {
      const timeSinceLastFetch = Date.now() - lastFetchTime.value.getTime()
      if (timeSinceLastFetch < 5000) {
        return
      }
    }

    loading.value = true
    error.value = null
    try {
      const response = await instanceApi.list()
      if (response.data.success) {
        instances.value = response.data.data || []
        lastFetchTime.value = new Date()
      } else {
        error.value = response.data.message || '获取实例列表失败'
        instances.value = []
      }
    } catch (err) {
      error.value = getErrorMessage(err, '获取实例列表失败')
      instances.value = []
    } finally {
      loading.value = false
    }
  }

  async function fetchInstance(id: string) {
    loading.value = true
    error.value = null
    try {
      const response = await instanceApi.get(id)
      if (response.data.success && response.data.data) {
        currentInstance.value = response.data.data
        // 更新列表中的实例
        updateInstanceInList(response.data.data)
        return response.data.data
      } else {
        error.value = response.data.message || '获取实例详情失败'
        return null
      }
    } catch (err) {
      error.value = getErrorMessage(err, '获取实例详情失败')
      return null
    } finally {
      loading.value = false
    }
  }

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
    } catch (err) {
      error.value = getErrorMessage(err, '创建实例失败')
      return null
    } finally {
      loading.value = false
    }
  }

  async function startInstance(id: string): Promise<boolean> {
    error.value = null
    actionInstance.value = id
    try {
      const response = await instanceApi.start(id)
      if (response.data.success && response.data.data) {
        updateInstanceInList(response.data.data)
        return true
      } else {
        error.value = response.data.message || '启动失败'
        return false
      }
    } catch (err) {
      error.value = getErrorMessage(err, '启动实例失败')
      return false
    } finally {
      actionInstance.value = null
    }
  }

  async function stopInstance(id: string): Promise<boolean> {
    error.value = null
    actionInstance.value = id
    try {
      const response = await instanceApi.stop(id)
      if (response.data.success && response.data.data) {
        updateInstanceInList(response.data.data)
        return true
      } else {
        error.value = response.data.message || '停止失败'
        return false
      }
    } catch (err) {
      error.value = getErrorMessage(err, '停止实例失败')
      return false
    } finally {
      actionInstance.value = null
    }
  }

  async function restartInstance(id: string): Promise<boolean> {
    error.value = null
    actionInstance.value = id
    try {
      const response = await instanceApi.restart(id)
      if (response.data.success && response.data.data) {
        updateInstanceInList(response.data.data)
        return true
      } else {
        error.value = response.data.message || '重启失败'
        return false
      }
    } catch (err) {
      error.value = getErrorMessage(err, '重启实例失败')
      return false
    } finally {
      actionInstance.value = null
    }
  }

  async function deleteInstance(id: string): Promise<boolean> {
    error.value = null
    actionInstance.value = id
    try {
      const response = await instanceApi.delete(id)
      if (response.data.success) {
        instances.value = instances.value.filter(i => i.id !== id)
        if (currentInstance.value?.id === id) {
          currentInstance.value = null
        }
        return true
      } else {
        error.value = response.data.message || '删除失败'
        return false
      }
    } catch (err) {
      error.value = getErrorMessage(err, '删除实例失败')
      return false
    } finally {
      actionInstance.value = null
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
    lastFetchTime,
    actionInstance,
    // 计算属性
    runningInstances,
    stoppedInstances,
    errorInstances,
    instanceCount,
    // 方法
    fetchInstances,
    fetchInstance,
    createInstance,
    startInstance,
    stopInstance,
    restartInstance,
    deleteInstance,
  }
})

export default useInstanceStore
