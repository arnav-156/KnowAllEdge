# =============================================================================
# Terraform Variables
# =============================================================================

variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name (development, staging, production)"
  type        = string
  
  validation {
    condition     = contains(["development", "staging", "production"], var.environment)
    error_message = "Environment must be development, staging, or production."
  }
}

variable "project_name" {
  description = "Project name"
  type        = string
  default     = "intuitscape"
}

# VPC Configuration
variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "public_subnets" {
  description = "CIDR blocks for public subnets"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
}

variable "private_subnets" {
  description = "CIDR blocks for private subnets"
  type        = list(string)
  default     = ["10.0.11.0/24", "10.0.12.0/24", "10.0.13.0/24"]
}

# Database Configuration
variable "db_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t3.medium"
}

variable "db_allocated_storage" {
  description = "Allocated storage for RDS (GB)"
  type        = number
  default     = 100
}

variable "db_name" {
  description = "Database name"
  type        = string
  default     = "intuitscape"
}

variable "db_username" {
  description = "Database master username"
  type        = string
  default     = "intuitscape_admin"
}

variable "db_backup_retention" {
  description = "Database backup retention period (days)"
  type        = number
  default     = 30
}

variable "db_multi_az" {
  description = "Enable Multi-AZ for RDS"
  type        = bool
  default     = true
}

# Redis Configuration
variable "redis_node_type" {
  description = "ElastiCache node type"
  type        = string
  default     = "cache.t3.medium"
}

variable "redis_num_nodes" {
  description = "Number of cache nodes"
  type        = number
  default     = 2
}

# ECS Configuration
variable "backend_image" {
  description = "Docker image for backend"
  type        = string
}

variable "backend_cpu" {
  description = "CPU units for backend task"
  type        = number
  default     = 1024
}

variable "backend_memory" {
  description = "Memory (MB) for backend task"
  type        = number
  default     = 2048
}

variable "backend_count" {
  description = "Number of backend tasks"
  type        = number
  default     = 3
}

variable "frontend_image" {
  description = "Docker image for frontend"
  type        = string
}

variable "frontend_cpu" {
  description = "CPU units for frontend task"
  type        = number
  default     = 512
}

variable "frontend_memory" {
  description = "Memory (MB) for frontend task"
  type        = number
  default     = 1024
}

variable "frontend_count" {
  description = "Number of frontend tasks"
  type        = number
  default     = 2
}

# Auto Scaling Configuration
variable "autoscaling_min" {
  description = "Minimum number of tasks"
  type        = number
  default     = 2
}

variable "autoscaling_max" {
  description = "Maximum number of tasks"
  type        = number
  default     = 10
}

variable "autoscaling_target_cpu" {
  description = "Target CPU utilization for auto scaling"
  type        = number
  default     = 70
}

# SSL Configuration
variable "ssl_certificate_arn" {
  description = "ARN of SSL certificate in ACM"
  type        = string
}

# Monitoring Configuration
variable "alert_email" {
  description = "Email address for alerts"
  type        = string
}

# Tags
variable "tags" {
  description = "Additional tags for resources"
  type        = map(string)
  default     = {}
}
