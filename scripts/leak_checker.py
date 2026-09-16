# -*- coding: utf-8 -*-
"""
leak_checker.py — 联邦开源仓库零泄漏合规扫描门禁 (FED-RELEASE-001)
=============================================================================
职责：
1. 深度扫描代码库、文档、配置文件中的敏感物理信息；
 2. 严厉拦截：物理真实 API Key、硬编码本地驱动器绝对路径（如 C 盘或任意盘符）、真实用户名/凭证；
3. 支持基准数据集 (HumanEval, BCB-Hard) 的测试语义白名单放行；
4. 退出码：0 (无泄漏，通过)，1 (检测到泄漏阻断，严禁 Commit / Push)。
"""
from __future__ import annotations

import os
import sys
import re
import argparse
from pathlib import Path
from typing import Dict, List, Tuple

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

BS = chr(92)

# 敏感特征正则库
PATTERNS = {
    "REAL_API_KEY": re.compile(
        r"(?:sk-[A-Za-z0-9]{20,}|AIza[A-Za-z0-9_-]{30,}|Bearer\s+[A-Za-z0-9_\-\.]{25,})"
    ),
    "PHYSICAL_DRIVE_PATH": re.compile(
        r"[A-Za-z]:[\\/](?:master|dsh-core|t1r1-lab|deep\s*seekapi|Gemini\s*key|fed-testbed|federation-open-source|zcode)",
        re.IGNORECASE
    ),
    "HARDCODED_ABSOLUTE_PATH": re.compile(
        r"[A-Za-z]:[\\/](?:Users|ProgramData|Windows|AppData)",
        re.IGNORECASE
    ),
    "LOCAL_USER_PATH": re.compile(
        r"(?:Users|home)[\\/]admin\b",
        re.IGNORECASE
    ),
    "HARDCODED_SECRET_ASSIGN": re.compile(
        r"(?i)(?:api_key|secret_key|private_key|auth_token)\s*=\s*['\"][A-Za-z0-9_\-]{20,}['\"]"
    )
}

IGNORED_DIRS = {".git", ".venv", "__pycache__", ".pytest_cache", ".idea", ".vscode"}
BENCHMARK_IGNORE_FILES = {"HumanEval.jsonl", "bcb_hard.jsonl"}


def scan_file(filepath: Path, repo_root: Path) -> List[Tuple[str, int, str, str]]:
    """扫描单个文件，返回 (规则名, 行号, 命中内容, 整行代码)"""
    violations = []
    is_benchmark_data = filepath.name in BENCHMARK_IGNORE_FILES

    try:
        content = filepath.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        return [("READ_ERROR", 1, str(e), "")]

    lines = content.splitlines()
    for line_idx, line in enumerate(lines, start=1):
        for rule_name, pat in PATTERNS.items():
            if is_benchmark_data and rule_name in ("LOCAL_USER_PATH", "HARDCODED_SECRET_ASSIGN"):
                continue

            for match in pat.finditer(line):
                matched_str = match.group(0)
                if "your_" in matched_str or "<" in matched_str or "example" in matched_str.lower():
                    continue
                violations.append((rule_name, line_idx, matched_str, line.strip()))

    return violations


def run_audit(target_dir: Path, verbose: bool = False) -> int:
    print("=" * 72)
    print("🛡️  联邦开源发布零泄漏合规扫描器 (Leak Checker) v1.0.0")
    print(f"📁 扫描目标目录: {target_dir.resolve()}")
    print("=" * 72)

    total_files = 0
    scanned_files = 0
    total_violations = 0
    results_by_rule: Dict[str, List[str]] = {r: [] for r in PATTERNS}

    ALLOWED_EXTS = {
        ".py", ".md", ".json", ".jsonl", ".js", ".html", ".css",
        ".txt", ".sh", ".cmd", ".bat", ".yml", ".yaml", ".env", ".example"
    }

    for root, dirs, files in os.walk(target_dir):
        dirs[:] = [d for d in dirs if d not in IGNORED_DIRS]

        for file in files:
            file_path = Path(root) / file
            total_files += 1

            if file_path.suffix.lower() not in ALLOWED_EXTS and not file.startswith(".env"):
                continue

            scanned_files += 1
            file_violations = scan_file(file_path, target_dir)

            if file_violations:
                rel = file_path.relative_to(target_dir)
                for rule_name, line_no, matched, line_content in file_violations:
                    total_violations += 1
                    preview = (line_content[:65] + '...') if len(line_content) > 65 else line_content
                    item_str = f"{rel}:{line_no} [{matched}] -> {preview}"
                    results_by_rule[rule_name].append(item_str)

    print(f"📊 扫描完成: 遍历文件 {total_files} 个，深度核查文件 {scanned_files} 个\n")

    for rule_name, items in results_by_rule.items():
        status_icon = "❌ 违规" if items else "✅ 安全"
        print(f"{status_icon} 【{rule_name}】: 发现 {len(items)} 处命中")
        if items:
            for item in items[:8]:
                print(f"   - {item}")
            if len(items) > 8:
                print(f"   ...以及其他 {len(items) - 8} 处")
            print()

    print("-" * 72)
    if total_violations == 0:
        print("🎉 恭喜！全仓合规核查通过，无物理密钥、无硬编码绝对路径、无本地凭证泄露！")
        print("门禁判定: PASS (Exit 0)")
        print("=" * 72)
        return 0
    else:
        print(f"⚠️ 阻断警告: 累计发现 {total_violations} 处敏感信息泄露！")
        print("门禁判定: REJECT (Exit 1) — 严禁提交至公共 Git 仓库，请立即脱敏！")
        print("=" * 72)
        return 1


def main():
    default_root = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(description="Federation Leak Checker")
    parser.add_argument(
        "--target",
        type=Path,
        default=default_root,
        help="Target directory to scan (default: repository root)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Verbose output"
    )
    args = parser.parse_args()

    exit_code = run_audit(args.target, args.verbose)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()