# PromptForge — 多Agent协作提示词工程优化流水线

基于 Claude Code / DeepSeek API 的多智能体提示词优化流水线，实现提示词分析→方案设计→效果测试→迭代优化的全自动化闭环。

## 架构

```
Analyzer → Designer → Tester → Optimizer
```

## 安装

```bash
pip install -r requirements.txt
```

## 使用

```bash
python -m src.main run ./demo/sample_task
```

## Agent 说明

- **Analyzer**: 分析现有提示词结构、语义完整性和潜在问题
- **Designer**: 基于分析结果，设计优化后的提示词方案
- **Tester**: 对比测试原始提示词与优化提示词的效果差异
- **Optimizer**: 迭代优化提示词，平衡效果与Token消耗

## 技术栈

- Python
- Claude Code / DeepSeek API
- Jinja2 模板引擎

## License

MIT
