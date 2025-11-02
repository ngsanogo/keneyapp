# 🔧 Corrections de Build - KeneyApp v3.0

**Date:** 2 novembre 2025  
**Problèmes résolus:** 2 erreurs critiques de build

---

## ❌ Problèmes Identifiés

### 1. Dépendance strawberry-graphql Invalide

**Erreur:**
```
ERROR: No matching distribution found for strawberry-graphql>=0.284.1
```

**Cause:** La version 0.284.1+ de strawberry-graphql n'existe pas encore (dernière version disponible: 0.283.3)

**Impact:** Impossible de build l'image Docker backend

---

### 2. Migration Alembic Cassée

**Erreur:**
```
KeyError: '009_add_modules'
UserWarning: Revision 009_add_modules referenced from 009_add_modules -> 010_add_messages (head), Add messages table for secure messaging is not present
```

**Cause:** La migration `010_add_messages.py` référence `009_add_modules` qui n'existe pas dans le projet

**Chaîne de migrations actuelle:**
```
000_initial_schema
  ↓
001_add_audit_logs
  ↓
002_user_security_enhancements
  ↓
003_add_tenants_and_modules
  ↓
004_add_domain_timestamps
  ↓
b9b286850b0d_add_medical_coding_tables_and_
  ↓
010_add_messages  ← référençait incorrectement 009_add_modules
  ↓
011_add_medical_documents
  ↓
012_add_medical_record_shares
```

**Impact:** Alembic ne peut pas upgrader la base de données, backend crash au démarrage

---

## ✅ Corrections Appliquées

### 1. Downgrade strawberry-graphql

**Fichier:** `requirements.txt`

**Avant:**
```python
strawberry-graphql[fastapi]>=0.284.1
```

**Après:**
```python
strawberry-graphql[fastapi]>=0.283.0
```

**Justification:** Version 0.283.0 est stable et disponible, supporte toutes les fonctionnalités GraphQL utilisées

---

### 2. Correction Chaîne de Migrations

**Fichier:** `alembic/versions/010_add_messages.py`

**Avant:**
```python
revision = '010_add_messages'
down_revision = '009_add_modules'  # ❌ N'existe pas
```

**Après:**
```python
revision = '010_add_messages'
down_revision = 'b9b286850b0d'  # ✅ Pointe vers la vraie migration précédente
```

**Justification:** 
- `b9b286850b0d` est la dernière migration avant v3.0
- Elle ajoute les tables de terminologie médicale (CIM-10, CCAM, etc.)
- Elle révise `004` correctement

---

## 🚀 Validation et Redéploiement

### Script de Rebuild Créé

**Fichier:** `scripts/rebuild_stack.sh`

**Fonctionnalités:**
- ✅ Détection automatique de Docker (Desktop macOS/Linux)
- ✅ Arrêt propre des conteneurs existants
- ✅ Suppression images old (force rebuild)
- ✅ Build avec nouvelles dépendances
- ✅ Vérification santé backend
- ✅ Validation migration Alembic
- ✅ Rapport complet des services

**Usage:**
```bash
./scripts/rebuild_stack.sh
```

---

## 📋 Checklist de Validation

### Avant Redémarrage
- [x] Correction version strawberry-graphql
- [x] Correction down_revision migration 010
- [x] Script rebuild_stack.sh créé et exécutable

### Après Redémarrage
- [ ] Backend build sans erreur
- [ ] Alembic migrations appliquées (head = 012_add_medical_record_shares)
- [ ] Backend API répond (http://localhost:8000/health)
- [ ] Frontend build sans erreur (http://localhost:3000)
- [ ] Pas d'erreurs dans logs backend
- [ ] Pas d'erreurs dans logs frontend
- [ ] Celery worker démarre correctement
- [ ] Celery beat démarre correctement
- [ ] Flower accessible (http://localhost:5555)

---

## 🔍 Vérification Migration Alembic

### Commande de Vérification

```bash
# Via Docker
docker compose exec backend alembic current

# Résultat attendu:
# 012_add_medical_record_shares (head)
```

### Historique Complet

```bash
docker compose exec backend alembic history
```

**Chaîne attendue:**
```
000 -> 001 -> 002 -> 003 -> 004 -> b9b286850b0d -> 010 -> 011 -> 012 (head)
```

---

## 🐛 Debugging si Problèmes Persistent

### 1. Vérifier Logs Backend
```bash
docker compose logs backend | grep -i error
```

### 2. Vérifier État Base de Données
```bash
docker compose exec db psql -U keneyapp -d keneyapp_dev -c "\dt"
```

### 3. Reset Complet (si nécessaire)
```bash
# ⚠️ DESTRUCTIF - Supprime toutes les données
docker compose down -v  # Supprime volumes
docker system prune -a  # Nettoie images
./scripts/rebuild_stack.sh
```

### 4. Vérifier Dépendances Python
```bash
docker compose exec backend pip list | grep strawberry
# Doit afficher: strawberry-graphql 0.283.x
```

---

## 📊 Impact sur Tests

**Aucun impact** - Les tests ne dépendent pas de la version strawberry-graphql exacte tant que l'API reste stable.

**Vérification recommandée:**
```bash
# Après rebuild, lancer tests
make test-all
```

---

## 🎯 Prochaines Étapes

1. **Exécuter le rebuild:**
   ```bash
   ./scripts/rebuild_stack.sh
   ```

2. **Vérifier services:**
   - Backend: http://localhost:8000/health
   - Frontend: http://localhost:3000
   - API Docs: http://localhost:8000/api/v1/docs

3. **Exécuter tests:**
   ```bash
   pip install -r requirements-test.txt
   make test-all
   ```

4. **Vérifier couverture:**
   ```bash
   open htmlcov/index.html
   ```

---

## 📝 Notes Techniques

### Pourquoi 0.283.0 et pas 0.283.3 ?

**`>=0.283.0`** permet d'installer la dernière version 0.283.x disponible:
- pip installera 0.283.3 automatiquement
- Compatible avec futures patches 0.283.4, 0.283.5, etc.
- Évite de bloquer sur une micro-version spécifique

### Migration b9b286850b0d

Cette migration ajoute:
- Table `medical_codes` (CIM-10, CCAM)
- Table `icd10_codes` (détails CIM-10)
- Table `ccam_codes` (détails CCAM)
- Table `loinc_codes` (analyses biologiques)
- Indexes optimisés pour recherche terminologie

**Essentielle pour:** Codification médicale, facturation, interopérabilité FHIR

---

## ✅ Résultat Attendu

Après `./scripts/rebuild_stack.sh` :

```
✅ Stack rebuild complete!

📊 Service URLs:
   Backend API:     http://localhost:8000
   API Docs:        http://localhost:8000/api/v1/docs
   Frontend:        http://localhost:3000
   Flower (Celery): http://localhost:5555
   Prometheus:      http://localhost:9090
   Grafana:         http://localhost:3001
```

---

**Document créé le 2 novembre 2025**  
**KeneyApp v3.0.0 - ISDATA Consulting**
