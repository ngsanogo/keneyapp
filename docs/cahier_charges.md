Super demande. Voici tout ce qu’il faut préparer et remettre à un(e) développeur·se full-stack pour construire un module de Dossier Médical Informatisé (DMI) “au top” — utilisable aussi bien en GHU, petit hôpital, cabinet ou médecin indépendant — avec un niveau d’exigence maximal sur la qualité de la donnée, l’UX et les bonnes pratiques santé.

1) Vision, périmètre, gouvernance
	•	Vision produit: problèmes à résoudre, cas d’usage prioritaires, non-objectifs.
	•	Périmètre MVP vs. V1/V2: ce qui est indispensable à la mise en prod multi-site.
	•	Stakeholders & RACI: Direction médicale, DSI, soignants, secrétariat, data, conformité.
	•	KPI de succès: temps de saisie, taux d’erreurs, complétude INS, adoption, latence < X ms.

2) Personae, parcours & blueprint de service
	•	Personae: urgentiste, médecin libéral, IDE, secrétaire, DIM, DPO, Data manager.
	•	Parcours clés (diagrammes + scénarios “happy path” + exceptions):
	•	Accueil/identito-vigilance → consultation → prescription → résultats → ordonnance/CR → facturation légère.
	•	Urgences: tri, soins, prescriptions rapides, traçabilité des actes.
	•	Cabinet: agenda, dossier patient longitudinal, renouvellements, correspondance.
	•	Service blueprint: frontstage/backstage, files, événements, intégrations SI.

3) Exigences fonctionnelles (par modules)
	•	Identito-vigilance: création/recherche patient, gestion doublons, fusion, INS.
	•	Agenda & admission: RDV, salles, ressources, motifs; lits/UF pour hôpital.
	•	Consultation: anamnèse, antécédents structurés, allergies, constantes, scores.
	•	Prescription & résultats: examens bio/imagery, médication (unitaire/plan), validation pharmaceutique, retour LIS/RIS/PACS.
	•	Documents: CR, ordonnances, certificats, modèles, export PDF, signature.
	•	Messagerie & coordination: envoi/recv avec correspondants, traçabilité.
	•	Tableaux de bord: suivi patient, file d’attente, alertes cliniques.
	•	Recherche & filtrage: plein-texte, facettes (dates, service, type doc…).

Pour chaque module, fournir des user stories INVEST + critères d’acceptation Gherkin + maquettes.

4) Interopérabilité & référentiels (à planifier dès le début)
	•	Modèle d’échange: FHIR R4/R5 (Patient, Encounter, Observation, Condition, Procedure, MedicationRequest, DocumentReference, Appointment, Task, Practitioner, Organization…).
	•	Terminologies: LOINC (bio), SNOMED CT (problèmes/actes), CIM-10, CCAM, CIP/UCD (médicaments), UCUM (unités).
	•	Imagerie: DICOM, WADO-RS; liaison PACS.
	•	Partage documentaire: IHE XDS.b / MHD.
	•	Flux France: INS, Pro Santé Connect (CPS/e-CPS), MSSanté, DMP, profils FHIR de l’ANS (Ségur), hébergement HDS.

5) Données: modèle, qualité, gouvernance
	•	Domaine & canonique: ERD/diagrammes + mapping → ressources FHIR.
	•	Dictionnaire de données: définitions, types, cardinalités, contraintes.
	•	Règles qualité: complétude, unicité, cohérence, fraîcheur, exactitude; plan de contrôles automatiques (ex: “AllergyIntolerance sans code interdit”, “Observation sans UCUM rejetée”).
	•	MDM identités: survivorship, fusion, scoring doublons.
	•	Traçabilité & lignage: horodatage fiable, provenance, horloge logique.
	•	Jeux de données synthétiques: safe-by-design pour dev/démo/tests.

6) Sécurité, confidentialité, conformité
	•	Cadre: RGPD, doctrine ANS, hébergement HDS, journal d’audit (exigences ISO 27789), politique de rétention, consentement & bases légales.
	•	IAM: RBAC/ABAC (médecin/IDE/secrétaire/admin/DIM), sessions courtes, SSO Pro Santé Connect.
	•	Sécurité appli: OWASP ASVS/Top-10, CSP, chiffrage at-rest/in-transit, gestion secrets, revocation, protection contre la ré-identification.
	•	Journalisation: accès, lecture/écriture DMI, export; alertes d’anomalies.
	•	Plan de gestion des incidents: détection, réponse, notification, preuves.

