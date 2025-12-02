# =============================================================================
# Main Terraform Configuration
# Infrastructure as Code for IntuiScape deployment
# =============================================================================

terraform {
  required_version = ">= 1.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  
  # Backend configuration for state management
  backend "s3" {
    bucket         = "intuitscape-terraform-state"
    key            = "production/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "intuitscape-terraform-locks"
  }
}

# Provider configuration
provider "aws" {
  region = var.aws_region
  
  default_tags {
    tags = {
      Project     = "IntuiScape"
      Environment = var.environment
      ManagedBy   = "Terraform"
    }
  }
}

# Data sources
data "aws_availability_zones" "available" {
  state = "available"
}

# VPC Module
module "vpc" {
  source = "./modules/vpc"
  
  environment         = var.environment
  vpc_cidr           = var.vpc_cidr
  availability_zones = data.aws_availability_zones.available.names
  public_subnets     = var.public_subnets
  private_subnets    = var.private_subnets
}

# Security Groups Module
module "security_groups" {
  source = "./modules/security_groups"
  
  environment = var.environment
  vpc_id      = module.vpc.vpc_id
}

# RDS Database Module
module "database" {
  source = "./modules/rds"
  
  environment           = var.environment
  vpc_id               = module.vpc.vpc_id
  private_subnet_ids   = module.vpc.private_subnet_ids
  security_group_ids   = [module.security_groups.database_sg_id]
  instance_class       = var.db_instance_class
  allocated_storage    = var.db_allocated_storage
  database_name        = var.db_name
  master_username      = var.db_username
  backup_retention     = var.db_backup_retention
  multi_az            = var.db_multi_az
}

# ElastiCache Redis Module
module "redis" {
  source = "./modules/elasticache"
  
  environment        = var.environment
  vpc_id            = module.vpc.vpc_id
  private_subnet_ids = module.vpc.private_subnet_ids
  security_group_ids = [module.security_groups.redis_sg_id]
  node_type         = var.redis_node_type
  num_cache_nodes   = var.redis_num_nodes
}

# ECS Cluster Module
module "ecs" {
  source = "./modules/ecs"
  
  environment        = var.environment
  vpc_id            = module.vpc.vpc_id
  public_subnet_ids  = module.vpc.public_subnet_ids
  private_subnet_ids = module.vpc.private_subnet_ids
  security_group_ids = [module.security_groups.ecs_sg_id]
  
  # Backend service
  backend_image      = var.backend_image
  backend_cpu        = var.backend_cpu
  backend_memory     = var.backend_memory
  backend_count      = var.backend_count
  
  # Frontend service
  frontend_image     = var.frontend_image
  frontend_cpu       = var.frontend_cpu
  frontend_memory    = var.frontend_memory
  frontend_count     = var.frontend_count
  
  # Environment variables
  database_url       = module.database.connection_string
  redis_host         = module.redis.endpoint
  redis_password     = module.redis.auth_token
}

# Application Load Balancer Module
module "alb" {
  source = "./modules/alb"
  
  environment        = var.environment
  vpc_id            = module.vpc.vpc_id
  public_subnet_ids  = module.vpc.public_subnet_ids
  security_group_ids = [module.security_groups.alb_sg_id]
  certificate_arn    = var.ssl_certificate_arn
  
  backend_target_group_arn  = module.ecs.backend_target_group_arn
  frontend_target_group_arn = module.ecs.frontend_target_group_arn
}

# Auto Scaling Module
module "autoscaling" {
  source = "./modules/autoscaling"
  
  environment           = var.environment
  ecs_cluster_name      = module.ecs.cluster_name
  backend_service_name  = module.ecs.backend_service_name
  frontend_service_name = module.ecs.frontend_service_name
  
  min_capacity = var.autoscaling_min
  max_capacity = var.autoscaling_max
  target_cpu   = var.autoscaling_target_cpu
}

# CloudWatch Monitoring Module
module "monitoring" {
  source = "./modules/monitoring"
  
  environment          = var.environment
  ecs_cluster_name     = module.ecs.cluster_name
  alb_arn             = module.alb.alb_arn
  database_identifier  = module.database.db_instance_id
  redis_cluster_id     = module.redis.cluster_id
  
  alert_email = var.alert_email
}

# S3 Buckets Module
module "s3" {
  source = "./modules/s3"
  
  environment = var.environment
  
  # Backup bucket
  backup_bucket_name = "${var.project_name}-${var.environment}-backups"
  
  # Static assets bucket
  assets_bucket_name = "${var.project_name}-${var.environment}-assets"
}

# Outputs
output "vpc_id" {
  description = "VPC ID"
  value       = module.vpc.vpc_id
}

output "alb_dns_name" {
  description = "Application Load Balancer DNS name"
  value       = module.alb.alb_dns_name
}

output "database_endpoint" {
  description = "RDS database endpoint"
  value       = module.database.endpoint
  sensitive   = true
}

output "redis_endpoint" {
  description = "ElastiCache Redis endpoint"
  value       = module.redis.endpoint
  sensitive   = true
}

output "ecs_cluster_name" {
  description = "ECS cluster name"
  value       = module.ecs.cluster_name
}
