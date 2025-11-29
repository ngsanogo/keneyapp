# Nouvelles Fonctionnalités KeneyApp v3.0

## Vue d'ensemble

Ce document détaille les nouvelles fonctionnalités implémentées pour transformer KeneyApp en une plateforme complète de dossier médical électronique (DME) conforme aux standards internationaux.

---

## 1. 💬 Messagerie Sécurisée Patient-Médecin

### Description

Système de messagerie chiffrée E2E permettant une communication sécurisée entre patients et professionnels de santé.

### Fonctionnalités

- **Chiffrement AES-256-GCM** : Tous les messages sont chiffrés au repos
- **Conversations threadées** : Regroupement automatique des messages par conversation
- **Statuts de lecture** : Suivi des messages lus/non lus
- **Messages urgents** : Marquage prioritaire pour les cas urgents
- **Pièces jointes** : Support pour joindre des documents médicaux
- **Soft delete** : Suppression côté utilisateur sans perte de données

### API Endpoints

```
POST   /api/v1/messages/                    # Envoyer un message
GET    /api/v1/messages/                    # Liste des messages (inbox + envoyés)
GET    /api/v1/messages/stats               # Statistiques messagerie
GET    /api/v1/messages/conversation/{id}   # Conversation avec un utilisateur
GET    /api/v1/messages/{id}                # Détails d'un message
POST   /api/v1/messages/{id}/read           # Marquer comme lu
DELETE /api/v1/messages/{id}                # Supprimer un message
```

### Modèle de données

```sql
TABLE messages (
  id, sender_id, receiver_id, encrypted_content,
  subject, status (sent/delivered/read/failed),
  is_urgent, attachment_ids, thread_id, reply_to_id,
  tenant_id, created_at, read_at, deleted_by_sender, deleted_by_receiver
)
```

### Sécurité

- ✅ Chiffrement des messages avec contexte tenant
- ✅ Validation RBAC (tous les rôles peuvent envoyer/recevoir)
- ✅ Rate limiting : 30 envois/min, 60 lectures/min
- ✅ Audit logging de tous les envois et lectures
- ✅ Pas de PHI dans les logs

### Migration

```bash
alembic upgrade head  # Applique 010_add_messages
```

---

## 2. 📄 Upload et Gestion de Documents Médicaux

### Description

Système complet de gestion documentaire pour stocker analyses, imagerie, ordonnances, vaccins, etc.

### Formats supportés

- **PDF** : Comptes-rendus, ordonnances
- **Images** : JPEG, PNG (radios, photos)
- **DICOM** : Imagerie médicale standard
- **Office** : DOCX, TXT

### Types de documents

- `lab_result` : Résultats d'analyses
- `imaging` : Imagerie médicale (X-ray, CT, MRI)
- `prescription` : Ordonnances
- `consultation_note` : Comptes-rendus
- `vaccination_record` : Carnets de vaccination
- `insurance` : Documents d'assurance
- `id_document` : Pièces d'identité
- `other` : Autres

### Fonctionnalités

- **Upload sécurisé** : Limite 50 MB, validation MIME
- **Détection de doublons** : Checksum SHA-256
- **Stockage local ou S3** : Configurable via env vars
- **Métadonnées enrichies** : Description, tags, associations
- **OCR ready** : Champ pour texte extrait (futur)
- **Soft delete** : Archivage sans suppression physique

### API Endpoints

```
POST   /api/v1/documents/upload             # Upload document
GET    /api/v1/documents/patient/{id}       # Documents d'un patient
GET    /api/v1/documents/stats               # Statistiques stockage
GET    /api/v1/documents/{id}                # Détails document
GET    /api/v1/documents/{id}/download       # Télécharger fichier
PATCH  /api/v1/documents/{id}                # Mettre à jour métadonnées
DELETE /api/v1/documents/{id}                # Supprimer document
```

### Modèle de données

