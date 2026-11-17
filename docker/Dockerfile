# Peptide Optimization Service
# ============================
# Multi-stage build with Mamba environment manager
# Requires: Python 3.10, CUDA 11.8, ADFRsuite, Vina, PyMOL, OmegaFold

# ============================
# Builder stage - Build Python wheel
# ============================
FROM python:3.10-slim AS builder

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build

# Copy package files
COPY pyproject.toml ./
COPY src/ ./src/

# Build wheel
RUN pip install build && python -m build --wheel

# ============================
# Runtime stage - Using Mamba
# ============================
# RTX 5090 (Blackwell) 需要 CUDA 12.8+
FROM nvidia/cuda:12.8.0-runtime-ubuntu22.04 AS runtime

# Avoid interactive prompts during installation
ENV DEBIAN_FRONTEND=noninteractive

# Install minimal system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    wget \
    git \
    libgomp1 \
    ca-certificates \
    libpq5 \
    libgl1-mesa-glx \
    libglu1-mesa \
    libxrender1 \
    libxft2 \
    libxext6 \
    libfreetype6 \
    libpng16-16 \
    libtk8.6 \
    libsm6 \
    libice6 \
    libxt6 \
    && rm -rf /var/lib/apt/lists/*

# ============================
# Install Miniforge (includes Mamba)
# ============================
ENV CONDA_DIR=/opt/conda
ENV PATH="${CONDA_DIR}/bin:${PATH}"

RUN wget -q https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-x86_64.sh -O /tmp/miniforge.sh \
    && bash /tmp/miniforge.sh -b -p ${CONDA_DIR} \
    && rm /tmp/miniforge.sh \
    && conda clean -afy

# ============================
# Create conda environment from environment.yml
# ============================
WORKDIR /app

# Copy environment file first (for better caching)
COPY environment.yml ./environment.yml

# Create environment using mamba (much faster than conda)
# Note: We modify torch version for CUDA 11.8 compatibility
RUN mamba env create -f environment.yml -n peptide \
    && mamba clean -afy

# Activate environment by default
ENV CONDA_DEFAULT_ENV=peptide
ENV PATH="${CONDA_DIR}/envs/peptide/bin:${PATH}"

# ============================
# Install PyTorch with CUDA 12.8 (RTX 5090 Blackwell support)
# 使用 PyTorch Nightly 版本以支持最新 GPU 架构
# ============================
RUN mamba run -n peptide pip install --no-cache-dir --pre \
    torch torchvision torchaudio \
    --index-url https://download.pytorch.org/whl/nightly/cu128

# ============================
# Install OmegaFold (after PyTorch)
# 重要：使用 --no-deps 跳过依赖检查，避免降级 PyTorch
# 然后手动安装 fair-esm 依赖
# ============================
RUN mamba run -n peptide pip install --no-cache-dir --no-deps \
    git+https://github.com/HeliXonProtein/OmegaFold.git && \
    mamba run -n peptide pip install --no-cache-dir fair-esm

# ============================
# Install AutoDock Vina from conda-forge (provides vina binary)
# ============================
RUN mamba install -n peptide -c conda-forge -y vina && \
    mamba clean -afy

# ============================
# Pre-download OmegaFold model weights (model 2)
# This prevents downloading during container runtime
# 注意：Docker build 时无 GPU，使用 cpu 下载模型；运行时自动使用 GPU
# ============================
RUN mkdir -p /tmp/omegafold_test && \
    echo ">test\nMKLLSVLLFLSLLVLQLVQSGAEVKKPGASVKVSCKASGGTFSSYAISWVRQAPGQGLEWMGGIIPIFGTANYAQKFQGRVTITADEST" > /tmp/omegafold_test/test.fasta && \
    mamba run -n peptide omegafold --model 2 /tmp/omegafold_test/test.fasta /tmp/omegafold_test/output || true && \
    rm -rf /tmp/omegafold_test

# Move the downloaded model to a system location accessible by all users
RUN mkdir -p /opt/omegafold_models && \
    if [ -d /root/.cache/omegafold_ckpt ]; then \
        cp -r /root/.cache/omegafold_ckpt/* /opt/omegafold_models/ && \
        chmod -R 755 /opt/omegafold_models; \
    fi

# ============================
# Install ADFRsuite (AutoDock CrankPep)
# ============================
WORKDIR /opt
RUN wget -q https://ccsb.scripps.edu/adfr/download/1038/ADFRsuite_Linux-x86_64_1.0.tar.gz \
    && tar zxf ADFRsuite_Linux-x86_64_1.0.tar.gz \
    && cd ADFRsuite_x86_64Linux_1.0 \
    && ./install.sh -d /opt/ADFRsuite-1.0 -c 0 \
    && cd .. \
    && rm -rf ADFRsuite_Linux-x86_64_1.0.tar.gz ADFRsuite_x86_64Linux_1.0

# Add ADFRsuite to PATH (after conda to avoid Python conflicts)
ENV PATH="${PATH}:/opt/ADFRsuite-1.0/bin"

WORKDIR /app

# Copy wheel from builder and install application
COPY --from=builder /build/dist/*.whl ./
RUN mamba run -n peptide pip install --no-cache-dir *.whl && rm -f *.whl

# Copy additional files
COPY docker/docker-entrypoint.sh /docker-entrypoint.sh
COPY vendor/ProteinMPNN/ ./vendor/ProteinMPNN/

# Create non-root user
RUN useradd --create-home --shell /bin/bash appuser

# Copy OmegaFold models to appuser's cache directory
RUN mkdir -p /home/appuser/.cache/omegafold_ckpt && \
    if [ -d /opt/omegafold_models ]; then \
        cp -r /opt/omegafold_models/* /home/appuser/.cache/omegafold_ckpt/ && \
        chown -R appuser:appuser /home/appuser/.cache; \
    fi

# Set permissions
RUN chmod +x /docker-entrypoint.sh && \
    chown -R appuser:appuser /app

# Create data directories
RUN mkdir -p /app/data/input /app/data/output /app/logs && \
    chown -R appuser:appuser /app/data /app/logs

# Initialize conda for the user
RUN conda init bash

USER appuser

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    LOG_LEVEL=INFO \
    PROTEINMPNN_PATH=/app/vendor/ProteinMPNN \
    CONDA_DEFAULT_ENV=peptide

EXPOSE 8000

HEALTHCHECK NONE

ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["python", "-m", "peptide_opt.steps", "--help"]
