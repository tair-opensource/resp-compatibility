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



# 输出实例信息,目前用于验证
output "tair_standard_instance_address" {
  value = alicloud_kvstore_instance.my_tair_standard.connection_domain
}

output "tair_standard_instance_port" {
  value = alicloud_kvstore_instance.my_tair_standard.private_connection_port
}


