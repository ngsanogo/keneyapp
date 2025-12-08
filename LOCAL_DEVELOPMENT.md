# 🚀 KeneyApp Local Development Environment

Cette documentation vous guide pour démarrer l'environnement de développement local complet de KeneyApp avec Docker.

Simple. Clean. Zen. 🧘

## 📋 Prérequis

- **Docker** 20.10+ [Installer](https://docs.docker.com/get-docker/)
- **Docker Compose** 1.29+ [Installer](https://docs.docker.com/compose/install/)
- **Windows Users**: PowerShell 5.1+ ou Git Bash
- **macOS/Linux Users**: Bash ou Zsh
- **8GB RAM minimum** (16GB recommandé pour la suite complète)
- **10GB disk space** pour les images et volumes

## 🎯 Démarrage Rapide

### Option 1: Windows PowerShell

```powershell
# Rendre le script exécutable et lancer
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
.\start.ps1
```

### Option 2: macOS/Linux (Bash)

```bash
# Rendre le script exécutable et lancer
chmod +x start.sh
./start.sh
```

### Option 3: Docker Compose Direct

```bash
# Créer le fichier .env
cp .env.example .env

# Démarrer tous les services
docker-compose -f docker-compose.local.yml up -d

# Vérifier l'état
docker-compose -f docker-compose.local.yml ps
```

### Option 4: Makefile (Recommandé)

```bash
# Setup complet (build, démarrage, migrations, seeding)
make -f Makefile.local setup

# Ou étapes individuelles
make -f Makefile.local build    # Construire les images
make -f Makefile.local up       # Démarrer les services
make -f Makefile.local db-migrate  # Migrations
make -f Makefile.local db-seed     # Seeding
```

## 📚 Services Disponibles

### 🌐 API & Documentation

| Service | Port | URL | Description |
|---------|------|-----|-------------|
| FastAPI | 8000 | http://localhost:8000 | API REST principale |
| Swagger | 8000 | http://localhost:8000/docs | Documentation interactive |
| ReDoc | 8000 | http://localhost:8000/redoc | Documentation alternative |
| Health | 8000 | http://localhost:8000/health | Health check endpoint |
| Metrics | 8000 | http://localhost:8000/metrics | Prometheus metrics |

### 📊 Monitoring & Analytics

| Service | Port | URL | Fonction |
|---------|------|-----|----------|
| Flower | 5555 | http://localhost:5555 | Celery task monitoring |
| Prometheus | 9090 | http://localhost:9090 | Metrics collection |
| Grafana | 3000 | http://localhost:3000 | Metrics visualization |

**Grafana Credentials:**
- Email: admin
- Password: admin

### 💾 Database Management

| Service | Port | Access | Description |
|---------|------|--------|-------------|
| PostgreSQL | 5432 | localhost:5432 | Database principal |
| pgAdmin | 5050 | http://localhost:5050 | PostgreSQL UI |
| Redis | 6379 | localhost:6379 | Cache & Message Broker |

**pgAdmin Credentials:**
- Email: admin@keneyapp.local
- Password: admin

### 🐍 Backend Services

| Service | Role | Status |
|---------|------|--------|
| backend | FastAPI API | Running on port 8000 |
| celery_worker | Async task processor | 4 concurrency workers |
| celery_beat | Task scheduler | Runs scheduled tasks |

## 🛠️ Commandes Courantes

### Démarrage & Arrêt

```bash
# Démarrer tous les services
make -f Makefile.local up

# Arrêter tous les services
make -f Makefile.local down

# Redémarrer tous les services
make -f Makefile.local restart

# Voir les logs en temps réel
make -f Makefile.local logs

# Logs spécifiques
make -f Makefile.local logs-backend    # Logs du backend
make -f Makefile.local logs-worker     # Logs du worker Celery
make -f Makefile.local logs-flower     # Logs de Flower
```

### Accès aux Conteneurs

```bash
# Shell du backend
make -f Makefile.local shell

# Shell du worker Celery
make -f Makefile.local shell-worker

# Shell PostgreSQL
make -f Makefile.local shell-db

# Shell Redis
make -f Makefile.local shell-redis
```

### Base de Données

```bash
# Exécuter les migrations
make -f Makefile.local db-migrate

# Seeder la base avec des données de démo
make -f Makefile.local db-seed

# Reset complet (drop, migrate, seed)
make -f Makefile.local db-reset

# Créer un backup
make -f Makefile.local db-backup
```

### Tests & Qualité du Code

```bash
# Exécuter les tests (exclut les tests lents)
make -f Makefile.local test

# Tous les tests
make -f Makefile.local test-all

# Tests avec couverture
make -f Makefile.local test-coverage

# Tests rapides
make -f Makefile.local test-fast

# Linting (flake8, mypy)
make -f Makefile.local lint

# Vérifier le formatage
make -f Makefile.local format-check

# Formater le code
make -f Makefile.local format

# Tous les checks de qualité
make -f Makefile.local quality
```

### IA & Améliorations

```bash
# Analyse complète du codebase
make -f Makefile.local ai-analyze

# Suggestions d'optimisation
make -f Makefile.local ai-optimize

# Audit de sécurité
make -f Makefile.local ai-security
```

### Utilitaires

```bash
# Voir l'état des services
make -f Makefile.local health

# Afficher toutes les URLs disponibles
make -f Makefile.local urls

# Afficher les conteneurs actifs
make -f Makefile.local ps

# Nettoyer les ressources Docker inutilisées
make -f Makefile.local prune

# Nettoyage profond (supprime tout)
make -f Makefile.local clean

# Construire les images
make -f Makefile.local build

# Construire sans cache
make -f Makefile.local build-nocache
```

### Commandes Docker Compose Directs

```bash
# Si vous préférez les commandes docker-compose directement
docker-compose -f docker-compose.local.yml up -d
docker-compose -f docker-compose.local.yml down
docker-compose -f docker-compose.local.yml logs -f
docker-compose -f docker-compose.local.yml ps
docker-compose -f docker-compose.local.yml exec backend bash
```

## 🔧 Configuration

### Variables d'Environnement (.env)

Le fichier `.env` est créé automatiquement au premier lancement. Vous pouvez le modifier :

```env
# Database
DB_USER=keneyapp
DB_PASSWORD=keneyapp_secure_pass
DB_NAME=keneyapp
DB_PORT=5432

# Redis
REDIS_PASSWORD=redis_secure_pass
REDIS_PORT=6379

# Security
SECRET_KEY=dev-secret-key-change-this-in-production
ENCRYPTION_KEY=dev-encryption-key-32-chars-exactly!!

# API Configuration
BACKEND_PORT=8000
FLOWER_PORT=5555
PROMETHEUS_PORT=9090
GRAFANA_PORT=3000
PGADMIN_PORT=5050

# Environment
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=INFO
```

Après modification de `.env`:
```bash
docker-compose -f docker-compose.local.yml restart
```

## 🏗️ Architecture

```
KeneyApp Local Stack
├── Frontend (React 18)
│   └── Port 3000 (non inclus dans ce stack, démarre séparément)
│
├── Backend Services
│   ├── FastAPI Backend (8000)
│   ├── Celery Worker (async tasks)
│   └── Celery Beat (scheduler)
│
├── Data & Caching
│   ├── PostgreSQL 15 (5432)
│   ├── Redis 7 (6379)
│   └── pgAdmin (5050)
│
└── Monitoring & Analytics
    ├── Flower (5555) - Celery monitoring
    ├── Prometheus (9090) - Metrics
    └── Grafana (3000) - Dashboards
```

## 📡 Health Checks

```bash
# Vérifier la santé du backend
curl http://localhost:8000/health

# Vérifier les métriques Prometheus
curl http://localhost:8000/metrics

# Test PostgreSQL
docker exec keneyapp_postgres pg_isready -U keneyapp

# Test Redis
docker exec keneyapp_redis redis-cli -a redis_secure_pass ping

# Vérifier les services Docker
make -f Makefile.local health
```

## 🐛 Dépannage

### Les services ne démarrent pas

```bash
# Vérifier les erreurs
docker-compose -f docker-compose.local.yml logs

# Réinstaller complètement
make -f Makefile.local clean
make -f Makefile.local setup
```

### Problèmes de connexion à la base de données

```bash
# Vérifier l'état de PostgreSQL
docker exec keneyapp_postgres pg_isready -U keneyapp

# Vérifier les logs
make -f Makefile.local logs | grep postgres

# Redémarrer PostgreSQL
docker-compose -f docker-compose.local.yml restart postgres
```

### Problèmes de Redis

```bash
# Test la connexion
docker exec keneyapp_redis redis-cli -a redis_secure_pass ping

# Voir les logs
make -f Makefile.local logs | grep redis

# Redémarrer Redis
docker-compose -f docker-compose.local.yml restart redis
```

### Backend ne répond pas

```bash
# Vérifier l'état
make -f Makefile.local logs-backend

# Redémarrer
docker-compose -f docker-compose.local.yml restart backend

# Accéder au shell pour déboguer
make -f Makefile.local shell
```

### Problèmes de ports

```bash
# Voir quels ports sont en utilisation
netstat -ano | findstr :8000  # Windows PowerShell
lsof -i :8000                  # macOS/Linux

# Changer le port dans .env
# Puis redémarrer les services
```

## 📊 Monitoring

### Grafana (http://localhost:3000)

1. **Login**: admin / admin
2. **Changer le mot de passe**: Settings → Password
3. **Ajouter des dashboards**: + → Import
4. **Datasource**: Prometheus (pré-configurée)

### Prometheus (http://localhost:9090)

- **Scrape targets**: Status → Targets
- **Metrics graph**: Graph
- **Requêtes d'exemple**:
  - `up` - Service availability
  - `http_requests_total` - Total requests
  - `http_request_duration_seconds` - Request latency

### Flower (http://localhost:5555)

- **Active tasks**: Voir les tâches Celery en cours
- **Task history**: Historique complet
- **Worker stats**: Performance des workers
- **Queue monitoring**: État des queues

## 🚀 Workflows de Développement

### Développement Backend

```bash
# 1. Démarrer le stack
make -f Makefile.local up

# 2. Modifier le code (auto-reload activé)

# 3. Consulter les logs
make -f Makefile.local logs-backend

# 4. Tester les changements
curl http://localhost:8000/health

# 5. Exécuter les tests
make -f Makefile.local test
```

### Ajout d'une Migration

```bash
# 1. Accéder au conteneur backend
make -f Makefile.local shell

# 2. Créer la migration
alembic revision --autogenerate -m "description"

# 3. Appliquer
alembic upgrade head

# 4. Quitter et vérifier les logs
exit
make -f Makefile.local logs-backend
```

### Debugging avec les Logs

```bash
# Logs temps réel de tous les services
make -f Makefile.local logs

# Logs du backend uniquement
make -f Makefile.local logs-backend

# Logs avec filtrage
docker-compose -f docker-compose.local.yml logs --tail=100 backend

# Logs d'une période (derniers 5 minutes)
docker-compose -f docker-compose.local.yml logs --since 5m backend
```

## 🔒 Sécurité (Développement)

⚠️ **Important**: Les credentials par défaut sont **UNIQUEMENT** pour le développement local!

```env
# À CHANGER en production:
SECRET_KEY=changez-ceci!
ENCRYPTION_KEY=changez-ceci!
DB_PASSWORD=changez-ceci!
REDIS_PASSWORD=changez-ceci!
PGADMIN_PASSWORD=changez-ceci!
GRAFANA_PASSWORD=changez-ceci!
```

## 📦 Volumes & Persistence

Les volumes Docker persistent les données :

```
postgres_data      → Database files
redis_data         → Cache/queue data
prometheus_data    → Metrics storage
grafana_data       → Grafana dashboards
pgadmin_data       → pgAdmin configuration
flower_data        → Flower task history
uploads            → User uploads
logs               → Application logs
```

**Important**: `make clean` supprime TOUS les volumes!

## 🆘 Support & Help

```bash
# Afficher tous les targets Makefile
make -f Makefile.local help

# Afficher l'état détaillé
make -f Makefile.local health

# Afficher toutes les URLs
make -f Makefile.local urls

# Voir les erreurs
make -f Makefile.local logs | grep -i error
```

## 🎓 Ressources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Reference](https://docs.docker.com/compose/compose-file/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Redis Documentation](https://redis.io/documentation)
- [Celery Documentation](https://docs.celeryproject.io/)

## 📝 Notes

- **Auto-reload**: Le backend redémarre automatiquement lors de changements de code
- **Database migrations**: Exécutées au démarrage via `alembic`
- **Monitoring**: Actif par défaut, accessible via Grafana
- **Tasks asynchrones**: Traitées par Celery avec Flower pour monitoring
- **Development mode**: DEBUG=true, permettant plus de verbosité

## 🎉 Prêt?

```bash
# Démarrer et profiter!
./start.ps1        # Windows
./start.sh         # macOS/Linux
make -f Makefile.local setup  # Anywhere
```

Happy coding! 🚀
