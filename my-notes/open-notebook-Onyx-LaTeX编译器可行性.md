---
title: Onyx LaTeX 编译器可行性分析
description: 在 Onyx 中添加 LaTeX 编译器支持（如 Overleaf、Prismer）的可行性评估
---

# Onyx LaTeX 编译器可行性分析

> 分析时间：2026-04-17
> 数据来源：多 Agent 并行分析

## 一、现状分析

### 现有 LaTeX 能力

**前端渲染**：
- KaTeX 用于数学公式渲染（`web/node_modules/katex/`）
- 仅支持客户端渲染，不支持编译

**后端处理**：
- `.tex` 文件不在 `DOCUMENT_EXTENSIONS` 中
- LaTeX 文件被视为纯文本处理

### 功能差距

| 功能 | 当前状态 | 需求 |
|------|----------|------|
| LaTeX 渲染 | ✅ KaTeX | 已有 |
| LaTeX 编译 | ❌ 无 | 需要 |
| 错误反馈 | ❌ 无 | 需要 |
| 多文件支持 | ❌ 无 | 需要 |
| PDF 输出 | ❌ 无 | 需要 |

## 二、使用场景

### 场景 1：LaTeX 文档索引

```python
# 用户上传 .tex 文件
# 系统编译并提取内容
# 生成可搜索的索引

tex_file = upload("paper.tex")
# 编译: pdflatex paper.tex
# 索引: 提取文本、图表、公式
# 存储: PDF 输出
```

### 场景 2：实时预览

```python
# 用户编辑 LaTeX
# 系统实时编译
# 返回预览结果

edit_latex(content)
# → POST /api/latex/compile
# ← { "pdf_url": "...", "errors": [...] }
```

### 场景 3：公式提取

```python
# 从 LaTeX 文档中提取公式
# 转换为可搜索的格式

extract_formulas_from_tex(tex_content)
# → [ "$E=mc^2$", "$\int_0^1 x dx$", ... ]
```

## 三、架构方案

### 方案一：Overleaf API

**优点**：
- 托管服务，无需运维
- 成熟的 API
- 自动缩放

**缺点**：
- 付费计划才支持 API
- 网络延迟
- 数据隐私考虑

```python
# backend/onyx/file_processing/latex_compiler.py

import requests

class OverleafCompiler:
    def __init__(self, api_key: str, project_id: str):
        self.api_key = api_key
        self.project_id = project_id
        self.base_url = "https://api.overleaf.com"

    def compile(self, tex_content: str) -> CompileResult:
        # 1. 上传文件
        self.upload_file("main.tex", tex_content)

        # 2. 触发编译
        compile_job = self.trigger_compile()

        # 3. 轮询状态
        result = self.wait_for_compile(compile_job["id"])

        # 4. 下载 PDF
        pdf_url = self.get_pdf_url(result)

        return CompileResult(
            success=True,
            pdf_url=pdf_url,
            logs=result["logs"],
        )
```

### 方案二：自部署（Prismer / LaTeX 在线编译器）

**优点**：
- 完全控制
- 无 API 成本
- 数据隐私

**缺点**：
- 需要运维
- 需要扩展资源

```python
# docker-compose.yml
services:
  latex-compiler:
    image: texlive:latest
    volumes:
      - ./latex-projects:/projects
    ports:
      - "8080:8080"
    command: ["python", "server.py"]

# backend/onyx/file_processing/latex_compiler.py

class LocalLatexCompiler:
    def __init__(self, base_url: str = "http://localhost:8080"):
        self.base_url = base_url

    def compile(self, tex_content: str) -> CompileResult:
        response = requests.post(
            f"{self.base_url}/compile",
            json={"tex": tex_content},
            timeout=60,
        )
        result = response.json()

        return CompileResult(
            success=result["success"],
            pdf_data=result["pdf"],
            logs=result["logs"],
            errors=result["errors"],
        )
```

### 方案三：本地 LaTeX（简单场景）

