---
title: react-resizable-panels 组件库详解
description: PanelGroup、Panel、PanelResizeHandle 三组件；嵌套布局；布局持久化；SSR注意事项
---

# react-resizable-panels 组件库详解

> 来源：[bvaughn/react-resizable-panels](https://github.com/bvaughn/react-resizable-panels)，5.2k stars，MIT，2026-04-03 更新 v4.9.0。

---

## 它是什么

React 组件库，用于构建**可拖拽调整大小的面板布局**——就是 VS Code 编辑器那种可以拖动边界、四宫格 / 多窗格的工作台界面。核心三个组件：`PanelGroup`（容器）、`Panel`（面板）、`PanelResizeHandle`（拖动把手）。

---

## 核心组件

### PanelGroup — 外层容器

```tsx
import { Panel, PanelGroup, PanelResizeHandle } from "react-resizable-panels";

<PanelGroup direction="horizontal">
  <Panel defaultSize={20}>侧边栏</Panel>
  <PanelResizeHandle />
  <Panel defaultSize={80}>主内容区</Panel>
</PanelGroup>
```

| Prop | 作用 |
|------|------|
| `direction` | `"horizontal"`（左右）或 `"vertical"`（上下） |
| `defaultLayout` | 默认布局，用于页面加载时恢复 |
| `onLayoutChange` | 拖动中实时触发（每次 pointer move） |
| `onLayoutChanged` | 拖动结束后触发（推荐用于保存布局） |
| `id` | 唯一标识，用于持久化布局 |
| `disabled` | 禁用整个 group 的调整功能 |
| `groupRef` | 命令式 API：`getLayout()`、`setLayout(layout)` |

### Panel — 面板单元

```tsx
<Panel defaultSize={50} minSize={20} maxSize={80} collapsible>
  内容区
</Panel>
```

| Prop | 作用 |
|------|------|
| `defaultSize` | 默认尺寸（默认按 Panel 数量自动分配） |
| `minSize` | 最小尺寸，达到后触发折叠 |
| `maxSize` | 最大尺寸 |
| `collapsible` | 启用折叠功能 |
| `collapsedSize` | 折叠后的尺寸（默认 0） |
| `disabled` | 禁用该面板的调整 |
| `panelRef` | 命令式 API：`collapse()`、`expand()`、`getSize()`、`isCollapsed()`、`resize(size)` |
| `onResize` | 尺寸变化时调用，参数含百分比和像素值 |

**尺寸格式**：数字默认像素，字符串支持 `50%`（百分比）、`200px`（像素）、`2rem`（字体单位）、`50vh`（视口单位）。

### PanelResizeHandle — 拖动把手

```tsx
<PanelResizeHandle className="handle-class" />
```

| Prop | 作用 |
|------|------|
| `disabled` | 禁用该把手 |
| `disableDoubleClick` | 双击不重置面板尺寸 |
| `className` / `style` | 自定义样式，配合 `[data-panel-resize-handle-active]` 使用 |

---

## 嵌套布局：四宫格示例

```tsx
<PanelGroup direction="horizontal">
  {/* 左侧 */}
  <Panel defaultSize={20}>
    <PanelGroup direction="vertical">
      <Panel defaultSize={50}>文件树</Panel>
      <PanelResizeHandle />
      <Panel defaultSize={50}>Notes</Panel>
    </PanelGroup>
  </Panel>

  <PanelResizeHandle />

  {/* 右侧 */}
  <Panel defaultSize={80}>
    <PanelGroup direction="vertical">
      <Panel defaultSize={70}>PDF 阅读区</Panel>
      <PanelResizeHandle />
      <Panel defaultSize={30}>AI 问答区</Panel>
    </PanelGroup>
  </Panel>
</PanelGroup>
```

这就是**四宫格 IDE 布局**：外层水平拆左右，左侧文件树 + 笔记，右侧 PDF 阅读 + AI 对话。

---

## 布局持久化

```tsx
// 保存到 localStorage
function App() {
  const [layout, setLayout] = useState(() => {
    const saved = localStorage.getItem("my-layout");
    return saved ? JSON.parse(saved) : undefined;
  });

  return (
    <PanelGroup
      direction="horizontal"
      defaultLayout={layout}
      onLayoutChanged={(layout) => {
        localStorage.setItem("my-layout", JSON.stringify(layout));
      }}
    >
      {/* ... */}
    </PanelGroup>
  );
}
```

`onLayoutChanged` 在拖动结束后触发，适合保存到 `localStorage` 或数据库。`id` 属性配合 `[data-panel]` 可以关联持久化状态。

---

## 样式处理

Panel 会渲染为一个**嵌套的 `div`**，样式隔离：

```css
/* 正确：给 Panel 里的内容加样式 */
.my-panel-content {
  height: 100%;
  overflow: auto;
}

/* 拖动把手的 hover 样式 */
[data-panel-resize-handle] {
  width: 4px;
  background: #e5e5e5;
}
[data-panel-resize-handle-active] {
  background: #3b82f6;
}
```

Separator 元素带 `data-separator` 属性，可通过 CSS 选择器精准控制。

---

## 键盘无障碍

Separator 组件自带 `role="separator"` 和 WAI-ARIA 属性，Tab 聚焦、方向键调整大小均已内置支持。搭配 `disableDoubleClick` 可以避免误触。

---

## SSR 注意事项

- `defaultSize` 用数字像素值而非百分比，可减少 SSR 时的布局抖动
- 组件支持 SSR（服务端渲染），需注意 `defaultLayout` 在水合时的初始值
- 官方建议：`onLayoutChanged` 保存布局而非 `onLayoutChange`（后者触发太频繁）

---

## 和前端构想的关系

配合 Zustand 做状态驱动、react-pdf 做 PDF 渲染，这套布局可以直接套用。**IDE 四宫格布局**：

```
左侧文件树 | 笔记面板
PDF 阅读区 | AI 问答区
```

---

## Source

- [bvaughn/react-resizable-panels](https://github.com/bvaughn/react-resizable-panels)
- 官方文档：https://react-resizable-panels.vercel.app/
