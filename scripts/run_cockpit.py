# -*- coding: utf-8 -*-
"""
scripts/run_cockpit.py — 联邦主权思考座舱一键冷启入口
=============================================================================
使用方法：
    python scripts/run_cockpit.py [--port 8765] [--host 127.0.0.1]
说明：
    - 纯标准库开箱即用，无需 pip install 任何第三方包；
    - 自动打开 http://127.0.0.1:8765 主座舱与 http://127.0.0.1:8765/world_tree 3D世界树。
"""
import sys
import os
from pathlib import Path

# 添加仓库根目录到 sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from cockpit.server import run_server

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Run Federation Cockpit")
    parser.add_argument("--host", default="127.0.0.1", help="Host address (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8765, help="Port (default: 8765)")
    args = parser.parse_args()

    run_server(host=args.host, port=args.port)