```bash
# 安装 pdflatex
# apt-get install texlive-latex-base

# backend/onyx/file_processing/latex_compiler.py

import subprocess
import os
import tempfile

class LocalLatexCompiler:
    def compile(self, tex_content: str, working_dir: str = None) -> CompileResult:
        if working_dir is None:
            working_dir = tempfile.mkdtemp()

        # 写入文件
        tex_path = os.path.join(working_dir, "main.tex")
        with open(tex_path, "w") as f:
            f.write(tex_content)

        # 编译
        result = subprocess.run(
            ["pdflatex", "-interaction=nonstopmode", "main.tex"],
            cwd=working_dir,
            capture_output=True,
            text=True,
        )

        # 读取 PDF
        pdf_path = os.path.join(working_dir, "main.pdf")
        if os.path.exists(pdf_path):
            with open(pdf_path, "rb") as f:
                pdf_data = f.read()
        else:
            pdf_data = None

        return CompileResult(
            success=result.returncode == 0,
            pdf_data=pdf_data,
            logs=result.stdout,
            errors=self.parse_errors(result.stdout),
        )

    def parse_errors(self, log: str) -> list[str]:
        """从 LaTeX 日志中提取错误"""
        errors = []
        for line in log.split("\n"):
            if "Error" in line or "!" in line:
                errors.append(line.strip())
        return errors
```

## 四、API 设计

### 编译接口

```python
# backend/onyx/server/features/latex/api.py

@router.post("/latex/compile")
async def compile_latex(
    tex_content: str,
    project_id: str = None,
    auto_compile: bool = True,
) -> LatexCompileResponse:
    """
    编译 LaTeX 文档

    返回：
    - PDF URL 或 Base64
    - 编译日志
    - 错误列表
    """
    result = latex_compiler.compile(tex_content)

    return LatexCompileResponse(
        success=result.success,
        pdf=result.pdf_url or base64.b64encode(result.pdf_data),
        logs=result.logs,
        errors=result.errors,
    )


@router.post("/latex/compile-async")
async def compile_latex_async(
    tex_content: str,
) -> dict:
    """异步编译，返回 job_id"""
    job_id = str(uuid.uuid4())

    # 入队 Celery 任务
    compile_latex_task.delay(job_id, tex_content)

    return {"job_id": job_id, "status": "queued"}


@router.get("/latex/status/{job_id}")
async def get_compile_status(job_id: str) -> LatexStatusResponse:
    """查询编译状态"""
    return LatexStatusResponse(
        job_id=job_id,
        status=get_job_status(job_id),
        result=get_job_result(job_id) if is_completed(job_id) else None,
    )
```

### 文件处理接口

```python
@router.post("/latex/upload")
async def upload_latex_project(
    files: list[UploadFile],
    folder_name: str = None,
) -> LatexProjectResponse:
    """
    上传完整的 LaTeX 项目
    支持：.tex, .sty, .cls, .bib, 图片等
    """
    project_id = str(uuid.uuid4())
    project_dir = f"/latex-projects/{project_id}"

    # 保存所有文件
    for file in files:
        save_file(file, project_dir)

    # 返回项目信息
    return LatexProjectResponse(
        project_id=project_id,
        files=[f.filename for f in files],
    )
```

## 五、Celery 任务设计

