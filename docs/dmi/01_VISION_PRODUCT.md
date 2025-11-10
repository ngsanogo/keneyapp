# Vision Produit DMI - Dossier Médical Informatisé

## 1. Vision et Problèmes à Résoudre

### 1.1 Vision Globale

Le DMI (Dossier Médical Informatisé) de KeneyApp vise à créer une solution cloud-native, interopérable et sécurisée pour la gestion complète des dossiers médicaux, utilisable par :
- **GHU (Groupement Hospitalier Universitaire)** : gestion de milliers de patients, coordination multi-services
- **Petits hôpitaux** : solution adaptable avec fonctionnalités essentielles
- **Cabinets médicaux** : interface simplifiée, mode offline-first
- **Médecins indépendants** : solution légère et autonome

### 1.2 Problèmes à Résoudre

#### Pour les Soignants
- ❌ Saisie manuelle répétitive et chronophage
- ❌ Données éparpillées dans plusieurs systèmes
- ❌ Manque de traçabilité et historique incomplet
- ❌ Difficultés de coordination entre services
- ❌ Alertes cliniques tardives ou manquantes

#### Pour les Établissements
- ❌ Interopérabilité limitée avec les SI existants
- ❌ Non-conformité RGPD/HDS
- ❌ Coûts d'intégration élevés
- ❌ Manque de visibilité sur la qualité des données
- ❌ Processus de facturation complexes

#### Pour les Patients
- ❌ Perte d'informations lors des transferts
- ❌ Redondance des examens
- ❌ Manque d'accès à leur propre dossier
- ❌ Délais de coordination entre professionnels

### 1.3 Cas d'Usage Prioritaires

#### Cas d'Usage 1 : Consultation Ambulatoire
**Acteur** : Médecin généraliste  
**Objectif** : Consulter un patient en moins de 10 minutes avec saisie structurée  
**Flux** :
1. Recherche/création patient avec INS
2. Consultation de l'historique (dernières consultations, allergies, traitements en cours)
3. Saisie anamnèse et examen clinique avec templates
4. Prescription médicamenteuse avec vérification d'interactions
5. Génération ordonnance et CR automatiques

**Critères de succès** :
- Temps de saisie < 5 minutes
- 0 erreur d'identification patient
- Détection automatique des interactions médicamenteuses
- Ordonnance générée conforme réglementations

#### Cas d'Usage 2 : Urgences Hospitalières
**Acteur** : Urgentiste  
**Objectif** : Trier, évaluer et traiter un patient aux urgences  
**Flux** :
1. Admission rapide avec identito-vigilance
2. Triage IAO (infirmier d'accueil et d'orientation)
3. Saisie constantes et scores d'urgence (Glasgow, NEWS)
4. Prescription examens complémentaires (bio, imagerie)
5. Consultation résultats en temps réel
6. Décision (hospitalisation, sortie, transfert)

**Critères de succès** :
- Admission < 2 minutes
- Disponibilité résultats labo < 30 minutes
- Traçabilité complète des actes
- Score de gravité calculé automatiquement

#### Cas d'Usage 3 : Prescription et Suivi Pharmaceutique
**Acteur** : Pharmacien hospitalier  
**Objectif** : Valider et optimiser les prescriptions  
**Flux** :
1. Réception prescription médicale
2. Vérification interactions médicamenteuses
3. Adaptation posologie selon fonction rénale/hépatique
4. Validation pharmaceutique
5. Traçabilité des dispensations

**Critères de succès** :
- Détection 100% interactions critiques
- Validation < 15 minutes
- Alerte si contre-indication

#### Cas d'Usage 4 : Résultats de Laboratoire
**Acteur** : Biologiste  
**Objectif** : Transmettre résultats structurés avec alertes  
**Flux** :
1. Réception demande d'examen (HL7 ORM)
2. Réalisation analyses
3. Transmission résultats (HL7 ORU) avec codes LOINC
4. Alerte si valeur critique
5. Intégration automatique au dossier patient

