# Jeux de Données Synthétiques - DMI

## 1. Vue d'Ensemble

### 1.1 Objectifs

Les données synthétiques sont essentielles pour :

- ✅ **Développement** : Tests unitaires et d'intégration
- ✅ **Démonstration** : Présentations clients et formations
- ✅ **Performance** : Tests de charge et de scalabilité
- ✅ **Sécurité** : Aucune donnée réelle de patients utilisée
- ✅ **Compliance** : Respect RGPD/HDS (pas de données personnelles)

### 1.2 Principes de Génération

#### Réalisme

- Scénarios cliniques cohérents
- Parcours patients crédibles
- Terminologies médicales valides (LOINC, SNOMED CT, CIM-10, ATC)
- Valeurs biologiques plausibles

#### Sécurité

- INS générés mais **non valides** (clé de contrôle incorrecte)
- Noms/prénoms issus de listes fictives
- Adresses, téléphones, emails générés
- Aucune correspondance avec données réelles possible

#### Diversité

- Âges : 0-100 ans
- Sexes : M, F, Indéterminé
- Pathologies variées
- Traitements multiples
- Services hospitaliers divers

### 1.3 Volumétrie

| Dataset | Nb Patients | Nb Consultations | Nb Prescriptions | Nb Résultats Labo | Utilisation |
|---------|-------------|------------------|------------------|-------------------|-------------|
| **Minimal** | 10 | 20 | 30 | 50 | Tests unitaires |
| **Standard** | 100 | 500 | 1,000 | 2,000 | Tests d'intégration, démo |
| **Large** | 1,000 | 10,000 | 20,000 | 50,000 | Tests de performance |
| **Stress** | 10,000 | 100,000 | 200,000 | 500,000 | Tests de charge |

## 2. Patients Synthétiques

### 2.1 Profils Types

#### Profil 1 : Patient Chronique (Diabète Type 2)

```json
{
  "id": "patient-001-diabete",
  "ipp": "100000018",
  "ins": "299120175012399", // Format: 1AAMMJJDDDCCCKK (15 characters, intentionally invalid for security)
  "ins_status": "PROVISOIRE",
  "nom": "DUBOIS",
  "prenom": "François",
  "date_naissance": "1965-03-12",
  "sexe": "M",
  "adresse": "42 Avenue de la République, 75011 Paris",
  "telephone": "+33612000001",
  "email": "francois.dubois.synthetic@keneyapp.test",
  "status": "ACTIVE",
  "conditions": [
    {
      "code": "E11",
      "system": "ICD-10",
      "display": "Diabète sucré de type 2",
      "verification_status": "CONFIRMED",
      "onset_date": "2015-06-15",
      "severity": "MODERATE"
    },
    {
      "code": "I10",
      "system": "ICD-10",
      "display": "Hypertension artérielle essentielle",
      "verification_status": "CONFIRMED",
      "onset_date": "2018-02-10"
    }
  ],
  "allergies": [
    {
      "allergen_code": "387207008",
      "allergen_display": "Pénicilline",
      "severity": "HIGH",
      "reaction_type": "ALLERGY",
      "verification_status": "CONFIRMED",
      "onset_date": "1985-07-20",
      "reactions": ["Rash cutané", "Prurit"]
    }
  ],
  "medications": [
    {
      "medication_code": "3400893432051",
      "medication_display": "METFORMINE 1000mg cp",
      "atc_code": "A10BA02",
      "dosage_text": "1 comprimé 2 fois par jour",
      "status": "ACTIVE",
      "start_date": "2015-06-15"
    },
    {
      "medication_code": "3400937265058",
      "medication_display": "RAMIPRIL 5mg cp",
      "atc_code": "C09AA05",
      "dosage_text": "1 comprimé 1 fois par jour le matin",
      "status": "ACTIVE",
      "start_date": "2018-02-10"
    }
  ],
  "recent_observations": [
    {
      "code": "2339-0",
      "display": "Glycémie à jeun",
      "value": 1.35,
      "unit": "g/L",
      "reference_low": 0.7,
      "reference_high": 1.1,
      "interpretation": "HIGH",
      "effective_date": "2025-01-05"
    },
    {
      "code": "4548-4",
      "display": "HbA1c",
      "value": 7.2,
      "unit": "%",
      "reference_low": 4.0,
      "reference_high": 6.0,
      "interpretation": "HIGH",
      "effective_date": "2025-01-05"
    }
  ]
}
```

