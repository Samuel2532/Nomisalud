# NOMISALUD — Project Context for Claude Code

> Copy this file into your project root as `CLAUDE.md` so Claude Code automatically reads it.

---

## 1. PROJECT OVERVIEW

**Nomisalud** is a Colombian web platform for managing medical incapacities (sick leave certificates) of common and work origin. It connects employees, HR departments, EPS (health insurance) and ARL (work risk) entities through a unified digital workflow with OCR processing, AI classification, state machine tracking, deadline alerts, and financial conciliation.

**Course:** Ingeniería de Software I — February 2026
**Team:** Jean Paul Bedoya, Samuel Parra Murillo, Sebastian Barco Correa, Brayan Armando Chiquito Posso

---

## 2. CURRENT TECH STACK

| Layer | Technology | Notes |
|-------|-----------|-------|
| Backend | Flask 3.1.3 (Python 3.12) | Originally spec'd for FastAPI — adapted due to environment constraints |
| Database | SQLite3 (via `sqlite3` stdlib) | Spec calls for PostgreSQL 14+ — migration pending |
| Auth | Session-based + PyJWT 2.7.0 | Werkzeug password hashing |
| Frontend | Jinja2 templates + vanilla JS | Spec calls for React.js 18 + TailwindCSS — migration pending |
| File upload | Werkzeug `secure_filename` | PDF, JPG, PNG; max 5MB |
| OCR | **Simulated** | Returns realistic fake text; spec requires Tesseract.js >85% precision |
| AI Classification | **Simulated** | Returns fake classification; spec requires Claude API >90% accuracy |
| Encryption | Not yet implemented | Spec requires AES-256 for documents at rest |
| Fonts | Google Fonts (DM Serif Display + Plus Jakarta Sans) | Loaded via CDN |

---

## 3. PROJECT STRUCTURE

```
nomisalud/
├── app.py                 # Flask app — all routes, API endpoints, helpers
├── models.py              # SQLite schema, init_db(), seed data, log_audit()
├── requirements.txt       # Python dependencies
├── README.md              # Setup + deploy instructions
├── nomisalud.db           # SQLite database (auto-created on first run)
├── .gitignore
├── templates/
│   ├── index.html         # Landing page (marketing)
│   ├── login.html         # Login page with demo account buttons
│   └── dashboard.html     # Main SPA — dashboard, incapacidades list, audit log
└── static/
    └── uploads/           # Uploaded documents stored here
```

---

## 4. DATABASE SCHEMA

8 tables in SQLite. All primary keys are UUID v4 strings. Dates stored as ISO 8601 text.

### entidades_salud
Health entities (EPS/ARL) with differentiated deadlines.
- `id` TEXT PK, `nombre`, `tipo` ('EPS'|'ARL'), `nit` UNIQUE, `plazo_max_dias` INT, `email_contacto`, `activa` BOOL

**Seeded entities and their deadlines:**
| Entity | Type | NIT | Plazo (days) |
|--------|------|-----|-------------|
| Salud Total | EPS | 800130907 | 365 |
| Nueva EPS | EPS | 900156264 | 365 |
| SOS | EPS | 805001157 | 365 |
| Sanitas | EPS | 800251440 | 1095 (3 years) |
| SURA EPS | EPS | 800088702 | 150 |
| Asmet Salud | EPS | 900074994 | 365 |
| ARL SURA | ARL | 890903790 | 730 |

### usuarios
- `id`, `nombre`, `apellido`, `email` UNIQUE, `password_hash`, `rol`, `activo`, `fecha_creacion`, `ultimo_acceso`
- Roles: `COLABORADOR`, `RECEPCION`, `AUXILIAR_RRHH`, `COORDINADOR_RRHH`, `CONTABILIDAD`

### colaboradores
Employee profiles linked to usuarios.
- `id`, `usuario_id` FK→usuarios UNIQUE, `cedula` UNIQUE, `cargo`, `area`, `fecha_ingreso`, `eps_id` FK, `arl_id` FK, `telefono`

