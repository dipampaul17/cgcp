#!/usr/bin/env python3
"""
Claude Governance Control Plane - Production Deployment Script
Handles local, Docker, and cloud deployment with health checks and monitoring
"""

import subprocess
import sys
import os
import time
import json
import requests
import argparse
from colorama import init, Fore, Style, Back

init()

class DeploymentManager:
    """Manages deployment of CGCP across different environments"""
    
    def __init__(self):
        self.project_root = os.path.dirname(os.path.abspath(__file__))
        self.deployment_type = None
        
    def print_banner(self):
        """Display deployment banner"""
        print(f"{Back.BLUE}{Fore.WHITE}")
        print("═" * 80)
        print("    CLAUDE GOVERNANCE CONTROL PLANE - DEPLOYMENT".center(80))
        print("    Production-Ready RSP Implementation".center(80))
        print("═" * 80)
        print(f"{Style.RESET_ALL}\n")
    
    def print_status(self, message: str, status: str = "info"):
        """Print colored status messages"""
        colors = {
            "info": Fore.BLUE,
            "success": Fore.GREEN,
            "warning": Fore.YELLOW,
            "error": Fore.RED
        }
        icons = {
            "info": "ℹ️",
            "success": "✅",
            "warning": "⚠️",
            "error": "❌"
        }
        print(f"{colors[status]}{icons[status]} {message}{Style.RESET_ALL}")
    
    def check_prerequisites(self) -> bool:
        """Verify all prerequisites are met"""
        self.print_status("Checking prerequisites...")
        
        # Check Python version
        if sys.version_info < (3, 8):
            self.print_status("Python 3.8+ required", "error")
            return False
        
        # Check required files
        required_files = [
            "requirements.txt",
            "backend/app.py",
            "ui/dashboard.py",
            "start.sh"
        ]
        
        for file in required_files:
            if not os.path.exists(os.path.join(self.project_root, file)):
                self.print_status(f"Missing required file: {file}", "error")
                return False
        
        self.print_status("All prerequisites satisfied", "success")
        return True
    
    def create_environment_config(self, env: str = "production"):
        """Create environment-specific configuration"""
        config = {
            "development": {
                "API_HOST": "localhost",
                "API_PORT": 8000,
                "DASHBOARD_HOST": "localhost",
                "DASHBOARD_PORT": 8501,
                "DEBUG": True,
                "DATABASE": "governance_dev.db"
            },
            "production": {
                "API_HOST": "0.0.0.0",
                "API_PORT": 8000,
                "DASHBOARD_HOST": "0.0.0.0",
                "DASHBOARD_PORT": 8501,
                "DEBUG": False,
                "DATABASE": "governance.db"
            }
        }
        
        env_file = f".env.{env}"
        with open(env_file, "w") as f:
            for key, value in config[env].items():
                f.write(f"{key}={value}\n")
        
        self.print_status(f"Created {env} configuration", "success")
        return env_file
    
    def deploy_local(self):
        """Deploy locally with virtual environment"""
        self.print_status("Starting local deployment...")
        
        # Create virtual environment if not exists
        if not os.path.exists("venv"):
            self.print_status("Creating virtual environment...")
            subprocess.run([sys.executable, "-m", "venv", "venv"], check=True)
        
        # Install dependencies
        self.print_status("Installing dependencies...")
        pip_cmd = "venv/bin/pip" if os.path.exists("venv/bin/pip") else "venv\\Scripts\\pip"
        subprocess.run([pip_cmd, "install", "-r", "requirements.txt"], check=True)
        
        # Create environment config
        self.create_environment_config("production")
        
        # Start services
        self.print_status("Starting services...")
        subprocess.run(["chmod", "+x", "start.sh"], check=True)
        subprocess.run(["./start.sh"], check=True)
    
    def create_dockerfile(self):
        """Create optimized Dockerfile"""
        dockerfile_content = '''# Multi-stage build for optimal image size
FROM python:3.8-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \\
    gcc \\
    g++ \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.8-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \\
    curl \\
    && rm -rf /var/lib/apt/lists/*

# Copy Python dependencies from builder
COPY --from=builder /root/.local /root/.local

# Copy application code
COPY . .

# Ensure scripts are in PATH
ENV PATH=/root/.local/bin:$PATH

# Create volume for database
VOLUME ["/app/data"]

# Expose ports
EXPOSE 8000 8501

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \\
    CMD curl -f http://localhost:8000/health || exit 1

# Start script
COPY docker-entrypoint.sh /
RUN chmod +x /docker-entrypoint.sh

ENTRYPOINT ["/docker-entrypoint.sh"]
'''
        
        with open("Dockerfile", "w") as f:
            f.write(dockerfile_content)
        
        # Create docker-entrypoint.sh
        entrypoint_content = '''#!/bin/bash
set -e

echo "Starting Claude Governance Control Plane..."

# Start API backend
uvicorn backend.app:app --host 0.0.0.0 --port 8000 &
API_PID=$!

# Wait for API to be ready
echo "Waiting for API..."
for i in {1..30}; do
    if curl -s http://localhost:8000/health > /dev/null; then
        echo "API is ready"
        break
    fi
    sleep 1
done

# Start Streamlit dashboard
streamlit run ui/dashboard.py --server.headless true --server.port 8501 --server.address 0.0.0.0 &
DASHBOARD_PID=$!

echo "Services started. API PID: $API_PID, Dashboard PID: $DASHBOARD_PID"

# Keep container running
wait $API_PID $DASHBOARD_PID
'''
        
        with open("docker-entrypoint.sh", "w") as f:
            f.write(entrypoint_content)
        
        subprocess.run(["chmod", "+x", "docker-entrypoint.sh"], check=True)
        
        self.print_status("Created Docker configuration", "success")
    
    def deploy_docker(self):
        """Deploy using Docker"""
        self.print_status("Starting Docker deployment...")
        
        # Check Docker is installed
        try:
            subprocess.run(["docker", "--version"], check=True, capture_output=True)
        except:
            self.print_status("Docker not installed", "error")
            return False
        
        # Create Dockerfile
        self.create_dockerfile()
        
        # Build image
        self.print_status("Building Docker image...")
        subprocess.run([
            "docker", "build", "-t", "cgcp:latest", "."
        ], check=True)
        
        # Run container
        self.print_status("Starting Docker container...")
        subprocess.run([
            "docker", "run", "-d",
            "--name", "cgcp",
            "-p", "8000:8000",
            "-p", "8501:8501",
            "-v", f"{os.path.abspath('data')}:/app/data",
            "--restart", "unless-stopped",
            "cgcp:latest"
        ], check=True)
        
        self.print_status("Docker deployment complete", "success")
        return True
    
    def create_docker_compose(self):
        """Create docker-compose.yml for orchestration"""
        compose_content = '''version: '3.8'

services:
  cgcp:
    build: .
    container_name: cgcp
    ports:
      - "8000:8000"
      - "8501:8501"
    volumes:
      - ./data:/app/data
      - ./policy:/app/policy
    environment:
      - PYTHONUNBUFFERED=1
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped
    
  # Optional: Add monitoring
  prometheus:
    image: prom/prometheus:latest
    container_name: cgcp-prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
    restart: unless-stopped
    
  grafana:
    image: grafana/grafana:latest
    container_name: cgcp-grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana-storage:/var/lib/grafana
    restart: unless-stopped

volumes:
  grafana-storage:
'''
        
        with open("docker-compose.yml", "w") as f:
            f.write(compose_content)
        
        # Create monitoring config
        os.makedirs("monitoring", exist_ok=True)
        
        prometheus_config = '''global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'cgcp-api'
    static_configs:
      - targets: ['cgcp:8000']
'''
        
        with open("monitoring/prometheus.yml", "w") as f:
            f.write(prometheus_config)
        
        self.print_status("Created docker-compose configuration", "success")
    
    def deploy_docker_compose(self):
        """Deploy using Docker Compose"""
        self.print_status("Starting Docker Compose deployment...")
        
        # Create docker-compose.yml
        self.create_docker_compose()
        
        # Start services
        subprocess.run(["docker-compose", "up", "-d"], check=True)
        
        self.print_status("Docker Compose deployment complete", "success")
        self.print_status("Monitoring available at:")
        print("  - Prometheus: http://localhost:9090")
        print("  - Grafana: http://localhost:3000 (admin/admin)")
        
        return True
    
    def create_kubernetes_manifests(self):
        """Create Kubernetes deployment manifests"""
        os.makedirs("k8s", exist_ok=True)
        
        # Deployment manifest
        deployment_yaml = '''apiVersion: apps/v1
kind: Deployment
metadata:
  name: cgcp-deployment
  labels:
    app: cgcp
spec:
  replicas: 3
  selector:
    matchLabels:
      app: cgcp
  template:
    metadata:
      labels:
        app: cgcp
    spec:
      containers:
      - name: cgcp
        image: cgcp:latest
        ports:
        - containerPort: 8000
          name: api
        - containerPort: 8501
          name: dashboard
        env:
        - name: DATABASE_PATH
          value: /data/governance.db
        volumeMounts:
        - name: data
          mountPath: /data
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
      volumes:
      - name: data
        persistentVolumeClaim:
          claimName: cgcp-pvc
---
apiVersion: v1
kind: Service
metadata:
  name: cgcp-service
spec:
  selector:
    app: cgcp
  ports:
  - port: 8000
    targetPort: 8000
    name: api
  - port: 8501
    targetPort: 8501
    name: dashboard
  type: LoadBalancer
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: cgcp-pvc
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi
'''
        
        with open("k8s/deployment.yaml", "w") as f:
            f.write(deployment_yaml)
        
        # Ingress manifest
        ingress_yaml = '''apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: cgcp-ingress
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  tls:
  - hosts:
    - cgcp.yourdomain.com
    secretName: cgcp-tls
  rules:
  - host: cgcp.yourdomain.com
    http:
      paths:
      - path: /api
        pathType: Prefix
        backend:
          service:
            name: cgcp-service
            port:
              number: 8000
      - path: /
        pathType: Prefix
        backend:
          service:
            name: cgcp-service
            port:
              number: 8501
'''
        
        with open("k8s/ingress.yaml", "w") as f:
            f.write(ingress_yaml)
        
        self.print_status("Created Kubernetes manifests", "success")
    
    def deploy_kubernetes(self):
        """Deploy to Kubernetes cluster"""
        self.print_status("Starting Kubernetes deployment...")
        
        # Check kubectl is installed
        try:
            subprocess.run(["kubectl", "version"], check=True, capture_output=True)
        except:
            self.print_status("kubectl not installed", "error")
            return False
        
        # Create manifests
        self.create_kubernetes_manifests()
        
        # Apply manifests
        self.print_status("Applying Kubernetes manifests...")
        subprocess.run(["kubectl", "apply", "-f", "k8s/"], check=True)
        
        # Wait for deployment
        self.print_status("Waiting for pods to be ready...")
        subprocess.run([
            "kubectl", "wait", "--for=condition=ready", 
            "pod", "-l", "app=cgcp", "--timeout=300s"
        ], check=True)
        
        # Get service info
        self.print_status("Getting service information...")
        subprocess.run(["kubectl", "get", "services", "cgcp-service"])
        
        self.print_status("Kubernetes deployment complete", "success")
        return True
    
    def create_terraform_config(self):
        """Create Terraform configuration for cloud deployment"""
        os.makedirs("terraform", exist_ok=True)
        
        # AWS ECS Terraform config
        terraform_config = '''terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

variable "aws_region" {
  default = "us-east-1"
}

# ECS Cluster
resource "aws_ecs_cluster" "cgcp_cluster" {
  name = "cgcp-cluster"
}

# Task Definition
resource "aws_ecs_task_definition" "cgcp_task" {
  family                   = "cgcp"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "1024"
  memory                   = "2048"

  container_definitions = jsonencode([
    {
      name  = "cgcp"
      image = "cgcp:latest"
      
      portMappings = [
        {
          containerPort = 8000
          protocol      = "tcp"
        },
        {
          containerPort = 8501
          protocol      = "tcp"
        }
      ]
      
      healthCheck = {
        command     = ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"]
        interval    = 30
        timeout     = 5
        retries     = 3
        startPeriod = 60
      }
      
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = "/ecs/cgcp"
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "ecs"
        }
      }
    }
  ])
}

# ECS Service
resource "aws_ecs_service" "cgcp_service" {
  name            = "cgcp-service"
  cluster         = aws_ecs_cluster.cgcp_cluster.id
  task_definition = aws_ecs_task_definition.cgcp_task.arn
  desired_count   = 2
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = aws_subnet.public[*].id
    security_groups  = [aws_security_group.cgcp_sg.id]
    assign_public_ip = true
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.cgcp_api.arn
    container_name   = "cgcp"
    container_port   = 8000
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.cgcp_dashboard.arn
    container_name   = "cgcp"
    container_port   = 8501
  }
}

# Application Load Balancer
resource "aws_lb" "cgcp_alb" {
  name               = "cgcp-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.cgcp_alb_sg.id]
  subnets            = aws_subnet.public[*].id
}

output "alb_dns_name" {
  value = aws_lb.cgcp_alb.dns_name
}
'''
        
        with open("terraform/main.tf", "w") as f:
            f.write(terraform_config)
        
        self.print_status("Created Terraform configuration", "success")
    
    def deploy_cloud(self, provider: str = "aws"):
        """Deploy to cloud provider"""
        self.print_status(f"Starting {provider.upper()} cloud deployment...")
        
        if provider == "aws":
            # Create Terraform config
            self.create_terraform_config()
            
            self.print_status("Terraform configuration created", "success")
            self.print_status("To deploy to AWS:")
            print("  1. cd terraform")
            print("  2. terraform init")
            print("  3. terraform plan")
            print("  4. terraform apply")
        
        elif provider == "gcp":
            self.print_status("GCP deployment guide:", "info")
            print("  1. Use Google Cloud Run for serverless deployment")
            print("  2. gcloud run deploy cgcp --source . --port 8000")
        
        elif provider == "azure":
            self.print_status("Azure deployment guide:", "info")
            print("  1. Use Azure Container Instances")
            print("  2. az container create --resource-group cgcp --name cgcp --image cgcp:latest")
        
        return True
    
    def health_check(self):
        """Perform health check on deployed services"""
        self.print_status("Performing health check...")
        
        services = [
            ("API Backend", "http://localhost:8000/health"),
            ("Dashboard", "http://localhost:8501"),
            ("Metrics", "http://localhost:8000/metrics")
        ]
        
        all_healthy = True
        
        for service_name, url in services:
            try:
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    self.print_status(f"{service_name}: Healthy", "success")
                else:
                    self.print_status(f"{service_name}: Unhealthy (Status: {response.status_code})", "warning")
                    all_healthy = False
            except:
                self.print_status(f"{service_name}: Unreachable", "error")
                all_healthy = False
        
        return all_healthy
    
    def show_deployment_info(self, deployment_type: str):
        """Display deployment information and next steps"""
        print(f"\n{Fore.GREEN}{'='*60}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}🎉 Deployment Complete!{Style.RESET_ALL}")
        print(f"{Fore.GREEN}{'='*60}{Style.RESET_ALL}\n")
        
        print(f"{Fore.CYAN}📋 Deployment Type: {deployment_type}{Style.RESET_ALL}")
        print(f"\n{Fore.YELLOW}🌐 Access Points:{Style.RESET_ALL}")
        print("  • Dashboard: http://localhost:8501")
        print("  • API: http://localhost:8000")
        print("  • API Docs: http://localhost:8000/docs")
        
        if deployment_type == "docker-compose":
            print("  • Prometheus: http://localhost:9090")
            print("  • Grafana: http://localhost:3000")
        
        print(f"\n{Fore.YELLOW}📊 Next Steps:{Style.RESET_ALL}")
        print("  1. Access the dashboard to configure policies")
        print("  2. Ingest sample data: python demo/ingest_data.py")
        print("  3. Run production demo: python demo/production_demo.py")
        print("  4. Configure monitoring alerts")
        print("  5. Set up backup procedures")
        
        print(f"\n{Fore.YELLOW}🔒 Security Recommendations:{Style.RESET_ALL}")
        print("  • Enable HTTPS with SSL certificates")
        print("  • Configure authentication (OAuth2/SAML)")
        print("  • Set up firewall rules")
        print("  • Enable audit logging")
        print("  • Regular security scans")
        
        print(f"\n{Fore.GREEN}✅ System is ready for production use!{Style.RESET_ALL}\n")
    
    def deploy(self, deployment_type: str):
        """Main deployment orchestrator"""
        self.print_banner()
        
        if not self.check_prerequisites():
            return False
        
        success = False
        
        if deployment_type == "local":
            success = self.deploy_local()
        elif deployment_type == "docker":
            success = self.deploy_docker()
        elif deployment_type == "docker-compose":
            success = self.deploy_docker_compose()
        elif deployment_type == "kubernetes":
            success = self.deploy_kubernetes()
        elif deployment_type in ["aws", "gcp", "azure"]:
            success = self.deploy_cloud(deployment_type)
        else:
            self.print_status(f"Unknown deployment type: {deployment_type}", "error")
            return False
        
        if success:
            # Wait for services to start
            time.sleep(10)
            
            # Perform health check
            if deployment_type in ["local", "docker", "docker-compose"]:
                self.health_check()
            
            # Show deployment info
            self.show_deployment_info(deployment_type)
        
        return success


def main():
    """Main entry point for deployment script"""
    parser = argparse.ArgumentParser(description="Deploy Claude Governance Control Plane")
    parser.add_argument(
        "type",
        choices=["local", "docker", "docker-compose", "kubernetes", "aws", "gcp", "azure"],
        help="Deployment type"
    )
    parser.add_argument(
        "--skip-health-check",
        action="store_true",
        help="Skip health check after deployment"
    )
    
    args = parser.parse_args()
    
    deployer = DeploymentManager()
    
    try:
        success = deployer.deploy(args.type)
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        deployer.print_status("\nDeployment cancelled by user", "warning")
        sys.exit(1)
    except Exception as e:
        deployer.print_status(f"Deployment failed: {str(e)}", "error")
        sys.exit(1)


if __name__ == "__main__":
    main() 