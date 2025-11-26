# AWS Well-Architected GenAI Assessment Platform

A comprehensive GenAI-powered application that scans AWS accounts across all regions and evaluates them against the 6 Well-Architected Framework pillars using AWS Bedrock Claude Sonnet 4.

## ✨ Features

- 🔐 **User Authentication**: Secure JWT-based login/signup system
- 🌍 **Multi-Region Scanning**: Automatically scans all enabled AWS regions
- 🏗️ **6 Pillar Assessment**: 
  - Operational Excellence
  - Security
  - Reliability
  - Performance Efficiency
  - Cost Optimization
  - Sustainability
- 🤖 **GenAI Analysis**: AWS Bedrock Claude Sonnet 4 powered recommendations
- 📚 **Knowledge Base**: Upload Well-Architected docs for enhanced AI responses
- 📊 **Report Generation**: Download comprehensive PDF/Excel reports
- 🔒 **Secure Credential Management**: Encrypted storage of AWS credentials
- ☁️ **Document Upload**: S3-based document management

## 🏗️ Architecture

```
Next.js Frontend (TypeScript + TailwindCSS)
    ↓
FastAPI Backend (Python 3.13)
    ↓
├─ JWT Authentication
├─ AWS Multi-Region Scanner (boto3)
├─ Multi-Agent AI System (6 Specialized Agents)
│  ├─ Operational Excellence Agent
│  ├─ Security Agent
│  ├─ Reliability Agent
│  ├─ Performance Efficiency Agent
│  ├─ Cost Optimization Agent
│  └─ Sustainability Agent
├─ Orchestrator (Aggregates & Prioritizes)
├─ Bedrock Claude Sonnet 4.5 (GenAI)
├─ Knowledge Base (RAG)
├─ Report Generator (PDF/Excel)
├─ DynamoDB (Database)
└─ S3 (Document Storage)
```

## 🛠️ Tech Stack

### Backend
- **Framework**: FastAPI 0.115+
- **Language**: Python 3.13
- **Database**: AWS DynamoDB
- **AI/ML**: AWS Bedrock (Claude Sonnet 4.5) with Multi-Agent System
- **Agents**: 6 specialized AI agents (one per pillar)
- **Storage**: AWS S3
- **AWS SDK**: boto3 (latest)
- **Reports**: ReportLab (PDF), openpyxl (Excel)

### Frontend
- **Framework**: Next.js 15 (App Router)
- **Language**: TypeScript 5.7+
- **Styling**: TailwindCSS 4
- **State**: TanStack Query (React Query)
- **HTTP**: Axios

### Infrastructure
- **IaC**: Pulumi (Python)
- **Cloud**: AWS (DynamoDB, S3, Bedrock, IAM)

## 🚀 Quick Start

### Prerequisites

- Python 3.13+
- Node.js 18+
- AWS Account with Bedrock access
- Pulumi CLI
- AWS CLI configured
- Docker (for ECS deployment)

### Option 1: Local Development

#### 1. Deploy Infrastructure

```bash
cd infrastructure
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
pulumi up
```

#### 2. Backend Setup

```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your configuration
python -m uvicorn main:app --reload
```

#### 3. Frontend Setup

```bash
cd frontend
npm install
cp .env.local.example .env.local
npm run dev
```

### Option 2: Production Deployment (ECS Fargate with Auto-Scaling)

#### 1. Deploy Infrastructure

```bash
cd infrastructure
pulumi up
# Save outputs: ECR URLs, ALB DNS, cluster name
```

#### 2. Build and Push Docker Images

```bash
# Get ECR login
aws ecr get-login-password --region ap-south-1 | docker login --username AWS --password-stdin $(pulumi stack output backend_ecr_url | cut -d'/' -f1)

# Build and push backend
cd backend
docker build -t wellarchitected-backend .
docker tag wellarchitected-backend:latest $(pulumi stack output backend_ecr_url):latest
docker push $(pulumi stack output backend_ecr_url):latest

# Build and push frontend
cd ../frontend
docker build -t wellarchitected-frontend .
docker tag wellarchitected-frontend:latest $(pulumi stack output frontend_ecr_url):latest
docker push $(pulumi stack output frontend_ecr_url):latest
```

#### 3. Deploy to ECS

```bash
# Services auto-deploy when images are pushed
# Or force new deployment:
aws ecs update-service --cluster WellArchitectedCluster --service wellarchitected-backend-service --force-new-deployment --region ap-south-1
aws ecs update-service --cluster WellArchitectedCluster --service wellarchitected-frontend-service --force-new-deployment --region ap-south-1
```

#### 4. Access Application

```bash
# Get application URL
pulumi stack output application_url
# Open in browser
```

### Production Features Included

