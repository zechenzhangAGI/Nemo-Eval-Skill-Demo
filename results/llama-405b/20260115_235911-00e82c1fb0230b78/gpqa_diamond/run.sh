# SPDX-FileCopyrightText: Copyright (c) 2025, NVIDIA CORPORATION. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


# check if docker exists
command -v docker >/dev/null 2>&1 || { echo 'docker not found'; exit 1; }

# Initialize: remove killed jobs file from previous runs
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
killed_jobs_file="$script_dir/killed_jobs.txt"
rm -f "$killed_jobs_file"

# Create all directories and stdout.log files upfront before any container starts

task_dir="/n/home04/zechenzhang/Nemo-Eval-Skill-Demo/results/llama-405b/20260115_235911-00e82c1fb0230b78/gpqa_diamond"
artifacts_dir="$task_dir/artifacts"
logs_dir="$task_dir/logs"

mkdir -m 777 -p "$task_dir"
mkdir -m 777 -p "$artifacts_dir"
mkdir -m 777 -p "$logs_dir"
# Create stdout.log file upfront
touch "$logs_dir/client_stdout.log"
chmod 666 "$logs_dir/client_stdout.log"



# 00e82c1fb0230b78.0 gpqa_diamond

task_dir="/n/home04/zechenzhang/Nemo-Eval-Skill-Demo/results/llama-405b/20260115_235911-00e82c1fb0230b78/gpqa_diamond"
artifacts_dir="$task_dir/artifacts"
logs_dir="$task_dir/logs"

mkdir -m 777 -p "$task_dir"
mkdir -m 777 -p "$artifacts_dir"
mkdir -m 777 -p "$logs_dir"

# Check if this job was killed
if [ -f "$killed_jobs_file" ] && grep -q "^00e82c1fb0230b78.0$" "$killed_jobs_file"; then
    echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) Job 00e82c1fb0230b78.0 (gpqa_diamond) was killed, skipping execution" | tee -a "$logs_dir/stdout.log"
