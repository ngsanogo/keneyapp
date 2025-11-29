# French Healthcare Integration Guide

## Vue d'ensemble

KeneyApp intègre les standards de santé français pour une conformité complète avec les exigences de l'Agence du Numérique en Santé (ANS) et la réglementation française.

### Fonctionnalités implémentées

✅ **INS (Identifiant National de Santé)** - Validation et vérification des identités patients
✅ **Pro Santé Connect** - Authentification des professionnels de santé via CPS/e-CPS
✅ **DMP (Dossier Médical Partagé)** - Préparation pour l'intégration (à venir)
✅ **MSSanté** - Préparation pour messagerie sécurisée certifiée (à venir)

---

## 1. INS (Identifiant National de Santé)

### Description

L'INS est l'identifiant national de santé unique et pérenne pour chaque patient en France. Il remplace le NIR dans le contexte médical.

**Format INS**: `1 YY MM RR DDD KKK CC`
- `1` : Sexe (1=M, 2=F)
- `YY` : Année de naissance (2 chiffres)
- `MM` : Mois de naissance
- `RR` : Département ou pays de naissance
- `DDD` : Code commune
- `KKK` : Ordre de naissance
- `CC` : Clé de contrôle (algorithme de Luhn modifié)

### Configuration

```bash
# .env
INS_API_URL=https://api.esante.gouv.fr/ins/v1
INS_API_KEY=votre_cle_api_ans
INS_VALIDATION_ENABLED=true
```

### Obtention des credentials INS

1. **Inscription sur le portail ANS**
   - URL: https://industriels.esante.gouv.fr
   - Créer un compte entreprise
   - Demander l'accès au Téléservice INS

2. **Certification**
   - Compléter le dossier de certification
   - Passer les tests de conformité ANS
   - Obtenir la clé API de production

3. **Environnements**
   - **Test**: `https://api-test.esante.gouv.fr/ins/v1`
   - **Production**: `https://api.esante.gouv.fr/ins/v1`

### API Endpoints

#### Vérifier l'INS d'un patient

```http
POST /api/v1/french-healthcare/ins/verify
Authorization: Bearer {token}
Content-Type: application/json

{
  "patient_id": "uuid-du-patient",
  "ins_number": "184127512345678",
  "birth_name": "DUPONT",
  "first_names": "JEAN PIERRE",
  "birth_date": "1984-12-25",
  "birth_location": "PARIS"
}
```

**Réponse**:
```json
{
  "success": true,
  "status": "verified",
  "ins_number": "184127512345678",
  "verified_at": "2025-11-29T14:30:00Z",
  "expires_at": "2026-11-29T14:30:00Z",
  "message": "INS verified successfully",
  "identity_traits": {
    "birth_name": "DUPONT",
    "first_names": "JEAN PIERRE",
    "birth_date": "1984-12-25",
    "birth_location": "PARIS 15EME ARRONDISSEMENT",
    "gender_code": "1"
  }
}
```

#### Récupérer l'INS d'un patient

```http
GET /api/v1/french-healthcare/ins/patient/{patient_id}
Authorization: Bearer {token}
```

### Modèle de données

```sql
TABLE patient_ins (
  id UUID PRIMARY KEY,
  patient_id UUID UNIQUE REFERENCES patients(id),
  ins_number VARCHAR(15) UNIQUE NOT NULL,
  nir_key VARCHAR(2),
  oid VARCHAR(50),
  status ENUM('pending', 'verified', 'failed', 'expired'),
  verified_at TIMESTAMP,
  verification_method VARCHAR(50), -- 'teleservice_ins', 'carte_vitale'
  verification_operator_id UUID REFERENCES users(id),
  birth_name VARCHAR(100),
  first_names VARCHAR(200),
  birth_date TIMESTAMP,
  birth_location VARCHAR(200),
  birth_location_code VARCHAR(10), -- Code INSEE
  gender_code VARCHAR(1), -- 1=M, 2=F
  expires_at TIMESTAMP,
  last_check_at TIMESTAMP,
  tenant_id UUID NOT NULL,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);
```

### Workflow d'utilisation

1. **Création patient**: Saisir les traits d'identité
2. **Vérification INS**: Appeler l'API de vérification
3. **Statuts possibles**:
   - `pending`: En attente de vérification
   - `verified`: INS vérifié par le Téléservice ANS
   - `failed`: Échec de vérification (traits incohérents)
   - `expired`: Vérification expirée (>1 an)

4. **Renouvellement**: Vérifier annuellement

### Sécurité

