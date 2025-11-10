# Documentation DMI (Dossier Médical Informatisé) - KeneyApp

## 📋 Vue d'Ensemble

Ce dossier contient la documentation complète pour le développement et le déploiement d'un Dossier Médical Informatisé (DMI) de niveau production, conforme aux standards internationaux et réglementations françaises/européennes.

**Objectif** : Fournir à une équipe de développement full-stack tous les artefacts nécessaires pour construire un DMI "au top", utilisable en GHU, petit hôpital, cabinet médical ou par médecin indépendant.

## 📚 Structure de la Documentation

### 1. [Vision Produit](01_VISION_PRODUCT.md) ⭐
**Contenu** :
- Vision globale et problèmes à résoudre
- Cas d'usage prioritaires (4 parcours détaillés)
- Périmètre MVP vs V1 vs V2
- Stakeholders et matrice RACI
- KPIs de succès (utilisateurs, techniques, business)
- Gouvernance produit et gestion des risques

**À qui** : Product Owner, Direction Médicale, DSI, Équipe projet

---

### 2. [Personas & Parcours](02_PERSONAS_PARCOURS.md) 👥
**Contenu** :
- 7 personas détaillés (Urgentiste, Médecin généraliste, IDE, Pharmacien, Secrétaire, DIM, DPO)
- 3 parcours utilisateurs complets avec points de friction
- Service blueprints (frontstage/backstage)
- Événements métier et intégrations SI

**À qui** : UX Designer, Product Owner, Développeurs, Équipe métier

---

### 3. [User Stories & Gherkin](03_USER_STORIES_GHERKIN.md) 📝
**Contenu** :
- 15+ user stories INVEST avec critères d'acceptation Gherkin
- Modules : Identito-vigilance, Consultation, Prescription, Laboratoire, Documents
- Règles qualité des données (50+ règles)
- Matrice de traçabilité (US → Ressources FHIR → Tests)

**À qui** : Développeurs, QA, Product Owner

---

### 4. [RBAC/ABAC & Sécurité](04_RBAC_ABAC_SECURITY.md) 🔐
**Contenu** :
- 8 rôles utilisateurs avec hiérarchie
- Matrice RBAC détaillée (40+ ressources × 8 rôles)
- Politiques ABAC (OPA) avec exemples
- Break-the-Glass workflow
- Gestion consentements (4 types)
- Audit logging (structure, rétention, conformité)
- Politiques de sécurité (mots de passe, chiffrement, sauvegardes)

**À qui** : Architecte Sécurité, RSSI, DPO, Développeurs backend

---

### 5. [Dictionnaire de Données](05_DATA_DICTIONARY.md) 📊
**Contenu** :
- 5 domaines de données (Patient, Encounter, Observation, Medication, Document)
- 40+ champs avec types, terminologies, règles qualité
- Mapping FHIR R4 (correspondance modèle DB → ressources FHIR)
- Extensions FHIR spécifiques France (INS, lieu de naissance)
- Exemples de données valides (JSON)

**À qui** : Data Architect, DBA, Développeurs backend

---

### 6. [Spécifications OpenAPI](06_OPENAPI_SPECS.md) 🔧
**Contenu** :
- Spécifications OpenAPI 3.1.0
- Endpoints REST (Patients, Prescriptions, Laboratoire, Documents)
- Schémas de données (Patient, Prescription, Observation, Error)
- Exemples de requêtes/réponses
- Codes erreur et gestion des cas limites
- Authentification (JWT, OAuth2)

**À qui** : Développeurs backend, Intégrateurs, DevOps

---

### 7. [Données Synthétiques](07_SYNTHETIC_DATA.md) 🧪
**Contenu** :
- 4 profils patients types (Diabète, Traumatisme, Nouveau-né, Oncologie)
- 3 parcours cliniques complets (Consultation diabète, Urgence, Hospitalisation chirurgie)
- Résultats laboratoire (NFS, Bilan métabolique, Bilan lipidique)
- Scripts Python génération patients
- Scripts SQL insertion données
- Volumétrie (Minimal, Standard, Large, Stress)

**À qui** : Développeurs, QA, Data Engineer

---

