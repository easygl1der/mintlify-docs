---
title: Prismer 学术研究助手
description: PrincetonSIGMA/Prismer 深度架构分析 - AI 驱动的学术研究平台
---

# Prismer 学术研究助手

> **GitHub**: https://github.com/PrincetonSIGMA/Prismer | 开源 Apache-2.0
> **来源**: 4 Agent 并行深度分析 (Frontend / Backend & API / LaTeX & Docker / Collaboration & AI)

## 核心定位

**Prismer** 是 PrincetonSIGMA 开发的**学术研究助手**，通过 AI Agent 编排 LaTeX 编译、Jupyter 执行、PDF 阅读等工具，为研究人员提供智能化的学术写作与代码执行环境。

### 核心差异化

| 特性 | 说明 |
|------|------|
| **Directive 协议** | Agent → Frontend 双向通信，AI 可直接操作 UI |
| **26 个 Workspace 工具** | 覆盖 LaTeX、Jupyter、PDF、数据分析全流程 |
| **6 个 Agent 模板** | mathematician, data-scientist, paper-reviewer 等 |
| **形式化验证** | 原生支持 Lean 4、Coq、Z3 |
| **Docker 服务栈** | 隔离的 LaTeX/Jupyter/Prover/arXiv 环境 |

## 技术架构总览

```
┌──────────────────────────────────────────────────────────────────┐
│                        Frontend (Next.js 16)                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │  LaTeX Editor │  │ Jupyter Cell  │  │  PDF Viewer / Notes   │  │
│  └──────┬───────┘  └──────┬───────┘  └──────────┬───────────┘  │
│         └───────────────────┼────────────────────┘                │
│                             ▼                                      │
│                      DirectiveQueue (EventEmitter)                 │
│                       SyncMatrixEngine                            │
└─────────────────────────────┼────────────────────────────────────┘
                              │ SSE + WebSocket
┌─────────────────────────────▼────────────────────────────────────┐
│                    Bridge API Layer                                │
│              /api/v2/im/bridge/[workspaceId]                       │
└─────────────────────────────┬────────────────────────────────────┘
                              │ WebSocket
┌─────────────────────────────▼────────────────────────────────────┐
│               Container Gateway (:16888)                           │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐    │
│  │  LaTeX     │ │  Jupyter   │ │  Prover    │ │   arXiv    │    │
│  │  :8080     │ │  :8888     │ │  :8081     │ │   :8082    │    │
│  └────────────┘ └────────────┘ └────────────┘ └────────────┘    │
└──────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────▼────────────────────────────────────┐
│                    OpenClaw Agent                                  │
│         (Kimi K2.5 / Claude Sonnet 4 providers)                  │
│  ┌─────────────────┐  ┌────────────────────────────────┐         │
│  │   prismer-im    │  │      prismer-workspace          │         │
│  │   (v0.2.0)     │  │        (v0.5.0)                 │         │
│  │                 │  │  26 工具: LaTeX/Jupyter/PDF/Data│         │
│  └─────────────────┘  └────────────────────────────────┘         │
└──────────────────────────────────────────────────────────────────┘
```

## 核心数据

| 指标 | 数值 |
|------|------|
| **Prisma 模型数** | 37 |
| **数据域数** | 7 |
| **Workspace 工具** | 26 |
| **Sync 规则数** | 11 |
| **Agent 模板** | 6 |
| **Docker 服务** | 5 |

## 分析报告索引

### 架构深度分析

| 页面 | 内容 | 覆盖范围 |
|------|------|----------|
| [整体架构](./Prismer-整体架构.md) | 系统架构总览、组件关系、数据流 | 100% |
| [前端架构](./Prismer-前端架构.md) | Next.js 16 + React 19 + Zustand 5 | 100% |
| [后端架构](./Prismer-后端架构.md) | Prisma + SQLite/MySQL + WebSocket | 100% |
| [LaTeX 编译](./Prismer-LaTeX编译.md) | Docker 服务栈、3 种引擎、模板库 | 100% |
| [Agent 编排](./Prismer-Agent编排.md) | OpenClaw 插件系统、6 个模板 | 100% |
| [协作功能](./Prismer-协作功能.md) | vs. Overleaf 功能对比 | 100% |
| [AI 功能](./Prismer-AI功能.md) | 26 个工具完整详解 | 100% |

---

## 关键发现

### 优势

1. **Directive 协议创新**: Agent 可直接操作 Frontend UI，无需用户手动切换
2. **完整 LaTeX 生态**: 3 种引擎、模板库、PDF 预览、形式化验证
3. **多 Provider 支持**: Kimi K2.5 + Claude Sonnet 4 可切换
4. **26 工具覆盖全流程**: 从论文阅读到代码执行到文档生成

### 局限

1. **无实时协作**: 缺少光标共享、内联评论、变更追踪
2. **单用户编辑**: 仅支持单用户 + AI 协作
3. **版本控制不足**: workspace snapshots 仅用于回放，非文档版本

### 与 Overleaf 对比

| 维度 | Overleaf | Prismer |
|------|----------|---------|
| 实时协作 | ✅ 完整 | ❌ 无 |
| AI 辅助 | ⚠️ 有限 | ✅ 深度集成 |
| Jupyter | ❌ | ✅ 原生 |
| 形式化验证 | ❌ | ✅ Lean/Coq/Z3 |
| 代码执行 | ❌ | ✅ 26 工具 |

---

## 技术栈总结

| 层级 | 技术 |
|------|------|
| **Frontend** | Next.js 16, React 19, TypeScript, Tailwind 4, Zustand 5, shadcn/ui |
| **Backend** | Prisma, SQLite/MySQL, Next.js API Routes, Server-Sent Events |
| **实时通信** | WebSocket (ws), EventEmitter |
| **Agent 运行时** | OpenClaw |
| **Docker 服务** | LaTeX (pdflatex/xelatex/lualatex), Jupyter, Lean 4/Coq/Z3, arXiv |
| **AI Providers** | Kimi K2.5, Claude Sonnet 4 |
