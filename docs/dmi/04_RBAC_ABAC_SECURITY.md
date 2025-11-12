# Matrice RBAC/ABAC et Sécurité - DMI

## 1. Rôles Utilisateurs

### 1.1 Hiérarchie des Rôles

```
Super Admin (système)
├─ Admin (établissement)
│  ├─ Direction Médicale
│  ├─ DIM (Data Manager)
│  └─ DPO
├─ Médecin
│  ├─ Chef de Service
│  ├─ Médecin Senior
│  └─ Interne
├─ Pharmacien
│  ├─ Pharmacien Chef
│  └─ Préparateur Pharmacie
├─ IDE (Infirmier·e)
│  ├─ IDEC (Cadre)
│  └─ IDE
├─ Secrétaire Médicale
│  ├─ Secrétaire Chef
│  └─ Secrétaire
└─ Patient (portail patient - V2)
```

### 1.2 Description des Rôles

#### Super Admin

- **Périmètre** : Multi-tenant, configuration plateforme
- **Responsabilités** : Gestion tenants, configuration système, support N3
- **Restrictions** : Pas d'accès données patients (sauf support avec audit)

#### Admin (Établissement)

- **Périmètre** : Établissement/tenant spécifique
- **Responsabilités** : Gestion utilisateurs, configuration établissement, rapports globaux
- **Restrictions** : Accès données patients en lecture seule (audit uniquement)

#### Médecin

- **Périmètre** : Patients dont il est référent ou consultés
- **Responsabilités** : Consultation, prescription, validation examens
- **Restrictions** : Break-the-glass requis pour patients hors périmètre

#### Pharmacien

- **Périmètre** : Prescriptions de l'établissement
- **Responsabilités** : Validation pharmaceutique, gestion interactions
- **Restrictions** : Pas de création/modification données cliniques hors prescription

#### IDE (Infirmier·e)

- **Périmètre** : Patients du service assigné
- **Responsabilités** : Saisie constantes, administration traitements, surveillance
- **Restrictions** : Pas de prescription (sauf protocoles validés), pas de consultation médicale

#### Secrétaire Médicale

- **Périmètre** : Service/cabinet assigné
- **Responsabilités** : Gestion RDV, saisie administrative, édition courriers
- **Restrictions** : Accès données médicales en lecture seule limitée

#### DIM (Data Manager)

- **Périmètre** : Établissement (données agrégées)
- **Responsabilités** : Extraction données, reporting, codage PMSI
- **Restrictions** : Accès données pseudonymisées sauf mission spécifique

#### DPO

- **Périmètre** : Établissement (audit et conformité)
- **Responsabilités** : Audit logs, gestion consentements, conformité RGPD
- **Restrictions** : Accès données patients pour audit uniquement (tracé)

## 2. Matrice RBAC Détaillée

### 2.1 Ressource : Patient

| Action | Super Admin | Admin | Médecin | Pharmacien | IDE | Secrétaire | DIM | DPO |
|--------|-------------|-------|---------|------------|-----|------------|-----|-----|
| **Créer** | ❌ | ✅ | ✅ | ❌ | ✅ | ✅ | ❌ | ❌ |
| **Lire - Identité** | ❌ (support) | ✅ (audit) | ✅ | ✅ | ✅ | ✅ | ⚠️ (pseudonymisé) | ✅ (audit) |
| **Lire - Données médicales** | ❌ | ❌ | ✅ | ✅ | ✅ | ⚠️ (limité) | ❌ | ❌ |
| **Modifier - Identité** | ❌ | ✅ | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ |
| **Modifier - Données médicales** | ❌ | ❌ | ✅ | ❌ | ⚠️ (constantes) | ❌ | ❌ | ❌ |
| **Supprimer (soft)** | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **Fusionner doublons** | ❌ | ✅ | ✅ | ❌ | ❌ | ⚠️ (avec validation) | ❌ | ❌ |
| **Exporter** | ❌ | ⚠️ (anonymisé) | ✅ | ❌ | ❌ | ❌ | ✅ (anonymisé) | ✅ (audit) |

**Légende** :

- ✅ = Autorisé sans restriction
- ⚠️ = Autorisé avec restrictions (voir détails)
- ❌ = Interdit

### 2.2 Ressource : Encounter (Consultation)

