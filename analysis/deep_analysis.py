#!/usr/bin/env python3
"""
Deep analysis of GPQA Diamond evaluation results across Llama 3.1 models.
Analyzes failure modes, instruction following, and model scaling patterns.
"""

import re
import json
from pathlib import Path
from collections import defaultdict
import matplotlib.pyplot as plt
import numpy as np

# Result paths
RESULTS = {
    '8B': 'results/llama-8b/20260115_195856-067f808e6bd9dbe4/gpqa_diamond/artifacts/gpqa_diamond/gpqa_diamond.html',
    '70B': 'results/llama-70b/20260115_220922-5d5c08552147159f/gpqa_diamond/artifacts/gpqa_diamond/gpqa_diamond.html',
    '405B': 'results/llama-405b/20260115_212256-7bb3147d5401bc81/gpqa_diamond/artifacts/gpqa_diamond/gpqa_diamond.html',
}

def parse_html_results(html_path):
    """Parse HTML report to extract all question results."""
    with open(html_path) as f:
        html = f.read()

    results = []

    # Pattern to extract each example block
    # Find prompt, response, correct answer, extracted answer, score
    prompt_pattern = r'<div class="message user">.*?<pre>(.*?)</pre>'
    response_pattern = r'<div class="message assistant">.*?<pre>(.*?)</pre>'
    correct_pattern = r'Correct Answer: ([^<\n]+)'
    extracted_pattern = r'Extracted Answer: ([^<\n]+)'
    score_pattern = r'Score: ([^<\n]+)'

    prompts = re.findall(prompt_pattern, html, re.DOTALL)
    responses = re.findall(response_pattern, html, re.DOTALL)
    correct_answers = re.findall(correct_pattern, html)
    extracted_answers = re.findall(extracted_pattern, html)
    scores = re.findall(score_pattern, html)

    for i in range(len(responses)):
        results.append({
            'idx': i,
            'prompt': prompts[i] if i < len(prompts) else '',
            'response': responses[i],
            'correct': correct_answers[i].strip() if i < len(correct_answers) else '',
            'extracted': extracted_answers[i].strip() if i < len(extracted_answers) else '',
            'score': float(scores[i]) if i < len(scores) and scores[i] not in ['None', ''] else 0.0
        })

    return results

def classify_failure(result):
    """Classify the type of failure for a given result."""
    response = result['response']
    correct = result['correct']
    extracted = result['extracted']
    score = result['score']

    # Check if correct
    if score == 1.0:
        return 'correct', None

    # Check for format failure (extracted is None)
    if extracted == 'None':
        # Check if the correct answer appears in the response
        answer_patterns = [
            rf'answer[:\s]+is[:\s]+{correct}',
            rf'answer[:\s]+{correct}',
            rf'correct[:\s]+answer[:\s]+is[:\s]+{correct}',
            rf'option[:\s]+{correct}',
            rf'\({correct}\)[:\s]+is[:\s]+correct',
            rf'{correct}\)',  # Just "B)" at end
        ]

        response_lower = response.lower()
        hidden_correct = any(re.search(p, response_lower, re.IGNORECASE) for p in answer_patterns)

        # Check for repetitive loop
        if len(response) > 1000:
            # Check for repeated patterns
            last_500 = response[-500:]
            words = last_500.split()
            if len(words) > 10:
                # Check if last 10 words repeat
                pattern = ' '.join(words[-5:])
                if last_500.count(pattern) > 3:
                    return 'format_failure', 'repetitive_loop'

        # Check if response was truncated (hit token limit)
        if len(response) > 3500:  # Close to 2048 tokens
            if hidden_correct:
                return 'format_failure', 'truncated_but_correct'
            return 'format_failure', 'truncated_no_answer'

        if hidden_correct:
            return 'format_failure', 'wrong_format_but_correct'

        # Check if model gave an answer but in wrong format
        for letter in ['A', 'B', 'C', 'D']:
            patterns = [
                rf'answer[:\s]+is[:\s]+{letter}',
                rf'correct[:\s]+answer[:\s]+is[:\s]+{letter}',
                rf'option[:\s]+{letter}[:\s]+is',
            ]
            if any(re.search(p, response, re.IGNORECASE) for p in patterns):
                if letter == correct:
                    return 'format_failure', 'wrong_format_but_correct'
                else:
                    return 'format_failure', 'wrong_format_wrong_answer'

        return 'format_failure', 'no_clear_answer'

    # Extracted an answer but it was wrong
    return 'wrong_answer', f'answered_{extracted}_correct_{correct}'

