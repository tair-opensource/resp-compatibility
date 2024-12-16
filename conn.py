import time
import yaml
import subprocess
import logging

# 配置日志记录
logging.basicConfig(
    filename='/tmp/conn.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


def update_config():
    yml_file_path = '/root/db_config.yml'
    config_file_path = 'config.yaml'

    try:
        logging.info(f"Reading YAML file from {yml_file_path} and config file from {config_file_path}")
        with open(yml_file_path, 'r') as yml_file, open(config_file_path, 'r') as config_file:
            yml_data = yaml.safe_load(yml_file)
            config_data = yaml.safe_load(config_file)

            logging.info("Merging YAML data into config data")
            for db_name, db_config in yml_data.items():
                if db_name in config_data['Database']:
                    for key, value in db_config.items():
                        config_data['Database'][db_name][key] = value
                else:
                    config_data['Database'][db_name] = db_config

        logging.info(f"Writing updated config data to {config_file_path}")
        with open(config_file_path, 'w') as config_file:
            yaml.dump(config_data, config_file, sort_keys=False, default_flow_style=False)

        logging.info("Config file updated successfully.")

    except FileNotFoundError as e:
        logging.error(f"Error: {e}. Please check the file paths.")
    except yaml.YAMLError as e:
        logging.error(f"Error in YAML processing: {e}")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")


def execute_command(commands):
    for command in commands:
        logging.info(f"Executing command: {command}")
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            logging.error(f"Error executing command '{command}': {result.stderr}")
            return False
        else:
            logging.info(f"Successfully executed command '{command}': {result.stdout}")
    return True


def run_tests():
    run_test_command = [
        "pip3 install -r requirements.txt",
        "python3 resp_compatibility.py --testfile cts.json --genhtml --show-failed",
    ]

    logging.info("Starting test execution")
    if not execute_command(run_test_command):
        logging.error("Test failed. Exiting...")
        exit(1)
    else:
        logging.info("Test completed successfully.")


def commit_and_push_results():
    commit_and_push_commands = [
        "mv html /root",
        "git stash -u",
        "git checkout gh-pages || git checkout -b gh-pages",
        "git pull origin gh-pages",
        "cp -r /root/html/* .",
        "git add .",
        "git commit -m 'Update test results'",
    ]

    logging.info("Starting commit and push process")
    if not execute_command(commit_and_push_commands):
        logging.error("Failed to commit and push changes. Exiting...")
        exit(1)


def git_push_with_retry():
    logging.info("Starting git push with retry")
    while True:
        result = subprocess.run("git push -u origin gh-pages", shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            logging.info("Successfully pushed to GitHub.")
            break
        else:
            logging.error(f"Git push failed: {result.stderr}. Retrying in 5 seconds...")
            time.sleep(5)


def main():
    logging.info("Starting main function")

    update_config()

    package_update_commands = [
        "apt-get update",
        "apt-get install -y python3-pip",
    ]
    logging.info("Updating packages")
    if not execute_command(package_update_commands):
        logging.error("Failed to update or install packages. Exiting...")
        exit(1)

    logging.info("Running tests")
    run_tests()

    commit_and_push_results()
    git_push_with_retry()

    logging.info("Main function completed successfully")


if __name__ == "__main__":
    main()
