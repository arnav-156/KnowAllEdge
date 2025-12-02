# Infrastructure as Code

This directory contains Infrastructure as Code (IaC) configurations for deploying KnowAllEdge to production.

## Directory Structure

```
infrastructure/
├── terraform/          # Terraform configurations for AWS
│   ├── main.tf        # Main Terraform configuration
│   ├── variables.tf   # Variable definitions
│   ├── terraform.tfvars.example  # Example variables
│   └── modules/       # Terraform modules (VPC, ECS, RDS, etc.)
├── kubernetes/        # Kubernetes manifests
│   └── deployment.yaml  # Complete K8s deployment
└── README.md          # This file
```

## Deployment Options

### Option 1: AWS with Terraform

Deploy to AWS using ECS, RDS, ElastiCache, and Application Load Balancer.

#### Prerequisites

- Terraform >= 1.0
- AWS CLI configured with appropriate credentials
- S3 bucket for Terraform state
- DynamoDB table for state locking

#### Setup

1. **Initialize Terraform backend:**

```bash
cd infrastructure/terraform

# Create S3 bucket for state
aws s3 mb s3://KNOWALLEDGE-terraform-state --region us-east-1

# Create DynamoDB table for locking
aws dynamodb create-table \
  --table-name KNOWALLEDGE-terraform-locks \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region us-east-1
```

2. **Configure variables:**

```bash
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your values
```

3. **Initialize and deploy:**

```bash
terraform init
terraform plan
terraform apply
```

#### Terraform Modules

- **VPC**: Creates VPC with public and private subnets across 3 AZs
- **Security Groups**: Configures security groups for ALB, ECS, RDS, Redis
- **RDS**: PostgreSQL database with Multi-AZ, automated backups
- **ElastiCache**: Redis cluster for caching and sessions
- **ECS**: Container orchestration with Fargate
- **ALB**: Application Load Balancer with SSL termination
- **Auto Scaling**: CPU-based auto scaling for ECS services
- **Monitoring**: CloudWatch alarms and dashboards
- **S3**: Buckets for backups and static assets

### Option 2: Kubernetes

Deploy to any Kubernetes cluster (EKS, GKE, AKS, or self-hosted).

#### Prerequisites

- kubectl configured with cluster access
- Kubernetes cluster >= 1.24
- cert-manager for SSL certificates (optional)
- nginx-ingress-controller (optional)

#### Setup

1. **Create secrets:**

```bash
kubectl create secret generic KNOWALLEDGE-secrets \
  --from-literal=SECRET_KEY=$(openssl rand -base64 32) \
  --from-literal=JWT_SECRET_KEY=$(openssl rand -base64 64) \
  --from-literal=GOOGLE_API_KEY=your_api_key \
  --from-literal=REDIS_PASSWORD=$(openssl rand -base64 24) \
  --from-literal=DATABASE_URL=postgresql://user:pass@host:5432/db \
  --from-literal=DB_PASSWORD=$(openssl rand -base64 24) \
  -n KNOWALLEDGE-production
```

2. **Deploy:**

```bash
kubectl apply -f infrastructure/kubernetes/deployment.yaml
```

3. **Verify deployment:**

```bash
kubectl get pods -n KNOWALLEDGE-production
kubectl get services -n KNOWALLEDGE-production
kubectl get ingress -n KNOWALLEDGE-production
```

#### Kubernetes Resources

- **Namespace**: Isolated namespace for production
- **ConfigMap**: Non-sensitive configuration
- **Secret**: Sensitive credentials (create manually)
- **StatefulSet**: PostgreSQL and Redis with persistent storage
- **Deployment**: Backend and frontend applications
- **Service**: Internal service discovery
- **Ingress**: External access with SSL
- **HorizontalPodAutoscaler**: Auto-scaling based on CPU/memory

## Environment-Specific Deployments

### Development

For local development, use Docker Compose:

