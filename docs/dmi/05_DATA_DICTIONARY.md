# Dictionnaire de Données et Règles Qualité - DMI

## 1. Domaine Patient (Identity Management)

### 1.1 Entité : Patient

| Champ | Type | Longueur | Obligatoire | Terminologie | Règle Qualité | Exemple |
|-------|------|----------|-------------|--------------|---------------|---------|
| **id** | UUID | 36 | Oui | - | UUID v4 valide | `550e8400-e29b-41d4-a716-446655440000` |
| **ipp** | String | 9 | Oui | - | Unique, numérique, clé Luhn | `123456780` |
| **ins** | String | 15 | Oui* | - | Format INS valide, clé contrôle | `1 84 12 75 123 456 78` |
| **ins_status** | Enum | - | Oui | `VALIDATED`, `PROVISOIRE`, `UNKNOWN` | - | `VALIDATED` |
| **nom** | String | 50 | Oui | - | Majuscules, sans accents | `MARTIN` |
| **nom_naissance** | String | 50 | Non | - | Majuscules, sans accents | `DUPONT` |
| **prenom** | String | 50 | Oui | - | Première lettre majuscule | `Jean` |
| **date_naissance** | Date | - | Oui | - | ≤ aujourd'hui, format ISO 8601 | `1984-12-07` |
| **sexe** | Enum | - | Oui | `M`, `F`, `I` (Indéterminé), `U` (Inconnu) | - | `M` |
| **adresse** | String | 200 | Non | - | Chiffré au repos | `12 rue de la Paix, 75001 Paris` |
| **telephone** | String | 15 | Non | - | Format E.164, chiffré | `+33612345678` |
| **email** | String | 100 | Non | - | Format email valide, chiffré | `jean.martin@example.com` |
| **status** | Enum | - | Oui | `ACTIVE`, `INACTIVE`, `DECEASED` | - | `ACTIVE` |
| **tenant_id** | UUID | 36 | Oui | - | Référence tenant valide | `tenant-uuid` |
| **created_at** | Timestamp | - | Oui | - | Horodatage UTC | `2025-01-10T14:30:00Z` |
| **updated_at** | Timestamp | - | Oui | - | Horodatage UTC | `2025-01-10T15:45:00Z` |
| **created_by** | UUID | 36 | Oui | - | Référence utilisateur | `user-uuid` |

**Règles Métier** :
- INS obligatoire sauf urgence (statut PROVISOIRE autorisé max 48h)
- Détection doublons : Levenshtein(nom+prénom) < 2 ET date_naissance = → score > 85%
- Chiffrement : nom, prenom, date_naissance, adresse, telephone, email
- Soft delete uniquement (flag status=INACTIVE)
- Historique modifications tracé (audit log)

### 1.2 Entité : PatientAllergy

| Champ | Type | Longueur | Obligatoire | Terminologie | Règle Qualité | Exemple |
|-------|------|----------|-------------|--------------|---------------|---------|
| **id** | UUID | 36 | Oui | - | UUID v4 valide | `uuid` |
| **patient_id** | UUID | 36 | Oui | - | Référence Patient valide | `patient-uuid` |
| **allergen_code** | String | 20 | Oui | SNOMED CT | Code SNOMED CT valide | `387207008` |
| **allergen_display** | String | 100 | Oui | - | Libellé associé au code | `Pénicilline` |
| **severity** | Enum | - | Oui | `LOW`, `MODERATE`, `HIGH`, `LIFE_THREATENING` | - | `HIGH` |
| **reaction_type** | Enum | - | Oui | `ALLERGY`, `INTOLERANCE` | - | `ALLERGY` |
| **verification_status** | Enum | - | Oui | `UNCONFIRMED`, `CONFIRMED`, `REFUTED` | - | `CONFIRMED` |
| **onset_date** | Date | - | Non | - | ≤ aujourd'hui | `2020-03-15` |
| **notes** | Text | 500 | Non | - | Texte libre | `Réaction cutanée sévère` |
| **recorded_date** | Timestamp | - | Oui | - | Horodatage UTC | `2025-01-10T14:30:00Z` |
| **recorded_by** | UUID | 36 | Oui | - | Référence utilisateur | `user-uuid` |

