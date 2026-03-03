# Dian QQ Bot 认证 API 文档

> 版本：v1.0  
> 最后更新：2026-03-03  
> 献给点点 💕

---

## 认证系统概述

Dian QQ Bot 使用 JWT（JSON Web Token）进行用户认证。所有需要权限的 API 都需要提供有效的 access_token。

### Token 类型

- **Access Token**: 用于访问受保护的 API，有效期 24 小时
- **Refresh Token**: 用于刷新 access_token，有效期 7 天

### 认证流程

1. 用户注册或登录获取 token
2. 在请求头中携带 access_token
3. Token 过期后使用 refresh_token 刷新
4. 刷新失败则重新登录

---

## 认证 API 接口

### 1. 用户注册

创建新用户账号。

**请求信息：**
- **Method:** POST
- **Path:** `/api/v1/auth/register`
- **Content-Type:** `application/json`

**请求体参数：**
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| username | string | 是 | 用户名（3-50 字符） |
| email | string | 是 | 邮箱地址 |
| password | string | 是 | 密码（最少 6 字符） |

**请求示例：**
```json
{
  "username": "admin",
  "email": "admin@example.com",
  "password": "securepassword123"
}
```

**响应示例（成功）：**
```json
{
  "success": true,
  "message": "注册成功",
  "data": {
    "id": "uuid-string",
    "username": "admin",
    "email": "admin@example.com",
    "role": "user"
  }
}
```

---

### 2. 用户登录

验证用户名和密码，返回 access_token 和 refresh_token。

**请求信息：**
- **Method:** POST
- **Path:** `/api/v1/auth/login`
- **Content-Type:** `application/json`

**请求体参数：**
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| username | string | 是 | 用户名 |
| password | string | 是 | 密码 |

**请求示例：**
```json
{
  "username": "admin",
  "password": "securepassword123"
}
```

**响应示例：**
```json
{
  "success": true,
  "message": "登录成功",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "user": {
      "id": "uuid-string",
      "username": "admin",
      "email": "admin@example.com",
      "role": "admin"
    }
  }
}
```

---

### 3. 刷新 Token

使用 refresh_token 获取新的 access_token。

**请求信息：**
- **Method:** POST
- **Path:** `/api/v1/auth/refresh`
- **Content-Type:** `application/json`

**请求体参数：**
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| refresh_token | string | 是 | 刷新令牌 |

**请求示例：**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**响应示例：**
```json
{
  "success": true,
  "message": "Token 刷新成功",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer"
  }
}
```

---

### 4. 获取当前用户信息

获取当前登录用户的详细信息。

**请求信息：**
- **Method:** GET
- **Path:** `/api/v1/auth/me`
- **Authorization:** Bearer Token

**请求头：**
```
Authorization: Bearer <access_token>
```

**响应示例：**
```json
{
  "success": true,
  "message": "获取用户信息成功",
  "data": {
    "id": "uuid-string",
    "username": "admin",
    "email": "admin@example.com",
    "role": "admin",
    "last_login": "2026-03-03T12:00:00"
  }
}
```

---

## 使用示例

### cURL 示例

```bash
# 登录并保存 token
TOKEN=$(curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"password123"}' \
  | jq -r '.data.access_token')

# 使用 token 访问受保护的 API
curl -X GET "http://localhost:8000/api/v1/instances/" \
  -H "Authorization: Bearer $TOKEN"
```

### JavaScript/Axios 示例

```javascript
import axios from 'axios'

const api = axios.create({
  baseURL: 'http://localhost:8000/api/v1',
})

// 登录
async function login(username, password) {
  const response = await api.post('/auth/login', {
    username,
    password,
  })
  
  const { access_token, refresh_token } = response.data.data
  localStorage.setItem('access_token', access_token)
  localStorage.setItem('refresh_token', refresh_token)
  
  return response.data
}

// 设置请求拦截器，自动添加 token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Token 过期自动刷新
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      // 尝试刷新 token
      const refreshToken = localStorage.getItem('refresh_token')
      try {
        const { data } = await api.post('/auth/refresh', {
          refresh_token: refreshToken,
        })
        
        localStorage.setItem('access_token', data.data.access_token)
        
        // 重试原请求
        error.config.headers.Authorization = `Bearer ${data.data.access_token}`
        return api.request(error.config)
      } catch (refreshError) {
        // 刷新失败，跳转到登录页
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        window.location.href = '/login'
        return Promise.reject(refreshError)
      }
    }
    return Promise.reject(error)
  }
)
```

### Vue 3 组合式 API 示例

```typescript
// composables/useAuth.ts
import { ref, computed } from 'vue'
import { api } from '@/api'

export function useAuth() {
  const user = ref(null)
  const token = ref(localStorage.getItem('access_token'))
  
  const isAuthenticated = computed(() => !!token.value)
  
  async function login(username: string, password: string) {
    const { data } = await api.post('/auth/login', {
      username,
      password,
    })
    
    token.value = data.data.access_token
    user.value = data.data.user
    
    localStorage.setItem('access_token', data.data.access_token)
    localStorage.setItem('refresh_token', data.data.refresh_token)
    
    return data
  }
  
  async function logout() {
    token.value = null
    user.value = null
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
  }
  
  async function fetchUser() {
    try {
      const { data } = await api.get('/auth/me')
      user.value = data.data
      return data
    } catch (error) {
      await logout()
      throw error
    }
  }
  
  return {
    user,
    token,
    isAuthenticated,
    login,
    logout,
    fetchUser,
  }
}
```

---

## 错误处理

### 常见错误响应

**401 Unauthorized - 未授权**
```json
{
  "success": false,
  "message": "Token 无效或已过期",
  "code": 401
}
```

**400 Bad Request - 请求参数错误**
```json
{
  "success": false,
  "message": "用户名已存在",
  "code": 400
}
```

**500 Internal Server Error - 服务器错误**
```json
{
  "success": false,
  "message": "服务器内部错误：详细错误信息",
  "code": 500
}
```

---

## 安全建议

1. **密码安全**
   - 密码使用 bcrypt 加密存储（12 轮）
   - 建议密码长度至少 8 位，包含大小写字母和数字
   - 不要使用弱密码

2. **Token 安全**
   - access_token 有效期 24 小时
   - refresh_token 有效期 7 天
   - 不要将 token 分享给他人
   - 生产环境使用 HTTPS

3. **会话管理**
   - 登出时清除本地存储的 token
   - 定期检查活跃会话
   - 发现异常立即修改密码

---

**祝使用愉快！献给点点 🐱💕**