#### Profil 2 : Patient Urgence (Traumatisme)

```json
{
  "id": "patient-002-traumatisme",
  "ipp": "100000026",
  "ins": "185061275034512",
  "ins_status": "PROVISOIRE",
  "nom": "LEROUX",
  "prenom": "Sophie",
  "date_naissance": "1992-06-25",
  "sexe": "F",
  "telephone": "+33698000002",
  "status": "ACTIVE",
  "emergency_context": {
    "admission_reason": "Chute vélo - trauma crânien",
    "glasgow_score": 15,
    "triage_level": "URGENT",
    "arrival_mode": "AMBULANCE",
    "arrival_datetime": "2025-01-10T14:30:00Z"
  },
  "conditions": [],
  "allergies": [],
  "medications": [
    {
      "medication_code": "3400938559019",
      "medication_display": "DOLIPRANE 1000mg",
      "status": "ACTIVE",
      "dosage_text": "1 comprimé si douleur (max 3g/jour)",
      "start_date": "2025-01-10",
      "end_date": "2025-01-17"
    }
  ],
  "recent_observations": [
    {
      "code": "8310-5",
      "display": "Température",
      "value": 37.2,
      "unit": "Cel",
      "effective_date": "2025-01-10T14:35:00Z"
    },
    {
      "code": "8867-4",
      "display": "Fréquence cardiaque",
      "value": 82,
      "unit": "bpm",
      "effective_date": "2025-01-10T14:35:00Z"
    },
    {
      "code": "85354-9",
      "display": "TA systolique",
      "value": 128,
      "unit": "mmHg",
      "effective_date": "2025-01-10T14:35:00Z"
    }
  ],
  "imaging_studies": [
    {
      "study_type": "CT_HEAD",
      "study_date": "2025-01-10T15:00:00Z",
      "status": "COMPLETED",
      "result": "Pas d'hémorragie intracrânienne. Surveillance clinique."
    }
  ]
}
```

#### Profil 3 : Nouveau-né (Pédiatrie)

```json
{
  "id": "patient-003-nouveau-ne",
  "ipp": "100000034",
  "ins": "124011075098765",
  "ins_status": "VALIDATED",
  "nom": "PETIT",
  "prenom": "Emma",
  "date_naissance": "2025-01-08",
  "sexe": "F",
  "adresse": "15 Rue des Lilas, 69001 Lyon",
  "status": "ACTIVE",
  "birth_context": {
    "gestational_age_weeks": 39,
    "birth_weight_grams": 3250,
    "birth_length_cm": 50,
    "apgar_1min": 9,
    "apgar_5min": 10,
    "delivery_mode": "VAGINAL"
  },
  "conditions": [],
  "allergies": [],
  "medications": [
    {
      "medication_code": "3400935752857",
      "medication_display": "VITAMINE K1 2mg/0.2ml amp inj",
      "status": "COMPLETED",
      "dosage_text": "2mg IM dose unique",
      "start_date": "2025-01-08",
      "end_date": "2025-01-08"
    }
  ],
  "recent_observations": [
    {
      "code": "8302-2",
      "display": "Taille",
      "value": 50,
      "unit": "cm",
      "effective_date": "2025-01-08"
    },
    {
      "code": "29463-7",
      "display": "Poids corporel",
      "value": 3.25,
      "unit": "kg",
      "effective_date": "2025-01-08"
    },
    {
      "code": "8310-5",
      "display": "Température",
      "value": 36.8,
      "unit": "Cel",
      "effective_date": "2025-01-09T08:00:00Z"
    }
  ],
  "vaccinations": [
    {
      "vaccine_code": "J07BK01",
      "vaccine_display": "BCG",
      "status": "SCHEDULED",
      "scheduled_date": "2025-02-08"
    }
  ]
}
```

