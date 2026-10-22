# Serverless Financial Tracker Platform

![AWS](https://img.shields.io/badge/AWS-%23FF9900.svg?style=for-the-badge&logo=amazon-aws&logoColor=white)
![Terraform](https://img.shields.io/badge/terraform-%235835CC.svg?style=for-the-badge&logo=terraform&logoColor=white)
![Nuxt](https://img.shields.io/badge/Nuxt-002E3B?style=for-the-badge&logo=nuxtdotjs&logoColor=#00DC82)
![Vue.js](https://img.shields.io/badge/vuejs-%2335495e.svg?style=for-the-badge&logo=vuedotjs&logoColor=%234FC08D)
![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=for-the-badge&logo=docker&logoColor=white)

A full-stack, cloud-native personal finance tracking application built with a strict serverless architecture. This platform is provisioned entirely via Infrastructure as Code (IaC) and features automated multi-environment CI/CD pipelines, secure user authentication, and automated financial reporting.

## 🚀 Live Demo

- **Production:** [https://finance.haikalahnaf.my.id](https://finance.haikalahnaf.my.id)
- **Guest Mode:** Visitors can freely test the application using the "Test as Guest" feature, which utilizes UUID partitioning to safely isolate temporary session data from production user data (auto-expiring via DynamoDB TTL).

---

## 🏗️ Architecture & Tech Stack

### Frontend (Client-Side)

- **Framework:** Nuxt 3 (Vue 3) configured as a Static Single Page Application (SPA).
- **Styling:** Tailwind CSS.
- **Hosting:** AWS S3 behind a CloudFront CDN.
- **Security:** Secured via CloudFront Origin Access Control (OAC), ensuring the S3 bucket is strictly private and only accessible through the CDN. ACM certificates configured in `us-east-1` for custom DNS routing via Cloudflare.

### Backend (Serverless API)

- **Compute:** AWS Lambda running custom Python Docker containers pulled from Amazon ECR.
- **Routing:** Amazon API Gateway (HTTP API) integrating directly with the Lambda function via proxy integration.
- **Database:** Amazon DynamoDB (Pay-Per-Request) utilizing single-table design with Partition Keys (PK) and Sort Keys (SK) for efficient querying.
- **Authentication:** Amazon Cognito User Pools for secure JWT-based auth flows.
- **Automated Jobs:** Amazon EventBridge triggers Lambda on a cron schedule to generate and email monthly financial summaries using Amazon Simple Email Service (SES).

### Infrastructure & Operations

- **IaC:** HashiCorp Terraform manages 100% of the cloud resources.
- **State Management:** Terraform state is securely stored in an S3 backend with strict logical isolation between `sandbox` and `production` environments.
- **CI/CD:** GitHub Actions orchestrates the build, test, and deployment phases.

---

## ⚙️ CI/CD Pipeline & Branching Strategy

The deployment pipeline is fully automated and environment-aware, completely separating development testing from live production data.

1. **Sandbox Environment (`dev` branch):**
   - Pushing to the `dev` branch triggers a workflow that provisions `FinancialTracker-sandbox` resources.
   - Terraform reads from `environments/sandbox/terraform.tfstate`.
   - Frontend generates with a `-sandbox` version tag and injects sandbox API/Cognito credentials.
2. **Production Environment (`main` branch):**
   - Merging to `main` provisions production-ready `FinancialTracker-production` resources.
   - Uses isolated production Terraform state and distinct ECR repositories to guarantee zero cross-contamination.
   - Triggers CloudFront cache invalidation post-deployment.

---

## 🛠️ Local Development

### Prerequisites

- Node.js 20+
- Docker & Docker Compose
- Terraform CLI >= 5.0
- AWS CLI configured with local credentials

### Running the Frontend

```bash
cd frontend
npm install
npm run dev
```
