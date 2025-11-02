# Guide de Démarrage Rapide - KeneyApp v3.0

## 🚀 Installation Rapide

### Prérequis
- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Node.js 18+ (pour frontend)

### 1. Clone et installation backend

```bash
# Cloner le repository
git clone https://github.com/ISData-consulting/keneyapp.git
cd keneyapp

# Créer environnement virtuel
python3 -m venv .venv
source .venv/bin/activate  # Sur Windows: .venv\Scripts\activate

# Installer dépendances
pip install -r requirements.txt
```

### 2. Configuration base de données

```bash
# Créer base PostgreSQL
createdb keneyapp

# Configurer .env
cat > .env << EOF
DATABASE_URL=postgresql://user:password@localhost:5432/keneyapp
SECRET_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(32))")
REDIS_HOST=localhost
REDIS_PORT=6379

# SMTP (optionnel pour notifications)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# Twilio (optionnel pour SMS)
TWILIO_ACCOUNT_SID=ACxxxxx
TWILIO_AUTH_TOKEN=your-token
TWILIO_FROM_NUMBER=+1234567890

# Documents
DOCUMENTS_UPLOAD_DIR=./uploads/medical_documents
MAX_DOCUMENT_SIZE=52428800
EOF

# Appliquer migrations
alembic upgrade head

# Initialiser données de test
python scripts/init_db.py
```

### 3. Démarrer les services

```bash
# Terminal 1 : Backend API
uvicorn app.main:app --reload --port 8000

# Terminal 2 : Celery Worker
celery -A app.core.celery_app worker --loglevel=info

# Terminal 3 : Celery Beat (scheduler)
celery -A app.core.celery_app beat --loglevel=info

# Terminal 4 : Frontend (optionnel)
cd frontend
npm install
npm start
```

### 4. Accès à l'application

- **API Backend** : http://localhost:8000
- **Documentation API** : http://localhost:8000/api/v1/docs
- **Frontend** : http://localhost:3000
- **Flower (Celery)** : http://localhost:5555

### 5. Comptes de test

| Rôle | Email | Mot de passe |
|------|-------|--------------|
| Admin | admin@keneyapp.com | admin123 |
| Docteur | doctor@keneyapp.com | doctor123 |
| Infirmière | nurse@keneyapp.com | nurse123 |
| Réceptionniste | receptionist@keneyapp.com | receptionist123 |

---

## 📝 Utilisation des Nouvelles Fonctionnalités

### 💬 Messagerie Sécurisée

#### Envoyer un message
```bash
curl -X POST http://localhost:8000/api/v1/messages/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "receiver_id": 2,
    "subject": "Question sur ordonnance",
    "content": "Bonjour docteur, j'ai une question...",
    "is_urgent": false
  }'
```

#### Lire les messages non lus
```bash
curl http://localhost:8000/api/v1/messages/?unread_only=true \
  -H "Authorization: Bearer $TOKEN"
```

#### Statistiques
```bash
curl http://localhost:8000/api/v1/messages/stats \
  -H "Authorization: Bearer $TOKEN"
```

---

### 📄 Upload de Documents

#### Upload via curl
```bash
curl -X POST http://localhost:8000/api/v1/documents/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@/path/to/document.pdf" \
  -F "patient_id=1" \
  -F "document_type=lab_result" \
  -F "description=Analyse de sang" \
  -F "tags=[\"sanguin\", \"hemogramme\"]"
```

#### Upload via Python
```python
import requests

url = "http://localhost:8000/api/v1/documents/upload"
headers = {"Authorization": f"Bearer {token}"}

files = {
    'file': open('analyse.pdf', 'rb')
}

data = {
    'patient_id': 1,
    'document_type': 'lab_result',
    'description': 'Analyse de sang',
    'tags': '["sanguin", "hemogramme"]',
    'is_sensitive': True
}

response = requests.post(url, headers=headers, files=files, data=data)
print(response.json())
```

#### Télécharger un document
```bash
curl http://localhost:8000/api/v1/documents/123/download \
  -H "Authorization: Bearer $TOKEN" \
  -o document.pdf
```

---

### 🔔 Notifications Automatiques

#### Configurer notifications email

1. **Gmail App Password**
   - Aller sur https://myaccount.google.com/apppasswords
   - Créer un mot de passe d'application
   - Ajouter dans `.env`:
     ```env
     SMTP_USER=your-email@gmail.com
     SMTP_PASSWORD=generated-app-password
     ```

2. **Test notification**
```python
from app.services.notification_service import NotificationService
from datetime import datetime, timedelta

NotificationService.send_appointment_reminder(
    patient_email="patient@example.com",
    patient_name="Jean Dupont",
    appointment_date=datetime.now() + timedelta(days=1),
    doctor_name="Dr. Martin",
    phone="+33612345678"
)
```

