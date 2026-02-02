# BESIKTNINGSAPP - FILSTRUKTUR

## Komplett projektstruktur

```
besiktnings-app/
│
├── README.md
├── .gitignore
├── .env.example
├── docker-compose.yml
├── docker-compose.prod.yml
├── Makefile
│
├── backend/
│   ├── Dockerfile
│   ├── Dockerfile.prod
│   ├── requirements.txt
│   ├── requirements-dev.txt
│   ├── setup.py
│   ├── pytest.ini
│   ├── .flake8
│   ├── mypy.ini
│   │
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                      # Flask app factory + endpoints
│   │   ├── config.py                    # Konfiguration från env vars (12-factor)
│   │   ├── extensions.py                # SQLAlchemy, Migrate, etc.
│   │   │
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── base.py                  # Base model med revision, timestamps
│   │   │   ├── user.py                  # User/Besiktningsman
│   │   │   ├── property.py              # Fastighet
│   │   │   ├── inspection.py            # Besiktning
│   │   │   ├── apartment.py             # Lägenhet + rum (JSON field)
│   │   │   ├── defect.py                # Felrapport
│   │   │   ├── image.py                 # Bildmetadata
│   │   │   ├── measurement.py           # Mätning
│   │   │   ├── pdf_version.py           # PDF-versionering
│   │   │   ├── sync_log.py              # Sync-logg för idempotens
│   │   │   └── standard_defect.py       # Standardfel (templates)
│   │   │
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py                  # Pydantic schemas för auth
│   │   │   ├── property.py              # Property request/response
│   │   │   ├── inspection.py            # Inspection request/response
│   │   │   ├── apartment.py             # Apartment + rum schemas
│   │   │   ├── defect.py                # Defect request/response
│   │   │   ├── image.py                 # Image metadata schemas
│   │   │   ├── measurement.py           # Measurement schemas
│   │   │   ├── sync.py                  # Sync push/pull schemas
│   │   │   ├── pdf.py                   # PDF request/response
│   │   │   └── common.py                # Gemensamma schemas (pagination, etc)
│   │   │
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── v1/
│   │   │   │   ├── __init__.py          # Blueprint registration
│   │   │   │   ├── auth.py              # /auth/login, /auth/me
│   │   │   │   ├── properties.py        # /properties CRUD
│   │   │   │   ├── inspections.py       # /inspections CRUD
│   │   │   │   ├── apartments.py        # /apartments CRUD
│   │   │   │   ├── defects.py           # /defects CRUD
│   │   │   │   ├── images.py            # /uploads/images, /uploads/presign
│   │   │   │   ├── measurements.py      # /measurements CRUD
│   │   │   │   ├── sync.py              # /sync/handshake, /sync/push, /sync/pull
│   │   │   │   ├── pdf.py               # /pdf/generate, /pdf/versions
│   │   │   │   ├── export.py            # /export endpoints
│   │   │   │   └── health.py            # /health, /ready
│   │   │
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── auth_service.py          # JWT token generation/validation
│   │   │   ├── property_service.py      # Business logic för fastigheter
│   │   │   ├── inspection_service.py    # Business logic för besiktningar
│   │   │   ├── sync_service.py          # Sync-logik (push/pull/conflict)
│   │   │   ├── storage_service.py       # Abstrakt interface för storage
│   │   │   ├── local_storage.py         # Lokal fillagring (dev)
│   │   │   ├── s3_storage.py            # S3/MinIO storage (prod)
│   │   │   ├── pdf_service.py           # PDF-generering + versionering
│   │   │   ├── image_service.py         # Bildhantering + validation
│   │   │   └── conflict_resolver.py     # Konflikthantering för sync
│   │   │
│   │   ├── utils/
│   │   │   ├── __init__.py
│   │   │   ├── validators.py            # Custom validators
│   │   │   ├── decorators.py            # Auth decorators, rate limiting
│   │   │   ├── errors.py                # Custom exceptions
│   │   │   ├── responses.py             # Standardiserade API-responses
│   │   │   ├── logger.py                # Logging setup
│   │   │   └── helpers.py               # Diverse hjälpfunktioner
│   │   │
│   │   └── migrations/
│   │       ├── versions/
│   │       │   ├── 001_initial_schema.py
│   │       │   ├── 002_add_pdf_versioning.py
│   │       │   └── ...
│   │       └── env.py
│   │
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── conftest.py                  # Pytest fixtures
│   │   ├── factories.py                 # Test data factories
│   │   │
│   │   ├── unit/
│   │   │   ├── __init__.py
│   │   │   ├── test_models.py
│   │   │   ├── test_services.py
│   │   │   ├── test_validators.py
│   │   │   └── test_conflict_resolver.py
│   │   │
│   │   ├── integration/
│   │   │   ├── __init__.py
│   │   │   ├── test_auth_api.py
│   │   │   ├── test_property_api.py
│   │   │   ├── test_inspection_api.py
│   │   │   ├── test_sync_api.py
│   │   │   ├── test_pdf_api.py
│   │   │   └── test_image_upload.py
│   │   │
│   │   └── e2e/
│   │       ├── __init__.py
│   │       └── test_full_workflow.py    # Hel arbetsflöde offline->sync
│   │
│   └── scripts/
│       ├── init_db.py                   # DB initialization
│       ├── seed_data.py                 # Seed med testdata
│       └── generate_test_pdfs.py        # Generate test PDFs
│
├── mobile/
│   ├── package.json                     # Om React Native
│   ├── package-lock.json
│   ├── babel.config.js
│   ├── metro.config.js
│   ├── tsconfig.json
│   ├── .eslintrc.js
│   ├── .prettierrc
│   │
│   ├── android/                         # Android-specifikt
│   │   ├── app/
│   │   ├── build.gradle
│   │   └── ...
│   │
│   ├── ios/                             # iOS-specifikt
│   │   ├── Podfile
│   │   ├── BesiktningsApp/
│   │   └── ...
│   │
│   ├── src/
│   │   ├── App.tsx
│   │   ├── index.tsx
│   │   │
│   │   ├── config/
│   │   │   ├── constants.ts
│   │   │   └── api.ts                   # API base URL, timeout, etc
│   │   │
│   │   ├── types/
│   │   │   ├── models.ts                # TypeScript interfaces för domän
│   │   │   ├── api.ts                   # API request/response types
│   │   │   └── navigation.ts            # Navigation types
│   │   │
│   │   ├── database/
│   │   │   ├── schema.ts                # SQLite schema (WatermelonDB/Realm)
│   │   │   ├── models/                  # Local DB models
│   │   │   │   ├── Property.ts
│   │   │   │   ├── Inspection.ts
│   │   │   │   ├── Apartment.ts
│   │   │   │   ├── Defect.ts
│   │   │   │   ├── Image.ts
│   │   │   │   └── SyncOperation.ts     # Outbox för sync
│   │   │   └── migrations/
│   │   │       └── ...
│   │   │
│   │   ├── services/
│   │   │   ├── api/
│   │   │   │   ├── client.ts            # Axios/fetch wrapper
│   │   │   │   ├── auth.ts              # Auth API calls
│   │   │   │   ├── properties.ts        # Property API calls
│   │   │   │   ├── inspections.ts       # Inspection API calls
│   │   │   │   ├── sync.ts              # Sync API calls
│   │   │   │   └── uploads.ts           # Image upload
│   │   │   │
│   │   │   ├── sync/
│   │   │   │   ├── SyncManager.ts       # Central sync orchestration
│   │   │   │   ├── OutboxProcessor.ts   # Process outbox queue
│   │   │   │   ├── ConflictResolver.ts  # Handle conflicts
│   │   │   │   └── NetworkMonitor.ts    # Monitor connectivity
│   │   │   │
│   │   │   ├── storage/
│   │   │   │   ├── SecureStorage.ts     # Keychain/Keystore för tokens
│   │   │   │   ├── FileStorage.ts       # Lokal bildlagring
│   │   │   │   └── CacheManager.ts      # Cache för API responses
│   │   │   │
│   │   │   └── pdf/
│   │   │       └── PdfViewer.ts         # PDF preview functionality
│   │   │
│   │   ├── store/                       # State management (Redux/MobX/Zustand)
│   │   │   ├── index.ts
│   │   │   ├── slices/
│   │   │   │   ├── authSlice.ts
│   │   │   │   ├── propertiesSlice.ts
│   │   │   │   ├── inspectionsSlice.ts
│   │   │   │   ├── syncSlice.ts
│   │   │   │   └── uiSlice.ts
│   │   │   └── hooks.ts
│   │   │
│   │   ├── navigation/
│   │   │   ├── AppNavigator.tsx         # Root navigator
│   │   │   ├── AuthNavigator.tsx        # Auth flow
│   │   │   └── MainNavigator.tsx        # Main app flow
│   │   │
│   │   ├── screens/
│   │   │   ├── auth/
│   │   │   │   └── LoginScreen.tsx
│   │   │   │
│   │   │   ├── properties/
│   │   │   │   ├── PropertyListScreen.tsx
│   │   │   │   ├── PropertyDetailScreen.tsx
│   │   │   │   └── PropertyFormScreen.tsx
│   │   │   │
│   │   │   ├── inspections/
│   │   │   │   ├── InspectionListScreen.tsx
│   │   │   │   ├── InspectionDetailScreen.tsx
│   │   │   │   ├── InspectionFormScreen.tsx
│   │   │   │   └── InspectionActiveScreen.tsx  # Timer + real-time
│   │   │   │
│   │   │   ├── apartments/
│   │   │   │   ├── ApartmentListScreen.tsx
│   │   │   │   ├── ApartmentFormScreen.tsx
│   │   │   │   └── RoomManagerScreen.tsx       # Hantera rum
│   │   │   │
│   │   │   ├── defects/
│   │   │   │   ├── DefectListScreen.tsx
│   │   │   │   ├── DefectFormScreen.tsx
│   │   │   │   └── DefectCameraScreen.tsx      # Ta bilder
│   │   │   │
│   │   │   ├── measurements/
│   │   │   │   └── MeasurementFormScreen.tsx
│   │   │   │
│   │   │   ├── sync/
│   │   │   │   ├── SyncStatusScreen.tsx        # Visa sync-status
│   │   │   │   └── ConflictResolverScreen.tsx  # Manuell konfliktlösning
│   │   │   │
│   │   │   ├── pdf/
│   │   │   │   ├── PdfPreviewScreen.tsx
│   │   │   │   └── PdfVersionsScreen.tsx
│   │   │   │
│   │   │   └── settings/
│   │   │       ├── SettingsScreen.tsx
│   │   │       ├── ProfileScreen.tsx
│   │   │       └── AboutScreen.tsx
│   │   │
│   │   ├── components/
│   │   │   ├── common/
│   │   │   │   ├── Button.tsx
│   │   │   │   ├── Input.tsx
│   │   │   │   ├── Card.tsx
│   │   │   │   ├── LoadingSpinner.tsx
│   │   │   │   ├── ErrorBoundary.tsx
│   │   │   │   └── OfflineBanner.tsx
│   │   │   │
│   │   │   ├── forms/
│   │   │   │   ├── PropertyForm.tsx
│   │   │   │   ├── InspectionForm.tsx
│   │   │   │   ├── ApartmentForm.tsx
│   │   │   │   ├── DefectForm.tsx
│   │   │   │   └── RoomSelector.tsx
│   │   │   │
│   │   │   ├── lists/
│   │   │   │   ├── PropertyList.tsx
│   │   │   │   ├── InspectionList.tsx
│   │   │   │   ├── DefectList.tsx
│   │   │   │   └── SyncQueueList.tsx
│   │   │   │
│   │   │   └── sync/
│   │   │       ├── SyncButton.tsx
│   │   │       ├── SyncStatusIndicator.tsx
│   │   │       └── ConflictCard.tsx
│   │   │
│   │   ├── hooks/
│   │   │   ├── useAuth.ts
│   │   │   ├── useSync.ts
│   │   │   ├── useNetworkStatus.ts
│   │   │   ├── useCamera.ts
│   │   │   └── useTimer.ts                     # För aktiv tid
│   │   │
│   │   └── utils/
│   │       ├── validation.ts
│   │       ├── formatting.ts
│   │       ├── sorting.ts
│   │       ├── uuid.ts                         # UUID generation
│   │       └── logger.ts
│   │
│   └── __tests__/
│       ├── unit/
│       │   ├── services/
│       │   ├── utils/
│       │   └── components/
│       │
│       └── integration/
│           └── sync/
│
├── k8s/                                         # Kubernetes manifests
│   ├── namespace.yaml
│   ├── configmap.yaml
│   ├── secret.yaml
│   │
│   ├── postgres/
│   │   ├── pvc.yaml                            # Persistent Volume Claim
│   │   ├── deployment.yaml
│   │   └── service.yaml
│   │
│   ├── minio/                                  # Object storage (optional)
│   │   ├── pvc.yaml
│   │   ├── deployment.yaml
│   │   └── service.yaml
│   │
│   ├── backend/
│   │   ├── pvc.yaml                            # För lokal fillagring (alt till MinIO)
│   │   ├── deployment.yaml                     # Med probes, env, volumes
│   │   ├── service.yaml
│   │   ├── ingress.yaml
│   │   └── hpa.yaml                            # Horizontal Pod Autoscaler
│   │
│   └── monitoring/                             # Optional men rekommenderat
│       ├── prometheus.yaml
│       └── grafana.yaml
│
├── docs/
│   ├── API.md                                  # API-dokumentation
│   ├── SYNC.md                                 # Sync-arkitektur och flow
│   ├── DEPLOYMENT.md                           # Deployment guide
│   ├── DEVELOPMENT.md                          # Dev setup
│   ├── ARCHITECTURE.md                         # Systemarkitektur
│   ├── SECURITY.md                             # Security considerations
│   └── images/
│       ├── architecture-diagram.png
│       ├── sync-flow.png
│       └── er-diagram.png
│
└── scripts/
    ├── deploy-dev.sh                           # Deploy till dev
    ├── deploy-prod.sh                          # Deploy till prod
    ├── backup-db.sh                            # DB backup script
    └── restore-db.sh                           # DB restore script
```

