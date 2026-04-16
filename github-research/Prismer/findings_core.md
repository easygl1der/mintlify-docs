---
title: Core Findings
description: Prismer 核心技术发现与架构分析
---

# 核心发现：Prismer 深度解析

## 1. 顶层设计与架构
Prismer 展示了极佳的模块化设计，将模型实现、工具函数与实验配置彻底解耦。

### 核心组件
- **Frozen Backbones**: 使用预训练且冻结的 ViT/SigLIP (Vision) 和 LLaMA (Language)。
- **Trainable Interface**: 轻量级适配层，负责多模态对齐。
- **Config-Driven**: 通过 YAML 零代码切换模型变体。

## 2. 技术栈矩阵
- **框架**: PyTorch (深度学习基石)
- **生态**: Hugging Face Transformers (模型接入)
- **效率工具**: Einops (优雅的张量操作), Tqdm (进度追踪)

## 3. 代码结构走势
```
Prismer/
├── prismer/           # 主包
│   ├── modeling/      # 核心逻辑 (prismer.py)
│   └── utils/         # 辅助功能
└── configs/           # YAML 配置集
```

## 4. 关键亮点
- **90%+ 训练参数缩减**: 通过冻结骨干网络，极大降低计算门槛。
- **即插即用**: 遵循标准 Python 包规范，易于二次开发。
