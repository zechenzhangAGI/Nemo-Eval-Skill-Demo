#!/usr/bin/env python3
"""
Compare GPQA Diamond results across Llama 3.1 model sizes.
Analyzes what questions each model gets right/wrong and finds patterns.
Tracks format failures as a separate metric.
"""

import json
import re
import os
from pathlib import Path
from collections import defaultdict
import argparse


def parse_html_report(html_path: Path) -> list:
    """Parse the HTML report to extract per-question results."""
    questions = []

    with open(html_path, 'r') as f:
        content = f.read()

    # Split by <hr> to get individual questions
    sections = content.split('<hr>')

    for section in sections:
        if 'Correct Answer:' not in section:
            continue

        # Extract question text
        question_match = re.search(r'<pre>(.*?)</pre>', section, re.DOTALL)
        question_text = question_match.group(1) if question_match else ""

        # Extract model response
        response_matches = re.findall(r'<pre>(.*?)</pre>', section, re.DOTALL)
        response_text = response_matches[1] if len(response_matches) > 1 else ""

        # Extract correct answer
        correct_match = re.search(r'Correct Answer: ([A-D])', section)
        correct_answer = correct_match.group(1) if correct_match else None

        # Extract model's extracted answer
        extracted_match = re.search(r'Extracted Answer: ([A-D]|None)', section)
        extracted_answer = extracted_match.group(1) if extracted_match else None
        if extracted_answer == "None":
            extracted_answer = None

        # Extract score
        score_match = re.search(r'Score: ([0-9.]+)', section)
        score = float(score_match.group(1)) if score_match else 0.0

        questions.append({
            "question": question_text[:200] + "..." if len(question_text) > 200 else question_text,
            "response": response_text,
            "correct_answer": correct_answer,
            "extracted_answer": extracted_answer,
            "score": score,
            "format_failure": extracted_answer is None
        })

    return questions


def load_results(results_dir: Path) -> dict:
    """Load evaluation results from a model's results directory."""
    # Find the latest run directory
    run_dirs = sorted(results_dir.glob("*/gpqa_diamond/artifacts"))
    if not run_dirs:
        return None

    latest = run_dirs[-1]

    results = {
        "metrics": None,
        "questions": [],
        "format_failures": 0,
        "total_questions": 0
    }

    # Load metrics
    metrics_file = latest / "gpqa_diamond" / "gpqa_diamond.json"
    if metrics_file.exists():
        with open(metrics_file) as f:
            results["metrics"] = json.load(f)

    # Load detailed results from HTML report
    html_file = latest / "gpqa_diamond" / "gpqa_diamond.html"
    if html_file.exists():
        results["questions"] = parse_html_report(html_file)
        results["total_questions"] = len(results["questions"])
        results["format_failures"] = sum(1 for q in results["questions"] if q["format_failure"])

    return results


def compare_models(results_base: Path, models: list) -> dict:
    """Compare results across multiple models."""
    all_results = {}

    for model in models:
        model_dir = results_base / model
        if model_dir.exists():
            all_results[model] = load_results(model_dir)
            if all_results[model]:
                print(f"Loaded {model}: {all_results[model]['total_questions']} questions")
        else:
            print(f"Warning: No results found for {model}")

    return all_results


def analyze_patterns(all_results: dict) -> dict:
    """Analyze patterns in model performance."""
    analysis = {
        "scores": {},
        "format_failures": {},
        "format_failure_rate": {},
        "correct_counts": {},
        "all_correct": [],      # Questions all models got right
        "all_wrong": [],        # Questions all models got wrong
        "only_large_correct": [], # Questions only 405B got right
        "size_scaling": [],     # Questions where larger = better
        "per_question": []
    }

    # Get scores and format failures
    for model, results in all_results.items():
        if results and results["metrics"]:
            analysis["scores"][model] = results["metrics"].get("score", 0)
            analysis["format_failures"][model] = results["format_failures"]
            analysis["format_failure_rate"][model] = results["format_failures"] / results["total_questions"] if results["total_questions"] > 0 else 0
            analysis["correct_counts"][model] = sum(1 for q in results["questions"] if q["score"] == 1.0)

    # Compare per-question results across models
    models_with_results = [m for m in all_results if all_results[m] and all_results[m]["questions"]]

    if len(models_with_results) >= 2:
        # Use the model with most questions as reference
        ref_model = max(models_with_results, key=lambda m: len(all_results[m]["questions"]))
        ref_questions = all_results[ref_model]["questions"]

        for i, ref_q in enumerate(ref_questions):
            q_analysis = {
                "index": i,
                "correct_answer": ref_q["correct_answer"],
                "question_preview": ref_q["question"][:100],
                "results": {}
            }

            for model in models_with_results:
                if i < len(all_results[model]["questions"]):
                    q = all_results[model]["questions"][i]
                    q_analysis["results"][model] = {
                        "extracted": q["extracted_answer"],
                        "correct": q["score"] == 1.0,
                        "format_failure": q["format_failure"]
                    }

            analysis["per_question"].append(q_analysis)

            # Categorize question
            results_by_model = q_analysis["results"]
            if all(r.get("correct", False) for r in results_by_model.values()):
                analysis["all_correct"].append(i)
            elif not any(r.get("correct", False) for r in results_by_model.values()):
                analysis["all_wrong"].append(i)
            elif results_by_model.get("llama-405b", {}).get("correct") and not results_by_model.get("llama-8b", {}).get("correct"):
                analysis["only_large_correct"].append(i)

    return analysis


