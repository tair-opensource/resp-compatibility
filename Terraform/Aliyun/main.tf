variable "access_key" {
  description = "Access key for Alicloud provider"
  type        = string
}

variable "secret_key" {
  description = "Secret key for Alicloud provider"
  type        = string
}

variable "github_token" {
  description = "GitHub token for accessing GitHub API"
  type        = string
}

variable "user_name" {
  description = "GitHub user name"
  type        = string
}

variable "user_email" {
  description = "GitHub user email"
  type        = string
}

locals {
  selected_zone_id = "cn-hongkong-b"
}

provider "alicloud" {
  access_key = var.access_key
  secret_key = var.secret_key
  region     = "cn-hongkong"
}

# 创建 VPC
resource "alicloud_vpc" "my_vpc" {
  vpc_name   = "MyVPC"
  cidr_block = "172.16.0.0/24"
}

# 创建 VSwitch
resource "alicloud_vswitch" "my_vswitch" {
  vswitch_name = "glcc_vswitch"
  vpc_id       = alicloud_vpc.my_vpc.id
  cidr_block   = "172.16.0.0/24"
  zone_id      = local.selected_zone_id
}

resource "alicloud_security_group" "my_sg" {
  name        = "glcc_test_security_group"
  vpc_id      = alicloud_vpc.my_vpc.id
  description = "Security Group for testing"
}

resource "alicloud_security_group_rule" "allow_ssh" {
  security_group_id = alicloud_security_group.my_sg.id
  type              = "ingress"
  ip_protocol       = "tcp"
  nic_type          = "intranet"
  policy            = "accept"
  port_range        = "22/22"
  priority          = 1
  cidr_ip           = "0.0.0.0/0"
}

resource "alicloud_security_group_rule" "allow_http" {
  security_group_id = alicloud_security_group.my_sg.id
  type              = "ingress"
  ip_protocol       = "tcp"
  nic_type          = "intranet"
  policy            = "accept"
  port_range        = "80/80"
  priority          = 100
  cidr_ip           = "0.0.0.0/0"
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
  port_range        = "6379/17005"
  cidr_ip           = "172.16.0.10/16"  # 仅允许特定 ECS 实例的私有 IP 访问
  description       = "Allow inbound Redis traffic"
}

# 云原生 1GB 标准版 Tair 6.0
resource "alicloud_kvstore_instance" "my_tair_standard" {
  db_instance_name = "glcc_tair_standard"
  instance_class   = "tair.rdb.1g"
  instance_type    = "Redis"
  engine_version   = "7.0"
  zone_id          = local.selected_zone_id
  vswitch_id       = alicloud_vswitch.my_vswitch.id
  payment_type     = "PostPaid"
  password         = "T123456@*"
  security_ips     = ["172.16.0.10"]
}


# 云原生 1GB 集群版 Tair 6.0
resource "alicloud_kvstore_instance" "my_tair_cluster" {
  db_instance_name = "glcc_tair_cluster"
  instance_class   = "tair.rdb.with.proxy.1g"
  instance_type    = "Redis"
  engine_version   = "7.0"
  shard_count      = "8"
  zone_id          = local.selected_zone_id
  vswitch_id       = alicloud_vswitch.my_vswitch.id
  payment_type     = "PostPaid"
  password         = "T123456@*"
  security_ips     = ["172.16.0.10"]
}

# 云原生 1GB 标准版 Redis 6.0
resource "alicloud_kvstore_instance" "my_redis_standard" {
  db_instance_name = "glcc_redis_standard"
  instance_class   = "redis.shard.small.2.ce"
  instance_type    = "Redis"
  engine_version   = "7.0"
  zone_id          = local.selected_zone_id
  vswitch_id       = alicloud_vswitch.my_vswitch.id
  payment_type     = "PostPaid"
  password         = "T123456@*"
  security_ips     = ["172.16.0.10"]
}


# 云原生 1GB 集群版 Redis 6.0
resource "alicloud_kvstore_instance" "my_redis_cluster" {
  db_instance_name = "glcc_redis_cluster"
  instance_class   = "redis.shard.with.proxy.small.ce"
  instance_type    = "Redis"
  engine_version   = "7.0"
  shard_count      = "8"
  zone_id          = local.selected_zone_id
  vswitch_id       = alicloud_vswitch.my_vswitch.id
  payment_type     = "PostPaid"
  password         = "T123456@*"
  security_ips     = ["172.16.0.10"]
}


# 输出实例信息,目前用于验证
output "tair_standard_instance_address" {
  value = alicloud_kvstore_instance.my_tair_standard.connection_domain
}

output "tair_standard_instance_port" {
  value = alicloud_kvstore_instance.my_tair_standard.private_connection_port
}

output "tair_standard_instance_password" {
  value     = alicloud_kvstore_instance.my_tair_standard.password
  sensitive = true
}

output "tair_cluster_instance_address" {
  value = alicloud_kvstore_instance.my_tair_cluster.connection_domain
}

output "tair_cluster_instance_port" {
  value = alicloud_kvstore_instance.my_tair_cluster.private_connection_port
}

