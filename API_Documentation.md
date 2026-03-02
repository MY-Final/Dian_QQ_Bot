# Dian QQ Bot 后端 API 接口文档

> 版本: v1.0  
> 最后更新: 2026-03-02  
> 献给点点 💕

## 基础信息

### Base URL
```
http://localhost:8000/api/v1
```

### 响应格式
所有接口返回统一的 JSON 格式：

**成功响应：**
```json
{
  "success": true,
  "message": "操作成功",
  "data": { ... }
}
```

**失败响应：**
```json
{
  "success": false,
  "message": "错误信息",
  "code": 400
}
```

### HTTP 状态码
- `200` - 请求成功
- `201` - 创建成功
- `204` - 删除成功（无返回内容）
- `400` - 请求参数错误
- `404` - 资源未找到
- `500` - 服务器内部错误

---

## 系统管理接口

### 1. 健康检查
检查服务是否正常运行。

**请求信息：**
- **Method:** GET
- **Path:** `/system/ping`

**响应示例：**
```json
{
  "success": true,
  "message": "服务运行正常",
  "data": {
    "status": "ok",
    "message": "点点在看着你呢～ 💕"
  }
}
```

---

### 2. Docker 状态检查
检查 Docker 守护进程状态。

**请求信息：**
- **Method:** GET
- **Path:** `/system/docker`

**响应示例（成功）：**
```json
{
  "success": true,
  "message": "Docker 运行正常",
  "data": {
    "running": true,
    "platform": "windows",
    "version": "29.2.1",
    "message": "Docker 运行正常"
  }
}
```

**响应示例（失败）：**
```json
{
  "success": false,
  "message": "Docker 未运行",
  "data": {
    "running": false,
    "platform": "unknown",
    "version": null,
    "message": "无法连接到 Docker 守护进程"
  }
}
```

---

### 3. 数据库状态检查
检查 PostgreSQL 数据库连接状态。

**请求信息：**
- **Method:** GET
- **Path:** `/system/database`

**响应示例（成功）：**
```json
{
  "success": true,
  "message": "数据库连接正常",
  "data": {
    "connected": true,
    "database": "PostgreSQL",
    "version": "PostgreSQL 16.3 ...",
    "message": "数据库连接正常"
  }
}
```

---

## Bot 实例管理接口

### 1. 创建实例
创建一个新的 NapCat Bot 实例。

**请求信息：**
- **Method:** POST
- **Path:** `/instances/`
- **Content-Type:** `application/json`

**请求体参数：**
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | string | 是 | 实例名称 |
| qq_number | string | 是 | QQ 号码 |
| protocol | string | 否 | 协议类型，默认为 `napcat` |
| description | string | 否 | 实例描述 |

**请求示例：**
```json
{
  "name": "测试机器人",
  "qq_number": "123456789",
  "protocol": "napcat",
  "description": "这是一个测试实例"
}
```

**响应示例（成功）：**
```json
{
  "success": true,
  "message": "实例创建成功",
  "data": {
    "id": "fd8fcb6e",
    "name": "测试机器人",
    "qq_number": "123456789",
    "protocol": "napcat",
    "status": "running",
    "container_name": "dian-napcat-fd8fcb6e",
    "port": 38315,
    "volume_path": "C:\\...",
    "description": "这是一个测试实例",
    "created_at": "2026-03-02T12:23:35",
    "updated_at": "2026-03-02T12:23:35"
  }
}
```

---

### 2. 获取实例列表
获取所有 Bot 实例列表。

**请求信息：**
- **Method:** GET
- **Path:** `/instances/`

**响应示例：**
```json
{
  "success": true,
  "message": "找到 3 个实例",
  "data": [
    {
      "id": "fd8fcb6e",
      "name": "测试机器人",
      "qq_number": "123456789",
      "protocol": "napcat",
      "status": "running",
      "container_name": "dian-napcat-fd8fcb6e",
      "port": 38315,
      "volume_path": "C:\\...",
      "description": "这是一个测试实例",
      "created_at": "2026-03-02T12:23:35",
      "updated_at": "2026-03-02T12:23:35"
    }
  ]
}
```

