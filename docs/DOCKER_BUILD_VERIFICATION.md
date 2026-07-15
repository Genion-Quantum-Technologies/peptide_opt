# Docker 构建验证报告

**日期**: 2026-01-12

> **⚠️ 历史构建报告（2026-01-12）**：本报告记录当时的构建，基础镜像为 `nvidia/cuda:11.8.0-runtime` + torch 2.0.1。**现行 `docker/Dockerfile` 已改为 `nvidia/cuda:12.8.0-runtime` + PyTorch nightly cu128**（RTX 5090/Blackwell）；下文版本号为当时的存档值，不代表现状。

## 验证结果

✅ **Docker 构建成功**

## 重要更新：使用 Mamba 环境管理

**更新原因**: 之前的 Dockerfile 直接使用 apt-get 安装 Python 和依赖，现在已改为使用 Mamba（Miniforge）作为 Python 环境管理器，与 `environment.yml` 保持一致。

### 主要变更

1. **环境管理**: 从 apt-get 直接安装改为使用 Mamba/Conda 环境
2. **基础镜像**: 仍使用 `nvidia/cuda:11.8.0-runtime-ubuntu22.04` 作为运行时基础镜像
3. **依赖安装**: 通过 `environment.yml` 和 Mamba 统一管理依赖

## 发现的问题及修复

### 1. CUDA 基础镜像版本问题

**问题**: 原 Dockerfile 使用 `nvidia/cuda:11.3.1-runtime-ubuntu20.04`，但 deadsnakes PPA 在 Ubuntu 20.04 上不再提供 Python 3.10 包。

**修复**: 更换为 `nvidia/cuda:11.8.0-runtime-ubuntu22.04`，Ubuntu 22.04 原生支持 Python 3.10。

```dockerfile
# 修改前
FROM nvidia/cuda:11.3.1-runtime-ubuntu20.04 as runtime

# 修改后
FROM nvidia/cuda:11.8.0-runtime-ubuntu22.04 AS runtime
```

### 2. 使用 Mamba 作为环境管理器

**问题**: 直接使用 apt-get 安装 Python 依赖与项目的 environment.yml 不一致。

**修复**: 安装 Miniforge (包含 Mamba)，使用 environment.yml 创建环境。

```dockerfile
# 安装 Miniforge
RUN wget -q https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-x86_64.sh -O /tmp/miniforge.sh \
    && bash /tmp/miniforge.sh -b -p ${CONDA_DIR} \
    && rm /tmp/miniforge.sh \
    && conda clean -afy

# 使用 mamba 创建环境
RUN mamba env create -f environment.yml -n peptide \
    && mamba clean -afy
```

### 3. PyTorch 版本不兼容

**问题**: OmegaFold 安装时会安装 `torch==1.12.0+cu113`，与新的 CUDA 11.8 基础镜像不兼容。

**修复**: 先安装 OmegaFold，然后强制重装 CUDA 11.8 兼容的 PyTorch 版本。

```dockerfile
# 先安装 OmegaFold
RUN mamba run -n peptide pip install --no-cache-dir \
    git+https://github.com/HeliXonProtein/OmegaFold.git

# 强制重装 PyTorch with CUDA 11.8
RUN mamba run -n peptide pip install --no-cache-dir --force-reinstall \
    torch==2.0.1+cu118 \
    --index-url https://download.pytorch.org/whl/cu118
```

### 4. PyMOL 依赖

**问题**: `peptide_opt/core/optimizer.py` 导入了 PyMOL (`from pymol import cmd`)。

**修复**: 通过 conda-forge 安装 `pymol-open-source`（在 environment.yml 中配置）。

### 5. Python 路径冲突

**问题**: ADFRsuite 安装后，其 `bin` 目录被添加到 PATH 最前面，导致 `python` 命令指向 ADFRsuite 自带的 Python 2.7。

**修复**: 
1. 将 ADFRsuite 路径添加到 PATH 末尾（而不是最前面）
2. 在 `docker-entrypoint.sh` 中显式激活 conda 环境

```bash
# docker-entrypoint.sh
source /opt/conda/etc/profile.d/conda.sh
conda activate peptide
exec python -m peptide_opt serve ...
```

### 6. Dockerfile 语法警告

**问题**: `FROM ... as` 中的 `as` 关键字大小写不一致，产生警告。

**修复**: 统一使用大写 `AS`。

## 修改的文件

| 文件 | 修改内容 |
|------|----------|
| `docker/Dockerfile` | 重构为使用 Mamba 环境管理，更新 PyTorch 安装顺序 |
| `docker/docker-entrypoint.sh` | 添加 conda 环境激活 |
| `environment.yml` | 移除 torch 版本（在 Dockerfile 中单独处理） |

## 构建后镜像信息

| 项目 | 信息 |
|------|------|
| 镜像名 | peptide-opt:mamba-test |
| 磁盘占用 | ~20.6GB |
| 压缩大小 | ~6.95GB |
| Python 版本 | 3.10.19 |
| CUDA 版本 | 11.8.0 |
| Ubuntu 版本 | 22.04 |
| 环境管理 | Mamba (Miniforge) |

## 已安装的主要依赖

- **PyTorch**: 2.0.1+cu118
- **BioPython**: 1.85
- **FastAPI**: 最新版本（通过 conda-forge）
- **PyMOL**: pymol-open-source（通过 conda-forge）
- **OmegaFold**: 从 GitHub 安装
- **AutoDock Vina**: 1.2.7
- **ADFRsuite**: 1.0

## 运行说明

### 构建镜像

```bash
cd /home/songyou/projects/peptide_opt
docker build -f docker/Dockerfile -t peptide-opt:latest .
```

### 运行服务

服务需要 PostgreSQL 数据库和 SeaweedFS 存储。推荐使用 docker-compose：

```bash
cd docker
docker-compose up -d
```

或者单独运行容器（需要配置环境变量）：

```bash
docker run -d \
  -p 8000:8000 \
  -e DB_HOST=your-postgres-host \
  -e DB_PORT=5432 \
  -e DB_USER=admin \
  -e DB_PASSWORD=secret \
  -e DB_NAME=peptide_opt \
  -e SEAWEED_FILER_ENDPOINT=http://your-seaweedfs:8888 \
  --gpus all \
  peptide-opt:latest
```

### 可用命令

| 命令 | 说明 |
|------|------|
| `serve` | 启动 API 服务（默认） |
| `run` | 运行肽段优化任务 |
| `shell` | 进入容器 shell |

## 注意事项

1. **GPU 支持**: 运行时需要 NVIDIA Docker runtime (`--gpus all`)
2. **数据库依赖**: 服务启动需要 PostgreSQL 连接
3. **存储依赖**: 文件存储需要 SeaweedFS 服务
4. **端口**: 默认 API 端口为 8000
