# User Stories et Critères d'Acceptation - DMI

## 1. Module Identito-Vigilance

### US-001 : Recherche Patient par INS

**En tant que** secrétaire médicale  
**Je veux** rechercher un patient par son numéro INS  
**Afin de** ouvrir rapidement son dossier sans risque d'erreur d'identité

**Priorité** : CRITIQUE  
**Estimation** : 5 points  
**Sprint** : 1

#### Critères d'acceptation (Gherkin)

```gherkin
Feature: Recherche patient par INS

Background:
  Given je suis authentifié comme "secrétaire"
  And un patient existe avec INS "1 84 12 75 123 456 78"

Scenario: Recherche réussie par INS complet
  Given je suis sur la page de recherche patient
  When je saisis "184127512345678" dans le champ INS
  And je clique sur "Rechercher"
  Then la fiche patient s'affiche en moins de 3 secondes
  And les informations affichées sont :
    | Champ          | Valeur                    |
    | Nom            | MARTIN                    |
    | Prénom         | Jean                      |
    | Date naissance | 12/07/1984                |
    | INS            | 1 84 12 75 123 456 78     |
  And le taux de doublons proposés est ≤ 1%

Scenario: Recherche avec INS invalide
  Given je suis sur la page de recherche patient
  When je saisis "123456789" dans le champ INS
  And je clique sur "Rechercher"
  Then un message d'erreur s'affiche "Format INS invalide"
  And le format attendu est indiqué : "1AAMMJJDDDCCCKK"

Scenario: Patient non trouvé avec INS valide
  Given je suis sur la page de recherche patient
  When je saisis "185030312345699" dans le champ INS
  And je clique sur "Rechercher"
  Then un message s'affiche "Aucun patient trouvé avec cet INS"
  And un bouton "Créer nouveau patient" est proposé
```

#### Règles métier
- Format INS : 15 chiffres (sexe, année, mois, jour, département, commune, ordre, clé)
- Validation clé de contrôle obligatoire
- Appel téléservice INS si patient non trouvé localement
- Timeout téléservice : 5 secondes maximum

#### Définition of Done
- [ ] Tests unitaires (couverture > 80%)
- [ ] Tests d'intégration avec téléservice INS (mock)
- [ ] Validation format INS côté client et serveur
- [ ] Logging audit (recherche patient)
- [ ] Documentation API mise à jour
- [ ] Revue code effectuée
- [ ] Tests performance (< 3 sec p95)

---

### US-002 : Création Patient avec Validation INS

**En tant que** médecin  
**Je veux** créer un nouveau patient avec validation INS automatique  
**Afin de** garantir l'unicité et la fiabilité de l'identité

**Priorité** : CRITIQUE  
**Estimation** : 8 points  
**Sprint** : 1

#### Critères d'acceptation (Gherkin)

```gherkin
Feature: Création patient avec validation INS

Scenario: Création patient avec INS validé
  Given je suis authentifié comme "médecin"
  And je suis sur le formulaire de création patient
  When je remplis les champs :
    | Champ          | Valeur                |
    | Nom            | DUPONT                |
    | Prénom         | Marie                 |
    | Date naissance | 15/03/1990            |
    | Sexe           | F                     |
    | INS            | 2 90 03 15 075 234 89 |
  And je clique sur "Valider INS"
  Then le téléservice INS est interrogé
  And la validation réussit en moins de 5 secondes
  And un indicateur "✓ INS validé" s'affiche
  When je clique sur "Créer patient"
  Then le patient est créé avec statut "INS_VALIDATED"
  And un numéro IPP unique est généré
  And un événement "PatientCreated" est publié

Scenario: Création patient avec INS invalide selon téléservice
  Given je suis authentifié comme "médecin"
  And je suis sur le formulaire de création patient
  When je remplis un formulaire avec INS "2 90 03 15 075 234 80"
  And je clique sur "Valider INS"
  Then le téléservice retourne "INS non validé"
  And un message d'avertissement s'affiche
  And je peux choisir :
    | Option                              |
    | Corriger l'INS                      |
    | Créer sans INS (statut PROVISOIRE) |
    | Annuler                             |

Scenario: Détection doublon potentiel
  Given un patient existe avec :
    | Nom            | MARTIN  |
    | Prénom         | Jean    |
    | Date naissance | 12/07/1984 |
  When je tente de créer un patient avec :
    | Nom            | MARTIN     |
    | Prénom         | Jean       |
    | Date naissance | 12/07/1984 |
  Then une alerte doublon s'affiche avec score de similarité > 90%
  And les informations des 2 patients sont affichées côte à côte
  And je peux choisir :
    | Option                    |
    | Ouvrir dossier existant   |
    | Confirmer création (doublon réel) |
    | Annuler                   |
```