## VIKTIGA DESIGNVAL

### Backend struktur
1. **Modulär service-layer**: Separerar business logic från API-endpoints
2. **Repository pattern**: Implicit via SQLAlchemy models, men kan extraheras vid behov
3. **Storage abstraction**: Interface som stöder både lokal disk och S3/MinIO
4. **Pydantic schemas**: För validering och serialisering (type-safe)

### Sync arkitektur
1. **Outbox pattern**: Append-only logg på klienten
2. **UUID-baserade client_id**: Klienten genererar UUID som mappas till server-id
3. **Revision-baserad konflikthantering**: Optimistisk låsning
4. **Idempotens**: X-Idempotency-Key + sync_log table

### PDF versionering
1. **Immutable versions**: Varje generering skapar ny version
2. **Metadata tracking**: versionnr, status, checksum, storage_path
3. **"Latest" via query**: Högsta versionnr eller senaste created_at

### Mobile arkitektur
1. **Offline-first**: Lokal SQLite/WatermelonDB som "source of truth"
2. **Background sync**: NetworkMonitor + OutboxProcessor
3. **State management**: Redux/Zustand för UI state
4. **Typed API client**: TypeScript interfaces matchar backend schemas

### Driftsättning
1. **Stateless backend**: All state i DB eller object storage
2. **Health probes**: /health (liveness) och /ready (readiness)
3. **12-factor app**: Config via env vars, secrets via K8s secrets
4. **Horizontal scaling**: Stateless design möjliggör HPA

