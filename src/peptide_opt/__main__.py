#!/usr/bin/env python3
"""
命令行入口点
支持 python -m peptide_opt 方式运行
"""

import argparse
import os
import sys


def main():
    """主入口函数"""
    parser = argparse.ArgumentParser(
        prog="peptide-opt",
        description="Peptide Optimization Service"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # run 子命令 - 直接运行优化
    run_parser = subparsers.add_parser("run", help="Run peptide optimization directly")
    run_parser.add_argument(
        "--input-dir",
        default="./data/input",
        help="Input directory containing peptide.fasta and receptor PDB"
    )
    run_parser.add_argument(
        "--output-dir",
        default="./data/output",
        help="Output directory for results"
    )
    run_parser.add_argument(
        "--cores",
        type=int,
        default=None,  # None 表示自动检测（80% CPU）
        help="Number of CPU cores for docking (default: auto-detect, use 80%% of available CPUs)"
    )
    run_parser.add_argument(
        "--step",
        type=int,
        choices=range(1, 9),
        help="Run specific step (1-8)"
    )
    run_parser.add_argument(
        "--no-cleanup",
        action="store_true",
        help="Keep intermediate files"
    )
    
    args = parser.parse_args()
    
    if args.command == "run":
        # 直接运行优化
        from peptide_opt.cli import run_optimizer
        run_optimizer(
            input_dir=args.input_dir,
            output_dir=args.output_dir,
            cores=args.cores,
            step=args.step,
            cleanup=not args.no_cleanup
        )
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