**Core Infrastructure:**
- ✅ **Fargate Serverless**: No server management
- ✅ **Auto-Scaling**: CPU/Memory based (2-10 tasks)
- ✅ **Load Balancer**: Application Load Balancer with health checks
- ✅ **Container Insights**: CloudWatch monitoring
- ✅ **High Availability**: Multi-AZ deployment
- ✅ **Zero Downtime**: Rolling updates

**Security & Compliance:**
- ✅ **Secrets Manager**: Encrypted secrets storage
- ✅ **WAF**: Web Application Firewall with managed rules
- ✅ **DynamoDB PITR**: Point-in-time recovery enabled
- ✅ **CloudWatch Alarms**: CPU, Memory, Health monitoring

**Performance & CDN:**
- ✅ **CloudFront**: Global CDN for frontend
- ✅ **HTTPS Redirect**: Automatic SSL/TLS
- ✅ **Compression**: Gzip enabled
- ✅ **Caching**: Optimized cache policies

**CI/CD:**
- ✅ **GitHub Actions**: Automated deployments
- ✅ **CodeBuild**: AWS native CI/CD
- ✅ **ECR Scanning**: Vulnerability scanning
- ✅ **Automated Testing**: Pre-deployment checks

## 📝 Environment Variables

### Backend (.env)
```env
AWS_REGION=ap-south-1
DYNAMODB_TABLE_NAME=WellArchitectedApp
BEDROCK_MODEL_ID=anthropic.claude-sonnet-4-20250514-v1:0
BEDROCK_INFERENCE_PROFILE_ARN=arn:aws:bedrock:ap-south-1:892345653395:inference-profile/apac.anthropic.claude-sonnet-4-20250514-v1:0
S3_DOCS_BUCKET=wellarchitected-docs-ap-south-1
S3_REPORTS_BUCKET=wellarchitected-reports-ap-south-1
SECRET_KEY=your-secret-key
ENCRYPTION_KEY=your-encryption-key
```

### Frontend (.env.local)
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## 📡 API Endpoints

### Authentication
- `POST /api/auth/signup` - User registration
- `POST /api/auth/login` - User login
- `GET /api/auth/me` - Get current user

### Credentials
- `POST /api/credentials/` - Store AWS credentials
- `GET /api/credentials/` - List credentials
- `DELETE /api/credentials/{id}` - Delete credential

### Scanning
- `POST /api/scan/` - Start AWS account scan
- `GET /api/scan/` - List all scans
- `GET /api/scan/{id}` - Get scan details
- `DELETE /api/scan/{id}` - Delete scan

### Reports
- `GET /api/report/{scan_id}/pdf` - Download PDF report
- `GET /api/report/{scan_id}/excel` - Download Excel report

### Documents
- `POST /api/s3/upload-document` - Upload Well-Architected docs
- `GET /api/s3/documents` - List uploaded documents
- `DELETE /api/s3/documents/{filename}` - Delete document

## 🎯 Usage

1. **Sign Up**: Create an account at `/signup`
2. **Add Credentials**: Navigate to Credentials and add AWS Access/Secret keys
3. **Upload Documents** (Optional): Upload Well-Architected Framework PDFs
4. **Start Scan**: Create a new scan, select credentials, and start
5. **Monitor Progress**: Watch real-time scanning progress
6. **Review Results**: View AI-powered recommendations by pillar
7. **Download Reports**: Export comprehensive PDF or Excel reports

## 🔒 Security

- ✅ AWS credentials encrypted at rest (Fernet encryption)
- ✅ JWT-based authentication with secure tokens
- ✅ Password hashing with bcrypt
- ✅ DynamoDB encryption at rest
- ✅ S3 bucket encryption
- ✅ IAM role-based access control
- ✅ CORS protection
- ✅ Input validation and sanitization

## 📊 AWS Resources Scanned

- **Compute**: EC2 instances, Lambda functions
- **Database**: RDS instances
- **Storage**: S3 buckets
- **Network**: VPCs, Security Groups
- **Identity**: IAM users, roles
- **Monitoring**: CloudWatch alarms

## 🤖 AI Features - Multi-Agent Architecture

- **Claude Sonnet 4.5**: Latest Anthropic model via Bedrock (ap-southeast-1)
- **6 Specialized AI Agents**: Each pillar has a dedicated expert agent
  - 🔧 Operational Excellence Agent
  - 🔒 Security Agent
  - 🛡️ Reliability Agent
  - ⚡ Performance Efficiency Agent
  - 💰 Cost Optimization Agent
  - 🌱 Sustainability Agent
- **Orchestrator System**: Aggregates findings and generates executive summary
- **RAG**: Knowledge Base integration for accurate responses
- **Parallel Processing**: All agents analyze simultaneously
- **Actionable Recommendations**: Specific, prioritized improvements per pillar
- **Context-Aware**: Uses uploaded documentation for enhanced accuracy

