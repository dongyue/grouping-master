#!/usr/bin/env python3
"""输出当前工作区相对 master 的全部差异，格式对 LLM 友好"""

import subprocess

OUTPUT = "diff.md"


def run(cmd):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True).stdout.strip()


# ---- 基本信息 ----
branch = run("git rev-parse --abbrev-ref HEAD")
commits = run("git log --oneline master..HEAD")
dirty = bool(run("git status --porcelain"))

lines = []
lines.append("# 相对 master 的变更\n")
lines.append(f"**分支**: `{branch}`")

if commits:
    lines.append(f"**提交**:  ")
    for c in commits.split("\n"):
        lines.append(f"  {c}")
lines.append("")

# ---- 所有已跟踪文件的差异（已提交 + 未暂存 + 暂存全合一） ----
diff_raw = run("git diff master")

# 从 diff 中提取涉及的文件列表
changed_files = set()
for line in run("git diff --name-only master").split("\n"):
    if line:
        changed_files.add(line)
# 也包括暂存区文件（--cached 对比 HEAD，但对比 master 更合适）
for line in run("git diff --name-only --cached master").split("\n"):
    if line:
        changed_files.add(line)

# 未跟踪文件（自动尊重 .gitignore）
untracked = run("git ls-files --others --exclude-standard")
untracked_files = [f for f in untracked.split("\n") if f]

# ---- 概述 ----
total = len(changed_files) + len(untracked_files)
lines.append(f"**变更文件**: {total} 个（已跟踪 {len(changed_files)}，未跟踪 {len(untracked_files)}）\n")

lines.append("---\n")

# ---- 逐个文件输出 ----
for path in sorted(changed_files):
    # 检查文件是否还存在（可能被删了）
    diff_text = run(f"git diff master -- '{path}'")
    if not diff_text:
        continue
    lines.append(f"### `{path}`\n")
    lines.append("```diff")
    lines.append(diff_text)
    lines.append("```\n")

for path in untracked_files:
    lines.append(f"### `{path}`（新文件，未跟踪）\n")
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        if content:
            content_lines = content.split("\n")
            if len(content_lines) > 300:
                content = "\n".join(content_lines[:80])
                lines.append(f"*(共 {len(content_lines)} 行，仅显示前 80 行)*")
            lang = "python" if path.endswith(".py") else ""
            lines.append(f"```{lang}")
            lines.append(content)
            lines.append("```")
    except Exception as e:
        lines.append(f"*(无法读取: {e})*")
    lines.append("")

# ---- 输出 ----
with open(OUTPUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))

print(f"✅ {OUTPUT} 已生成 — {total} 个变更文件")
