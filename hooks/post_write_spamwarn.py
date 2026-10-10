#!/usr/bin/env python3
"""lhg-email 硬门②（警告级，不拦截）：写邮件稿件时，
检测到垃圾邮件触发词或缺退订链接时提醒。

触发：PostToolUse / Write|Edit。只做提醒，永远 exit 0、不拦截写入。

逃生方式：LHG_EMAIL_HOOKS_OFF=1（环境变量）可关闭本提醒；
或 /plugin disable lhg-email 停用整个插件。
零第三方依赖。
"""

import json
import os
import re
import sys

SPAM_WORDS = [
    "免费领取", "一夜暴富", "点击赚钱", "恭喜中奖", "100%免费",
    "make money fast", "guaranteed income", "no risk",
    "act now!!!", "double your income",
]
UNSUB_RE = re.compile(r"unsubscribe|退订|取消订阅", re.I)
MAIL_EXTS = {".md", ".html", ".txt"}
SKIP_DIR_PARTS = {"node_modules", "dist", "build", ".git", "__pycache__", "fixtures"}


def main() -> int:
    if os.environ.get("LHG_EMAIL_HOOKS_OFF") == "1":
        return 0

    try:
        raw = sys.stdin.read()
        payload = json.loads(raw) if raw.strip() else {}
    except Exception:
        return 0

    tool_input = payload.get("tool_input", {}) or {}
    file_path = tool_input.get("file_path", "") or ""
    if not file_path:
        return 0

    _, ext = os.path.splitext(file_path)
    if ext not in MAIL_EXTS:
        return 0
    parts = file_path.replace("\\", "/").split("/")
    if any(p in SKIP_DIR_PARTS for p in parts):
        return 0
    if not os.path.isfile(file_path):
        return 0

    try:
        with open(file_path, encoding="utf-8", errors="replace") as fh:
            text = fh.read()
    except OSError:
        return 0

    # 只看疑似邮件稿件：含 subject/标题/退订/邮件营销字样才提醒，避免骚扰
    if not re.search(r"subject|标题|退订|unsubscribe|邮件", text, re.I):
        return 0

    notes = []
    hits = [w for w in SPAM_WORDS if w in text]
    if hits:
        notes.append("检测到垃圾邮件触发词（%s）：容易被过滤器拦截，建议换说法（审计规则 EM-SPM-001）。"
                     % "、".join(hits[:3]))
    if not UNSUB_RE.search(text):
        notes.append("没找到退订链接：每封营销邮件底部必须有一键退订，这是合规红线（审计规则 EM-CMP-001）。")

    if not notes:
        return 0

    msg = ("邮件合规提醒（lhg-email）：%s\n%s\n"
           "关闭本提醒：export LHG_EMAIL_HOOKS_OFF=1（当前会话有效）。"
           ) % (file_path, "\n".join("- " + n for n in notes))
    out = {
        "hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "additionalContext": msg,
        }
    }
    sys.stdout.write(json.dumps(out, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
