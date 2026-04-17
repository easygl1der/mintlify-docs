---
title: MinerU 集成可行性分析
description: 在 Onyx 中集成 MinerU 进行 PDF 到 Markdown 转换的可行性评估和实施方案
---

# Onyx MinerU 集成可行性分析

> 分析时间：2026-04-17
> 数据来源：多 Agent 并行分析

## 一、MinerU 简介

**MinerU** 是一个强大的 PDF 解析工具，能够：
- 将 PDF 转换为结构化的 Markdown
- 保留标题层级、表格、列表等格式
- 提取并保存图像
- 识别公式（LaTeX）

### 对比现有方案

| 特性 | 现有方案（pypdf） | MinerU |
|------|-------------------|--------|
| 文本提取 | ✅ 支持 | ✅ 支持 |
| 格式保留 | ❌ 无 | ✅ 保留标题、列表 |
| 表格提取 | ❌ 纯文本 | ✅ 结构化表格 |
| 图像提取 | ✅ 可选 | ✅ 自动提取 |
| 公式处理 | ❌ 无 | ✅ LaTeX 输出 |
| Markdown 输出 | ❌ 无 | ✅ 原生支持 |

## 二、现有 PDF 处理流程

**文件位置**：`backend/onyx/file_processing/extract_file_text.py:203-279`

```python
def read_pdf_file(file_path: str) -> ExtractionResult:
    reader = PdfReader(file_path)

    # 简单文本提取
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"

    # 可选图片提取
    images = []
    if get_image_extraction_and_analysis_enabled():
        images = extract_images_from_pdf(file_path)

    return ExtractionResult(
        text_content=text,
        embedded_images=images,
        metadata={...}
    )
```

### 问题分析
1. **格式丢失**：纯文本输出，标题层级、列表结构全部丢失
2. **表格混乱**：表格内容变成无结构的文本块
3. **图像孤立**：图片提取与文本上下文分离
4. **上下文缺失**：无法理解文档结构

## 三、MinerU 集成方案

### 方案一：作为可选后端（推荐）

与现有 Unstructured API 集成模式相同，在配置中启用：

```python
# 伪代码：mineru_integration.py

from mineru import MagicPDF

def mineru_extract_pdf(file_path: str) -> ExtractionResult:
    """使用 MinerU 提取 PDF"""

    # 初始化 MinerU
    pdf_processor = MagicPDF()

    # 处理 PDF
    result = pdf_processor.extract(
        file_path,
        extract_images=True,
        extract_tables=True,
        extract_formulas=True,
    )

    # 转换为 Onyx 格式
    return ExtractionResult(
        text_content=result.markdown,  # 结构化 Markdown
        embedded_images=result.images,
        tables=result.tables,          # 结构化表格
        formulas=result.formulas,     # LaTeX 公式
        metadata={
            "toc": result.table_of_contents,  # 目录结构
            "page_count": result.page_count,
        }
    )
```

### 集成点

**文件位置**：`backend/onyx/file_processing/extract_file_text.py:640-774`

```python
def extract_text_and_images(
    file_path: str,
    file_name: str,
    ignore_unsupported_file_types: bool = False,
) -> ExtractionResult:
    """主提取函数，根据配置选择提取器"""

    extension = Path(file_name).suffix.lower()

    if extension == ".pdf":
        # 根据配置选择提取器
        if is_mineru_enabled():
            return mineru_extract_pdf(file_path)
        elif is_unstructured_enabled():
            return unstructured_to_text(file_path)
        else:
            return read_pdf_file(file_path)  # 默认 pypdf

    # ... 其他文件类型
```

### 配置项

```python
# backend/onyx/configs/model_utils.py 或新配置文件

def is_mineru_enabled() -> bool:
    """检查是否启用 MinerU"""
    return (
        os.environ.get("MINERU_ENABLED", "false").lower() == "true"
        and os.environ.get("MINERU_API_KEY")  # API Key 或本地模型
    )

# 配置示例
# MINERU_ENABLED=true
# MINERU_API_KEY=your-api-key
# MINERU_MODEL=local  # 或 "cloud"
```

## 四、实施步骤

### Phase 1：基础集成（1-2 天）

```python
# 1. 安装 MinerU SDK
# requirements.txt
# mineru>=1.0.0

# 2. 创建 mineru_integration.py
# backend/onyx/file_processing/mineru_integration.py

# 3. 修改 extract_file_text.py 添加 MinerU 选项
```

### Phase 2：测试验证（1 天）

