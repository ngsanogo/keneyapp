# Local CI/CD Testing with Act

Ce guide explique comment tester vos workflows GitHub Actions localement avec `act`, évitant ainsi les problèmes de quota ou de facturation GitHub.

## 🚀 Quick Start

### Installation (déjà fait)

```bash
brew install act
```

### Configuration

Un fichier `.actrc` a été créé avec les images Docker recommandées :

```bash
-P ubuntu-latest=catthehacker/ubuntu:act-latest
-P ubuntu-22.04=catthehacker/ubuntu:act-22.04
-P ubuntu-20.04=catthehacker/ubuntu:act-20.04
--container-architecture linux/amd64
```

## 📋 Commandes Disponibles

### Via Makefile (Recommandé)

```bash
# Lister tous les jobs CI disponibles
make ci-list

# Tester le linting backend
make ci-test-lint

# Tester le linting frontend
make ci-test-frontend

# Tester les tests unitaires frontend
make ci-test-frontend-unit

# Tester le build frontend
make ci-test-build

# Voir les commandes disponibles
make ci-dry-run
```

### Commandes act directes

```bash
# Lister tous les workflows et jobs
act -l

# Exécuter un job spécifique (dry-run)
act -j backend-lint-and-security -W .github/workflows/ci-enhanced.yml -n

# Exécuter réellement un job
act -j backend-lint-and-security -W .github/workflows/ci-enhanced.yml

# Exécuter tous les jobs d'un workflow
act -W .github/workflows/ci-enhanced.yml

# Exécuter sur un événement spécifique
act push -W .github/workflows/ci-enhanced.yml

# Mode verbose pour debug
act -j backend-lint-and-security -W .github/workflows/ci-enhanced.yml -v
```

## 🎯 Jobs Testables Localement

### ✅ Jobs Fonctionnels (sans services externes)

Ces jobs fonctionnent parfaitement avec act :

1. **Backend Linting & Security** (`backend-lint-and-security`)

   ```bash
   make ci-test-lint
   # ou
   act -j backend-lint-and-security -W .github/workflows/ci-enhanced.yml
   ```

2. **Frontend Linting** (`frontend-lint-and-format`)

   ```bash
   make ci-test-frontend
   ```

3. **Frontend Build** (`frontend-build`)

   ```bash
   make ci-test-build
   ```

4. **Backend Type Checking** (`backend-type-check`)

   ```bash
   act -j backend-type-check -W .github/workflows/ci-enhanced.yml
   ```

### ⚠️ Jobs avec Limitations

Ces jobs nécessitent des services (PostgreSQL, Redis) et peuvent avoir des problèmes :

1. **Backend Unit Tests** (`backend-unit-tests`)
   - Nécessite PostgreSQL et Redis
   - Bug connu avec act et les services Docker
   - Alternative : Exécuter directement avec pytest localement

2. **Integration Tests** (`integration-tests`)
   - Nécessite la stack complète
   - Utiliser `docker-compose` à la place

## 🐛 Problèmes Connus et Solutions

### 1. Jobs avec Services (PostgreSQL, Redis)

**Problème** : Act a un bug avec les service containers dans certains workflows.

**Solution** : Utilisez docker-compose pour les tests d'intégration :

```bash
# Démarrer la stack complète
./scripts/start_stack.sh

# Exécuter les tests
pytest tests/ -v

# ou via make
make test
```

### 2. Secrets et Variables d'Environnement

**Problème** : Act n'a pas accès aux secrets GitHub.

**Solution** : Créez un fichier `.secrets` (ajouté au .gitignore) :

```bash
# .secrets
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/keneyapp
SECRET_KEY=your-secret-key-for-testing
CODECOV_TOKEN=optional-for-local
```

Utilisez-le avec act :

```bash
act -j backend-lint-and-security -W .github/workflows/ci-enhanced.yml --secret-file .secrets
```

### 3. Variables d'Environnement

Passez des variables avec `-e` :