| Action | Super Admin | Admin | Médecin | Pharmacien | IDE | Secrétaire | DIM | DPO |
|--------|-------------|-------|---------|------------|-----|------------|-----|-----|
| **Créer** | ❌ | ❌ | ✅ | ❌ | ⚠️ (triage) | ⚠️ (admission) | ❌ | ❌ |
| **Lire** | ❌ | ❌ | ✅ | ✅ | ✅ | ⚠️ (résumé) | ⚠️ (agrégé) | ❌ |
| **Modifier** | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **Clôturer** | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **Annuler** | ❌ | ⚠️ (admin) | ✅ | ❌ | ❌ | ⚠️ (avant début) | ❌ | ❌ |

### 2.3 Ressource : Observation (Constantes, Résultats)

| Action | Super Admin | Admin | Médecin | Pharmacien | IDE | Secrétaire | DIM | DPO |
|--------|-------------|-------|---------|------------|-----|------------|-----|-----|
| **Créer** | ❌ | ❌ | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ |
| **Lire** | ❌ | ❌ | ✅ | ✅ | ✅ | ❌ | ⚠️ (agrégé) | ❌ |
| **Modifier** | ❌ | ❌ | ✅ | ❌ | ⚠️ (24h) | ❌ | ❌ | ❌ |
| **Supprimer** | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **Valider** | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |

### 2.4 Ressource : MedicationRequest (Prescription)

| Action | Super Admin | Admin | Médecin | Pharmacien | IDE | Secrétaire | DIM | DPO |
|--------|-------------|-------|---------|------------|-----|------------|-----|-----|
| **Créer** | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **Lire** | ❌ | ❌ | ✅ | ✅ | ✅ | ❌ | ⚠️ (agrégé) | ❌ |
| **Modifier** | ❌ | ❌ | ✅ | ⚠️ (adaptation) | ❌ | ❌ | ❌ | ❌ |
| **Annuler** | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **Valider (pharma)** | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ |
| **Refuser (pharma)** | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ |
| **Administrer** | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ |

### 2.5 Ressource : ServiceRequest (Examens Lab/Imagerie)

| Action | Super Admin | Admin | Médecin | Pharmacien | IDE | Secrétaire | DIM | DPO |
|--------|-------------|-------|---------|------------|-----|------------|-----|-----|
| **Créer** | ❌ | ❌ | ✅ | ❌ | ⚠️ (protocole) | ❌ | ❌ | ❌ |
| **Lire** | ❌ | ❌ | ✅ | ✅ | ✅ | ⚠️ (planning) | ⚠️ (stats) | ❌ |
| **Modifier** | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **Annuler** | ❌ | ❌ | ✅ | ❌ | ❌ | ⚠️ (admin) | ❌ | ❌ |

### 2.6 Ressource : DocumentReference

| Action | Super Admin | Admin | Médecin | Pharmacien | IDE | Secrétaire | DIM | DPO |
|--------|-------------|-------|---------|------------|-----|------------|-----|-----|
| **Upload** | ❌ | ❌ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ |
| **Lire** | ❌ | ❌ | ✅ | ✅ | ✅ | ✅ | ❌ | ⚠️ (audit) |
| **Télécharger** | ❌ | ❌ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ |
| **Supprimer** | ❌ | ⚠️ (admin) | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **Partager (externe)** | ❌ | ❌ | ✅ | ❌ | ❌ | ⚠️ (avec délégation) | ❌ | ❌ |

### 2.7 Ressource : Appointment

| Action | Super Admin | Admin | Médecin | Pharmacien | IDE | Secrétaire | DIM | DPO |
|--------|-------------|-------|---------|------------|-----|------------|-----|-----|
| **Créer** | ❌ | ❌ | ✅ | ❌ | ⚠️ (propre agenda) | ✅ | ❌ | ❌ |
| **Lire - Propre agenda** | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ |
| **Lire - Autres agendas** | ❌ | ✅ | ⚠️ (même service) | ❌ | ⚠️ (même service) | ✅ | ❌ | ❌ |
| **Modifier** | ❌ | ✅ | ✅ | ❌ | ⚠️ (propre agenda) | ✅ | ❌ | ❌ |
| **Annuler** | ❌ | ✅ | ✅ | ❌ | ⚠️ (propre agenda) | ✅ | ❌ | ❌ |

### 2.8 Ressource : AuditLog

