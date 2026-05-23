"""
PromptForge — 多Agent协作提示词工程优化流水线

Analyzer → Designer → Tester → Optimizer
"""

import json
import sys
from pathlib import Path

from .analyzer import AnalyzerAgent
from .designer import DesignerAgent
from .tester import TesterAgent
from .optimizer import OptimizerAgent


class PromptForgePipeline:
    def __init__(self, api_provider: str = "claude"):
        self.analyzer = AnalyzerAgent(api_provider)
        self.designer = DesignerAgent(api_provider)
        self.tester = TesterAgent(api_provider)
        self.optimizer = OptimizerAgent(api_provider)

    def run(self, project_path: str):
        print("=" * 60)
        print("PromptForge — 提示词工程优化流水线")
        print("=" * 60)

        # 加载任务配置
        config = self._load_config(project_path)
        original_prompt = config.get("prompt", "")
        task_type = config.get("task_type", "general")
        domain = config.get("domain", "general")
        test_inputs = config.get("test_inputs", [])
        max_iterations = config.get("max_iterations", 3)

        print(f"  任务类型: {task_type}")
        print(f"  领域: {domain}")
        print(f"  提示词长度: {len(original_prompt)} 字符")

        # Step 1: 提示词分析
        print(f"\n[1/4] Analyzer Agent: 分析提示词结构与质量...")
        analysis = self.analyzer.analyze(original_prompt, task_type, domain)
        print(f"  结构评分: {analysis['structure_score']:.2f}")
        print(f"  语义评分: {analysis['semantic_score']:.2f}")
        print(f"  发现问题: {len(analysis['issues'])} 个")

        # Step 2: 方案设计
        print(f"\n[2/4] Designer Agent: 设计优化方案...")
        design = self.designer.design(analysis, original_prompt, task_type)
        optimized_prompt = design["optimized_prompt"]
        print(f"  优化策略: {', '.join(design['strategies'])}")
        print(f"  新提示词长度: {len(optimized_prompt)} 字符")

        # Step 3: 效果测试
        print(f"\n[3/4] Tester Agent: 对比测试原始与优化提示词...")
        test_result = self.tester.test(
            original_prompt, optimized_prompt, test_inputs, task_type
        )
        print(f"  原始平均分: {test_result['original_avg_score']:.2f}")
        print(f"  优化平均分: {test_result['optimized_avg_score']:.2f}")
        print(f"  提升幅度: {test_result['improvement']:.2%}")

        # Step 4: 迭代优化
        print(f"\n[4/4] Optimizer Agent: 迭代优化提示词...")
        final_result = self.optimizer.optimize(
            optimized_prompt, test_result, max_iterations
        )
        print(f"  迭代次数: {final_result['iterations']}")
        print(f"  最终评分: {final_result['final_score']:.2f}")

        # 输出完整报告
        report = {
            "config": config,
            "analysis": analysis,
            "design": design,
            "test_result": test_result,
            "final_result": final_result,
            "original_prompt": original_prompt,
            "final_prompt": final_result["optimized_prompt"],
        }

        output_path = Path(project_path) / "output" / "report.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        # 保存最终优化后的提示词
        prompt_path = Path(project_path) / "output" / "optimized_prompt.txt"
        with open(prompt_path, "w", encoding="utf-8") as f:
            f.write(final_result["optimized_prompt"])

        print("\n" + "=" * 60)
        print(f"流水线完成!")
        print(f"  报告: {output_path}")
        print(f"  优化提示词: {prompt_path}")
        print("=" * 60)

        return report

    def _load_config(self, project_path: str) -> dict:
        config_path = Path(project_path) / "config.json"
        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                return json.load(f)

        return {
            "task_type": "general",
            "domain": "general",
            "prompt": "请帮我完成以下任务：",
            "test_inputs": ["示例输入1", "示例输入2"],
            "max_iterations": 3,
        }


def main():
    if len(sys.argv) < 3 or sys.argv[1] != "run":
        print("用法: python -m src.main run <project_path> [--provider claude|deepseek]")
        sys.exit(1)

    project_path = sys.argv[2]
    provider = "claude"
    if "--provider" in sys.argv:
        idx = sys.argv.index("--provider")
        if idx + 1 < len(sys.argv):
            provider = sys.argv[idx + 1]

    pipeline = PromptForgePipeline(api_provider=provider)
    pipeline.run(project_path)


if __name__ == "__main__":
    main()
