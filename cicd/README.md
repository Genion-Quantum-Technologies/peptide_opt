# Peptide Optimization CI/CD 文档和脚本

> ⚠️ **LEGACY / 已废弃（2026-07-14，ADR 0012 · `docs/adr/0012-compute-scheduling-plane-argo.md`）**：本目录脚本描述的是**裸机 micromamba 单机部署**，`cicd/scripts/*.sh` 硬编码了上一位作者机器的 `/home/davis/...` 路径、并启动一个**已不存在的 `main.py`**（代码已重构进 `src/peptide_opt/`）；仓库根目录也**没有** `./deploy` / `./service` 快捷脚本。集群现由 **Argo Workflows** 运行（每任务一个 Workflow，`peptide-opt` Deployment `replicas: 0`）。本地开发请用 `python -m peptide_opt serve` 或 `docker compose -f docker/docker-compose.yml up -d`；下方内容仅存档，勿照抄。

这个目录包含了Peptide Optimization服务的所有CI/CD相关文件，包括部署脚本和相关文档。

## 📂 目录结构

```
cicd/
├── scripts/                    # 部署和管理脚本
│   ├── deploy.sh              # 主部署脚本
│   └── start_peptide_service.sh  # 服务管理脚本
└── docs/                      # 文档
    └── DEPLOYMENT_GUIDE.md    # 部署指南
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

# 服务管理
./service start         # 启动Peptide Optimization服务
./service stop          # 停止服务
./service status        # 查看服务状态
```

### 方式二：直接使用CI/CD脚本

```bash
# 进入脚本目录
cd cicd/scripts/

# 完整部署
./deploy.sh start
```

## 📋 脚本功能说明

### 核心脚本

| 脚本 | 功能 | 用途 |
|------|------|------|
| `deploy.sh` | 主部署脚本 | 统一管理服务的部署 |
| `start_peptide_service.sh` | 服务管理 | 管理Peptide Optimization API服务 |

### 配置脚本

| 脚本 | 功能 | 用途 |
|------|------|------|
| `deploy` | 快速部署 | 一键部署和管理 |
| `service` | 服务管理 | 快速服务操作 |

## 🔧 配置说明

### 环境变量

主要配置文件在各脚本顶部：

```bash
# 项目路径
PROJECT_DIR="/home/davis/projects/genion_quantum/peptide_opt"

# 服务配置
CONDA_ENV_NAME="peptide_opt"
SERVICE_PORT=8001

# 日志配置
LOG_DIR="/home/davis/projects/serverlogs"
```

### 部署流程

1. **环境检查**: `./deploy check`
2. **启动服务**: `./deploy start`
3. **验证部署**: `./deploy status` 和 `./deploy test`

## 📖 详细文档

更详细的部署说明请参考：[部署指南](docs/DEPLOYMENT_GUIDE.md)

## 🐛 故障排除

### 常见问题

1. **权限问题**: 确保所有脚本有执行权限
   ```bash
   chmod +x cicd/scripts/*.sh
   ```

2. **路径问题**: 脚本已配置相对路径，可在项目任意位置运行

3. **服务状态**: 使用 `./deploy status` 查看服务状态

### 日志位置

- Peptide Optimization服务: `/home/davis/projects/serverlogs/peptide_opt.log`

## 🆚 与AstraMolecula的区别

- **无需反向代理**: peptide_opt只在本地运行
- **简化部署**: 去除了AutoSSH和Nginx配置
- **统一日志**: 使用相同的日志目录结构

## 🔄 更新记录

- 基于AstraMolecula架构重构peptide_opt
- 简化为本地服务部署
- 统一日志管理
- 添加快捷访问脚本

---

*最后更新: 2025年9月*
