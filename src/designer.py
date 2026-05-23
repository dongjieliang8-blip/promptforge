"""Designer Agent: 基于分析结果设计优化后的提示词方案"""

import json
import os
from pathlib import Path


class DesignerAgent:
    def __init__(self, api_provider: str = "claude"):
        self.api_provider = api_provider

    def design(self, analysis: dict, original_prompt: str, task_type: str) -> dict:
        """根据分析结果设计优化方案"""
        strategies = []
        optimized = original_prompt

        # 根据问题列表选择优化策略
        for issue in analysis.get("issues", []):
            if "角色" in issue:
                optimized = self._add_role(optimized, task_type)
                strategies.append("角色定义增强")
            elif "格式" in issue:
                optimized = self._add_format_constraint(optimized, task_type)
                strategies.append("输出格式约束")
            elif "过短" in issue:
                optimized = self._expand_prompt(optimized, task_type, analysis.get("domain", "general"))
                strategies.append("内容扩展")

        # 根据建议选择增强策略
        for suggestion in analysis.get("suggestions", []):
            if "示例" in suggestion and "Few-shot" in suggestion:
                optimized = self._add_fewshot(optimized, task_type)
                strategies.append("Few-shot示例")
            elif "约束" in suggestion:
                optimized = self._add_constraints(optimized, task_type)
                strategies.append("约束条件")
            elif "专业术语" in suggestion:
                optimized = self._enhance_domain(optimized, analysis.get("domain", "general"))
                strategies.append("领域增强")

        # 结构化重组
        optimized = self._restructure(optimized, task_type)
        strategies.append("结构化重组")

        # 去重策略
        strategies = list(dict.fromkeys(strategies))

        return {
            "optimized_prompt": optimized,
            "strategies": strategies,
            "original_length": len(original_prompt),
            "optimized_length": len(optimized),
        }

    def _add_role(self, prompt: str, task_type: str) -> str:
        role_map = {
            "classification": "你是一位资深的数据分类专家，擅长对文本进行精准分类。",
            "extraction": "你是一位专业的信息抽取专家，擅长从文本中提取结构化信息。",
            "generation": "你是一位创意写作专家，擅长生成高质量的原创内容。",
            "summarization": "你是一位专业的文本摘要专家，擅长提炼核心要点。",
            "translation": "你是一位专业的翻译专家，擅长中英文高质量翻译。",
            "qa": "你是一位知识渊博的问答专家，擅长给出准确、全面的回答。",
            "code": "你是一位资深的软件工程师，擅长编写高质量代码。",
            "general": "你是一位专业的AI助手，擅长理解用户意图并提供高质量输出。",
        }

        role = role_map.get(task_type, role_map["general"])
        return f"{role}\n\n{prompt}"

    def _add_format_constraint(self, prompt: str, task_type: str) -> str:
        format_map = {
            "classification": "\n\n【输出格式】\n请以JSON格式输出，包含字段：label（分类标签）, confidence（置信度0-1）, reason（判断理由）。",
            "extraction": "\n\n【输出格式】\n请以JSON格式输出提取结果，字段名使用英文，值为提取到的内容。",
            "generation": "\n\n【输出格式】\n请直接输出生成内容，不需要额外说明。",
            "summarization": "\n\n【输出格式】\n请以结构化方式输出摘要，包含：核心观点（1-3条）、详细摘要、关键词。",
            "translation": "\n\n【输出格式】\n请直接输出翻译结果，保持原文段落结构。",
            "qa": "\n\n【输出格式】\n请先给出直接回答，再提供详细解释和参考依据。",
            "code": "\n\n【输出格式】\n请输出完整可运行的代码，包含必要的注释。",
            "general": "\n\n【输出格式】\n请以清晰的结构输出结果。",
        }
        fmt = format_map.get(task_type, format_map["general"])
        return f"{prompt}{fmt}"

    def _add_fewshot(self, prompt: str, task_type: str) -> str:
        examples = {
            "classification": "\n\n【示例】\n输入：这家公司的季度财报显示营收增长30%\n输出：{\"label\": \"positive\", \"confidence\": 0.92, \"reason\": \"营收增长30%为正面财务指标\"}",
            "extraction": "\n\n【示例】\n输入：张三于2024年3月15日入职，担任高级工程师\n输出：{\"name\": \"张三\", \"date\": \"2024-03-15\", \"title\": \"高级工程师\"}",
            "translation": "\n\n【示例】\n输入：人工智能正在改变世界\n输出：Artificial intelligence is transforming the world.",
            "qa": "\n\n【示例】\n问：什么是机器学习？\n答：机器学习是人工智能的一个分支，它使计算机能够从数据中学习，而无需显式编程。核心思想是通过算法从数据中发现模式并做出预测或决策。",
            "code": "\n\n【示例】\n需求：计算斐波那契数列第n项\ncode:\ndef fibonacci(n):\n    if n <= 1:\n        return n\n    a, b = 0, 1\n    for _ in range(2, n + 1):\n        a, b = b, a + b\n    return b",
        }

        example = examples.get(task_type, "")
        if example:
            return f"{prompt}{example}"
        return prompt

    def _add_constraints(self, prompt: str, task_type: str) -> str:
        constraints = "\n\n【约束条件】\n- 不要编造不确定的信息\n- 不要输出与任务无关的内容\n- 保持输出的专业性和准确性"
        return f"{prompt}{constraints}"

    def _expand_prompt(self, prompt: str, task_type: str, domain: str) -> str:
        expanded = f"""【任务说明】
{prompt}

【输入要求】
请接收用户输入的原始内容作为处理对象。

【处理规则】
1. 仔细理解输入内容的意图和上下文
2. 根据任务要求进行相应处理
3. 确保输出的准确性和完整性

【质量要求】
- 输出必须专业、准确
- 如有不确定之处，请明确标注
- 保持输出的一致性和可复用性"""
        return expanded

    def _enhance_domain(self, prompt: str, domain: str) -> str:
        domain_notes = {
            "finance": "注意使用金融领域专业术语，确保财务数据的准确性。",
            "medical": "注意使用医学规范术语，确保信息的严谨性。",
            "legal": "注意法律条文的准确性，避免歧义表述。",
            "education": "注意教学内容的适龄性和科学性。",
            "technology": "注意技术术语的准确使用，确保方案的可行性。",
        }

        note = domain_notes.get(domain, "")
        if note:
            return f"{prompt}\n\n【领域注意】{note}"
        return prompt

    def _restructure(self, prompt: str, task_type: str) -> str:
        """将提示词重组为结构化格式"""
        # 如果已经包含结构化标记，则不再重组
        if any(marker in prompt for marker in ["【", "[", "##", "Role:", "Task:"]):
            return prompt

        parts = prompt.split("\n\n", 1)
        if len(parts) == 2:
            return f"{parts[0]}\n\n{parts[1]}"
        return prompt
