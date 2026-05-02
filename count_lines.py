#!/usr/bin/env python3
"""统计项目代码行数，遵守 .gitignore，排除 .md 文件。"""
import subprocess
import sys
from collections import defaultdict
from datetime import datetime

try:
    result = subprocess.run(
        ["git", "ls-files", "-z"],
        capture_output=True, text=True, check=True
    )
except subprocess.CalledProcessError as e:
    print(f"错误：无法执行 git ls-files: {e}", file=sys.stderr)
    sys.exit(1)

CODE_EXTS = {".py", ".vue", ".js"}

files = [
    f for f in result.stdout.split("\0")
    if f and any(f.endswith(ext) for ext in CODE_EXTS)
]

if not files:
    print("没有找到需要统计的源代码文件。")
    sys.exit(0)

stats = defaultdict(int)
total = 0

for f in files:
    try:
        with open(f, encoding="utf-8", errors="ignore") as fh:
            lines = sum(1 for _ in fh)
            ext = f.rsplit(".", 1)[-1] if "." in f else "other"
            stats[ext] += lines
            total += lines
    except (OSError, UnicodeDecodeError):
        pass

print(f"文件数：{len(files)}")
print(f"总行数：{total}")
print(f"统计时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()
print(f"{'类型':<12} {'行数':>8} {'占比':>8}")
print("-" * 30)
for ext in sorted(stats, key=stats.get, reverse=True):
    cnt = stats[ext]
    pct = f"{cnt / total * 100:.1f}%" if total else "0%"
    print(f".{ext:<11} {cnt:>8} {pct:>8}")
