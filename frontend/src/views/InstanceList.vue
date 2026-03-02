<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { instanceApi, type InstanceResponse } from '@/api'

const router = useRouter()
const instances = ref<InstanceResponse[]>([])
const loading = ref(false)

const statusColors: Record<string, string> = {
  running: 'success',
  stopped: 'info',
  error: 'danger',
  created: 'warning',
}

const loadInstances = async () => {
  loading.value = true
  try {
    const response = await instanceApi.list()
    instances.value = response.data
  } catch (error) {
    ElMessage.error('加载实例列表失败')
  } finally {
    loading.value = false
  }
}

const handleStart = async (id: string) => {
  try {
    await instanceApi.start(id)
    ElMessage.success('启动成功')
    loadInstances()
  } catch (error) {
    ElMessage.error('启动失败')
  }
}

const handleStop = async (id: string) => {
  try {
    await instanceApi.stop(id)
    ElMessage.success('停止成功')
    loadInstances()
  } catch (error) {
    ElMessage.error('停止失败')
  }
}

const handleRestart = async (id: string) => {
  try {
    await instanceApi.restart(id)
    ElMessage.success('重启成功')
    loadInstances()
  } catch (error) {
    ElMessage.error('重启失败')
  }
}

const handleDelete = async (id: string) => {
  try {
    await ElMessageBox.confirm('确定要删除这个实例吗？', '警告', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    })
    await instanceApi.delete(id)
    ElMessage.success('删除成功')
    loadInstances()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const goToCreate = () => {
  router.push('/create')
}

const goToDetail = (id: string) => {
  router.push(`/instance/${id}`)
}

onMounted(() => {
  loadInstances()
})
</script>

<template>
  <div class="instance-list">
    <div class="header">
      <h1>Bot 实例列表</h1>
      <el-button type="primary" @click="goToCreate">创建实例</el-button>
    </div>

    <el-table :data="instances" v-loading="loading" style="width: 100%">
      <el-table-column prop="name" label="名称" width="150" />
      <el-table-column prop="qq_number" label="QQ号" width="120" />
      <el-table-column prop="protocol" label="协议" width="100" />
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="statusColors[row.status] || 'info'">
            {{ row.status }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="port" label="端口" width="80" />
      <el-table-column prop="created_at" label="创建时间" width="180">
        <template #default="{ row }">
          {{ new Date(row.created_at).toLocaleString() }}
        </template>
      </el-table-column>
      <el-table-column label="操作" fixed="right" width="220">
        <template #default="{ row }">
          <el-button size="small" @click="goToDetail(row.id)">详情</el-button>
          <el-button 
            v-if="row.status !== 'running'" 
            size="small" 
            type="success"
            @click="handleStart(row.id)"
          >
            启动
          </el-button>
          <el-button 
            v-else 
            size="small" 
            type="warning"
            @click="handleStop(row.id)"
          >
            停止
          </el-button>
          <el-button 
            size="small" 
            type="danger"
            @click="handleDelete(row.id)"
          >
            删除
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-empty v-if="!loading && instances.length === 0" description="暂无Bot实例" />
  </div>
</template>

<style scoped>
.instance-list {
  padding: 20px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.header h1 {
  margin: 0;
  font-size: 24px;
  color: #333;
}
</style>
