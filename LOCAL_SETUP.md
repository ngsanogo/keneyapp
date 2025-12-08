# 🧘 Local Development - Simple is Beautiful

Ce répertoire contient tout ce dont vous avez besoin pour développer **localement** avec Docker.

## 🚀 Quick Start

```bash
# Windows
.\start.ps1

# macOS/Linux
./start.sh

# Ou directement
docker-compose -f docker-compose.local.yml up -d
make -f Makefile.local setup
```

## 📦 What You Get

- ✅ **PostgreSQL 15** - Database
- ✅ **Redis 7** - Cache & Message Broker
- ✅ **FastAPI** - Backend API
- ✅ **Celery** - Async Tasks
- ✅ **Flower** - Task Monitoring (http://localhost:5555)
- ✅ **Prometheus** - Metrics (http://localhost:9090)
- ✅ **Grafana** - Dashboards (http://localhost:3000)
- ✅ **pgAdmin** - Database UI (http://localhost:5050)

## 🎯 Core Commands

```bash
# View all commands
make -f Makefile.local help

# Start stack
make -f Makefile.local up

# Run tests
make -f Makefile.local test

# View logs
make -f Makefile.local logs

# Access shell
make -f Makefile.local shell

# Health check
make -f Makefile.local health
```

## 📝 Files Included

- `docker-compose.local.yml` - Complete Docker setup (11 services)
- `start.ps1` / `start.sh` - Startup scripts
- `Makefile.local` - 60+ helpful commands
- `init-db.sql` - Database initialization
- `monitoring/` - Prometheus & Grafana configs
- `LOCAL_DEVELOPMENT.md` - Full documentation

## ⚙️ Configuration

Environment variables in `.env` (auto-created):
- Database credentials
- Redis password
- API ports
- Security keys

Edit `.env` and restart containers:
```bash
docker-compose -f docker-compose.local.yml restart
```

## 🔧 Philosophy

**Simple is Beautiful** 🧘

- No GitHub Actions (free account = limited credits)
- No CI/CD overhead
- Just LOCAL development with Docker
- Everything runs in containers
- Full autonomy, full freedom

## 📚 Documentation

See `LOCAL_DEVELOPMENT.md` for:
- Detailed setup guide
- Service descriptions
- Troubleshooting
- Development workflows

## ⚠️ Important Notes

⚠️ Default credentials are **ONLY for local development**
- Change them in `.env` if needed
- Do NOT commit `.env` to git
- Keep sensitive data local

## 🎉 Ready?

```bash
# Windows
.\start.ps1

# Linux/Mac
./start.sh
```

Happy coding! 🚀
