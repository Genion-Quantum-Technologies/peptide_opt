# Peptide Optimization CI/CD 文档和脚本

> ⚠️ **LEGACY / 已废弃（2026-07-14，ADR 0012）**：本指南描述**裸机 micromamba 单机部署**；`cicd/scripts/deploy.sh` 与 `start_peptide_service.sh` 硬编码 `/home/davis/...` 路径、并运行**已不存在的 `main.py`**（代码已迁入 `src/peptide_opt/`）。集群现由 **Argo Workflows** 运行（`peptide-opt` Deployment `replicas: 0`）。本地开发用 `python -m peptide_opt serve` 或 `docker compose -f docker/docker-compose.yml up -d`。下方步骤仅存档。

这个目录包含了Peptide Optimization服务的所有CI/CD相关文件，包括部署脚本和相关文档。

## 📂 目录结构

```
cicd/
├── scripts/                    # 部署和管理脚本
│   ├── deploy.sh              # 主部署脚本
│   └── start_peptide_service.sh  # 服务管理脚本
└── docs/                      # 文档
    └── DEPLOYMENT_GUIDE.md    # 部署指南（本文档）
```

## 🚀 快速开始

### 方式一：使用快捷脚本（推荐）

在项目根目录下，可以直接使用快捷脚本：

```bash
# 部署管理
./deploy start          # 启动服务
./deploy stop           # 停止服务
./deploy status         # 查看状态
./deploy logs           # 查看日志
./deploy test           # 测试连接
./deploy check          # 环境检查

# 服务管理
./service start         # 启动Peptide Optimization服务
./service stop          # 停止服务
./service status        # 查看服务状态
./service logs          # 查看实时日志
```

### 方式二：直接使用CI/CD脚本

```bash
# 进入脚本目录
cd cicd/scripts/

# 完整部署
./deploy.sh start

# 服务管理
./start_peptide_service.sh start
```

## 📋 脚本功能说明

### 核心脚本

| 脚本 | 功能 | 用途 |
|------|------|------|
| `deploy.sh` | 主部署脚本 | 统一管理服务的部署和状态检查 |
| `start_peptide_service.sh` | 服务管理 | 管理Peptide Optimization API服务 |

### 快捷脚本

| 脚本 | 功能 | 用途 |
|------|------|------|
| `deploy` | 部署快捷入口 | 在项目根目录快速访问部署功能 |
| `service` | 服务快捷入口 | 在项目根目录快速管理服务 |

## 🔧 配置说明

### 环境变量

主要配置在脚本中定义：

```bash
# 项目路径
PROJECT_DIR="/home/davis/projects/genion_quantum/peptide_opt"

# 服务配置
CONDA_ENV_NAME="peptide"
SERVICE_PORT=8001

# 日志配置
LOG_DIR="/home/davis/projects/serverlogs"
LOG_FILE="$LOG_DIR/peptide_opt.log"
```

### Conda环境

脚本会自动检查和创建conda环境：
- 环境名称：`peptide`
- 配置文件：`environment.yml`
- 自动安装依赖包

### 服务配置

- **端口**: 8001（本地服务，无需反向代理）
- **日志路径**: `/home/davis/projects/serverlogs/peptide_opt.log`
- **PID文件**: `/home/davis/projects/serverlogs/peptide_opt.pid`

## 📖 部署流程

1. **环境检查**: `./deploy check`
2. **启动服务**: `./deploy start`
3. **验证部署**: `./deploy status` 和 `./deploy test`

## 🔍 服务监控

### 状态检查
```bash
./deploy status     # 完整状态报告
./service status    # 服务详细状态
```

### 日志监控
```bash
./deploy logs       # 实时日志
./service logs      # 服务日志
```

### 连接测试
```bash
./deploy test       # 测试API连接
```

## 🔗 API访问

服务启动后可通过以下地址访问：

- **API根路径**: http://localhost:8001/
- **健康检查**: http://localhost:8001/health
- **API文档**: http://localhost:8001/docs
- **状态查询**: http://localhost:8001/status

## 🐛 故障排除

### 常见问题

1. **权限问题**: 确保所有脚本有执行权限
   ```bash
   chmod +x cicd/scripts/*.sh
   chmod +x deploy service
   ```

2. **环境问题**: 检查conda环境和依赖
   ```bash
   ./deploy check
   ```

3. **端口占用**: 脚本会自动检测并提示处理

4. **服务状态**: 使用状态检查命令
   ```bash
   ./deploy status
   ```

### 日志位置

- **服务日志**: `/home/davis/projects/serverlogs/peptide_opt.log`
- **错误排查**: 查看日志文件中的错误信息

### 重启服务

如果遇到问题，可以重启服务：
```bash
./deploy restart
```

## 🆚 与AstraMolecula的区别

| 特性 | AstraMolecula | Peptide Optimization |
|------|---------------|---------------------|
| 反向代理 | ✅ 有AutoSSH隧道 | ❌ 本地服务 |
| 端口 | 8000 | 8001 |
| 部署方式 | 云服务器+本地 | 仅本地 |
| 日志路径 | 统一serverlogs | 统一serverlogs |
| 脚本结构 | 相同 | 相同 |

## 🔄 更新记录

- 初始版本：基于AstraMolecula架构创建
- 简化部署：去除反向代理配置
- 本地服务：专注本地API服务

---

*最后更新: 2025年9月*