7) Design & UX
	•	Design system: tokens (color/typography/space), composants, states, densité.
	•	Maquettes: low-fi → hi-fi pour desktop, tablette, mobile; responsive.
	•	Patrons UX cliniques: saisie rapide, raccourcis clavier, smart defaults, auto-save, conflits de version.
	•	Accessibilité: RGAA / WCAG 2.1 AA; contrastes, navigation clavier, lecteurs d’écran.
	•	Recherche & découverte: global search, commandes rapides, favoris.
	•	Localisation: FR d’abord; i18n prêt.

8) Architecture cible
	•	API-first: OpenAPI/AsyncAPI; FHIR server de référence; BFF par client.
	•	Événementiel: bus (ex: Kafka/NATS); FHIR Subscriptions; outbox pattern.
	•	Stockage: PostgreSQL (OLTP), JSONB pour ressources FHIR, objet (documents/imagery), cache (Redis), moteur de recherche (OpenSearch/PG trigram).
	•	Traitements: workers asynchrones, ordonnanceur; règles cliniques.
	•	Multi-tenant/multi-établissement: isolation logique, quotas, paramétrage.
	•	Offline-first (option cabinet): sync résiliente, queues locales chiffrées.
	•	Observabilité: logs structurés, métriques, traces distrib (OpenTelemetry).

9) DevEx & SDLC
	•	Monorepo ou polyrepo structuré; conventions nommage.
	•	CI/CD: build, SAST/DAST, IaC scan, tests, migrations DB, versionning.
	•	Environnements: dev / test / pré-prod / prod; feature flags; seed data.
	•	Qualité code: linters, formatters, coverage, règles merge.
	•	Docs vivantes: ADRs (Architecture Decision Records), Tech spec par feature.

10) Test & validation (focus santé)
	•	Tests: unitaires, contract (OpenAPI/FHIR), e2e (parcours cliniques), perfo (P95/P99), charge, résilience/chaos, sécurité (ASVS), accessibilité.
	•	Connectathons internes: échanges FHIR/DICOM, IHE.
	•	Vérifs métier: revues par médecins/IDE; revues de sécurité/DPO.
	•	Dossier de conformité: preuves, matrices, rapports, SOPs.

11) Exploitation & SRE
	•	SLO/erro budget: latence, dispo, taux d’erreurs, RTO/RPO.
	•	Runbooks: reprises, corruption, dégradations; exercices.
	•	Sauvegardes & PRA: chiffrées, testées; DR régulier.
	•	Supervision: dashboards, alerting, journaux d’audit infalsifiables.

12) Migration & interfaçage SI
	•	Inventaire sources: PMSI/LIS/RIS/PACS/Pharma/agenda/ancienne GED.
	•	Stratégie: migration à blanc, cutover, rétro-compatibilité, mapping terminologies, règles de reprise d’antériorité.

13) Plan de livraison
	•	Découpage en incréments: ex. I1 Identito+Consult, I2 Prescriptions+Résultats, I3 Documents+Messagerie.
	•	DOD/DOR par équipe.
	•	Plan de déploiement: pilote cabinet, petit hôpital, élargissement GHU.

⸻

Artefacts concrets à remettre au développeur (prêts à l’emploi)

A. Exemple de user story + critères d’acceptation
	•	Story: “En tant que médecin, je peux rechercher un patient par INS, nom/naissance, pour ouvrir son dossier en <3 s.”
	•	Gherkin:

Feature: Recherche patient
Scenario: Recherche par INS
  Given un patient avec INS "1 84 12 75 123 456 78"
  When je saisis "184127512345678"
  Then la fiche patient s’affiche en moins de 3 secondes
  And le taux de doublon proposé est ≤ 1 %

B. Extrait de matrice RBAC/ABAC (échantillon)

Ressource	Action	Médecin	IDE	Secrétaire	Pharmacien	Admin
Patient	read/write	✓/✓	✓/✗	✓/✗	✓/✗	✓/✓
Observation	read/write	✓/✓	✓/✓	✓/✗	✓/✗	✓/✓
MedicationRequest	read/write	✓/✓	✓/✗	✓/✗	✓/✓	✓/✓
DocumentReference	read/upload	✓/✓	✓/✓	✓/✓	✓/✓	✓/✓

