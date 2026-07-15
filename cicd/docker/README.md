# Peptide Optimization CI/CD Docker 配置

> ⚠️ **LEGACY（2026-07-14，ADR 0012）**：集群已改用 Argo Workflows（`peptide-opt` Deployment `replicas: 0`），下方 CI compose 仅用于本地测试。**注意：本目录并无 `Dockerfile.ci`**——真正的构建文件是仓库 `docker/Dockerfile`（仓库根级**没有** `Dockerfile` / `docker-compose.yml`）。

本目录包含用于 CI/CD 流程的 Docker 配置文件。

## 目录结构

```
cicd/docker/
├── docker-compose.ci.yml  # CI/CD 测试环境（build 指向仓库 docker/Dockerfile）
└── README.md              # 本文件
```

## CI/CD 使用

### GitHub Actions 示例

```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Build and Test
        run: |
          docker compose -f cicd/docker/docker-compose.ci.yml up --build --abort-on-container-exit
          
      - name: Build Production Image
        run: |
          docker build -t peptide-opt:${{ github.sha }} .
```

### 本地 CI 测试

```bash
# 运行完整的 CI 测试
docker compose -f cicd/docker/docker-compose.ci.yml up --build

# 清理
docker compose -f cicd/docker/docker-compose.ci.yml down -v
```

## 生产部署

**生产由集群 Argo Workflows 运行**（每任务一个 Workflow：`fold→dock-score→redesign→report`，见 ADR 0012），`peptide-opt` Deployment `replicas: 0`——**不再用 docker-compose 部署生产**。本地/开发用 compose 时，文件在仓库 `docker/` 下（无根级 `Dockerfile` / `docker-compose.yml`）：

```bash
# 本地/开发（非生产）
docker compose -f docker/docker-compose.yml up -d
```

详见 [docs/DOCKER_DEPLOYMENT.md](../../docs/DOCKER_DEPLOYMENT.md)