#### Règles métier
- INS obligatoire sauf cas d'urgence (statut PROVISOIRE autorisé)
- Téléservice INS doit être interrogé avant création
- Détection doublons : algorithme Levenshtein + date naissance
- Score doublon > 85% → alerte obligatoire
- Patient PROVISOIRE → workflow régularisation sous 48h

#### Définition of Done
- [ ] Intégration téléservice INS (prod + mock test)
- [ ] Algorithme détection doublons implémenté
- [ ] Tests unitaires et intégration (> 80%)
- [ ] Gestion timeout téléservice (fallback mode dégradé)
- [ ] Audit logging (création + validation INS)
- [ ] Alertes doublons fonctionnelles
- [ ] Documentation utilisateur

---

## 2. Module Consultation

### US-010 : Saisie Consultation avec Template

**En tant que** médecin  
**Je veux** utiliser un template de consultation pré-rempli  
**Afin de** gagner du temps et standardiser la saisie

**Priorité** : HAUTE  
**Estimation** : 5 points  
**Sprint** : 2

#### Critères d'acceptation (Gherkin)

```gherkin
Feature: Saisie consultation avec template

Scenario: Utilisation template "Renouvellement ordonnance"
  Given je suis authentifié comme "médecin"
  And j'ai ouvert le dossier d'un patient
  When je clique sur "Nouvelle consultation"
  And je sélectionne le template "Renouvellement ordonnance"
  Then le formulaire se pré-remplit avec :
    | Section           | Contenu                           |
    | Motif             | Renouvellement ordonnance         |
    | Anamnèse          | "Traitement bien toléré"          |
    | Examen clinique   | Template avec constantes          |
    | Conclusion        | "Poursuite traitement en cours"   |
  And les traitements en cours sont affichés
  And je peux modifier tous les champs

Scenario: Auto-sauvegarde consultation
  Given je suis en train de saisir une consultation
  When je modifie le champ "Motif de consultation"
  Then le brouillon est sauvegardé automatiquement en moins de 2 secondes
  And un indicateur "✓ Sauvegardé" s'affiche temporairement
  When je quitte la page sans enregistrer
  And je rouvre la consultation
  Then mes modifications sont restaurées (brouillon)

Scenario: Calcul automatique scores cliniques
  Given je suis sur le formulaire consultation
  When je saisis les constantes :
    | Constante      | Valeur |
    | Poids          | 75 kg  |
    | Taille         | 1.75 m |
    | TA systolique  | 140    |
    | TA diastolique | 90     |
    | Créatinine     | 95     |
  Then l'IMC est calculé automatiquement : 24.5
  And la clairance rénale (Cockroft) est calculée : 89 ml/min
  And un indicateur d'alerte s'affiche si valeurs anormales
```

#### Règles métier
- Templates personnalisables par médecin
- Auto-sauvegarde toutes les 30 secondes
- Brouillon conservé 7 jours
- Calculs automatiques : IMC, clairance rénale, score de risque
- Alertes si constantes en dehors normes (paramétrable)

---

### US-011 : Saisie Constantes avec Validation

**En tant que** IDE  
**Je veux** saisir rapidement les constantes vitales avec validation automatique  
**Afin de** minimiser les erreurs et gagner du temps

**Priorité** : HAUTE  
**Estimation** : 3 points  
**Sprint** : 2

#### Critères d'acceptation (Gherkin)