#### Profil 4 : Patient Oncologie

```json
{
  "id": "patient-004-cancer",
  "ipp": "100000042",
  "ins": "278091075056789",
  "ins_status": "VALIDATED",
  "nom": "DURAND",
  "prenom": "Michel",
  "date_naissance": "1958-09-17",
  "sexe": "M",
  "adresse": "8 Boulevard Saint-Germain, 75005 Paris",
  "telephone": "+33601000004",
  "email": "michel.durand.synthetic@keneyapp.test",
  "status": "ACTIVE",
  "conditions": [
    {
      "code": "C61",
      "system": "ICD-10",
      "display": "Tumeur maligne de la prostate",
      "verification_status": "CONFIRMED",
      "onset_date": "2024-03-15",
      "severity": "HIGH",
      "stage": "T2N0M0"
    }
  ],
  "allergies": [],
  "medications": [
    {
      "medication_code": "3400927544385",
      "medication_display": "BICALUTAMIDE 50mg cp",
      "atc_code": "L02BB03",
      "dosage_text": "1 comprimé par jour",
      "status": "ACTIVE",
      "start_date": "2024-04-01"
    }
  ],
  "recent_observations": [
    {
      "code": "2857-1",
      "display": "PSA (antigène prostatique spécifique)",
      "value": 12.5,
      "unit": "ng/mL",
      "reference_low": 0.0,
      "reference_high": 4.0,
      "interpretation": "HIGH",
      "effective_date": "2025-01-05"
    },
    {
      "code": "718-7",
      "display": "Hémoglobine",
      "value": 11.2,
      "unit": "g/dL",
      "reference_low": 13.0,
      "reference_high": 17.0,
      "interpretation": "LOW",
      "effective_date": "2025-01-05"
    }
  ],
  "procedures": [
    {
      "code": "33.21",
      "system": "CCAM",
      "display": "Biopsie prostatique échoguidée",
      "performed_date": "2024-03-20",
      "status": "COMPLETED"
    }
  ]
}
```

### 2.2 Distributions Démographiques

#### Distribution par Âge

```python
age_distribution = {
    "0-1 ans": 2,      # Néonatologie, pédiatrie
    "1-5 ans": 5,      # Pédiatrie
    "5-18 ans": 10,    # Pédiatrie, adolescence
    "18-30 ans": 15,   # Jeunes adultes
    "30-50 ans": 25,   # Adultes actifs
    "50-65 ans": 20,   # Adultes matures
    "65-80 ans": 15,   # Seniors
    "80+ ans": 8       # Gériatrie
}
```

#### Distribution par Sexe

```python
sexe_distribution = {
    "M": 48,
    "F": 50,
    "I": 1,    # Indéterminé (intersexe, nouveau-nés)
    "U": 1     # Inconnu (urgences sans identité)
}
```

#### Distribution Pathologies

```python
pathologies_distribution = {
    "Aucune (patient sain)": 30,
    "1 pathologie chronique": 35,
    "2-3 pathologies": 25,
    "Polypathologie (4+)": 10
}

pathologies_top = [
    ("E11", "Diabète type 2", 15),
    ("I10", "Hypertension artérielle", 20),
    ("E78", "Hypercholestérolémie", 12),
    ("J45", "Asthme", 8),
    ("M79", "Douleurs articulaires", 10),
    ("F32", "Épisode dépressif", 6),
    ("E66", "Obésité", 9),
    ("K21", "Reflux gastro-œsophagien", 7)
]
```

## 3. Parcours Cliniques Synthétiques

### 3.1 Parcours 1 : Consultation Diabète (Suivi Régulier)

