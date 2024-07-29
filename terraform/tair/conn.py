import os
import yaml
import subprocess

def read_temp_file(file_path):
    info = {}
    with open(file_path, 'r') as file:
        for line in file:
            key, value = line.strip().split('=')
            info[key] = value
    return info

temp_file_path = '/path/to/temp/file'  # 替换为实际的 temp 文件路径
info = read_temp_file(temp_file_path)

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
    "cd compatibility-test-suite-for-redis",
    "git checkout gh-pages",
    "source venv/bin/activate",
    "pip3 install -r requirements.txt",
    "python3 resp_compatibility.py --testfile cts.json --genhtml --show-failed",
    "deactivate",
]

execute_command(run_test_command)

# 提交测试结果到 GitHub 的命令
commit_and_push_commands = [
    "git add html/*",
    "git commit -m 'Daily test results'",
    "git push origin gh-pages"
]
execute_command(commit_and_push_commands)
