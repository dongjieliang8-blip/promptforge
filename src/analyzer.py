"""Analyzer Agent: 分析提示词结构、语义完整性和潜在问题"""

import json
import os
from pathlib import Path


class AnalyzerAgent:
    def __init__(self, api_provider: str = "claude"):
        self.api_provider = api_provider

    def analyze(self, prompt: str, task_type: str, domain: str) -> dict:
        """分析提示词质量，返回评分和问题列表"""
        issues = []
        suggestions = []

        # 结构分析
        structure_score = self._analyze_structure(prompt, issues, suggestions)
        # 语义分析
        semantic_score = self._analyze_semantics(prompt, task_type, domain, issues, suggestions)
        # 长度分析
        length_analysis = self._analyze_length(prompt)

        return {
            "structure_score": structure_score,
            "semantic_score": semantic_score,
            "overall_score": (structure_score + semantic_score) / 2,
            "issues": issues,
            "suggestions": suggestions,
            "length_analysis": length_analysis,
            "task_type": task_type,
            "domain": domain,
        }

    def _analyze_structure(self, prompt: str, issues: list, suggestions: list) -> float:
        score = 1.0

        # 检查是否有角色定义
        role_keywords = ["你是", "作为", "扮演", "You are", "Act as", "Role:"]
        has_role = any(kw in prompt for kw in role_keywords)
        if not has_role:
            issues.append("缺少角色定义（Role），建议添加明确的AI角色描述")
            suggestions.append("添加如：'你是一位资深的{领域}专家' 的角色设定")
            score -= 0.15

        # 检查是否有明确指令
        if len(prompt) < 20:
            issues.append("提示词过短，指令不够明确")
            suggestions.append("补充任务描述、输入格式和输出要求")
            score -= 0.2

        # 检查是否有输出格式要求
        format_keywords = ["格式", "输出", "返回", "JSON", "Markdown", "format", "output"]
        has_format = any(kw in prompt for kw in format_keywords)
        if not has_format:
            issues.append("缺少输出格式约束，可能导致输出不稳定")
            suggestions.append("添加明确的输出格式要求，如JSON结构或Markdown模板")
            score -= 0.1

        # 检查是否有示例
        example_keywords = ["例如", "示例", "例如：", "Example", "e.g.", "for instance"]
        has_examples = any(kw in prompt for kw in example_keywords)
        if not has_examples:
            suggestions.append("考虑添加Few-shot示例以提升输出一致性")
            score -= 0.05

        # 检查是否有约束条件
        constraint_keywords = ["不要", "避免", "必须", "确保", "注意", "do not", "must", "ensure"]
        has_constraints = any(kw in prompt for kw in constraint_keywords)
        if not has_constraints:
            suggestions.append("添加约束条件以限定输出范围")
            score -= 0.05

        return max(0.0, score)

    def _analyze_semantics(self, prompt: str, task_type: str, domain: str, issues: list, suggestions: list) -> float:
        score = 1.0

        # 检查提示词与任务类型的一致性
        task_type_hints = {
            "classification": ["分类", "类别", "属于", "classify", "category"],
            "extraction": ["提取", "抽取", "识别", "extract", "identify"],
            "generation": ["生成", "编写", "创作", "generate", "create", "write"],
            "summarization": ["总结", "概括", "摘要", "summarize", "summary"],
            "translation": ["翻译", "译", "translate"],
            "qa": ["回答", "问答", "Q&A", "answer", "question"],
            "code": ["代码", "编程", "程序", "code", "program", "implement"],
        }

        if task_type in task_type_hints:
            hints = task_type_hints[task_type]
            alignment = sum(1 for h in hints if h in prompt)
            if alignment == 0:
                issues.append(f"提示词内容与任务类型'{task_type}'对齐度不足")
                suggestions.append(f"在提示词中明确与{task_type}相关的关键词")
                score -= 0.15

        # 检查领域专业术语
        domain_terms = {
            "finance": ["金融", "财务", "投资", "风险"],
            "medical": ["医学", "临床", "诊断", "患者"],
            "legal": ["法律", "法规", "合同", "条款"],
            "education": ["教育", "教学", "学习", "课程"],
            "technology": ["技术", "系统", "架构", "开发"],
        }

        if domain in domain_terms:
            terms = domain_terms[domain]
            has_terms = any(t in prompt for t in terms)
            if not has_terms:
                suggestions.append(f"建议添加{domain}领域专业术语以提升领域适配性")
                score -= 0.05

        return max(0.0, score)

    def _analyze_length(self, prompt: str) -> dict:
        char_count = len(prompt)
        word_count = len(prompt.split())
        line_count = len(prompt.split("\n"))

        if char_count < 50:
            length_quality = "过短"
        elif char_count < 200:
            length_quality = "偏短"
        elif char_count < 2000:
            length_quality = "适中"
        elif char_count < 5000:
            length_quality = "偏长"
        else:
            length_quality = "过长"

        return {
            "char_count": char_count,
            "word_count": word_count,
            "line_count": line_count,
            "quality": length_quality,
        }