#### Configurer Celery Beat

Dans `app/core/celery_app.py`, ajouter:
```python
from celery.schedules import crontab

app.conf.beat_schedule = {
    'appointment-reminders-daily': {
        'task': 'send_upcoming_appointment_reminders',
        'schedule': crontab(hour=8, minute=0),
    },
    'prescription-reminders-daily': {
        'task': 'send_prescription_renewal_reminders',
        'schedule': crontab(hour=9, minute=0),
    },
}
```

---

### 🔗 Partage de Dossier Médical

#### Créer un partage
```python
import requests

url = "http://localhost:8000/api/v1/shares/"
headers = {"Authorization": f"Bearer {token}"}

data = {
    "patient_id": 1,
    "scope": "full_record",
    "recipient_email": "dr.external@hospital.com",
    "recipient_name": "Dr. Martin",
    "expires_in_hours": 48,
    "max_access_count": 3,
    "require_pin": True,
    "purpose": "Consultation spécialisée"
}

response = requests.post(url, headers=headers, json=data)
share = response.json()

print(f"Token: {share['share_token']}")
print(f"PIN: {share['access_pin']}")
print(f"Expires: {share['expires_at']}")
```

#### Accéder au dossier partagé (sans authentification)
```python
url = "http://localhost:8000/api/v1/shares/access"

data = {
    "token": "xYz123AbC...",
    "pin": "845621"
}

response = requests.post(url, json=data)
record = response.json()

print(f"Patient: {record['patient']['first_name']} {record['patient']['last_name']}")
print(f"Allergies: {record['allergies']}")
print(f"Rendez-vous: {len(record['appointments'])}")
```

#### Révoquer un partage
```bash
curl -X DELETE http://localhost:8000/api/v1/shares/123 \
  -H "Authorization: Bearer $TOKEN"
```

---

## 🧪 Tests

### Tests unitaires
```bash
# Tous les tests
pytest tests/ -v

# Tests spécifiques
pytest tests/test_messages.py -v
pytest tests/test_documents.py -v
pytest tests/test_shares.py -v

# Avec couverture
pytest --cov=app --cov-report=html tests/
```

### Tests API avec Postman

Importer collection Postman:
```bash
# À venir
```

### Tests de charge

Avec Locust:
```bash
pip install locust
locust -f tests/load_test.py
```

---

## 🐳 Déploiement Docker

### Development
```bash
# Tout en un
./scripts/start_stack.sh

# Ou manuellement
docker-compose up -d

# Voir les logs
docker-compose logs -f backend
```

### Production
```bash
docker-compose -f docker-compose.prod.yml up -d
```

---

## 📊 Monitoring

### Prometheus Metrics
```bash
curl http://localhost:8000/metrics
```

### Flower (Celery)
```bash
celery -A app.core.celery_app flower --port=5555
# Accès: http://localhost:5555
```

### Logs
```bash
# Logs backend
tail -f logs/app.log

# Logs Celery
tail -f logs/celery.log
```

---

## 🔧 Troubleshooting

### Problème : Migrations échouent
```bash
# Reset migrations (ATTENTION : perte de données)
alembic downgrade base
alembic upgrade head

# Ou migration spécifique
alembic upgrade 010_add_messages
```

### Problème : Celery ne démarre pas
```bash
# Vérifier Redis
redis-cli ping  # Doit retourner PONG

# Tester Celery
celery -A app.core.celery_app inspect active
```

### Problème : Upload documents échoue
```bash
# Vérifier permissions dossier
mkdir -p ./uploads/medical_documents
chmod 755 ./uploads/medical_documents

# Vérifier taille limite
echo "MAX_DOCUMENT_SIZE=52428800" >> .env
```

### Problème : Notifications ne partent pas
```bash
# Test SMTP
python -c "
from app.services.notification_service import EmailNotification
EmailNotification.send_email('test@example.com', 'Test', 'Hello')
"

# Test Twilio
python -c "
from app.services.notification_service import SMSNotification
SMSNotification.send_sms('+33612345678', 'Test message')
"
```

---

## 📚 Ressources

### Documentation
- [API Reference](API_REFERENCE.md)
- [Architecture](../ARCHITECTURE.md)
- [Sécurité](SECURITY_BEST_PRACTICES.md)
- [FHIR Guide](FHIR_GUIDE.md)

### Liens utiles
- **FastAPI** : https://fastapi.tiangolo.com
- **Celery** : https://docs.celeryq.dev
- **Twilio** : https://www.twilio.com/docs
- **FHIR** : https://www.hl7.org/fhir

### Support
📧 contact@isdataconsulting.com

---

**Bon développement ! 🚀**