output "tair_cluster_instance_password" {
  value     = alicloud_kvstore_instance.my_tair_cluster.password
  sensitive = true
}

output "redis_standard_instance_address" {
  value = alicloud_kvstore_instance.my_redis_standard.connection_domain
}

output "redis_standard_instance_port" {
  value = alicloud_kvstore_instance.my_redis_standard.private_connection_port
}

output "redis_standard_instance_password" {
  value     = alicloud_kvstore_instance.my_redis_standard.password
  sensitive = true
}

output "redis_cluster_instance_address" {
  value = alicloud_kvstore_instance.my_redis_cluster.connection_domain
}

output "redis_cluster_instance_port" {
  value = alicloud_kvstore_instance.my_redis_cluster.private_connection_port
}

output "redis_cluster_instance_password" {
  value     = alicloud_kvstore_instance.my_redis_cluster.password
  sensitive = true
}

# 创建 ECS 实例
resource "alicloud_instance" "my_ecs" {
  private_ip               = "172.16.0.10"
  instance_type            = "ecs.g6.xlarge"
  security_groups          = [alicloud_security_group.my_sg.id]
  instance_charge_type     = "PostPaid"
  internet_charge_type     = "PayByTraffic"
  internet_max_bandwidth_out = 10
  image_id                 = "ubuntu_22_04_x64_20G_alibase_20240130.vhd"
  instance_name            = "glcc_ecs"
  vswitch_id               = alicloud_vswitch.my_vswitch.id
  system_disk_category     = "cloud_efficiency"
  password                 = "T123456@*"

  lifecycle {
    create_before_destroy = true
  }

  user_data = <<EOF
#!/bin/bash
export HOME=/root
apt-get update
apt-get install -y python3-pip git docker.io
systemctl start docker
pip install "pyyaml>=6.0"
git config --global credential.helper 'store'
source /etc/profile

# 写入数据库配置信息
cat <<EOT >> /root/db_config.yml
AliyunTair:
  host: ${alicloud_kvstore_instance.my_tair_standard.connection_domain}
  port: ${alicloud_kvstore_instance.my_tair_standard.private_connection_port}
  password: T123456@*
  ssl: false
  cluster: false
  version: 7.0

AliyunTairCluster:
  host: ${alicloud_kvstore_instance.my_tair_cluster.connection_domain}
  port: ${alicloud_kvstore_instance.my_tair_cluster.private_connection_port}
  password: T123456@*
  ssl: false
  cluster: true
  version: 7.0

AliyunRedis:
  host: ${alicloud_kvstore_instance.my_redis_standard.connection_domain}
  port: ${alicloud_kvstore_instance.my_redis_standard.private_connection_port}
  password: T123456@*
  ssl: false
  cluster: false
  version: 7.0

AliyunRedisCluster:
  host: ${alicloud_kvstore_instance.my_redis_cluster.connection_domain}
  port: ${alicloud_kvstore_instance.my_redis_cluster.private_connection_port}
  password: T123456@*
  ssl: false
  cluster: true
  version: 7.0
EOT


# 拉取和运行数据库容器
docker pull docker.io/redis:latest
docker run --name redis -d -p 6379:6379 redis

docker pull docker.dragonflydb.io/dragonflydb/dragonfly:latest
docker run --name dragonflydb -d -p 6380:6379 docker.dragonflydb.io/dragonflydb/dragonfly

docker pull apache/kvrocks:latest
docker run --name kvrocks -d -p 6381:6666 apache/kvrocks

docker pull docker.io/eqalpha/keydb:latest
docker run --name keydb -d -p 6382:6379 eqalpha/keydb

docker pull docker.io/pikadb/pika:latest
docker run --name pika -d -p 6383:6383 pikadb/pika

docker pull valkey/valkey:latest
docker run --name valkey -d -p 6384:6379 valkey/valkey


# 配置Git
echo "https://${var.github_token}:x-oauth-basic@github.com" > ~/.git-credentials
git config --global user.name "${var.user_name}"
git config --global user.email "${var.user_email}"

git clone https://github.com/redis/redis.git
cd redis
make -j
cd utils/create-cluster
 ./create-cluster start
yes yes | ./create-cluster create

# 尝试克隆 Git 仓库，最多尝试 10 次
REPO_URL="https://github.com/MrHappyEnding/compatibility-test-suite-for-redis.git"
RETRY_COUNT=0
MAX_RETRIES=10
SLEEP_DURATION=30

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
  if git clone $REPO_URL; then
    echo "Git clone succeeded"
    break
  else
    RETRY_COUNT=$((RETRY_COUNT + 1))
    echo "Git clone failed, attempt $RETRY_COUNT/$MAX_RETRIES"
    sleep $SLEEP_DURATION
  fi
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
  echo "Git clone failed after $MAX_RETRIES attempts" >&2
  exit 1
fi

cd compatibility-test-suite-for-redisa
git checkout dailyTest
python3 conn.py
EOF
}


output "ecs_ip_address" {
  value = alicloud_instance.my_ecs.private_ip
}

