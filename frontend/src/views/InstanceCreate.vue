<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { instanceApi, type InstanceCreate } from '@/api'

const router = useRouter()
const loading = ref(false)

const form = reactive<InstanceCreate>({
  name: '',
  qq_number: '',
  protocol: 'napcat',
  description: '',
})

const rules = {
  name: [
    { required: true, message: '请输入实例名称', trigger: 'blur' },
    { min: 1, max: 100, message: '长度在 1 到 100 个字符', trigger: 'blur' },
  ],
  qq_number: [
    { required: true, message: '请输入QQ号', trigger: 'blur' },
    { min: 5, max: 15, message: 'QQ号长度在 5 到 15 位', trigger: 'blur' },
  ],
}

const formRef = ref()

const handleSubmit = async () => {
  if (!formRef.value) return
  
  await formRef.value.validate(async (valid: boolean) => {
    if (valid) {
      loading.value = true
      try {
        await instanceApi.create(form)
        ElMessage.success('创建成功')
        router.push('/')
      } catch (error) {
        ElMessage.error('创建失败')
      } finally {
        loading.value = false
      }
    }
  })
}

const handleReset = () => {
  formRef.value?.resetFields()
}

const goBack = () => {
  router.push('/')
}
</script>

<template>
  <div class="instance-create">
    <div class="header">
      <el-button @click="goBack">返回</el-button>
      <h1>创建 Bot 实例</h1>
    </div>

    <el-card class="form-card">
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="120px"
        @submit.prevent="handleSubmit"
      >
        <el-form-item label="实例名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入实例名称" />
        </el-form-item>

        <el-form-item label="QQ号" prop="qq_number">
          <el-input v-model="form.qq_number" placeholder="请输入QQ号" />
        </el-form-item>

        <el-form-item label="协议" prop="protocol">
          <el-select v-model="form.protocol" placeholder="请选择协议">
            <el-option label="NapCat" value="napcat" />
            <el-option label="LLOneBot" value="llonebot" />
            <el-option label="Custom" value="custom" />
          </el-select>
        </el-form-item>

        <el-form-item label="描述" prop="description">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="3"
            placeholder="请输入描述（可选）"
          />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" native-type="submit" :loading="loading">
            创建
          </el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<style scoped>
.instance-create {
  padding: 20px;
  max-width: 600px;
  margin: 0 auto;
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

.form-card {
  margin-top: 20px;
}
</style>