**Règles Métier** :
- Code SNOMED CT obligatoire (recherche dans référentiel)
- Allergie `LIFE_THREATENING` → alerte bloquante si prescription
- Vérification croisée avec prescriptions existantes
- Historique modifications tracé

## 2. Domaine Consultation (Encounters & Observations)

### 2.1 Entité : Encounter

| Champ | Type | Longueur | Obligatoire | Terminologie | Règle Qualité | Exemple |
|-------|------|----------|-------------|--------------|---------------|---------|
| **id** | UUID | 36 | Oui | - | UUID v4 valide | `uuid` |
| **patient_id** | UUID | 36 | Oui | - | Référence Patient valide | `patient-uuid` |
| **type** | Enum | - | Oui | `AMBULATORY`, `EMERGENCY`, `INPATIENT`, `OUTPATIENT` | - | `AMBULATORY` |
| **status** | Enum | - | Oui | `PLANNED`, `IN_PROGRESS`, `FINISHED`, `CANCELLED` | - | `IN_PROGRESS` |
| **class** | String | 10 | Oui | HL7 v3 ActCode | Code valide | `AMB` |
| **period_start** | Timestamp | - | Oui | - | ≤ aujourd'hui | `2025-01-10T09:00:00Z` |
| **period_end** | Timestamp | - | Non | - | ≥ period_start | `2025-01-10T09:45:00Z` |
| **reason_code** | String | 20 | Non | CIM-10 ou SNOMED CT | Code valide | `R05` (toux) |
| **reason_display** | String | 200 | Non | - | Libellé associé | `Toux persistante` |
| **chief_complaint** | Text | 1000 | Non | - | Texte libre | `Patient se plaint de...` |
| **practitioner_id** | UUID | 36 | Oui | - | Référence utilisateur médecin | `medecin-uuid` |
| **service_id** | UUID | 36 | Non | - | Référence service | `service-uuid` |
| **location_id** | UUID | 36 | Non | - | Référence salle/lieu | `location-uuid` |
| **tenant_id** | UUID | 36 | Oui | - | Référence tenant | `tenant-uuid` |

**Règles Métier** :
- period_end obligatoire si status = FINISHED
- Durée consultation : 5 min ≤ durée ≤ 2h (alerte si hors plage)
- Médecin référent obligatoire
- Une consultation IN_PROGRESS max par patient simultanément

### 2.2 Entité : Observation (Constantes & Résultats)

| Champ | Type | Longueur | Obligatoire | Terminologie | Règle Qualité | Exemple |
|-------|------|----------|-------------|--------------|---------------|---------|
| **id** | UUID | 36 | Oui | - | UUID v4 valide | `uuid` |
| **patient_id** | UUID | 36 | Oui | - | Référence Patient | `patient-uuid` |
| **encounter_id** | UUID | 36 | Non | - | Référence Encounter | `encounter-uuid` |
| **code** | String | 20 | Oui | LOINC | Code LOINC valide | `8310-5` |
| **code_display** | String | 100 | Oui | - | Libellé LOINC | `Température corporelle` |
| **value_quantity** | Decimal | 10,3 | Oui* | - | Valeur numérique | `37.5` |
| **value_string** | String | 100 | Oui* | - | Valeur textuelle (si qualitatif) | `Positif` |
| **unit** | String | 20 | Oui | UCUM | Unité UCUM valide | `Cel` (Celsius) |
| **reference_range_low** | Decimal | 10,3 | Non | - | Borne inférieure normale | `36.0` |
| **reference_range_high** | Decimal | 10,3 | Non | - | Borne supérieure normale | `38.0` |
| **interpretation** | Enum | - | Non | `NORMAL`, `LOW`, `HIGH`, `CRITICAL_LOW`, `CRITICAL_HIGH` | - | `NORMAL` |
| **status** | Enum | - | Oui | `REGISTERED`, `PRELIMINARY`, `FINAL`, `AMENDED`, `CANCELLED` | - | `FINAL` |
| **effective_datetime** | Timestamp | - | Oui | - | ≤ aujourd'hui | `2025-01-10T09:30:00Z` |
| **performer_id** | UUID | 36 | Oui | - | Référence utilisateur (IDE/médecin) | `user-uuid` |
| **method** | String | 50 | Non | SNOMED CT | Méthode de mesure | `Mesure automatique` |
| **device_id** | UUID | 36 | Non | - | Référence device (si automatique) | `device-uuid` |