```python
# 测试用例
def test_mineru_pdf_extraction():
    pdf_path = "test/sample.pdf"

    result = mineru_extract_pdf(pdf_path)

    assert result.text_content.startswith("#")  # Markdown 格式
    assert len(result.tables) > 0  # 表格提取
    assert len(result.embedded_images) > 0  # 图片提取
```

### Phase 3：生产部署（1 天）

```bash
# 环境配置
export MINERU_ENABLED=true
export MINERU_API_KEY=$MINERU_API_KEY

# 重启 Celery Worker
```

## 五、优势分析

### 1. 更好的结构化提取

**现有输出**：
```
This is some text. Here is a table: column1, column2, value1, value2.
Here is another section. More text here.
```

**MinerU 输出**：
```markdown
# Document Title

This is some text.

## Table Section

| Column1 | Column2 |
|---------|---------|
| Value1  | Value2  |

## Another Section

More text here.
```

### 2. 改进 RAG 效果

```python
# 标题层级 → 更好的语义分块
# 表格结构 → 保留表格关系
# 公式提取 → 支持科学文档
```

### 3. 图像上下文

```python
# MinerU 自动关联图像与上下文
result = mineru_extract_pdf(pdf_path)
for img in result.embedded_images:
    print(f"Image: {img.path}")
    print(f"Context: {img.caption}")  # 图像说明
```

## 六、注意事项

### 1. 性能考量

```python
# MinerU 处理时间可能比 pypdf 长
# 建议：
# - 使用异步队列
# - 设置超时限制
# - 提供降级方案

@shared_task(timeout=300)  # 5 分钟超时
def process_pdf_with_mineru(file_id: int):
    try:
        result = mineru_extract_pdf(file_path)
    except TimeoutError:
        # 降级到 pypdf
        return read_pdf_file(file_path)
```

### 2. API 成本

```python
# 云端 API 成本
# 本地部署（推荐用于大量文档）
# docker run -p 8080:8080 mineru/local-model
```

### 3. 兼容性测试

```python
# 需要测试的文件类型：
# - 扫描 PDF（无文本层）
# - 混合 PDF（文本+图片）
# - 表格密集型 PDF
# - 公式密集型 PDF
# - 多语言 PDF
```

## 七、代码示例

### 完整集成代码

```python
# backend/onyx/file_processing/mineru_integration.py

import os
from dataclasses import dataclass
from typing import Optional

@dataclass
class MinerUResult:
    markdown: str
    images: list[dict]
    tables: list[dict]
    formulas: list[dict]
    metadata: dict

def mineru_extract_pdf(file_path: str) -> ExtractionResult:
    """MinerU PDF 提取主函数"""

    # 检查环境
    if not is_mineru_enabled():
        raise RuntimeError("MinerU is not enabled")

    try:
        # 导入 MinerU
        from mineru import MagicPDF

        # 初始化（本地或云端）
        processor = MagicPDF(
            api_key=os.environ.get("MINERU_API_KEY"),
            mode="local" if "local" in os.environ.get("MINERU_MODEL", "") else "cloud",
        )

        # 处理
        result = processor.extract(
            file_path,
            extract_images=True,
            extract_tables=True,
            extract_formulas=True,
            output_format="markdown",
        )

        # 转换为 Onyx 格式
        return ExtractionResult(
            text_content=result.markdown,
            embedded_images=[
                {
                    "path": img.path,
                    "data": img.data,
                    "caption": img.caption,
                }
                for img in result.images
            ],
            tables=result.tables,
            formulas=result.formulas,
            metadata={
                "toc": result.table_of_contents,
                "page_count": result.page_count,
                "extractor": "mineru",
            },
        )

    except Exception as e:
        # 记录日志并降级
        logger.warning(f"MinerU extraction failed: {e}, falling back to pypdf")
        return read_pdf_file(file_path)
```

## 八、风险评估

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 处理时间长 | 中 | 异步队列 + 超时 |
| API 成本 | 中 | 本地部署 |
| 格式兼容性 | 低 | 测试套件 |
| 依赖复杂性 | 低 | 可选依赖 |

## 九、推荐优先级

**🥇 第一优先级实现**

理由：
- 实施难度低（类似 Unstructured 集成）
- 收益显著（结构化输出 → 更好 RAG）
- 可独立验证
- 不破坏现有功能（降级方案）

## 十、后续扩展

### 1. 公式渲染支持
```python
# 在前端添加 LaTeX 渲染
# 支持科学论文、教育文档
```

### 2. 表格结构保留
```python
# 在索引时保留表格结构
# 支持"查询表格数据"场景
```

### 3. 图像描述生成
```python
# 使用 VLM 为图像生成描述
# 增强图像检索效果
```
