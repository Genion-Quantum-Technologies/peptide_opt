# 项目结构重组说明

## 概述

本文档描述了 `peptide_opt` 项目从旧结构迁移到新的 Python 最佳实践结构的变更。

## 新旧结构对照

### 旧结构 → 新结构

```
旧文件/目录                          →  新文件/目录
─────────────────────────────────────────────────────────────────
peptide_optimizer.py                →  src/peptide_opt/core/optimizer.py
async_task_processor.py             →  src/peptide_opt/tasks/processor.py
main.py                             →  src/peptide_opt/api/app.py
utils.py                            →  src/peptide_opt/core/validators.py
run_optimization.py                 →  src/peptide_opt/cli.py

config/                             →  src/peptide_opt/config/
  ├── settings.py                   →    settings.py
  ├── settings.yaml                 →    settings.yaml
  ├── logging_config.py             →    logging.py
  └── database_config.py            →    (merged into settings.py)

database/                           →  src/peptide_opt/db/
  └── db.py                         →    postgres.py

services/storage/                   →  src/peptide_opt/storage/
  └── seaweed_storage.py            →    seaweed.py

Dockerfile                          →  docker/Dockerfile
docker-compose.yml                  →  docker/docker-compose.yml
docker-entrypoint.sh                →  docker/docker-entrypoint.sh

input/                              →  data/input/
output_test/                        →  data/output/

ProteinMPNN/                        →  vendor/ProteinMPNN/

(新增)                              →  tests/
                                        ├── conftest.py
                                        ├── unit/
                                        └── integration/

(新增)                              →  pyproject.toml
```

## 新结构说明

```
peptide_opt/
├── src/                           # 源代码目录 (PEP 517/518 推荐)
│   └── peptide_opt/              # 主包
│       ├── __init__.py           # 包初始化，导出版本号和主要类
│       ├── __main__.py           # CLI 入口 (python -m peptide_opt)
│       ├── cli.py                # 命令行工具实现
│       ├── api/                  # FastAPI 相关
│       │   ├── __init__.py
│       │   ├── app.py            # 应用工厂
│       │   ├── dependencies.py   # 依赖注入
│       │   └── routes/           # 路由模块
│       ├── core/                 # 核心业务逻辑
│       │   ├── __init__.py
│       │   ├── optimizer.py      # 肽段优化器主类
│       │   └── validators.py     # 文件验证工具
│       ├── tasks/                # 异步任务处理
│       │   ├── __init__.py
│       │   └── processor.py      # 任务处理器
│       ├── db/                   # 数据库层
│       │   ├── __init__.py
│       │   └── postgres.py       # PostgreSQL 连接池
│       ├── storage/              # 存储服务
│       │   ├── __init__.py
│       │   └── seaweed.py        # SeaweedFS 客户端
│       └── config/               # 配置管理
│           ├── __init__.py
│           ├── settings.py       # 配置加载器
│           ├── settings.yaml     # 配置文件
│           └── logging.py        # 日志配置
├── tests/                        # 测试目录
│   ├── conftest.py               # pytest fixtures
│   ├── unit/                     # 单元测试
│   └── integration/              # 集成测试
├── docker/                       # Docker 相关
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── docker-entrypoint.sh
├── scripts/                      # 运维脚本
├── docs/                         # 文档
├── data/                         # 数据目录 (gitignored)
│   ├── input/
│   └── output/
├── vendor/                       # 第三方依赖
│   └── ProteinMPNN/
├── pyproject.toml               # 项目配置
├── README.md
├── .env.example                 # 环境变量示例
└── .gitignore
```

## 主要改进

### 1. 包结构规范化
- 使用 `src/` 布局，符合 PEP 517/518 标准
- 模块按功能分层组织 (api, core, tasks, db, storage, config)

### 2. 配置管理改进
- 使用 dataclass 定义类型安全的配置类
- 支持环境变量覆盖 YAML 配置
- 单例模式确保配置一致性

### 3. 依赖管理
- 使用 `pyproject.toml` 替代 `setup.py`
- 明确区分生产依赖和开发依赖
- 配置代码质量工具 (black, isort, ruff, mypy)

### 4. 测试支持
- 独立的 `tests/` 目录
- pytest fixtures 支持
- 单元测试和集成测试分离

### 5. Docker 优化
- 多阶段构建减小镜像体积
- 非 root 用户运行
- 健康检查支持

## 使用方式

### 安装

```bash
# 开发模式安装
pip install -e ".[dev]"

# 生产安装
pip install .
```

### 运行

```bash
# 启动 API 服务
peptide-opt serve --host 0.0.0.0 --port 8000

# 或使用 python -m
python -m peptide_opt serve

# 直接运行优化
peptide-opt run --input-dir ./data/input --output-dir ./data/output

# 运行测试
pytest
```

### Docker

```bash
# 构建镜像
cd docker && docker compose build

# 启动服务
docker compose up -d

# 查看日志
docker compose logs -f peptide-opt
```

## 迁移注意事项

1. **导入路径变更**: 所有导入需要更新为新路径
   ```python
   # 旧
   from peptide_optimizer import PeptideOptimizer
   
   # 新
   from peptide_opt.core.optimizer import PeptideOptimizer
   # 或
   from peptide_opt import PeptideOptimizer
   ```

2. **配置文件位置**: 配置文件现在位于包内
   - 开发时: `src/peptide_opt/config/settings.yaml`
   - 部署时: 通过环境变量覆盖

3. **ProteinMPNN**: 移动到 `vendor/` 目录
   - 建议使用 git submodule 管理

4. **数据目录**: 使用 `data/` 目录
   - `data/input/`: 输入文件
   - `data/output/`: 输出结果

## 保留的旧文件

以下旧文件当时暂时保留以保持向后兼容。**注（2026-07）：这些根级旧文件后续已全部删除，代码只保留在 `src/peptide_opt/` 下，迁移已完成。**

- `peptide_optimizer.py` → 使用 `src/peptide_opt/core/optimizer.py`
- `async_task_processor.py` → 使用 `src/peptide_opt/tasks/processor.py`
- `main.py` → 使用 `src/peptide_opt/api/app.py`
- `config/` 目录 → 使用 `src/peptide_opt/config/`
- `database/` 目录 → 使用 `src/peptide_opt/db/`
- `services/` 目录 → 使用 `src/peptide_opt/storage/`
