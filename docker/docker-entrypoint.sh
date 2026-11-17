#!/bin/bash
set -e

# Docker entrypoint script for Peptide Optimization Service

echo "=========================================="
echo "Peptide Optimization Service"
echo "=========================================="
echo "Starting at: $(date)"
echo ""

# Initialize conda
source /opt/conda/etc/profile.d/conda.sh
conda activate peptide

echo "Using Python: $(which python)"
echo "Python version: $(python --version)"
echo ""

# Argo supplies the explicit scientific stage command.
exec "$@"
