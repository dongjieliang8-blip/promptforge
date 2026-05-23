"""Optimizer Agent: 迭代优化提示词，平衡效果与Token消耗"""

import json
import os
from pathlib import Path


class OptimizerAgent:
    def __init__(self, api_provider: str = "claude"):
        self.api_provider = api_provider

    def optimize(self, current_prompt: str, test_result: dict, max_iterations: int = 3) -> dict:
        """迭代优化提示词"""
        best_prompt = current_prompt
        best_score = test_result.get("optimized_avg_score", 5.0)
        history = []

        for i in range(max_iterations):
            # 根据上一轮测试结果调整策略
            improvement = test_result.get("improvement", 0)

            if improvement > 0.1:
                # 效果好，保持结构，微调细节
                candidate = self._fine_tune(best_prompt, "detail")
            elif improvement > 0:
                # 有提升但不大，尝试增强
                candidate = self._enhance(best_prompt, test_result)
            else:
                # 无提升，尝试不同策略
                candidate = self._rethink(best_prompt, test_result)

            # Token效率检查
            token_efficiency = self._check_token_efficiency(candidate, best_prompt)
            if token_efficiency < 0.5:
                candidate = self._compress(candidate)

            # 模拟评估候选方案
            candidate_score = self._evaluate_candidate(candidate, test_result)

            iteration_result = {
                "iteration": i + 1,
                "score": candidate_score,
                "token_efficiency": token_efficiency,
                "action": "detail" if improvement > 0.1 else ("enhance" if improvement > 0 else "rethink"),
            }
            history.append(iteration_result)

            if candidate_score > best_score:
                best_prompt = candidate
                best_score = candidate_score

        return {
            "optimized_prompt": best_prompt,
            "final_score": best_score,
            "iterations": max_iterations,
            "history": history,
            "token_usage": self._estimate_tokens(best_prompt),
        }

    def _fine_tune(self, prompt: str, mode: str) -> str:
        """微调：调整措辞和示例"""
        lines = prompt.split("\n")
        refined_lines = []
        for line in lines:
            # 移除冗余表述
            if "另外" in line and "此外" in line:
                line = line.replace("另外", "").strip()
            # 统一标点
            line = line.replace("。。", "。").replace(",,", ",")
            refined_lines.append(line)
        return "\n".join(refined_lines)

    def _enhance(self, prompt: str, test_result: dict) -> str:
        """增强：添加更具体的指令"""
        enhancement = "\n\n【优化补充】\n- 确保输出的完整性和准确性\n- 如遇模糊输入，优先选择保守策略"
        if "【优化补充】" not in prompt:
            return f"{prompt}{enhancement}"
        return prompt

    def _rethink(self, prompt: str, test_result: dict) -> str:
        """重构：重新组织提示词结构"""
        # 尝试将提示词分为更清晰的模块
        if "【" in prompt:
            return prompt  # 已经是结构化的

        parts = prompt.split("\n\n")
        if len(parts) >= 2:
            header = parts[0]
            body = "\n\n".join(parts[1:])
            return f"## 核心指令\n{header}\n\n## 详细要求\n{body}"
        return prompt

    def _compress(self, prompt: str) -> str:
        """压缩：在保持语义的前提下减少Token消耗"""
        lines = prompt.split("\n")
        compressed = []
        prev_empty = False

        for line in lines:
            stripped = line.strip()
            if not stripped:
                if not prev_empty:
                    compressed.append("")
                prev_empty = True
                continue
            prev_empty = False

            # 移除冗余修饰词
            stripped = stripped.replace("非常", "").replace("十分", "").replace("特别", "")
            compressed.append(stripped)

        return "\n".join(compressed)

    def _check_token_efficiency(self, new_prompt: str, old_prompt: str) -> float:
        """检查Token效率：新提示词相比旧提示词的Token效率"""
        new_tokens = self._estimate_tokens(new_prompt)
        old_tokens = self._estimate_tokens(old_prompt)

        if old_tokens == 0:
            return 1.0

        # 理想情况下，新提示词不应比旧提示词长太多
        ratio = new_tokens / old_tokens
        if ratio <= 1.0:
            return 1.0
        elif ratio <= 1.2:
            return 0.8
        elif ratio <= 1.5:
            return 0.6
        else:
            return 0.4

    def _estimate_tokens(self, text: str) -> int:
        """估算Token数量（中文约1.5字/token，英文约4字符/token）"""
        chinese_chars = sum(1 for c in text if '一' <= c <= '鿿')
        other_chars = len(text) - chinese_chars
        return int(chinese_chars * 1.5 + other_chars / 4)

    def _evaluate_candidate(self, candidate: str, test_result: dict) -> float:
        """评估候选提示词的质量"""
        base_score = test_result.get("optimized_avg_score", 5.0)

        # 结构优化加分
        structure_bonus = 0
        if "【" in candidate and "】" in candidate:
            structure_bonus += 0.2
        if any(kw in candidate for kw in ["示例", "Example"]):
            structure_bonus += 0.1

        # 长度合理性
        length_bonus = 0
        token_count = self._estimate_tokens(candidate)
        if 100 < token_count < 1500:
            length_bonus = 0.2
        elif token_count > 3000:
            length_bonus = -0.3  # 过长惩罚

        return round(base_score + structure_bonus + length_bonus, 2)
