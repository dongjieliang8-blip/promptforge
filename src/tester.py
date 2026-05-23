"""Tester Agent: 对比测试原始提示词与优化提示词的效果差异"""

import json
import os
import random
from pathlib import Path


class TesterAgent:
    def __init__(self, api_provider: str = "claude"):
        self.api_provider = api_provider

    def test(
        self,
        original_prompt: str,
        optimized_prompt: str,
        test_inputs: list,
        task_type: str,
    ) -> dict:
        """对比测试原始和优化后的提示词效果"""
        original_scores = []
        optimized_scores = []

        for test_input in test_inputs:
            # 模拟API调用评估（实际使用时替换为真实API调用）
            orig_score = self._evaluate_response(original_prompt, test_input, task_type)
            opt_score = self._evaluate_response(optimized_prompt, test_input, task_type)
            original_scores.append(orig_score)
            optimized_scores.append(opt_score)

        original_avg = sum(original_scores) / len(original_scores) if original_scores else 0
        optimized_avg = sum(optimized_scores) / len(optimized_scores) if optimized_scores else 0
        improvement = (optimized_avg - original_avg) / original_avg if original_avg > 0 else 0

        return {
            "original_avg_score": original_avg,
            "optimized_avg_score": optimized_avg,
            "improvement": improvement,
            "original_scores": original_scores,
            "optimized_scores": optimized_scores,
            "test_count": len(test_inputs),
            "test_inputs": test_inputs,
        }

    def _evaluate_response(self, prompt: str, test_input: str, task_type: str) -> float:
        """评估提示词在给定输入下的输出质量评分"""
        # 模拟评估逻辑：
        # 1. 提示词越长、结构越好，得分越高
        # 2. 包含示例的得分更高
        # 3. 有角色定义的得分更高

        score = 5.0  # 基础分

        # 结构加分
        if any(kw in prompt for kw in ["你是", "作为", "扮演", "You are"]):
            score += 0.5
        if any(kw in prompt for kw in ["【", "[", "##"]):
            score += 0.3
        if any(kw in prompt for kw in ["示例", "Example", "e.g."]):
            score += 0.4
        if any(kw in prompt for kw in ["输出格式", "格式", "JSON"]):
            score += 0.3

        # 长度加分（适度）
        if 100 < len(prompt) < 2000:
            score += 0.3
        elif len(prompt) >= 2000:
            score += 0.1  # 过长反而略减

        # 添加随机波动模拟真实评估
        score += random.uniform(-0.3, 0.3)

        return round(min(10.0, max(1.0, score)), 2)

    def test_with_api(self, original_prompt: str, optimized_prompt: str, test_inputs: list, task_type: str) -> dict:
        """使用真实API进行对比测试"""
        api_key = os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("DEEPSEEK_API_KEY")
        if not api_key:
            return self.test(original_prompt, optimized_prompt, test_inputs, task_type)

        # 使用Anthropic API
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=api_key)

            original_scores = []
            optimized_scores = []

            for test_input in test_inputs:
                # 测试原始提示词
                orig_response = client.messages.create(
                    model="claude-sonnet-4-20250514",
                    max_tokens=1024,
                    messages=[{"role": "user", "content": f"{original_prompt}\n\n输入：{test_input}"}],
                )
                orig_score = self._score_response(orig_response.content[0].text, task_type)
                original_scores.append(orig_score)

                # 测试优化提示词
                opt_response = client.messages.create(
                    model="claude-sonnet-4-20250514",
                    max_tokens=1024,
                    messages=[{"role": "user", "content": f"{optimized_prompt}\n\n输入：{test_input}"}],
                )
                opt_score = self._score_response(opt_response.content[0].text, task_type)
                optimized_scores.append(opt_score)

            original_avg = sum(original_scores) / len(original_scores)
            optimized_avg = sum(optimized_scores) / len(optimized_scores)

            return {
                "original_avg_score": original_avg,
                "optimized_avg_score": optimized_avg,
                "improvement": (optimized_avg - original_avg) / original_avg,
                "original_scores": original_scores,
                "optimized_scores": optimized_scores,
                "test_count": len(test_inputs),
                "test_inputs": test_inputs,
            }

        except Exception as e:
            print(f"    API调用失败，回退到模拟评估: {e}")
            return self.test(original_prompt, optimized_prompt, test_inputs, task_type)

    def _score_response(self, response: str, task_type: str) -> float:
        """对API返回的响应进行评分"""
        score = 5.0

        # 基于响应质量的启发式评分
        if len(response) > 50:
            score += 0.5
        if len(response) > 200:
            score += 0.3

        # 检查是否包含结构化输出
        if "{" in response and "}" in response:
            score += 0.5

        # 检查是否有错误信息
        error_indicators = ["error", "无法", "sorry", "抱歉", "不能"]
        if any(e in response.lower() for e in error_indicators):
            score -= 1.0

        score += random.uniform(-0.2, 0.2)
        return round(min(10.0, max(1.0, score)), 2)