```sql
TABLE medical_documents (
  id, filename, original_filename,
  document_type, document_format, mime_type, file_size,
  storage_path, storage_type, checksum,
  status (uploading/processing/ready/failed/archived),
  processing_error, ocr_text, extracted_metadata,
  patient_id, uploaded_by_id, appointment_id, prescription_id,
  description, tags, is_sensitive, encryption_key_id,
  tenant_id, created_at, updated_at, deleted_at
)
```

### Configuration

```env
DOCUMENTS_UPLOAD_DIR=./uploads/medical_documents  # Local storage path
MAX_DOCUMENT_SIZE=52428800                        # 50 MB in bytes
```

### Sécurité

- ✅ Validation MIME type stricte
- ✅ Limite de taille fichier
- ✅ Checksum pour intégrité
- ✅ Détection doublons
- ✅ PHI marqué par défaut
- ✅ Audit logging téléchargements
- ✅ Rate limiting : 20 uploads/min, 30 downloads/min

### Migration

```bash
alembic upgrade head  # Applique 011_add_medical_documents
```

---

## 3. 🔔 Système d'Alertes et Rappels Automatiques

### Description

Notifications automatiques multi-canal (email, SMS) pour rappels et alertes importantes.

### Types de notifications

#### 📅 Rappels de rendez-vous

- Envoyés 24h avant le rendez-vous
- Email + SMS (si numéro fourni)
- Tâche Celery : `send_upcoming_appointment_reminders` (daily)

#### 🧪 Résultats d'analyses disponibles

- Notification immédiate après upload
- Tâche Celery : `send_lab_results_notifications`
- Déclenchée manuellement après upload document

#### 💊 Renouvellement d'ordonnances

- Rappel 7 jours avant expiration
- Email + SMS
- Tâche Celery : `send_prescription_renewal_reminders` (daily)

#### 💉 Rappels de vaccination

- Configurable par vaccin
- Tâche Celery : `send_vaccination_reminder`

#### 💬 Nouveaux messages

- Notification immédiate
- Tâche Celery : `send_new_message_notification`
- Déclenchée après création message

### Service de notifications

**Module**: `app/services/notification_service.py`

Classes:

- `EmailNotification` : SMTP (Gmail, SendGrid, SES)
- `SMSNotification` : Twilio, AWS SNS
- `NotificationService` : Orchestrateur unifié

### Configuration

```env
# Email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM=noreply@keneyapp.com

# SMS via Twilio
SMS_PROVIDER=twilio
TWILIO_ACCOUNT_SID=ACxxxxx
TWILIO_AUTH_TOKEN=your-token
TWILIO_FROM_NUMBER=+1234567890
```

### Tâches Celery

```python
# Dans app/tasks.py
send_upcoming_appointment_reminders()      # Daily at 8 AM
send_lab_results_notifications(doc_id, patient_id)  # On-demand
send_prescription_renewal_reminders()      # Daily at 9 AM
send_new_message_notification(msg_id, receiver_id)  # On-demand
```

### Planification Celery Beat

Ajouter dans configuration Celery Beat :

```python
from celery.schedules import crontab

beat_schedule = {
    'appointment-reminders-daily': {
        'task': 'send_upcoming_appointment_reminders',
        'schedule': crontab(hour=8, minute=0),  # 8 AM daily
    },
    'prescription-reminders-daily': {
        'task': 'send_prescription_renewal_reminders',
        'schedule': crontab(hour=9, minute=0),  # 9 AM daily
    },
}
```

### Sécurité

- ✅ Pas de PHI dans les logs
- ✅ Emails avec opt-out (futur)
- ✅ RGPD compliant
- ✅ Rate limiting providers

### Dépendances

```bash
pip install twilio==9.3.7
```

---

## 4. 🔗 Partage Contrôlé du Dossier Médical

### Description

Système de partage temporaire et sécurisé des dossiers médicaux via tokens et liens.