**Critères de succès** :
- Latence transmission < 2 minutes (p95)
- 100% résultats avec codes LOINC
- Alerte temps réel pour valeurs critiques

### 1.4 Non-Objectifs (Out of Scope MVP)

#### Hors Périmètre Initial
- ❌ Télémédecine avec visioconférence (prévu V2)
- ❌ Intelligence artificielle pour aide au diagnostic (R&D)
- ❌ Blockchain pour traçabilité (non prioritaire)
- ❌ Application mobile native (web responsive suffit)
- ❌ Intégration systèmes de paiement complexes
- ❌ Gestion complète de la facturation T2A
- ❌ Module de recherche clinique avancé

#### Fonctionnalités Reportées
- Module de téléconsultation vidéo → V2 (Q2 2026)
- Analytics prédictifs → V3
- IA assistant médical → Phase R&D
- Intégration IoT/wearables → V2
- Portail patient complet → V2

## 2. Périmètre MVP vs V1/V2

### 2.1 MVP (Minimum Viable Product) - 6 mois

#### Modules Essentiels
✅ **Identito-vigilance**
- Création/recherche patient avec INS
- Gestion doublons et fusion manuelle
- Intégration téléservice INS

✅ **Dossier Patient**
- Fiche patient complète
- Antécédents médicaux structurés
- Allergies et intolérances
- Traitements en cours

✅ **Consultation**
- Saisie anamnèse et examen
- Constantes vitales
- Scores cliniques de base (IMC, clairance rénale)

✅ **Prescription**
- Prescription médicamenteuse avec BDM (Base de Données Médicamenteuses)
- Détection interactions de base
- Génération ordonnance PDF

✅ **Documents**
- Stockage documents (PDF, images)
- Génération comptes-rendus simples
- Signature électronique basique

✅ **Sécurité & Conformité**
- RBAC (4 rôles : Admin, Médecin, Infirmier, Secrétaire)
- Chiffrement données au repos
- Journal d'audit RGPD
- Consentement patient

#### Standards & Interopérabilité MVP
- FHIR R4 : Patient, Encounter, Observation, Condition, MedicationRequest
- Terminologies : LOINC (résultats bio), ATC (médicaments), CIM-10 (diagnostics)
- APIs REST sécurisées

### 2.2 V1 - Production Multi-Site (6-12 mois)

#### Modules Additionnels
✅ **Agenda & Admission**
- Gestion rendez-vous multi-praticiens
- Planning salles et ressources
- Gestion lits et UF (Unités Fonctionnelles)

✅ **Laboratoire**
- Intégration HL7 v2 (ORM/ORU)
- Résultats structurés avec codes LOINC
- Alertes valeurs critiques

✅ **Imagerie**
- Intégration PACS (DICOM)
- Visionneuse DICOM web
- Liens ImagingStudy FHIR

✅ **Messagerie**
- Messagerie sécurisée MSSanté
- Échange documents IHE XDS
- Notifications multi-canal

✅ **Tableaux de Bord**
- File d'attente temps réel
- Indicateurs cliniques
- Alertes personnalisées

#### Standards & Interopérabilité V1
- HL7 v2 : ADT, ORM, ORU
- DICOM : SR, WADO-RS
- IHE profils : XDS.b, PIX, PDQ
- FHIR Subscriptions

### 2.3 V2 - Fonctionnalités Avancées (12-18 mois)

#### Modules Avancés
✅ **Recherche Avancée**
- Recherche plein-texte ElasticSearch
- Filtres multi-critères
- Historique recherches

✅ **Télémédecine**
- Visioconférence WebRTC
- Téléconsultation structurée
- E-prescription

✅ **Analytics**
- Dashboards personnalisables
- Export données anonymisées
- Requêtes OLAP

✅ **Portail Patient**
- Accès dossier patient
- Prise RDV en ligne
- Demande renouvellement ordonnance

#### Intelligence & Automatisation
- Validation pharmaceutique assistée par IA
- Détection interactions avancées
- Suggestions diagnostiques contextuelles
- Auto-complétion intelligente