## 📚 Documentation

- [Complete Guide](COMPLETE_GUIDE.md) - Full technical guide for LinkedIn/Medium
- [CV Notes](CV_NOTE.md) - Resume and portfolio descriptions

## 🏃 Development

### Backend
```bash
cd backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend
```bash
cd frontend
npm run dev
```

### Infrastructure
```bash
cd infrastructure
pulumi preview  # Preview changes
pulumi up       # Deploy changes
pulumi destroy  # Tear down resources
```

## 🔐 Production Setup

### 1. Secrets Manager Configuration

```bash
# Update secrets in AWS Console or CLI
aws secretsmanager update-secret \
  --secret-id wellarchitected/backend/secrets \
  --secret-string '{
    "SECRET_KEY": "your-production-secret-key",
    "ENCRYPTION_KEY": "your-production-encryption-key",
    "BEDROCK_INFERENCE_PROFILE_ARN": "arn:aws:bedrock:ap-south-1:..."
  }' \
  --region ap-south-1
```

### 2. CloudFront Setup

```bash
# Get CloudFront domain
pulumi stack output cloudfront_url

# Access via CloudFront (HTTPS enabled)
# https://<cloudfront-domain>
```

### 3. WAF Configuration

```bash
# Add allowed IPs to WAF (optional)
aws wafv2 update-ip-set \
  --name wellarchitected-allowed-ips \
  --scope CLOUDFRONT \
  --id <ip-set-id> \
  --addresses "1.2.3.4/32" "5.6.7.8/32" \
  --region us-east-1
```

### 4. CI/CD with GitHub Actions

```bash
# Add secrets to GitHub repository
# Settings → Secrets → Actions → New repository secret

AWS_ACCESS_KEY_ID=<your-key>
AWS_SECRET_ACCESS_KEY=<your-secret>

# Push to main branch triggers automatic deployment
git push origin main
```

### 5. CloudWatch Alarms

Monitor your application:
- Backend CPU > 80%
- Backend Memory > 85%
- Unhealthy ALB targets
- WAF blocked requests

### 6. DynamoDB Backup

```bash
# Point-in-time recovery is enabled automatically
# Restore to any point in last 35 days

aws dynamodb restore-table-to-point-in-time \
  --source-table-name WellArchitectedApp \
  --target-table-name WellArchitectedApp-Restored \
  --restore-date-time 2024-01-01T00:00:00Z \
  --region ap-south-1
```

## 🧪 Testing

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

## 📦 Project Structure

```
AWS-WellArchitected-GenAI-App/
├── backend/
│   ├── app/
│   │   ├── api/routes/      # API endpoints
│   │   ├── core/            # Config, security
│   │   ├── db/              # DynamoDB client
│   │   ├── repositories/    # Data access layer
│   │   ├── services/        # Business logic
│   │   └── schemas/         # Pydantic models
│   ├── main.py              # FastAPI app
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── app/             # Next.js pages
│   │   └── lib/             # API client, utils
│   ├── package.json
│   └── tsconfig.json
└── infrastructure/
    ├── __main__.py          # Pulumi resources
    └── requirements.txt
```

## 🤝 Contributing

Contributions welcome! Please follow these steps:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details

## 💰 Cost Estimation

### Monthly Costs (Production)

| Service | Configuration | Estimated Cost |
|---------|--------------|----------------|
| **ECS Fargate** | 2-10 tasks (1 vCPU, 2GB RAM) | $50-150 |
| **Application Load Balancer** | 1 ALB | $20 |
| **CloudFront** | 1TB data transfer | $85 |
| **WAF** | 1 Web ACL + managed rules | $10 |
| **DynamoDB** | Pay-per-request | $5-20 |
| **S3** | 100GB storage | $3 |
| **CloudWatch** | Logs + metrics | $10 |
| **Secrets Manager** | 2 secrets | $1 |
| **ECR** | 10GB images | $1 |
| **Total** | | **$185-300/month** |

### Cost Optimization Tips
- Use Fargate Spot for 70% savings on non-critical workloads
- Enable S3 lifecycle policies for old reports
- Reduce CloudWatch log retention to 3 days
- Use CloudFront regional edge locations only
- Optimize DynamoDB with on-demand pricing

## 🚨 Monitoring & Alerts

### CloudWatch Alarms Configured
- **Backend CPU**: Alert when > 80% for 10 minutes
- **Backend Memory**: Alert when > 85% for 10 minutes
- **ALB Unhealthy Targets**: Alert immediately
- **WAF Blocked Requests**: Monitor attack patterns

### Logs & Metrics
```bash
# View backend logs
aws logs tail /ecs/wellarchitected-backend --follow

