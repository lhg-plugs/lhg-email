---
description: 邮件营销一条龙：用户分层→序列规划→标题正文撰写→送达率 checklist，出海商家刚需。
argument-hint: ["产品/店铺一句话介绍"] [--lang zh|en]
---

# /lhg-email:email —— 邮件营销一条龙

用户输入在 `$ARGUMENTS` 中：`"<产品/店铺一句话介绍>" [--lang zh|en]`。默认英文（出海场景），`--lang zh` 出中文版。

## 流程（加载 lhg-email-segment → lhg-email-sequence → lhg-email-copy → lhg-email-deliver 全程指导）

### 1. 用户分层（lhg-email-segment）
先问清 3 件事：你现在有什么用户（新订阅/加购未买/已购买/沉睡）？每类大概多少人？用什么工具发信（Mailchimp/Klaviyo/自建）？
输出分层表：每类用户的特征 + 当前最该解决的问题（一类用户只解决一个问题）。

### 2. 序列规划（lhg-email-sequence）
按四类序列排优先级（小白默认顺序）：
1. **欢迎序列**（3 封）：第 1 天欢迎+给钩子 → 第 3 天讲品牌故事 → 第 7 天首单优惠
2. **培育序列**（持续）：每周 1 封，内容 80% / 促销 20%
3. **转化序列**（加购未买 3 封）：1 小时后提醒 → 24 小时后给评价背书 → 72 小时后小额优惠
4. **召回序列**（沉睡 3 封）：90 天未购 → "我们想你了" + 问卷 → 最后通牒优惠

### 3. 标题+正文撰写（lhg-email-copy）
每封邮件输出：标题（3 选 1 备选）+ 预览文本 + 正文 + CTA（一封邮件只放一个 CTA）。
写完先自查：标题党了吗？承诺能兑现吗？移动端 3 秒能看完吗？

### 4. 送达率 checklist（lhg-email-deliver）
跑确定性审计：
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/audit/email_audit.py --target <邮件稿目录> --format text
```
blocker（无退订链接）必须修；再按 lhg-email-deliver 过 SPF/DKIM/发信域名/垃圾词人工项。

## 交付物
- `emails/`：每封邮件一个文件（HTML + 纯文本版）
- `EMAIL_PLAN.md`：分层表 + 序列规划 + 发送节奏 + 送达率 checklist 结果

## 硬规则
- 只做方法论与内容层，**不碰发信基础设施**（不帮你配 SMTP 服务器、不导用户邮箱）。
- 无退订链接的邮件 → 不许定稿，这是合规红线。
- 标题党、虚假承诺 → 不许写，短期打开率换来的是长期进垃圾箱。
- 用户没说清分层就写稿 → 停下来先问，给错的人发对的邮件也是错的。
