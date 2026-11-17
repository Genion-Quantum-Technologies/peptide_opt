"""
配置加载器 - 从 settings.yaml 加载配置
支持环境变量覆盖: PEPTIDE_<SECTION>_<KEY>
"""

import os
from pathlib import Path


# 尝试加载 .env 文件
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


# ============ CPU 核心数自动检测 ============

def _detect_cpu_cores() -> int:
    """
    自动检测可用 CPU 核心数，返回 80% 的核心数（向下取整）
    
    在 Docker 容器中，Python 3.10 的 os.cpu_count() 可能返回宿主机的全部核心数
    而非 Docker 限制的 CPU 数量。因此优先从 cgroup 读取实际限制。
    
    检测优先级：
    1. cgroup v2: /sys/fs/cgroup/cpu.max
    2. cgroup v1: /sys/fs/cgroup/cpu/cpu.cfs_quota_us + cpu.cfs_period_us
    3. os.sched_getaffinity (受 taskset/cpuset 影响)
    4. os.cpu_count() (fallback，可能不受 Docker --cpus 限制)
    """
    try:
        # 尝试 cgroup v2 (现代 Linux / Docker)
        cgroup_v2 = Path("/sys/fs/cgroup/cpu.max")
        if cgroup_v2.exists():
            content = cgroup_v2.read_text().strip()
            parts = content.split()
            if parts[0] != "max":
                quota = int(parts[0])
                period = int(parts[1])
                cgroup_cpus = quota / period
                cores = max(1, int(cgroup_cpus * 0.8))
                return cores

        # 尝试 cgroup v1 (旧版 Docker)
        cgroup_v1_quota = Path("/sys/fs/cgroup/cpu/cpu.cfs_quota_us")
        cgroup_v1_period = Path("/sys/fs/cgroup/cpu/cpu.cfs_period_us")
        if cgroup_v1_quota.exists() and cgroup_v1_period.exists():
            quota = int(cgroup_v1_quota.read_text().strip())
            period = int(cgroup_v1_period.read_text().strip())
            if quota > 0 and period > 0:
                cgroup_cpus = quota / period
                cores = max(1, int(cgroup_cpus * 0.8))
                return cores

        # 尝试 sched_getaffinity (受 cpuset 限制影响)
        try:
            cpu_count = len(os.sched_getaffinity(0))
        except (AttributeError, OSError):
            cpu_count = os.cpu_count() or 4

        # 使用 80% 的 CPU 核心，向下取整，最少 1 核
        cores = max(1, int(cpu_count * 0.8))
        return cores
    except Exception:
        return 4  # 出错时使用安全的默认值


# 应用启动时初始化 CPU 核心数（只计算一次）
DEFAULT_CPU_CORES: int = _detect_cpu_cores()


def get_default_cores() -> int:
    """
    获取默认 CPU 核心数
    
    优先级：
    1. CPU_CORES 环境变量（允许手动覆盖）
    2. 自动检测的 80% CPU 核心数
    """
    env_cores = os.environ.get('CPU_CORES')
    if env_cores:
        try:
            return int(env_cores)
        except ValueError:
            pass
    return DEFAULT_CPU_CORES