**Règles Métier** :
- Code LOINC obligatoire (rejet si absent)
- Unité UCUM obligatoire (rejet si absent)
- value_quantity OU value_string (au moins 1)
- Plage de valeurs plausibles par code LOINC (alerte si aberrant)
- Valeur critique → notification immédiate médecin
- Modification possible uniquement dans les 24h par créateur

**Plages de Valeurs (exemples)** :

| Code LOINC | Observation | Plage Normale | Plage Max Acceptable | Alerte |
|------------|-------------|---------------|----------------------|--------|
| `8310-5` | Température | 36.0-38.0 °C | 30.0-45.0 °C | < 35 ou > 39 |
| `8867-4` | Fréquence cardiaque | 60-100 bpm | 30-220 bpm | < 50 ou > 120 |
| `85354-9` | TA systolique | 90-140 mmHg | 50-250 mmHg | < 90 ou > 140 |
| `2339-0` | Glycémie | 0.7-1.1 g/L | 0.2-5.0 g/L | < 0.6 ou > 2.0 |
| `2951-2` | Sodium | 135-145 mmol/L | 100-180 mmol/L | < 130 ou > 150 |

## 3. Domaine Prescription (Medications)

### 3.1 Entité : MedicationRequest

| Champ | Type | Longueur | Obligatoire | Terminologie | Règle Qualité | Exemple |
|-------|------|----------|-------------|--------------|---------------|---------|
| **id** | UUID | 36 | Oui | - | UUID v4 valide | `uuid` |
| **patient_id** | UUID | 36 | Oui | - | Référence Patient | `patient-uuid` |
| **encounter_id** | UUID | 36 | Non | - | Référence Encounter | `encounter-uuid` |
| **medication_code** | String | 20 | Oui | CIP/UCD | Code CIP ou UCD valide | `3400936404649` |
| **medication_display** | String | 200 | Oui | - | Nom commercial + dosage | `DOLIPRANE 1000mg cp` |
| **atc_code** | String | 7 | Non | ATC | Code ATC niveau 5 | `N02BE01` |
| **dosage_text** | String | 200 | Oui | - | Instructions textuelles | `1 comprimé 3 fois par jour` |
| **dosage_dose_quantity** | Decimal | 10,2 | Oui | - | Dose par prise | `1.0` |
| **dosage_dose_unit** | String | 20 | Oui | UCUM | Unité de dose | `{tablet}` |
| **dosage_frequency** | String | 20 | Oui | - | Fréquence structurée | `3x/day` |
| **dosage_route** | Enum | - | Oui | SNOMED CT | Voie administration | `PO` (per os) |
| **duration_value** | Integer | - | Oui | - | Durée traitement | `5` |
| **duration_unit** | Enum | - | Oui | `days`, `weeks`, `months` | Unité durée | `days` |
| **status** | Enum | - | Oui | `DRAFT`, `ACTIVE`, `ON_HOLD`, `CANCELLED`, `COMPLETED` | - | `ACTIVE` |
| **intent** | Enum | - | Oui | `PROPOSAL`, `PLAN`, `ORDER`, `REFLEX_ORDER` | - | `ORDER` |
| **priority** | Enum | - | Oui | `ROUTINE`, `URGENT`, `STAT` | - | `ROUTINE` |
| **authored_on** | Timestamp | - | Oui | - | ≤ aujourd'hui | `2025-01-10T10:00:00Z` |
| **prescriber_id** | UUID | 36 | Oui | - | Référence médecin | `medecin-uuid` |
| **pharmacy_validation_status** | Enum | - | Oui | `PENDING`, `VALIDATED`, `ADAPTED`, `REFUSED` | - | `PENDING` |
| **pharmacy_validation_date** | Timestamp | - | Non | - | Si validé/refusé | `2025-01-10T11:00:00Z` |
| **pharmacist_id** | UUID | 36 | Non | - | Référence pharmacien | `pharmacien-uuid` |
| **pharmacy_notes** | Text | 500 | Non | - | Commentaires pharmacien | `Adaptation posologie...` |