```yaml
Parcours: Consultation ambulatoire - Suivi diabète
Patient: Patient-001-diabete (François DUBOIS, 59 ans)
Durée: 30 minutes

Étapes:
  1. Prise RDV (J-7):
    - Type: Consultation de suivi
    - Praticien: Dr. MARTIN (endocrinologue)
    - Date: 2025-01-10 09:00

  2. Accueil (J, 09:00):
    - Vérification identité (INS)
    - Mise à jour coordonnées
    - Statut: "Arrivé"

  3. Pré-consultation IDE (J, 09:05):
    - Poids: 85 kg (stable)
    - Taille: 175 cm
    - TA: 135/82 mmHg
    - FC: 72 bpm
    - Glycémie capillaire: 1.42 g/L

  4. Consultation Médecin (J, 09:15):
    - Anamnèse: Observance traitement bonne, pas d'hypoglycémie
    - Examen: RAS, pouls périphériques présents
    - Résultats labo (J-5):
      * HbA1c: 7.2% (cible < 7%)
      * Créatinine: 95 µmol/L (DFG > 60)
      * LDL: 1.1 g/L (cible < 1.0)
    - Diagnostic: Diabète type 2 équilibré, HTA contrôlée
    - Plan:
      * Poursuite METFORMINE 1000mg x2/j
      * Poursuite RAMIPRIL 5mg x1/j
      * Ajout ATORVASTATINE 20mg (LDL limite)
      * RDV suivi dans 3 mois

  5. Prescription (J, 09:25):
    - Ordonnance ALD (3 mois):
      * METFORMINE 1000mg: 1cp matin et soir
      * RAMIPRIL 5mg: 1cp le matin
      * ATORVASTATINE 20mg: 1cp le soir
    - Prescription bilan biologique (J+90):
      * Glycémie à jeun
      * HbA1c
      * Bilan lipidique
      * Créatinine + DFG

  6. Documents générés:
    - Ordonnance ALD (PDF signé)
    - Prescription laboratoire
    - CR consultation (envoi médecin traitant)

  7. Sortie (J, 09:30):
    - Télétransmission CPAM effectuée
    - RDV de suivi programmé (2025-04-10)
```

### 3.2 Parcours 2 : Urgence Traumatisme

```yaml
Parcours: Urgences - Traumatisme crânien léger
Patient: Patient-002-traumatisme (Sophie LEROUX, 32 ans)
Durée: 4 heures

Étapes:
  1. Arrivée SAMU (J, 14:30):
    - Admission par ambulance
    - Motif: Chute vélo, TC sans PCI
    - Glasgow: 15/15
    - Triage: URGENT (niveau 2)

  2. Prise en charge IDE (14:32):
    - Création dossier (identité provisoire si besoin)
    - Constantes:
      * TA: 128/78 mmHg
      * FC: 82 bpm
      * Temp: 37.2°C
      * SpO2: 98% (air ambiant)
      * Glasgow: 15/15
    - Installation box urgences

  3. Examen Médecin Urgentiste (14:40):
    - Anamnèse:
      * Chute vélo il y a 1h
      * PCI < 1 minute
      * Céphalées, pas de vomissements
      * Pas d'antécédents
    - Examen clinique:
      * Plaie cuir chevelu temporal droit (3 cm)
      * Pas de déficit neuro
      * Mobilité cervicale normale
    - Décision: Scanner cérébral + suture

  4. Examens Complémentaires (15:00):
    - Scanner cérébral sans injection
    - Résultat (15:30): Pas d'hémorragie intracrânienne

  5. Soins (15:45):
    - Nettoyage plaie
    - Anesthésie locale (Xylocaïne 1%)
    - Suture 4 points
    - Pansement

  6. Prescription Sortie (16:15):
    - DOLIPRANE 1000mg: 1cp si douleur (max 3g/j) x 7j
    - Pas d'AINS (risque hémorragique post-TC)
    - Consignes surveillance 48h
    - Ablation points J+10

  7. Documents générés:
    - CR passage urgences
    - Ordonnance
    - Consignes écrites surveillance TC
    - Courrier médecin traitant

  8. Sortie (16:30):
    - Mode sortie: Retour domicile accompagné
    - RDV ablation fils prévu (2025-01-20)
```