```gherkin
Feature: Saisie constantes vitales

Scenario: Saisie constantes normale
  Given je suis authentifié comme "IDE"
  And j'ai ouvert le dossier d'un patient
  When je clique sur "Saisir constantes"
  And je remplis :
    | Constante     | Valeur | Unité |
    | Température   | 37.2   | °C    |
    | FC            | 75     | bpm   |
    | TA            | 120/80 | mmHg  |
    | SpO2          | 98     | %     |
  And je clique sur "Valider"
  Then les constantes sont enregistrées
  And un événement "VitalSignsRecorded" est publié
  And l'horodatage exact est enregistré

Scenario: Alerte constante critique
  Given je suis en train de saisir des constantes
  When je saisis "FC : 135 bpm"
  Then une alerte "Tachycardie" s'affiche immédiatement
  And la constante est mise en évidence (rouge)
  And je peux confirmer ou corriger la valeur
  When je confirme
  Then une notification est envoyée au médecin référent
  And la constante est flaggée "CRITICAL" en base

Scenario: Saisie impossible avec valeur aberrante
  Given je suis en train de saisir des constantes
  When je saisis "Température : 50°C"
  Then un message d'erreur bloquant s'affiche
  And le message indique "Valeur aberrante (plage : 30-45°C)"
  And je ne peux pas valider tant que non corrigé
```

#### Règles métier
- Plages de valeurs par constante (normales, alertes, aberrantes)
- Alertes critiques : notification temps réel médecin
- Horodatage précis (seconde) obligatoire
- Traçabilité : qui a saisi, quand, device (si intégré)
- Courbes de suivi automatiques sur 24h/7j/30j

---

## 3. Module Prescription

### US-020 : Prescription Médicamenteuse avec Vérification Interactions

**En tant que** médecin  
**Je veux** prescrire un médicament avec vérification automatique des interactions  
**Afin de** prévenir les risques iatrogènes

**Priorité** : CRITIQUE  
**Estimation** : 13 points  
**Sprint** : 3

#### Critères d'acceptation (Gherkin)

```gherkin
Feature: Prescription médicamenteuse

Scenario: Prescription simple sans interaction
  Given je suis authentifié comme "médecin"
  And le patient a comme traitement en cours : "Paracétamol 1g"
  When je clique sur "Nouvelle prescription"
  And je recherche "Ibuprofène"
  And je sélectionne "Ibuprofène 400mg - ADVIL"
  And je saisis :
    | Champ          | Valeur                 |
    | Posologie      | 1 comprimé             |
    | Fréquence      | 3 fois par jour        |
    | Durée          | 5 jours                |
  Then une analyse d'interactions est lancée automatiquement
  And le résultat "Aucune interaction détectée" s'affiche en vert
  When je clique sur "Ajouter à l'ordonnance"
  Then le médicament est ajouté à l'ordonnance
  And le coût approximatif est affiché

Scenario: Détection interaction médicamenteuse majeure
  Given le patient a comme traitement : "Warfarine 5mg"
  When je tente de prescrire "Aspirine 100mg"
  Then une alerte "INTERACTION MAJEURE" s'affiche en rouge
  And le détail de l'interaction est affiché :
    """
    Risque hémorragique augmenté.
    Contre-indication relative.
    Si prescription maintenue : surveillance INR rapprochée.
    """
  And je peux choisir :
    | Option                                |
    | Annuler prescription                  |
    | Prescrire malgré alerte (avec motif)  |
    | Voir alternatives thérapeutiques      |
  When je choisis "Voir alternatives"
  Then une liste de médicaments alternatifs est proposée

Scenario: Alerte allergie patient
  Given le patient a une allergie déclarée : "Pénicilline"
  When je tente de prescrire "Amoxicilline 1g"
  Then une alerte "ALLERGIE PATIENT" bloquante s'affiche
  And le message indique : "Patient allergique à la Pénicilline"
  And je ne peux pas poursuivre sans annuler ou contacter pharmacien

Scenario: Adaptation posologie selon fonction rénale
  Given le patient a une clairance rénale de 45 ml/min
  When je prescris "Enoxaparine"
  Then une alerte "Adaptation posologie" s'affiche
  And la posologie recommandée est proposée automatiquement
  And la justification est affichée : "Insuffisance rénale modérée"
```

#### Règles métier
- Base médicamenteuse (BDM) mise à jour mensuellement
- Analyse interactions : base Thériaque/ANSM
- Niveaux d'alerte : Information < Précaution < Contre-indication < Allergie
- Allergie patient = alerte bloquante
- Adaptation posologie : clairance rénale, poids, âge
- Traçabilité décisions (prescription malgré alerte)