### 8. [Plan de Livraison](08_DELIVERY_PLAN.md) 🚀
**Contenu** :
- Roadmap 18 mois (MVP 6 mois, V1 6 mois, V2 6 mois)
- Sprint planning détaillé (24 sprints)
- Budget et composition équipe
- Déploiement pilote et migration données
- Matrice des risques et mitigation
- Dossier de conformité (RGPD, HDS, ISO 27001)
- Formation et support utilisateurs
- KPIs projet et métier

**À qui** : Product Owner, DSI, Direction Générale, Chef de Projet

---

## 🎯 Utilisation de la Documentation

### Pour Product Owner
1. Commencer par **01_VISION_PRODUCT.md** (vision, KPIs, roadmap)
2. Valider les **02_PERSONAS_PARCOURS.md** avec équipes métier
3. Prioriser les **03_USER_STORIES_GHERKIN.md** par sprint
4. Suivre l'avancement avec **08_DELIVERY_PLAN.md**

### Pour Développeurs Backend
1. Étudier **05_DATA_DICTIONARY.md** (modèle de données)
2. Implémenter selon **06_OPENAPI_SPECS.md** (contrats API)
3. Appliquer les règles **04_RBAC_ABAC_SECURITY.md** (sécurité)
4. Tester avec **07_SYNTHETIC_DATA.md** (jeux de données)

### Pour Développeurs Frontend
1. Comprendre les **02_PERSONAS_PARCOURS.md** (UX, workflows)
2. Implémenter selon **03_USER_STORIES_GHERKIN.md** (critères acceptation)
3. Consommer l'API **06_OPENAPI_SPECS.md**
4. Respecter **04_RBAC_ABAC_SECURITY.md** (RBAC frontend)

### Pour QA / Test Engineers
1. Créer tests à partir de **03_USER_STORIES_GHERKIN.md** (Gherkin)
2. Utiliser **07_SYNTHETIC_DATA.md** (données de test)
3. Valider sécurité selon **04_RBAC_ABAC_SECURITY.md**
4. Vérifier conformité **05_DATA_DICTIONARY.md** (qualité données)

### Pour Architecte / Tech Lead
1. Valider l'architecture dans **08_DELIVERY_PLAN.md**
2. Définir les standards **05_DATA_DICTIONARY.md** + **06_OPENAPI_SPECS.md**
3. Implémenter la sécurité **04_RBAC_ABAC_SECURITY.md**
4. Coordonner les sprints selon **08_DELIVERY_PLAN.md**

## 📊 Standards et Conformité

### Standards Médicaux
- **FHIR R4** : Interopérabilité complète (profils France si disponibles)
- **Terminologies** :
  - LOINC : Analyses biologiques
  - SNOMED CT : Problèmes de santé, actes
  - CIM-10 / ICD-11 : Diagnostics
  - ATC : Médicaments (classification)
  - CIP/UCD : Médicaments (codes France)
  - CCAM/CPT : Actes médicaux

### Conformité Réglementaire
- ✅ **RGPD** (Europe) : Protection données personnelles
- ✅ **HDS** (France) : Hébergement Données de Santé
- ✅ **HIPAA** (US) : Confidentialité informations santé (si applicable)

### Sécurité
- OAuth2/OIDC : Authentification (Pro Santé Connect)
- JWT : Sessions utilisateurs
- AES-256-GCM : Chiffrement données PHI au repos
- TLS 1.3 : Chiffrement en transit
- RBAC/ABAC : Contrôle d'accès fin
- Audit logging : Traçabilité complète (WORM)

## 🛠️ Technologies Recommandées

### Backend
- **Framework** : FastAPI (Python) ou NestJS (Node.js)
- **Base de données** : PostgreSQL 15+ (JSONB pour FHIR)
- **Cache** : Redis 7+
- **Queue** : Celery (Python) ou BullMQ (Node.js)
- **FHIR Server** : HAPI FHIR (option) ou custom

### Frontend
- **Framework** : React 18+ avec TypeScript
- **State Management** : Zustand ou Redux Toolkit
- **Formulaires** : React Hook Form + Zod
- **UI Components** : Material-UI ou Ant Design (accessible WCAG 2.1 AA)

