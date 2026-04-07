---
title: 2026-04-01~03 GitHub Trending Cross-Date Analysis
description: GitHub 每日飙升榜跨日分析 · 2026-04-01 ~ 2026-04-03
---

# 2026-04-01~03 GitHub Trending Cross-Date Analysis

> 数据来源: [OpenGithubs/github-daily-rank](https://github.com/OpenGithubs/github-daily-rank)
> 分析范围: 2026-04-01 · 2026-04-02 · 2026-04-03

---

## 1. Sustained Performers — Multi-Day Repos (2+ Days)

以下项目在 3 天内多次上榜，按总 Stars 增量排序：

| 项目 | 04-01 | 04-02 | 04-03 | 3日总增量 |
|------|-------|-------|-------|-----------|
| [luongnv89/claude-howto](https://github.com/luongnv89/claude-howto) | +2,791 | +1,606 | +705 | **+5,102** |
| [Yeachan-Heo/oh-my-claudecode](https://github.com/Yeachan-Heo/oh-my-claudecode) | +1,928 | +1,417 | +1,013 | **+4,358** |
| [shareAI-lab/learn-claude-code](https://github.com/shareAI-lab/learn-claude-code) | +1,328 | +827 | +658 | **+2,813** |
| [msitarzewski/agency-agents](https://github.com/msitarzewski/agency-agents) | +752 | +781 | +861 | **+2,394** |
| [sherlock-project/sherlock](https://github.com/sherlock-project/sherlock) | +927 | — | +1,310 | **+2,237** |
| [microsoft/VibeVoice](https://github.com/microsoft/VibeVoice) | +1,393 | +867 | — | **+2,260** |
| [NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent) | +1,346 | +1,147 | +1,076 | **+3,569** |
| [onyx-dot-app/onyx](https://github.com/onyx-dot-app/onyx) | — | +1,169 | +1,498 | **+2,667** |
| [google-research/timesfm](https://github.com/google-research/timesfm) | — | +1,383 | +731 | **+2,114** |
| [farion1231/cc-switch](https://github.com/farion1231/cc-switch) | +705 | +768 | — | **+1,473** |

> 注: "—" 表示当日未进入 Top 10 榜单

---

## 2. Velocity Leaders — Star Velocity Ratio Top 5

Velocity Ratio = 今日新增 Stars / 总 Stars (衡量相对增长速度)

| 排名 | 日期 | 项目 | 今日新增 | 总 Stars | Velocity Ratio |
|------|------|------|----------|----------|----------------|
| 1 | 04-03 | Yeachan-Heo/oh-my-codex | +2,477 | 13.8k | **17.9%** |
| 2 | 04-01 | luongnv89/claude-howto | +2,791 | 15.3k | **18.2%** |
| 3 | 04-03 | onyx-dot-app/onyx | +1,498 | 23.1k | **6.5%** |
| 4 | 04-01 | shanraisshan/claude-code-best-practice | +2,097 | 30.3k | **6.9%** |
| 5 | 04-02 | luongnv89/claude-howto | +1,606 | 16.9k | **9.5%** |

**观察**: claude-howto 和 oh-my-codex 以远超均值的 velocity ratio 领跑，说明新项目的早期爆发力极强。

---

## 3. Category Breakdown

| Category | 代表项目 | 3日总 Stars 增量 |
|----------|---------|-----------------|
| **Learning / Education** | claude-howto, learn-claude-code, claude-code-best-practice | ~10,000+ |
| **Claude-Specific Wrappers** | oh-my-claudecode, oh-my-codex, VibeVoice | ~8,500+ |
| **Agent / Framework** | hermes-agent, agency-agents, deer-flow | ~6,000+ |
| **Research / ML** | timesfm, onyx, codex | ~6,500+ |
| **Utilities / Tools** | sherlock, cc-switch, openscreen | ~5,000+ |

---

## 4. Key Ecosystem Insights

- **"oh-my-" Claude 生态爆发**: oh-my-claudecode、oh-my-codex、oh-my-claudecode 三者同时上榜，形成 "oh-my-" 包装库热潮，反映开发者对 Claude 模型最佳实践集合的强烈需求。

- **学习类项目主导流量**: claude-howto、learn-claude-code、claude-code-best-practice 在 04-01 当天全部进入 Top 10，3 日总增量均超过 2,000+，表明 Claude Code 工具链学习资源严重供不应求。

- **Agent 框架持续蓄力**: hermes-agent 和 agency-agents 均保持 3 日连续上榜，说明 Agentic AI 开发框架仍是热点方向，且具有可持续的用户关注度。

- **sherlock 意外长尾**: OSINT 工具 sherlock 在 04-01 和 04-03 分别获得 927 和 1,310 stars，velocity ratio 稳定保持在 1.2%-2.0%，推测由社交媒体话题驱动。

- **04-03 新晋项目病毒式传播**: oh-my-codex (+2,477) 和 openscreen (+2,355) 在 04-03 当天 debuted 即以极高增量冲榜，体现出 AI 包装项目在社交媒体中的快速传播特征。

---

## 5. Data Quality Notes

| 问题 | 说明 |
|------|------|
| **04-02 独立报告缺失** | 仅存在 index.md，缺少各 repo 独立 .md 分析文件（疑似采集超时或解析失败） |
| **04-03 独立报告缺失** | 同上，仅有 index.md，无独立 repo 数据文件 |
| **04-01 数据完整** | 10 个项目均有独立分析文件，数据完整 |
| **跨日 Repo 追踪问题** | oh-my-codex、openscreen 等 04-03 新晋项目在 04-01/04-02 无记录，无法计算完整 velocity 变化曲线 |

> 建议: 检查 04-02 和 04-03 的采集流程，排除超时或 API 限流问题，确保跨日数据完整性。

---

*数据来源: [github-daily-rank](https://github.com/OpenGithubs/github-daily-rank) · 分析完成于 2026-04-07*
