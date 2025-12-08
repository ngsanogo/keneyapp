#!/bin/bash
# Script de démarrage complet de KeneyApp en Docker local
# Usage: chmod +x start.sh && ./start.sh

set -e

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Configuration
PROJECT_NAME="keneyapp"
COMPOSE_FILE="docker-compose.local.yml"

# Bannière
clear
echo -e "${CYAN}"
echo "╔════════════════════════════════════════════════════════╗"
echo "║      🏥 KeneyApp Local Development Stack               ║"
echo "║           Healthcare Platform with Docker              ║"
echo "╚════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Créer le fichier .env s'il n'existe pas
if [ ! -f .env ]; then
    echo -e "${YELLOW}📝 Creating .env file...${NC}"
    cat > .env << 'EOF'
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
EOF
    echo -e "${GREEN}✅ .env file created${NC}"
else
    echo -e "${BLUE}ℹ️  .env file already exists${NC}"
fi

# Vérifier Docker
echo ""
echo -e "${YELLOW}📋 Checking prerequisites...${NC}"

if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Docker found${NC}"

if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ Docker Compose is not installed${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Docker Compose found${NC}"

# Créer les répertoires nécessaires
echo ""
echo -e "${YELLOW}📁 Creating required directories...${NC}"
mkdir -p ./uploads ./ai_artifacts ./ai_logs ./monitoring ./logs

# Créer les fichiers de configuration monitoring
if [ ! -f ./monitoring/prometheus.yml ]; then
    echo -e "${YELLOW}📝 Creating Prometheus configuration...${NC}"
    mkdir -p ./monitoring
    cat > ./monitoring/prometheus.yml << 'EOF'
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'keneyapp'
    static_configs:
      - targets: ['localhost:8000']
EOF
fi

if [ ! -f ./monitoring/grafana-datasource.yml ]; then
    echo -e "${YELLOW}📝 Creating Grafana datasource configuration...${NC}"
    cat > ./monitoring/grafana-datasource.yml << 'EOF'
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    editable: true
EOF
fi

# Arrêter les containers existants
echo ""
echo -e "${YELLOW}⏹️  Stopping existing containers...${NC}"
docker-compose -f $COMPOSE_FILE down 2>/dev/null || true

# Nettoyer les images
echo -e "${YELLOW}🧹 Cleaning up dangling images...${NC}"
docker image prune -f 2>/dev/null || true

# Construire les images
echo ""
echo -e "${YELLOW}🔨 Building Docker images...${NC}"
docker-compose -f $COMPOSE_FILE build --no-cache

# Démarrer les services
echo ""
echo -e "${YELLOW}🚀 Starting services...${NC}"
docker-compose -f $COMPOSE_FILE up -d

# Attendre le démarrage
echo ""
echo -e "${YELLOW}⏳ Waiting for services to start...${NC}"
sleep 10

# Afficher l'état
echo ""
echo -e "${YELLOW}📊 Service status:${NC}"
docker-compose -f $COMPOSE_FILE ps

# Vérifier la santé
echo ""
echo -e "${YELLOW}🏥 Health checks:${NC}"

# Backend health
echo -n "  Backend: "
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅${NC}"
else
    echo -e "${YELLOW}⏳ (starting)${NC}"
fi

# PostgreSQL health
echo -n "  PostgreSQL: "
if docker exec keneyapp_postgres pg_isready -U keneyapp > /dev/null 2>&1; then
    echo -e "${GREEN}✅${NC}"
else
    echo -e "${RED}❌${NC}"
fi

# Redis health
echo -n "  Redis: "
if docker exec keneyapp_redis redis-cli -a redis_secure_pass ping > /dev/null 2>&1; then
    echo -e "${GREEN}✅${NC}"
else
    echo -e "${RED}❌${NC}"
fi

# Afficher les URLs
echo ""
echo -e "${CYAN}════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✅ KeneyApp is running!${NC}"
echo -e "${CYAN}════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${BLUE}📚 Available Services:${NC}"
echo ""
echo -e "  ${CYAN}API & Documentation:${NC}"
echo "    • FastAPI:    ${CYAN}http://localhost:8000${NC}"
echo "    • Swagger:    ${CYAN}http://localhost:8000/docs${NC}"
echo "    • ReDoc:      ${CYAN}http://localhost:8000/redoc${NC}"
echo ""
echo -e "  ${CYAN}Monitoring & Analytics:${NC}"
echo "    • Flower:     ${CYAN}http://localhost:5555${NC}   (Celery tasks)"
echo "    • Prometheus: ${CYAN}http://localhost:9090${NC}   (Metrics)"
echo "    • Grafana:    ${CYAN}http://localhost:3000${NC}   (Dashboards)"
echo ""
echo -e "  ${CYAN}Database Management:${NC}"
echo "    • pgAdmin:    ${CYAN}http://localhost:5050${NC}"
echo "      Email: admin@keneyapp.local"
echo "      Password: admin"
echo ""
echo -e "  ${CYAN}Cache:${NC}"
echo "    • Redis:      localhost:6379"
echo ""
echo -e "${BLUE}🛠️  Useful Commands:${NC}"
echo ""
echo "  # View logs"
echo "    docker-compose -f $COMPOSE_FILE logs -f backend"
echo ""
echo "  # Access container shell"
echo "    docker exec -it keneyapp_backend bash"
echo ""
echo "  # Run database migrations"
echo "    docker exec -it keneyapp_backend alembic upgrade head"
echo ""
echo "  # Run tests"
echo "    docker exec -it keneyapp_backend pytest tests/ -v"
echo ""
echo "  # Run AI analysis"
echo "    docker exec -it keneyapp_backend python scripts/ai_improvement.py --task-type full_analysis"
echo ""
echo "  # Format code"
echo "    docker exec -it keneyapp_backend black app tests"
echo ""
echo "  # Stop all services"
echo "    docker-compose -f $COMPOSE_FILE down"
echo ""
echo "  # Stop and remove volumes (full cleanup)"
echo "    docker-compose -f $COMPOSE_FILE down -v"
echo ""
echo -e "${CYAN}════════════════════════════════════════════════════════${NC}"
echo ""