### incapacidades
Core entity — the medical incapacity record.
- `id`, `colaborador_id` FK, `tipo`, `origen` ('COMUN'|'LABORAL'), `estado`, `fecha_inicio`, `fecha_fin`, `dias_incapacidad`, `diagnostico_cie10`, `entidad_emisora_id` FK, `fecha_recepcion`, `fecha_vencimiento_plazo`, `observaciones`, `creado_por_id` FK, `created_at`, `updated_at`
- Types: `ENFERMEDAD_COMUN`, `ACCIDENTE_LABORAL`, `ENFERMEDAD_LABORAL`, `LICENCIA_MATERNIDAD`, `LICENCIA_PATERNIDAD`

### documentos
Uploaded files with OCR/AI processing results.
- `id`, `incapacidad_id` FK, `tipo_documento`, `ruta_archivo`, `nombre_original`, `formato_archivo`, `tamano_bytes`, `texto_ocr`, `precision_ocr` REAL, `clasificacion_ia`, `confianza_ia` REAL, `campos_extraidos` TEXT(JSON), `fecha_carga`
- Document types: `CERTIFICADO_INCAPACIDAD`, `EPICRISIS`, `FURIPS`, `CERTIFICADO_NACIDO_VIVO`, `REGISTRO_CIVIL`, `OTRO`

### alertas_vencimiento
Deadline tracking with semáforo (traffic light) system.
- `id`, `incapacidad_id` FK, `tipo_alerta`, `fecha_programada`, `fecha_envio`, `enviada` BOOL, `dias_restantes` INT, `nivel_semaforo` ('VERDE'|'AMARILLO'|'ROJO'), `created_at`
- Semáforo rules: >30 days = VERDE, 15-30 = AMARILLO, <15 = ROJO

### pagos_eps
Payment records from EPS/ARL entities.
- `id`, `incapacidad_id` FK, `monto` REAL, `fecha_pago`, `fecha_registro`, `referencia_pago`, `conciliada` BOOL, `fecha_conciliacion`, `registrado_por_id` FK

### auditoria_log
Full audit trail of all system actions.
- `id`, `usuario_id` FK, `accion`, `entidad`, `entidad_id`, `estado_anterior`, `estado_nuevo`, `detalle`, `ip_address`, `fecha_hora`

---

## 5. STATE MACHINE

The incapacidad lifecycle follows this state diagram with validated transitions:

```
RECIBIDA → PROCESANDO_IA → EN_VERIFICACION → TRANSCRITA → COBRADA → PAGADA → ARCHIVADA
                              ↓                              ↓
                        REQUIERE_CORRECCION              RECHAZADA → COBRO_JURIDICO
                              ↓                                          ↓
                           RECIBIDA (reopen)                         PAGADA
                           VENCIDA (expire)
```

**Valid transitions (enforced in app.py):**
```python
VALID_TRANSITIONS = {
    "RECIBIDA": ["PROCESANDO_IA"],
    "PROCESANDO_IA": ["EN_VERIFICACION", "REQUIERE_CORRECCION"],
    "EN_VERIFICACION": ["TRANSCRITA", "REQUIERE_CORRECCION"],
    "REQUIERE_CORRECCION": ["RECIBIDA", "VENCIDA"],
    "TRANSCRITA": ["COBRADA"],
    "COBRADA": ["PAGADA", "RECHAZADA"],
    "RECHAZADA": ["TRANSCRITA", "COBRO_JURIDICO"],
    "COBRO_JURIDICO": ["PAGADA"],
    "PAGADA": ["ARCHIVADA"],
}
```

**Automatic transitions on upload:**
- File uploaded → `RECIBIDA`
- OCR + AI runs → if OCR precision ≥ 85%: `EN_VERIFICACION`, else: `REQUIERE_CORRECCION`

---

## 6. API ENDPOINTS

All API routes are prefixed with `/api/`. Auth is session-based (Flask session cookie).

### Auth
| Method | Route | Body | Response | Auth |
|--------|-------|------|----------|------|
| POST | `/api/auth/login` | `{email, password}` | `{token, user}` | Public |
| POST | `/api/auth/logout` | — | `{message}` | Any |
| GET | `/api/auth/me` | — | `{id, nombre, apellido, email, rol}` | Any |

