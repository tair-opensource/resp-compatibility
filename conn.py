import os
import threading
import time
import yaml
import subprocess

# 更新配置文件
try:
    yml_file_path = '/root/db_config.yml'
    config_file_path = '/compatibility-test-suite-for-redis/config.yaml'

    with open(yml_file_path, 'r') as yml_file, open(config_file_path, 'r') as config_file:
        yml_data = yaml.safe_load(yml_file)
        config_data = yaml.safe_load(config_file)

        for db_name, db_config in yml_data.items():
            if db_name in config_data['Database']:
                for key, value in db_config.items():
                    config_data['Database'][db_name][key] = value
            else:
                config_data['Database'][db_name] = db_config

    with open(config_file_path, 'w') as config_file:
        yaml.dump(config_data, config_file, default_flow_style=False)

    print("Config file updated successfully.")

except FileNotFoundError as e:
    print(f"Error: {e}. Please check the file paths.")
except yaml.YAMLError as e:
    print(f"Error in YAML processing: {e}")
except Exception as e:
    print(f"An unexpected error occurred: {e}")


# 执行命令并判断是否成功
def execute_command(commands):
    for command in commands:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Error executing command '{command}': {result.stderr}")
            return False
        else:
            print(f"Successfully executed command '{command}': {result.stdout}")
    return True



commands = [
    "apt-get update",
    "apt-get install -y python3-pip",
]
if not execute_command(commands):
    print("Failed to update or install packages. Exiting...")
    exit(1)

# 运行测试命令
run_test_command = [
    "pip3 install -r requirements.txt",
    "python3 resp_compatibility.py --testfile cts.json --genhtml --show-failed",
]

def run_test():
    if not execute_command(run_test_command):
        print("Test failed. Exiting...")
        exit(1)
    else:
        print("Test completed successfully.")

# 启动测试脚本的线程
test_thread = threading.Thread(target=run_test)
test_thread.start()

time.sleep(300)

# 提交和推送测试结果
commit_and_push_commands = [
    "mv html /root",
    "git stash -u",
    "git checkout gh-pages || git checkout -b gh-pages",
    "git pull origin gh-pages",
    "cp -r /root/html/* .", #更新直接覆盖原同名文件
    "git add .",
    "git commit -m 'Update test results'",
]
if not execute_command(commit_and_push_commands):
    print("Failed to commit and push changes. Exiting...")
    exit(1)

# 推送到 GitHub 并重试
def git_push_with_retry():
    while True:
        result = subprocess.run("git push -u origin gh-pages", shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print("Successfully pushed to GitHub.")
            break
        else:
            print(f"Git push failed: {result.stderr}. Retrying in 5 seconds...")
            time.sleep(5)

git_push_with_retry()

