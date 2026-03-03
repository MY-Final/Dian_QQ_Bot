import { ref, computed } from 'vue'
import { setupApi } from '@/api'
import type { DatabaseConfig } from '@/types/setup'

export interface AdminConfig {
  username: string
  email: string
  password: string
  confirmPassword: string
}

export type SetupStep = 1 | 2 | 3 | 4 | 5

export function useSetupWizard() {
  // 当前步骤
  const currentStep = ref<SetupStep>(1)
  
  // 数据库模式
  const dbMode = ref(false) // false=内置，true=外部
  
  // 数据库配置
  const dbConfig = ref<DatabaseConfig>({
    host: 'localhost',
    port: 5432,
    database: 'dian_bot',
    username: 'postgres',
    password: '',
  })
  
  // 管理员配置
  const adminConfig = ref<AdminConfig>({
    username: '',
    email: '',
    password: '',
    confirm_password: '',
  })
  
  // 状态标记
  const dbConnected = ref(false)
  const dbInitialized = ref(false)
  const testingConnection = ref(false)
  const initializingDb = ref(false)
  const creatingAdmin = ref(false)
  
  // 密码可见性
  const showDbPassword = ref(false)
  const showAdminPassword = ref(false)
  const showConfirmPassword = ref(false)
  
  // 切换数据库模式
  function toggleDbMode() {
    dbMode.value = !dbMode.value
    dbConnected.value = false
    
    if (!dbMode.value) {
      // 内置模式：默认配置
      dbConfig.value = {
        host: 'localhost',
        port: 5432,
        database: 'dian_bot',
        username: 'postgres',
        password: '',
      }
    }
  }
  
  // 切换密码可见性
  function togglePassword(field: 'db' | 'admin' | 'confirm') {
    if (field === 'db') {
      showDbPassword.value = !showDbPassword.value
    } else if (field === 'admin') {
      showAdminPassword.value = !showAdminPassword.value
    } else {
      showConfirmPassword.value = !showConfirmPassword.value
    }
  }
  
  // 获取密码输入类型
  function getPasswordType(field: 'db' | 'admin' | 'confirm') {
    if (field === 'db') return showDbPassword.value ? 'text' : 'password'
    if (field === 'admin') return showAdminPassword.value ? 'text' : 'password'
    return showConfirmPassword.value ? 'text' : 'password'
  }
  
  // 验证密码强度
  function validatePassword(password: string) {
    const hasMinLength = password.length >= 8
    const hasLowercase = /[a-z]/.test(password)
    const hasUppercase = /[A-Z]/.test(password)
    const hasDigit = /\d/.test(password)
    const hasSpecial = /[@$!%*?&]/.test(password)
    
    return {
      hasMinLength,
      hasLowercase,
      hasUppercase,
      hasDigit,
      hasSpecial,
      isValid: hasMinLength && hasLowercase && hasUppercase && hasDigit && hasSpecial,
    }
  }
  
  // 测试数据库连接
  async function testConnection() {
    testingConnection.value = true
    dbConnected.value = false
    
    try {
      const response = await setupApi.testConnection(dbConfig.value)
      if (response.data.success) {
        dbConnected.value = true
        return { success: true, message: '数据库连接成功' }
      } else {
        return { success: false, message: response.data.message }
      }
    } catch (error: any) {
      return { success: false, message: error.message || '连接失败' }
    } finally {
      testingConnection.value = false
    }
  }
  
  // 初始化数据库表
  async function initializeDb() {
    initializingDb.value = true
    dbInitialized.value = false
    
    try {
      const response = await setupApi.initializeDb(dbConfig.value)
      if (response.data.success) {
        dbInitialized.value = true
        return { success: true, message: '数据库表创建成功' }
      } else {
        return { success: false, message: response.data.message }
      }
    } catch (error: any) {
      return { success: false, message: error.message || '初始化失败' }
    } finally {
      initializingDb.value = false
    }
  }
  
  // 创建管理员账号
  async function createAdmin() {
    creatingAdmin.value = true
    
    try {
      const response = await setupApi.createAdmin({
        admin: {
          username: adminConfig.value.username,
          email: adminConfig.value.email,
          password: adminConfig.value.password,
          confirm_password: adminConfig.value.confirmPassword,
        },
        database: dbConfig.value,
      })
      if (response.data.success) {
        // 标记刚刚完成初始化（用于路由守卫）
        sessionStorage.setItem('just_initialized', 'true')
        currentStep.value = 5  // 跳转到完成页面
        return { success: true, message: '管理员创建成功，系统初始化完成' }
      } else {
        return { success: false, message: response.data.message }
      }
    } catch (error: any) {
      return { success: false, message: error.message || '创建失败' }
    } finally {
      creatingAdmin.value = false
    }
  }
  
  // 验证步骤 2（数据库配置）
  function validateStep2() {
    if (dbMode.value && !dbConnected.value) {
      return { valid: false, message: '请先测试数据库连接' }
    }
    return { valid: true }
  }
  
  // 验证步骤 4（管理员配置）
  function validateStep4() {
    const { username, email, password, confirmPassword } = adminConfig.value
    
    if (!username || !email || !password) {
      return { valid: false, message: '请填写完整的管理员信息' }
    }
    
    if (password !== confirmPassword) {
      return { valid: false, message: '两次输入的密码不一致' }
    }
    
    const validation = validatePassword(password)
    if (!validation.isValid) {
      const requirements = []
      if (!validation.hasMinLength) requirements.push('至少 8 位')
      if (!validation.hasLowercase) requirements.push('小写字母')
      if (!validation.hasUppercase) requirements.push('大写字母')
      if (!validation.hasDigit) requirements.push('数字')
      if (!validation.hasSpecial) requirements.push('特殊字符')
      return { valid: false, message: '密码必须包含：' + requirements.join('、') }
    }
    
    return { valid: true }
  }
  
  // 下一步
  async function nextStep() {
    if (currentStep.value === 1) {
      // 步骤 1 → 步骤 2
      currentStep.value = 2
      return { success: true }
    } else if (currentStep.value === 2) {
      // 步骤 2 → 步骤 3：验证数据库连接
      const validation = validateStep2()
      if (!validation.valid) {
        return { success: false, message: validation.message }
      }
      currentStep.value = 3
      return { success: true }
    } else if (currentStep.value === 3) {
      // 步骤 3 → 步骤 4：初始化数据库表
      const result = await initializeDb()
      if (result.success) {
        currentStep.value = 4
      }
      return result
    } else if (currentStep.value === 4) {
      // 步骤 4 → 步骤 5：创建管理员
      const validation = validateStep4()
      if (!validation.valid) {
        return { success: false, message: validation.message }
      }
      return await createAdmin()
    }
    return { success: true }
  }
  
  // 上一步
  function prevStep() {
    if (currentStep.value > 1) {
      currentStep.value--
    }
  }
  
  // 获取步骤状态
  function getStepStatus(step: number): 'active' | 'completed' | 'pending' {
    if (step < currentStep.value) return 'completed'
    if (step === currentStep.value) return 'active'
    return 'pending'
  }
  
  return {
    // 状态
    currentStep,
    dbMode,
    dbConfig,
    adminConfig,
    dbConnected,
    dbInitialized,
    testingConnection,
    initializingDb,
    creatingAdmin,
    showDbPassword,
    showAdminPassword,
    showConfirmPassword,
    
    // 方法
    toggleDbMode,
    togglePassword,
    getPasswordType,
    validatePassword,
    testConnection,
    initializeDb,
    createAdmin,
    validateStep2,
    validateStep4,
    nextStep,
    prevStep,
    getStepStatus,
  }
}
