"""
Nomisalud — Flask Application
Full-stack web app for medical incapacity management.
"""
import os
import uuid
import json
import re
from datetime import datetime, date, timedelta
from functools import wraps

from flask import (
    Flask, request, jsonify, render_template, redirect,
    url_for, session, send_from_directory, g
)
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import jwt

from models import get_db, init_db, log_audit

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "nomisalud-dev-secret-key-2026")
app.config["UPLOAD_FOLDER"] = os.path.join(os.path.dirname(__file__), "static", "uploads")
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024  # 5 MB

ALLOWED_EXTENSIONS = {"pdf", "jpg", "jpeg", "png"}
JWT_SECRET = app.secret_key
JWT_ALGORITHM = "HS256"


# ============ HELPERS ============

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def generate_token(user):
    payload = {
        "user_id": user["id"],
        "email": user["email"],
        "rol": user["rol"],
        "nombre": user["nombre"],
        "exp": datetime.utcnow() + timedelta(hours=24),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def get_current_user():
    """Get user from session."""
    if "user_id" not in session:
        return None
    db = get_db()
    user = db.execute("SELECT * FROM usuarios WHERE id=?", (session["user_id"],)).fetchone()
    db.close()
    return user


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        user = get_current_user()
        if not user:
            if request.is_json or request.path.startswith("/api/"):
                return jsonify({"error": "No autorizado"}), 401
            return redirect(url_for("login_page"))
        g.user = dict(user)
        return f(*args, **kwargs)
    return decorated


def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if g.user["rol"] not in roles:
                return jsonify({"error": "No tiene permisos para esta acción"}), 403
            return f(*args, **kwargs)
        return decorated
    return decorator


def extract_text_from_file(filepath):
    """Extract real text from a PDF or image file. Returns (text, precision)."""
    ext = filepath.rsplit(".", 1)[-1].lower()

    if ext == "pdf":
        try:
            from pdfminer.high_level import extract_text as _pdf_extract
            extracted = _pdf_extract(filepath) or ""
            extracted = extracted.strip()
            if extracted:
                return extracted, 0.97
            return "", 0.0
        except Exception:
            return "", 0.0

    # For images (jpg/png): no OCR available without an external binary — route to REQUIERE_CORRECCION
    return "", 0.0


# Known Colombian EPS/ARL names
_KNOWN_ENTITIES = [
    "sura", "nueva eps", "sanitas", "salud total", "sos", "asmet salud",
    "compensar", "famisanar", "coosalud", "medimás", "aliansalud",
    "colmédicos", "savia salud", "emssanar", "comfenalco", "coomeva",
    "arl sura", "positiva", "colmena", "liberty", "equidad",
]

# Phrases that strongly signal an official incapacity certificate header
_CERT_HEADERS = [
    "certificado de incapacidad", "incapacidad médica", "certifica que",
    "certificado médico de incapacidad", "constancia de incapacidad",
    "incapacidad laboral", "se certifica", "el suscrito médico",
]

_DATE_PATTERN = (
    r"\d{4}-\d{2}-\d{2}"           # ISO 2024-01-15
    r"|\d{1,2}/\d{1,2}/\d{4}"      # DD/MM/YYYY
    r"|\d{1,2}\s+de\s+\w+\s+de\s+\d{4}"  # 15 de enero de 2024
)


def _find_cie10(text):
    """Find CIE-10 codes like M54.5, J06.9. Excludes version-number false positives."""
    # CIE-10: single uppercase letter + 2 digits + optional decimal subdivision
    # Negative lookbehind for v/V to skip version strings like V3.0
    codes = re.findall(r'(?<![Vv\d])(?<![A-Z]{2})\b[A-Z]\d{2}(?:\.\d{1,2})?\b(?!\d)', text)
    # Additional filter: letter must be in the valid ICD-10 chapter range (A–Z, no U codes in common use)
    return [c for c in codes if c[0] in "ABCDEFGHJKLMNOPQRSTVWXYZ"]


def _find_labeled_date(text, label_pattern):
    """Find a date value that appears after a specific field label."""
    pattern = rf"{label_pattern}[:\s]{{1,10}}({_DATE_PATTERN})"
    m = re.search(pattern, text, re.IGNORECASE)
    return m.group(1).strip() if m else None


def _find_days(text):
    """Find the number of incapacity days from structured text."""
    patterns = [
        r"(\d+)\s*d[ií]as?\s+de\s+incapacidad",
        r"incapacidad\s+(?:de|por)\s+(\d+)\s*d[ií]as?",
        r"d[ií]as?\s+de\s+incapacidad[:\s]+(\d+)",
        r"(\d+)\s*d[ií]as?\s+(?:h[aá]biles|calendario)\s+de\s+incapacidad",
    ]
    for p in patterns:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            val = int(m.group(1))
            if 1 <= val <= 540:  # sanity range: 1 day to 18 months
                return val
    return None


def _find_patient_name(text):
    """Find a patient name following standard Colombian certificate phrasing."""
    patterns = [
        r"(?:nombre\s+del?\s+paciente|nombre\s+del?\s+usuario)[:\s]+([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+){1,3})",
        r"(?:paciente|señor[a]?|usuario)[:\s]+([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+){1,3})",
        r"certifica\s+que\s+(?:el\s+|la\s+)?(?:señor[a]?\s+|paciente\s+)?([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+){1,3})",
    ]
    for p in patterns:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            name = m.group(1).strip()
            # Reject if it looks like a section header (all caps or too short)
            if len(name) >= 6 and not name.isupper():
                return name
    return None


def _find_document_number(text):
    """Find a Colombian cédula or document number."""
    patterns = [
        r"(?:c[eé]dula\s+de\s+ciudadan[ií]a|c[eé]dula|c\.c\.|documento\s+de\s+identidad|identificaci[oó]n)[:\s#°]*(\d{6,10})",
        r"\bcc[:\s#°]*(\d{6,10})\b",
    ]
    for p in patterns:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            return m.group(1)
    return None


def _find_entity(text):
    """Find the EPS or ARL entity name."""
    lower = text.lower()
    for entity in _KNOWN_ENTITIES:
        if entity in lower:
            return entity.upper()
    m = re.search(
        r"(?:eps|arl|entidad)[:\s]+([A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑa-záéíóúñ\s]{2,30}?)(?:\n|,|\.|$)",
        text, re.IGNORECASE
    )
    return m.group(1).strip() if m else None


def classify_document(texto):
    """
    Classify a document using structural field detection, not keyword counting.
    A genuine incapacity certificate must have co-occurring structured fields
    (CIE-10 code, labeled date pair, days, patient identity) that a generic
    health poster or unrelated document cannot fake by topic alone.

    Returns (tipo_documento, confianza, campos, validaciones, is_medical).
    """
    # --- Extract each structural field ---
    cie10_codes   = _find_cie10(texto)
    fecha_inicio  = _find_labeled_date(texto, r"fecha\s+(?:de\s+)?inicio")
    fecha_fin     = _find_labeled_date(texto, r"fecha\s+(?:de\s+)?(?:fin|terminaci[oó]n|egreso)")
    days          = _find_days(texto)
    patient_name  = _find_patient_name(texto)
    doc_number    = _find_document_number(texto)
    entity        = _find_entity(texto)

    texto_lower = texto.lower()
    has_cert_header = any(h in texto_lower for h in _CERT_HEADERS)
    has_doctor = bool(re.search(r"m[eé]dico\s+tratante|firma\s+m[eé]dico|dr\.?\s+[A-Z]", texto, re.IGNORECASE))

    # --- Score required fields (0-5 points) ---
    # CIE-10 and labeled date pair are the critical/distinctive ones
    required = {
        "diagnostico_cie10": cie10_codes[0] if cie10_codes else None,
        "fecha_par":         "sí" if (fecha_inicio and fecha_fin) else None,
        "dias_incapacidad":  days,
        "nombre_paciente":   patient_name,
        "documento_id":      doc_number,
    }
    field_hits = sum(1 for v in required.values() if v is not None)
    has_critical = bool(cie10_codes) or bool(fecha_inicio and fecha_fin)

    # --- Determine document sub-type ---
    if "furips" in texto_lower:
        tipo = "FURIPS"
    elif "epicrisis" in texto_lower:
        tipo = "EPICRISIS"
    elif "nacido vivo" in texto_lower:
        tipo = "CERTIFICADO_NACIDO_VIVO"
    elif "registro civil" in texto_lower:
        tipo = "REGISTRO_CIVIL"
    else:
        tipo = "CERTIFICADO_INCAPACIDAD"

    # --- Decision: need ≥2 required fields AND ≥1 critical field ---
    if field_hits < 2 or not has_critical:
        reasons = []
        if not cie10_codes:
            reasons.append("No se encontró código de diagnóstico CIE-10 (ej. M54.5, J06.9)")
        if not (fecha_inicio and fecha_fin):
            reasons.append("No se encontró par de fechas etiquetadas (fecha inicio / fecha fin)")
        if not days:
            reasons.append("No se encontró número de días de incapacidad")
        if not patient_name:
            reasons.append("No se identificó nombre del paciente en formato estructurado")
        if not doc_number:
            reasons.append("No se encontró número de cédula o documento de identidad")

        return (
            "OTRO",
            round(field_hits / 5 * 0.45, 2),
            {},
            [{"campo": "estructura", "valido": False,
              "mensaje": "El documento no tiene la estructura de un certificado de incapacidad. " + " | ".join(reasons)}],
            False,
        )

    # --- Confidence: structural fields + supporting signals ---
    base_conf = 0.50 + (field_hits / 5) * 0.35       # 0.57 – 0.85
    bonus = 0.0
    if has_cert_header:  bonus += 0.05
    if has_doctor:       bonus += 0.04
    if entity:           bonus += 0.03
    if cie10_codes and days and fecha_inicio and fecha_fin:
        bonus += 0.05  # all core clinical fields present
    confianza = round(min(base_conf + bonus, 0.99), 2)

    # --- Build extracted fields dict ---
    campos = {}
    if patient_name:          campos["nombre_paciente"]  = patient_name
    if doc_number:            campos["documento"]         = doc_number
    if cie10_codes:           campos["diagnostico_cie10"] = cie10_codes[0]
    if days:                  campos["dias_incapacidad"]  = days
    if fecha_inicio:          campos["fecha_inicio"]      = fecha_inicio
    if fecha_fin:             campos["fecha_fin"]         = fecha_fin
    if entity:                campos["entidad_emisora"]   = entity
    if len(cie10_codes) > 1:  campos["codigos_adicionales"] = ", ".join(cie10_codes[1:])

    # --- Validations ---
    validaciones = []
    if patient_name:
        validaciones.append({"campo": "nombre_paciente", "valido": True,
                             "mensaje": f"Nombre del paciente extraído: {patient_name}"})
    if cie10_codes:
        validaciones.append({"campo": "diagnostico_cie10", "valido": True,
                             "mensaje": f"Código CIE-10 encontrado: {cie10_codes[0]}"})
    if fecha_inicio and fecha_fin and days:
        validaciones.append({"campo": "fechas", "valido": True,
                             "mensaje": f"Fechas extraídas: {fecha_inicio} → {fecha_fin} ({days} días)"})
    elif fecha_inicio or fecha_fin:
        validaciones.append({"campo": "fechas", "valido": False,
                             "mensaje": "Solo se encontró una de las dos fechas — verificar manualmente"})
    if not entity:
        validaciones.append({"campo": "entidad", "valido": False,
                             "mensaje": "Entidad EPS/ARL no identificada — verificar manualmente"})
    if not has_doctor:
        validaciones.append({"campo": "medico", "valido": False,
                             "mensaje": "No se detectó firma o referencia al médico tratante"})

    return tipo, confianza, campos, validaciones, True


def calcular_semaforo(dias_restantes):
    if dias_restantes > 30:
        return "VERDE"
    elif dias_restantes > 15:
        return "AMARILLO"
    return "ROJO"


# ============ PAGE ROUTES ============

@app.route("/")
def index():
    user = get_current_user()
    return render_template("index.html", user=user)


@app.route("/login")
def login_page():
    if get_current_user():
        return redirect(url_for("dashboard"))
    return render_template("login.html")


@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html", user=g.user)


# ============ AUTH API ============

@app.route("/api/auth/login", methods=["POST"])
def api_login():
    data = request.get_json()
    if not data or not data.get("email") or not data.get("password"):
        return jsonify({"error": "Email y contraseña son requeridos"}), 400

    db = get_db()
    user = db.execute(
        "SELECT * FROM usuarios WHERE email=? AND activo=1",
        (data["email"],)
    ).fetchone()

    if not user or not check_password_hash(user["password_hash"], data["password"]):
        db.close()
        return jsonify({"error": "Credenciales inválidas"}), 401

    db.execute(
        "UPDATE usuarios SET ultimo_acceso=? WHERE id=?",
        (datetime.utcnow().isoformat(), user["id"])
    )
    log_audit(db, user["id"], "LOGIN", "usuarios", user["id"],
              ip=request.remote_addr)
    db.commit()

    session["user_id"] = user["id"]
    session["user_rol"] = user["rol"]
    session["user_nombre"] = f"{user['nombre']} {user['apellido']}"

    token = generate_token(user)
    db.close()

    return jsonify({
        "token": token,
        "user": {
            "id": user["id"],
            "nombre": user["nombre"],
            "apellido": user["apellido"],
            "email": user["email"],
            "rol": user["rol"],
        }
    })


@app.route("/api/auth/logout", methods=["POST"])
def api_logout():
    session.clear()
    return jsonify({"message": "Sesión cerrada"})


@app.route("/api/auth/me")
@login_required
def api_me():
    return jsonify({
        "id": g.user["id"],
        "nombre": g.user["nombre"],
        "apellido": g.user["apellido"],
        "email": g.user["email"],
        "rol": g.user["rol"],
    })


# ============ INCAPACIDADES API ============

@app.route("/api/incapacidades", methods=["GET"])
@login_required
def api_list_incapacidades():
    db = get_db()
    rol = g.user["rol"]

    query = """
        SELECT i.*, e.nombre as entidad_nombre,
               u.nombre || ' ' || u.apellido as colaborador_nombre,
               c.cedula,
               (SELECT CASE WHEN COUNT(*) > 0 THEN 1 ELSE 0 END
                FROM documentos d
                WHERE d.incapacidad_id = i.id
                AND (d.clasificacion_ia = 'OTRO' OR d.confianza_ia < 0.70 OR d.precision_ocr = 0)
               ) as doc_sospechoso
        FROM incapacidades i
        LEFT JOIN entidades_salud e ON i.entidad_emisora_id = e.id
        LEFT JOIN colaboradores c ON i.colaborador_id = c.id
        LEFT JOIN usuarios u ON c.usuario_id = u.id
    """
    params = []

    # Collaborators only see their own
    if rol == "COLABORADOR":
        col = db.execute(
            "SELECT id FROM colaboradores WHERE usuario_id=?", (g.user["id"],)
        ).fetchone()
        if col:
            query += " WHERE i.colaborador_id=?"
            params.append(col["id"])
        else:
            db.close()
            return jsonify([])

    # Apply filters
    estado = request.args.get("estado")
    tipo = request.args.get("tipo")
    entidad = request.args.get("entidad_id")

    conditions = []
    if estado:
        conditions.append("i.estado=?")
        params.append(estado)
    if tipo:
        conditions.append("i.tipo=?")
        params.append(tipo)
    if entidad:
        conditions.append("i.entidad_emisora_id=?")
        params.append(entidad)

    if conditions:
        joiner = " AND " if "WHERE" in query else " WHERE "
        query += joiner + " AND ".join(conditions)

    query += " ORDER BY i.created_at DESC"

    rows = db.execute(query, params).fetchall()
    result = [dict(r) for r in rows]
    db.close()
    return jsonify(result)


@app.route("/api/incapacidades/<incapacidad_id>", methods=["GET"])
@login_required
def api_get_incapacidad(incapacidad_id):
    db = get_db()
    inc = db.execute("""
        SELECT i.*, e.nombre as entidad_nombre, e.plazo_max_dias,
               u.nombre || ' ' || u.apellido as colaborador_nombre,
               c.cedula, c.cargo, c.area
        FROM incapacidades i
        LEFT JOIN entidades_salud e ON i.entidad_emisora_id = e.id
        LEFT JOIN colaboradores c ON i.colaborador_id = c.id
        LEFT JOIN usuarios u ON c.usuario_id = u.id
        WHERE i.id=?
    """, (incapacidad_id,)).fetchone()

    if not inc:
        db.close()
        return jsonify({"error": "Incapacidad no encontrada"}), 404

    docs = db.execute(
        "SELECT * FROM documentos WHERE incapacidad_id=? ORDER BY fecha_carga",
        (incapacidad_id,)
    ).fetchall()

    alertas = db.execute(
        "SELECT * FROM alertas_vencimiento WHERE incapacidad_id=? ORDER BY fecha_programada",
        (incapacidad_id,)
    ).fetchall()

    audit = db.execute("""
        SELECT a.*, u.nombre || ' ' || u.apellido as usuario_nombre
        FROM auditoria_log a
        LEFT JOIN usuarios u ON a.usuario_id = u.id
        WHERE a.entidad='incapacidades' AND a.entidad_id=?
        ORDER BY a.fecha_hora DESC LIMIT 20
    """, (incapacidad_id,)).fetchall()

    pago = db.execute(
        "SELECT * FROM pagos_eps WHERE incapacidad_id=?",
        (incapacidad_id,)
    ).fetchone()

    db.close()

    return jsonify({
        "incapacidad": dict(inc),
        "documentos": [dict(d) for d in docs],
        "alertas": [dict(a) for a in alertas],
        "auditoria": [dict(a) for a in audit],
        "pago": dict(pago) if pago else None,
    })


@app.route("/api/incapacidades", methods=["POST"])
@login_required
@role_required("COLABORADOR", "RECEPCION", "AUXILIAR_RRHH", "COORDINADOR_RRHH")
def api_create_incapacidad():
    db = get_db()

    # Get or determine collaborator
    if g.user["rol"] == "COLABORADOR":
        col = db.execute(
            "SELECT id FROM colaboradores WHERE usuario_id=?", (g.user["id"],)
        ).fetchone()
        if not col:
            db.close()
            return jsonify({"error": "No tiene perfil de colaborador"}), 400
        colaborador_id = col["id"]
    else:
        colaborador_id = request.form.get("colaborador_id")
        if not colaborador_id:
            # Use first collaborator as default for demo
            col = db.execute("SELECT id FROM colaboradores LIMIT 1").fetchone()
            colaborador_id = col["id"] if col else None

    if not colaborador_id:
        db.close()
        return jsonify({"error": "Colaborador no especificado"}), 400

    # Check file
    if "archivo" not in request.files:
        db.close()
        return jsonify({"error": "Archivo es requerido"}), 400

    file = request.files["archivo"]
    if file.filename == "" or not allowed_file(file.filename):
        db.close()
        return jsonify({"error": "Formato no válido. Use PDF, JPG o PNG (máx 5MB)"}), 400

    # Save file
    filename = secure_filename(f"{uuid.uuid4()}_{file.filename}")
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(filepath)
    file_size = os.path.getsize(filepath)

    tipo = request.form.get("tipo", "ENFERMEDAD_COMUN")
    origen = "LABORAL" if tipo in ("ACCIDENTE_LABORAL", "ENFERMEDAD_LABORAL") else "COMUN"

    # Find collaborator's EPS
    col_data = db.execute("""
        SELECT c.*, e.id as eps_entity_id, e.plazo_max_dias
        FROM colaboradores c
        LEFT JOIN entidades_salud e ON c.eps_id = e.id
        WHERE c.id=?
    """, (colaborador_id,)).fetchone()

    entidad_id = request.form.get("entidad_id") or (col_data["eps_entity_id"] if col_data else None)

    # Calculate deadline
    plazo_dias = 365
    if entidad_id:
        ent = db.execute("SELECT plazo_max_dias FROM entidades_salud WHERE id=?", (entidad_id,)).fetchone()
        if ent:
            plazo_dias = ent["plazo_max_dias"]

    now = datetime.utcnow().isoformat()
    fecha_vencimiento = (date.today() + timedelta(days=plazo_dias)).isoformat()

    # Create incapacidad
    inc_id = str(uuid.uuid4())
    db.execute("""
        INSERT INTO incapacidades
        (id, colaborador_id, tipo, origen, estado, entidad_emisora_id,
         fecha_recepcion, fecha_vencimiento_plazo, creado_por_id, created_at, updated_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?)
    """, (inc_id, colaborador_id, tipo, origen, "RECIBIDA", entidad_id,
          now, fecha_vencimiento, g.user["id"], now, now))

    # Create document record
    doc_id = str(uuid.uuid4())
    ext = filename.rsplit(".", 1)[1].lower()
    db.execute("""
        INSERT INTO documentos
        (id, incapacidad_id, ruta_archivo, nombre_original, formato_archivo,
         tamano_bytes, fecha_carga)
        VALUES (?,?,?,?,?,?,?)
    """, (doc_id, inc_id, filename, file.filename, ext, file_size, now))

    log_audit(db, g.user["id"], "CREAR_INCAPACIDAD", "incapacidades", inc_id,
              estado_nuevo="RECIBIDA", ip=request.remote_addr)

    # ---- REAL TEXT EXTRACTION + DOCUMENT CLASSIFICATION ----
    texto_ocr, precision_ocr = extract_text_from_file(filepath)

    if not texto_ocr:
        # Could not extract text (image file or empty PDF)
        tipo_doc, confianza_ia, campos, validaciones = (
            "OTRO", 0.0, {},
            [{"campo": "extraccion", "valido": False,
              "mensaje": "No se pudo extraer texto. Para imágenes se requiere revisión manual."}]
        )
        is_medical = False
    else:
        tipo_doc, confianza_ia, campos, validaciones, is_medical = classify_document(texto_ocr)

    # Update document with extraction results
    db.execute("""
        UPDATE documentos SET
            texto_ocr=?, precision_ocr=?, tipo_documento=?,
            clasificacion_ia=?, confianza_ia=?, campos_extraidos=?
        WHERE id=?
    """, (texto_ocr, precision_ocr, tipo_doc, tipo_doc, confianza_ia,
          json.dumps(campos, ensure_ascii=False), doc_id))

    # Route to REQUIERE_CORRECCION if not medical or extraction failed
    new_estado = "EN_VERIFICACION" if (is_medical and precision_ocr >= 0.85) else "REQUIERE_CORRECCION"
    update_fields = {"estado": new_estado, "updated_at": datetime.utcnow().isoformat()}

    if campos.get("fecha_inicio"):
        update_fields["fecha_inicio"] = campos["fecha_inicio"]
    if campos.get("fecha_fin"):
        update_fields["fecha_fin"] = campos["fecha_fin"]
    if campos.get("dias_incapacidad"):
        update_fields["dias_incapacidad"] = campos["dias_incapacidad"]
    if campos.get("diagnostico"):
        update_fields["diagnostico_cie10"] = campos["diagnostico"]

    set_clause = ", ".join(f"{k}=?" for k in update_fields)
    db.execute(
        f"UPDATE incapacidades SET {set_clause} WHERE id=?",
        list(update_fields.values()) + [inc_id]
    )

    log_audit(db, g.user["id"], "PROCESAR_IA", "incapacidades", inc_id,
              estado_anterior="RECIBIDA", estado_nuevo=new_estado,
              detalle=json.dumps({
                  "ocr_precision": precision_ocr,
                  "ia_confianza": confianza_ia,
                  "tipo_documento": tipo_doc,
                  "campos_extraidos": len(campos),
              }), ip=request.remote_addr)

    # Create deadline alert
    dias_restantes = (date.fromisoformat(fecha_vencimiento) - date.today()).days
    alerta_fecha = (date.fromisoformat(fecha_vencimiento) - timedelta(days=7)).isoformat()
    db.execute("""
        INSERT INTO alertas_vencimiento
        (id, incapacidad_id, tipo_alerta, fecha_programada, dias_restantes,
         nivel_semaforo, created_at)
        VALUES (?,?,?,?,?,?,?)
    """, (str(uuid.uuid4()), inc_id, "VENCIMIENTO_PLAZO", alerta_fecha,
          dias_restantes, calcular_semaforo(dias_restantes), now))

    db.commit()
    db.close()

    return jsonify({
        "id": inc_id,
        "estado": new_estado,
        "ocr": {"precision": precision_ocr, "texto_length": len(texto_ocr)},
        "ia": {"tipo_documento": tipo_doc, "confianza": confianza_ia,
               "campos_extraidos": campos, "validaciones": validaciones},
        "alerta": {"fecha_vencimiento": fecha_vencimiento, "dias_restantes": dias_restantes},
        "message": "Incapacidad creada y procesada exitosamente"
    }), 201


@app.route("/api/incapacidades/<incapacidad_id>/estado", methods=["PATCH"])
@login_required
@role_required("AUXILIAR_RRHH", "COORDINADOR_RRHH")
def api_update_estado(incapacidad_id):
    data = request.get_json()
    nuevo_estado = data.get("estado")
    motivo = data.get("motivo", "")

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

    db = get_db()
    inc = db.execute("SELECT * FROM incapacidades WHERE id=?", (incapacidad_id,)).fetchone()
    if not inc:
        db.close()
        return jsonify({"error": "Incapacidad no encontrada"}), 404

    estado_actual = inc["estado"]
    allowed = VALID_TRANSITIONS.get(estado_actual, [])
    if nuevo_estado not in allowed:
        db.close()
        return jsonify({
            "error": f"Transición no válida: {estado_actual} → {nuevo_estado}",
            "transiciones_permitidas": allowed
        }), 400

    now = datetime.utcnow().isoformat()
    db.execute(
        "UPDATE incapacidades SET estado=?, updated_at=?, observaciones=? WHERE id=?",
        (nuevo_estado, now, motivo, incapacidad_id)
    )

    log_audit(db, g.user["id"], "CAMBIAR_ESTADO", "incapacidades", incapacidad_id,
              estado_anterior=estado_actual, estado_nuevo=nuevo_estado,
              detalle=motivo, ip=request.remote_addr)

    db.commit()
    db.close()

    return jsonify({
        "id": incapacidad_id,
        "estado_anterior": estado_actual,
        "estado_nuevo": nuevo_estado,
        "message": f"Estado actualizado: {estado_actual} → {nuevo_estado}"
    })


# ============ PAGOS API ============

@app.route("/api/pagos", methods=["POST"])
@login_required
@role_required("CONTABILIDAD", "AUXILIAR_RRHH", "COORDINADOR_RRHH")
def api_registrar_pago():
    data = request.get_json()
    inc_id = data.get("incapacidad_id")
    monto = data.get("monto")

    if not inc_id or not monto:
        return jsonify({"error": "incapacidad_id y monto son requeridos"}), 400

    db = get_db()
    inc = db.execute("SELECT * FROM incapacidades WHERE id=?", (inc_id,)).fetchone()
    if not inc:
        db.close()
        return jsonify({"error": "Incapacidad no encontrada"}), 404

    now = datetime.utcnow().isoformat()
    pago_id = str(uuid.uuid4())
    db.execute("""
        INSERT INTO pagos_eps
        (id, incapacidad_id, monto, fecha_pago, fecha_registro,
         referencia_pago, registrado_por_id)
        VALUES (?,?,?,?,?,?,?)
    """, (pago_id, inc_id, monto, data.get("fecha_pago", date.today().isoformat()),
          now, data.get("referencia", ""), g.user["id"]))

    log_audit(db, g.user["id"], "REGISTRAR_PAGO", "pagos_eps", pago_id,
              detalle=json.dumps({"monto": monto}), ip=request.remote_addr)

    db.commit()
    db.close()

    return jsonify({"id": pago_id, "message": "Pago registrado exitosamente"}), 201


# ============ ENTIDADES API ============

@app.route("/api/entidades", methods=["GET"])
@login_required
def api_list_entidades():
    db = get_db()
    rows = db.execute("SELECT * FROM entidades_salud WHERE activa=1 ORDER BY nombre").fetchall()
    db.close()
    return jsonify([dict(r) for r in rows])


# ============ DASHBOARD STATS API ============

@app.route("/api/dashboard/stats", methods=["GET"])
@login_required
def api_dashboard_stats():
    db = get_db()

    total = db.execute("SELECT COUNT(*) as n FROM incapacidades").fetchone()["n"]

    estados = db.execute("""
        SELECT estado, COUNT(*) as n FROM incapacidades GROUP BY estado
    """).fetchall()

    por_tipo = db.execute("""
        SELECT tipo, COUNT(*) as n FROM incapacidades GROUP BY tipo
    """).fetchall()

    por_entidad = db.execute("""
        SELECT e.nombre, COUNT(i.id) as n
        FROM incapacidades i
        LEFT JOIN entidades_salud e ON i.entidad_emisora_id = e.id
        GROUP BY e.nombre
    """).fetchall()

    alertas_activas = db.execute("""
        SELECT COUNT(*) as n FROM alertas_vencimiento
        WHERE enviada=0 AND fecha_programada >= date('now')
    """).fetchone()["n"]

    alertas_rojas = db.execute("""
        SELECT COUNT(*) as n FROM alertas_vencimiento
        WHERE nivel_semaforo='ROJO' AND enviada=0
    """).fetchone()["n"]

    recientes = db.execute("""
        SELECT a.*, u.nombre || ' ' || u.apellido as usuario_nombre
        FROM auditoria_log a
        LEFT JOIN usuarios u ON a.usuario_id = u.id
        ORDER BY a.fecha_hora DESC LIMIT 10
    """).fetchall()

    db.close()

    return jsonify({
        "total": total,
        "por_estado": {r["estado"]: r["n"] for r in estados},
        "por_tipo": {r["tipo"]: r["n"] for r in por_tipo},
        "por_entidad": {r["nombre"]: r["n"] for r in por_entidad if r["nombre"]},
        "alertas_activas": alertas_activas,
        "alertas_rojas": alertas_rojas,
        "auditoria_reciente": [dict(r) for r in recientes],
    })


# ============ USERS API ============

@app.route("/api/usuarios", methods=["GET"])
@login_required
@role_required("COORDINADOR_RRHH")
def api_list_usuarios():
    db = get_db()
    rows = db.execute(
        "SELECT id, nombre, apellido, email, rol, activo, fecha_creacion, ultimo_acceso FROM usuarios ORDER BY nombre"
    ).fetchall()
    db.close()
    return jsonify([dict(r) for r in rows])


# ============ AUDIT LOG API ============

@app.route("/api/auditoria", methods=["GET"])
@login_required
@role_required("COORDINADOR_RRHH", "AUXILIAR_RRHH")
def api_auditoria():
    db = get_db()
    limit = request.args.get("limit", 50, type=int)
    rows = db.execute("""
        SELECT a.*, u.nombre || ' ' || u.apellido as usuario_nombre
        FROM auditoria_log a
        LEFT JOIN usuarios u ON a.usuario_id = u.id
        ORDER BY a.fecha_hora DESC LIMIT ?
    """, (limit,)).fetchall()
    db.close()
    return jsonify([dict(r) for r in rows])


# ============ STATIC FILES ============

@app.route("/uploads/<filename>")
@login_required
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


# ============ ERROR HANDLERS ============
# Return JSON for all errors on /api/ routes so the frontend never sees HTML.

@app.errorhandler(404)
def not_found(e):
    if request.path.startswith("/api/"):
        return jsonify({"error": "Ruta no encontrada", "path": request.path}), 404
    return e

@app.errorhandler(500)
def server_error(e):
    if request.path.startswith("/api/"):
        return jsonify({"error": "Error interno del servidor", "detail": str(e)}), 500
    return e

@app.errorhandler(Exception)
def unhandled(e):
    if request.path.startswith("/api/"):
        return jsonify({"error": type(e).__name__, "detail": str(e)}), 500
    raise e

@app.route("/api/health")
def api_health():
    """Public endpoint to verify the app is running and the DB is reachable."""
    try:
        db = get_db()
        user_count = db.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0]
        db.close()
        return jsonify({"status": "ok", "usuarios": user_count})
    except Exception as e:
        return jsonify({"status": "error", "detail": str(e)}), 500


# ============ INIT ============

try:
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    init_db()
except Exception as e:
    print(f"STARTUP ERROR: {e}")

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
