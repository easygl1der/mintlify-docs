# Yitwah Notes — Mintlify 文档站点

基于 [Mintlify](https://mintlify.com) 构建的个人知识库，支持 AI 问答、搜索和 GitHub Pages 部署。

## 核心原理

**`★ Insight ─────────────────────────────────────`**
Mintlify 是"文档即代码"理念的现代化实现——内容是 Markdown/MDX，导航是 JSON 配置，部署是 Git push。最大的设计亮点是 **contextual AI** 特性：AI 助手能"看到"当前页面内容并基于此回答问题，实现真正的私有知识库问答。
`─────────────────────────────────────────────────`

## 快速启动

```bash
# 方式一：使用 npx（推荐，无需全局安装）
npx mint dev

# 方式二：全局安装后启动
npm install -g mintlify
mint dev
```

访问 **http://localhost:3000** 即可预览。

## Mintlify 核心概念

### 1. docs.json — 导航配置（最关键）

控制整个站点的左侧导航栏结构和多 tab 分组。

```json
{
  "tabs": [
    {
      "tab": "文档",
      "groups": [
        {
          "group": "入门",
          "pages": ["index", "quickstart"]
        }
      ]
    }
  ]
}
```

**三条规则：**
- `"pages"` 中的路径**不带文件扩展名**（`index` 而非 `index.mdx`）
- 路径相对于项目根目录
- 支持嵌套分组（`expanded: false` 控制默认折叠）

### 2. Frontmatter — 页面元数据

每个 `.mdx` 文件顶部必须有 YAML frontmatter：

```yaml
---
title: "页面标题"           # 浏览器标签和导航中显示
description: "简短描述"    # SEO 和 AI 上下文的摘要
---
```

**来自本仓库的真实示例**（`index.mdx`）：

```yaml
---
title: "知识库总览"
description: "Yitwah 的个人知识管理站点"
---
```

### 3. MDX — Markdown + JSX

Mintlify 使用 MDX 格式——在 Markdown 中直接使用 React 组件。

```mdx
# 标准 Markdown

**支持** 所有标准语法

## 嵌入组件示例

<Note>这是一条提示</Note>

<Tip>这是一个技巧</Tip>

<Warning>这是警告</Warning>
```

内置组件包括：`Note`, `Tip`, `Warning`, `Card`, `Cards`, `Callout`, `Steps`, `CodeGroup` 等。

### 4. 目录结构规范

```
├── docs.json              # 导航配置（必需）
├── index.mdx              # 首页（必需）
├── images/                # 公共图片资源
├── snippets/              # 可复用 MDX 片段
├── .mintlify/             # 主题配置文件
├── [任意目录]/            # 按内容类型组织
│   └── [页面].mdx
└── README.md
```

## 本仓库结构详解

```
★ Insight ─────────────────────────────────────
本仓库采用了 **多 Tab 分组**策略：将知识库分为"文档"、"社交热点"、"GitHub Trending"、"我的笔记"四大板块。docs.json 中的嵌套 group（带 expanded 控制）实现了按日期折叠的优雅体验。
─────────────────────────────────────────────────
```

| 目录/文件 | 用途 |
|-----------|------|
| `docs.json` | 完整的导航配置，控制所有 tab 和页面分组 |
| `index.mdx` | 首页 — 知识库总览和快速入口 |
| `quickstart.mdx` | 快速上手指南 — 新用户引导 |
| `concepts/` | 概念文档 — 知识管理理念和最佳实践 |
| `how-to/` | 实践指南 — 部署、笔记整理等操作手册 |
| `my-notes/` | 个人笔记 — 学习/工作/想法等分类笔记 |
| `trending/` | GitHub Trending 每日追踪 |
| `social-media/` | 社交热点内容聚合 |
| `snippets/` | 可复用的 MDX 片段 |

## docs.json 字段说明

```json
{
  "theme": "mint",                    // 固定为 "mint"
  "name": "Yitwah Notes",            // 站点名称（浏览器标题）
  "logo": { "light/dark": "/images/logo.svg" },
  "favicon": "/images/favicon.svg",
  "colors": {                        // 主题色配置
    "primary": "#16A34A",
    "light": "#07C983",
    "dark": "#15803D"
  },
  "navigation": { ... },             // 导航结构
  "footer": { "socials": { ... } },   // 页脚社交链接
  "contextual": {                    // AI 助手配置
    "options": ["copy", "view", "claude"]
  }
}
```

**contextual AI** 是 Mintlify 的核心特性 — 配置后每个页面右下角会出现 AI 助手图标，能基于当前页面内容回答用户问题。

## 部署到 GitHub Pages

```bash
# 1. 本地开发测试
npx mint dev

# 2. 构建生产版本
npx mint build

# 3. GitHub Actions 自动部署
# 推送到 main 分支后，.github/workflows 接管构建并部署
```

本仓库的 GitHub Pages 配置已在 `.github/workflows` 中设置，push 后自动触发。

## 添加新内容的完整流程

**Step 1：创建 MDX 文件**，例如 `my-notes/新笔记.md`：

```yaml
---
title: "新笔记标题"
description: "简短描述"
---

# 新笔记标题

内容...
```

**Step 2：在 docs.json 中注册路径**：

在对应 tab 的 `pages` 数组中添加文件名（不含扩展名）：

```json
"pages": [
  "my-notes/index",
  "my-notes/关于我",
  "my-notes/新笔记"    // <-- 新增
]
```

**Step 3：本地预览并提交**：

```bash
npx mint dev    # 预览
git add .
git commit -m "docs: 添加新笔记"
git push
```

## Frontmatter 进阶配置

```yaml
---
title: "页面标题"
description: "描述文字"
# 下面为可选配置
# icon: "📚"                          # 导航中的图标
# mode: "pure"                        # 纯文档模式（隐藏侧边栏）
# ogImage: "/images/og.png"          # Open Graph 图片
---
```

## AI 助手配置（contextual）

本仓库启用了三个 contextual 选项：

```json
"contextual": {
  "options": ["copy", "view", "claude"]
}
```

- **copy** — 一键复制代码块
- **view** — 查看页面源码
- **claude** — Mintlify 内置 AI 问答（基于当前页面内容）

> `★ Insight ─────────────────────────────────────`
> contextual AI 的实现原理是：在构建时将页面内容注入 AI 上下文中。因此添加新内容后需要重新部署，AI 才能"看到"新内容并回答相关问题。
> `─────────────────────────────────────────────────`
