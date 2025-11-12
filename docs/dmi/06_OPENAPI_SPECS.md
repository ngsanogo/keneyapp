# Spécifications OpenAPI - DMI

## 1. Vue d'Ensemble

### 1.1 Informations Générales

```yaml
openapi: 3.1.0
info:
  title: KeneyApp DMI API
  version: 1.0.0
  description: |
    API du Dossier Médical Informatisé (DMI) de KeneyApp.

    Cette API fournit un accès sécurisé aux fonctionnalités suivantes :
    - Gestion des patients (identito-vigilance)
    - Consultations et observations
    - Prescriptions médicamenteuses
    - Examens de laboratoire et imagerie
    - Documents médicaux
    - Messagerie sécurisée

    **Standards supportés** :
    - FHIR R4 (HL7)
    - Terminologies : LOINC, SNOMED CT, CIM-10, ATC, CCAM/CPT
    - Sécurité : OAuth2/OIDC, RBAC/ABAC
    - Conformité : RGPD, HDS, HIPAA

  contact:
    name: Support Technique KeneyApp
    email: support@keneyapp.com
    url: https://keneyapp.com/support
  license:
    name: Proprietary
    url: https://keneyapp.com/license

servers:
  - url: https://api.keneyapp.com/v1
    description: Production
  - url: https://api-staging.keneyapp.com/v1
    description: Staging
  - url: http://localhost:8000/api/v1
    description: Développement local

security:
  - BearerAuth: []
  - OAuth2: [read, write]

tags:
  - name: Patients
    description: Gestion identito-vigilance et dossiers patients
  - name: Encounters
    description: Consultations et admissions
  - name: Observations
    description: Constantes vitales et résultats cliniques
  - name: Medications
    description: Prescriptions et administration médicamenteuse
  - name: Laboratory
    description: Demandes et résultats d'analyses biologiques
  - name: Documents
    description: Gestion documents médicaux
  - name: Appointments
    description: Gestion agenda et rendez-vous
  - name: FHIR
    description: Endpoints conformes FHIR R4
  - name: Audit
    description: Consultation logs d'audit
```

### 1.2 Authentification

```yaml
components:
  securitySchemes:
    BearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT
      description: |
        Authentification JWT. Token obtenu via `/auth/login`.

        **Format header** : `Authorization: Bearer <token>`

        **Durée validité** :
        - Access token : 30 minutes
        - Refresh token : 7 jours

        **Claims JWT** :
        ```json
        {
          "sub": "user-uuid",
          "email": "dr.martin@hospital.fr",
          "role": "MEDECIN",
          "tenant_id": "tenant-uuid",
          "rpps": "12345678901",
          "iat": 1704902400,
          "exp": 1704904200
        }
        ```

    OAuth2:
      type: oauth2
      flows:
        authorizationCode:
          authorizationUrl: https://auth.keneyapp.com/oauth/authorize
          tokenUrl: https://auth.keneyapp.com/oauth/token
          refreshUrl: https://auth.keneyapp.com/oauth/refresh
          scopes:
            read: Lecture données
            write: Écriture données
            admin: Administration
            patient: Accès portail patient
```

## 2. Endpoints Patients

### 2.1 Recherche Patient

