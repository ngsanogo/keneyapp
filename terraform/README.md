# Terraform Infrastructure for KeneyApp

This directory contains Terraform configurations for deploying KeneyApp to various cloud providers.

## Supported Providers

- **AWS** - Amazon Web Services deployment
- **Azure** - Microsoft Azure deployment
- **GCP** - Google Cloud Platform deployment

## Prerequisites

1. Install Terraform (>= 1.5.0)
2. Configure cloud provider credentials
3. Review and customize variables

## Quick Start

### AWS Deployment

```bash
cd terraform/aws
terraform init
terraform plan
terraform apply
```

### Azure Deployment

```bash
cd terraform/azure
terraform init
terraform plan
terraform apply
```

### GCP Deployment

```bash
cd terraform/gcp
terraform init
terraform plan
terraform apply
```

## Configuration

Each provider directory contains:

- `main.tf` - Main infrastructure configuration
- `variables.tf` - Input variables
- `outputs.tf` - Output values
- `terraform.tfvars.example` - Example variable values

## Resources Created

### Common Resources (All Providers)

- Kubernetes cluster (EKS/AKS/GKE)
- PostgreSQL managed database
- Redis cache instance
- Load balancer
- Container registry
- Virtual network
- Security groups/firewall rules
- SSL/TLS certificates
- Monitoring and logging

### AWS Specific

- EKS cluster
- RDS PostgreSQL
- ElastiCache Redis
- ALB
- ECR
- VPC
- Security Groups
- Route53
- ACM certificates

### Azure Specific

- AKS cluster
- Azure Database for PostgreSQL
- Azure Cache for Redis
- Application Gateway
- ACR
- Virtual Network
- NSGs
- Azure DNS
- Key Vault

### GCP Specific

- GKE cluster
- Cloud SQL PostgreSQL
- Memorystore Redis
- Cloud Load Balancing
- Artifact Registry
- VPC
- Firewall rules
- Cloud DNS
- Secret Manager

## Cost Estimation

Run `terraform plan` to see estimated costs for your configuration.

Approximate monthly costs (production setup):

- **AWS**: $500-1000/month
- **Azure**: $450-950/month
- **GCP**: $480-980/month

Costs vary based on:

- Cluster size
- Database instance type
- Data transfer
- Storage usage

## Security Considerations

1. Store Terraform state in remote backend (S3, Azure Storage, GCS)
2. Enable encryption at rest for all resources
3. Use managed secrets (AWS Secrets Manager, Azure Key Vault, GCP Secret Manager)
4. Implement least privilege IAM policies
5. Enable audit logging
6. Use private subnets for database and cache
7. Enable DDoS protection
8. Regular security scanning

## Maintenance

### Backup

```bash
terraform state pull > terraform.tfstate.backup
```

### Destroy

```bash
terraform destroy
```

**Warning**: This will delete all resources. Ensure data is backed up first.

## Support

For issues or questions, contact: <support@isdataconsulting.com>
