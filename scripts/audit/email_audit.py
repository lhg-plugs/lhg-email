#!/usr/bin/env python3
"""lhg-email 确定性邮件审计：12 条规则，零第三方依赖。

扫描目标目录的邮件稿件（.md / .html / .txt），输出 JSON 与人类可读报告；
有 blocker 时以 exit code 2 退出（供 hooks 与 CI 使用）。

用法：
    python3 email_audit.py --target <目录> [--format json|text] [--fail-on blocker|warning|nit]

规则全部原创（方法论见插件 skills/ 下的 lhg-email-segment/sequence/copy/deliver，
未复制任何第三方 skill/插件的原文案与代码）。
只做方法论与内容层检查，不碰发信基础设施。
"""

import argparse
import json
import os
import re
import sys

VERSION = "1.0.0"
TOOL = "lhg-email/email-audit"

SKIP_DIRS = {
    "node_modules", ".next", "dist", "build", ".git", "coverage",
    "__pycache__", "vendor", ".turbo", "out", "fixtures",
}
SCAN_EXTS = {".md", ".html", ".txt"}

SPAM_WORDS = [
    "免费领取", "一夜暴富", "点击赚钱", "恭喜中奖", "100%免费",
    "make money fast", "guaranteed income", "no risk",
    "act now!!!", "double your income",
]
SUBJECT_RE = re.compile(r"^\s*(subject|标题)\s*[:：]\s*(.*)$", re.I | re.M)
UNSUB_RE = re.compile(r"unsubscribe|退订|取消订阅", re.I)
FROM_RE = re.compile(r"^\s*(from|发件人)\s*[:：]", re.I | re.M)
ADDRESS_RE = re.compile(r"地址|\bstreet\b|\bSt\.?,|\bAve\b|\bRoad\b|路\d*\s*号", re.I)
PREVIEW_RE = re.compile(r"preview|预览文本", re.I)
LINK_RE = re.compile(r"https?://[^\s\"'<>）)]+")
EMOJI_RE = re.compile(r"[\U0001F300-\U0001FAFF\u2600-\u27BF\u2B00-\u2BFF\U0001F000-\U0001F2FF]")


class Finding:
    __slots__ = ("rule_id", "severity", "category", "title", "file", "line", "snippet", "detail")

    def __init__(self, rule_id, severity, category, title, file, line, snippet, detail):
        self.rule_id = rule_id
        self.severity = severity
        self.category = category
        self.title = title
        self.file = file
        self.line = line
        self.snippet = snippet
        self.detail = detail

    def to_dict(self):
        return {
            "rule_id": self.rule_id, "severity": self.severity,
            "category": self.category, "title": self.title,
            "file": self.file, "line": self.line,
            "snippet": self.snippet, "detail": self.detail,
        }


def collect_files(target):
    out = []
    for root, dirs, files in os.walk(target):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for f in files:
            _, ext = os.path.splitext(f)
            if ext in SCAN_EXTS:
                out.append(os.path.join(root, f))
    return sorted(out)


def read_text(path):
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            return fh.read()
    except OSError:
        return ""


def _hit(rule_id, path, lineno, snippet):
    rule = _RULE_BY_ID[rule_id]
    return Finding(rule["id"], rule["severity"], rule["category"], rule["title"],
                   path, lineno, snippet[:160], rule["detail"])


def _file_hit(rule_id, path):
    return _hit(rule_id, path, 1, os.path.basename(path))


RULES = []
_RULE_BY_ID = {}


def rule(rule_id, severity, category, title, detail):
    def deco(fn):
        r = {"id": rule_id, "severity": severity,
             "category": category, "title": title, "detail": detail}
        _RULE_BY_ID[rule_id] = r
        r["check"] = fn
        RULES.append(r)
        return fn
    return deco


def _subjects(text):
    """抽取所有 Subject:/标题： 行，返回 (行号, 标题文本)。"""
    out = []
    for m in SUBJECT_RE.finditer(text):
        lineno = text[:m.start()].count("\n") + 1
        out.append((lineno, m.group(2).strip()))
    return out


# ---------------- 合规 ----------------