### Security
1. **JWT auth**: Bearer tokens med exp
2. **Input validation**: Pydantic på backend, Yup/Zod på frontend
3. **File upload limits**: Max size, allowed types, sanitized filenames
4. **SQL injection**: Parametriserade queries via SQLAlchemy
5. **Path traversal**: Validering av filnamn och paths

## FILSTRUKTUR RATIONALE

### Backend (/backend)
- **app/models/**: En model per fil, arv från base.py för common fields
- **app/schemas/**: Pydantic schemas separerade från models för tydlighet
- **app/api/v1/**: Versioned API, enkel att lägga till v2 senare
- **app/services/**: Business logic isolerad från HTTP-layer
- **tests/**: Separerade unit/integration/e2e för olika test-scope

### Mobile (/mobile)
- **database/models/**: Local-first models, kan vara lite olika från backend
- **services/sync/**: Komplex sync-logik isolerad i egen modul
- **screens/**: Feature-baserad struktur (properties, inspections, etc)
- **components/**: Reusable components uppdelade efter typ

### K8s (/k8s)
- **Per-service directories**: Separata manifests för varje service
- **Base + overlays**: Kan utökas med Kustomize för dev/staging/prod
- **PVC**: För persistent data (DB, files om inte S3)

### Docs (/docs)
- **Comprehensive docs**: API, sync, deployment, security
- **Diagrams**: Visuell dokumentation för arkitektur

## NÄSTA STEG

1. **Implementera base models + schemas** (backend foundation)
2. **Skapa auth endpoints + JWT** (authentication)
3. **Implementera core CRUD** (properties, inspections, apartments, defects)
4. **Bygga sync service** (push/pull/conflict resolution)
5. **PDF-generering + versionering**
6. **Mobile scaffold + database**
7. **Mobile sync implementation**
8. **Docker + K8s setup**
9. **Testing + CI/CD**
10. **Documentation + deployment guides**

## TEKNOLOGI STACK SAMMANFATTNING

**Backend:**
- Python 3.11+
- Flask 3.x
- SQLAlchemy 2.x + Alembic
- Pydantic 2.x
- PyJWT
- Boto3 (för S3/MinIO)
- ReportLab eller WeasyPrint (PDF)
- Pytest + pytest-cov
- Gunicorn (production WSGI)

**Mobile:**
- React Native
- TypeScript
- WatermelonDB eller Realm (offline DB)
- Redux Toolkit eller Zustand (state)
- React Navigation
- Axios
- React Native Camera
- React Native PDF (viewing)
- Jest + React Native Testing Library

**Infrastructure:**
- Docker + Docker Compose
- Kubernetes
- PostgreSQL 15+
- MinIO eller S3 (object storage)
- Nginx (ingress)

**Dev Tools:**
- ESLint + Prettier (mobile)
- Black + Flake8 + mypy (backend)
- GitHub Actions eller GitLab CI
- Sentry (error tracking)
- Prometheus + Grafana (monitoring)