def print_comparison(all_results: dict, analysis: dict):
    """Print a formatted comparison of model results."""
    print("\n" + "="*70)
    print("GPQA Diamond Model Comparison")
    print("="*70)

    # Print scores
    print("\n## Overall Scores\n")
    print(f"{'Model':<15} {'Score':<10} {'Correct':<10} {'Format Fail':<12} {'Fail Rate':<10}")
    print("-"*57)
    for model in ["llama-8b", "llama-70b", "llama-405b"]:
        if model in analysis["scores"]:
            score = analysis["scores"][model]
            correct = analysis["correct_counts"].get(model, 0)
            fmt_fail = analysis["format_failures"].get(model, 0)
            fmt_rate = analysis["format_failure_rate"].get(model, 0)
            print(f"{model:<15} {score*100:>6.1f}%    {correct:<10} {fmt_fail:<12} {fmt_rate*100:>6.1f}%")
        else:
            print(f"{model:<15} {'N/A':<10} {'N/A':<10} {'N/A':<12} {'N/A':<10}")

    # Print pattern analysis
    print("\n## Question Patterns\n")
    print(f"All models correct:     {len(analysis['all_correct'])} questions")
    print(f"All models wrong:       {len(analysis['all_wrong'])} questions")
    print(f"Only 405B correct:      {len(analysis['only_large_correct'])} questions")

    # Show examples of questions only large model got right
    if analysis["only_large_correct"]:
        print("\n## Examples: Questions Only 405B Got Right\n")
        for idx in analysis["only_large_correct"][:5]:
            q = analysis["per_question"][idx]
            print(f"Q{idx}: {q['question_preview']}...")
            print(f"   Correct: {q['correct_answer']}")
            for model, result in q["results"].items():
                status = "✓" if result["correct"] else ("∅" if result["format_failure"] else "✗")
                print(f"   {model}: {result['extracted']} {status}")
            print()

    print("="*70)


def export_comparison(all_results: dict, analysis: dict, output_file: Path):
    """Export comparison results to JSON."""
    export_data = {
        "scores": analysis["scores"],
        "format_failures": analysis["format_failures"],
        "format_failure_rate": analysis["format_failure_rate"],
        "correct_counts": analysis["correct_counts"],
        "models": list(all_results.keys()),
        "pattern_summary": {
            "all_correct": len(analysis["all_correct"]),
            "all_wrong": len(analysis["all_wrong"]),
            "only_large_correct": len(analysis["only_large_correct"])
        },
        "all_correct_indices": analysis["all_correct"],
        "all_wrong_indices": analysis["all_wrong"],
        "only_large_correct_indices": analysis["only_large_correct"],
        "per_question": analysis["per_question"]
    }

    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w') as f:
        json.dump(export_data, f, indent=2)

    print(f"\nExported comparison to: {output_file}")


def main():
    parser = argparse.ArgumentParser(description="Compare GPQA Diamond results across models")
    parser.add_argument("--results-dir", type=Path, default=Path("results"),
                        help="Base directory containing model results")
    parser.add_argument("--models", nargs="+", default=["llama-8b", "llama-70b", "llama-405b"],
                        help="Models to compare")
    parser.add_argument("--output", type=Path, default=Path("analysis/comparison.json"),
                        help="Output file for comparison results")

    args = parser.parse_args()

    # Load all results
    print("Loading results...")
    all_results = compare_models(args.results_dir, args.models)

    # Analyze patterns
    print("\nAnalyzing patterns...")
    analysis = analyze_patterns(all_results)

    # Print comparison
    print_comparison(all_results, analysis)

    # Export results
    export_comparison(all_results, analysis, args.output)


if __name__ == "__main__":
    main()
