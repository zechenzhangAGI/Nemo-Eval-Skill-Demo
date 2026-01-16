#!/bin/bash
# Run GPQA Diamond evaluation on multiple Llama 3.1 model sizes
# and compare results

set -e

cd "$(dirname "$0")"

# Load environment variables
source .env
export NGC_API_KEY HF_TOKEN

# Activate virtual environment
source venv/bin/activate

MODELS=("llama-8b" "llama-70b" "llama-405b")

echo "=============================================="
echo "GPQA Diamond Model Comparison Study"
echo "=============================================="
echo ""

# Run evaluation for each model
for model in "${MODELS[@]}"; do
    echo "----------------------------------------------"
    echo "Running evaluation for: $model"
    echo "----------------------------------------------"

    config_file="configs/${model}.yaml"

    if [ ! -f "$config_file" ]; then
        echo "Error: Config file not found: $config_file"
        continue
    fi

    echo "Config: $config_file"
    echo "Output: results/${model}/"
    echo ""

    nemo-evaluator-launcher run --config "$config_file"

    echo ""
    echo "Completed: $model"
    echo ""
done

echo "=============================================="
echo "All evaluations complete!"
echo "=============================================="
echo ""

# Run comparison analysis
echo "Running comparison analysis..."
python analysis/compare_models.py --results-dir results --output analysis/comparison.json

echo ""
echo "Done! Results saved to analysis/comparison.json"