# View frontend logs
aws logs tail /ecs/wellarchitected-frontend --follow

# Check ECS service status
aws ecs describe-services \
  --cluster WellArchitectedCluster \
  --services wellarchitected-backend-service
```

## 🔄 CI/CD Pipeline

### GitHub Actions Workflow
Automatically deploys on push to `main` branch:

1. **Build Phase**: Docker images built for backend and frontend
2. **Push Phase**: Images pushed to ECR with tags
3. **Deploy Phase**: ECS services updated with new images
4. **Verify Phase**: Health checks confirm deployment

### Setup GitHub Actions
```bash
# Add repository secrets in GitHub:
# Settings → Secrets and variables → Actions

AWS_ACCESS_KEY_ID=<your-access-key>
AWS_SECRET_ACCESS_KEY=<your-secret-key>

# Commit and push to trigger deployment
git add .
git commit -m "Deploy to production"
git push origin main
```

### AWS CodeBuild (Alternative)
```bash
# Start build manually
aws codebuild start-build \
  --project-name wellarchitected-backend-build

aws codebuild start-build \
  --project-name wellarchitected-frontend-build
```

## 🔐 Security Best Practices

### Implemented
- ✅ Secrets stored in AWS Secrets Manager
- ✅ WAF with rate limiting and OWASP rules
- ✅ DynamoDB point-in-time recovery (35 days)
- ✅ Encrypted S3 buckets
- ✅ IAM least privilege access
- ✅ VPC security groups
- ✅ HTTPS redirect via CloudFront
- ✅ ECR image scanning

### Recommended Additions
- [ ] Add custom domain with Route53
- [ ] Configure ACM SSL certificate
- [ ] Enable AWS GuardDuty
- [ ] Set up AWS Config rules
- [ ] Add SNS notifications for alarms
- [ ] Enable AWS X-Ray tracing
- [ ] Configure VPC Flow Logs

## 📈 Scaling Configuration

### Auto-Scaling Policies

**Backend Service:**
- Min tasks: 2
- Max tasks: 10
- Scale out: CPU > 70% or Memory > 80%
- Scale in: CPU < 30% for 5 minutes
- Cooldown: 60s (out), 300s (in)

**Frontend Service:**
- Min tasks: 2
- Max tasks: 10
- Scale out: CPU > 70%
- Scale in: CPU < 30% for 5 minutes
- Cooldown: 60s (out), 300s (in)

### Load Testing
```bash
# Install Apache Bench
apt-get install apache2-utils

# Test backend API
ab -n 10000 -c 100 http://<alb-dns>/api/health

# Test frontend
ab -n 10000 -c 100 http://<alb-dns>/
```

## 🆘 Troubleshooting

### Common Issues

**1. ECS Tasks Not Starting**
```bash
# Check task stopped reason
aws ecs describe-tasks \
  --cluster WellArchitectedCluster \
  --tasks <task-arn> \
  --query 'tasks[0].stoppedReason'
```

**2. Image Pull Errors**
```bash
# Verify ECR permissions
aws ecr describe-repositories

# Check if image exists
aws ecr describe-images \
  --repository-name wellarchitected-backend
```

**3. Health Check Failures**
```bash
# Test health endpoint
curl http://<alb-dns>/api/health

# Check target health
aws elbv2 describe-target-health \
  --target-group-arn <tg-arn>
```

**4. High Costs**
```bash
# Check CloudWatch metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/ECS \
  --metric-name CPUUtilization \
  --dimensions Name=ServiceName,Value=wellarchitected-backend-service \
  --start-time 2024-01-01T00:00:00Z \
  --end-time 2024-01-02T00:00:00Z \
  --period 3600 \
  --statistics Average
```

## 🗑️ Cleanup

### Delete All Resources
```bash
cd infrastructure
pulumi destroy

# Confirm deletion
# This will remove:
# - ECS cluster and services
# - Load balancer
# - ECR repositories
# - DynamoDB table
# - S3 buckets
# - CloudFront distribution
# - WAF rules
# - All IAM roles
```

### Partial Cleanup (Keep Data)
```bash
# Delete only compute resources
pulumi destroy --target ecs_cluster
pulumi destroy --target alb

# Keep DynamoDB and S3 for data retention
```

## 🆘 Support

For issues or questions:
- Review CloudWatch logs
- Check [COMPLETE_GUIDE.md](COMPLETE_GUIDE.md) for detailed documentation
- Verify AWS permissions and quotas
- Ensure Bedrock model access is enabled
- Test with AWS CLI before using the application

## 🎉 Acknowledgments

- AWS Well-Architected Framework
- AWS Bedrock and Claude Sonnet 4
- FastAPI and Next.js communities
- Open source contributors