```python
# backend/onyx/background/celery/tasks/latex_processing/tasks.py

@shared_task(
    bind=True,
    max_retries=2,
    default_retry_delay=30,
    expires=300,  # 5 分钟过期
)
def compile_latex_task(self, job_id: str, tex_content: str) -> dict:
    """LaTeX 异步编译任务"""

    try:
        # 1. 创建工作目录
        working_dir = f"/tmp/latex-compile-{job_id}"
        os.makedirs(working_dir, exist_ok=True)

        # 2. 写入文件
        tex_path = os.path.join(working_dir, "main.tex")
        with open(tex_path, "w") as f:
            f.write(tex_content)

        # 3. 编译（多次运行以解决交叉引用）
        for _ in range(3):
            result = subprocess.run(
                ["pdflatex", "-interaction=nonstopmode", "main.tex"],
                cwd=working_dir,
                capture_output=True,
                text=True,
            )

        # 4. 读取结果
        pdf_path = os.path.join(working_dir, "main.pdf")
        if os.path.exists(pdf_path):
            with open(pdf_path, "rb") as f:
                pdf_data = f.read()

            # 5. 存储 PDF
            pdf_url = file_store.save_file_from_bytes(
                pdf_data,
                f"{job_id}.pdf",
            )

            # 6. 更新状态
            update_job_result(job_id, {
                "success": True,
                "pdf_url": pdf_url,
                "logs": result.stdout,
            })
        else:
            update_job_result(job_id, {
                "success": False,
                "errors": parse_latex_errors(result.stdout),
            })

    except Exception as e:
        # 重试或标记失败
        raise self.retry(exc=e)
```

## 六、文件类型支持

```python
# backend/onyx/file_processing/file_types.py

DOCUMENT_EXTENSIONS = [
    # ... 现有扩展
    ".tex",  # 添加 LaTeX 支持
]

def is_latex_file(filename: str) -> bool:
    """检查是否为 LaTeX 文件"""
    return Path(filename).suffix.lower() == ".tex"

def extract_text_from_latex(tex_content: str) -> str:
    """从 LaTeX 提取纯文本"""
    # 移除命令
    text = re.sub(r'\\command\{[^}]*\}', '', tex_content)
    # 移除环境
    text = re.sub(r'\\begin\{[^}]*\}[^}]*\\end\{[^}]*\}', '', text)
    return text
```

## 七、挑战与解决方案

### 挑战 1：编译复杂性

```python
# LaTeX 编译可能需要多次运行解决交叉引用
# 依赖外部包可能不存在

# 解决方案：
# - 使用完整版 TeX Live 镜像
# - 预安装常用包
# - 提供错误反馈让用户修复
```

### 挑战 2：安全性

```python
# \write18 可以执行任意命令
# 恶意 .tex 文件可能执行攻击代码

# 解决方案：
# - 使用 Docker 沙箱
# - 禁用 \write18
# - 限制文件访问
```

### 挑战 3：多文件项目

```python
# 主 .tex 引用其他 .tex, .sty, .bib 文件
# 需要完整项目结构

# 解决方案：
# - 支持 ZIP 上传
# - 或完整目录结构
```

### 挑战 4：编译时间

```python
# LaTeX 编译可能需要几秒钟
# 大文档可能需要更长时间

# 解决方案：
# - 异步任务 + 轮询
# - WebSocket 推送
# - 超时限制
```

## 八、推荐方案

### 方案选择

| 场景 | 推荐方案 | 理由 |
|------|----------|------|
| 快速验证 | 本地 pdflatex | 无需外部依赖 |
| 生产环境 | 自部署服务 | 完全控制 + 成本可控 |
| 企业用户 | Overleaf API | 托管服务 + 专业支持 |

### 实施建议

**暂缓实现，理由**：
1. 架构复杂，需要新增子系统
2. 安全性考量（LaTeX 注入风险）
3. 需要额外的运维资源
4. 当前优先级较低

**建议后续规划**：
1. 首先明确服务提供商选择
2. 设计完整的 API 和任务队列
3. 评估安全风险和缓解措施
4. 准备运维资源和监控

## 九、风险评估

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 安全性 | 高 | Docker 沙箱 + 禁用危险命令 |
| 编译时间 | 中 | 异步队列 + 超时 |
| 依赖复杂性 | 中 | 使用完整 TeX Live |
| 运维成本 | 中 | 容器化部署 |

## 十、相关参考

### 开源方案

- **Prismer**：https://github.com/your-repos/prismer
- **LaTeX Online**：https://github.com/asymptote/asymptote
- ** Papeeria**：商业托管方案

### Docker 镜像

```dockerfile
# texlive-sandbox/Dockerfile
FROM texlive/texlive:latest

# 禁用危险命令
RUN pdflatex --version

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1
```
