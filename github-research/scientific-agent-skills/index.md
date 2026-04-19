# scientific-agent-skills 技术调研报告

> 作者: @K-Dense-AI | 今日新增: ⭐+0 | 总计: ⭐18881

## 基本信息

| 项目 | 信息 |
|------|------|
| **仓库名** | scientific-agent-skills |
| **作者** | K-Dense-AI (K-Dense Inc.) |
| **编程语言** | Python |
| **Stars** | 18881 |
| **开源协议** | MIT License |
| **Agent 兼容** | Cursor, Claude Code, Codex, Gemini CLI 及任何支持 Agent Skills 标准的 AI Agent |
| **技能数量** | 133 个科学技能 |
| **数据库覆盖** | 78+ 个公共科学数据库 |
| **项目地址** | https://github.com/K-Dense-AI/scientific-agent-skills |

---

## 项目简介

**Scientific Agent Skills**（前身为 Claude Scientific Skills）是一个综合性的 **AI Agent 科学技能库**，包含 **133 个可直接使用的科学研究技能**。项目覆盖癌症基因组学、药物靶点结合、分子动力学、RNA velocity、地理空间科学、时间序列预测等众多科学领域，以及 **78+ 个公共科学数据库**的访问能力。

该项目遵循开放的 [Agent Skills](https://agentskills.io/) 标准，使其能够与任何兼容该标准的 AI Agent协同工作，包括 Cursor、Claude Code、Codex、Gemini CLI 等。项目同时配套推出 **K-Dense BYOK**——一款免费的桌面端 AI 共同科学家应用，基于 Scientific Agent Skills 构建，支持自带 API keys、40+ 模型选择、本地运行，可选扩展至云端 Modal 计算。

### 核心定位

```
AI Agent + 科学技能 = AI 科学家
```

通过将专业科学工具以技能（Skills）形式封装，使 AI Agent 能够执行复杂的多步骤科学研究工作流。

---

## 技术栈分析

### 主要技术栈

| 类别 | 技术 | 说明 |
|------|------|------|
| **运行环境** | Python 3.11+ (推荐 3.12+) | 核心开发语言 |
| **包管理** | uv | 必需的 Python 包管理器 |
| **Agent 标准** | Agent Skills (agentskills.io) | 开放的技能规范标准 |
| **安装方式** | npx / gh skill | 跨平台标准化安装 |

### 技能分类技术矩阵

| 技能类别 | 代表性技能 | 底层依赖 |
|----------|------------|----------|
| **生物信息学** | BioPython, Scanpy, pysam, scVelo, PyDESeq2 | BioPython, NumPy, Pandas |
| **化学信息学** | RDKit, Datamol, DeepChem, DiffDock | RDKit, PyTorch |
| **机器学习** | PyTorch Lightning, scikit-learn, TimesFM, PyMC | PyTorch, scikit-learn |
| **量子计算** | PennyLane, Qiskit, Cirq, QuTiP | NumPy, JAX |
| **分子动力学** | OpenMM, MDAnalysis | NumPy, MDAnalysis |
| **数据库访问** | Database Lookup (78+ 数据库) | Requests, BioServices |
| **科学可视化** | Matplotlib, Seaborn, NetworkX | Matplotlib, NumPy |
| **科学通信** | Literature Review, Scientific Writing | ArXiv API, PubMed API |

---

## 代码结构

### 目录结构

```
scientific-agent-skills/
├── .github/                    # GitHub 工作流配置
├── .gitignore
├── LICENSE.md                 # MIT 协议
├── README.md                  # 42KB 详细文档
├── SECURITY.md               # 478KB 安全扫描报告
├── docs/                      # 文档目录
│   ├── examples.md            # 工作流示例
│   ├── scientific-skills.md  # 完整技能清单
│   └── open-source-sponsors.md
├── pyproject.toml            # 项目配置
├── scan_pr_skills.py         # PR 技能扫描脚本
├── scan_skills.py            # 技能扫描脚本
├── scientific-skills/         # 核心技能目录（133 个技能）
└── uv.lock                   # 依赖锁定文件
```

### 技能组织方式

每个技能包含：
- `SKILL.md` — 技能定义文档（含 frontmatter 元数据）
- `references/` — 参考资料目录
- 代码示例和使用最佳实践

---

## 依赖分析

### 核心依赖

| 依赖类型 | 代表性包 | 数量级 |
|----------|----------|--------|
| **科学计算** | NumPy, SciPy, Pandas | ~10 个 |
| **机器学习** | PyTorch, scikit-learn, Transformers | ~15 个 |
| **生物信息学** | BioPython, Scanpy, RDKit | ~20 个 |
| **API 集成** | Requests, aiohttp | ~5 个 |
| **数据验证** | Pydantic | 1 个 |
| **环境管理** | python-dotenv | 1 个 |

### 依赖管理特点

- 使用 `uv` 作为统一包管理器
- `pyproject.toml` 定义项目元数据和依赖
- `uv.lock` 锁定所有传递依赖版本
- 技能级依赖隔离（按需安装，而非全量安装）

---

## 可运行性评估

### 安装方式

```bash
# 方式一：npx（所有平台通用）
npx skills add K-Dense-AI/scientific-agent-skills

# 方式二：gh CLI（v2.90.0+）
gh skill install K-Dense-AI/scientific-agent-skills
```

### 前置要求

| 要求 | 版本 | 说明 |
|------|------|------|
| Python | 3.11+ (推荐 3.12+) | 运行时 |
| uv | 最新版 | 包管理器 |
| Agent 客户端 | 兼容 Agent Skills 标准 | 如 Claude Code, Cursor 等 |

### 验证安装

```bash
uv --version  # 验证 uv 安装
```

---

## 技术亮点

### 1. 开放的 Agent Skills 标准

项目不绑定特定 AI Agent，遵循 `agentskills.io` 开放标准，实现**一次编写，多端运行**。当前已验证兼容：
- Cursor
- Claude Code / Claude Cowork
- Codex
- Gemini CLI
- 任何支持该标准的未来 Agent

### 2. 海量科学数据库覆盖

通过统一的 `database-lookup` 技能，提供对 **78+ 公共数据库**的 REST API 访问：

| 数据库类型 | 代表性数据库 |
|------------|--------------|
| 化学 | PubChem, ChEMBL, ZINC |
| 基因组 | UniProt, Ensembl, NCBI Gene |
| 蛋白质结构 | PDB, AlphaFold |
| 通路 | KEGG, Reactome, STRING |
| 临床 | ClinVar, COSMIC, ClinicalTrials.gov |
| 专利 | USPTO |
| 金融 | U.S. Treasury Fiscal Data, FRED |

### 3. 端到端科学研究工作流示例

项目提供详细的药物发现、单细胞分析、多组学 biomarker 发现等**完整工作流示例**：

```
药物发现流程示例：
ChEMBL (EGFR 抑制剂查询) → RDKit (SAR 分析) → datamol (类似物生成)
→ DiffDock (虚拟筛选) → AlphaFold DB (结构验证) → PubMed (耐药机制调研)
→ COSMIC (突变查询) → 可视化报告
```

### 4. 安全的社区贡献机制

- 所有技能通过 [Cisco AI Defense Skill Scanner](https://github.com/cisco-ai-defense/skill-scanner) 安全扫描
- `SECURITY.md` 记录每周安全扫描结果（文件大小达 478KB）
- 明确的安全免责声明和安装建议

### 5. 商业化产品支撑

项目背后有商业产品 **K-Dense Web** 和 **K-Dense BYOK** 支撑，确保开源项目的长期维护性和社区支持。

---

## 潜在问题

### 1. 技能质量参差不齐风险

> ⚠️ 官方提示：项目现在包含大量社区贡献，K-Dense 团队无法保证每个技能都经过haustive review。

**缓解措施**：
- 仅安装实际需要的技能，而非全量安装
- 安装前阅读 `SKILL.md` 了解技能行为
- 优先使用 K-Dense 团队维护的技能（可通过 git 提交历史判断）

### 2. API 稳定性风险

部分技能依赖外部 API（PubChem, ChEMBL, AlphaFold 等），这些 API 可能：
- 实施速率限制
- 变更接口或认证方式
- 遭遇服务中断

**建议**：实现本地缓存和优雅降级策略。

### 3. 安全攻击面

Agent Skills 可以执行任意代码、安装包、发起网络请求。恶意技能可能：
- 窃取 API credentials
- 植入后门
- 破坏本地文件

**建议**：在隔离环境（如 Docker）中使用未知来源的技能。

### 4. Python 依赖地狱

133 个技能涉及大量 Python 包，科学计算库的版本兼容性是一大挑战。`uv.lock` 一定程度上缓解了此问题。

---

## 总结与建议

### 综合评分

| 评估维度 | 评分 | 说明 |
|----------|------|------|
| **技术栈合理性** | ⭐⭐⭐⭐⭐ 9/10 | 遵循开放标准，Python 生态完美契合 |
| **代码质量** | ⭐⭐⭐⭐ 8/10 | 结构清晰，每个技能独立封装 |
| **文档完善度** | ⭐⭐⭐⭐⭐ 10/10 | README 达 42KB，示例详尽 |
| **社区活跃度** | ⭐⭐⭐⭐ 8/10 | 18.8k Stars，持续更新 |
| **安全合规** | ⭐⭐⭐⭐ 7/10 | 有扫描机制，但依赖社区贡献质量 |
| **综合评分** | **8.4/10** | 强烈推荐关注 |

### 适用场景

| 场景 | 推荐度 | 说明 |
|------|--------|------|
| AI 辅助科学研究 | ⭐⭐⭐⭐⭐ | 核心场景，覆盖全面 |
| 药物发现工作流 | ⭐⭐⭐⭐⭐ | RDKit, DiffDock, ChEMBL 无缝衔接 |
| 单细胞 RNA-seq 分析 | ⭐⭐⭐⭐⭐ | Scanpy, Cellxgene, PyDESeq2 全套 |
| 生物信息学教学 | ⭐⭐⭐⭐ | 示例丰富，适合学习 |
| 企业级科学计算 | ⭐⭐⭐ | 需评估社区技能安全风险 |

### 推荐行动

1. **立即尝试**：在本地 Claude Code 或 Cursor 中安装一个感兴趣的技能（如 RDKit 或 Scanpy），体验 AI 辅助科学计算的便利
2. **工作流集成**：将项目作为 AI 科学家助手，整合到现有科研流程
3. **社区贡献**：如发现缺失技能，可参照 CONTRIBUTING.md 规范提交 PR
4. **安全优先**：生产环境使用时，仅安装经过验证的技能子集

---

## 参考链接

- [GitHub 仓库](https://github.com/K-Dense-AI/scientific-agent-skills)
- [Agent Skills 标准](https://agentskills.io/)
- [K-Dense BYOK（桌面应用）](https://github.com/K-Dense-AI/k-dense-byok)
- [K-Dense Web（云平台）](https://k-dense.ai)
- [Cisco AI Defense Skill Scanner](https://github.com/cisco-ai-defense/skill-scanner)
