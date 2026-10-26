<!-- About 简介（推送后填写到仓库 About 栏）：
邮件营销专家：用户分层→序列规划→标题正文→送达率 checklist ｜ 一键安装：/plugin marketplace add lhg-plugs/lhg-email
-->
<!-- topics（推送后打）：claude-code, claude-plugin, agent-skills, email-marketing, newsletter -->

# lhg-email：邮件营销专家

> **一句话介绍**：给 AI 编程助手装上"邮件营销一条龙"——用户分层→欢迎/培育/转化/召回序列规划→标题+正文撰写→12 条确定性规则送达率诊断，出海商家做邮件营销不踩合规坑。
>
> **一键安装**：在 Claude Code 里运行
> ```
> /plugin marketplace add lhg-plugs/lhg-email
> /plugin install lhg-email@lhg-plugs
> ```

## 它是什么

`lhg-email` 是一个 Claude Code 插件（plugin 为主、skill 为辅）：

- **4 个命令**（小白入口）：`email` 营销一条龙，`subject` 标题优化，`sequence` 序列规划，`deliver` 送达率诊断
- **4 个平台中立 skill**（方法论，可移植到豆包/Workbuddy 等 agent 平台）：用户分层、序列规划、标题正文撰写、送达率 checklist
- **2 个专家 agent**：邮件文案、送达率审计
- **2 个硬门 hooks**：commit 前合规拦截（无退订链接）、写邮件稿件的垃圾词/退订提醒（均可一键豁免）
- **12 条确定性邮件审计规则**：纯 Python、零第三方依赖，5 秒出结果

**边界**：本插件只做方法论与内容层，**不碰发信基础设施**（不配 SMTP、不导用户邮箱、不代配 DNS）。

## 4 个命令用法

| 命令 | 作用 | 示例 |
|---|---|---|
| `/lhg-email:email` | 用户分层→序列规划→标题正文→送达率 checklist，一条龙 | `/lhg-email:email "宠物用品独立站" --lang en` |
| `/lhg-email:subject` | 标题优化：3 套公式备选 + 长度/emoji/垃圾词硬检 | `/lhg-email:subject "首单优惠邮件"` |
| `/lhg-email:sequence` | 欢迎/培育/转化/召回四类序列一次定稿 | `/lhg-email:sequence "电商"` |
| `/lhg-email:deliver` | 送达率诊断（脚本 + SPF/DKIM/合规人工项） | `/lhg-email:deliver ./emails` |

## 自查说明

自查 = 确定性脚本（机器）+ 人工复核清单（人）：

1. 先跑 `scripts/audit/email_audit.py`（12 条规则：无退订链接、垃圾触发词、标题超长/emoji 滥用、无纯文本版、链接无追踪参数等），零 LLM 成本；
2. 发现分三级：**blocker**（无退订链接，commit 前 hook 会拦截）、**warning**（修或写豁免理由）、**nit**（顺手修）；
3. 再按 `lhg-email-deliver` skill 过人工项（SPF/DKIM/DMARC、发信子域名、预热状态、退订实测）。

blocker 清零才算能发；为清零改规则算作弊，不许。

## 目录结构

```
lhg-email/
├── .claude-plugin/          # plugin.json（插件清单）+ marketplace.json（本仓即市场）
├── commands/                # 4 个命令：email / subject / sequence / deliver
├── skills/                  # 4 个平台中立 skill（lhg-email-segment/sequence/copy/deliver）
├── agents/                  # 2 个专家 agent（copy-writer / deliver-auditor）
├── hooks/                   # 2 个硬门（commit 前合规拦截 / 垃圾词提醒）+ 豁免说明
├── scripts/audit/           # 12 条确定性邮件审计规则（零第三方依赖）
├── fixtures/                # 冒烟测试用例（坏/好对照）
├── smoke_test.py            # 一键冒烟测试
├── ATTRIBUTION.md           # 灵感来源与许可声明
└── LICENSE                  # MIT
```

## 什么时候用 / 什么时候不用（FAQ）

**什么时候用：**

- 你是出海商家（独立站/SaaS），想做邮件营销但不知道从哪下手时 → 用 `/lhg-email:email`
- 邮件打开率一直上不去，怀疑标题有问题时 → 用 `/lhg-email:subject`
- 想搭一套自动化的欢迎/加购挽回/沉睡召回序列时 → 用 `/lhg-email:sequence`
- 邮件发出后老进垃圾箱，想系统排查时 → 跑 `/lhg-email:deliver`
- 邮件稿写完，怕有合规问题（退订链接、垃圾词）时 → 审计脚本 5 秒扫一遍

**什么时候不用：**

- 你需要的是发信基础设施（搭 SMTP 服务器、配 DNS、做 IP 预热）→ 本插件不碰这些，找你的发信服务商
- 你只想群发一次通知（如系统维护公告）→ 不需要分层和序列，直接写就行
- 你的用户列表是买来的 → 先删掉名单，买名单群发是垃圾邮件，法律风险自负
- 你只做国内短信/微信营销 → 方法论部分可借鉴，但合规与送达规则是按邮件写的

## lhg-plugs 插件矩阵

| 插件 | 一句话 | 安装 |
|---|---|---|
| [lhg-email](https://github.com/lhg-plugs/lhg-email) | 邮件营销专家：分层→序列→标题正文→送达率诊断一条龙 | `/plugin install lhg-email@lhg-plugs` |
| *（后续插件在此追加，保持表格格式一致）* | | |

## 自检与反馈

- 每次用完任一 skill，按其「自检与反馈」节做轻量自检。
- 标准冒烟用例：`python3 smoke_test.py`（仓库根目录），全绿才算过。
- 反馈渠道：以 `[QC] <一句话问题>` 为标题提交到 https://github.com/lhg-plugs/lhg-email/issues，正文写清「输入 → 错误输出 → 期望输出」。规则误报/漏报请附最小复现代码。

## 出品

**出品：刘洪光**（安徽合肥），归属 [lhg-skills](https://github.com/lhg-skills)。

- GitHub 主页：https://github.com/lhg-skills —— 全部 skill 开源在此，欢迎 star
- 抖音：搜「刘老师讲AI实战」
- 微信：lhgsmsw