```yaml
/patients/search:
  get:
    tags: [Patients]
    summary: Rechercher des patients
    description: |
      Recherche patients par différents critères.

      **Cas d'usage** :
      - Recherche par INS (identifiant national santé)
      - Recherche nominative (nom, prénom, date naissance)
      - Recherche par IPP (identifiant patient provisoire)

      **Détection doublons** : Score de similarité retourné si > 85%

    operationId: searchPatients
    parameters:
      - name: ins
        in: query
        description: Numéro INS (15 chiffres)
        schema:
          type: string
          pattern: '^\d{15}$'
          example: "184127512345678"

      - name: nom
        in: query
        description: Nom de famille (sensible à la casse)
        schema:
          type: string
          minLength: 2
          maxLength: 50
          example: "MARTIN"

      - name: prenom
        in: query
        description: Prénom
        schema:
          type: string
          minLength: 2
          maxLength: 50
          example: "Jean"

      - name: date_naissance
        in: query
        description: Date de naissance (ISO 8601)
        schema:
          type: string
          format: date
          example: "1984-12-07"

      - name: ipp
        in: query
        description: Identifiant Patient Provisoire
        schema:
          type: string
          example: "123456780"

      - name: limit
        in: query
        description: Nombre max résultats
        schema:
          type: integer
          minimum: 1
          maximum: 100
          default: 20

      - name: offset
        in: query
        description: Offset pagination
        schema:
          type: integer
          minimum: 0
          default: 0

    responses:
      '200':
        description: Recherche réussie
        content:
          application/json:
            schema:
              type: object
              properties:
                total:
                  type: integer
                  example: 1
                patients:
                  type: array
                  items:
                    $ref: '#/components/schemas/Patient'
                potential_duplicates:
                  type: array
                  description: Doublons potentiels détectés (score > 85%)
                  items:
                    type: object
                    properties:
                      patient:
                        $ref: '#/components/schemas/Patient'
                      similarity_score:
                        type: number
                        format: float
                        minimum: 0
                        maximum: 100
                        example: 92.5
            examples:
              success:
                value:
                  total: 1
                  patients:
                    - id: "550e8400-e29b-41d4-a716-446655440000"
                      ipp: "123456780"
                      ins: "184127512345678"
                      ins_status: "VALIDATED"
                      nom: "MARTIN"
                      prenom: "Jean"
                      date_naissance: "1984-12-07"
                      sexe: "M"
                      status: "ACTIVE"
                  potential_duplicates: []

      '400':
        description: Paramètres invalides
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/Error'
            example:
              error: "INVALID_PARAMETERS"
              message: "Format INS invalide. Attendu : 15 chiffres"
              details:
                field: "ins"
                constraint: "pattern"

      '401':
        $ref: '#/components/responses/Unauthorized'

      '403':
        $ref: '#/components/responses/Forbidden'

      '429':
        $ref: '#/components/responses/RateLimitExceeded'

    security:
      - BearerAuth: []

    x-rate-limit: "60/minute"
    x-audit-log: true
    x-required-role: ["MEDECIN", "IDE", "SECRETAIRE", "ADMIN"]
```

### 2.2 Créer Patient

