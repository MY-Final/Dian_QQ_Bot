// Setup 相关类型定义

export interface DatabaseConfig {
  host: string
  port: number
  database: string
  username: string
  password: string
}

export interface AdminConfig {
  username: string
  email: string
  password: string
  confirmPassword: string
}

export type SetupStep = 1 | 2 | 3

export type DbMode = 'internal' | 'external'

export interface SetupState {
  currentStep: SetupStep
  dbMode: DbMode
  dbConfig: DatabaseConfig
  adminConfig: AdminConfig
  dbConnected: boolean
  testingConnection: boolean
  submitting: boolean
}

export interface PasswordValidation {
  hasMinLength: boolean
  hasLowercase: boolean
  hasUppercase: boolean
  hasDigit: boolean
  hasSpecial: boolean
  isValid: boolean
}