### Fonctionnalités

- **Tokens temporaires** : Validité 1h à 30 jours
- **Protection PIN optionnelle** : Code à 6 chiffres
- **Limitation d'accès** : Nombre maximum d'accès configurable
- **Restriction email** : Limite l'accès à un email spécifique
- **Scopes personnalisables** :
  - `full_record` : Dossier complet
  - `appointments_only` : Rendez-vous uniquement
  - `prescriptions_only` : Ordonnances uniquement
  - `documents_only` : Documents uniquement
  - `custom` : Sélection personnalisée

### Cas d'usage

1. **Consultation externe** : Patient partage son dossier avec un nouveau médecin
2. **Urgences** : Accès rapide aux données critiques (allergies, traitements)
3. **Assurance** : Partage de documents spécifiques pour remboursement
4. **Famille** : Partage avec proche pour suivi médical

### API Endpoints

```
POST   /api/v1/shares/                      # Créer un partage
GET    /api/v1/shares/                      # Liste des partages créés
POST   /api/v1/shares/access                # Accéder via token (public)
GET    /api/v1/shares/{id}                  # Détails d'un partage
DELETE /api/v1/shares/{id}                  # Révoquer un partage
```

### Modèle de données

```sql
TABLE medical_record_shares (
  id, patient_id, shared_by_user_id,
  share_token (secure random), scope,
  custom_resources, recipient_email, recipient_name,
  access_pin, status (active/expired/revoked/used),
  expires_at, access_count, max_access_count,
  last_accessed_at, last_accessed_ip,
  purpose, notes, consent_given, consent_date,
  tenant_id, created_at, updated_at, revoked_at, revoked_by_user_id
)
```

### Exemple d'utilisation

**1. Créer un partage**

```json
POST /api/v1/shares/
{
  "patient_id": 123,
  "scope": "full_record",
  "recipient_email": "dr.external@hospital.com",
  "recipient_name": "Dr. Martin",
  "expires_in_hours": 48,
  "max_access_count": 3,
  "require_pin": true,
  "purpose": "Consultation spécialisée"
}

Response:
{
  "id": 1,
  "share_token": "xYz123AbC...",
  "access_pin": "845621",
  "expires_at": "2025-11-04T10:00:00Z",
  ...
}
```

**2. Accéder au dossier partagé** (sans authentification)

```json
POST /api/v1/shares/access
{
  "token": "xYz123AbC...",
  "pin": "845621"
}

Response:
{
  "patient": {
    "first_name": "Jean",
    "last_name": "Dupont",
    "date_of_birth": "1980-05-15",
    "blood_type": "A+",
    "allergies": "Pénicilline"
  },
  "appointments": [...],
  "prescriptions": [...],
  "documents": [...],
  "medical_history": "...",
  "scope": "full_record",
  "accessed_at": "2025-11-02T15:30:00Z"
}
```

### Sécurité

- ✅ Tokens sécurisés (secrets.token_urlsafe)
- ✅ PINs aléatoires 6 chiffres
- ✅ Expiration automatique
- ✅ Révocation manuelle
- ✅ Audit logging de tous les accès
- ✅ Tracking IP
- ✅ Rate limiting : 10 créations/h, 20 accès/h
- ✅ Consentement patient requis

### Migration

```bash
alembic upgrade head  # Applique 012_add_medical_record_shares
```

---

## 5. 📊 Statistiques et Tableaux de Bord Professionnels (À venir)

### Description

Analytics avancés pour le suivi des patients chroniques et KPIs médicaux.

### Fonctionnalités prévues

- Suivi patients chroniques
- Alertes pathologies
- Graphiques tendances
- Exports rapports PDF/Excel
- Tableaux de bord personnalisables

---

## 6. 💳 Intégration Paiement en Ligne (À venir)

### Description

Module de paiement pour téléconsultations.

### Fonctionnalités prévues