```yaml
/patients:
  post:
    tags: [Patients]
    summary: Créer un nouveau patient
    description: |
      Crée un nouveau dossier patient avec validation INS.

      **Workflow** :
      1. Validation format données (côté client + serveur)
      2. Interrogation téléservice INS (si INS fourni)
      3. Détection doublons (algorithme Levenshtein + date naissance)
      4. Si doublon score > 85% → alerte retournée
      5. Création patient avec statut VALIDATED ou PROVISOIRE
      6. Génération IPP unique
      7. Publication événement `PatientCreated`

      **INS Provisoire** :
      - Autorisé en urgence
      - Régularisation obligatoire sous 48h
      - Flag `ins_status: PROVISOIRE`

    operationId: createPatient
    requestBody:
      required: true
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/PatientCreate'
          examples:
            patient_valide:
              value:
                ins: "184127512345678"
                nom: "MARTIN"
                prenom: "Jean"
                date_naissance: "1984-12-07"
                sexe: "M"
                adresse: "12 rue de la Paix, 75001 Paris"
                telephone: "+33612345678"
                email: "jean.martin@example.com"

            patient_provisoire:
              value:
                ins_status: "PROVISOIRE"
                nom: "DUPONT"
                prenom: "Marie"
                date_naissance: "1990-03-15"
                sexe: "F"
                telephone: "+33698765432"

    responses:
      '201':
        description: Patient créé avec succès
        headers:
          Location:
            schema:
              type: string
            description: URL du patient créé
            example: /patients/550e8400-e29b-41d4-a716-446655440000
        content:
          application/json:
            schema:
              type: object
              properties:
                patient:
                  $ref: '#/components/schemas/Patient'
                warnings:
                  type: array
                  description: Avertissements (ex: doublons potentiels)
                  items:
                    type: object
                    properties:
                      code:
                        type: string
                        enum: [POTENTIAL_DUPLICATE, INS_NOT_VALIDATED]
                      message:
                        type: string
                      severity:
                        type: string
                        enum: [LOW, MEDIUM, HIGH]
                      potential_duplicate:
                        $ref: '#/components/schemas/Patient'
            example:
              patient:
                id: "550e8400-e29b-41d4-a716-446655440000"
                ipp: "123456780"
                ins: "184127512345678"
                ins_status: "VALIDATED"
                nom: "MARTIN"
                prenom: "Jean"
                date_naissance: "1984-12-07"
                sexe: "M"
                status: "ACTIVE"
                created_at: "2025-01-10T14:30:00Z"
              warnings: []

      '202':
        description: Patient créé avec avertissements (doublons potentiels)
        content:
          application/json:
            schema:
              type: object
              properties:
                patient:
                  $ref: '#/components/schemas/Patient'
                warnings:
                  type: array
                  items:
                    type: object
                    properties:
                      code:
                        type: string
                      message:
                        type: string
                      severity:
                        type: string
                      potential_duplicate:
                        $ref: '#/components/schemas/Patient'
            example:
              patient:
                id: "new-patient-uuid"
                ipp: "987654321"
                ins_status: "PROVISOIRE"
                nom: "MARTIN"
                prenom: "Jean"
                date_naissance: "1984-12-07"
                sexe: "M"
                status: "ACTIVE"
              warnings:
                - code: "POTENTIAL_DUPLICATE"
                  message: "Patient similaire détecté"
                  severity: "HIGH"
                  potential_duplicate:
                    id: "existing-patient-uuid"
                    ipp: "123456780"
                    ins: "184127512345678"
                    nom: "MARTIN"
                    prenom: "Jean"
                    date_naissance: "1984-12-07"

      '400':
        $ref: '#/components/responses/BadRequest'

      '401':
        $ref: '#/components/responses/Unauthorized'

      '403':
        $ref: '#/components/responses/Forbidden'

      '409':
        description: Conflit - Patient déjà existant
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/Error'
            example:
              error: "PATIENT_ALREADY_EXISTS"
              message: "Un patient avec cet INS existe déjà"
              details:
                existing_patient_id: "550e8400-e29b-41d4-a716-446655440000"

      '429':
        $ref: '#/components/responses/RateLimitExceeded'

      '503':
        description: Service externe indisponible (téléservice INS)
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/Error'
            example:
              error: "EXTERNAL_SERVICE_UNAVAILABLE"
              message: "Téléservice INS temporairement indisponible"
              details:
                service: "INS"
                fallback: "Patient créé en mode dégradé (INS PROVISOIRE)"

    security:
      - BearerAuth: []

    x-rate-limit: "20/minute"
    x-audit-log: true
    x-required-role: ["MEDECIN", "IDE", "SECRETAIRE", "ADMIN"]
```

### 2.3 Lire Patient