### 3.3 Parcours 3 : Hospitalisation Chirurgie

```yaml
Parcours: Hospitalisation - Cholécystectomie programmée
Patient: Patient-005-chir (Martine LEFÈVRE, 52 ans)
Durée: 3 jours

Jour J-7 (Consultation Pré-opératoire):
  - Examen clinique
  - Prescription bilan pré-op:
    * NFS, TP, TCA
    * Groupe sanguin RAI
    * Glycémie, créatinine
    * ECG
  - Explications intervention
  - Consentement éclairé signé

Jour J-1 (Admission):
  - Admission service chirurgie (17:00)
  - Chambre individuelle
  - Consultation anesthésiste:
    * Score ASA 2
    * Pas d'intubation difficile
    * Validation bilan pré-op
  - Prescription pré-op:
    * À jeun depuis 22h
    * DAFALGAN 1g à 22h
    * Douche Bétadine matin J

Jour J (Intervention):
  - Prémédication (07:00):
    * ATARAX 25mg per os
  - Départ bloc (08:00)
  - Intervention (08:30 - 10:00):
    * Cholécystectomie laparoscopique
    * Pas de complication
    * Vésicule lithiasique
  - Réveil (10:00 - 11:00):
    * EVA douleur: 3/10
    * Constantes stables
  - Retour chambre (11:00)
  - Prescription post-op:
    * Perfusion NaCl 0.9% 1L/8h
    * PARACETAMOL 1g IV x4/j
    * MORPHINE 10mg SC si EVA > 4
    * Lever autorisé J+0 soir
    - Reprise alimentation progressive

Jour J+1 (Post-op J+1):
  - Constantes normales
  - Douleur contrôlée (EVA 2/10)
  - Lever effectué, déambulation
  - Ablation perfusion
  - Passage per os:
    * DAFALGAN 1g x4/j
  - Bilan biologique:
    * NFS: normale
    * CRP: 45 mg/L (attendu post-op)

Jour J+2 (Sortie):
  - Examen clinique: cicatrices propres
  - Pas de fièvre, douleur minime
  - Transit repris
  - Prescription sortie:
    * DAFALGAN 1g x3/j si besoin x 7j
  - Documents:
    * Ordonnance
    * CR opératoire
    * CR hospitalisation
    * Consignes post-op
    * Arrêt travail 14 jours
    * RDV consultation post-op J+15
  - Sortie domicile (11:00)
```

## 4. Résultats de Laboratoire Synthétiques

### 4.1 Panels Biologiques Standards

#### Numération Formule Sanguine (NFS)

```json
{
  "panel_code": "57021-8",
  "panel_display": "Numération Formule Sanguine",
  "effective_date": "2025-01-05T08:30:00Z",
  "status": "FINAL",
  "tests": [
    {
      "code": "718-7",
      "display": "Hémoglobine",
      "value": 14.2,
      "unit": "g/dL",
      "reference_low": 13.0,
      "reference_high": 17.0,
      "interpretation": "NORMAL"
    },
    {
      "code": "4544-3",
      "display": "Hématocrite",
      "value": 42.5,
      "unit": "%",
      "reference_low": 40.0,
      "reference_high": 50.0,
      "interpretation": "NORMAL"
    },
    {
      "code": "789-8",
      "display": "Globules rouges",
      "value": 4.8,
      "unit": "10*6/µL",
      "reference_low": 4.5,
      "reference_high": 5.9,
      "interpretation": "NORMAL"
    },
    {
      "code": "6690-2",
      "display": "Leucocytes",
      "value": 7.2,
      "unit": "10*3/µL",
      "reference_low": 4.0,
      "reference_high": 10.0,
      "interpretation": "NORMAL"
    },
    {
      "code": "777-3",
      "display": "Plaquettes",
      "value": 225,
      "unit": "10*3/µL",
      "reference_low": 150,
      "reference_high": 400,
      "interpretation": "NORMAL"
    }
  ]
}
```