**Règles Métier** :
- Code CIP/UCD obligatoire (validation base médicamenteuse)
- Analyse interactions automatique avant enregistrement
- Vérification allergie patient (bloquante si allergie connue)
- Validation pharmaceutique obligatoire en milieu hospitalier
- Posologie : adaptation automatique si clairance rénale < 60 ml/min
- Modification autorisée uniquement par prescripteur (< 24h) ou pharmacien (adaptation)

### 3.2 Entité : MedicationAdministration

| Champ | Type | Longueur | Obligatoire | Terminologie | Règle Qualité | Exemple |
|-------|------|----------|-------------|--------------|---------------|---------|
| **id** | UUID | 36 | Oui | - | UUID v4 valide | `uuid` |
| **medication_request_id** | UUID | 36 | Oui | - | Référence MedicationRequest | `prescription-uuid` |
| **patient_id** | UUID | 36 | Oui | - | Référence Patient | `patient-uuid` |
| **status** | Enum | - | Oui | `IN_PROGRESS`, `COMPLETED`, `NOT_DONE`, `ON_HOLD` | - | `COMPLETED` |
| **status_reason** | Text | 200 | Non | - | Si NOT_DONE, raison obligatoire | `Patient refuse` |
| **effective_datetime** | Timestamp | - | Oui | - | Heure réelle administration | `2025-01-10T14:00:00Z` |
| **performer_id** | UUID | 36 | Oui | - | Référence IDE | `ide-uuid` |
| **dose_administered** | Decimal | 10,2 | Oui | - | Dose réellement administrée | `1.0` |
| **dose_unit** | String | 20 | Oui | UCUM | Unité | `{tablet}` |
| **route** | Enum | - | Oui | SNOMED CT | Voie réelle administration | `PO` |
| **site** | String | 50 | Non | SNOMED CT | Site anatomique (si injectable) | `Bras gauche` |
| **device_id** | UUID | 36 | Non | - | Device (pompe, pousse-seringue...) | `device-uuid` |
| **note** | Text | 500 | Non | - | Commentaires | `Bien toléré` |

**Règles Métier** :
- Administration tracée individuellement (chaque prise)
- Scan code-barre patient + médicament obligatoire (si équipé)
- Écart > 30 min vs horaire prévu → alerte + justification
- NOT_DONE → raison obligatoire + notification médecin

## 4. Domaine Laboratoire (Lab Orders & Results)

### 4.1 Entité : ServiceRequest (Lab Order)