| Action | Super Admin | Admin | Médecin | Pharmacien | IDE | Secrétaire | DIM | DPO |
|--------|-------------|-------|---------|------------|-----|------------|-----|-----|
| **Créer** | Auto | Auto | Auto | Auto | Auto | Auto | Auto | Auto |
| **Lire - Propres actions** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Lire - Tous logs** | ⚠️ (support) | ⚠️ (admin) | ❌ | ❌ | ❌ | ❌ | ⚠️ (stats) | ✅ |
| **Exporter** | ❌ | ⚠️ (anonymisé) | ❌ | ❌ | ❌ | ❌ | ⚠️ (agrégé) | ✅ |
| **Supprimer** | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |

## 3. Règles ABAC (Attribute-Based Access Control)

### 3.1 Attributs Contextuels

#### Attributs Utilisateur

```json
{
  "user_id": "uuid",
  "role": "MEDECIN",
  "speciality": "CARDIOLOGIE",
  "service_id": "uuid",
  "establishment_id": "uuid",
  "rpps": "12345678901",
  "on_call": false,
  "on_duty": true
}
```

#### Attributs Patient

```json
{
  "patient_id": "uuid",
  "consent_status": "GIVEN",
  "consent_scope": ["TREATMENT", "RESEARCH"],
  "emergency_access": false,
  "vip_flag": false,
  "assigned_service_id": "uuid",
  "current_encounter_id": "uuid"
}
```

#### Attributs Contexte de Soins

```json
{
  "encounter_id": "uuid",
  "encounter_status": "IN_PROGRESS",
  "care_team": ["user_id_1", "user_id_2"],
  "emergency": false,
  "intensive_care": false
}
```

#### Attributs Temporels

```json
{
  "access_time": "2025-01-10T14:30:00Z",
  "work_hours": true,
  "within_encounter_timeframe": true,
  "data_age_days": 2
}
```

### 3.2 Politiques ABAC (exemples OPA)

#### Politique 1 : Accès Dossier Patient

```rego
package dmi.patient.access

# Autoriser si médecin dans l'équipe de soins actuelle
allow {
    input.user.role == "MEDECIN"
    input.encounter.care_team[_] == input.user.id
    input.encounter.status == "IN_PROGRESS"
}

# Autoriser si IDE du service assigné
allow {
    input.user.role == "IDE"
    input.patient.assigned_service_id == input.user.service_id
}

# Autoriser si urgence ET soignant de garde
allow {
    input.encounter.emergency == true
    input.user.on_call == true
    input.user.role in ["MEDECIN", "IDE"]
}

# Autoriser Break-the-Glass (tracé)
allow {
    input.break_the_glass == true
    input.btg_justification != ""
    input.user.role in ["MEDECIN", "IDE"]
    # BTG est ensuite loggé et nécessite validation a posteriori
}

# Refuser si patient a révoqué consentement
deny {
    input.patient.consent_status == "REVOKED"
    not input.emergency
}
```

#### Politique 2 : Modification Prescription

```rego
package dmi.prescription.modify

# Médecin peut modifier sa propre prescription (< 24h)
allow {
    input.user.role == "MEDECIN"
    input.prescription.prescriber_id == input.user.id
    input.prescription.age_hours < 24
    input.prescription.status == "DRAFT"
}

# Pharmacien peut adapter posologie
allow {
    input.user.role == "PHARMACIEN"
    input.action == "ADAPT_DOSAGE"
    input.prescription.status == "PENDING_VALIDATION"
}

# Interdire modification si prescription dispensée
deny {
    input.prescription.status == "DISPENSED"
}
```

#### Politique 3 : Export Données

```rego
package dmi.data.export

# DIM peut exporter données pseudonymisées
allow {
    input.user.role == "DIM"
    input.export.pseudonymized == true
    input.export.purpose == "REPORTING"
}

# DPO peut exporter pour audit
allow {
    input.user.role == "DPO"
    input.export.purpose == "AUDIT"
    input.export.with_pii == true
    # Export loggé et nécessite justification
}

# Médecin peut exporter ses propres patients (consentement requis)
allow {
    input.user.role == "MEDECIN"
    input.export.patient_ids[_] in input.user.assigned_patients
    all_consented(input.export.patient_ids)
}

all_consented(patient_ids) {
    count([id | id := patient_ids[_]; patient_consent[id] == true]) == count(patient_ids)
}
```

### 3.3 Break-the-Glass (Accès d'Urgence)

#### Workflow BTG

