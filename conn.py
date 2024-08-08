import os
import threading
import time

import yaml
import subprocess

def read_temp_file(file_path):
    info = {}
    with open(file_path, 'r') as file:
        for line in file:
            key, value = line.strip().split('=')
            info[key] = value
    return info

# temp_file_path = '/path/to/temp/file'
# info = read_temp_file(temp_file_path)

access_key_id = ''
access_key_secret = ''
ecs_ip = ''
tair_host = ''
tair_port = ''
tair_password = ''
ecs_password = ''

def execute_command(commands):
    for command in commands:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Error executing command '{command}': {result.stderr}")
        else:
            print(f"Successfully executed command '{command}': {result.stdout}")


commands = [
    "apt-get update",
    "apt-get install -y python3-pip",
    "apt-get install -y python3-venv",
    "git config --global user.name 'name'",
    "git config --global user.email 'email'",
]

execute_command(commands)

# 更新 config.yaml 文件
def update_config_file(tair_host, tair_port, tair_password):
    config_path = '/root/compatibility-test-suite-for-redis/config.yaml'

    with open(config_path, 'r') as file:
        config = yaml.safe_load(file)

    config['Database']['Tair']['host'] = tair_host
    config['Database']['Tair']['port'] = tair_port
    config['Database']['Tair']['password'] = tair_password

    with open(config_path, 'w') as file:
        yaml.safe_dump(config, file)

update_config_file(tair_host, tair_port, tair_password)

# 运行测试脚本
run_test_command = [
    "pip3 install -r requirements.txt",
    "python3 resp_compatibility.py --testfile cts.json --genhtml --show-failed",
]

def run_test():
    execute_command(run_test_command)

# 启动测试脚本的线程
test_thread = threading.Thread(target=run_test)
test_thread.start()

# 主线程等待3分钟
time.sleep(180)


# 提交测试结果到 GitHub
commit_and_push_commands = [
    "mv html /tmp/test-results",
    "git stash",
    "git checkout gh-pages || git checkout -b gh-pages",
    "cp -r /tmp/test-results/* .",
    "git add .",
    "git commit -m 'Update test results'",
]
execute_command(commit_and_push_commands)

# 确保 git push 成功的循环
def git_push_with_retry():
    while True:
        result = subprocess.run("cd /root/compatibility-test-suite-for-redis/ && git push origin gh-pages", shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print("Successfully pushed to GitHub.")
            break
        else:
            print(f"Git push failed: {result.stderr}. Retrying in 5 seconds...")
            time.sleep(5)

git_push_with_retry()