| Champ | Type | Longueur | Obligatoire | Terminologie | Règle Qualité | Exemple |
|-------|------|----------|-------------|--------------|---------------|---------|
| **id** | UUID | 36 | Oui | - | UUID v4 valide | `uuid` |
| **patient_id** | UUID | 36 | Oui | - | Référence Patient | `patient-uuid` |
| **encounter_id** | UUID | 36 | Non | - | Référence Encounter | `encounter-uuid` |
| **code** | String | 20 | Oui | LOINC | Code LOINC panel ou test | `57021-8` (NFS) |
| **code_display** | String | 100 | Oui | - | Libellé | `Numération Formule Sanguine` |
| **category** | Enum | - | Oui | `LABORATORY`, `IMAGING`, `PROCEDURE` | - | `LABORATORY` |
| **status** | Enum | - | Oui | `DRAFT`, `ACTIVE`, `COMPLETED`, `CANCELLED` | - | `ACTIVE` |
| **intent** | Enum | - | Oui | `PROPOSAL`, `PLAN`, `ORDER` | - | `ORDER` |
| **priority** | Enum | - | Oui | `ROUTINE`, `URGENT`, `STAT` | - | `ROUTINE` |
| **authored_on** | Timestamp | - | Oui | - | Date/heure prescription | `2025-01-10T09:00:00Z` |
| **requester_id** | UUID | 36 | Oui | - | Référence médecin | `medecin-uuid` |
| **clinical_info** | Text | 1000 | Non | - | Renseignements cliniques | `Suspicion anémie` |
| **specimen_type** | Enum | - | Non | SNOMED CT | Type prélèvement | `Blood` |
| **specimen_collected_date** | Timestamp | - | Non | - | Date/heure prélèvement | `2025-01-10T09:30:00Z` |
| **performer_organization** | String | 100 | Non | - | Laboratoire destinataire | `Lab Central CHU` |
| **hl7_message_id** | String | 50 | Non | - | ID message HL7 ORM envoyé | `HL7-12345` |

**Règles Métier** :
- Code LOINC obligatoire (panel ou test individuel)
- Renseignements cliniques recommandés (améliore interprétation)
- Priority STAT → traitement prioritaire labo (< 1h)
- Envoi message HL7 v2 ORM au LIS automatique
- Traçabilité prélèvement (IDE, date/heure)

## 5. Domaine Documents

### 5.1 Entité : DocumentReference

| Champ | Type | Longueur | Obligatoire | Terminologie | Règle Qualité | Exemple |
|-------|------|----------|-------------|--------------|---------------|---------|
| **id** | UUID | 36 | Oui | - | UUID v4 valide | `uuid` |
| **patient_id** | UUID | 36 | Oui | - | Référence Patient | `patient-uuid` |
| **encounter_id** | UUID | 36 | Non | - | Référence Encounter | `encounter-uuid` |
| **type** | String | 20 | Oui | LOINC (si dispo) ou custom | Code type document | `11488-4` (CR consultation) |
| **type_display** | String | 100 | Oui | - | Libellé type | `Compte-rendu consultation` |
| **category** | Enum | - | Oui | `CLINICAL_NOTE`, `LAB_REPORT`, `IMAGING_REPORT`, `PRESCRIPTION`, `ADMINISTRATIVE` | - | `CLINICAL_NOTE` |
| **status** | Enum | - | Oui | `CURRENT`, `SUPERSEDED`, `ENTERED_IN_ERROR` | - | `CURRENT` |
| **date** | Timestamp | - | Oui | - | Date création document | `2025-01-10T10:00:00Z` |
| **author_id** | UUID | 36 | Oui | - | Référence utilisateur | `user-uuid` |
| **description** | Text | 500 | Non | - | Description document | `CR consultation cardiologie` |
| **content_type** | String | 50 | Oui | MIME type | Type fichier | `application/pdf` |
| **content_size** | Integer | - | Oui | - | Taille en octets | `102400` |
| **content_hash** | String | 64 | Oui | SHA-256 | Hash intégrité | `sha256-hash` |
| **content_url** | String | 500 | Oui | - | URL stockage objet (S3) | `s3://bucket/doc-uuid.pdf` |
| **signed** | Boolean | - | Oui | - | Document signé électroniquement | `true` |
| **signature_date** | Timestamp | - | Non | - | Date signature | `2025-01-10T10:05:00Z` |
| **signature_certificate** | Text | 5000 | Non | - | Certificat électronique | `-----BEGIN CERTIFICATE-----` |