#### Définition of Done
- [ ] Intégration BDM (CIP/UCD + ATC)
- [ ] Moteur d'analyse interactions (Thériaque ou équivalent)
- [ ] Gestion alertes (niveaux, blocking/non-blocking)
- [ ] Calcul posologies adaptées (fonction rénale, poids)
- [ ] Tests unitaires et intégration (> 80%)
- [ ] Performance (analyse < 500ms p95)
- [ ] Audit logging (prescriptions + alertes)
- [ ] Documentation clinique

---

### US-021 : Validation Pharmaceutique

**En tant que** pharmacien  
**Je veux** valider ou refuser une prescription médicale  
**Afin de** sécuriser le circuit du médicament

**Priorité** : CRITIQUE  
**Estimation** : 8 points  
**Sprint** : 4

#### Critères d'acceptation (Gherkin)

```gherkin
Feature: Validation pharmaceutique

Scenario: Validation prescription conforme
  Given je suis authentifié comme "pharmacien"
  And une prescription est en attente de validation
  When j'ouvre la prescription
  Then j'ai une vue consolidée :
    | Section                  | Contenu                           |
    | Patient                  | Identité, poids, âge, allergies   |
    | Diagnostic               | Motif hospitalisation             |
    | Fonction rénale          | Clairance 85 ml/min (normale)     |
    | Traitements en cours     | Liste complète                    |
    | Nouvelle prescription    | Détail médicament + posologie     |
    | Interactions             | Analyse automatique               |
  When je clique sur "Valider"
  Then la prescription passe en statut "VALIDATED"
  And une notification est envoyée au médecin et à l'IDE
  And l'heure de validation est enregistrée

Scenario: Refus prescription avec contre-indication
  Given une prescription contient une contre-indication
  When je clique sur "Refuser"
  Then un formulaire de refus s'affiche avec :
    | Champ                 | Type            |
    | Motif refus           | Liste déroulante |
    | Commentaire           | Texte libre     |
    | Alternative proposée  | Recherche médicament |
  When je remplis le motif "Contre-indication majeure"
  And je propose "Alternative : Paracétamol 1g"
  And je clique sur "Envoyer"
  Then la prescription passe en statut "REFUSED"
  And une notification urgente est envoyée au médecin prescripteur
  And le refus est tracé dans l'audit log

Scenario: Adaptation posologie
  Given une prescription a une posologie inadaptée
  When je clique sur "Adapter posologie"
  Then je peux modifier :
    | Champ       | Modification                |
    | Dose        | 500mg → 250mg               |
    | Fréquence   | 3x/j → 2x/j                 |
    | Commentaire | "Adaptation insuffisance rénale" |
  When je valide l'adaptation
  Then la prescription est mise à jour
  And le statut devient "ADAPTED_BY_PHARMACIST"
  And le médecin reçoit une notification pour validation finale
```

#### Règles métier
- Validation obligatoire par pharmacien avant dispensation
- Délai validation cible : < 2h (hors urgences)
- Urgences vitales : validation a posteriori possible (tracée)
- Refus/adaptation : retour médecin obligatoire
- Toutes décisions tracées avec horodatage + justification

---

## 4. Module Laboratoire

### US-030 : Prescription Analyses Biologiques

**En tant que** médecin  
**Je veux** prescrire des analyses biologiques avec codes LOINC  
**Afin de** transmettre la demande au laboratoire de façon structurée

**Priorité** : HAUTE  
**Estimation** : 8 points  
**Sprint** : 5

#### Critères d'acceptation (Gherkin)