@rule("EM-CMP-001", "blocker", "合规", "无退订链接",
      "营销邮件没有一键退订链接。CAN-SPAM / GDPR / 中国《互联网电子邮件服务管理办法》都要求，这是红线。")
def r_cmp_001(lines, text, path, ctx):
    if UNSUB_RE.search(text):
        return []
    return [_file_hit("EM-CMP-001", path)]


@rule("EM-CMP-002", "warning", "合规", "缺发件人物理地址",
      "英文营销邮件底部应有公司物理地址（CAN-SPAM 要求）。中文邮件建议也加上，增加信任。")
def r_cmp_002(lines, text, path, ctx):
    if ADDRESS_RE.search(text):
        return []
    return [_file_hit("EM-CMP-002", path)]


# ---------------- 垃圾词与标题 ----------------

@rule("EM-SPM-001", "warning", "垃圾词", "垃圾邮件触发词",
      "命中垃圾过滤器高频词。换说法：不说「免费领取」，说「新用户专享」。")
def r_spm_001(lines, text, path, ctx):
    out = []
    for i, ln in enumerate(lines):
        for w in SPAM_WORDS:
            if w in ln:
                out.append(_hit("EM-SPM-001", path, i + 1, "触发词：%s" % w))
                break
    return out


@rule("EM-SPM-002", "warning", "垃圾词", "标题全大写/感叹号过多",
      "标题全大写或 ≥3 个感叹号是垃圾过滤器的重点照顾对象。改成正常语气。")
def r_spm_002(lines, text, path, ctx):
    out = []
    for lineno, subj in _subjects(text):
        bangs = subj.count("!") + subj.count("！")
        letters = [c for c in subj if c.isalpha()]
        upper_ratio = (sum(1 for c in letters if c.isupper()) / len(letters)) if letters else 0
        if bangs >= 3 or (len(letters) >= 10 and upper_ratio >= 0.7):
            out.append(_hit("EM-SPM-002", path, lineno, subj))
    return out


@rule("EM-SPM-003", "warning", "垃圾词", "正文感叹号堆砌",
      "全文感叹号超过 5 个，读起来像在吼，也容易被过滤器盯上。留 1-2 个给最重要的 CTA。")
def r_spm_003(lines, text, path, ctx):
    n = text.count("!") + text.count("！")
    if n > 5:
        return [_hit("EM-SPM-003", path, 1, "全文感叹号 %d 个" % n)]
    return []


@rule("EM-TIT-001", "warning", "标题", "标题超长",
      "标题超过 60 字符，移动端显示不全，关键信息会被截断。英文 ≤50 字符/中文 ≤20 字。")
def r_tit_001(lines, text, path, ctx):
    out = []
    for lineno, subj in _subjects(text):
        if len(subj) > 60:
            out.append(_hit("EM-TIT-001", path, lineno, subj))
    return out


@rule("EM-TIT-002", "warning", "标题", "标题 emoji 过多",
      "标题里 emoji 超过 2 个，显得廉价且部分邮箱显示为方框。最多 1 个，别放开头。")
def r_tit_002(lines, text, path, ctx):
    out = []
    for lineno, subj in _subjects(text):
        if len(EMOJI_RE.findall(subj)) > 2:
            out.append(_hit("EM-TIT-002", path, lineno, subj))
    return out


# ---------------- 格式与追踪 ----------------

@rule("EM-FMT-001", "warning", "格式", "缺纯文本版本",
      "HTML 邮件没有同名的 .txt/.md 纯文本版。某些企业邮箱拒收纯 HTML 邮件。")
def r_fmt_001(lines, text, path, ctx):
    if not path.endswith(".html"):
        return []
    stems = ctx.get("stems", set())
    stem = os.path.splitext(os.path.basename(path))[0]
    if stem in stems:
        return []
    return [_file_hit("EM-FMT-001", path)]


@rule("EM-TRK-001", "warning", "追踪", "链接缺 UTM 追踪参数",
      "有链接没带 utm_ 参数，发了多少、点了多少全靠猜。统一加 utm_source/email。")