```bash
cd KNOWALLEDGE-main
docker-compose up -d
```

### Staging

Deploy to staging environment:

**Terraform:**
```bash
cd infrastructure/terraform
terraform workspace new staging
terraform apply -var-file=staging.tfvars
```

**Kubernetes:**
```bash
kubectl apply -f infrastructure/kubernetes/deployment.yaml -n KNOWALLEDGE-staging
```

### Production

Deploy to production environment:

**Terraform:**
```bash
cd infrastructure/terraform
terraform workspace new production
terraform apply -var-file=production.tfvars
```

**Kubernetes:**
```bash
kubectl apply -f infrastructure/kubernetes/deployment.yaml -n KNOWALLEDGE-production
```

## Monitoring and Observability

### CloudWatch (AWS)

Terraform automatically creates:
- CloudWatch Log Groups for ECS tasks
- CloudWatch Alarms for CPU, memory, error rates
- CloudWatch Dashboard for system overview

### Prometheus + Grafana (Kubernetes)

Deploy monitoring stack:

```bash
# Add Prometheus Helm repo
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

# Install Prometheus
helm install prometheus prometheus-community/kube-prometheus-stack \
  -n monitoring --create-namespace

# Access Grafana
kubectl port-forward -n monitoring svc/prometheus-grafana 3000:80
```

## Backup and Disaster Recovery

### Database Backups

**AWS RDS:**
- Automated daily backups (30-day retention)
- Manual snapshots before major changes
- Cross-region replication (optional)

**Kubernetes:**
```bash
# Manual backup
kubectl exec -n KNOWALLEDGE-production postgres-0 -- \
  pg_dump -U KNOWALLEDGE_user KNOWALLEDGE > backup.sql

# Restore
kubectl exec -i -n KNOWALLEDGE-production postgres-0 -- \
  psql -U KNOWALLEDGE_user KNOWALLEDGE < backup.sql
```

### Application Rollback

See `scripts/rollback.sh` for automated rollback procedures.

## Security Considerations

### Secrets Management

**AWS:**
- Use AWS Secrets Manager or Parameter Store
- Rotate secrets regularly
- Enable encryption at rest

**Kubernetes:**
- Use Kubernetes Secrets (encrypted at rest)
- Consider external secrets operators (e.g., External Secrets Operator)
- Rotate secrets regularly

### Network Security

- All traffic encrypted in transit (TLS)
- Private subnets for databases and Redis
- Security groups with least privilege
- VPC flow logs enabled

### Compliance

- GDPR-compliant data handling
- Audit logging enabled
- Encryption at rest for all data stores
- Regular security scans

## Cost Optimization

### AWS

- Use Reserved Instances for predictable workloads
- Enable auto-scaling to match demand
- Use S3 lifecycle policies for backups
- Monitor costs with AWS Cost Explorer

### Kubernetes

- Use cluster autoscaler
- Set resource requests and limits
- Use spot instances for non-critical workloads
- Monitor with Kubecost

## Troubleshooting

### Common Issues

**Terraform state locked:**
```bash
# Force unlock (use with caution)
terraform force-unlock <lock-id>
```

**ECS tasks failing:**
```bash
# Check logs
aws logs tail /ecs/KNOWALLEDGE-backend --follow
```

**Kubernetes pods not starting:**
```bash
# Check pod status
kubectl describe pod <pod-name> -n KNOWALLEDGE-production

# Check logs
kubectl logs <pod-name> -n KNOWALLEDGE-production
```

## Support

For infrastructure issues:
1. Check CloudWatch/Prometheus logs
2. Review security group rules
3. Verify secrets are correctly configured
4. Check resource quotas and limits

## References

- [Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [AWS ECS Best Practices](https://docs.aws.amazon.com/AmazonECS/latest/bestpracticesguide/)
- [Kubernetes Production Best Practices](https://kubernetes.io/docs/setup/best-practices/)