```gherkin
Feature: Prescription analyses biologiques

Scenario: Prescription bilan biologique standard
  Given je suis authentifié comme "médecin"
  And j'ai ouvert le dossier patient
  When je clique sur "Prescrire examens"
  And je recherche "NFS"
  Then une liste de panels pré-définis s'affiche :
    | Panel                        | Codes LOINC inclus        |
    | NFS (Numération Formule)     | 57021-8, 718-7, 777-3...  |
    | Ionogramme                   | 2951-2, 2823-3, 2075-0... |
    | Bilan hépatique              | 1742-6, 1920-8, 6768-6... |
  When je sélectionne "NFS"
  Then les examens individuels du panel sont affichés
  And je peux ajouter/retirer des examens
  When je clique sur "Valider prescription"
  Then une ServiceRequest FHIR est créée
  And un message HL7 ORM est envoyé au LIS
  And un événement "LabOrderCreated" est publié

Scenario: Ajout renseignements cliniques
  Given je prescris des analyses biologiques
  When j'ajoute le renseignement clinique : "Suspicion d'anémie"
  And je marque l'examen comme "URGENT"
  Then ces informations sont incluses dans le message ORM
  And le laboratoire reçoit le contexte clinique
  And la priorité "URGENT" est transmise

Scenario: Consultation historique analyses
  Given le patient a des résultats d'analyses antérieurs
  When je consulte l'historique "NFS"
  Then je vois un graphique d'évolution sur :
    | Période   | Données affichées           |
    | 7 jours   | Valeurs quotidiennes        |
    | 1 mois    | Évolution hebdomadaire      |
    | 1 an      | Évolution mensuelle         |
  And les valeurs hors normes sont mises en évidence
  And je peux exporter les données (CSV, PDF)
```

#### Règles métier
- Nomenclature LOINC obligatoire
- Panels pré-définis personnalisables par service
- Transmission HL7 v2 ORM vers LIS
- Renseignements cliniques optionnels mais recommandés
- Priorités : ROUTINE / URGENT / STAT (immédiat)
- Historique analyses conservé (loi : 20 ans mini)

---

### US-031 : Réception et Affichage Résultats Labo

**En tant que** médecin  
**Je veux** recevoir les résultats d'analyses en temps réel avec alertes  
**Afin de** réagir rapidement aux valeurs critiques

**Priorité** : CRITIQUE  
**Estimation** : 13 points  
**Sprint** : 5-6

#### Critères d'acceptation (Gherkin)

```gherkin
Feature: Réception résultats laboratoire

Scenario: Réception résultats normaux
  Given une prescription d'analyses a été envoyée au LIS
  When le laboratoire transmet les résultats (HL7 ORU)
  Then les résultats sont intégrés automatiquement au dossier patient
  And des ressources Observation FHIR sont créées avec codes LOINC
  And le médecin prescripteur reçoit une notification
  And les résultats sont affichés dans l'onglet "Résultats"
  And le délai de réception est < 2 minutes (p95)

Scenario: Alerte résultat critique
  Given une analyse a été prescrite
  When le laboratoire transmet un résultat critique :
    | Analyse       | Valeur | Norme      | Seuil critique |
    | Kaliémie      | 6.5    | 3.5-5.0    | > 6.0          |
  Then une alerte "RÉSULTAT CRITIQUE" est générée immédiatement
  And le médecin prescripteur reçoit une notification push
  And le résultat est mis en évidence (rouge, gras)
  And un flag "CRITICAL" est enregistré
  And l'équipe soignante (IDE) est notifiée

Scenario: Comparaison avec résultats antérieurs
  Given le patient a des résultats antérieurs pour "Créatinine"
  When je consulte le nouveau résultat "Créatinine : 150 µmol/L"
  Then le résultat précédent est affiché à côté : "100 µmol/L (J-7)"
  And l'évolution est calculée : "+50% en 7 jours"
  And un indicateur visuel (flèche rouge ↑) est affiché

Scenario: Résultat en attente
  Given une prescription a été envoyée il y a 2 heures
  When je consulte les résultats
  Then le statut "En attente" s'affiche
  And l'heure de prescription est indiquée
  And un timer "Délai depuis prescription : 2h05" est affiché
```

#### Règles métier
- Réception HL7 v2 ORU (listener 24/7)
- Mapping LOINC obligatoire (validation à la réception)
- Valeurs critiques : notification immédiate (< 1 min)
- Unités UCUM obligatoires
- Comparaison avec résultats antérieurs automatique
- Courbes d'évolution générées (7j, 1m, 3m, 1an)
- Archivage résultats : 20 ans minimum

---

## 5. Module Documents

### US-040 : Génération Ordonnance PDF

**En tant que** médecin  
**Je veux** générer automatiquement une ordonnance PDF conforme  
**Afin de** gagner du temps et assurer la conformité réglementaire

**Priorité** : HAUTE  
**Estimation** : 5 points  
**Sprint** : 7