def r_trk_001(lines, text, path, ctx):
    links = LINK_RE.findall(text)
    # 图片资源不算营销链接，跳过
    links = [u for u in links if not re.search(r"\.(png|jpe?g|gif|webp|svg|css|js)(\?|$)", u, re.I)]
    if not links:
        return []
    bare = [u for u in links if "utm_" not in u]
    if bare:
        return [_hit("EM-TRK-001", path, 1, "无追踪参数链接：%s" % bare[0][:80])]
    return []


# ---------------- 送达 ----------------

@rule("EM-DLV-001", "warning", "送达", "缺发件人标识",
      "没写 From/发件人。收件人看不到是谁发的，信任度和打开率都受影响。")
def r_dlv_001(lines, text, path, ctx):
    if FROM_RE.search(text):
        return []
    return [_file_hit("EM-DLV-001", path)]


@rule("EM-DLV-002", "nit", "送达", "图片无 alt 文本",
      "图片被屏蔽时收件人只能看到空白。加 alt，至少让人知道图里是什么。")
def r_dlv_002(lines, text, path, ctx):
    out = []
    for i, ln in enumerate(lines):
        for m in re.finditer(r"<img\b[^>]*>", ln, re.I):
            if not re.search(r"\balt\s*=", m.group(0), re.I):
                out.append(_hit("EM-DLV-002", path, i + 1, ln.strip()))
    return out


@rule("EM-DLV-003", "nit", "送达", "无预览文本",
      "没写预览文本（Preview Text），浪费了一半标题栏。40~90 字符，把标题没说完的话放这里。")
def r_dlv_003(lines, text, path, ctx):
    if PREVIEW_RE.search(text):
        return []
    return [_file_hit("EM-DLV-003", path)]


def run(target):
    files = collect_files(target)
    # stems：有纯文本版（.txt/.md）的 html 文件名集合，供 EM-FMT-001 用
    stems = set()
    for p in files:
        _, ext = os.path.splitext(p)
        if ext in (".txt", ".md"):
            stems.add(os.path.splitext(os.path.basename(p))[0])
    ctx = {"files": files, "stems": stems}
    findings = []
    for path in files:
        text = read_text(path)
        lines = text.split("\n")
        rel = os.path.relpath(path, target)
        for r in RULES:
            try:
                findings.extend(r["check"](lines, text, rel, ctx))
            except Exception:
                pass
    return files, findings


def main(argv=None):
    ap = argparse.ArgumentParser(description="lhg-email 确定性邮件审计")
    ap.add_argument("--target", default=".", help="扫描目录")
    ap.add_argument("--format", choices=["json", "text"], default="text")
    ap.add_argument("--fail-on", choices=["blocker", "warning", "nit"], default="blocker")
    args = ap.parse_args(argv)

    target = os.path.abspath(args.target)
    if not os.path.isdir(target):
        print("target 不是目录：%s" % args.target, file=sys.stderr)
        return 1

    files, findings = run(target)

    sev_rank = {"blocker": 3, "warning": 2, "nit": 1}
    counts = {"blocker": 0, "warning": 0, "nit": 0}
    for f in findings:
        counts[f.severity] = counts.get(f.severity, 0) + 1

    result = {
        "tool": TOOL,
        "version": VERSION,
        "target": args.target,
        "summary": {
            "files_scanned": len(files),
            "rules_run": len(RULES),
            "blocker": counts["blocker"],
            "warning": counts["warning"],
            "nit": counts["nit"],
        },
        "findings": [f.to_dict() for f in sorted(
            findings, key=lambda x: (-sev_rank.get(x.severity, 0), x.file, x.line))],
    }

    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        s = result["summary"]
        print("邮件审计：扫描 %d 文件，运行 %d 条规则" % (s["files_scanned"], s["rules_run"]))
        print("blocker=%d warning=%d nit=%d" % (s["blocker"], s["warning"], s["nit"]))
        for f in result["findings"]:
            print("[%s][%s] %s:%d %s" % (
                f["severity"].upper(), f["rule_id"], f["file"], f["line"], f["title"]))
            print("    %s" % f["detail"])
            if f["snippet"]:
                print("    → %s" % f["snippet"])

    level = sev_rank[args.fail_on]
    bad = any(sev_rank.get(f.severity, 0) >= level for f in findings)
    return 2 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