```bash
act -j backend-lint-and-security -e PYTHON_VERSION=3.12
```

### 4. Cache et Performance

Act télécharge les actions à chaque exécution. Pour accélérer :

```bash
# Utiliser le cache local
export ACT_ACTIONS_CACHE=$HOME/.cache/act

# Pull les images en avance
docker pull catthehacker/ubuntu:act-latest
docker pull postgres:15-alpine
docker pull redis:7-alpine
```

## 📊 Workflows Disponibles

Liste complète des workflows testables :

| Workflow | Fichier | Jobs Principaux |
|----------|---------|----------------|
| Enhanced CI/CD | `ci-enhanced.yml` | backend-lint, frontend-lint, frontend-build |
| CI/CD Complete | `ci-cd-complete.yml` | backend-test, frontend-test, code-quality |
| Documentation | `documentation.yml` | generate-api-docs, generate-frontend-docs |
| Security Scans | `security-scans.yml` | codeql, snyk, trivy |
| E2E Tests | `e2e-tests.yml` | e2e-tests (playwright) |

## 🔧 Configuration Avancée

### Utiliser des Images Personnalisées

Modifiez `.actrc` pour utiliser vos propres images :

```bash
-P ubuntu-latest=my-custom-image:latest
```

### Exécuter sur un Event Spécifique

```bash
# Push event
act push

# Pull request event
act pull_request

# Workflow dispatch
act workflow_dispatch
```

### Debug Mode

```bash
# Verbose
act -j backend-lint-and-security -v

# Très verbose
act -j backend-lint-and-security -vv

# Garder le container après exécution
act -j backend-lint-and-security --reuse
```

## 📈 Workflow Recommandé

Pour un cycle de développement complet :

```bash
# 1. Vérifier les changements localement
make lint
make format
make test

# 2. Tester les jobs CI critiques
make ci-test-lint
make ci-test-frontend

# 3. Vérifier avec la stack Docker
./scripts/start_stack.sh
pytest tests/ -v

# 4. Commit et push
git add .
git commit -m "feat: nouvelle fonctionnalité"
git push origin main
```

## 🎓 Exemples Pratiques

### Exemple 1 : Tester le Linting Avant Commit

```bash
# Tester si le linting passera sur GitHub
make ci-test-lint

# Si échec, corriger et re-tester
make format
make ci-test-lint
```

### Exemple 2 : Tester le Build Frontend

```bash
# Vérifier que le build frontend fonctionne
make ci-test-build

# En cas d'erreur, voir les logs détaillés
act -j frontend-build -W .github/workflows/ci-enhanced.yml -v
```

### Exemple 3 : Tester Plusieurs Jobs en Parallèle

```bash
# Terminal 1
make ci-test-lint

# Terminal 2
make ci-test-frontend

# Terminal 3
make ci-test-build
```

## 🔗 Ressources

- [Act Documentation](https://github.com/nektos/act)
- [Act Docker Images](https://github.com/catthehacker/docker_images)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)

## ⚡ Performance Tips

1. **Pre-pull les images** avant de commencer :

   ```bash
   docker pull catthehacker/ubuntu:act-latest
   docker pull postgres:15-alpine
   docker pull redis:7-alpine
   ```

2. **Utiliser le cache** :

   ```bash
   export ACT_ACTIONS_CACHE=$HOME/.cache/act
   ```

3. **Réutiliser les containers** pour le debug :

   ```bash
   act -j backend-lint-and-security --reuse
   ```

4. **Limiter les jobs testés** : Ne testez que les jobs modifiés, pas tout le workflow.

## 🎯 Conclusion

Act vous permet de :

- ✅ Tester les workflows CI/CD localement
- ✅ Éviter les problèmes de quota GitHub Actions
- ✅ Détecter les erreurs avant de pusher
- ✅ Accélérer le cycle de développement
- ✅ Économiser les minutes GitHub Actions

**Note** : Certains jobs complexes (avec services) peuvent nécessiter docker-compose au lieu de act.