**Règles Métier** :
- Hash SHA-256 obligatoire (intégrité)
- Documents médicaux : signature électronique obligatoire
- MIME types autorisés : PDF, JPEG, PNG, DICOM
- Taille max : 20 Mo par document
- Stockage chiffré (S3 SSE-KMS)
- Rétention : 20 ans minimum (légal)

## 6. Règles de Qualité Transversales

### 6.1 Règles Générales

#### RQ-GEN-001 : Horodatage Fiable
```
Tous les timestamps DOIVENT :
- Être en UTC (timezone explicite)
- Avoir précision à la seconde minimum
- Provenir d'une source NTP synchronisée
- Être immuables après création
```

#### RQ-GEN-002 : Identifiants Uniques
```
Tous les identifiants (id, ipp, ins) DOIVENT :
- Être générés côté serveur
- Être uniques au sein du tenant (ou global si spécifié)
- Ne jamais être réutilisés (même après suppression)
```

#### RQ-GEN-003 : Soft Delete
```
Suppression logique uniquement :
- Flag deleted_at (timestamp)
- Ou status = INACTIVE/DELETED
- Données conservées pour audit
- Accès restreint (admin + audit)
```

#### RQ-GEN-004 : Traçabilité
```
Pour toute modification critique :
- Qui (user_id)
- Quand (timestamp précis)
- Quoi (champs modifiés, before/after)
- Pourquoi (commentaire si applicable)
- Enregistré dans audit_log
```

### 6.2 Règles de Cohérence

#### RQ-COH-001 : Dates Logiques
```sql
-- Exemple : Date naissance ≤ date consultation
CHECK (patient.date_naissance <= encounter.period_start)

-- Date prescription ≤ date validation pharmacien
CHECK (medication_request.authored_on <= medication_request.pharmacy_validation_date)

-- Durée consultation plausible (5 min ≤ durée ≤ 2h)
CHECK (
  EXTRACT(EPOCH FROM (encounter.period_end - encounter.period_start)) / 60 
  BETWEEN 5 AND 120
)
```

#### RQ-COH-002 : Références Intégrité
```sql
-- Toutes les références FK doivent exister
FOREIGN KEY (patient_id) REFERENCES patients(id)
FOREIGN KEY (encounter_id) REFERENCES encounters(id)
FOREIGN KEY (user_id) REFERENCES users(id)

-- Cascade sur tenant_id (isolation multi-tenant)
FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE
```

#### RQ-COH-003 : Valeurs Énumérées
```
Utiliser des ENUM ou tables de référence :
- Statuts (DRAFT, ACTIVE, COMPLETED, CANCELLED)
- Priorités (ROUTINE, URGENT, STAT)
- Rôles utilisateurs (MEDECIN, IDE, PHARMACIEN...)
- Validation côté serveur (rejet valeurs invalides)
```

### 6.3 Règles de Complétude

#### RQ-COMP-001 : Complétude Minimale Patient
```
À la création, un patient DOIT avoir :
- Nom, prénom, date naissance, sexe
- INS (ou statut PROVISOIRE avec régularisation < 48h)
- Au moins 1 moyen de contact (téléphone OU email OU adresse)
```

#### RQ-COMP-002 : Complétude Prescription
```
Une prescription DOIT avoir :
- Médicament (code CIP/UCD)
- Posologie complète (dose, fréquence, durée, voie)
- Prescripteur (RPPS)
- Date prescription
- Statut initial = DRAFT ou ACTIVE
```

#### RQ-COMP-003 : Complétude Observation
```
Une observation DOIT avoir :
- Code terminologie (LOINC/SNOMED CT)
- Valeur (quantity OU string)
- Unité UCUM (si quantitatif)
- Date/heure effective
- Opérateur (qui a mesuré/saisi)
```

## 7. Mapping FHIR R4

### 7.1 Correspondance Entités → Ressources FHIR

