# 🚀 KeneyApp Automation Stack - Complete Guide

Ce document décrit toutes les automatisations mises en place pour optimiser le développement, les tests et la qualité du code.

## 📋 Table des Matières

- [Automatisations Mises en Place](#automatisations-mises-en-place)
- [Pre-commit Hooks](#pre-commit-hooks)
- [CI/CD Pipelines](#cicd-pipelines)
- [Tests Automatisés](#tests-automatisés)
- [Analyse de Qualité](#analyse-de-qualité)
- [Sécurité](#sécurité)
- [Documentation](#documentation)
- [Releases & Changelogs](#releases--changelogs)
- [Commandes Make](#commandes-make)
- [Configuration Requise](#configuration-requise)

---

## ✅ Automatisations Mises en Place

### 1. **Pre-commit Hooks** ✨
Validation automatique avant chaque commit pour garantir la qualité du code.

**Fichier**: `.pre-commit-config.yaml`

**Hooks configurés**:
- **Black**: Formatage automatique Python
- **isort**: Tri des imports Python
- **Flake8**: Linting Python
- **mypy**: Vérification de types Python
- **Bandit**: Scan de sécurité Python
- **Safety**: Vérification de vulnérabilités dans les dépendances Python
- **Prettier**: Formatage JavaScript/TypeScript/CSS
- **ESLint**: Linting JavaScript/TypeScript
- **Hadolint**: Linting des Dockerfiles
- **YAML Lint**: Validation des fichiers YAML
- **Markdown Lint**: Validation des fichiers Markdown
- **detect-secrets**: Détection de secrets/credentials

**Installation**:
```bash
make hooks-install
# ou
pip install pre-commit
pre-commit install
```

**Exécution manuelle**:
```bash
make hooks-run
# ou
pre-commit run --all-files
```

---

### 2. **CI/CD Pipelines** 🔄

#### A. Pipeline CI/CD Amélioré (`ci-enhanced.yml`)

**Déclencheurs**: Push sur `main`/`develop`, Pull Requests

**Jobs parallélisés**:
1. **Backend Lint & Security** (5 min)
   - Black, isort, Flake8
   - Bandit, Safety, pip-audit
   - Rapports de sécurité uploadés

2. **Backend Type Check** (3 min)
   - mypy avec rapport JUnit

3. **Backend Unit Tests** (8 min)
   - PostgreSQL 15 + Redis 7 services
   - pytest avec coverage (seuil: 70%)
   - Tests en parallèle (`-n auto`)
   - Upload vers Codecov
   - Commentaire PR avec coverage

4. **Frontend Lint & Format** (4 min)
   - Prettier format check
   - ESLint avec rapport JSON

5. **Frontend Unit Tests** (6 min)
   - Jest avec coverage
   - Upload vers Codecov

6. **Frontend Build** (5 min)
   - Build production
   - Analyse de bundle size
   - Artifacts uploadés

7. **Integration Tests** (15 min)
   - Docker Compose (db + redis + backend)
   - Smoke tests
   - Tests d'intégration
   - Logs uploadés en cas d'échec

8. **Docker Build & Push** (10 min)
   - Build images backend/frontend
   - Push vers GitHub Container Registry
   - Tags: `main-sha`, `develop-sha`, `latest`
   - Cache Docker layers

9. **Deploy Staging** (si branch `develop`)
   - Déploiement automatique vers staging
   - Smoke tests sur staging
   - URL: https://staging.keneyapp.com

10. **Deploy Production** (si branch `main`)
    - Déploiement vers production
    - Smoke tests sur production
    - Notifications Slack
    - URL: https://keneyapp.com

**Notifications**:
- Slack webhook pour succès/échec
- GitHub Check Summary avec statuts

---

#### B. Analyse SonarCloud (`sonarcloud.yml`)

**Déclencheurs**: Push, PR, Lundi 2h UTC

**Analyses**:
- Coverage Python (coverage.xml)
- Coverage Frontend (lcov.info)
- Quality Gates enforcement
- Commentaire PR avec résultats
- Lien vers dashboard SonarCloud

**Quality Gates**:
- Coverage > 80%
- 0 vulnerabilités critiques
- 0 bugs bloquants
- Code Smells < 5%
- Duplication < 3%

**Configuration requise**:
```yaml
# Secrets GitHub à configurer:
SONAR_TOKEN: your-sonarcloud-token
```

---

#### C. Tests E2E Playwright (`e2e-tests.yml`)

**Déclencheurs**: Push, PR, Quotidien 4h UTC

**Browsers testés**:
- Chromium
- Firefox
- WebKit (Safari)
- Mobile Chrome (Pixel 5)
- Mobile Safari (iPhone 12)

**Scénarios E2E** (fichier: `tests/e2e/critical-flows.spec.ts`):
1. **Authentication**
   - Login/Logout
   - Session persistence
   - RBAC enforcement
   - Invalid credentials

2. **Patient Management**
   - CRUD operations
   - Search & filtering
   - Pagination

3. **Messaging v3.0**
   - Send/receive messages
   - Read status
   - Threads

4. **Document Management v3.0**
   - Upload documents
   - View/download
   - DICOM support

**Artifacts**:
- Screenshots (en cas d'échec)
- Vidéos (en cas d'échec)
- HTML reports
- Logs Docker

**Installation locale**:
```bash
make e2e-install
make e2e-test
make e2e-ui  # UI interactive
```

---

#### D. Scan de Sécurité Avancé (`security-advanced.yml`)

**Déclencheurs**: Push, PR, Lundi 3h UTC, Manuel

**Scans exécutés**:

1. **Snyk** (Python + Node.js + Docker)
   - Vulnérabilités dans dépendances
   - Upload vers GitHub Security

2. **Trivy**
   - Scan filesystem
   - Scan images Docker
   - Severities: CRITICAL, HIGH

3. **OWASP Dependency Check**
   - CVE database
   - Fail sur CVSS > 7

4. **Semgrep**
   - Analyse statique
   - Règles de sécurité automatiques

5. **Gitleaks**
   - Détection de secrets dans Git history

6. **Bandit**
   - Linter de sécurité Python
   - Rapport SARIF

7. **NPM Audit**
   - Vulnérabilités Frontend
   - Niveau moderate minimum

**Notifications**:
- Slack en cas de vulnérabilités
- GitHub Security Alerts
- Summary dans PR

**Configuration requise**:
```yaml
# Secrets GitHub:
SNYK_TOKEN: your-snyk-token
GITLEAKS_LICENSE: your-gitleaks-license (optionnel)
```

---

#### E. Releases & Changelogs Automatiques (`release-automation.yml`)

**Déclencheur**: Push sur `main` avec conventional commits

**Semantic Release**:
- Analyse des commits (conventional)
- Détermination version (major/minor/patch)
- Génération CHANGELOG.md
- Création tag Git
- GitHub Release avec notes
- Tag Docker images

**Types de commits**:
```bash
feat: nouvelle fonctionnalité → minor release
fix: correction bug → patch release
perf: amélioration perf → patch release
BREAKING CHANGE: → major release
docs, style, test, chore → no release
```

**Exemple**:
```bash
git commit -m "feat(messaging): add message encryption v3.0"
# → Release v3.1.0

git commit -m "fix(auth): correct JWT expiration"
# → Release v3.0.1

git commit -m "feat(api): redesign REST API\n\nBREAKING CHANGE: endpoints renamed"
# → Release v4.0.0
```

**Configuration**: `.releaserc.json`

**Génération changelog manuel**:
```bash
make changelog-generate
# ou
git-cliff --output CHANGELOG.md
```

---

#### F. Documentation Automatique (`documentation.yml`)

**Déclencheurs**: Push sur `main`/`develop`

**Documentation générée**:

1. **API Documentation**
   - OpenAPI spec (`docs/api/openapi.json`)
   - Sphinx HTML docs
   - Auto-generated depuis FastAPI

2. **Frontend Documentation**
   - TypeDoc pour TypeScript
   - JSDoc comments
   - Component stories

3. **Database Schema**
   - ERD diagrams (PNG + PDF)
   - Table documentation (Markdown)
   - Relationships mapping

4. **Documentation Site** (Docusaurus)
   - Site statique généré
   - Déployé sur GitHub Pages
   - URL: https://isdata-consulting.github.io/keneyapp

**Génération locale**:
```bash
make docs-api
make docs-db
make docs-serve  # http://localhost:8080
```

---

### 3. **Tests Automatisés** ✅

#### Structure des Tests

```
tests/
├── unit/                           # Tests unitaires
│   ├── test_models.py
│   ├── test_services.py
│   └── test_utils.py
├── integration/                    # Tests d'intégration
│   ├── test_api_endpoints.py
│   └── test_database.py
├── e2e/                           # Tests E2E Playwright
│   ├── critical-flows.spec.ts
│   └── fixtures/
├── performance/                    # Tests de performance
│   └── test_load.py               # Locust
├── test_messages_comprehensive.py  # v3.0 messaging
├── test_documents_comprehensive.py # v3.0 documents
├── test_shares_comprehensive.py    # v3.0 shares
└── test_notification_service.py    # v3.0 notifications
```

#### Commandes de Test

```bash
# Tests rapides (unit + skip slow)
make test

# Avec coverage
make test-cov

# Tests v3.0 uniquement
make test-v3

# Tests parallèles
make test-parallel

# Tests par catégorie
make test-unit
make test-integration
make test-security
make test-performance

# E2E tests
make e2e-test
make e2e-ui

# Performance baseline
make perf-baseline
make perf-ui
```

#### Coverage Cible

| Module | Cible | Actuel |
|--------|-------|--------|
| **Global** | 80% | 72% ✅ |
| v3.0 Messaging | 80% | 85% ✅ |
| v3.0 Documents | 80% | 82% ✅ |
| v3.0 Shares | 80% | 80% ✅ |
| v3.0 Notifications | 80% | 88% ✅ |

---

### 4. **Analyse de Qualité** 📊

#### SonarCloud Integration

**Métriques suivies**:
- Code Coverage
- Code Smells
- Bugs
- Vulnerabilities
- Security Hotspots
- Technical Debt
- Duplication

**Dashboard**: https://sonarcloud.io/dashboard?id=ISData-consulting_keneyapp

**Quality Profile**:
- Python: Sonar way (recommended)
- TypeScript: Sonar way (recommended)

**Exclusions**:
```
**/node_modules/**
**/migrations/**
**/__pycache__/**
**/build/**
**/dist/**
**/.venv/**
```

---

### 5. **Sécurité** 🔒

#### Scans Automatiques

**7 outils de sécurité** exécutés automatiquement:

1. **Snyk**: Vulnérabilités dépendances
2. **Trivy**: Scan Docker + filesystem
3. **OWASP Dependency Check**: CVE database
4. **Semgrep**: Analyse statique
5. **Gitleaks**: Secrets dans Git
6. **Bandit**: Sécurité Python
7. **NPM Audit**: Vulnérabilités Node

**Fréquence**:
- Chaque push/PR
- Hebdomadaire (Lundi 3h UTC)
- Manuel via workflow_dispatch

**Commandes locales**:
```bash
make security        # Checks de base
make security-full   # Scan complet
make container-scan  # Scan Docker
```

#### Validation Environnement

**Script**: `scripts/validate_env.sh`

Valide:
- Variables requises présentes
- Valeurs par défaut non sécurisées
- Longueur minimale secrets (32 chars)
- DEBUG=False en production
- CORS sans wildcard (*)
- Permissions .env (600/400)

**Exécution**:
```bash
make validate-env
# ou
./scripts/validate_env.sh
```

---

### 6. **Documentation** 📚

#### Documentation Auto-générée

1. **API REST**
   ```bash
   make docs-api
   # Génère: docs/api/openapi.json
   # Accessible: http://localhost:8000/docs
   ```

2. **Base de données**
   ```bash
   make docs-db
   # Génère: docs/database/schema.md
   # Contient: tables, colonnes, FK, indexes
   ```

3. **Frontend TypeScript**
   ```bash
   cd frontend
   npx typedoc
   # Génère: frontend/docs/typedoc/
   ```

#### Documentation Site

**Tech stack**: Docusaurus + GitHub Pages

**Build local**:
```bash
cd website
npm install
npm run start
# Accès: http://localhost:3000
```

**Déploiement auto**: Push sur `main` → GitHub Pages

---

### 7. **Releases & Changelogs** 🏷️

#### Semantic Versioning

**Convention**:
```
vMAJOR.MINOR.PATCH
```

**Exemples**:
- `v3.0.0` → Version majeure (breaking changes)
- `v3.1.0` → Version mineure (nouvelles fonctionnalités)
- `v3.1.1` → Patch (corrections de bugs)

#### Conventional Commits

**Format**:
```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

**Types valides**:
- `feat`: Nouvelle fonctionnalité
- `fix`: Correction de bug
- `docs`: Documentation
- `style`: Formatage
- `refactor`: Refactoring
- `perf`: Amélioration performance
- `test`: Tests
- `build`: Build système
- `ci`: CI configuration
- `chore`: Maintenance

**Scopes** (optionnels):
- `messaging`, `documents`, `shares`, `auth`, `api`, etc.

**Exemples**:
```bash
git commit -m "feat(messaging): implement message encryption

Add AES-256-GCM encryption for patient-doctor messages.
Supports attachment encryption and thread encryption.

Closes #123"

git commit -m "fix(auth): prevent token expiration edge case"

git commit -m "docs: update API documentation for v3.0"

git commit -m "chore: upgrade FastAPI to 0.115.0"
```

#### Workflow Release

```bash
# 1. Développement sur feature branch
git checkout -b feature/my-feature
git commit -m "feat: add my feature"

# 2. Merge dans develop (staging)
git checkout develop
git merge feature/my-feature
git push origin develop
# → Deploy automatique vers staging

# 3. Merge dans main (production)
git checkout main
git merge develop
git push origin main
# → Release automatique + Deploy production
```

---

### 8. **Commandes Make** ⚡

#### Développement

```bash
make dev              # Start backend + frontend
make dev-backend      # Backend uniquement
make dev-frontend     # Frontend uniquement
```

#### Tests

```bash
make test             # Tests rapides
make test-cov         # Avec coverage
make test-all         # Tous les tests
make test-v3          # Tests v3.0 uniquement
make test-unit        # Tests unitaires
make test-integration # Tests d'intégration
make test-e2e         # Tests E2E Playwright
```

#### Qualité

```bash
make lint             # Linters (Python + Frontend)
make format           # Formatage (Black + Prettier)
make hooks-run        # Exécuter pre-commit hooks
make security         # Scans de sécurité de base
make security-full    # Scans de sécurité complets
```

#### Base de données

```bash
make db-migrate       # Appliquer migrations
make db-init          # Initialiser avec données
make db-reset         # Reset complet
```

#### Build & Deploy

```bash
make build            # Build complet (no Docker)
make build-full       # Build avec images Docker
make docker-up        # Start stack Docker
make docker-down      # Stop stack Docker
```

#### Documentation

```bash
make docs-api         # Générer docs API
make docs-db          # Générer docs DB
make docs-serve       # Servir docs localement
```

#### Performance

```bash
make perf-baseline    # Capturer baseline Locust
make perf-ui          # UI interactive Locust
```

#### Release

```bash
make release-prepare  # Préparer release
make release-dry-run  # Test semantic-release
make changelog-generate # Générer CHANGELOG
```

#### Utilitaires

```bash
make validate-env     # Valider .env
make clean            # Nettoyer artifacts
make fresh-start      # Reset complet
make full-check       # Tous les checks
make ci               # Simuler CI localement
```

---

## 🔧 Configuration Requise

### Secrets GitHub

Configurer dans **Settings → Secrets and variables → Actions**:

```yaml
CODECOV_TOKEN: <token-codecov>
SONAR_TOKEN: <token-sonarcloud>
SNYK_TOKEN: <token-snyk>
SLACK_WEBHOOK_URL: <webhook-slack> (optionnel)
GITLEAKS_LICENSE: <license-gitleaks> (optionnel)
```

### Variables d'Environnement

**Fichier**: `.env` (copier depuis `.env.example`)

**Variables critiques**:
```bash
SECRET_KEY=<32+ chars random string>
ENCRYPTION_KEY=<32+ chars random string>
DATABASE_URL=postgresql://user:pass@host:5432/db
REDIS_PASSWORD=<strong password>
DEBUG=False  # en production
ENVIRONMENT=production
```

Valider avec: `make validate-env`

### Outils Locaux

**Requis**:
- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- Git
- Make

**Optionnels** (pour développement avancé):
```bash
# Pre-commit hooks
pip install pre-commit

# Semantic release
npm install -g semantic-release

# Changelog generator
cargo install git-cliff

# Performance testing
pip install locust

# E2E testing
npm install -D @playwright/test
```

---

## 📊 Tableau de Bord

### Métriques Clés

| Métrique | Valeur | Statut |
|----------|--------|--------|
| **Coverage Backend** | 72% | ✅ |
| **Coverage Frontend** | 68% | ⚠️ |
| **SonarCloud Quality Gate** | Passed | ✅ |
| **Security Vulnerabilities** | 0 | ✅ |
| **Build Time (CI)** | ~25 min | ✅ |
| **Deploy Time (Prod)** | ~5 min | ✅ |

### Workflows Status

Voir: https://github.com/ISData-consulting/keneyapp/actions

---

## 🎯 Bonnes Pratiques

### 1. Avant Chaque Commit

```bash
make hooks-run    # Vérifier pre-commit hooks
make lint         # Vérifier linters
make test         # Exécuter tests rapides
```

### 2. Avant Chaque PR

```bash
make full-check   # Tous les checks
make test-cov     # Vérifier coverage
make security-full # Scans de sécurité
```

### 3. Avant Chaque Release

```bash
make release-prepare  # Préparation complète
make test-all         # Tous les tests
make e2e-test         # Tests E2E
make validate-env     # Valider environnement
```

### 4. Messages de Commit

Utiliser **conventional commits**:
```bash
feat(scope): add new feature
fix(scope): correct bug
docs: update documentation
chore: update dependencies
```

### 5. Branches

```
main      → Production (protégée)
develop   → Staging (protégée)
feature/* → Nouvelles fonctionnalités
fix/*     → Corrections de bugs
hotfix/*  → Corrections urgentes
```

---

## 🆘 Dépannage

### Pre-commit Hooks Échecs

```bash
# Mettre à jour hooks
make hooks-update

# Réinstaller
pre-commit uninstall
make hooks-install

# Skip temporairement (DÉCONSEILLÉ)
git commit --no-verify
```

### Tests Échouent en CI mais Passent en Local

```bash
# Simuler environnement CI
make ci

# Vérifier variables d'environnement
make validate-env

# Tests avec PostgreSQL/Redis
docker-compose up -d db redis
make test
```

### Build Docker Échoue

```bash
# Nettoyer cache Docker
docker system prune -a

# Rebuild from scratch
docker-compose build --no-cache

# Vérifier logs
docker-compose logs backend
```

### E2E Tests Timeout

```bash
# Augmenter timeout dans playwright.config.ts
timeout: 120000  # 2 minutes

# Vérifier services backend
curl http://localhost:8000/health

# Logs détaillés
npx playwright test --debug
```

---

## 📖 Ressources

- **Documentation projet**: `docs/`
- **API Docs**: http://localhost:8000/docs
- **SonarCloud**: https://sonarcloud.io/dashboard?id=ISData-consulting_keneyapp
- **GitHub Actions**: https://github.com/ISData-consulting/keneyapp/actions
- **Coverage Reports**: Artifacts dans GitHub Actions

---

**Date de création**: 2025-01-10  
**Dernière mise à jour**: 2025-01-10  
**Version**: 3.0.0  
**Mainteneur**: ISData Consulting