#### Critères d'acceptation (Gherkin)

```gherkin
Feature: Génération ordonnance

Scenario: Génération ordonnance simple
  Given j'ai prescrit 2 médicaments
  When je clique sur "Générer ordonnance"
  Then un PDF est généré en moins de 5 secondes
  And le PDF contient :
    | Section                    | Contenu                          |
    | En-tête                    | Logo + coordonnées praticien     |
    | Identité patient           | Nom, prénom, date naissance      |
    | Date prescription          | JJ/MM/AAAA                       |
    | Liste médicaments          | DCI, posologie, durée            |
    | Signature                  | Signature électronique praticien |
    | Mentions légales           | QR code, N° RPPS, ALD...         |
  And le format est conforme réglementation française

Scenario: Ordonnance bizone (ALD)
  Given le patient est en ALD (Affection Longue Durée)
  When je génère l'ordonnance
  And je coche "ALD : Diabète de type 2"
  Then une ordonnance bizone est générée
  And la partie "ALD" contient les médicaments concernés
  And la partie "Hors ALD" contient les autres médicaments
  And les codes CIM-10 ALD sont inclus

Scenario: Signature électronique ordonnance
  Given une ordonnance a été générée
  When je clique sur "Signer électroniquement"
  Then un workflow de signature est lancé
  And je peux signer avec :
    | Méthode           | Dispositif        |
    | Carte CPS         | Lecteur carte     |
    | e-CPS             | Authentification SSO |
  When je signe avec e-CPS
  Then l'ordonnance est signée avec certificat électronique
  And un sceau horodaté est appliqué
  And le PDF final est non modifiable
```

#### Règles métier
- Format ordonnance conforme décret (mentions obligatoires)
- QR code DataMatrix pour sécurisation
- Signature électronique CPS/e-CPS obligatoire
- Ordonnance bizone si patient ALD
- Archivage ordonnances : 3 ans minimum
- Envoi optionnel email/SMS patient

---

## 6. Règles Qualité des Données

### RQ-001 : Complétude Obligatoire Dossier Patient

```gherkin
Feature: Complétude dossier patient

Rule: Champs obligatoires patient
  Given la création d'un nouveau patient
  Then les champs suivants sont OBLIGATOIRES :
    | Champ           | Règle                               |
    | Nom             | Non vide, 2-50 caractères           |
    | Prénom          | Non vide, 2-50 caractères           |
    | Date naissance  | Format JJ/MM/AAAA, ≤ aujourd'hui    |
    | Sexe            | M / F / Autre                       |
    | INS             | Format valide ou statut PROVISOIRE  |

Rule: Interdiction doublons stricts
  Given un patient existe avec (Nom, Prénom, Date naissance)
  When je tente de créer un patient avec les mêmes données
  Then la création est bloquée
  And une alerte doublon s'affiche
  And le dossier existant est proposé
```

### RQ-002 : Observation Clinique Structurée

```gherkin
Feature: Qualité observations cliniques

Rule: Code terminologie obligatoire
  Given la saisie d'une observation clinique
  Then un code LOINC ou SNOMED CT est OBLIGATOIRE
  And le libellé textuel seul est INTERDIT
  
Example: Observation conforme
  | Type observation | Code LOINC | Valeur   | Unité UCUM |
  | Glycémie         | 2339-0     | 1.2      | g/L        |
  | Température      | 8310-5     | 37.5     | Cel        |

Example: Observation rejetée
  | Type observation | Code  | Valeur | Raison rejet                 |
  | "Température"    | null  | 37.5   | Code LOINC manquant          |
  | Glycémie         | 2339-0| 1.2    | Unité UCUM manquante         |

Rule: Plage de valeurs plausibles
  Given une observation avec code LOINC
  Then une plage de valeurs plausibles est définie
  And une valeur hors plage génère une alerte
  
Example: Alertes valeurs aberrantes
  | Observation | Valeur | Plage normale | Plage max   | Action           |
  | Température | 25°C   | 36-38°C       | 30-45°C     | Alerte aberrant  |
  | FC          | 200    | 60-100 bpm    | 30-220 bpm  | Alerte critique  |
  | Glycémie    | 50 g/L | 0.7-1.1 g/L   | 0.2-5 g/L   | Rejet (aberrant) |
```