Règles ABAC : filtre par établissement/UF, rôle de garde, contexte de soin actif, consentement.

C. Spéc OpenAPI (extrait minimal)

openapi: 3.1.0
info: { title: DMI API, version: 0.1.0 }
paths:
  /fhir/Patient/{id}:
    get:
      summary: Get Patient (FHIR)
      parameters: [{ name: id, in: path, required: true, schema: { type: string } }]
      responses:
        '200': { description: OK, content: { application/fhir+json: { schema: { $ref: '#/components/schemas/Patient' } } } }
components:
  schemas:
    Patient:
      description: FHIR Patient resource (profile FR)

D. Dictionnaire de données (extrait)

Champ	Type	Oblig.	Règle qualité	Terminologie
patient.ins	string	Oui	format INS valide, clé unique	—
observation.code	codeable	Oui	doit référencer un code LOINC/SNOMED	LOINC/SNOMED
observation.value	quantity	Oui	unité UCUM obligatoire, plage plausible par type	UCUM

E. Règles de qualité (échantillon)
	•	Rejeter Observation clinique sans effectiveDateTime.
	•	Interdire AllergyIntolerance sans verificationStatus.
	•	Bloquer doublon patient si distance Levenshtein < X ET date de naissance =.

F. Journal d’audit (exigences minimales)
	•	Qui? Quoi? Quand? Où? Pourquoi (motif d’accès)? Avant/Après.
	•	Scellé (hash/chaînage) + horodatage fiable (NTP/Authenticode).

G. Diagramme d’architecture (liste à produire)
	•	Contexte (C4-1), conteneurs (C4-2), composants (C4-3), déploiement (C4-4).
	•	Flux FHIR/DICOM, files, BFF, IAM, stockage, monitoring.

H. Jeux de données synthétiques
	•	Patients avec INS plausibles mais irréversibles.
	•	50+ parcours réalistes (consult, bio, imagerie, ordonnances).
	•	Scripts d’initialisation + anonymisation s’il y a reprise.

⸻

Pile technologique recommandée (indicative, adaptable)
	•	Front: React/Next.js, TypeScript, state mgmt (Zustand/Redux Toolkit), formulaires (React Hook Form), validation (Zod), i18n, tests (Vitest/Playwright).
	•	Design system: tokens, librairie interne accessible (WCAG AA).
	•	Back: Node.js (NestJS) ou Python (FastAPI), FHIR server (HAPI FHIR ou implémentation dédiée), workers (Celery/BullMQ).
	•	Base: PostgreSQL (OLTP), JSONB FHIR, Redis, objet (S3 compatible), recherche (OpenSearch/pg_trgm).
	•	Intégrations: FHIR REST, DICOMweb, MSSanté, Pro Santé Connect.
	•	DevOps: Docker/Compose, IaC (Terraform), GitHub Actions, SAST/DAST, OpenTelemetry, Grafana/Prometheus, Loki/ELK; hébergement certifié HDS.

⸻

Livrables à fournir au dev (checklist)
	1.	Vision produit, KPI, roadmap incrémentale.
	2.	Personae, parcours, blueprint et maquettes hi-fi.
	3.	User stories + Gherkin + DOD/DOR.
	4.	Spéc FHIR + profils FR visés, mapping terminologies.
	5.	OpenAPI/AsyncAPI + schémas d’événements.
	6.	Dictionnaire de données + règles qualité + MDM identités.
	7.	Matrice RBAC/ABAC + flux de consentement + politiques RGPD.
	8.	Architecture C4 + ADRs + plan infra & environnements.
	9.	Stratégie tests (unit/contract/e2e/perf/séc/accès) + données synthétiques.
	10.	Plan migration & intégrations SI.
	11.	Runbooks SRE + SLO + PRA/PCA.
	12.	Dossier conformité (RGPD/HDS) + modèles juridiques (AIPD, registres).
	13.	Scripts d’initialisation & seeds, templates CI/CD.

Si vous voulez, je peux transformer ce plan en un package prêt-à-remettre (modèles de documents, trames OpenAPI/ADR, matrices Excel RBAC, gabarits Gherkin, seed SQL/JSON) ou l’adapter exactement à votre contexte GHU/petit hôpital/cabinet.