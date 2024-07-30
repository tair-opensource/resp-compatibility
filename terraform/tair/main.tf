variable "access_key" {
  description = "Access key for Alicloud provider"
  type        = string
  // 默认值可以设置为空，或者根据实际情况提供一个默认值
#  default     = ""
}

variable "secret_key" {
  description = "Secret key for Alicloud provider"
  type        = string
#  default     = ""
}

variable "github_token" {
  description = "GitHub token for accessing GitHub API"
  type        = string
#  default     = ""
}


provider "alicloud" {
  access_key = var.access_key
  secret_key = var.secret_key
  region     = "cn-hangzhou"
}

# 创建 VPC
resource "alicloud_vpc" "my_vpc" {
  vpc_name       = "MyVPC"
  cidr_block = "172.16.0.0/24"  # 已更新为指定的CIDR块
}

# 创建 VSwitch
resource "alicloud_vswitch" "my_vswitch" {
  vswitch_name   = "glcc_vswitch"
  vpc_id            = alicloud_vpc.my_vpc.id
  cidr_block        = "172.16.0.0/24"  # 已更新与VPC相同的CIDR块
  zone_id           = "cn-hangzhou-h"  # 已更新为指定的可用区
}

#简单安全组定义
resource "alicloud_security_group" "my_sg" {
  name = "glcc_test_security_group"
  vpc_id = alicloud_vpc.my_vpc.id
  description = "Security Group for testing"
}

resource "alicloud_security_group_rule" "allow_ssh" {
  security_group_id = alicloud_security_group.my_sg.id
  type = "ingress"
  ip_protocol = "tcp"
  nic_type = "intranet"
  policy = "accept"
  port_range = "22/22"
  priority = 1
  cidr_ip = "0.0.0.0/0"
}

resource "alicloud_security_group_rule" "allow_http" {
  security_group_id = alicloud_security_group.my_sg.id
  type = "ingress"
  ip_protocol = "tcp"
  nic_type = "intranet"
  policy = "accept"
  port_range = "80/80"
  priority = 100
  cidr_ip = "0.0.0.0/0"
}

resource "alicloud_security_group_rule" "allow_https_outbound" {
  type              = "egress"
  security_group_id = alicloud_security_group.my_sg.id
  ip_protocol       = "tcp"
  nic_type          = "intranet"
  policy            = "accept"
  port_range        = "443/443"
  cidr_ip           = "0.0.0.0/0"
  description       = "Allow outbound HTTPS traffic to external services"
}

resource "alicloud_security_group_rule" "allow_redis" {
  type              = "ingress"
  security_group_id = alicloud_security_group.my_sg.id
  ip_protocol       = "tcp"
  nic_type          = "intranet"
  policy            = "accept"
  port_range        = "6379/6379"
  cidr_ip           = "0.0.0.0/0"
  description       = "Allow inbound Redis traffic"
}


# resource "alicloud_security_group_rule" "ecs_to_tair" {
#   type = "ingress"
#   security_group_id = alicloud_security_group.my_sg.id
#   ip_protocol = "tcp"
#   nic_type = "intranet"
#   policy = "accept"
#   port_range = "${alicloud_kvstore_instance.my_tair.port}/${alicloud_kvstore_instance.my_tair.port}"
#   cidr_ip = "0.0.0.0/0"
# }


resource "alicloud_kvstore_instance" "my_tair" {
  db_instance_name   = "glcc_tair"
  instance_class    = "tair.rdb.1g"
  instance_type     = "Redis"
  engine_version    = "7.0"
  zone_id           = "cn-hangzhou-h"
  vswitch_id        = alicloud_vswitch.my_vswitch.id
#   private_ip        = "192.168.0.1"  # 如果需要指定私有网络 IP
  payment_type      = "PostPaid"
  password           = "Tair123456@*"
  security_ips      = ["172.16.0.10"]
}


output "tair_instance_address" {
  value = alicloud_kvstore_instance.my_tair.connection_domain
}

output "tair_instance_port" {
#   value = "6379"
  value = alicloud_kvstore_instance.my_tair.private_connection_port
}

output "tair_instance_password" {
  value = alicloud_kvstore_instance.my_tair.password
  sensitive = true
}


# 创建 ECS 实例, 配置 ECS 实例连接 Tair
# 在ecs登录github; git clone CTS代码; 运行测试CTS测试; 将测试结果genhtml作为PR提交到github pages
resource "alicloud_instance" "my_ecs" {
  private_ip             = "172.16.0.10"  # 指定私有 IP 地址, avoid conflict dependency with tair
  instance_type          = "ecs.n4.large"  # 已更改为通用型实例
  security_groups        = [alicloud_security_group.my_sg.id]
  instance_charge_type   = "PostPaid"
  internet_charge_type   = "PayByTraffic"
  internet_max_bandwidth_out = 10
  image_id               = "ubuntu_20_04_x64_20G_alibase_20240630.vhd"  # 举例更新为Ubuntu的镜像ID
  instance_name            = "glcc_ecs2"
  vswitch_id             = alicloud_vswitch.my_vswitch.id
  system_disk_category   = "cloud_efficiency"
  password               = "Tair123456@*"

  lifecycle {
    create_before_destroy = true
  }

  #config to tair,同时设置为环境变量可以保证之后config文件参数的获取
  user_data = <<-EOF
  #!/bin/bash
  export HOME=/root
  apt-get update
  apt-get install -y python3-pip
  apt-get install -y git
  pip install "pyyaml>=6.0"
  git config --global credential.helper 'store'
  source /etc/profile
  # 使用个人访问令牌
  echo "https://${var.github_token}:x-oauth-basic@github.com" > ~/.git-credentials
  git clone https://github.com/MrHappyEnding/compatibility-test-suite-for-redis.git #make sure the internet is ok, so there shall have an insurance
  cd compatibility-test-suite-for-redis
  git checkout gh-pages
  EOF
}

output "ecs_ip_address" {
  value = alicloud_instance.my_ecs.private_ip
}




