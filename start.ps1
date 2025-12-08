# Script de démarrage complet de KeneyApp en Docker local pour Windows
# Usage: .\start.ps1

# Set error handling
$ErrorActionPreference = "Stop"

# Couleurs
$cyan = "`e[36m"
$green = "`e[32m"
$yellow = "`e[33m"
$blue = "`e[34m"
$red = "`e[31m"
$reset = "`e[0m"

# Configuration
$composeFile = "docker-compose.local.yml"

# Bannière
Clear-Host
Write-Host "${cyan}" -NoNewline
Write-Host "╔════════════════════════════════════════════════════════╗"
Write-Host "║      🏥 KeneyApp Local Development Stack               ║"
Write-Host "║           Healthcare Platform with Docker              ║"
Write-Host "╚════════════════════════════════════════════════════════╝"
Write-Host "${reset}"

# Créer le fichier .env s'il n'existe pas
if (-not (Test-Path ".env")) {
    Write-Host "${yellow}📝 Creating .env file...${reset}"
    @"
# ============================================
# KeneyApp Local Development Environment
# ============================================

# Database Configuration
DB_USER=keneyapp
DB_PASSWORD=keneyapp_secure_pass
DB_NAME=keneyapp
DB_PORT=5432

# Redis Configuration
REDIS_PASSWORD=redis_secure_pass
REDIS_PORT=6379

# Security
SECRET_KEY=dev-secret-key-change-this-in-production
ENCRYPTION_KEY=dev-encryption-key-32-chars-exactly!!

# CORS Origins
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000,http://localhost:8080

# Environment
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=INFO

# API Ports
BACKEND_PORT=8000
FLOWER_PORT=5555
PROMETHEUS_PORT=9090
GRAFANA_PORT=3000
PGADMIN_PORT=5050

# pgAdmin Configuration
PGADMIN_EMAIL=admin@keneyapp.local
PGADMIN_PASSWORD=admin

# Grafana Configuration
GRAFANA_PASSWORD=admin
"@ | Out-File -FilePath ".env" -Encoding UTF8
    Write-Host "${green}✅ .env file created${reset}"
} else {
    Write-Host "${blue}ℹ️  .env file already exists${reset}"
}

# Vérifier Docker
Write-Host ""
Write-Host "${yellow}📋 Checking prerequisites...${reset}"

try {
    docker --version > $null
    Write-Host "${green}✅ Docker found${reset}"
} catch {
    Write-Host "${red}❌ Docker is not installed${reset}"
    exit 1
}

try {
    docker-compose --version > $null
    Write-Host "${green}✅ Docker Compose found${reset}"
} catch {
    Write-Host "${red}❌ Docker Compose is not installed${reset}"
    exit 1
}

# Créer les répertoires nécessaires
Write-Host ""
Write-Host "${yellow}📁 Creating required directories...${reset}"
@("uploads", "ai_artifacts", "ai_logs", "monitoring", "logs") | ForEach-Object {
    if (-not (Test-Path $_)) {
        New-Item -ItemType Directory -Path $_ -Force > $null
    }
}

# Créer les fichiers de configuration monitoring
if (-not (Test-Path "monitoring/prometheus.yml")) {
    Write-Host "${yellow}📝 Creating Prometheus configuration...${reset}"
    @"
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'keneyapp'
    static_configs:
      - targets: ['localhost:8000']
"@ | Out-File -FilePath "monitoring/prometheus.yml" -Encoding UTF8
}

if (-not (Test-Path "monitoring/grafana-datasource.yml")) {
    Write-Host "${yellow}📝 Creating Grafana datasource configuration...${reset}"
    @"
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    editable: true
"@ | Out-File -FilePath "monitoring/grafana-datasource.yml" -Encoding UTF8
}

# Arrêter les containers existants
Write-Host ""
Write-Host "${yellow}⏹️  Stopping existing containers...${reset}"
try {
    docker-compose -f $composeFile down 2>$null
} catch {}

# Nettoyer les images
Write-Host "${yellow}🧹 Cleaning up dangling images...${reset}"
try {
    docker image prune -f 2>$null
} catch {}

