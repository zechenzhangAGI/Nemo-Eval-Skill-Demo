#!/usr/bin/env python3
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib_venn import venn3, venn3_circles
import json

# Load data
with open("/n/home04/zechenzhang/Nemo-Eval-Skill-Demo/analysis/model_results.json") as f:
    results = json.load(f)

# Get wrong answer sets for each model
wrong_8b = set(i for i, s in enumerate(results["8B"]["scores"]) if s == 0.0)
wrong_70b = set(i for i, s in enumerate(results["70B"]["scores"]) if s == 0.0)
wrong_405b = set(i for i, s in enumerate(results["405B"]["scores"]) if s == 0.0)

# Also get correct answer sets
correct_8b = set(i for i, s in enumerate(results["8B"]["scores"]) if s == 1.0)
correct_70b = set(i for i, s in enumerate(results["70B"]["scores"]) if s == 1.0)
correct_405b = set(i for i, s in enumerate(results["405B"]["scores"]) if s == 1.0)

# Create figure with two Venn diagrams
fig, axes = plt.subplots(1, 2, figsize=(16, 8))

# WRONG answers Venn diagram
ax1 = axes[0]
v1 = venn3([wrong_8b, wrong_70b, wrong_405b],
           set_labels=('Llama-3.1-8B-Instruct\n(144 wrong)',
                       'Llama-3.3-70B-Instruct\n(103 wrong)',
                       'Llama-3.1-405B-Instruct\n(93 wrong)'),
           ax=ax1)

# Style the Venn diagram
if v1:
    for text in v1.set_labels:
        if text:
            text.set_fontsize(11)
            text.set_fontweight('bold')
    for text in v1.subset_labels:
        if text:
            text.set_fontsize(12)
            text.set_fontweight('bold')

# Add circles outline
venn3_circles([wrong_8b, wrong_70b, wrong_405b], ax=ax1, linewidth=2)

ax1.set_title('WRONG Answers Overlap\n(Questions each model got WRONG)',
              fontsize=14, fontweight='bold', pad=20)

# CORRECT answers Venn diagram
ax2 = axes[1]
v2 = venn3([correct_8b, correct_70b, correct_405b],
           set_labels=('Llama-3.1-8B-Instruct\n(54 correct)',
                       'Llama-3.3-70B-Instruct\n(95 correct)',
                       'Llama-3.1-405B-Instruct\n(105 correct)'),
           ax=ax2)

# Style the Venn diagram
if v2:
    for text in v2.set_labels:
        if text:
            text.set_fontsize(11)
            text.set_fontweight('bold')
    for text in v2.subset_labels:
        if text:
            text.set_fontsize(12)
            text.set_fontweight('bold')

# Add circles outline
venn3_circles([correct_8b, correct_70b, correct_405b], ax=ax2, linewidth=2)

ax2.set_title('CORRECT Answers Overlap\n(Questions each model got RIGHT)',
              fontsize=14, fontweight='bold', pad=20)

plt.suptitle('Llama Model Comparison on GPQA Diamond (198 questions)',
             fontsize=16, fontweight='bold', y=0.98)

plt.tight_layout()
plt.savefig('/n/home04/zechenzhang/Nemo-Eval-Skill-Demo/analysis/venn_diagrams.png',
            dpi=150, bbox_inches='tight', facecolor='white')
print("Saved venn_diagrams.png")

# Also print the numbers for verification
print("\nWRONG answers breakdown:")
print(f"  Only 8B wrong: {len(wrong_8b - wrong_70b - wrong_405b)}")
print(f"  Only 70B wrong: {len(wrong_70b - wrong_8b - wrong_405b)}")
print(f"  Only 405B wrong: {len(wrong_405b - wrong_8b - wrong_70b)}")
print(f"  8B & 70B wrong (not 405B): {len((wrong_8b & wrong_70b) - wrong_405b)}")
print(f"  8B & 405B wrong (not 70B): {len((wrong_8b & wrong_405b) - wrong_70b)}")
print(f"  70B & 405B wrong (not 8B): {len((wrong_70b & wrong_405b) - wrong_8b)}")
print(f"  ALL THREE wrong: {len(wrong_8b & wrong_70b & wrong_405b)}")

print("\nCORRECT answers breakdown:")
print(f"  Only 8B correct: {len(correct_8b - correct_70b - correct_405b)}")
print(f"  Only 70B correct: {len(correct_70b - correct_8b - correct_405b)}")
print(f"  Only 405B correct: {len(correct_405b - correct_8b - correct_70b)}")
print(f"  8B & 70B correct (not 405B): {len((correct_8b & correct_70b) - correct_405b)}")
print(f"  8B & 405B correct (not 70B): {len((correct_8b & correct_405b) - correct_70b)}")
print(f"  70B & 405B correct (not 8B): {len((correct_70b & correct_405b) - correct_8b)}")
print(f"  ALL THREE correct: {len(correct_8b & correct_70b & correct_405b)}")
