# GRA - 数据分级保护与访问控制系统

基于 Flask 的 Web 系统，实现用户数据的分级加密存储、细粒度访问控制与跨用户安全查询。

## 系统架构

```
data.xml → process_to_mongodb.py → MongoDB (user_data)
                                           ↓
                                    transfer_user_data.py
                                           ↓
                                    MongoDB (user/permission/request)
                                           ↓
                                    Flask Web (app.py)
```

## 功能特性

### 数据分级加密
| 等级 | 加密方式 | 适用字段 |
|------|---------|---------|
| L1 | 明文存储 | 名字 |
| L2 | 128-bit AES | 性别、年龄 |
| L3 | 256-bit AES | 身高、体重 |

### 用户系统
- **管理员**: 用户管理（增删）、数据同步、全局控制
- **普通用户**: 查看/修改个人数据、管理请求与权限

### 数据查询
用户间数据查询需经过 **请求 → 授权 → RSA加密传输 → RSA解密查看** 的完整链路：

1. 用户 A 向用户 B 发送查询请求
2. 用户 B 同意请求后，A 获得查询权限
3. A 发起查询，系统使用 B 的 AES 密钥解密 B 的数据
4. 再使用 A 的 RSA 公钥加密后传输
5. A 使用自己的 RSA 私钥解密查看

### 数据库结构

| 数据库 | 用途 |
|--------|------|
| `user` | 用户数据（含密钥、等级标签） |
| `user_data` | 原始导入数据（info/keys/levels/tags） |
| `request` | 查询请求记录 |
| `permission` | 授权记录 |

## 快速开始

### 环境要求
- Python 3.8+
- MongoDB（本地运行，默认端口 27017）
- pip 依赖

### 安装

```bash
# 安装依赖
pip install flask pymongo pycryptodome
```

### 运行

```bash
# 1. 导入测试数据到 MongoDB
python process_to_mongodb.py

# 2. 将数据传输到 user 库
python transfer_user_data.py

# 3. 创建请求与权限集合
python create_request_db.py
python create_permission_db.py

# 4. 启动 Web 服务
python app.py
```

浏览器访问 `http://localhost:5000`

### 默认管理员
- 用户名: `admin`
- 密码: `123456`

## 项目文件

| 文件 | 说明 |
|------|------|
| `app.py` | Flask Web 主应用 |
| `aes_utils.py` | AES 加密/解密工具 |
| `process_to_mongodb.py` | XML 数据解析并存储到 MongoDB |
| `transfer_user_data.py` | user_data → user 库数据迁移 |
| `decrypt_user_data.py` | 用户数据解密命令行工具 |
| `update_user_data.py` | 用户数据更新（含分级加密） |
| `send_request.py` | 发送数据查询请求 |
| `handle_request.py` | 处理（同意/拒绝）查询请求 |
| `query_data.py` | 跨用户安全数据查询 |
| `create_request_db.py` | 初始化 request 数据库 |
| `create_permission_db.py` | 初始化 permission 数据库 |
| `data.xml` | 示例用户测试数据 |
| `templates/` | HTML 页面模板 |

## 数据分级策略

- **L1（公开）**：基础身份标识，如姓名
- **L2（内部）**：一般个人信息，性别、年龄等
- **L3（敏感）**：高敏感个人信息，身高、体重等

跨用户查询时仅可解密 L1 和 L2 数据，L3 数据不可被查询者获取。