```yaml
/patients/{id}:
  get:
    tags: [Patients]
    summary: Récupérer un patient par ID
    description: |
      Récupère les informations complètes d'un patient.

      **Contrôle d'accès** :
      - Médecin : Autorisé si dans équipe de soins ou Break-the-Glass
      - IDE : Autorisé si patient du service assigné
      - Secrétaire : Autorisé (lecture seule, données limitées)
      - Pharmacien : Autorisé (contexte prescription)
      - DIM : Refusé (accès données pseudonymisées uniquement)

      **Audit** :
      - Toute lecture tracée dans audit log
      - Break-the-Glass → notification DPO immédiate

    operationId: getPatient
    parameters:
      - name: id
        in: path
        required: true
        description: ID unique du patient (UUID)
        schema:
          type: string
          format: uuid
          example: "550e8400-e29b-41d4-a716-446655440000"

      - name: include
        in: query
        description: |
          Relations à inclure (comma-separated).
          Options : allergies, medications, encounters, observations, documents
        schema:
          type: string
          example: "allergies,medications"

      - name: break_the_glass
        in: query
        description: Accès d'urgence (justification requise)
        schema:
          type: boolean
          default: false

      - name: btg_justification
        in: query
        description: Justification Break-the-Glass (obligatoire si btg=true)
        schema:
          type: string
          minLength: 20
          example: "Urgence vitale - arrêt cardiaque - besoin antécédents"

    responses:
      '200':
        description: Patient trouvé
        content:
          application/json:
            schema:
              type: object
              properties:
                patient:
                  $ref: '#/components/schemas/PatientDetailed'
                _embedded:
                  type: object
                  description: Relations incluses
                  properties:
                    allergies:
                      type: array
                      items:
                        $ref: '#/components/schemas/Allergy'
                    medications:
                      type: array
                      items:
                        $ref: '#/components/schemas/MedicationSummary'
            example:
              patient:
                id: "550e8400-e29b-41d4-a716-446655440000"
                ipp: "123456780"
                ins: "184127512345678"
                ins_status: "VALIDATED"
                nom: "MARTIN"
                prenom: "Jean"
                date_naissance: "1984-12-07"
                sexe: "M"
                adresse: "12 rue de la Paix, 75001 Paris"
                telephone: "+33612345678"
                email: "jean.martin@example.com"
                status: "ACTIVE"
                created_at: "2020-01-15T10:00:00Z"
                updated_at: "2025-01-10T14:30:00Z"
              _embedded:
                allergies:
                  - id: "allergy-uuid"
                    allergen_code: "387207008"
                    allergen_display: "Pénicilline"
                    severity: "HIGH"
                    verification_status: "CONFIRMED"
                medications:
                  - id: "med-uuid"
                    medication_display: "DOLIPRANE 1000mg"
                    status: "ACTIVE"
                    start_date: "2025-01-05"

      '403':
        description: Accès refusé - Hors périmètre autorisé
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/Error'
            example:
              error: "ACCESS_DENIED"
              message: "Vous n'êtes pas autorisé à accéder à ce patient"
              details:
                reason: "Patient hors de votre équipe de soins"
                break_the_glass_available: true
                btg_warning: "Accès tracé et notifié au DPO"

      '404':
        $ref: '#/components/responses/NotFound'

      '401':
        $ref: '#/components/responses/Unauthorized'

    security:
      - BearerAuth: []

    x-rate-limit: "120/minute"
    x-audit-log: true
    x-required-role: ["MEDECIN", "IDE", "PHARMACIEN", "SECRETAIRE"]
```

## 3. Endpoints Prescriptions

### 3.1 Créer Prescription