#### Bilan Métabolique

```json
{
  "panel_code": "51990-0",
  "panel_display": "Bilan métabolique de base",
  "effective_date": "2025-01-05T08:30:00Z",
  "status": "FINAL",
  "tests": [
    {
      "code": "2339-0",
      "display": "Glycémie",
      "value": 1.35,
      "unit": "g/L",
      "reference_low": 0.70,
      "reference_high": 1.10,
      "interpretation": "HIGH"
    },
    {
      "code": "2951-2",
      "display": "Sodium",
      "value": 140,
      "unit": "mmol/L",
      "reference_low": 135,
      "reference_high": 145,
      "interpretation": "NORMAL"
    },
    {
      "code": "2823-3",
      "display": "Potassium",
      "value": 4.2,
      "unit": "mmol/L",
      "reference_low": 3.5,
      "reference_high": 5.0,
      "interpretation": "NORMAL"
    },
    {
      "code": "2075-0",
      "display": "Chlorure",
      "value": 102,
      "unit": "mmol/L",
      "reference_low": 98,
      "reference_high": 107,
      "interpretation": "NORMAL"
    },
    {
      "code": "2160-0",
      "display": "Créatinine",
      "value": 95,
      "unit": "µmol/L",
      "reference_low": 60,
      "reference_high": 110,
      "interpretation": "NORMAL"
    },
    {
      "code": "33914-3",
      "display": "DFG (MDRD)",
      "value": 78,
      "unit": "mL/min/1.73m2",
      "reference_low": 90,
      "reference_high": null,
      "interpretation": "LOW"
    }
  ]
}
```

#### Bilan Lipidique

```json
{
  "panel_code": "57698-3",
  "panel_display": "Bilan lipidique",
  "effective_date": "2025-01-05T08:30:00Z",
  "status": "FINAL",
  "tests": [
    {
      "code": "2093-3",
      "display": "Cholestérol total",
      "value": 2.35,
      "unit": "g/L",
      "reference_low": null,
      "reference_high": 2.00,
      "interpretation": "HIGH"
    },
    {
      "code": "2089-1",
      "display": "LDL cholestérol",
      "value": 1.45,
      "unit": "g/L",
      "reference_low": null,
      "reference_high": 1.30,
      "interpretation": "HIGH"
    },
    {
      "code": "2085-9",
      "display": "HDL cholestérol",
      "value": 0.52,
      "unit": "g/L",
      "reference_low": 0.40,
      "reference_high": null,
      "interpretation": "NORMAL"
    },
    {
      "code": "2571-8",
      "display": "Triglycérides",
      "value": 1.85,
      "unit": "g/L",
      "reference_low": null,
      "reference_high": 1.50,
      "interpretation": "HIGH"
    }
  ]
}
```

### 4.2 Résultats Critiques (Alertes)

#### Hyperkaliémie Sévère

```json
{
  "test_code": "2823-3",
  "test_display": "Potassium",
  "value": 6.8,
  "unit": "mmol/L",
  "reference_low": 3.5,
  "reference_high": 5.0,
  "interpretation": "CRITICAL_HIGH",
  "alert_level": "CRITICAL",
  "alert_message": "HYPERKALIÉMIE SÉVÈRE - ALERTE CRITIQUE",
  "clinical_significance": "Risque d'arythmie cardiaque potentiellement fatale",
  "recommended_action": "Contrôle immédiat + ECG + traitement hyperkaliémiant urgent",
  "effective_date": "2025-01-10T16:45:00Z",
  "notified_practitioners": [
    "medecin-uuid-1",
    "ide-uuid-1"
  ],
  "notification_timestamp": "2025-01-10T16:46:12Z"
}
```

## 5. Scripts de Génération

### 5.1 Script Python - Génération Patients

