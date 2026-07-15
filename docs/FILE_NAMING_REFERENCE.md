# Peptide Optimization 项目文件名使用参考文档

本文档详细列出了 `peptide_opt` 项目中所有涉及指定文件名的代码位置，包括输入文件、中间文件、输出文件和配置文件。

> **⚠️ 链接失效提示（2026-07）**：本文档写于 `src/` 重构前，文中所有 `../<根级文件>` 链接（`../main.py`、`../peptide_optimizer.py`、`../async_task_processor.py`、`../config/…` 等）**均已失效**——代码已迁入 `src/peptide_opt/`（`core/optimizer.py`、`tasks/processor.py`、`api/app.py` 等，行号亦已漂移）。另：SeaweedFS 存储路径自 [ADR 0012](../../../../docs/adr/0012-compute-scheduling-plane-argo.md) 起由 `astra-step` 统一处理，实际前缀为 `jobs/peptide_optimization/{job_id}`；文中 `tasks/{task_id}/peptide/…` 为旧格式。行号仅供历史参考。

---

## 目录

1. [输入文件](#1-输入文件)
2. [中间处理文件](#2-中间处理文件)
3. [输出文件](#3-输出文件)
4. [配置文件](#4-配置文件)
5. [远程存储路径](#5-远程存储路径)
6. [文件路径汇总表](#6-文件路径汇总表)

---

## 1. 输入文件

### 1.1 `peptide.fasta` - 肽段序列文件

| 位置 | 文件 | 行号 | 用途 |
|------|------|------|------|
| 读取 | [peptide_optimizer.py](../peptide_optimizer.py#L108) | 108 | Step 1: OmegaFold 结构预测输入 |
| 读取 | [peptide_optimizer.py](../peptide_optimizer.py#L149) | 149 | Step 3: 读取肽段序列用于对接 |
| 读取 | [peptide_optimizer.py](../peptide_optimizer.py#L409) | 409 | Step 8: 读取原始序列进行分析 |
| 读取 | [peptide_optimizer.py](../peptide_optimizer.py#L494) | 494 | 运行流程时读取序列信息 |
| 检查 | [run_optimization.py](../run_optimization.py#L32) | 32 | 检查输入文件是否存在 |
| 读取 | [async_task_processor.py](../async_task_processor.py#L216) | 216 | 任务处理时检查文件 |
| 读取 | [async_task_processor.py](../async_task_processor.py#L243) | 243 | 读取序列计算参数 |

**路径格式**: `{input_dir}/peptide.fasta`

---

### 1.2 受体 PDB 文件 (动态文件名)

| 位置 | 文件 | 行号 | 用途 |
|------|------|------|------|
| 读取 | [peptide_optimizer.py](../peptide_optimizer.py#L119) | 119 | Step 2: 加载受体结构去除 HETATM |
| 参数 | [peptide_optimizer.py](../peptide_optimizer.py#L42) | 42 | 构造函数接收受体文件名参数 |
| 配置 | [async_task_processor.py](../async_task_processor.py#L220) | 220 | 从配置读取受体文件名（默认: `5ffg.pdb`）|
| 检查 | [async_task_processor.py](../async_task_processor.py#L221) | 221 | 检查受体文件是否存在 |
| 检测 | [run_optimization.py](../run_optimization.py#L39) | 39 | 自动检测 `*.pdb` 或 `*.pdbqt` 文件 |

**路径格式**: `{input_dir}/{receptor_pdb_filename}`

---

## 2. 中间处理文件

所有中间文件存储在 `{output_dir}/../middlefiles/` 目录中。

### 2.1 结构预测输出

| 文件名 | 文件 | 行号 | 用途 |
|--------|------|------|------|
| `peptide.pdb` | [peptide_optimizer.py](../peptide_optimizer.py#L137) | 137 | OmegaFold 预测的肽段结构 |

---

### 2.2 加氢处理文件

| 文件名 | 文件 | 行号 | 用途 |
|--------|------|------|------|
| `receptor.pdb` | [peptide_optimizer.py](../peptide_optimizer.py#L121) | 121 | 去除 HETATM 后的受体结构 |
| `receptorH.pdb` | [peptide_optimizer.py](../peptide_optimizer.py#L134) | 134 | 添加氢原子后的受体结构 |
| `peptideH.pdb` | [peptide_optimizer.py](../peptide_optimizer.py#L140) | 140 | 添加氢原子后的肽段结构 |

---

### 2.3 分子对接文件

| 文件名 | 文件 | 行号 | 用途 |
|--------|------|------|------|
| `receptorH.pdbqt` | [peptide_optimizer.py](../peptide_optimizer.py#L161) | 161 | 受体 PDBQT 格式（对接输入）|
| `peptideH.pdbqt` | [peptide_optimizer.py](../peptide_optimizer.py#L169) | 169 | 配体 PDBQT 格式（对接输入）|
| `complex.trg` | [peptide_optimizer.py](../peptide_optimizer.py#L177) | 177 | AGFR 生成的对接网格文件 |
| `peptide_ranked_{i}.pdb` | [peptide_optimizer.py](../peptide_optimizer.py#L200) | 200 | ADCP 对接输出（i=1 到 n_poses）|

**注**: `i` 取值范围为 1 到 `n_poses`（默认10）

---

### 2.4 原子排序文件

| 文件名 | 文件 | 行号 | 用途 |
|--------|------|------|------|
| `peptide_ranked_{i}_sorted.pdb` | [peptide_optimizer.py](../peptide_optimizer.py#L205) | 205 | 排序后的对接结果 |
| `peptide_ranked_{i}_sorted_H.pdb` | [peptide_optimizer.py](../peptide_optimizer.py#L211) | 211 | 排序并加氢后的对接结果 |
| `peptide_ranked_{i}_sorted_H.pdbqt` | [peptide_optimizer.py](../peptide_optimizer.py#L226) | 226 | 转换为 PDBQT 格式用于评分 |

---

### 2.5 评分文件

| 文件名 | 文件 | 行号 | 用途 |
|--------|------|------|------|
| `score_rank_1_{n_poses}.dat` | [peptide_optimizer.py](../peptide_optimizer.py#L222) | 222 | 写入：结合亲和力评分数据 |
| `score_rank_1_{n_poses}.dat` | [peptide_optimizer.py](../peptide_optimizer.py#L431) | 431 | 读取：用于最终分析 |

**示例**: 当 `n_poses=10` 时，文件名为 `score_rank_1_10.dat`

---

### 2.6 ProteinMPNN 中间文件

存储在 `{middlefiles}/pmpnn/complex{n}/` 目录中：

| 文件名 | 文件 | 行号 | 用途 |
|--------|------|------|------|
| `complex.pdb` | [peptide_optimizer.py](../peptide_optimizer.py#L299) | 299 | 合并的蛋白-肽段复合物结构 |
| `parsed_pdbs.jsonl` | [peptide_optimizer.py](../peptide_optimizer.py#L345) | 345 | ProteinMPNN 解析的链信息 |
| `assigned_pdbs.jsonl` | [peptide_optimizer.py](../peptide_optimizer.py#L346) | 346 | ProteinMPNN 分配的固定链信息 |
| `seqs/complex.fa` | [peptide_optimizer.py](../peptide_optimizer.py#L440) | 440 | ProteinMPNN 优化的序列输出 |

---

## 3. 输出文件

输出文件存储在 `{output_dir}/` 目录中。

### 3.1 最终结果文件

| 文件名 | 文件 | 行号 | 用途 |
|--------|------|------|------|
| `result.csv` | [peptide_optimizer.py](../peptide_optimizer.py#L466) | 466 | 最终分析报告（CSV 格式）|
| `complex{i}.pdb` | [peptide_optimizer.py](../peptide_optimizer.py#L457-458) | 457-458 | 优化后的复合物结构（i=1 到 n_poses）|

**输出目录说明**（来自 [run_optimization.py](../run_optimization.py#L53-57)）：
- `result.csv`: 详细的分析报告
- `complex1.pdb` - `complex10.pdb`: 优化后的复合物结构

---

## 4. 配置文件

### 4.1 任务配置文件

| 文件名 | 文件 | 行号 | 用途 |
|--------|------|------|------|
| `optimization_config.txt` | [async_task_processor.py](../async_task_processor.py#L165) | 165 | 任务参数配置文件 |

**路径格式**: `{job_dir}/optimization_config.txt`

**配置文件格式示例**:
```ini
receptor_pdb_filename=5ffg.pdb
n_poses=10
num_seq_per_target=10
proteinmpnn_seed=37
cores=12
cleanup=true
```

---

### 4.2 系统配置文件

| 文件名 | 文件 | 行号 | 用途 |
|--------|------|------|------|
| `settings.yaml` | [config/settings.py](../config/settings.py#L18) | 18 | 主配置文件 |

---

## 5. 远程存储路径

### 5.1 SeaweedFS 存储路径格式

| 路径模式 | 文件 | 行号 | 用途 |
|----------|------|------|------|
| `tasks/{task_id}/peptide/output/{filename}` | [main.py](../main.py#L228) | 228 | 主要输出路径 |
| `tasks/{task_id}/peptide/output/complexes/{filename}` | [main.py](../main.py#L229) | 229 | 复合物子目录 |
| `tasks/{task_id}/peptide/output/pdb/{filename}` | [main.py](../main.py#L230) | 230 | PDB 文件子目录 |
| `tasks/{task_id}/peptide/output/{relative_path}` | [async_task_processor.py](../async_task_processor.py#L502) | 502 | 上传结果到存储 |

---

### 5.2 下载 API 路径

| API 端点 | 文件 | 行号 | 用途 |
|----------|------|------|------|
| `/tasks/{task_id}/peptide/download/{filename}` | [main.py](../main.py#L192) | 192 | 下载肽优化输出文件 |

**本地文件搜索路径**（按优先级排序，来自 [main.py](../main.py#L263-279)）：
1. `{job_dir}/output/{filename}`
2. `{job_dir}/output/complexes/{filename}`
3. `{job_dir}/output/complex/{filename}`
4. `{job_dir}/output/pdb/{filename}`
5. `{job_dir}/output/pdbs/{filename}`
6. `{job_dir}/middlefiles/{filename}`
7. `{job_dir}/middlefiles/pdb/{filename}`
8. `{job_dir}/input/{filename}`
9. `{job_dir}/{filename}`

---

## 6. 文件路径汇总表

### 6.1 按处理阶段分类

| 阶段 | 文件类型 | 文件名模式 | 所在目录 |
|------|----------|------------|----------|
| **输入** | FASTA | `peptide.fasta` | `{input_dir}/` |
| **输入** | PDB | `{receptor_pdb_filename}` | `{input_dir}/` |
| **Step 1** | PDB | `peptide.pdb` | `{middle_dir}/` |
| **Step 2** | PDB | `receptor.pdb`, `receptorH.pdb`, `peptideH.pdb` | `{middle_dir}/` |
| **Step 3** | PDBQT | `receptorH.pdbqt`, `peptideH.pdbqt` | `{middle_dir}/` |
| **Step 3** | TRG | `complex.trg` | `{middle_dir}/` |
| **Step 3** | PDB | `peptide_ranked_{i}.pdb` | `{middle_dir}/` |
| **Step 4** | PDB | `peptide_ranked_{i}_sorted.pdb` | `{middle_dir}/` |
| **Step 4** | PDB | `peptide_ranked_{i}_sorted_H.pdb` | `{middle_dir}/` |
| **Step 5** | PDBQT | `peptide_ranked_{i}_sorted_H.pdbqt` | `{middle_dir}/` |
| **Step 5** | DAT | `score_rank_1_{n_poses}.dat` | `{middle_dir}/` |
| **Step 6** | PDB | `complex.pdb` | `{pmpnn_dir}/complex{n}/` |
| **Step 7** | JSONL | `parsed_pdbs.jsonl`, `assigned_pdbs.jsonl` | `{pmpnn_dir}/complex{n}/` |
| **Step 7** | FASTA | `complex.fa` | `{pmpnn_dir}/complex{n}/seqs/` |
| **输出** | CSV | `result.csv` | `{output_dir}/` |
| **输出** | PDB | `complex{i}.pdb` | `{output_dir}/` |

---

### 6.2 目录结构说明

```
{job_dir}/
├── input/
│   ├── peptide.fasta          # 输入: 肽段序列
│   └── {receptor}.pdb         # 输入: 受体结构
├── output/
│   ├── result.csv             # 输出: 分析报告
│   ├── complex1.pdb           # 输出: 优化复合物
│   ├── complex2.pdb
│   └── ...
├── middlefiles/
│   ├── peptide.pdb            # 中间: OmegaFold 预测结果
│   ├── receptor.pdb           # 中间: 清理后的受体
│   ├── receptorH.pdb          # 中间: 加氢受体
│   ├── peptideH.pdb           # 中间: 加氢肽段
│   ├── receptorH.pdbqt        # 中间: 对接格式受体
│   ├── peptideH.pdbqt         # 中间: 对接格式配体
│   ├── complex.trg            # 中间: 对接网格
│   ├── peptide_ranked_*.pdb   # 中间: 对接结果
│   ├── score_rank_1_*.dat     # 中间: 评分数据
│   └── pmpnn/
│       ├── complex1/
│       │   ├── complex.pdb
│       │   ├── parsed_pdbs.jsonl
│       │   ├── assigned_pdbs.jsonl
│       │   └── seqs/
│       │       └── complex.fa
│       ├── complex2/
│       └── ...
└── optimization_config.txt    # 配置: 任务参数
```

---

### 6.3 文件格式说明

| 扩展名 | 格式 | 描述 |
|--------|------|------|
| `.fasta` | FASTA | 蛋白质/肽段序列文件 |
| `.fa` | FASTA | FASTA 格式的简写扩展名 |
| `.pdb` | PDB | 蛋白质数据库格式，包含三维结构信息 |
| `.pdbqt` | PDBQT | AutoDock 对接格式，包含部分电荷和原子类型 |
| `.trg` | TRG | AGFR 对接网格文件 |
| `.jsonl` | JSON Lines | 每行一个 JSON 对象的文本格式 |
| `.dat` | DAT | 数据文件，纯文本格式 |
| `.csv` | CSV | 逗号分隔值，表格数据 |
| `.txt` | TXT | 纯文本配置文件 |
| `.yaml` | YAML | 系统配置文件格式 |

---

## 更新日志

- **2026-01-11**: 初始版本，完整记录所有文件名使用位置