```
1. Utilisateur tente d'accéder à un patient hors périmètre habituel
   └─> Accès refusé par règles RBAC/ABAC normales

2. Option "Accès d'urgence" proposée
   └─> Utilisateur doit fournir justification

3. Accès accordé IMMÉDIATEMENT
   └─> Action tracée avec flag "BREAK_THE_GLASS"

4. Notification automatique DPO + responsable hiérarchique
   └─> Revue a posteriori obligatoire

5. Si justification invalide
   └─> Sanction + alerte sécurité
```

#### Règles BTG

- ✅ Disponible uniquement pour : Médecin, IDE, Pharmacien
- ✅ Justification obligatoire (texte libre, min 20 caractères)
- ✅ Accès accordé immédiatement (urgence vitale)
- ✅ Traçabilité renforcée (email + notification + log immuable)
- ✅ Revue a posteriori par DPO dans les 24h
- ❌ BTG désactivé hors heures ouvrées (sauf urgences)
- ❌ BTG bloqué si historique d'abus

#### Logging BTG

```json
{
  "event": "BREAK_THE_GLASS",
  "timestamp": "2025-01-10T02:35:12Z",
  "user_id": "uuid-user",
  "user_role": "MEDECIN",
  "patient_id": "uuid-patient",
  "justification": "Patient admis aux urgences, arrêt cardiaque, besoin antécédents immédiats",
  "access_duration_minutes": 15,
  "actions_performed": ["READ_MEDICAL_HISTORY", "READ_ALLERGIES", "READ_MEDICATIONS"],
  "reviewed_by_dpo": false,
  "review_status": "PENDING",
  "alert_sent_to": ["dpo@hospital.fr", "chef-service@hospital.fr"]
}
```

## 4. Gestion des Consentements

### 4.1 Types de Consentements

#### Consentement Soins

- **Portée** : Accès dossier pour soins
- **Défaut** : Donné (consentement implicite loi)
- **Révocable** : Oui (tracé, sauf urgence)

#### Consentement Recherche

- **Portée** : Utilisation données pour recherche (anonymisées)
- **Défaut** : Non donné (opt-in)
- **Révocable** : Oui

#### Consentement Partage DMP

- **Portée** : Alimentation DMP national
- **Défaut** : Donné (opt-out possible)
- **Révocable** : Oui

#### Consentement Portail Patient

- **Portée** : Accès dossier via portail web/mobile
- **Défaut** : Non activé (opt-in)
- **Révocable** : Oui

### 4.2 Workflow Consentement

```gherkin
Feature: Gestion consentements patient

Scenario: Enregistrement consentement soins
  Given un patient vient d'être créé
  When le secrétaire/médecin clique sur "Gérer consentements"
  Then un formulaire s'affiche avec :
    | Type consentement      | Statut par défaut | Modifiable |
    | Soins                  | GIVEN             | Oui        |
    | Recherche              | NOT_GIVEN         | Oui        |
    | DMP                    | GIVEN             | Oui        |
    | Portail patient        | NOT_GIVEN         | Oui        |
  When le patient donne son consentement "Recherche"
  Then le consentement est enregistré avec :
    | Champ            | Valeur                        |
    | Type             | RESEARCH                      |
    | Status           | GIVEN                         |
    | Date             | 2025-01-10T14:30:00Z          |
    | Recorded_by      | user_id (secrétaire/médecin)  |
    | Valid_from       | 2025-01-10T14:30:00Z          |
    | Valid_until      | null (indéfini)               |
  And un événement "ConsentGiven" est publié

Scenario: Révocation consentement
  Given un patient a donné son consentement "Recherche"
  When le patient révoque ce consentement
  Then le consentement passe en statut "REVOKED"
  And la date de révocation est enregistrée
  And un événement "ConsentRevoked" est publié
  And toutes les données de recherche le concernant sont marquées pour suppression
```

## 5. Gestion des Sessions et Timeouts

### 5.1 Durée de Sessions

| Rôle | Durée Session Inactive | Durée Max Session | Renouvellement |
|------|------------------------|-------------------|----------------|
| **Médecin** | 30 minutes | 12 heures | Automatique si activité |
| **IDE** | 20 minutes | 12 heures | Automatique si activité |
| **Pharmacien** | 30 minutes | 12 heures | Automatique si activité |
| **Secrétaire** | 15 minutes | 8 heures | Automatique si activité |
| **Admin** | 15 minutes | 4 heures | Manuelle (re-auth) |
| **DPO** | 10 minutes | 2 heures | Manuelle (re-auth) |