```yaml
/medications/prescriptions:
  post:
    tags: [Medications]
    summary: Créer une prescription médicamenteuse
    description: |
      Crée une nouvelle prescription avec vérifications automatiques :
      - Analyse interactions médicamenteuses
      - Vérification allergies patient
      - Adaptation posologie (fonction rénale, poids, âge)
      - Détection contre-indications

      **Niveaux d'alerte** :
      - INFO : Information (pas de blocage)
      - PRÉCAUTION : Précaution (confirmation médecin)
      - CONTRE-INDICATION : Contre-indication relative (justification obligatoire)
      - ALLERGIE : Allergie patient (blocage, contact pharmacien requis)

    operationId: createPrescription
    requestBody:
      required: true
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/PrescriptionCreate'
          example:
            patient_id: "patient-uuid"
            encounter_id: "encounter-uuid"
            medication_code: "3400936404649"
            dosage_text: "1 comprimé 3 fois par jour pendant 5 jours"
            dosage:
              dose_quantity: 1.0
              dose_unit: "{tablet}"
              frequency: "3x/day"
              route: "PO"
            duration:
              value: 5
              unit: "days"
            priority: "ROUTINE"
            clinical_context: "Douleurs post-opératoires modérées"

    responses:
      '201':
        description: Prescription créée
        content:
          application/json:
            schema:
              type: object
              properties:
                prescription:
                  $ref: '#/components/schemas/Prescription'
                alerts:
                  type: array
                  items:
                    $ref: '#/components/schemas/DrugAlert'
            examples:
              no_alerts:
                value:
                  prescription:
                    id: "prescription-uuid"
                    status: "ACTIVE"
                    medication_display: "DOLIPRANE 1000mg"
                    created_at: "2025-01-10T15:00:00Z"
                  alerts: []

              with_interaction:
                value:
                  prescription:
                    id: "prescription-uuid"
                    status: "PENDING_VALIDATION"
                    medication_display: "ASPIRINE 100mg"
                  alerts:
                    - level: "CONTRE_INDICATION"
                      type: "DRUG_INTERACTION"
                      message: "Interaction majeure avec Warfarine"
                      description: "Risque hémorragique augmenté"
                      interacting_medication: "WARFARINE 5mg"
                      recommendation: "Surveillance INR rapprochée si maintien"
                      alternatives:
                        - medication_code: "3400912345678"
                          medication_display: "PARACÉTAMOL 1000mg"
                          reason: "Pas d'interaction, même indication"

      '400':
        $ref: '#/components/responses/BadRequest'

      '409':
        description: Allergie patient - Prescription bloquée
        content:
          application/json:
            schema:
              type: object
              properties:
                error:
                  type: string
                message:
                  type: string
                allergy:
                  $ref: '#/components/schemas/Allergy'
                action_required:
                  type: string
            example:
              error: "ALLERGY_CONTRAINDICATION"
              message: "Patient allergique à la Pénicilline"
              allergy:
                allergen_code: "387207008"
                allergen_display: "Pénicilline"
                severity: "HIGH"
                verification_status: "CONFIRMED"
              action_required: "Contacter pharmacien ou choisir alternative"

    security:
      - BearerAuth: []

    x-rate-limit: "30/minute"
    x-audit-log: true
    x-required-role: ["MEDECIN"]
```

## 4. Schémas de Données