### RQ-003 : Prescription Complète et Traçable

```gherkin
Feature: Qualité prescriptions

Rule: Champs obligatoires prescription
  Given une nouvelle prescription médicamenteuse
  Then les champs suivants sont OBLIGATOIRES :
    | Champ            | Règle                                |
    | Médicament       | Code CIP ou UCD                      |
    | Posologie        | Dose + unité (mg, g, UI...)          |
    | Voie admin       | Liste contrôlée (PO, IV, IM...)      |
    | Fréquence        | Structuré (1x/j, 3x/j, toutes les 6h)|
    | Durée            | Nombre de jours ou "Long cours"      |
    | Prescripteur     | RPPS médecin                         |
    | Date prescription| Horodatage exact                     |

Rule: Validation interactions avant enregistrement
  Given une prescription avec médicament M1
  When j'ajoute un médicament M2
  Then une analyse d'interactions est lancée AVANT enregistrement
  And si interaction MAJEURE détectée :
    | Action                                           |
    | Blocage avec confirmation médecin obligatoire    |
    | Traçabilité de la décision (motif si maintenue)  |

Rule: Allergie patient bloquante
  Given un patient avec allergie "Pénicilline"
  When je tente de prescrire un médicament contenant "Pénicilline"
  Then la prescription est BLOQUÉE
  And un message d'erreur s'affiche
  And la prescription ne peut pas être enregistrée
```

---

## 7. Matrice de Traçabilité (Exemples)

| User Story | Persona      | Module          | FHIR Resource       | Tests Gherkin | Sprint |
|------------|--------------|-----------------|---------------------|---------------|--------|
| US-001     | Secrétaire   | Identito        | Patient             | ✅ 3 scenarios | 1      |
| US-002     | Médecin      | Identito        | Patient             | ✅ 3 scenarios | 1      |
| US-010     | Médecin      | Consultation    | Encounter           | ✅ 3 scenarios | 2      |
| US-011     | IDE          | Consultation    | Observation         | ✅ 3 scenarios | 2      |
| US-020     | Médecin      | Prescription    | MedicationRequest   | ✅ 4 scenarios | 3      |
| US-021     | Pharmacien   | Prescription    | MedicationRequest   | ✅ 3 scenarios | 4      |
| US-030     | Médecin      | Laboratoire     | ServiceRequest      | ✅ 3 scenarios | 5      |
| US-031     | Médecin      | Laboratoire     | Observation         | ✅ 4 scenarios | 5-6    |
| US-040     | Médecin      | Documents       | DocumentReference   | ✅ 3 scenarios | 7      |

---

## 8. Templates de User Stories (À Compléter)

### Template US : Nouvelle Fonctionnalité

```markdown
### US-XXX : [Titre court et explicite]

**En tant que** [rôle/persona]  
**Je veux** [action/fonctionnalité]  
**Afin de** [bénéfice/objectif]

**Priorité** : [CRITIQUE / HAUTE / MOYENNE / BASSE]  
**Estimation** : [points Fibonacci]  
**Sprint** : [numéro]

#### Contexte
[Description détaillée du contexte métier]

#### Critères d'acceptation (Gherkin)
```gherkin
Feature: [Nom feature]

Scenario: [Scenario principal - happy path]
  Given [contexte initial]
  When [action utilisateur]
  Then [résultat attendu]
  And [vérifications complémentaires]

Scenario: [Scenario alternatif]
  [...]

Scenario: [Scenario d'erreur]
  [...]
```

#### Règles métier
- [Liste des règles métier applicables]

#### Dépendances
- [US ou modules dépendants]

#### Maquettes
- [Lien vers maquettes Figma/Sketch]

#### Définition of Done
- [ ] Tests unitaires (couverture > 80%)
- [ ] Tests d'intégration
- [ ] Tests Gherkin automatisés
- [ ] Revue code effectuée
- [ ] Documentation utilisateur
- [ ] Documentation technique
- [ ] Performance validée
- [ ] Sécurité validée
- [ ] Accessibilité WCAG 2.1 AA
- [ ] Audit logging si applicable
```

---

**Document validé par** : Product Owner, Tech Lead, Direction Médicale  
**Date** : 2025-01-10  
**Version** : 1.0  
**Prochaine revue** : 2025-02-10