### 5.2 Règles de Sécurité Sessions

- ✅ Token JWT avec refresh token
- ✅ Invalidation immédiate lors déconnexion
- ✅ Rotation refresh tokens (7 jours max)
- ✅ Détection sessions multiples (alerte si > 2)
- ✅ Verrouillage automatique après 3 échecs authentification
- ✅ Notification email si connexion depuis nouveau device

## 6. Audit et Traçabilité

### 6.1 Événements Audités

#### Événements de Sécurité (100% tracés)

```
- LOGIN_SUCCESS
- LOGIN_FAILED
- LOGOUT
- PASSWORD_CHANGE
- PASSWORD_RESET_REQUEST
- SESSION_EXPIRED
- BREAK_THE_GLASS
- UNAUTHORIZED_ACCESS_ATTEMPT
- PRIVILEGE_ESCALATION_ATTEMPT
```

#### Événements Données Patients (100% tracés)

```
- PATIENT_CREATED
- PATIENT_READ (si hors équipe soins habituelle)
- PATIENT_UPDATED
- PATIENT_MERGED
- PATIENT_DELETED (soft)
- CONSENT_GIVEN
- CONSENT_REVOKED
```

#### Événements Cliniques (100% tracés)

```
- PRESCRIPTION_CREATED
- PRESCRIPTION_VALIDATED
- PRESCRIPTION_REFUSED
- MEDICATION_ADMINISTERED
- OBSERVATION_CREATED
- LAB_RESULT_ACCESSED
- DOCUMENT_UPLOADED
- DOCUMENT_DOWNLOADED
- DOCUMENT_SHARED
```

### 6.2 Structure Log Audit

```json
{
  "event_id": "uuid",
  "timestamp": "2025-01-10T14:30:00.123Z",
  "event_type": "PATIENT_READ",
  "severity": "INFO",
  "user": {
    "id": "uuid",
    "username": "dr.martin",
    "role": "MEDECIN",
    "rpps": "12345678901"
  },
  "resource": {
    "type": "Patient",
    "id": "uuid-patient",
    "ipp": "123456789"
  },
  "context": {
    "encounter_id": "uuid-encounter",
    "break_the_glass": false,
    "ip_address": "192.168.1.100",
    "user_agent": "Mozilla/5.0...",
    "correlation_id": "uuid-request"
  },
  "action": {
    "operation": "READ",
    "fields_accessed": ["demographics", "allergies", "medications"],
    "success": true
  },
  "metadata": {
    "establishment_id": "uuid",
    "service_id": "uuid",
    "session_id": "uuid"
  }
}
```

### 6.3 Rétention Logs

| Type Log | Durée Rétention | Format Stockage | Accès |
|----------|----------------|-----------------|-------|
| **Logs Sécurité** | 5 ans | Immuable (WORM) | DPO, Admin |
| **Logs Cliniques** | 20 ans | Immuable (WORM) | DPO, patient (droit accès) |
| **Logs Techniques** | 1 an | Standard | Support, Admin |

## 7. Politiques de Sécurité

### 7.1 Mots de Passe

- Longueur min : 12 caractères
- Complexité : Majuscule + minuscule + chiffre + caractère spécial
- Historique : 5 derniers mots de passe interdits
- Expiration : 90 jours (rôles admin), 180 jours (autres)
- Blocage : 3 tentatives échouées = blocage 15 minutes
- Réinitialisation : Envoi email + SMS (2FA)

### 7.2 Chiffrement

- **Transit** : TLS 1.3 minimum
- **Repos** : AES-256-GCM pour données PHI
- **Clés** : Gestion via KMS (rotation automatique)
- **Champs chiffrés** : Nom, Prénom, Date naissance, Adresse, Téléphone, Email, Données cliniques sensibles

### 7.3 Sauvegardes

- **Fréquence** : Quotidienne (complète) + horaire (incrémentale)
- **Chiffrement** : Oui (AES-256)
- **Rétention** : 30 jours (quotidienne), 7 jours (horaire)
- **Tests restauration** : Mensuel (automatisé)
- **Localisation** : Multi-sites (géo-redondance)

---

**Document validé par** : RSSI, DPO, DSI
**Date** : 2025-01-10
**Version** : 1.0
**Prochaine revue** : 2025-04-10
