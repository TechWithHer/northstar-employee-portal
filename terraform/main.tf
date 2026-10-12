module "networking" {
  source = "./modules/networking"

  project_name = "northstar"
  environment  = "v2"

  vpc_cidr = "10.0.0.0/16"
}

resource "aws_vpc" "this" {
  cidr_block = var.vpc_cidr

  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = {
    Name        = "${var.project_name}-${var.environment}-vpc"
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}