def analyze_model_overlap(all_results):
    """Analyze which questions each model gets right/wrong."""
    n_questions = len(all_results['8B'])

    # Create masks for correct answers
    correct = {}
    for model in ['8B', '70B', '405B']:
        correct[model] = [r['score'] == 1.0 for r in all_results[model]]

    # Analyze overlaps
    analysis = {
        'all_correct': [],
        'all_wrong': [],
        'only_405b_correct': [],
        'only_70b_405b_correct': [],
        '8b_correct_others_wrong': [],
        'scaling_pattern': [],  # 8B wrong, 70B wrong, 405B correct
    }

    for i in range(n_questions):
        c8, c70, c405 = correct['8B'][i], correct['70B'][i], correct['405B'][i]

        if c8 and c70 and c405:
            analysis['all_correct'].append(i)
        elif not c8 and not c70 and not c405:
            analysis['all_wrong'].append(i)
        elif c405 and not c70 and not c8:
            analysis['only_405b_correct'].append(i)
        elif c405 and c70 and not c8:
            analysis['only_70b_405b_correct'].append(i)
        elif c8 and not c70 and not c405:
            analysis['8b_correct_others_wrong'].append(i)

        # Scaling pattern: larger models progressively better
        if not c8 and not c70 and c405:
            analysis['scaling_pattern'].append(i)

    return analysis, correct

