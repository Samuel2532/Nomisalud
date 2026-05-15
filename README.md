# Nomisalud — Sistema de Gestión de Incapacidades

Sistema web completo para gestión de incapacidades médicas de origen común y laboral en Colombia.

## Stack

- **Backend:** Flask 3.1 (Python)
- **Database:** SQLite3
- **Frontend:** HTML5/CSS3/JS (Jinja2 templates)
- **Auth:** Session-based + JWT
- **OCR/IA:** Simulado (listo para integrar Tesseract.js / Claude API)

## Estructura del proyecto

```
nomisalud/
├── app.py                 # Servidor Flask — todas las rutas y API
├── models.py              # Modelos SQLite y seed de datos
├── requirements.txt       # Dependencias Python
├── nomisalud.db           # Base de datos (se crea automáticamente)
├── templates/
│   ├── index.html         # Landing page
│   ├── login.html         # Página de login
│   └── dashboard.html     # Dashboard SPA
└── static/
    └── uploads/           # Documentos cargados
```

## Instalación y ejecución en localhost

```bash
# 1. Clonar o descargar el proyecto
cd nomisalud

# 2. Crear entorno virtual (recomendado)
python3 -m venv venv
source venv/bin/activate    # Linux/Mac
# venv\Scripts\activate     # Windows

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Ejecutar
python app.py
```

Abrir **http://localhost:5000** en el navegador.

## Cuentas de demostración

| Email | Contraseña | Rol |
|-------|-----------|-----|
| admin@nomisalud.co | admin123 | Coordinador RRHH |
| auxiliar@nomisalud.co | aux123 | Auxiliar RRHH |
| colaborador@nomisalud.co | col123 | Colaborador |
| recepcion@nomisalud.co | rec123 | Recepción |
| contabilidad@nomisalud.co | cont123 | Contabilidad |

## Funcionalidades implementadas

- **Autenticación** — Login con roles (5 roles), sesión segura
- **Carga de documentos** — Upload drag-and-drop (PDF, JPG, PNG, max 5MB)
- **OCR simulado** — Extrae texto con precisión 83-97%
- **Clasificación IA** — Clasifica tipo de documento, extrae 7 campos
- **Máquina de estados** — 11 estados con transiciones validadas
- **Dashboard** — Stats, distribución por estado, actividad reciente
- **Panel de detalle** — Info completa, OCR, campos IA, alertas, auditoría
- **Semáforo de alertas** — Verde/Amarillo/Rojo según días restantes
- **Log de auditoría** — Trazabilidad completa de todas las acciones
- **7 entidades EPS/ARL** — Con plazos diferenciados (SURA 150d, Sanitas 3 años)

## API Endpoints

| Método | Ruta | Descripción |
|--------|------|-------------|
| POST | `/api/auth/login` | Login |
| POST | `/api/auth/logout` | Logout |
| GET | `/api/auth/me` | Usuario actual |
| GET | `/api/incapacidades` | Listar (filtros: estado, tipo) |
| POST | `/api/incapacidades` | Crear + upload + OCR + IA |
| GET | `/api/incapacidades/:id` | Detalle completo |
| PATCH | `/api/incapacidades/:id/estado` | Cambiar estado |
| POST | `/api/pagos` | Registrar pago |
| GET | `/api/entidades` | Listar EPS/ARL |
| GET | `/api/dashboard/stats` | Estadísticas |
| GET | `/api/auditoria` | Log de auditoría |

## Subir a GitHub

```bash
git init
git branch -M main
git add .
git commit -m "feat: Nomisalud full-stack app"
# Crear repo en github.com/new → nomisalud
git remote add origin https://github.com/TU_USUARIO/nomisalud.git
git push -u origin main
```

## Deploy en Render.com (gratis, soporta Flask)

1. Sube a GitHub
2. Ve a [render.com](https://render.com) → New → Web Service
3. Conecta tu repositorio
4. Configuración:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python app.py`
   - **Environment:** Python 3
5. Deploy → tu app estará en `https://nomisalud.onrender.com`

## Deploy en Railway (alternativa)

1. Instala Railway CLI: `npm i -g @railway/cli`
2. `railway login && railway init && railway up`

## Equipo

Jean Paul Bedoya, Samuel Parra Murillo, Sebastian Barco Correa, Brayan Armando Chiquito Posso
Ingeniería de Software I — 2026
