"""
Nomisalud — Database Models
SQLite database with all domain entities from the class diagram.
"""
import sqlite3
import os
import uuid
from datetime import datetime, date, timedelta
from werkzeug.security import generate_password_hash, check_password_hash

DB_PATH = os.path.join(os.path.dirname(__file__), "nomisalud.db")


def get_db():
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    conn = get_db()
    c = conn.cursor()

    c.executescript("""
    CREATE TABLE IF NOT EXISTS entidades_salud (
        id TEXT PRIMARY KEY,
        nombre TEXT NOT NULL,
        tipo TEXT NOT NULL CHECK(tipo IN ('EPS','ARL')),
        nit TEXT UNIQUE,
        plazo_max_dias INTEGER NOT NULL DEFAULT 365,
        email_contacto TEXT,
        activa INTEGER NOT NULL DEFAULT 1
    );

    CREATE TABLE IF NOT EXISTS usuarios (
        id TEXT PRIMARY KEY,
        nombre TEXT NOT NULL,
        apellido TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        rol TEXT NOT NULL CHECK(rol IN (
            'COLABORADOR','RECEPCION','AUXILIAR_RRHH',
            'COORDINADOR_RRHH','CONTABILIDAD'
        )),
        activo INTEGER NOT NULL DEFAULT 1,
        fecha_creacion TEXT NOT NULL,
        ultimo_acceso TEXT
    );

    CREATE TABLE IF NOT EXISTS colaboradores (
        id TEXT PRIMARY KEY,
        usuario_id TEXT NOT NULL UNIQUE REFERENCES usuarios(id),
        cedula TEXT UNIQUE NOT NULL,
        cargo TEXT,
        area TEXT,
        fecha_ingreso TEXT,
        eps_id TEXT REFERENCES entidades_salud(id),
        arl_id TEXT REFERENCES entidades_salud(id),
        telefono TEXT
    );

    CREATE TABLE IF NOT EXISTS incapacidades (
        id TEXT PRIMARY KEY,
        colaborador_id TEXT NOT NULL REFERENCES colaboradores(id),
        tipo TEXT NOT NULL CHECK(tipo IN (
            'ENFERMEDAD_COMUN','ACCIDENTE_LABORAL',
            'ENFERMEDAD_LABORAL','LICENCIA_MATERNIDAD',
            'LICENCIA_PATERNIDAD'
        )),
        origen TEXT NOT NULL CHECK(origen IN ('COMUN','LABORAL')),
        estado TEXT NOT NULL DEFAULT 'RECIBIDA' CHECK(estado IN (
            'RECIBIDA','PROCESANDO_IA','EN_VERIFICACION',
            'REQUIERE_CORRECCION','TRANSCRITA','COBRADA',
            'RECHAZADA','COBRO_JURIDICO','PAGADA',
            'ARCHIVADA','VENCIDA'
        )),
        fecha_inicio TEXT,
        fecha_fin TEXT,
        dias_incapacidad INTEGER,
        diagnostico_cie10 TEXT,
        entidad_emisora_id TEXT REFERENCES entidades_salud(id),
        fecha_recepcion TEXT NOT NULL,
        fecha_vencimiento_plazo TEXT,
        observaciones TEXT,
        creado_por_id TEXT REFERENCES usuarios(id),
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS documentos (
        id TEXT PRIMARY KEY,
        incapacidad_id TEXT NOT NULL REFERENCES incapacidades(id),
        tipo_documento TEXT CHECK(tipo_documento IN (
            'CERTIFICADO_INCAPACIDAD','EPICRISIS','FURIPS',
            'CERTIFICADO_NACIDO_VIVO','REGISTRO_CIVIL','OTRO'
        )),
        ruta_archivo TEXT NOT NULL,
        nombre_original TEXT NOT NULL,
        formato_archivo TEXT NOT NULL,
        tamano_bytes INTEGER,
        texto_ocr TEXT,
        precision_ocr REAL,
        clasificacion_ia TEXT,
        confianza_ia REAL,
        campos_extraidos TEXT,
        fecha_carga TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS alertas_vencimiento (
        id TEXT PRIMARY KEY,
        incapacidad_id TEXT NOT NULL REFERENCES incapacidades(id),
        tipo_alerta TEXT NOT NULL,
        fecha_programada TEXT NOT NULL,
        fecha_envio TEXT,
        enviada INTEGER NOT NULL DEFAULT 0,
        dias_restantes INTEGER,
        nivel_semaforo TEXT CHECK(nivel_semaforo IN ('VERDE','AMARILLO','ROJO')),
        created_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS pagos_eps (
        id TEXT PRIMARY KEY,
        incapacidad_id TEXT NOT NULL REFERENCES incapacidades(id),
        monto REAL NOT NULL,
        fecha_pago TEXT NOT NULL,
        fecha_registro TEXT NOT NULL,
        referencia_pago TEXT,
        conciliada INTEGER NOT NULL DEFAULT 0,
        fecha_conciliacion TEXT,
        registrado_por_id TEXT REFERENCES usuarios(id)
    );

    CREATE TABLE IF NOT EXISTS auditoria_log (
        id TEXT PRIMARY KEY,
        usuario_id TEXT REFERENCES usuarios(id),
        accion TEXT NOT NULL,
        entidad TEXT NOT NULL,
        entidad_id TEXT,
        estado_anterior TEXT,
        estado_nuevo TEXT,
        detalle TEXT,
        ip_address TEXT,
        fecha_hora TEXT NOT NULL
    );
    """)

    # Seed EPS/ARL entities
    entidades = [
        ("Salud Total", "EPS", "800130907", 365),
        ("Nueva EPS", "EPS", "900156264", 365),
        ("SOS", "EPS", "805001157", 365),
        ("Sanitas", "EPS", "800251440", 1095),
        ("SURA EPS", "EPS", "800088702", 150),
        ("Asmet Salud", "EPS", "900074994", 365),
        ("ARL SURA", "ARL", "890903790", 730),
    ]
    for nombre, tipo, nit, plazo in entidades:
        existing = c.execute(
            "SELECT id FROM entidades_salud WHERE nit=?", (nit,)
        ).fetchone()
        if not existing:
            c.execute(
                "INSERT INTO entidades_salud (id,nombre,tipo,nit,plazo_max_dias) VALUES (?,?,?,?,?)",
                (str(uuid.uuid4()), nombre, tipo, nit, plazo),
            )

    # Seed demo users if none exist
    if not c.execute("SELECT id FROM usuarios LIMIT 1").fetchone():
        now = datetime.utcnow().isoformat()

        # Admin / Coordinador
        coord_id = str(uuid.uuid4())
        c.execute(
            "INSERT INTO usuarios VALUES (?,?,?,?,?,?,?,?,?)",
            (coord_id, "Carlos", "Ramírez", "admin@nomisalud.co",
             generate_password_hash("admin123"), "COORDINADOR_RRHH", 1, now, None),
        )

        # Auxiliar RRHH
        aux_id = str(uuid.uuid4())
        c.execute(
            "INSERT INTO usuarios VALUES (?,?,?,?,?,?,?,?,?)",
            (aux_id, "Laura", "Gómez", "auxiliar@nomisalud.co",
             generate_password_hash("aux123"), "AUXILIAR_RRHH", 1, now, None),
        )

        # Colaborador
        col_user_id = str(uuid.uuid4())
        c.execute(
            "INSERT INTO usuarios VALUES (?,?,?,?,?,?,?,?,?)",
            (col_user_id, "Jean Paul", "Bedoya", "colaborador@nomisalud.co",
             generate_password_hash("col123"), "COLABORADOR", 1, now, None),
        )
        eps = c.execute(
            "SELECT id FROM entidades_salud WHERE nombre='SURA EPS'"
        ).fetchone()
        arl = c.execute(
            "SELECT id FROM entidades_salud WHERE nombre='ARL SURA'"
        ).fetchone()
        col_id = str(uuid.uuid4())
        c.execute(
            "INSERT INTO colaboradores VALUES (?,?,?,?,?,?,?,?,?)",
            (col_id, col_user_id, "1234567890", "Desarrollador", "Tecnología",
             "2023-01-15", eps["id"] if eps else None,
             arl["id"] if arl else None, "3001234567"),
        )

        # Recepcion
        rec_id = str(uuid.uuid4())
        c.execute(
            "INSERT INTO usuarios VALUES (?,?,?,?,?,?,?,?,?)",
            (rec_id, "María", "López", "recepcion@nomisalud.co",
             generate_password_hash("rec123"), "RECEPCION", 1, now, None),
        )

        # Contabilidad
        cont_id = str(uuid.uuid4())
        c.execute(
            "INSERT INTO usuarios VALUES (?,?,?,?,?,?,?,?,?)",
            (cont_id, "Andrés", "Torres", "contabilidad@nomisalud.co",
             generate_password_hash("cont123"), "CONTABILIDAD", 1, now, None),
        )

    conn.commit()
    conn.close()
    print("Database initialized successfully.")


def log_audit(conn, user_id, accion, entidad, entidad_id=None,
              estado_anterior=None, estado_nuevo=None, detalle=None, ip=None):
    conn.execute(
        "INSERT INTO auditoria_log VALUES (?,?,?,?,?,?,?,?,?,?)",
        (str(uuid.uuid4()), user_id, accion, entidad, entidad_id,
         estado_anterior, estado_nuevo, detalle, ip,
         datetime.utcnow().isoformat()),
    )


if __name__ == "__main__":
    init_db()
