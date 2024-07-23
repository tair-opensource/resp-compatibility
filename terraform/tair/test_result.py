import os
import subprocess
import yaml


#之后用for循环收集每个数据库terraform的output即可
def update_config_yaml():
    # 从环境变量中获取 Tair 的连接信息
    tair_host = os.getenv('TAIR_HOST')
    tair_port = os.getenv('TAIR_PORT')
    tair_password = os.getenv('TAIR_PASSWORD')

    # 读取现有的 config.yaml 文件
    with open('config.yaml', 'r') as file:
        config = yaml.safe_load(file)

    # 更新 Tair 配置部分
    config['Database']['Tair'] = {
        'host': tair_host,
        'port': tair_port,
        'password': tair_password,
        'ssl': False,
        'cluster': False,
        'version': ''  # 根据需要填写或留空
    }

    # 写回更新后的配置
    with open('config.yaml', 'w') as file:
        yaml.safe_dump(config, file, default_flow_style=False)

if __name__ == '__main__':
    update_config_yaml()