# 🧪 Local CI Testing

Reproduis l'environnement GitHub Actions localement avec Docker.

## 📋 Prérequis

- **Docker** (version 20.10+)
- **Docker Compose** (version 1.29+)
- **PowerShell** (Windows) ou **Bash** (Linux/macOS)

## 🚀 Démarrage Rapide

### Windows (PowerShell)

```powershell
# Test CI simple
.\test-ci.ps1

# Avec logs en direct
.\test-ci.ps1 -Logs

# Nettoyer et reconstruire
.\test-ci.ps1 -Clean -Rebuild

# Voir les logs après
docker-compose -f docker-compose.ci.yml logs app
```

### Linux/macOS (Bash)

```bash
# Test CI simple
chmod +x test-ci.sh
./test-ci.sh

# Avec logs en direct
./test-ci.sh --logs

# Nettoyer et reconstruire
./test-ci.sh --clean --rebuild

# Voir les logs après
docker-compose -f docker-compose.ci.yml logs app
```

## 📊 Qu'est-ce qui est testé?

Le script teste exactement la même chose que GitHub Actions:

✅ **Migrations** - Applique toutes les migrations Alembic  
✅ **Tests Backend** - Lance pytest avec couverture  
✅ **Format (Black)** - Vérifie le formatage Python (100 chars)  
✅ **Import Sort (isort)** - Vérifie l'ordre des imports  
✅ **Lint (Flake8)** - Analyse de code statique  
✅ **Type Check (mypy)** - Vérification de type Python  

## 📁 Fichiers

- `Dockerfile.ci` - Image Docker avec toutes les dépendances
- `docker-compose.ci.yml` - PostgreSQL, Redis, App
- `test-ci.ps1` - Script de lancement Windows
- `test-ci.sh` - Script de lancement Linux/macOS

## 🔧 Options Avancées

### Voir les logs en temps réel

```bash
# PowerShell
.\test-ci.ps1 -Logs

# Bash
./test-ci.sh --logs
```

### Nettoyer les conteneurs

```bash
# PowerShell
.\test-ci.ps1 -Clean

# Bash
./test-ci.sh --clean
```

### Reconstruire l'image

```bash
# PowerShell
.\test-ci.ps1 -Rebuild

# Bash
./test-ci.sh --rebuild
```

### Arrêter les services

```bash
docker-compose -f docker-compose.ci.yml down
```

### Supprimer tout

```bash
docker-compose -f docker-compose.ci.yml down -v
```

## 📊 Coverage Report

Après les tests, un rapport de couverture est généré:

```bash
# Voir le rapport HTML
start htmlcov/index.html  # Windows
open htmlcov/index.html   # macOS
firefox htmlcov/index.html # Linux
```

## 🐛 Dépannage

### "postgres: command not found"

```bash
# Les services ne sont pas prêts, attendez 30 secondes
docker-compose -f docker-compose.ci.yml ps
```

### "Connection refused"

```bash
# Vérifiez que les services sont en bonne santé
docker-compose -f docker-compose.ci.yml ps

# Vérifiez les logs PostgreSQL
docker-compose -f docker-compose.ci.yml logs postgres
```

### Tests échouent en Docker mais pas localement

Cela signifie que l'environnement Docker est différent de votre machine locale.  
C'est normal! C'est exactement ce que GitHub Actions va faire.

### Forcer une reconstruction complète

```bash
# PowerShell
.\test-ci.ps1 -Clean -Rebuild

# Bash
./test-ci.sh --clean --rebuild
```

## 💡 Tips

1. **Première exécution** - Prendra 2-3 minutes (téléchargement des images)
2. **Exécutions suivantes** - Prendra 30-60 secondes (cache Docker)
3. **Volume montée** - Les fichiers locaux sont synchronisés avec le conteneur
4. **Modifications de code** - Les tests s'exécutent immédiatement avec le nouveau code

## 🔍 Voir ce qui se passe

```bash
# Tous les conteneurs
docker ps -a

# Logs PostgreSQL
docker-compose -f docker-compose.ci.yml logs postgres

# Logs Redis
docker-compose -f docker-compose.ci.yml logs redis

# Logs App
docker-compose -f docker-compose.ci.yml logs app

# Logs en temps réel
docker-compose -f docker-compose.ci.yml logs -f app
```

## 🚨 Si la CI échoue

1. Regardez le message d'erreur dans la console
2. Vérifiez les logs: `docker-compose -f docker-compose.ci.yml logs app`
3. Vérifiez le type d'erreur:
   - **Migrations** - Problème de base de données
   - **Tests** - Problème de logique
   - **Black** - Problème de formatage
   - **isort** - Problème d'ordre d'imports
   - **Flake8** - Problème de style
   - **mypy** - Problème de types Python

4. Fixez le problème localement et relancez

## 📝 Variables d'environnement

Le conteneur utilise les mêmes variables que GitHub Actions:

```
DATABASE_URL: postgresql://keneyapp:keneyapp_secure_pass@postgres:5432/keneyapp
REDIS_HOST: redis
REDIS_PORT: 6379
SECRET_KEY: test-secret-key
ENCRYPTION_KEY: test-encryption-key-32-chars-exactly!!
```

Si vous avez besoin de différentes valeurs, modifiez `docker-compose.ci.yml`.
