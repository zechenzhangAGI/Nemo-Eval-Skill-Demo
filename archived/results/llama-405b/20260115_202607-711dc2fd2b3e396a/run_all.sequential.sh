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

task_dir="/n/home04/zechenzhang/Nemo-Eval-Skill-Demo/results/llama-405b/20260115_202607-711dc2fd2b3e396a/gpqa_diamond"
artifacts_dir="$task_dir/artifacts"
logs_dir="$task_dir/logs"

mkdir -m 777 -p "$task_dir"
mkdir -m 777 -p "$artifacts_dir"
mkdir -m 777 -p "$logs_dir"
# Create stdout.log file upfront
touch "$logs_dir/client_stdout.log"
chmod 666 "$logs_dir/client_stdout.log"



# 711dc2fd2b3e396a.0 gpqa_diamond

task_dir="/n/home04/zechenzhang/Nemo-Eval-Skill-Demo/results/llama-405b/20260115_202607-711dc2fd2b3e396a/gpqa_diamond"
artifacts_dir="$task_dir/artifacts"
logs_dir="$task_dir/logs"

mkdir -m 777 -p "$task_dir"
mkdir -m 777 -p "$artifacts_dir"
mkdir -m 777 -p "$logs_dir"

# Check if this job was killed
if [ -f "$killed_jobs_file" ] && grep -q "^711dc2fd2b3e396a.0$" "$killed_jobs_file"; then
    echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) Job 711dc2fd2b3e396a.0 (gpqa_diamond) was killed, skipping execution" | tee -a "$logs_dir/stdout.log"
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
    #     max_new_tokens: 2048
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
    #             max_new_tokens: 2048
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
        --name client-gpqa_diamond-20260115_202608_465646 \
      --volume "$artifacts_dir":/results \
      -e HF_TOKEN=$HF_TOKEN \
      -e API_KEY=$NGC_API_KEY \
      nvcr.io/nvidia/eval-factory/simple-evals:25.11 \
      bash -c '
        echo "" | base64 -d > pre_cmd.sh && echo "Y29uZmlnOgogIG91dHB1dF9kaXI6IC9yZXN1bHRzCiAgcGFyYW1zOgogICAgbG9nX3NhbXBsZXM6IHRydWUKICAgIG1heF9uZXdfdG9rZW5zOiAyMDQ4CiAgICBwYXJhbGxlbGlzbTogMwogICAgdGVtcGVyYXR1cmU6IDAuNgogIHR5cGU6IGdwcWFfZGlhbW9uZAptZXRhZGF0YToKICBsYXVuY2hlcl9yZXNvbHZlZF9jb25maWc6CiAgICBkZXBsb3ltZW50OgogICAgICB0eXBlOiBub25lCiAgICBldmFsdWF0aW9uOgogICAgICBuZW1vX2V2YWx1YXRvcl9jb25maWc6CiAgICAgICAgY29uZmlnOgogICAgICAgICAgcGFyYW1zOgogICAgICAgICAgICBsb2dfc2FtcGxlczogdHJ1ZQogICAgICAgICAgICBtYXhfbmV3X3Rva2VuczogMjA0OAogICAgICAgICAgICBwYXJhbGxlbGlzbTogMwogICAgICAgICAgICB0ZW1wZXJhdHVyZTogMC42CiAgICAgIHRhc2tzOgogICAgICAtIGVudl92YXJzOgogICAgICAgICAgSEZfVE9LRU46IEhGX1RPS0VOCiAgICAgICAgbmFtZTogZ3BxYV9kaWFtb25kCiAgICBleGVjdXRpb246CiAgICAgIGV4dHJhX2RvY2tlcl9hcmdzOiAnJwogICAgICBtb2RlOiBzZXF1ZW50aWFsCiAgICAgIG91dHB1dF9kaXI6IC4vcmVzdWx0cy9sbGFtYS00MDViCiAgICAgIHR5cGU6IGxvY2FsCiAgICB0YXJnZXQ6CiAgICAgIGFwaV9lbmRwb2ludDoKICAgICAgICBhcGlfa2V5X25hbWU6IE5HQ19BUElfS0VZCiAgICAgICAgbW9kZWxfaWQ6IG1ldGEvbGxhbWEtMy4xLTQwNWItaW5zdHJ1Y3QKICAgICAgICB1cmw6IGh0dHBzOi8vaW50ZWdyYXRlLmFwaS5udmlkaWEuY29tL3YxL2NoYXQvY29tcGxldGlvbnMKICB2ZXJzaW9uaW5nOgogICAgbmVtb19ldmFsdWF0b3JfbGF1bmNoZXI6IDAuMS42Nwp0YXJnZXQ6CiAgYXBpX2VuZHBvaW50OgogICAgYXBpX2tleTogQVBJX0tFWQogICAgbW9kZWxfaWQ6IG1ldGEvbGxhbWEtMy4xLTQwNWItaW5zdHJ1Y3QKICAgIHR5cGU6IGNoYXQKICAgIHVybDogaHR0cHM6Ly9pbnRlZ3JhdGUuYXBpLm52aWRpYS5jb20vdjEvY2hhdC9jb21wbGV0aW9ucwo=" | base64 -d > config_ef.yaml && cmd=$(command -v nemo-evaluator >/dev/null 2>&1 && echo nemo-evaluator || echo eval-factory) && source pre_cmd.sh && $cmd run_eval --run_config config_ef.yaml ;
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