### Incapacidades
| Method | Route | Body/Params | Response | Roles |
|--------|-------|-------------|----------|-------|
| GET | `/api/incapacidades` | `?estado=&tipo=&entidad_id=` | `[{...}]` | Any (COLABORADOR sees own only) |
| POST | `/api/incapacidades` | FormData: `archivo` (file), `tipo`, `colaborador_id?`, `entidad_id?` | `{id, estado, ocr, ia, alerta}` | COLABORADOR, RECEPCION, AUXILIAR_RRHH, COORDINADOR_RRHH |
| GET | `/api/incapacidades/:id` | — | `{incapacidad, documentos, alertas, auditoria, pago}` | Any |
| PATCH | `/api/incapacidades/:id/estado` | `{estado, motivo?}` | `{id, estado_anterior, estado_nuevo}` | AUXILIAR_RRHH, COORDINADOR_RRHH |

### Pagos
| Method | Route | Body | Response | Roles |
|--------|-------|------|----------|-------|
| POST | `/api/pagos` | `{incapacidad_id, monto, fecha_pago?, referencia?}` | `{id, message}` | CONTABILIDAD, AUXILIAR_RRHH, COORDINADOR_RRHH |

### Other
| Method | Route | Response | Roles |
|--------|-------|----------|-------|
| GET | `/api/entidades` | `[{id, nombre, tipo, nit, plazo_max_dias}]` | Any |
| GET | `/api/dashboard/stats` | `{total, por_estado, por_tipo, por_entidad, alertas_activas, alertas_rojas, auditoria_reciente}` | Any |
| GET | `/api/usuarios` | `[{id, nombre, apellido, email, rol, activo}]` | COORDINADOR_RRHH |
| GET | `/api/auditoria?limit=50` | `[{...audit entries}]` | COORDINADOR_RRHH, AUXILIAR_RRHH |

---

## 7. DEMO ACCOUNTS

| Email | Password | Role | Permissions |
|-------|----------|------|-------------|
| admin@nomisalud.co | admin123 | COORDINADOR_RRHH | Full access, state changes, audit, users |
| auxiliar@nomisalud.co | aux123 | AUXILIAR_RRHH | State changes, audit |
| colaborador@nomisalud.co | col123 | COLABORADOR | Upload, view own incapacidades |
| recepcion@nomisalud.co | rec123 | RECEPCION | Upload documents |
| contabilidad@nomisalud.co | cont123 | CONTABILIDAD | Register payments |

---

## 8. ROLE-BASED ACCESS CONTROL

| Feature | COLABORADOR | RECEPCION | AUXILIAR_RRHH | COORDINADOR_RRHH | CONTABILIDAD |
|---------|:-----------:|:---------:|:-------------:|:----------------:|:------------:|
| View dashboard | ✓ | ✓ | ✓ | ✓ | ✓ |
| Upload documents | ✓ (own) | ✓ | ✓ | ✓ | ✗ |
| View incapacidades | Own only | All | All | All | All |
| Change state | ✗ | ✗ | ✓ | ✓ | ✗ |
| Register payments | ✗ | ✗ | ✓ | ✓ | ✓ |
| View audit log | ✗ | ✗ | ✓ | ✓ | ✗ |
| Manage users | ✗ | ✗ | ✗ | ✓ | ✗ |

---

## 9. KNOWN ISSUES & BUGS FIXED

1. **Row serialization error (FIXED):** `g.user` was a SQLite `Row` object → Jinja `tojson` crashed. Fixed by converting to `dict(user)` in `login_required` decorator.
2. **OCR/AI is simulated:** `simulate_ocr()` and `simulate_ai_classification()` in app.py generate fake data — they need to be replaced with real Tesseract.js and Claude API integrations.

---

## 10. WHAT NEEDS TO BE BUILT (ROADMAP)