## 3. Stakeholders & RACI

### 3.1 Matrice RACI

| Activité | Direction Médicale | DSI | Soignants | Secrétariat | Data Manager | DPO | Qualité |
|----------|-------------------|-----|-----------|-------------|--------------|-----|---------|
| **Validation besoins cliniques** | A | C | R | I | I | I | C |
| **Architecture technique** | C | A/R | I | I | C | C | I |
| **Développement** | I | A | C | I | I | C | I |
| **Tests utilisateurs** | C | C | R/A | R | I | I | C |
| **Conformité RGPD/HDS** | C | C | I | I | R | A | R |
| **Déploiement** | C | A/R | C | C | I | C | C |
| **Formation** | C | C | R/A | R/A | I | I | C |
| **Maintenance** | I | A/R | C | C | I | C | C |
| **Évolutions** | A | C | R | C | R | C | C |

**Légende** : R = Responsable | A = Autorité (Accountable) | C = Consulté | I = Informé

### 3.2 Comités de Pilotage

#### Comité Stratégique (Mensuel)
- Direction Médicale
- DSI
- Direction Générale
- DPO
- Responsable Qualité

**Décisions** : Roadmap, budget, priorités, conformité

#### Comité Technique (Bi-mensuel)
- Architecte Solution
- Tech Lead Backend/Frontend
- DevOps Lead
- Responsable Sécurité
- DBA

**Décisions** : Choix techniques, architecture, performance, sécurité

#### Comité Utilisateurs (Mensuel)
- Médecins représentants par service
- IDE référentes
- Secrétaires médicales
- Pharmacien
- Radiologue

**Décisions** : UX, workflows, priorisation fonctionnalités

## 4. KPI de Succès

### 4.1 KPI Utilisateurs

#### Efficacité Clinique
| KPI | Cible MVP | Cible V1 | Mesure |
|-----|-----------|----------|--------|
| **Temps de saisie consultation** | < 7 min | < 5 min | Temps moyen workflow complet |
| **Temps recherche patient** | < 10 sec | < 3 sec | p95 latence recherche |
| **Temps génération ordonnance** | < 30 sec | < 15 sec | De saisie à PDF signé |
| **Nombre de clics création RDV** | < 10 | < 5 | Parcours optimisé |

#### Qualité des Données
| KPI | Cible MVP | Cible V1 | Mesure |
|-----|-----------|----------|--------|
| **Complétude INS** | > 95% | > 98% | % patients avec INS validé |
| **Taux d'erreurs saisie** | < 2% | < 1% | Erreurs détectées/corrigées |
| **Complétude allergies** | > 90% | > 95% | % dossiers avec info allergie |
| **Doublons détectés** | < 0.5% | < 0.2% | % doublons dans base |

#### Adoption
| KPI | Cible MVP | Cible V1 | Mesure |
|-----|-----------|----------|--------|
| **Taux d'adoption** | > 70% | > 90% | % utilisateurs actifs/total |
| **Satisfaction utilisateurs** | > 3.5/5 | > 4/5 | Score NPS mensuel |
| **Formation requise** | < 4h | < 2h | Temps formation autonomie |
| **Tickets support/utilisateur** | < 0.5/mois | < 0.2/mois | Volume support |

### 4.2 KPI Techniques

#### Performance
| KPI | Cible MVP | Cible V1 | Mesure |
|-----|-----------|----------|--------|
| **Latence API (p95)** | < 500 ms | < 300 ms | Temps réponse endpoints |
| **Disponibilité** | > 99% | > 99.5% | Uptime mensuel |
| **Erreurs 5xx** | < 1% | < 0.5% | Taux erreurs serveur |
| **Temps chargement page** | < 3 sec | < 2 sec | Time to Interactive |

#### Sécurité & Conformité
| KPI | Cible MVP | Cible V1 | Mesure |
|-----|-----------|----------|--------|
| **Incidents sécurité** | 0 | 0 | Incidents majeurs/mois |
| **Complétude audit logs** | 100% | 100% | % actions tracées |
| **Conformité RGPD** | 100% | 100% | Check-list conformité |
| **Chiffrement données sensibles** | 100% | 100% | % données PHI chiffrées |