else
    # Create pre-start stage file
    echo "$(date -u +%Y-%m-%dT%H:%M:%SZ)" > "$logs_dir/stage.pre-start"

    # Debug contents of the eval factory command's config
    # Contents of pre_cmd.sh

    # Contents of config_ef.yaml
    # config:
    #   output_dir: /results
    #   params:
    #     log_samples: true
    #     max_new_tokens: 16384
    #     parallelism: 3
    #     temperature: 0.6
    #   type: gpqa_diamond
    # metadata:
    #   launcher_resolved_config:
    #     deployment:
    #       type: none
    #     evaluation:
    #       nemo_evaluator_config:
    #         config:
    #           params:
    #             log_samples: true
    #             max_new_tokens: 16384
    #             parallelism: 3
    #             temperature: 0.6
    #       tasks:
    #       - env_vars:
    #           HF_TOKEN: HF_TOKEN
    #         name: gpqa_diamond
    #     execution:
    #       extra_docker_args: ''
    #       mode: sequential
    #       output_dir: ./results/llama-405b
    #       type: local
    #     target:
    #       api_endpoint:
    #         api_key_name: NGC_API_KEY
    #         model_id: meta/llama-3.1-405b-instruct
    #         url: https://integrate.api.nvidia.com/v1/chat/completions
    #   versioning:
    #     nemo_evaluator_launcher: 0.1.67
    # target:
    #   api_endpoint:
    #     api_key: API_KEY
    #     model_id: meta/llama-3.1-405b-instruct
    #     type: chat
    #     url: https://integrate.api.nvidia.com/v1/chat/completions

    # Docker run with eval factory command
    (
        echo "$(date -u +%Y-%m-%dT%H:%M:%SZ)" > "$logs_dir/stage.running"
        
        docker run --rm --shm-size=100g  \
        --name client-gpqa_diamond-20260115_235912_793783 \
      --volume "$artifacts_dir":/results \
      -e HF_TOKEN=$HF_TOKEN \
      -e API_KEY=$NGC_API_KEY \
      nvcr.io/nvidia/eval-factory/simple-evals:25.11 \
      bash -c '
        echo "" | base64 -d > pre_cmd.sh && echo "Y29uZmlnOgogIG91dHB1dF9kaXI6IC9yZXN1bHRzCiAgcGFyYW1zOgogICAgbG9nX3NhbXBsZXM6IHRydWUKICAgIG1heF9uZXdfdG9rZW5zOiAxNjM4NAogICAgcGFyYWxsZWxpc206IDMKICAgIHRlbXBlcmF0dXJlOiAwLjYKICB0eXBlOiBncHFhX2RpYW1vbmQKbWV0YWRhdGE6CiAgbGF1bmNoZXJfcmVzb2x2ZWRfY29uZmlnOgogICAgZGVwbG95bWVudDoKICAgICAgdHlwZTogbm9uZQogICAgZXZhbHVhdGlvbjoKICAgICAgbmVtb19ldmFsdWF0b3JfY29uZmlnOgogICAgICAgIGNvbmZpZzoKICAgICAgICAgIHBhcmFtczoKICAgICAgICAgICAgbG9nX3NhbXBsZXM6IHRydWUKICAgICAgICAgICAgbWF4X25ld190b2tlbnM6IDE2Mzg0CiAgICAgICAgICAgIHBhcmFsbGVsaXNtOiAzCiAgICAgICAgICAgIHRlbXBlcmF0dXJlOiAwLjYKICAgICAgdGFza3M6CiAgICAgIC0gZW52X3ZhcnM6CiAgICAgICAgICBIRl9UT0tFTjogSEZfVE9LRU4KICAgICAgICBuYW1lOiBncHFhX2RpYW1vbmQKICAgIGV4ZWN1dGlvbjoKICAgICAgZXh0cmFfZG9ja2VyX2FyZ3M6ICcnCiAgICAgIG1vZGU6IHNlcXVlbnRpYWwKICAgICAgb3V0cHV0X2RpcjogLi9yZXN1bHRzL2xsYW1hLTQwNWIKICAgICAgdHlwZTogbG9jYWwKICAgIHRhcmdldDoKICAgICAgYXBpX2VuZHBvaW50OgogICAgICAgIGFwaV9rZXlfbmFtZTogTkdDX0FQSV9LRVkKICAgICAgICBtb2RlbF9pZDogbWV0YS9sbGFtYS0zLjEtNDA1Yi1pbnN0cnVjdAogICAgICAgIHVybDogaHR0cHM6Ly9pbnRlZ3JhdGUuYXBpLm52aWRpYS5jb20vdjEvY2hhdC9jb21wbGV0aW9ucwogIHZlcnNpb25pbmc6CiAgICBuZW1vX2V2YWx1YXRvcl9sYXVuY2hlcjogMC4xLjY3CnRhcmdldDoKICBhcGlfZW5kcG9pbnQ6CiAgICBhcGlfa2V5OiBBUElfS0VZCiAgICBtb2RlbF9pZDogbWV0YS9sbGFtYS0zLjEtNDA1Yi1pbnN0cnVjdAogICAgdHlwZTogY2hhdAogICAgdXJsOiBodHRwczovL2ludGVncmF0ZS5hcGkubnZpZGlhLmNvbS92MS9jaGF0L2NvbXBsZXRpb25zCg==" | base64 -d > config_ef.yaml && cmd=$(command -v nemo-evaluator >/dev/null 2>&1 && echo nemo-evaluator || echo eval-factory) && source pre_cmd.sh && $cmd run_eval --run_config config_ef.yaml ;
        exit_code=$?
        chmod 777 -R /results;
        if [ "$exit_code" -ne 0 ]; then
            echo "The evaluation container failed with exit code $exit_code" >&2;
            exit "$exit_code";
        fi;
        echo "Container completed successfully" >&2;
        exit 0;
      ' > "$logs_dir/client_stdout.log" 2>&1
    exit_code=$?

    

    echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) $exit_code" > "$logs_dir/stage.exit"
) >> "$logs_dir/stdout.log" 2>&1



fi
