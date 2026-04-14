## Formatting & Error Handling Rules

▎ 为确保 MDX 文件在 Mintlify 项目中能够正确解析，请遵循以下底层逻辑与顶层设计规范：

- **标签安全**：任何出现 `<` 开头的内容（如版本号 `<2.0.0`）必须使用反引号包裹为行内代码 `` `<2.0.0` ``，防止被解析为 JSX 标签。
- **换行标签**：所有 `<br>` 必须写成自闭合形式 `<br/>`，如需双换行请使用 `<br/><br/>`。禁止使用 `<br >` 或带有冗余空格的标签。
- **表格闭合**：MDX 表格的每行必须以 `|` 开始并以 `|` 结束，列数保持一致。
- **Frontmatter**：
  - 必须包含 `title` 和 `description`。
  - 仅使用 YAML 块标记 `---` 包裹。
  - 禁止使用 `icon` 字段（除非有特殊需求且已在 docs.json 配置中拉通）。
  - 冒号后必须紧跟空格。如果描述中包含冒号，必须用双引号包裹整个描述字符串。
- **代码块**：使用三重反引号包裹，明确语言标记，如 `````md` 或 `````tsx`。
- **路径引用**：在 MDX 中链接其他页面时，使用绝对路径（从根目录开始，带 `/`），且不带文件扩展名，如 `[标题](/concepts/overview)`。
- **组件使用**：仅使用 Mintlify 官方组件（Card、Callout、Tabs、Tip、Note、Warning 等），禁止自定义未注册组件。

> 通过上述抓手可以实现解析闭环，确保文档在 CI 中通过 MDX 校验。


## Project Context

This repository contains Mintlify documentation — the same documentation published at https://www.mintlify.com/docs. When working on any documentation page, always use the live Mintlify docs as the **primary reference** for structure, formatting, and best practices.

## Using Mintlify Docs as Reference

When building or updating any Mintlify documentation page, consult these official organize-section pages **before** writing any content:

| Topic | Reference URL |
|-------|--------------|
| Navigation structure & ordering | https://www.mintlify.com/docs/organize/navigation |
| Global & page-level settings | https://www.mintlify.com/docs/organize/settings |
| Page types, MDX components, syntax | https://www.mintlify.com/docs/organize/pages |
| Hidden pages & draft content | https://www.mintlify.com/docs/organize/hidden-pages |
| Excluding files from deploy (`mintignore`) | https://www.mintlify.com/docs/organize/mintignore |

### How to Read These Pages Effectively

1. **Navigation** — Understand how pages are ordered and grouped. The `mint.json` navigation config controls this; follow the same hierarchy patterns already established in this repo.
2. **Settings** — Note which settings are global (`mint.json`) vs. per-page (frontmatter). Match existing frontmatter patterns in similar pages.
3. **Pages** — Study what MDX components and syntax features are used. Reuse the same component patterns (e.g., `Card`, `Callout`, tabs) rather than inventing new ones.
4. **Hidden-pages** — Know when content should be excluded from sidebar vs. truly hidden.
5. **Mintignore** — Know which files are intentionally excluded so you don't accidentally re-add them.

### Content Organization Principles

- Follow the **same directory grouping** as the live docs URL structure (e.g., `organize/navigation` content lives under `organize/navigation/`)
- Use **frontmatter** (`title`, `description`, `icon`, `description`) exactly as shown in the official docs
- Keep **page-level configurations** minimal and consistent with neighboring pages
- All MDX components used must be from the Mintlify component library — no custom components unless explicitly required

### Updating Existing Pages

When updating a page that covers one of these topics:

1. Open the corresponding official doc URL listed above
2. Compare the current local page against the official doc
3. If the official doc introduced new features/settings, add them following the existing local patterns
4. If the local page has content the official doc doesn't cover, flag it — it may be stale or a local addition worth preserving

### Markdown Style Reference

When writing or updating any Markdown/MDX content, these are the **authoritative references** for formatting and style:

| Reference | URL |
|-----------|-----|
| Markdown Guide Basic Syntax | https://www.markdownguide.org/basic-syntax/ |
| Technical Writing Markdown Best Practices | https://technicalwritingmp.com/docs/markdown-best-practices/ |
| Google Markdown Style Guide | https://google.github.io/styleguide/docguide/style.html |
| CommonMark Best Practices Discussion | https://talk.commonmark.org/t/markdown-best-practices/3115 |

### GitHub Trending Daily Rank — Standard Template

The canonical template for writing GitHub Trending daily rank index pages is:

**`/Users/yueyh/Projects/mintlify-docs/trending/2026-04-06/index.md`**

When creating or updating a `trending/YYYY-MM-DD/index.md` file, follow this structure exactly:

```md
---
title: YYYY-MM-DD GitHub Daily Rank
description: GitHub 每日飙升榜 · YYYY-MM-DD
---

# YYYY-MM-DD GitHub Daily Rank

> 数据来源: [OpenGithubs/github-daily-rank](https://github.com/OpenGithubs/github-daily-rank)

## Top 10 排行榜

| 项目 | 今日新增 | 总 Stars | 分析报告 |
|------|----------|----------|----------|
| [owner/repo](https://github.com/owner/repo) | ⭐+N | Xk | [📄 查看报告](/trending/YYYY-MM-DD/repo-name) |
... (10 rows total)

---
*数据来源: [github-daily-rank](https://github.com/OpenGithubs/github-daily-rank) · 每日早上 8:30 更新*
```

Key rules:
- Frontmatter uses `title` and `description` only (no `icon`)
- Table columns: **项目** (link to GitHub), **今日新增** (⭐+N format), **总 Stars** (Xk format), **分析报告** (link to local MDX file)
- Repo links use full GitHub URL format: `https://github.com/owner/repo`
- Analysis report links use relative path: `/trending/YYYY-MM-DD/repo-name`
- Footer line: data source attribution + update time note
- Empty line before `---` horizontal rule
- **Always exactly 10 rows** in the table

### Social Media Hot Trends — File Naming

Reference: `/Users/yueyh/Projects/mintlify-docs/social-media/2026-04-04/20-00.mdx`

Canonical template path: `social-media/{YYYY-MM-DD}/{HH:MM}.mdx`

Frontmatter format:
```yaml
---
title: YYYY-MM-DD HH:MM 社交热点
description: 微博/知乎/抖音/B站/头条/豆瓣/BBC/什么值得买/纽约时报 · 全平台热点监控
---
```

Key rules:
- File path: `social-media/{YYYY-MM-DD}/{HH:MM}.mdx` (e.g. `social-media/2026-04-08/02:38.mdx`)
- `title` field must include full date: `YYYY-MM-DD HH:MM 社交热点`
- Table for each platform: **热度 | 标题 | 情感 | 摘要** (所有平台统一格式：微博/知乎/B站/抖音/头条/豆瓣/BBC/什么值得买/纽约时报)
- Sentiment: `🟢 正面` / `🟡 中性` / `🔴 负面` / `⚪ 未知`
- **Must also update `docs.json`** navigation to register new date group

### Key Patterns to Follow

- Navigation order in `mint.json` matches the sidebar order users see in the live docs
- Frontmatter `title` and `description` are required on every page
- Use **tabs** for multi-platform/ multi-language instructions (follow existing tab patterns in this repo)
- Use **code groups** (````code-group` wrapper) when showing multiple framework variants
- Keep code blocks with **explicit language tags** for syntax highlighting

### GitHub Repo Research — Standard Workflow

When analyzing a GitHub repo (via article link or direct URL), follow this workflow:

**1. Agent Team Setup**
```
TeamCreate "github-research-analysis"
TaskCreate(3): 读取文章 / Web调研 / 制定方案
Agent reader + researcher + planner (all background)
```

**2. Reader** — Read source content
- Use `browser_navigate` + `browser_snapshot` via Playwright MCP (WebFetch fails on WeChat/某些域名)
- Extract: title, author, core claims, key features

**3. Researcher** — Web expansion research
- Search for: latest news, competitors, academic response, GitHub stars/trends
- Use WebSearch and browser tools

**4. Planner** — Develop 3 implementation plans
- Based on reader + researcher findings
- Each plan: problem definition, implementation, expected output, risks

**5. Mintlify Output** — Always create vault
```
mintlify-docs/github-research/{repo-name}/
├── index.mdx              # 入口索引页
├── findings_deepscientist.md   # 核心发现
├── findings_competitors.md     # 竞品分析
├── findings_academic.md       # 学术反响
└── research_plan.md           # 研究计划
```

**6. Navigation** — Update docs.json
```json
{
  "tab": "GitHub Research",
  "groups": [{
    "group": "{repo-name}",
    "expanded": true,    // true=展开显示所有子页面
    "pages": [
      "github-research/{repo-name}/index",
      "github-research/{repo-name}/findings_*",
      ...
    ]
  }]
}
```

**Team Config Reference**: `~/.claude/teams/github-research-analysis/config.json`