```python
#!/usr/bin/env python3
"""
Générateur de patients synthétiques pour DMI KeneyApp
"""
import random
import uuid
from datetime import datetime, timedelta
from typing import List, Dict

# Listes de noms/prénoms fictifs
NOMS = ["MARTIN", "BERNARD", "DUBOIS", "THOMAS", "ROBERT", "PETIT", "DURAND",
        "LEROY", "MOREAU", "SIMON", "LAURENT", "LEFEBVRE", "MICHEL", "GARCIA"]

PRENOMS_M = ["Jean", "Pierre", "Michel", "André", "Philippe", "Alain", "François",
             "Jacques", "Daniel", "Patrick", "Nicolas", "Christophe"]

PRENOMS_F = ["Marie", "Nathalie", "Isabelle", "Sylvie", "Catherine", "Françoise",
             "Sophie", "Martine", "Christine", "Monique", "Sandrine", "Valérie"]

def generate_ins(sexe: str, date_naissance: datetime) -> str:
    """
    Génère un INS synthétique (NON VALIDE - clé incorrecte)
    Format: 1AAMMJJDDDCCCKK
    """
    sexe_code = "1" if sexe == "M" else "2"
    annee = date_naissance.strftime("%y")
    mois = date_naissance.strftime("%m")
    jour = date_naissance.strftime("%d")
    dept = random.randint(1, 95)  # Département
    commune = random.randint(1, 999)  # Commune
    ordre = random.randint(1, 999)  # Ordre

    # Clé INCORRECTE volontairement (sécurité)
    cle_invalide = "99"

    ins = f"{sexe_code}{annee}{mois}{jour}{dept:02d}{commune:03d}{ordre:03d}{cle_invalide}"
    return ins

def generate_ipp() -> str:
    """Génère un IPP avec clé Luhn"""
    base = random.randint(10000000, 99999999)
    # Calcul clé Luhn simplifié
    cle = (10 - (sum(int(d) * (2 if i % 2 else 1) for i, d in enumerate(str(base))) % 10)) % 10
    return f"{base}{cle}"

def generate_patient() -> Dict:
    """Génère un patient synthétique"""
    patient_id = str(uuid.uuid4())
    sexe = random.choice(["M", "F"])

    # Date naissance aléatoire (0-90 ans)
    age_days = random.randint(0, 90 * 365)
    date_naissance = datetime.now() - timedelta(days=age_days)

    nom = random.choice(NOMS)
    prenom = random.choice(PRENOMS_M if sexe == "M" else PRENOMS_F)

    patient = {
        "id": patient_id,
        "ipp": generate_ipp(),
        "ins": generate_ins(sexe, date_naissance),
        "ins_status": random.choice(["VALIDATED"] * 9 + ["PROVISOIRE"]),
        "nom": nom,
        "prenom": prenom,
        "date_naissance": date_naissance.strftime("%Y-%m-%d"),
        "sexe": sexe,
        "adresse": f"{random.randint(1,999)} {random.choice(['Rue', 'Avenue', 'Boulevard'])} {random.choice(['de la Paix', 'Victor Hugo', 'des Fleurs'])}, {random.randint(10000, 99999)} {random.choice(['Paris', 'Lyon', 'Marseille', 'Toulouse'])}",
        "telephone": f"+336{random.randint(10000000, 99999999)}",
        "email": f"{prenom.lower()}.{nom.lower()}.synthetic@keneyapp.test",
        "status": "ACTIVE",
        "tenant_id": "default-tenant",
        "created_at": datetime.now().isoformat() + "Z"
    }

    return patient

def generate_patients(count: int = 100) -> List[Dict]:
    """Génère N patients synthétiques"""
    return [generate_patient() for _ in range(count)]

if __name__ == "__main__":
    # Génération 100 patients
    patients = generate_patients(100)

    # Export JSON
    import json
    with open("synthetic_patients.json", "w", encoding="utf-8") as f:
        json.dump(patients, f, ensure_ascii=False, indent=2)

    print(f"✅ {len(patients)} patients synthétiques générés → synthetic_patients.json")
```

### 5.2 Script SQL - Insertion Données

