# CLAUDE.md — Mintlify Documentation Project

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
- Table for each platform: **热度 | 标题 | 情感 | 摘要** (微博/知乎/B站) or **热度 | 标题 | 链接** (抖音/头条/豆瓣/BBC/什么值得买/纽约时报)
- Sentiment: `🟢 正面` / `🟡 中性` / `🔴 负面` / `⚪ 未知`
- **Must also update `docs.json`** navigation to register new date group

### Key Patterns to Follow

- Navigation order in `mint.json` matches the sidebar order users see in the live docs
- Frontmatter `title` and `description` are required on every page
- Use **tabs** for multi-platform/ multi-language instructions (follow existing tab patterns in this repo)
- Use **code groups** (````code-group` wrapper) when showing multiple framework variants
- Keep code blocks with **explicit language tags** for syntax highlighting
