# Peptide Optimization Service

肽段结构优化和序列设计服务，使用 ProteinMPNN 和分子对接技术。

## 📋 功能特性

- 🧬 使用 OmegaFold 进行肽段结构预测
- 🔬 分子对接和结合亲和力评分
- 🧪 使用 ProteinMPNN 进行序列优化
- 📊 性质分析和报告生成
- 🚀 异步任务处理
- 🗄️ PostgreSQL 数据库支持
- 📦 SeaweedFS 对象存储

## 🚀 快速开始

### 环境要求

- Python 3.10
- **CPU 即可运行** —— 生产部署（k3s `peptide-opt`）自 2026-07-14 起为**纯 CPU**：不申请 `nvidia.com/gpu`，核数经 `CPU_CORES` 分配。
- （可选）CUDA GPU 仅用于加速步骤 1 的 OmegaFold；**无 GPU 时 OmegaFold 自动回落 CPU**（实测 11-mer 约 26.5s，相对分钟级的 adcp 对接可忽略）。
  > ⚠️ 集群里那张 RTX 5070 已整卡独占给 `highfold-c2c`（AF2/JAX），**不要给 peptide-opt 申请 GPU**。

### 依赖软件安装

#### 1. OmegaFold (肽段结构预测)

```bash
# 方式一：直接安装
pip install OmegaFold

# 方式二：从 GitHub 安装
pip install git+https://github.com/HeliXonProtein/OmegaFold
```

详情参考: https://github.com/HeliXonProtein/OmegaFold

#### 2. AutoDock CrankPep (分子对接)

```bash
# 下载 ADFRsuite
wget https://ccsb.scripps.edu/adfr/download/1038/ADFRsuite_Linux-x86_64_1.0.tar.gz

# 解压
tar zxvf ADFRsuite_Linux-x86_64_1.0.tar.gz

# 安装
cd ADFRsuite_x86_64Linux_1.0
./install.sh -d ~/ADFRsuite-1.0 -c 0
```

详情参考: https://ccsb.scripps.edu/adcp/downloads/

#### 3. AutoDock Vina (结合评分计算)

```bash
# mamba 安装
mamba install -c conda-forge vina

```

#### 4. PyMOL (添加氢原子和突变)

```bash
mamba install -c conda-forge -c schrodinger pymol-bundle
```

#### 5. BioPython

```bash
pip install biopython
```

#### 6. ProteinMPNN (序列优化)

```bash
# 克隆到 vendor 目录（无需安装）
git clone https://github.com/dauparas/ProteinMPNN vendor/ProteinMPNN
```

### 项目安装

```bash
# 克隆仓库
git clone https://github.com/yourusername/peptide-opt.git
cd peptide-opt

# 方式一：使用 mamba 环境（推荐）
mamba env create -f environment.yml
mamba activate peptide

# 方式二：使用 venv
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows
pip install -e ".[dev]"
```

### 运行

#### 1. 启动 API 服务

```bash
# 使用命令行工具
peptide-opt serve --host 0.0.0.0 --port 8000

# 或使用 python -m
python -m peptide_opt serve
```

#### 2. 直接运行优化

```bash
# 运行完整优化流程
peptide-opt run --input-dir ./data/input --output-dir ./data/output

# 指定参数
peptide-opt run \
    --input-dir ./data/input \
    --output-dir ./data/output \
    --cores 8 \
    --no-cleanup
```

### Docker 部署

项目采用 **3-worker 架构**，每个 worker 独占部分 P-core 并共享 E-core（针对 Intel Core Ultra 9 285K 优化）。

```bash
# 复制环境变量配置
cp .env.example .env
# 编辑 .env 设置数据库密码等

# 构建并启动全部 3 个 worker
cd docker
docker compose up -d

# 仅启动部分 worker
docker compose up -d peptide-opt-1
docker compose up -d peptide-opt-1 peptide-opt-2

# 查看日志
docker compose logs -f                  # 所有 worker
docker compose logs -f peptide-opt-1    # 指定 worker
```

> **CPU 绑定策略**: Worker 1 → P-core 0-2, Worker 2 → P-core 3-5, Worker 3 → P-core 6-7，三者共享 E-core 8-23。

## 📁 项目结构

```
peptide_opt/
├── src/peptide_opt/          # 源代码
│   ├── api/                  # FastAPI 应用
│   ├── core/                 # 核心业务逻辑
│   ├── tasks/                # 异步任务处理
│   ├── db/                   # 数据库层
│   ├── storage/              # 存储服务
│   └── config/               # 配置管理
├── tests/                    # 测试
├── docker/                   # Docker 配置
├── docs/                     # 文档
├── vendor/                   # 第三方依赖 (ProteinMPNN)
└── data/                     # 数据目录
```

## 📖 API 文档

启动服务后访问:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 🔧 配置

配置通过以下方式管理（优先级从高到低）:

1. 环境变量 (`PEPTIDE_*`)
2. `.env` 文件
3. `config/settings.yaml`

主要配置项:

```yaml
# 数据库配置
DB_HOST=localhost
DB_PORT=5432
DB_USER=admin
DB_PASSWORD=secret
DB_NAME=peptide_opt

# 存储配置
SEAWEED_FILER_ENDPOINT=http://localhost:8888
SEAWEED_BUCKET=peptide-opt

# 任务处理器（⚠️ 仅遗留轮询 worker 用；集群自 2026-07-14 起改用 Argo，
# 轮询默认关闭，需 LEGACY_POLLER=1 才启动 —— 见 ADR 0012）
MAX_WORKERS=2
POLL_INTERVAL=30
```

> **CPU 核心自动检测**: 程序会按优先级检测可用 CPU 核心数——cgroup v2 → cgroup v1 → `sched_getaffinity`（受 cpuset 限制）→ `os.cpu_count()`——并自动使用 80% 的核心。在 Docker 容器中能正确识别 `--cpus` 和 `cpuset` 限制。

## 🧪 测试

```bash
# 运行所有测试
pytest

# 运行并显示覆盖率
pytest --cov=src/peptide_opt --cov-report=html

# 运行特定测试
pytest tests/unit/test_validators.py -v
```

## 📝 优化流程

1. **步骤1**: 使用 OmegaFold 预测肽段结构
2. **步骤2**: 添加氢原子到受体和肽段
3. **步骤3**: 分子对接
4. **步骤4**: 原子排序和添加氢原子
5. **步骤5**: 计算结合亲和力评分
6. **步骤6**: 合并肽段和蛋白质结构
7. **步骤7**: 使用 ProteinMPNN 进行序列优化
8. **步骤8**: 最终分析和报告生成

## 📂 输入文件要求

输入目录需要包含:
- `peptide.fasta`: 肽段序列文件
- `*.pdb`: 受体蛋白质结构文件

## 🤝 贡献

欢迎贡献代码！请查看 [CONTRIBUTING.md](docs/CONTRIBUTING.md)。

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE)