#### Scalabilité
| KPI | Cible MVP | Cible V1 | Mesure |
|-----|-----------|----------|--------|
| **Utilisateurs concurrents** | 100 | 500 | Capacité pic |
| **Volume données** | 10k patients | 100k patients | Nombre patients |
| **Temps de réponse (charge)** | < 800 ms | < 500 ms | p95 sous charge |
| **Coût/patient/mois** | < 1€ | < 0.5€ | Infrastructure cloud |

### 4.3 KPI Business

#### ROI et Efficience
| KPI | Cible MVP | Cible V1 | Mesure |
|-----|-----------|----------|--------|
| **Réduction temps admin** | -20% | -30% | Temps tâches administratives |
| **Gain productivité médecin** | +15% | +25% | Patients/jour supplémentaires |
| **Réduction examens redondants** | -10% | -20% | % examens évités |
| **ROI** | Break-even 18 mois | Break-even 12 mois | Investissement vs gains |

## 5. Gouvernance du Produit

### 5.1 Processus de Décision

#### Prioritisation Fonctionnalités
**Framework RICE** :
- **R**each (Portée) : Nombre d'utilisateurs impactés
- **I**mpact : Impact métier (0.25, 0.5, 1, 2, 3)
- **C**onfidence : Niveau de confiance (0-100%)
- **E**ffort : Effort développement (personne-jours)

**Score RICE** = (Reach × Impact × Confidence) / Effort

#### Critères d'Acceptation Feature
- ✅ User stories INVEST complètes
- ✅ Critères d'acceptation Gherkin
- ✅ Maquettes validées
- ✅ Tests automatisés (couverture > 80%)
- ✅ Documentation à jour
- ✅ Conformité sécurité/RGPD
- ✅ Performance validée (< seuils KPI)
- ✅ Validation utilisateurs (UAT)

### 5.2 Cadence de Livraison

- **Sprints** : 2 semaines
- **Release MVP** : Toutes les 4 semaines (stabilisation)
- **Release Production** : Mensuelle (après MVP)
- **Hotfix** : Au besoin (< 24h pour critique)

### 5.3 Gestion des Risques

| Risque | Probabilité | Impact | Mitigation |
|--------|-------------|--------|------------|
| **Complexité FHIR** | Moyenne | Élevé | Formation équipe, profils simplifiés, tests conformance |
| **Performance HL7** | Faible | Moyen | Architecture événementielle, buffering, monitoring |
| **Adoption utilisateurs** | Moyenne | Élevé | Formation continue, champions utilisateurs, UX itératif |
| **Conformité HDS** | Faible | Critique | Audit continu, hébergeur certifié, procédures documentées |
| **Doublons patients** | Moyenne | Élevé | Algorithme scoring, workflow validation, audit régulier |

## 6. Success Metrics - Synthèse

### Objectifs 6 Mois (MVP)
- ✅ 70% adoption utilisateurs pilotes
- ✅ < 7 min temps saisie consultation
- ✅ 95% complétude INS
- ✅ 0 incident sécurité majeur
- ✅ 99% disponibilité
- ✅ Satisfaction > 3.5/5

### Objectifs 12 Mois (V1)
- ✅ 90% adoption multi-sites
- ✅ < 5 min temps saisie consultation
- ✅ 98% complétude INS
- ✅ Latence p95 < 300 ms
- ✅ 99.5% disponibilité
- ✅ ROI positif

### Objectifs 18 Mois (V2)
- ✅ Déploiement GHU complet
- ✅ Télémédecine opérationnelle
- ✅ Analytics avancés
- ✅ Portail patient actif
- ✅ Satisfaction > 4.5/5
- ✅ Leader marché segment cible

---

**Document validé par** : Direction Médicale, DSI, Product Owner  
**Date** : 2025-01-10  
**Version** : 1.0  
**Prochaine revue** : 2025-04-10