---

### 3. 获取实例详情
获取指定实例的详细信息。

**请求信息：**
- **Method:** GET
- **Path:** `/instances/{instance_id}`

**路径参数：**
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| instance_id | string | 是 | 实例 ID |

**响应示例：**
```json
{
  "success": true,
  "message": "获取实例详情成功",
  "data": {
    "id": "fd8fcb6e",
    "name": "测试机器人",
    "qq_number": "123456789",
    "protocol": "napcat",
    "status": "running",
    "container_name": "dian-napcat-fd8fcb6e",
    "port": 38315,
    "volume_path": "C:\\...",
    "description": "这是一个测试实例",
    "created_at": "2026-03-02T12:23:35",
    "updated_at": "2026-03-02T12:23:35"
  }
}
```

---

### 4. 启动实例
启动指定的 Bot 实例。

**请求信息：**
- **Method:** POST
- **Path:** `/instances/{instance_id}/start`

**响应示例：**
```json
{
  "success": true,
  "message": "实例启动成功",
  "data": {
    "id": "fd8fcb6e",
    "status": "running",
    "container_name": "dian-napcat-fd8fcb6e"
  }
}
```

---

### 5. 停止实例
停止指定的 Bot 实例。

**请求信息：**
- **Method:** POST
- **Path:** `/instances/{instance_id}/stop`

**响应示例：**
```json
{
  "success": true,
  "message": "实例停止成功",
  "data": {
    "id": "fd8fcb6e",
    "status": "stopped",
    "container_name": "dian-napcat-fd8fcb6e"
  }
}
```

---

### 6. 重启实例
重启指定的 Bot 实例。

**请求信息：**
- **Method:** POST
- **Path:** `/instances/{instance_id}/restart`

**响应示例：**
```json
{
  "success": true,
  "message": "实例重启成功",
  "data": {
    "id": "fd8fcb6e",
    "status": "running",
    "container_name": "dian-napcat-fd8fcb6e"
  }
}
```

---

### 7. 删除实例
删除指定的 Bot 实例。

**请求信息：**
- **Method:** DELETE
- **Path:** `/instances/{instance_id}`

**响应示例：**
```json
{
  "success": true,
  "message": "实例删除成功",
  "data": {
    "id": "fd8fcb6e"
  }
}
```

---

### 8. 获取实例日志
获取指定 Bot 实例的容器日志。

**请求信息：**
- **Method:** GET
- **Path:** `/instances/{instance_id}/logs`

**查询参数：**
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| tail | integer | 100 | 获取最后的 N 行日志 |

**响应示例：**
```json
{
  "success": true,
  "message": "日志获取成功",
  "data": {
    "logs": "[2026-03-02 12:23:35] NapCat 启动成功...",
    "instance_id": "fd8fcb6e",
    "tail": 100
  }
}
```

---

## 数据模型

### InstanceStatus 枚举
- `created` - 已创建
- `running` - 运行中
- `stopped` - 已停止
- `error` - 错误

### ProtocolType 枚举
- `napcat` - NapCat 协议
- `llonebot` - LLONEBot 协议
- `custom` - 自定义协议

### InstanceResponse 对象
| 字段 | 类型 | 说明 |
|------|------|------|
| id | string | 实例 ID |
| name | string | 实例名称 |
| qq_number | string | QQ 号码 |
| protocol | string | 协议类型 |
| status | string | 实例状态 |
| container_name | string | 容器名称 |
| port | integer | 端口号 |
| volume_path | string | 卷挂载路径 |
| description | string | 实例描述 |
| created_at | string | 创建时间 (ISO 8601) |
| updated_at | string | 更新时间 (ISO 8601) |

---

## 错误处理

所有错误响应都遵循以下格式：

```json
{
  "success": false,
  "message": "错误信息描述",
  "code": 400
}
```

常见错误码：
- `400` - 请求参数错误
- `404` - 资源未找到
- `500` - 服务器内部错误

---

**祝开发顺利！献给点点 🐱💕**