- ✅ Audit logging de toutes les vérifications INS
- ✅ Chiffrement des données d'identité
- ✅ Rate limiting: 10 vérifications/minute
- ✅ RBAC: Admin, Médecin, Infirmier seulement
- ✅ Pas de PHI dans les logs

---

## 2. Pro Santé Connect (PSC)

### Description

Pro Santé Connect est le système d'authentification unique des professionnels de santé en France, basé sur la CPS (Carte de Professionnel de Santé) ou e-CPS.

### Configuration

```bash
# .env
PSC_CLIENT_ID=votre_client_id
PSC_CLIENT_SECRET=votre_client_secret
PSC_AUTHORIZATION_ENDPOINT=https://wallet.esw.esante.gouv.fr/auth
PSC_TOKEN_ENDPOINT=https://auth.esw.esante.gouv.fr/auth/realms/esante-wallet/protocol/openid-connect/token
PSC_USERINFO_ENDPOINT=https://auth.esw.esante.gouv.fr/auth/realms/esante-wallet/protocol/openid-connect/userinfo
PSC_JWKS_URI=https://auth.esw.esante.gouv.fr/auth/realms/esante-wallet/protocol/openid-connect/certs
PSC_SCOPE=openid profile email rpps
```

### Obtention des credentials PSC

1. **Inscription**
   - URL: https://industriels.esante.gouv.fr/produits-services/pro-sante-connect
   - Créer un dossier de demande
   - Justifier de l'activité dans le secteur santé

2. **Environnements**
   - **Test**: https://test-wallet.esw.esante.gouv.fr
   - **Production**: https://wallet.esw.esante.gouv.fr

3. **Configuration OAuth2**
   - Type: OpenID Connect (OIDC)
   - Flow: Authorization Code
   - Redirect URI: `https://votredomaine.fr/api/v1/auth/psc/callback`

### API Endpoints

#### Obtenir l'URL d'autorisation

```http
GET /api/v1/french-healthcare/psc/authorize
```

**Réponse**:
```json
{
  "authorization_url": "https://wallet.esw.esante.gouv.fr/auth?response_type=code&client_id=...",
  "state": "random-csrf-token"
}
```

#### Callback PSC (après authentification)

```http
POST /api/v1/french-healthcare/psc/callback
Content-Type: application/json

{
  "code": "authorization-code-from-psc",
  "state": "same-csrf-token"
}
```

**Réponse**:
```json
{
  "access_token": "jwt-token",
  "token_type": "bearer",
  "user": {
    "id": "uuid",
    "username": "psc_10012345678",
    "email": "jean.dupont@medecin.fr",
    "full_name": "Dr. Jean DUPONT",
    "role": "doctor"
  },
  "cps_details": {
    "cps_number": "12345678",
    "rpps_number": "10012345678",
    "profession_category": "Médecin",
    "specialty_label": "Médecine générale",
    "cps_type": "e_cps"
  }
}
```

#### Récupérer mes informations CPS

```http
GET /api/v1/french-healthcare/psc/me
Authorization: Bearer {token}
```

### Modèle de données

```sql
TABLE healthcare_professional_cps (
  id UUID PRIMARY KEY,
  user_id UUID UNIQUE REFERENCES users(id),
  cps_type ENUM('cps', 'e_cps', 'cpf'),
  cps_number VARCHAR(20) UNIQUE NOT NULL,
  rpps_number VARCHAR(11) UNIQUE, -- Répertoire Partagé des Professionnels de Santé
  adeli_number VARCHAR(9), -- Ancien identifiant
  profession_code VARCHAR(10), -- Code profession (ex: 10 = Médecin)
  profession_category VARCHAR(50),
  specialty_code VARCHAR(10),
  specialty_label VARCHAR(200),
  practice_structure_id VARCHAR(50), -- FINESS/SIRET
  practice_structure_name VARCHAR(200),
  psc_sub VARCHAR(100) UNIQUE, -- Subject ID de Pro Santé Connect
  psc_token_endpoint VARCHAR(500),
  psc_last_login TIMESTAMP,
  issue_date TIMESTAMP,
  expiry_date TIMESTAMP,
  is_active BOOLEAN DEFAULT TRUE,
  tenant_id UUID NOT NULL,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);
```

### Workflow OAuth2/OIDC

1. **Redirection vers PSC**: Frontend redirige vers l'URL d'autorisation
2. **Authentification CPS**: Professionnel s'authentifie avec CPS/e-CPS
3. **Callback**: PSC redirige vers `/api/v1/auth/psc/callback?code=...&state=...`
4. **Exchange code**: Backend échange le code contre tokens
5. **Création/MAJ user**: Création du compte ou mise à jour si existant
6. **Token KeneyApp**: Génération du JWT KeneyApp
7. **Redirection frontend**: Avec le token d'accès

