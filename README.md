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

Abrir **http://localhost:5000** en el navegador.

pip install -requirements.txt
python app.py

## Cuentas de demostración

| Email | Contraseña | Rol |
|-------|-----------|-----|
| admin@nomisalud.co | admin123 | Coordinador RRHH |
| auxiliar@nomisalud.co | aux123 | Auxiliar RRHH |
| colaborador@nomisalud.co | col123 | Colaborador |
| recepcion@nomisalud.co | rec123 | Recepción |
| contabilidad@nomisalud.co | cont123 | Contabilidad |

Samuel Parra Murillo
Ingeniería de Software I — 2026