```yaml
components:
  schemas:
    Patient:
      type: object
      required: [id, ipp, nom, prenom, date_naissance, sexe, status]
      properties:
        id:
          type: string
          format: uuid
          description: Identifiant unique patient
        ipp:
          type: string
          pattern: '^\d{9}$'
          description: Identifiant Patient Provisoire (9 chiffres + clé Luhn)
          example: "123456780"
        ins:
          type: string
          pattern: '^\d{15}$'
          description: Identifiant National Santé (15 chiffres)
          example: "184127512345678"
        ins_status:
          type: string
          enum: [VALIDATED, PROVISOIRE, UNKNOWN]
          description: Statut validation INS
        nom:
          type: string
          minLength: 2
          maxLength: 50
          description: Nom de famille (majuscules)
          example: "MARTIN"
        prenom:
          type: string
          minLength: 2
          maxLength: 50
          description: Prénom
          example: "Jean"
        date_naissance:
          type: string
          format: date
          description: Date de naissance (ISO 8601)
          example: "1984-12-07"
        sexe:
          type: string
          enum: [M, F, I, U]
          description: |
            Sexe :
            - M : Masculin
            - F : Féminin
            - I : Indéterminé
            - U : Inconnu
        adresse:
          type: string
          maxLength: 200
          description: Adresse postale (chiffrée)
        telephone:
          type: string
          pattern: '^\+\d{1,15}$'
          description: Téléphone (format E.164, chiffré)
          example: "+33612345678"
        email:
          type: string
          format: email
          maxLength: 100
          description: Email (chiffré)
        status:
          type: string
          enum: [ACTIVE, INACTIVE, DECEASED]
        created_at:
          type: string
          format: date-time
          readOnly: true
        updated_at:
          type: string
          format: date-time
          readOnly: true

    PatientCreate:
      type: object
      required: [nom, prenom, date_naissance, sexe]
      properties:
        ins:
          type: string
          pattern: '^\d{15}$'
        ins_status:
          type: string
          enum: [VALIDATED, PROVISOIRE]
          default: VALIDATED
        nom:
          type: string
          minLength: 2
          maxLength: 50
        prenom:
          type: string
          minLength: 2
          maxLength: 50
        date_naissance:
          type: string
          format: date
        sexe:
          type: string
          enum: [M, F, I, U]
        adresse:
          type: string
          maxLength: 200
        telephone:
          type: string
          pattern: '^\+\d{1,15}$'
        email:
          type: string
          format: email
          maxLength: 100

    Prescription:
      type: object
      properties:
        id:
          type: string
          format: uuid
        patient_id:
          type: string
          format: uuid
        medication_code:
          type: string
          description: Code CIP ou UCD
        medication_display:
          type: string
          description: Nom commercial + dosage
        atc_code:
          type: string
          pattern: '^[A-Z]\d{2}[A-Z]{2}\d{2}$'
          description: Code ATC niveau 5
        dosage_text:
          type: string
          description: Instructions posologie (texte libre)
        status:
          type: string
          enum: [DRAFT, ACTIVE, ON_HOLD, CANCELLED, COMPLETED]
        pharmacy_validation_status:
          type: string
          enum: [PENDING, VALIDATED, ADAPTED, REFUSED]
        authored_on:
          type: string
          format: date-time
        prescriber_id:
          type: string
          format: uuid

    DrugAlert:
      type: object
      properties:
        level:
          type: string
          enum: [INFO, PRÉCAUTION, CONTRE_INDICATION, ALLERGIE]
        type:
          type: string
          enum: [DRUG_INTERACTION, ALLERGY, CONTRAINDICATION, DOSAGE_ADAPTATION]
        message:
          type: string
          description: Message court
        description:
          type: string
          description: Description détaillée
        recommendation:
          type: string
          description: Recommandation clinique
        alternatives:
          type: array
          items:
            type: object
            properties:
              medication_code:
                type: string
              medication_display:
                type: string
              reason:
                type: string

    Error:
      type: object
      required: [error, message]
      properties:
        error:
          type: string
          description: Code erreur
          enum:
            - INVALID_PARAMETERS
            - PATIENT_NOT_FOUND
            - PATIENT_ALREADY_EXISTS
            - ACCESS_DENIED
            - UNAUTHORIZED
            - ALLERGY_CONTRAINDICATION
            - EXTERNAL_SERVICE_UNAVAILABLE
        message:
          type: string
          description: Message erreur lisible
        details:
          type: object
          description: Détails additionnels
        timestamp:
          type: string
          format: date-time
        correlation_id:
          type: string
          format: uuid
          description: ID corrélation pour traçage

  responses:
    BadRequest:
      description: Requête invalide
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/Error'

    Unauthorized:
      description: Non authentifié
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/Error'

    Forbidden:
      description: Accès interdit
      content:
        application/json:
            $ref: '#/components/schemas/Error'

    NotFound:
      description: Ressource non trouvée
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/Error'

    RateLimitExceeded:
      description: Limite de taux dépassée
      headers:
        X-Rate-Limit-Limit:
          schema:
            type: integer
          description: Limite de requêtes
        X-Rate-Limit-Remaining:
          schema:
            type: integer
          description: Requêtes restantes
        X-Rate-Limit-Reset:
          schema:
            type: integer
          description: Timestamp reset (Unix epoch)
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/Error'
```

---

**Document validé par** : Tech Lead, Architecte API
**Date** : 2025-01-10
**Version** : 1.0
**Prochaine revue** : 2025-02-10