### Intégration Frontend (React)

```typescript
// Initier la connexion PSC
const handlePSCLogin = async () => {
  const response = await fetch('/api/v1/french-healthcare/psc/authorize');
  const data = await response.json();
  
  // Stocker le state pour vérification CSRF
  sessionStorage.setItem('psc_state', data.state);
  
  // Rediriger vers Pro Santé Connect
  window.location.href = data.authorization_url;
};

// Callback page (route: /psc/callback)
const PSCCallback = () => {
  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const code = urlParams.get('code');
    const state = urlParams.get('state');
    const storedState = sessionStorage.getItem('psc_state');
    
    if (state !== storedState) {
      console.error('CSRF state mismatch');
      return;
    }
    
    fetch('/api/v1/french-healthcare/psc/callback', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ code, state })
    })
    .then(res => res.json())
    .then(data => {
      localStorage.setItem('token', data.access_token);
      window.location.href = '/dashboard';
    });
  }, []);
  
  return <div>Authentification en cours...</div>;
};
```

---

## 3. DMP (Dossier Médical Partagé)

### Status

🚧 **En préparation** - Nécessite certification ANS et accès API DMP

### Description

Le DMP est le dossier médical partagé national permettant aux patients de centraliser leurs données de santé et de les partager avec les professionnels de santé.

### Configuration (à venir)

```bash
# .env
DMP_API_URL=https://api-dmp.esante.gouv.fr
DMP_API_KEY=votre_cle_api_dmp
DMP_INTEGRATION_ENABLED=true
```

### Fonctionnalités prévues

- ✅ Enregistrement du consentement patient
- ✅ Envoi de documents vers le DMP
- ✅ Récupération de documents depuis le DMP
- ✅ Synchronisation bidirectionnelle
- ✅ Audit logging des accès DMP

### Modèle de données

```sql
TABLE dmp_integration (
  id UUID PRIMARY KEY,
  patient_id UUID REFERENCES patients(id),
  dmp_id VARCHAR(50) UNIQUE, -- Identifiant DMP (basé sur INS)
  dmp_consent BOOLEAN DEFAULT FALSE,
  dmp_consent_date TIMESTAMP,
  dmp_access_mode VARCHAR(20), -- 'normal', 'urgence', 'bris_de_glace'
  last_sync_at TIMESTAMP,
  documents_sent_count INTEGER DEFAULT 0,
  documents_received_count INTEGER DEFAULT 0,
  last_error TEXT,
  tenant_id UUID NOT NULL,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);
```

### Endpoint status

```http
GET /api/v1/french-healthcare/dmp/status
```

---

## 4. MSSanté (Messagerie Sécurisée de Santé)

### Status

🚧 **En préparation** - Nécessite compte MSSanté certifié

### Description

MSSanté est la messagerie sécurisée de santé permettant l'échange d'informations médicales entre professionnels de santé de manière sécurisée et conforme.

**Format adresse MSSanté**: `prenom.nom@structure.mssante.fr`

### Configuration (à venir)

```bash
# .env
MSSANTE_ENABLED=true
MSSANTE_SMTP_HOST=smtp.mssante.fr
MSSANTE_SMTP_PORT=587
MSSANTE_USERNAME=votre.adresse@structure.mssante.fr
MSSANTE_PASSWORD=votre_mot_de_passe
MSSANTE_FROM_ADDRESS=votre.adresse@structure.mssante.fr
```

### Obtention d'un compte MSSanté

1. **Inscription**
   - URL: https://esante.gouv.fr/produits-services/mssante
   - Demande via votre structure de santé
   - Certification de l'établissement requise

2. **Prérequis**
   - Être un professionnel de santé inscrit (RPPS/ADELI)
   - Avoir une adresse email professionnelle
   - Accepter la charte MSSanté

### Fonctionnalités prévues

- ✅ Envoi de messages sécurisés
- ✅ Réception de messages MSSanté
- ✅ Pièces jointes chiffrées
- ✅ Accusés de réception
- ✅ Synchronisation avec messagerie interne KeneyApp

### Modèle de données

```sql
TABLE mssante_messages (
  id UUID PRIMARY KEY,
  internal_message_id UUID REFERENCES messages(id),
  mssante_message_id VARCHAR(100) UNIQUE,
  sender_mssante_address VARCHAR(200) NOT NULL,
  receiver_mssante_address VARCHAR(200) NOT NULL,
  subject VARCHAR(500),
  sent_at TIMESTAMP,
  received_at TIMESTAMP,
  read_at TIMESTAMP,
  status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'sent', 'delivered', 'read', 'failed'
  error_message TEXT,
  has_attachments BOOLEAN DEFAULT FALSE,
  attachment_count INTEGER DEFAULT 0,
  tenant_id UUID NOT NULL,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);
```