| Entité DB | Ressource FHIR | Profil FR | Notes |
|-----------|----------------|-----------|-------|
| Patient | Patient | [FrPatient](http://interop.esante.gouv.fr/ig/fhir/StructureDefinition-fr-patient.html) | INS obligatoire |
| PatientAllergy | AllergyIntolerance | - | Code SNOMED CT |
| Encounter | Encounter | - | Type: ambulatory, inpatient... |
| Observation | Observation | [FrObservation](http://interop.esante.gouv.fr/ig/fhir/StructureDefinition-fr-observation.html) | Code LOINC |
| MedicationRequest | MedicationRequest | [FrMedicationRequest](http://interop.esante.gouv.fr/ig/fhir/StructureDefinition-fr-medication-request.html) | Code CIP/UCD |
| MedicationAdministration | MedicationAdministration | - | Traçabilité IDE |
| ServiceRequest | ServiceRequest | - | Lab orders, imaging orders |
| DocumentReference | DocumentReference | [FrDocumentReference](http://interop.esante.gouv.fr/ig/fhir/StructureDefinition-fr-document-reference.html) | PDF, DICOM... |

### 7.2 Extensions FHIR Spécifiques France

```json
{
  "resourceType": "Patient",
  "extension": [
    {
      "url": "http://interopsante.org/fhir/StructureDefinition/FrPatientINSNIR",
      "valueIdentifier": {
        "system": "urn:oid:1.2.250.1.213.1.4.8",
        "value": "184127512345678"
      }
    },
    {
      "url": "http://interopsante.org/fhir/StructureDefinition/FrPatientBirthPlace",
      "valueAddress": {
        "city": "Paris",
        "postalCode": "75015",
        "country": "FRA"
      }
    }
  ]
}
```

## 8. Exemples de Données Valides

### 8.1 Patient Complet

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "ipp": "123456780",
  "ins": "184127512345678",
  "ins_status": "VALIDATED",
  "nom": "MARTIN",
  "prenom": "Jean",
  "date_naissance": "1984-12-07",
  "sexe": "M",
  "adresse": "12 rue de la Paix, 75001 Paris",
  "telephone": "+33612345678",
  "email": "jean.martin@example.com",
  "status": "ACTIVE",
  "tenant_id": "tenant-uuid",
  "created_at": "2025-01-10T14:30:00Z",
  "updated_at": "2025-01-10T14:30:00Z",
  "created_by": "user-uuid"
}
```

### 8.2 Observation (Température)

```json
{
  "id": "obs-uuid",
  "patient_id": "patient-uuid",
  "encounter_id": "encounter-uuid",
  "code": "8310-5",
  "code_display": "Température corporelle",
  "value_quantity": 37.5,
  "unit": "Cel",
  "reference_range_low": 36.0,
  "reference_range_high": 38.0,
  "interpretation": "NORMAL",
  "status": "FINAL",
  "effective_datetime": "2025-01-10T09:30:00Z",
  "performer_id": "ide-uuid"
}
```

### 8.3 Prescription

```json
{
  "id": "prescription-uuid",
  "patient_id": "patient-uuid",
  "encounter_id": "encounter-uuid",
  "medication_code": "3400936404649",
  "medication_display": "DOLIPRANE 1000mg comprimé",
  "atc_code": "N02BE01",
  "dosage_text": "1 comprimé 3 fois par jour pendant 5 jours",
  "dosage_dose_quantity": 1.0,
  "dosage_dose_unit": "{tablet}",
  "dosage_frequency": "3x/day",
  "dosage_route": "PO",
  "duration_value": 5,
  "duration_unit": "days",
  "status": "ACTIVE",
  "intent": "ORDER",
  "priority": "ROUTINE",
  "authored_on": "2025-01-10T10:00:00Z",
  "prescriber_id": "medecin-uuid",
  "pharmacy_validation_status": "PENDING"
}
```

---

**Document validé par** : Data Architect, DBA, Tech Lead  
**Date** : 2025-01-10  
**Version** : 1.0  
**Prochaine revue** : 2025-02-10