```sql
-- Script d'insertion de données synthétiques
-- À exécuter sur environnement de dev/test UNIQUEMENT

-- Insertion patients
INSERT INTO patients (id, ipp, ins, ins_status, nom, prenom, date_naissance, sexe, adresse, telephone, email, status, tenant_id, created_at, updated_at)
VALUES
  ('550e8400-e29b-41d4-a716-446655440000', '100000018', '299120175012399', 'PROVISOIRE', 'DUBOIS', 'François', '1965-03-12', 'M', '42 Avenue de la République, 75011 Paris', '+33612000001', 'francois.dubois.synthetic@keneyapp.test', 'ACTIVE', 'default-tenant', NOW(), NOW()),
  ('550e8400-e29b-41d4-a716-446655440001', '100000026', '185061275034512', 'PROVISOIRE', 'LEROUX', 'Sophie', '1992-06-25', 'F', '28 Rue des Lilas, 69001 Lyon', '+33698000002', 'sophie.leroux.synthetic@keneyapp.test', 'ACTIVE', 'default-tenant', NOW(), NOW());

-- Insertion allergies
INSERT INTO patient_allergies (id, patient_id, allergen_code, allergen_display, severity, reaction_type, verification_status, onset_date, recorded_date, recorded_by)
VALUES
  (gen_random_uuid(), '550e8400-e29b-41d4-a716-446655440000', '387207008', 'Pénicilline', 'HIGH', 'ALLERGY', 'CONFIRMED', '1985-07-20', NOW(), 'system');

-- Insertion conditions (pathologies)
INSERT INTO conditions (id, patient_id, code, code_system, display, verification_status, onset_date, severity, tenant_id, created_at)
VALUES
  (gen_random_uuid(), '550e8400-e29b-41d4-a716-446655440000', 'E11', 'ICD-10', 'Diabète sucré de type 2', 'CONFIRMED', '2015-06-15', 'MODERATE', 'default-tenant', NOW()),
  (gen_random_uuid(), '550e8400-e29b-41d4-a716-446655440000', 'I10', 'ICD-10', 'Hypertension artérielle essentielle', 'CONFIRMED', '2018-02-10', 'MODERATE', 'default-tenant', NOW());

-- Insertion prescriptions
INSERT INTO medication_requests (id, patient_id, medication_code, medication_display, atc_code, dosage_text, status, authored_on, prescriber_id, tenant_id)
VALUES
  (gen_random_uuid(), '550e8400-e29b-41d4-a716-446655440000', '3400893432051', 'METFORMINE 1000mg cp', 'A10BA02', '1 comprimé 2 fois par jour', 'ACTIVE', '2015-06-15', 'medecin-uuid', 'default-tenant'),
  (gen_random_uuid(), '550e8400-e29b-41d4-a716-446655440000', '3400937265058', 'RAMIPRIL 5mg cp', 'C09AA05', '1 comprimé 1 fois par jour le matin', 'ACTIVE', '2018-02-10', 'medecin-uuid', 'default-tenant');

-- Insertion observations (constantes)
INSERT INTO observations (id, patient_id, code, code_display, value_quantity, unit, reference_range_low, reference_range_high, interpretation, status, effective_datetime, performer_id, tenant_id)
VALUES
  (gen_random_uuid(), '550e8400-e29b-41d4-a716-446655440000', '2339-0', 'Glycémie à jeun', 1.35, 'g/L', 0.7, 1.1, 'HIGH', 'FINAL', '2025-01-05 08:30:00', 'labo-uuid', 'default-tenant'),
  (gen_random_uuid(), '550e8400-e29b-41d4-a716-446655440000', '4548-4', 'HbA1c', 7.2, '%', 4.0, 6.0, 'HIGH', 'FINAL', '2025-01-05 08:30:00', 'labo-uuid', 'default-tenant');
```

---

**Document validé par** : Data Engineer, Tech Lead
**Date** : 2025-01-10
**Version** : 1.0
**Prochaine revue** : 2025-02-10