# Construire les images
Write-Host ""
Write-Host "${yellow}🔨 Building Docker images...${reset}"
docker-compose -f $composeFile build --no-cache

# Démarrer les services
Write-Host ""
Write-Host "${yellow}🚀 Starting services...${reset}"
docker-compose -f $composeFile up -d

# Attendre le démarrage
Write-Host ""
Write-Host "${yellow}⏳ Waiting for services to start...${reset}"
Start-Sleep -Seconds 10

# Afficher l'état
Write-Host ""
Write-Host "${yellow}📊 Service status:${reset}"
docker-compose -f $composeFile ps

# Vérifier la santé
Write-Host ""
Write-Host "${yellow}🏥 Health checks:${reset}"

# Backend health
Write-Host -NoNewline "  Backend: "
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -ErrorAction SilentlyContinue
    if ($response.StatusCode -eq 200) {
        Write-Host "${green}✅${reset}"
    }
} catch {
    Write-Host "${yellow}⏳ (starting)${reset}"
}

# PostgreSQL health
Write-Host -NoNewline "  PostgreSQL: "
try {
    $output = docker exec keneyapp_postgres pg_isready -U keneyapp 2>$null
    Write-Host "${green}✅${reset}"
} catch {
    Write-Host "${red}❌${reset}"
}

# Redis health
Write-Host -NoNewline "  Redis: "
try {
    $output = docker exec keneyapp_redis redis-cli -a redis_secure_pass ping 2>$null
    Write-Host "${green}✅${reset}"
} catch {
    Write-Host "${red}❌${reset}"
}

# Afficher les URLs
Write-Host ""
Write-Host "${cyan}════════════════════════════════════════════════════════${reset}"
Write-Host "${green}✅ KeneyApp is running!${reset}"
Write-Host "${cyan}════════════════════════════════════════════════════════${reset}"
Write-Host ""
Write-Host "${blue}📚 Available Services:${reset}"
Write-Host ""
Write-Host "${cyan}  API & Documentation:${reset}"
Write-Host "    • FastAPI:    ${cyan}http://localhost:8000${reset}"
Write-Host "    • Swagger:    ${cyan}http://localhost:8000/docs${reset}"
Write-Host "    • ReDoc:      ${cyan}http://localhost:8000/redoc${reset}"
Write-Host ""
Write-Host "${cyan}  Monitoring & Analytics:${reset}"
Write-Host "    • Flower:     ${cyan}http://localhost:5555${reset}   (Celery tasks)"
Write-Host "    • Prometheus: ${cyan}http://localhost:9090${reset}   (Metrics)"
Write-Host "    • Grafana:    ${cyan}http://localhost:3000${reset}   (Dashboards)"
Write-Host ""
Write-Host "${cyan}  Database Management:${reset}"
Write-Host "    • pgAdmin:    ${cyan}http://localhost:5050${reset}"
Write-Host "      Email: admin@keneyapp.local"
Write-Host "      Password: admin"
Write-Host ""
Write-Host "${cyan}  Cache:${reset}"
Write-Host "    • Redis:      localhost:6379"
Write-Host ""
Write-Host "${blue}🛠️  Useful Commands:${reset}"
Write-Host ""
Write-Host "  # View logs"
Write-Host "    docker-compose -f $composeFile logs -f backend"
Write-Host ""
Write-Host "  # Access container shell"
Write-Host "    docker exec -it keneyapp_backend bash"
Write-Host ""
Write-Host "  # Run database migrations"
Write-Host "    docker exec -it keneyapp_backend alembic upgrade head"
Write-Host ""
Write-Host "  # Run tests"
Write-Host "    docker exec -it keneyapp_backend pytest tests/ -v"
Write-Host ""
Write-Host "  # Stop all services"
Write-Host "    docker-compose -f $composeFile down"
Write-Host ""
Write-Host "  # Stop and remove volumes (full cleanup)"
Write-Host "    docker-compose -f $composeFile down -v"
Write-Host ""
Write-Host "${cyan}════════════════════════════════════════════════════════${reset}"
Write-Host ""