### DevOps
- **Conteneurs** : Docker + Kubernetes (Helm charts)
- **CI/CD** : GitHub Actions
- **Monitoring** : Prometheus + Grafana
- **Logging** : ELK Stack ou Loki
- **Tracing** : OpenTelemetry + Jaeger

### Intégrations
- **HL7 v2** : Mirth Connect / NextGen Connect
- **DICOM** : Orthanc / DCM4CHEE
- **Messagerie** : MSSanté (SMTP sécurisé)
- **Identité** : Téléservice INS (France)

## 📈 KPIs de Succès

### MVP (6 mois)
- 70% adoption utilisateurs pilotes
- < 7 min temps saisie consultation
- 95% complétude INS
- 0 incident sécurité majeur
- 99% disponibilité

### V1 (12 mois)
- 90% adoption multi-sites
- < 5 min temps saisie consultation
- 98% complétude INS
- Latence p95 < 300 ms
- 99.5% disponibilité
- ROI positif

### V2 (18 mois)
- Déploiement GHU complet
- Télémédecine opérationnelle
- Portail patient actif
- Satisfaction > 4.5/5
- Leader marché segment cible

## 🚀 Quick Start

### Étape 1 : Lecture Rapide
1. Lire **01_VISION_PRODUCT.md** (30 min)
2. Parcourir **08_DELIVERY_PLAN.md** section Timeline (15 min)
3. Survoler les autres documents (titres + résumés)

### Étape 2 : Approfondir par Rôle
- **Product** : 01, 02, 03, 08
- **Backend** : 05, 06, 04, 07
- **Frontend** : 02, 03, 06
- **QA** : 03, 07, 04
- **DevOps** : 08, 06, 04

### Étape 3 : Planifier
1. Constituer équipe (voir 08_DELIVERY_PLAN.md)
2. Setup environnements
3. Lancer Sprint 1 (Identito-vigilance)

## ❓ FAQ

### Q1 : Cette documentation est-elle complète pour démarrer le développement ?
**R** : Oui. Elle fournit :
- Vision produit et KPIs
- User stories avec critères d'acceptation
- Spécifications API (OpenAPI)
- Modèle de données complet
- Règles de sécurité
- Jeux de données de test
- Plan de livraison 18 mois

### Q2 : Faut-il suivre exactement le plan de livraison ?
**R** : Non, c'est un guide. Adaptez selon :
- Ressources disponibles
- Contraintes métier
- Priorités clients
- Feedback utilisateurs

### Q3 : Les données synthétiques sont-elles utilisables en production ?
**R** : **NON**. Elles sont uniquement pour :
- Développement
- Tests
- Démonstration
- Formation

Les INS générés sont volontairement invalides.

### Q4 : Comment gérer les évolutions après V2 ?
**R** : Processus continu :
1. Collecter feedback utilisateurs
2. Prioriser avec framework RICE (voir 01_VISION_PRODUCT.md)
3. Créer user stories (modèle dans 03_USER_STORIES_GHERKIN.md)
4. Intégrer dans sprints
5. Déployer incrémentalement

### Q5 : Où trouver de l'aide pour les standards médicaux ?
**R** : Ressources officielles :
- **FHIR** : https://www.hl7.org/fhir/
- **FHIR France** : https://interop.esante.gouv.fr/ig/fhir/
- **LOINC** : https://loinc.org/
- **SNOMED CT** : https://www.snomed.org/
- **ANS** : https://esante.gouv.fr/

## 📞 Support

Pour questions sur cette documentation :
- **Email** : contact@isdataconsulting.com
- **GitHub Issues** : [Créer une issue](https://github.com/ISData-consulting/keneyapp/issues)

---

**Auteurs** : ISDATA Consulting - Équipe KeneyApp  
**Date création** : 2025-01-10  
**Version** : 1.0  
**Licence** : Proprietary (ISDATA Consulting)

**Note** : Cette documentation constitue un livrable complet pour le développement d'un DMI de production. Elle est le fruit d'une analyse approfondie des besoins métier, des standards internationaux, et des meilleures pratiques de l'industrie.