### High Priority — Core Functionality
- [ ] **Real OCR integration:** Replace `simulate_ocr()` with Tesseract.js or pytesseract. Target >85% precision. The function receives a filename and should return `(extracted_text, precision_float)`.
- [ ] **Real AI classification:** Replace `simulate_ai_classification()` with Claude API call. Target >90% confidence. Receives OCR text, returns `(tipo_documento, confianza, campos_dict, validaciones_list)`.
- [ ] **AES-256 encryption:** Encrypt uploaded documents at rest per Ley Habeas Data compliance. Use the `cryptography` package (already installed).
- [ ] **Email notifications:** Send alerts when incapacidades approach deadline (semáforo AMARILLO/ROJO). Use SMTP or SendGrid.
- [ ] **User registration / management CRUD:** Currently only seeded users exist. Build admin panel for creating/editing/deactivating users.

### Medium Priority — UX & Features
- [ ] **Migrate frontend to React.js 18 + TailwindCSS** (per original spec).
- [ ] **Migrate backend to FastAPI** (per original spec).
- [ ] **Migrate database to PostgreSQL 14+** (per original spec).
- [ ] **Colaborador profile management:** Let employees update their EPS/ARL, cédula, phone.
- [ ] **Multiple document upload:** Currently 1 file per incapacidad. Support attaching additional documents later.
- [ ] **Financial conciliation module:** Match EPS payments against cobros. The `pagos_eps.conciliada` field exists but the workflow doesn't.
- [ ] **Excel export:** Export incapacidades list and financial reports to .xlsx.
- [ ] **Search:** Full-text search across incapacidades, collaborator name, cédula, diagnosis.
- [ ] **Pagination:** API currently returns all records. Add `?page=&limit=` params.

### Low Priority — Polish
- [ ] **Prolonged incapacity sub-state:** Track incapacidades >180 days with special workflow (Res. 1843/2025).
- [ ] **Dark mode**
- [ ] **Mobile responsive improvements** (sidebar collapses, detail panel is full-width on mobile already)
- [ ] **PDF report generation:** Auto-generate management reports.
- [ ] **Dashboard charts:** Replace the badge-based "chart" with Recharts or Chart.js.
- [ ] **Automated testing:** Unit tests for API endpoints, integration tests for state machine.

---

## 11. REGULATORY CONTEXT (COLOMBIA)

- **Resolución 1843 de 2025:** Regulates medical incapacity management, prolonged incapacities (>180 days), employer obligations.
- **Ley 1581 de 2012 (Habeas Data):** Personal health data must be encrypted, access-controlled, and auditable.
- **Decreto 780 de 2016:** EPS/ARL reimbursement deadlines and procedures.
- **ICD-10 (CIE-10):** Diagnosis codes used in the `diagnostico_cie10` field.

---

## 12. DESIGN SYSTEM

- **Primary color:** Deep teal `#065F46` (teal-800)
- **Accent:** Coral `#EF7654`
- **Fonts:** DM Serif Display (headings), Plus Jakarta Sans (body)
- **Border radius:** 10-14px for cards, 100px for badges
- **Shadows:** Subtle (`0 1px 3px rgba(0,0,0,.04)` for cards)

---

## 13. HOW TO RUN

```bash
cd nomisalud
python3 -m venv venv
source venv/bin/activate          # Linux/Mac
# venv\Scripts\activate           # Windows
pip install -r requirements.txt
python app.py
# Open http://localhost:5000
```

Database and seed data are created automatically on first run.
To reset: delete `nomisalud.db` and restart.

---

## 14. DEPLOYMENT

**Render.com (recommended for Flask):**
- Build: `pip install -r requirements.txt`
- Start: `python app.py`
- Note: SQLite doesn't persist on Render free tier — migrate to PostgreSQL for production.

**Railway:** `railway login && railway init && railway up`

---

## 15. ORIGINAL VISION DOCUMENT

The full requirements spec is in `Nomisalud_Vision_Alcance (1).docx` (not in repo, available separately). Key specs from that document:

- **10 core features (C-01 to C-10):** OCR capture, AI classification, lifecycle management, deadline alerts, financial conciliation, encrypted storage, audit trail, role-based access, EPS/ARL entity management, management dashboard.
- **3 planned releases:** R1 (OCR + upload + basic tracking), R2 (AI + alerts + financial), R3 (reports + analytics + integrations).
- **Non-functional requirements:** <3s response time, 99.5% uptime, AES-256 encryption, WCAG 2.1 AA accessibility.