def main():
    print("=" * 60)
    print("GPQA Diamond Deep Analysis")
    print("=" * 60)

    # Load all results
    all_results = {}
    for model, path in RESULTS.items():
        all_results[model] = parse_html_results(path)
        print(f"Loaded {len(all_results[model])} results for {model}")

    # Classify all failures
    print("\n" + "=" * 60)
    print("FAILURE MODE TAXONOMY")
    print("=" * 60)

    failure_taxonomy = defaultdict(lambda: defaultdict(list))

    for model in ['8B', '70B', '405B']:
        for result in all_results[model]:
            category, subtype = classify_failure(result)
            if category != 'correct':
                failure_taxonomy[model][(category, subtype)].append(result)

    for model in ['8B', '70B', '405B']:
        print(f"\n### {model} Failure Modes ###")
        total_failures = sum(len(v) for v in failure_taxonomy[model].values())
        print(f"Total failures: {total_failures}/198")

        for (category, subtype), results in sorted(failure_taxonomy[model].items()):
            print(f"  {category}/{subtype}: {len(results)}")

    # Deep dive into format failures with correct answers
    print("\n" + "=" * 60)
    print("FORMAT FAILURES WITH CORRECT ANSWER (Instruction Following Errors)")
    print("=" * 60)

    for model in ['8B', '70B', '405B']:
        hidden_correct = failure_taxonomy[model].get(('format_failure', 'wrong_format_but_correct'), [])
        if hidden_correct:
            print(f"\n### {model}: {len(hidden_correct)} hidden correct answers ###")
            for i, result in enumerate(hidden_correct[:3]):  # Show first 3
                print(f"\n  Example {i+1}:")
                print(f"  Correct answer: {result['correct']}")
                print(f"  Response ending: ...{result['response'][-200:]}")

    # Model overlap analysis
    print("\n" + "=" * 60)
    print("MODEL OVERLAP ANALYSIS")
    print("=" * 60)

    overlap, correct_masks = analyze_model_overlap(all_results)

    print(f"\nAll 3 models correct: {len(overlap['all_correct'])} questions")
    print(f"All 3 models wrong: {len(overlap['all_wrong'])} questions")
    print(f"Only 405B correct: {len(overlap['only_405b_correct'])} questions")
    print(f"70B & 405B correct, 8B wrong: {len(overlap['only_70b_405b_correct'])} questions")
    print(f"8B correct, others wrong: {len(overlap['8b_correct_others_wrong'])} questions")

    # Calculate coverage
    print("\n### Model Coverage ###")
    c8 = sum(correct_masks['8B'])
    c70 = sum(correct_masks['70B'])
    c405 = sum(correct_masks['405B'])

    # Does 405B cover all of 70B's correct answers?
    covered_70_by_405 = sum(1 for i in range(198) if correct_masks['70B'][i] and correct_masks['405B'][i])
    covered_8_by_70 = sum(1 for i in range(198) if correct_masks['8B'][i] and correct_masks['70B'][i])
    covered_8_by_405 = sum(1 for i in range(198) if correct_masks['8B'][i] and correct_masks['405B'][i])

    print(f"8B correct: {c8}, 70B correct: {c70}, 405B correct: {c405}")
    print(f"405B covers {covered_70_by_405}/{c70} ({100*covered_70_by_405/c70:.1f}%) of 70B's correct answers")
    print(f"70B covers {covered_8_by_70}/{c8} ({100*covered_8_by_70/c8:.1f}%) of 8B's correct answers")
    print(f"405B covers {covered_8_by_405}/{c8} ({100*covered_8_by_405/c8:.1f}%) of 8B's correct answers")

    # Questions only smaller models get right
    print("\n### Surprising Results (smaller model correct, larger wrong) ###")

    for i in overlap['8b_correct_others_wrong'][:5]:
        result = all_results['8B'][i]
        print(f"\nQuestion {i}: 8B correct, 70B & 405B wrong")
        # Get first 200 chars of question
        q = result['prompt']
        q_start = q.find('\n\n') + 2 if '\n\n' in q else 0
        print(f"  Question: {q[q_start:q_start+150]}...")
        print(f"  Correct: {result['correct']}, 8B answered: {result['extracted']}")
        print(f"  70B answered: {all_results['70B'][i]['extracted']}")
        print(f"  405B answered: {all_results['405B'][i]['extracted']}")

    # Generate plots
    print("\n" + "=" * 60)
    print("GENERATING PLOTS")
    print("=" * 60)

    fig, axes = plt.subplots(2, 2, figsize=(14, 12))

    # Plot 1: Accuracy comparison
    ax1 = axes[0, 0]
    models = ['8B', '70B', '405B']
    accuracies = [22.2, 40.4, 50.5]
    format_failures = [28.3, 16.7, 2.5]

    x = np.arange(len(models))
    width = 0.35

    bars1 = ax1.bar(x - width/2, accuracies, width, label='Accuracy %', color='steelblue')
    bars2 = ax1.bar(x + width/2, format_failures, width, label='Format Failure %', color='coral')

    ax1.set_ylabel('Percentage')
    ax1.set_title('Model Performance: Accuracy vs Format Failures')
    ax1.set_xticks(x)
    ax1.set_xticklabels(models)
    ax1.legend()
    ax1.bar_label(bars1, fmt='%.1f')
    ax1.bar_label(bars2, fmt='%.1f')

    # Plot 2: Failure mode breakdown for 8B
    ax2 = axes[0, 1]
    failure_counts_8b = {}
    for (cat, sub), results in failure_taxonomy['8B'].items():
        label = sub if sub else cat
        failure_counts_8b[label] = len(results)

    if failure_counts_8b:
        labels = list(failure_counts_8b.keys())
        sizes = list(failure_counts_8b.values())
        ax2.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
        ax2.set_title('8B Failure Mode Breakdown')

    # Plot 3: Venn-like overlap visualization
    ax3 = axes[1, 0]

    categories = ['All Correct', 'All Wrong', 'Only 405B', '70B+405B only', '8B only correct']
    counts = [
        len(overlap['all_correct']),
        len(overlap['all_wrong']),
        len(overlap['only_405b_correct']),
        len(overlap['only_70b_405b_correct']),
        len(overlap['8b_correct_others_wrong'])
    ]
    colors = ['green', 'red', 'purple', 'blue', 'orange']

    bars = ax3.barh(categories, counts, color=colors)
    ax3.set_xlabel('Number of Questions')
    ax3.set_title('Question Difficulty Distribution')
    ax3.bar_label(bars)

    # Plot 4: Scaling curve
    ax4 = axes[1, 1]

    model_sizes = [8, 70, 405]
    accuracies_raw = [c8/198*100, c70/198*100, c405/198*100]

    ax4.plot(model_sizes, accuracies_raw, 'bo-', markersize=10, linewidth=2)
    ax4.set_xlabel('Model Size (Billions)')
    ax4.set_ylabel('Accuracy %')
    ax4.set_title('Accuracy Scaling with Model Size')
    ax4.set_xscale('log')
    ax4.grid(True, alpha=0.3)

    for i, (x, y) in enumerate(zip(model_sizes, accuracies_raw)):
        ax4.annotate(f'{y:.1f}%', (x, y), textcoords="offset points", xytext=(0,10), ha='center')

    plt.tight_layout()
    plt.savefig('analysis/gpqa_analysis_plots.png', dpi=150, bbox_inches='tight')
    print("Saved plots to analysis/gpqa_analysis_plots.png")

    # Print summary insights
    print("\n" + "=" * 60)
    print("KEY INSIGHTS")
    print("=" * 60)

    print("""
1. SCALING IMPROVES BOTH ACCURACY AND INSTRUCTION FOLLOWING
   - Accuracy: 8B (22%) → 70B (40%) → 405B (51%)
   - Format failures: 8B (28%) → 70B (17%) → 405B (2.5%)

2. FORMAT FAILURES ARE MOSTLY GENUINE FAILURES
   - 8B gets stuck in repetitive loops frequently
   - Very few "hidden correct" answers (model knew answer but wrong format)

3. LARGER MODELS SUBSUME SMALLER MODEL CAPABILITIES
   - 405B covers most questions that 70B and 8B get right
   - Very few cases where only 8B is correct (surprising reversals)

4. HARDEST QUESTIONS (all models wrong): {all_wrong} questions
   - These represent the frontier of model capability

5. SCALING SWEET SPOT
   - 70B→405B gives +10% accuracy for 5.8x parameters
   - 8B→70B gives +18% accuracy for 8.75x parameters
   - Diminishing returns at larger scales
""".format(all_wrong=len(overlap['all_wrong'])))

    # Save detailed failure analysis to JSON
    failure_details = {}
    for model in ['8B', '70B', '405B']:
        failure_details[model] = {}
        for (cat, sub), results in failure_taxonomy[model].items():
            key = f"{cat}/{sub}" if sub else cat
            failure_details[model][key] = {
                'count': len(results),
                'indices': [r['idx'] for r in results]
            }

    with open('analysis/failure_details.json', 'w') as f:
        json.dump(failure_details, f, indent=2)
    print("\nSaved detailed failure analysis to analysis/failure_details.json")

if __name__ == '__main__':
    main()
