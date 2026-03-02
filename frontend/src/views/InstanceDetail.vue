<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { instanceApi, type InstanceResponse } from '@/api'

const route = useRoute()
const router = useRouter()

const instance = ref<InstanceResponse | null>(null)
const logs = ref('')
const loading = ref(false)
const logsLoading = ref(false)

const instanceId = computed(() => route.params.id as string)

const statusColors: Record<string, string> = {
  running: 'success',
  stopped: 'info',
  error: 'danger',
  created: 'warning',
}

const loadInstance = async () => {
  loading.value = true
  try {
    const response = await instanceApi.get(instanceId.value)
    instance.value = response.data
  } catch (error) {
    ElMessage.error('加载实例详情失败')
  } finally {
    loading.value = false
  }
}

const loadLogs = async () => {
  logsLoading.value = true
  try {
    const response = await instanceApi.logs(instanceId.value, 100)
    logs.value = response.data.logs || '暂无日志'
  } catch (error) {
    logs.value = '加载日志失败'
  } finally {
    logsLoading.value = false
  }
}

const handleStart = async () => {
  try {
    await instanceApi.start(instanceId.value)
    ElMessage.success('启动成功')
    loadInstance()
  } catch (error) {
    ElMessage.error('启动失败')
  }
}

const handleStop = async () => {
  try {
    await instanceApi.stop(instanceId.value)
    ElMessage.success('停止成功')
    loadInstance()
  } catch (error) {
    ElMessage.error('停止失败')
  }
}

const handleRestart = async () => {
  try {
    await instanceApi.restart(instanceId.value)
    ElMessage.success('重启成功')
    loadInstance()
  } catch (error) {
    ElMessage.error('重启失败')
  }
}

const handleDelete = async () => {
  try {
    await ElMessageBox.confirm('确定要删除这个实例吗？', '警告', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    })
    await instanceApi.delete(instanceId.value)
    ElMessage.success('删除成功')
    router.push('/')
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const goBack = () => {
  router.push('/')
}

onMounted(() => {
  loadInstance()
  loadLogs()
})
</script>

<template>
  <div class="instance-detail">
    <div class="header">
      <el-button @click="goBack">返回</el-button>
      <h1>实例详情</h1>
    </div>

    <div v-loading="loading">
      <el-card v-if="instance" class="info-card">
        <template #header>
          <div class="card-header">
            <span>{{ instance.name }}</span>
            <el-tag :type="statusColors[instance.status] || 'info'">
              {{ instance.status }}
            </el-tag>
          </div>
        </template>

        <el-descriptions :column="2" border>
          <el-descriptions-item label="实例ID">
            {{ instance.id }}
          </el-descriptions-item>
          <el-descriptions-item label="QQ号">
            {{ instance.qq_number }}
          </el-descriptions-item>
          <el-descriptions-item label="协议">
            {{ instance.protocol }}
          </el-descriptions-item>
          <el-descriptions-item label="端口">
            {{ instance.port }}
          </el-descriptions-item>
          <el-descriptions-item label="容器名">
            {{ instance.container_name }}
          </el-descriptions-item>
          <el-descriptions-item label="卷路径">
            {{ instance.volume_path }}
          </el-descriptions-item>
          <el-descriptions-item label="创建时间">
            {{ new Date(instance.created_at).toLocaleString() }}
          </el-descriptions-item>
          <el-descriptions-item label="更新时间">
            {{ new Date(instance.updated_at).toLocaleString() }}
          </el-descriptions-item>
          <el-descriptions-item label="描述" :span="2">
            {{ instance.description || '无' }}
          </el-descriptions-item>
        </el-descriptions>

        <div class="actions">
          <el-button 
            v-if="instance.status !== 'running'" 
            type="success"
            @click="handleStart"
          >
            启动
          </el-button>
          <el-button 
            v-if="instance.status === 'running'" 
            type="warning"
            @click="handleStop"
          >
            停止
          </el-button>
          <el-button type="primary" @click="handleRestart">重启</el-button>
          <el-button type="danger" @click="handleDelete">删除</el-button>
        </div>
      </el-card>

      <el-card class="logs-card">
        <template #header>
          <div class="card-header">
            <span>日志</span>
            <el-button size="small" @click="loadLogs">刷新</el-button>
          </div>
        </template>
        <pre v-loading="logsLoading" class="logs-content">{{ logs }}</pre>
      </el-card>
    </div>
  </div>
</template>

<style scoped>
.instance-detail {
  padding: 20px;
}

.header {
  display: flex;
  align-items: center;
  gap: 20px;
  margin-bottom: 20px;
}

.header h1 {
  margin: 0;
  font-size: 24px;
}

.info-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header span {
  font-size: 18px;
  font-weight: bold;
}

.actions {
  margin-top: 20px;
  display: flex;
  gap: 10px;
}

.logs-card {
  margin-top: 20px;
}

.logs-content {
  max-height: 400px;
  overflow-y: auto;
  background: #f5f5f5;
  padding: 10px;
  border-radius: 4px;
  font-size: 12px;
  line-height: 1.5;
  white-space: pre-wrap;
  word-break: break-all;
}
</style>