### Endpoint status

```http
GET /api/v1/french-healthcare/mssante/status
```

---

## 5. Migration de base de données

### Appliquer les migrations

```bash
# Vérifier le statut des migrations
python -m alembic current

# Appliquer la migration French Healthcare
python -m alembic upgrade head

# Vérifier que tout est OK
python -m alembic current
```

### Migration créée

- **Fichier**: `alembic/versions/013_french_healthcare.py`
- **Tables**:
  - `patient_ins` - INS des patients
  - `healthcare_professional_cps` - CPS/RPPS des professionnels
  - `dmp_integration` - Intégration DMP
  - `mssante_messages` - Messages MSSanté

---

## 6. Tests et validation

### Tests unitaires

```bash
# Tester la validation INS
pytest tests/services/test_ins_service.py -v

# Tester Pro Santé Connect
pytest tests/services/test_pro_sante_connect.py -v

# Tester les endpoints
pytest tests/routers/test_french_healthcare.py -v
```

### Tests manuels (Postman/curl)

```bash
# 1. Vérifier INS
curl -X POST http://localhost:8000/api/v1/french-healthcare/ins/verify \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": "uuid",
    "ins_number": "184127512345678",
    "birth_name": "DUPONT",
    "first_names": "JEAN",
    "birth_date": "1984-12-25"
  }'

# 2. Obtenir URL PSC
curl http://localhost:8000/api/v1/french-healthcare/psc/authorize

# 3. Status DMP
curl http://localhost:8000/api/v1/french-healthcare/dmp/status

# 4. Status MSSanté
curl http://localhost:8000/api/v1/french-healthcare/mssante/status
```

---

## 7. Sécurité et conformité

### Audit logging

Tous les accès aux données de santé sont loggés:
- Vérification INS
- Authentification PSC
- Accès DMP
- Envoi/réception MSSanté

### Rate limiting

- INS verification: 10/minute
- PSC authorization: 10/minute
- PSC callback: 10/minute
- PSC userinfo: 30/minute

### RGPD

- ✅ Consentement patient pour DMP
- ✅ Droit d'accès aux données
- ✅ Droit de rectification
- ✅ Droit à l'effacement
- ✅ Traçabilité complète

### HDS (Hébergement Données de Santé)

⚠️ **Important**: Pour une mise en production en France, KeneyApp doit être hébergé sur une infrastructure certifiée HDS.

Fournisseurs HDS certifiés:
- OVHcloud
- Scaleway
- AWS (avec engagement HDS)
- Azure (avec engagement HDS)
- Google Cloud (avec engagement HDS)

---

## 8. Roadmap et prochaines étapes

### Q1 2026 (Court terme)

- ✅ INS validation complète
- ✅ Pro Santé Connect OAuth2
- 🚧 Certification ANS pour INS Téléservice
- 🚧 Tests d'intégration avec environnement ANS de test

### Q2 2026 (Moyen terme)

- 🔲 Intégration DMP (envoi/réception documents)
- 🔲 Compte MSSanté et messagerie sécurisée
- 🔲 Certification HDS de l'infrastructure
- 🔲 Profils FHIR Ségur

### Q3 2026 (Long terme)

- 🔲 Ségur vague 2 (identité numérique)
- 🔲 INS Vitale (lecture carte Vitale)
- 🔲 Ordonnance électronique
- 🔲 Carnet de vaccination électronique

---

## 9. Support et ressources

### Documentation ANS

- **Portail industriels**: https://industriels.esante.gouv.fr
- **INS**: https://esante.gouv.fr/produits-services/ins
- **Pro Santé Connect**: https://industriels.esante.gouv.fr/produits-services/pro-sante-connect
- **DMP**: https://esante.gouv.fr/produits-services/dmp
- **MSSanté**: https://esante.gouv.fr/produits-services/mssante
- **Ségur**: https://esante.gouv.fr/segur

### Support KeneyApp

- **Email**: issasanogo2000@gmail.com
- **Documentation**: https://github.com/ngsanogo/keneyapp/docs
- **Issues**: https://github.com/ngsanogo/keneyapp/issues

---

**Version**: 1.0
**Date**: 29 novembre 2025
**Auteur**: Issa Sanogo
**License**: Proprietary