- Intégration Stripe/PayPal
- Gestion transactions
- Facturation automatique
- Remboursements

---

## 7. 📹 Module Téléconsultation (À venir)

### Description

Visioconférence intégrée pour consultations à distance.

### Fonctionnalités prévues

- WebRTC ou Twilio Video
- Salles d'attente virtuelles
- Enregistrement consultations (avec consentement)
- Chat vidéo sécurisé

---

## Installation et Configuration

### 1. Installer les dépendances

```bash
pip install -r requirements.txt
```

### 2. Appliquer les migrations

```bash
alembic upgrade head
```

### 3. Configurer les variables d'environnement

```bash
# Créer .env avec les configs SMTP, Twilio, etc.
cp .env.example .env
nano .env
```

### 4. Redémarrer les services

```bash
# Backend
uvicorn app.main:app --reload

# Celery worker
celery -A app.core.celery_app worker --loglevel=info

# Celery beat (scheduler)
celery -A app.core.celery_app beat --loglevel=info
```

---

## Tests

### Tests unitaires

```bash
# Tester messagerie
pytest tests/test_messages.py -v

# Tester documents
pytest tests/test_documents.py -v

# Tester partages
pytest tests/test_shares.py -v

# Tester notifications
pytest tests/test_notifications.py -v
```

### Tests d'intégration

```bash
# Full suite
pytest tests/ -v --cov=app
```

---

## Conformité et Sécurité

### RGPD

- ✅ Droit d'accès (partages avec tokens)
- ✅ Droit à l'effacement (soft deletes)
- ✅ Portabilité (exports futurs)
- ✅ Consentement explicite (partages)
- ✅ Audit complet

### HIPAA

- ✅ Chiffrement au repos (AES-256)
- ✅ Chiffrement en transit (TLS)
- ✅ Contrôle d'accès (RBAC)
- ✅ Audit trail complet
- ✅ Authentification forte

### HDS (France)

- ✅ Hébergement sécurisé
- ✅ Traçabilité accès
- ✅ Chiffrement données santé
- ✅ Gestion consentements

---

## Métriques et Monitoring

### Nouvelles métriques Prometheus

```python
# Messages
messages_sent_total
messages_read_total
messages_urgent_total

# Documents
documents_uploaded_total
documents_downloaded_total
documents_total_size_bytes

# Partages
shares_created_total
shares_accessed_total
shares_revoked_total

# Notifications
notifications_sent_total{type="email"}
notifications_sent_total{type="sms"}
notifications_failed_total
```

### Logs structurés

Tous les événements sont loggés en JSON pour analyse:

```json
{
  "event": "document_uploaded",
  "user_id": 123,
  "patient_id": 456,
  "document_type": "lab_result",
  "file_size": 2048576,
  "timestamp": "2025-11-02T10:30:00Z"
}
```

---

## Support et Documentation

### Documentation API

- Swagger UI : `http://localhost:8000/api/v1/docs`
- ReDoc : `http://localhost:8000/api/v1/redoc`

### Guides

- [Guide développeur](DEVELOPMENT.md)
- [Guide déploiement](DEPLOYMENT.md)
- [Guide sécurité](SECURITY.md)

### Contact

📧 <contact@isdataconsulting.com>

---

## Roadmap

### Q1 2026

- ✅ Messagerie sécurisée
- ✅ Upload documents
- ✅ Notifications automatiques
- ✅ Partage dossiers

### Q2 2026

- 📊 Statistiques avancées
- 💳 Paiements en ligne
- 📹 Téléconsultation
- 📱 Application mobile React Native

### Q3 2026

- 🤖 IA pour analyse prédictive
- 🌍 Multi-langue
- 📊 Business Intelligence
- 🔐 Blockchain pour traçabilité

---

**Version**: 3.0.0
**Date**: 2 novembre 2025
**Auteur**: ISDATA Consulting
**License**: Proprietary
