"""
Genera documentos PDF de ejemplo para demostrar el clasificador de Nomisalud.
Ejecutar: python generar_ejemplos.py
Los PDFs se guardan en static/ejemplos/
"""

import os
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "static", "ejemplos")
os.makedirs(OUTPUT_DIR, exist_ok=True)


def make_doc(filename):
    path = os.path.join(OUTPUT_DIR, filename)
    doc = SimpleDocTemplate(
        path, pagesize=letter,
        leftMargin=2.5*cm, rightMargin=2.5*cm,
        topMargin=2.5*cm, bottomMargin=2.5*cm,
    )
    return doc, path


def styles():
    base = getSampleStyleSheet()
    title   = ParagraphStyle("titulo",   parent=base["Title"],   fontSize=14, spaceAfter=4,  alignment=TA_CENTER)
    entity  = ParagraphStyle("entidad",  parent=base["Normal"],  fontSize=11, spaceAfter=2,  alignment=TA_CENTER, textColor=colors.HexColor("#065F46"))
    heading = ParagraphStyle("heading",  parent=base["Heading2"],fontSize=10, spaceBefore=10, spaceAfter=4, textColor=colors.HexColor("#1E293B"))
    body    = ParagraphStyle("body",     parent=base["Normal"],  fontSize=9,  spaceAfter=3,  leading=14)
    label   = ParagraphStyle("label",    parent=base["Normal"],  fontSize=8,  textColor=colors.HexColor("#64748B"), spaceAfter=1)
    value   = ParagraphStyle("value",    parent=base["Normal"],  fontSize=10, textColor=colors.HexColor("#0F172A"), spaceAfter=6, fontName="Helvetica-Bold")
    footer  = ParagraphStyle("footer",   parent=base["Normal"],  fontSize=7,  textColor=colors.grey, alignment=TA_CENTER, spaceBefore=20)
    return title, entity, heading, body, label, value, footer


def field_row(label_text, value_text, lbl_style, val_style):
    return [Paragraph(label_text, lbl_style), Paragraph(value_text, val_style)]


# ─────────────────────────────────────────────────────────────────────────────
# CATEGORIA 1: DOCUMENTOS VALIDOS
# ─────────────────────────────────────────────────────────────────────────────

def gen_valido_enfermedad_comun():
    """Certificado completo de enfermedad comun - debe pasar con alta confianza."""
    doc, path = make_doc("1_valido_enfermedad_comun.pdf")
    title, entity, heading, body, lbl, val, footer = styles()
    story = []

    story.append(Paragraph("EPS SURA S.A.", entity))
    story.append(Paragraph("NIT 800.088.702-3", ParagraphStyle("nit", parent=entity, fontSize=8, textColor=colors.grey)))
    story.append(Spacer(1, 0.3*cm))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#065F46")))
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph("CERTIFICADO DE INCAPACIDAD MEDICA", title))
    story.append(Paragraph("No. 2026-0045871", ParagraphStyle("num", parent=entity, fontSize=9, textColor=colors.grey)))
    story.append(Spacer(1, 0.5*cm))

    story.append(Paragraph("INFORMACION DEL PACIENTE", heading))
    data = [
        [Paragraph("Nombre del paciente:", lbl),      Paragraph("Maria Fernanda Gomez Rios", val)],
        [Paragraph("Cedula de ciudadania:", lbl),      Paragraph("52.478.901", val)],
        [Paragraph("Fecha de nacimiento:", lbl),       Paragraph("14 de marzo de 1990", val)],
        [Paragraph("Entidad EPS:", lbl),               Paragraph("EPS SURA", val)],
    ]
    t = Table(data, colWidths=[5*cm, 10*cm])
    t.setStyle(TableStyle([("VALIGN", (0,0), (-1,-1), "TOP"), ("TOPPADDING", (0,0), (-1,-1), 3)]))
    story.append(t)

    story.append(Paragraph("DIAGNOSTICO Y PERIODO DE INCAPACIDAD", heading))
    data2 = [
        [Paragraph("Diagnostico CIE-10:", lbl),              Paragraph("M54.5 - Dolor lumbar inespecifico", val)],
        [Paragraph("Tipo de incapacidad:", lbl),             Paragraph("Enfermedad de origen comun", val)],
        [Paragraph("Dias de incapacidad:", lbl),             Paragraph("7 dias calendario", val)],
        [Paragraph("Fecha inicio:", lbl),                    Paragraph("2026-05-10", val)],
        [Paragraph("Fecha fin:", lbl),                       Paragraph("2026-05-16", val)],
        [Paragraph("Reintegro laboral:", lbl),               Paragraph("2026-05-17", val)],
    ]
    t2 = Table(data2, colWidths=[5*cm, 10*cm])
    t2.setStyle(TableStyle([("VALIGN", (0,0), (-1,-1), "TOP"), ("TOPPADDING", (0,0), (-1,-1), 3)]))
    story.append(t2)

    story.append(Paragraph("MEDICO TRATANTE", heading))
    data3 = [
        [Paragraph("Medico tratante:", lbl),   Paragraph("Dr. Carlos Eduardo Rodriguez Vargas", val)],
        [Paragraph("Registro medico:", lbl),    Paragraph("RM-45892", val)],
        [Paragraph("Especialidad:", lbl),       Paragraph("Medicina General", val)],
        [Paragraph("Institucion:", lbl),        Paragraph("Clinica SURA - Sede Laureles", val)],
    ]
    t3 = Table(data3, colWidths=[5*cm, 10*cm])
    t3.setStyle(TableStyle([("VALIGN", (0,0), (-1,-1), "TOP"), ("TOPPADDING", (0,0), (-1,-1), 3)]))
    story.append(t3)

    story.append(Spacer(1, 1*cm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey))
    story.append(Paragraph("_________________________________", ParagraphStyle("firma", parent=val, alignment=TA_CENTER, spaceBefore=15)))
    story.append(Paragraph("Firma medico tratante y sello institucional", ParagraphStyle("firmalbl", parent=lbl, alignment=TA_CENTER)))
    story.append(Spacer(1, 0.5*cm))
    story.append(Paragraph("Este certificado es valido con sello original de la institucion. Ley 1581 de 2012 - Habeas Data.", footer))
    story.append(Paragraph("Generado el 15 de mayo de 2026 | EPS SURA | Confidencial", footer))

    doc.build(story)
    return path


def gen_valido_accidente_laboral():
    """Certificado de accidente laboral con ARL - debe pasar con alta confianza."""
    doc, path = make_doc("2_valido_accidente_laboral.pdf")
    title, entity, heading, body, lbl, val, footer = styles()
    story = []

    story.append(Paragraph("ARL SURA", entity))
    story.append(Paragraph("Administradora de Riesgos Laborales | NIT 890.903.790-1", ParagraphStyle("nit", parent=entity, fontSize=8, textColor=colors.grey)))
    story.append(Spacer(1, 0.3*cm))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#065F46")))
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph("CERTIFICADO DE INCAPACIDAD - ACCIDENTE LABORAL", title))
    story.append(Paragraph("Reporte AT No. 2026-LAB-00312", ParagraphStyle("num", parent=entity, fontSize=9, textColor=colors.grey)))
    story.append(Spacer(1, 0.5*cm))

    story.append(Paragraph("DATOS DEL TRABAJADOR", heading))
    data = [
        [Paragraph("Nombre del paciente:", lbl),       Paragraph("Andres Felipe Torres Medina", val)],
        [Paragraph("Cedula de ciudadania:", lbl),       Paragraph("71.345.678", val)],
        [Paragraph("Empresa empleadora:", lbl),         Paragraph("Construcciones Pacifico S.A.S.", val)],
        [Paragraph("Cargo:", lbl),                      Paragraph("Operario de planta", val)],
    ]
    t = Table(data, colWidths=[5*cm, 10*cm])
    t.setStyle(TableStyle([("VALIGN", (0,0), (-1,-1), "TOP"), ("TOPPADDING", (0,0), (-1,-1), 3)]))
    story.append(t)

    story.append(Paragraph("DIAGNOSTICO DEL ACCIDENTE", heading))
    data2 = [
        [Paragraph("Diagnostico CIE-10:", lbl),         Paragraph("S62.00 - Fractura del escafoides del carpo", val)],
        [Paragraph("Mecanismo del accidente:", lbl),     Paragraph("Caida de altura - plataforma de trabajo", val)],
        [Paragraph("Origen:", lbl),                      Paragraph("Accidente de trabajo (laboral)", val)],
        [Paragraph("Dias de incapacidad:", lbl),         Paragraph("30 dias calendario", val)],
        [Paragraph("Fecha inicio:", lbl),                Paragraph("2026-05-02", val)],
        [Paragraph("Fecha fin:", lbl),                   Paragraph("2026-06-01", val)],
    ]
    t2 = Table(data2, colWidths=[5*cm, 10*cm])
    t2.setStyle(TableStyle([("VALIGN", (0,0), (-1,-1), "TOP"), ("TOPPADDING", (0,0), (-1,-1), 3)]))
    story.append(t2)

    story.append(Paragraph("MEDICO TRATANTE", heading))
    data3 = [
        [Paragraph("Medico tratante:", lbl),    Paragraph("Dr. Luis Alberto Gonzalez Parra", val)],
        [Paragraph("Especialidad:", lbl),        Paragraph("Medicina del Trabajo y Ortopedia", val)],
        [Paragraph("IPS:", lbl),                 Paragraph("Clinica Bolivariana - Urgencias", val)],
    ]
    t3 = Table(data3, colWidths=[5*cm, 10*cm])
    t3.setStyle(TableStyle([("VALIGN", (0,0), (-1,-1), "TOP"), ("TOPPADDING", (0,0), (-1,-1), 3)]))
    story.append(t3)

    story.append(Spacer(1, 1*cm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey))
    story.append(Paragraph("_________________________________", ParagraphStyle("firma", parent=val, alignment=TA_CENTER, spaceBefore=15)))
    story.append(Paragraph("Firma medico tratante y sello ARL SURA", ParagraphStyle("firmalbl", parent=lbl, alignment=TA_CENTER)))
    story.append(Paragraph("Decreto 1072 de 2015 - Riesgos Laborales Colombia", footer))

    doc.build(story)
    return path


# ─────────────────────────────────────────────────────────────────────────────
# CATEGORIA 2: DOCUMENTOS CON ERRORES
# ─────────────────────────────────────────────────────────────────────────────

def gen_incompleto_sin_fechas():
    """Certificado con CIE-10 y paciente pero sin fechas ni dias - genera advertencia."""
    doc, path = make_doc("3_incompleto_sin_fechas.pdf")
    title, entity, heading, body, lbl, val, footer = styles()
    story = []

    story.append(Paragraph("CLINICA GENERAL DEL NORTE", entity))
    story.append(Paragraph("NIT 812.005.431-2", ParagraphStyle("nit", parent=entity, fontSize=8, textColor=colors.grey)))
    story.append(Spacer(1, 0.3*cm))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.grey))
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph("CONSTANCIA DE INCAPACIDAD MEDICA", title))
    story.append(Spacer(1, 0.5*cm))

    story.append(Paragraph("DATOS DEL PACIENTE", heading))
    data = [
        [Paragraph("Nombre del paciente:", lbl),   Paragraph("Laura Valentina Rios Castillo", val)],
        [Paragraph("Cedula de ciudadania:", lbl),   Paragraph("1.037.892.456", val)],
        [Paragraph("EPS:", lbl),                    Paragraph("Nueva EPS", val)],
    ]
    t = Table(data, colWidths=[5*cm, 10*cm])
    t.setStyle(TableStyle([("VALIGN", (0,0), (-1,-1), "TOP"), ("TOPPADDING", (0,0), (-1,-1), 3)]))
    story.append(t)

    story.append(Paragraph("DIAGNOSTICO", heading))
    data2 = [
        [Paragraph("Diagnostico CIE-10:", lbl),   Paragraph("J06.9 - Infeccion aguda de las vias respiratorias superiores", val)],
        [Paragraph("Tipo:", lbl),                  Paragraph("Enfermedad de origen comun", val)],
        # INTENCIONALMENTE sin dias, fecha inicio ni fecha fin
    ]
    t2 = Table(data2, colWidths=[5*cm, 10*cm])
    t2.setStyle(TableStyle([("VALIGN", (0,0), (-1,-1), "TOP"), ("TOPPADDING", (0,0), (-1,-1), 3)]))
    story.append(t2)

    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph(
        "<b>NOTA:</b> El periodo de incapacidad y las fechas exactas deben ser confirmadas "
        "directamente con la EPS. Este documento es preliminar y requiere actualizacion.",
        ParagraphStyle("nota", parent=body, textColor=colors.HexColor("#B45309"),
                       backColor=colors.HexColor("#FEF3C7"), borderPadding=6, borderColor=colors.HexColor("#F59E0B"))
    ))

    story.append(Paragraph("MEDICO TRATANTE", heading))
    data3 = [
        [Paragraph("Medico tratante:", lbl),   Paragraph("Dr. Ricardo Moreno Silva", val)],
        [Paragraph("Registro:", lbl),           Paragraph("RM-29341", val)],
    ]
    t3 = Table(data3, colWidths=[5*cm, 10*cm])
    t3.setStyle(TableStyle([("VALIGN", (0,0), (-1,-1), "TOP"), ("TOPPADDING", (0,0), (-1,-1), 3)]))
    story.append(t3)

    story.append(Spacer(1, 1*cm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey))
    story.append(Paragraph("_________________________________", ParagraphStyle("firma", parent=val, alignment=TA_CENTER, spaceBefore=15)))
    story.append(Paragraph("Firma medico tratante", ParagraphStyle("firmalbl", parent=lbl, alignment=TA_CENTER)))
    story.append(Paragraph("DOCUMENTO INCOMPLETO - Pendiente confirmacion de fechas por parte de la EPS", footer))

    doc.build(story)
    return path


def gen_incompleto_sin_cie10():
    """Certificado con fechas y paciente pero sin codigo CIE-10 - genera advertencia."""
    doc, path = make_doc("4_incompleto_sin_codigo_cie10.pdf")
    title, entity, heading, body, lbl, val, footer = styles()
    story = []

    story.append(Paragraph("SALUD TOTAL EPS", entity))
    story.append(Paragraph("NIT 800.130.907-7", ParagraphStyle("nit", parent=entity, fontSize=8, textColor=colors.grey)))
    story.append(Spacer(1, 0.3*cm))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#065F46")))
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph("CERTIFICADO DE INCAPACIDAD MEDICA", title))
    story.append(Spacer(1, 0.5*cm))

    story.append(Paragraph("DATOS DEL PACIENTE", heading))
    data = [
        [Paragraph("Nombre del paciente:", lbl),   Paragraph("Jorge Esteban Vargas Moreno", val)],
        [Paragraph("Cedula de ciudadania:", lbl),   Paragraph("79.654.321", val)],
        [Paragraph("Entidad EPS:", lbl),            Paragraph("Salud Total", val)],
    ]
    t = Table(data, colWidths=[5*cm, 10*cm])
    t.setStyle(TableStyle([("VALIGN", (0,0), (-1,-1), "TOP"), ("TOPPADDING", (0,0), (-1,-1), 3)]))
    story.append(t)

    story.append(Paragraph("INCAPACIDAD", heading))
    data2 = [
        # INTENCIONALMENTE sin codigo CIE-10 - solo descripcion libre
        [Paragraph("Diagnostico:", lbl),             Paragraph("Gastroenteritis aguda con deshidratacion leve (pendiente codificacion)", val)],
        [Paragraph("Dias de incapacidad:", lbl),     Paragraph("5 dias calendario", val)],
        [Paragraph("Fecha inicio:", lbl),            Paragraph("2026-05-13", val)],
        [Paragraph("Fecha fin:", lbl),               Paragraph("2026-05-17", val)],
    ]
    t2 = Table(data2, colWidths=[5*cm, 10*cm])
    t2.setStyle(TableStyle([("VALIGN", (0,0), (-1,-1), "TOP"), ("TOPPADDING", (0,0), (-1,-1), 3)]))
    story.append(t2)

    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph(
        "<b>OBSERVACION:</b> El codigo diagnostico CIE-10 no fue incluido en este certificado. "
        "Se recomienda solicitar al medico tratante la correccion del documento con el codigo correspondiente.",
        ParagraphStyle("nota", parent=body, textColor=colors.HexColor("#B45309"))
    ))

    story.append(Paragraph("MEDICO TRATANTE", heading))
    data3 = [
        [Paragraph("Medico tratante:", lbl),   Paragraph("Dra. Paola Andrea Suarez Jimenez", val)],
        [Paragraph("Especialidad:", lbl),       Paragraph("Medicina Interna", val)],
    ]
    t3 = Table(data3, colWidths=[5*cm, 10*cm])
    t3.setStyle(TableStyle([("VALIGN", (0,0), (-1,-1), "TOP"), ("TOPPADDING", (0,0), (-1,-1), 3)]))
    story.append(t3)

    story.append(Spacer(1, 1*cm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey))
    story.append(Paragraph("_________________________________", ParagraphStyle("firma", parent=val, alignment=TA_CENTER, spaceBefore=15)))
    story.append(Paragraph("Firma medico tratante y sello institucional", ParagraphStyle("firmalbl", parent=lbl, alignment=TA_CENTER)))
    story.append(Paragraph("Salud Total EPS | Valido con sello original | 2026", footer))

    doc.build(story)
    return path


def gen_fechas_inconsistentes():
    """Certificado con fechas que no cuadran con los dias declarados."""
    doc, path = make_doc("5_incompleto_fechas_inconsistentes.pdf")
    title, entity, heading, body, lbl, val, footer = styles()
    story = []

    story.append(Paragraph("SANITAS EPS", entity))
    story.append(Paragraph("NIT 800.251.440-4", ParagraphStyle("nit", parent=entity, fontSize=8, textColor=colors.grey)))
    story.append(Spacer(1, 0.3*cm))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#065F46")))
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph("CERTIFICADO DE INCAPACIDAD MEDICA", title))
    story.append(Spacer(1, 0.5*cm))

    story.append(Paragraph("DATOS DEL PACIENTE", heading))
    data = [
        [Paragraph("Nombre del paciente:", lbl),   Paragraph("Diana Marcela Ospina Benitez", val)],
        [Paragraph("Cedula de ciudadania:", lbl),   Paragraph("43.112.789", val)],
        [Paragraph("EPS:", lbl),                    Paragraph("Sanitas", val)],
    ]
    t = Table(data, colWidths=[5*cm, 10*cm])
    t.setStyle(TableStyle([("VALIGN", (0,0), (-1,-1), "TOP"), ("TOPPADDING", (0,0), (-1,-1), 3)]))
    story.append(t)

    story.append(Paragraph("DIAGNOSTICO E INCAPACIDAD", heading))
    data2 = [
        [Paragraph("Diagnostico CIE-10:", lbl),     Paragraph("F32.0 - Episodio depresivo leve", val)],
        [Paragraph("Dias de incapacidad:", lbl),     Paragraph("15 dias calendario", val)],
        # INTENCIONALMENTE inconsistente: 15 dias pero fechas que solo cubren 7
        [Paragraph("Fecha inicio:", lbl),            Paragraph("2026-05-01", val)],
        [Paragraph("Fecha fin:", lbl),               Paragraph("2026-05-08", val)],
    ]
    t2 = Table(data2, colWidths=[5*cm, 10*cm])
    t2.setStyle(TableStyle([("VALIGN", (0,0), (-1,-1), "TOP"), ("TOPPADDING", (0,0), (-1,-1), 3)]))
    story.append(t2)

    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph(
        "<b>ATENCION:</b> Los 15 dias declarados no coinciden con el rango de fechas "
        "(01/05 al 08/05 = 7 dias). Este documento presenta inconsistencia que debe ser "
        "corregida por el medico emisor antes de ser procesado.",
        ParagraphStyle("nota", parent=body, textColor=colors.HexColor("#DC2626"),
                       backColor=colors.HexColor("#FEF2F2"))
    ))

    story.append(Paragraph("MEDICO TRATANTE", heading))
    data3 = [
        [Paragraph("Medico tratante:", lbl),   Paragraph("Psiquiatra tratante (firma ilegible)", val)],
        [Paragraph("IPS:", lbl),               Paragraph("Centro de Salud Mental Sanitas", val)],
    ]
    t3 = Table(data3, colWidths=[5*cm, 10*cm])
    t3.setStyle(TableStyle([("VALIGN", (0,0), (-1,-1), "TOP"), ("TOPPADDING", (0,0), (-1,-1), 3)]))
    story.append(t3)

    story.append(Spacer(1, 1*cm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey))
    story.append(Paragraph("_________________________________", ParagraphStyle("firma", parent=val, alignment=TA_CENTER, spaceBefore=15)))
    story.append(Paragraph("Firma medico tratante y sello institucional", ParagraphStyle("firmalbl", parent=lbl, alignment=TA_CENTER)))

    doc.build(story)
    return path


# ─────────────────────────────────────────────────────────────────────────────
# CATEGORIA 3: DOCUMENTOS NO RELACIONADOS
# ─────────────────────────────────────────────────────────────────────────────

def gen_no_medico_practica_laboratorio():
    """Informe de practica de laboratorio de quimica - debe ser rechazado."""
    doc, path = make_doc("6_no_medico_practica_laboratorio.pdf")
    title, entity, heading, body, lbl, val, footer = styles()
    story = []

    story.append(Paragraph("UNIVERSIDAD AUTONOMA DE OCCIDENTE", entity))
    story.append(Paragraph("Facultad de Ciencias Basicas | Departamento de Quimica", ParagraphStyle("sub", parent=entity, fontSize=9, textColor=colors.grey)))
    story.append(Spacer(1, 0.3*cm))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#1D4ED8")))
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph("INFORME DE PRACTICA DE LABORATORIO", title))
    story.append(Paragraph("Practica No. 4 - Reacciones de Oxidacion-Reduccion", ParagraphStyle("num", parent=entity, fontSize=10, textColor=colors.HexColor("#1D4ED8"))))
    story.append(Spacer(1, 0.5*cm))

    story.append(Paragraph("DATOS DEL ESTUDIANTE", heading))
    data = [
        [Paragraph("Nombre:", lbl),           Paragraph("Juan Esteban Morales Cano", val)],
        [Paragraph("Codigo estudiantil:", lbl),Paragraph("2023145867", val)],
        [Paragraph("Asignatura:", lbl),        Paragraph("Quimica Organica II - Grupo 3", val)],
        [Paragraph("Docente:", lbl),           Paragraph("Prof. Martha Liliana Restrepo", val)],
        [Paragraph("Fecha de entrega:", lbl),  Paragraph("14 de mayo de 2026", val)],
    ]
    t = Table(data, colWidths=[5*cm, 10*cm])
    t.setStyle(TableStyle([("VALIGN", (0,0), (-1,-1), "TOP"), ("TOPPADDING", (0,0), (-1,-1), 3)]))
    story.append(t)

    story.append(Paragraph("1. OBJETIVO", heading))
    story.append(Paragraph(
        "Identificar y caracterizar reacciones de oxidacion-reduccion mediante el uso de permanganato "
        "de potasio (KMnO4) como agente oxidante, y determinar el potencial de reduccion estandar "
        "de distintos metales mediante la serie electroquimica.",
        body
    ))

    story.append(Paragraph("2. MATERIALES Y REACTIVOS", heading))
    story.append(Paragraph(
        "Permanganato de potasio 0.1M, acido sulfurico concentrado, hierro en polvo, cobre en "
        "lamina, zinc metalico, pipetas graduadas 10mL, buretas 50mL, vasos de precipitado 250mL, "
        "agitador magnetico, balanza analitica.",
        body
    ))

    story.append(Paragraph("3. PROCEDIMIENTO EXPERIMENTAL", heading))
    story.append(Paragraph(
        "Se prepararon soluciones de referencia a concentraciones de 0.01M, 0.05M y 0.1M. "
        "La temperatura se mantuvo constante a 25 grados Celsius. Se midio el pH inicial y final "
        "de cada reaccion. Se registro el cambio de color en la solucion de KMnO4 al adicionar "
        "los diferentes reductores.",
        body
    ))

    story.append(Paragraph("4. RESULTADOS", heading))
    results_data = [
        [Paragraph("<b>Metal</b>", body), Paragraph("<b>E (V)</b>", body), Paragraph("<b>Reaccion</b>", body)],
        [Paragraph("Zinc (Zn)", body),    Paragraph("-0.76 V", body),       Paragraph("Oxidacion espontanea", body)],
        [Paragraph("Hierro (Fe)", body),  Paragraph("-0.44 V", body),       Paragraph("Oxidacion moderada", body)],
        [Paragraph("Cobre (Cu)", body),   Paragraph("+0.34 V", body),       Paragraph("Sin reaccion observable", body)],
    ]
    tr = Table(results_data, colWidths=[5*cm, 3*cm, 7*cm])
    tr.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#DBEAFE")),
        ("GRID", (0,0), (-1,-1), 0.5, colors.lightgrey),
        ("TOPPADDING", (0,0), (-1,-1), 4),
    ]))
    story.append(tr)

    story.append(Paragraph("5. CONCLUSIONES", heading))
    story.append(Paragraph(
        "Los resultados obtenidos confirman que el zinc presenta mayor tendencia a oxidarse "
        "en comparacion con el hierro y el cobre, lo que concuerda con la serie electroquimica "
        "teorica. El error experimental promedio fue del 3.2%, dentro del rango aceptable.",
        body
    ))

    story.append(Paragraph("Calificacion asignada: _______  /  5.0", ParagraphStyle("cal", parent=val, alignment=TA_RIGHT, spaceBefore=20)))
    story.append(Paragraph("Universidad Autonoma de Occidente | Curso 2026-1 | Documento academico", footer))

    doc.build(story)
    return path


def gen_no_medico_poster_prevencion():
    """Poster de prevencion de accidentes laborales - debe ser rechazado a pesar de mencionar ARL."""
    doc, path = make_doc("7_no_medico_poster_prevencion_arl.pdf")
    title, entity, heading, body, lbl, val, footer = styles()
    story = []

    story.append(Paragraph("ARL SURA | PROGRAMA DE SEGURIDAD Y SALUD EN EL TRABAJO", entity))
    story.append(Spacer(1, 0.3*cm))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#DC2626")))
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph("PREVENCION DE ACCIDENTES LABORALES", title))
    story.append(Paragraph("Guia rapida para trabajadores | SST 2026", ParagraphStyle("num", parent=entity, fontSize=9, textColor=colors.grey)))
    story.append(Spacer(1, 0.5*cm))

    story.append(Paragraph("POR QUE OCURREN LOS ACCIDENTES DE TRABAJO?", heading))
    story.append(Paragraph(
        "Los accidentes laborales son eventos no deseados que interrumpen el proceso productivo "
        "y pueden causar lesiones a los trabajadores. Segun el Decreto 1072 de 2015, el empleador "
        "es responsable de implementar el Sistema de Gestion de Seguridad y Salud en el Trabajo (SG-SST).",
        body
    ))

    story.append(Paragraph("LAS 3 CAUSAS PRINCIPALES", heading))
    causas = [
        ["1. Condiciones inseguras",   "Equipos sin mantenimiento, falta de senalizacion, iluminacion deficiente."],
        ["2. Actos inseguros",          "No usar EPP, trabajar bajo efectos de sustancias, omitir procedimientos."],
        ["3. Factores del entorno",     "Ruido excesivo, temperaturas extremas, ergonomia inadecuada."],
    ]
    for causa, desc in causas:
        story.append(Paragraph(f"<b>{causa}:</b> {desc}", body))

    story.append(Paragraph("QUE HACER EN CASO DE ACCIDENTE LABORAL?", heading))
    pasos = [
        "Reportar inmediatamente al jefe directo y al area de Salud Ocupacional.",
        "Acudir a la IPS designada por la ARL SURA para atencion medica.",
        "El empleador debe reportar el accidente a la ARL en un maximo de 2 dias habiles.",
        "La ARL investigara el accidente para determinar su origen laboral.",
        "Si se determina origen laboral, la ARL SURA cubrira la incapacidad y el tratamiento.",
        "El trabajador tiene derecho a prestaciones economicas y asistenciales segun la Ley 1562 de 2012.",
    ]
    for i, paso in enumerate(pasos, 1):
        story.append(Paragraph(f"{i}. {paso}", body))

    story.append(Paragraph("ENFERMEDADES LABORALES MAS COMUNES", heading))
    story.append(Paragraph(
        "Segun cifras de Fasecolda 2025, las enfermedades laborales mas frecuentes en Colombia son: "
        "sindrome del tunel carpiano, lumbalgia ocupacional, hipoacusia neurosensorial, y "
        "trastornos musculoesqueleticos. La ARL financia programas de prevencion y vigilancia "
        "epidemiologica para reducir su incidencia.",
        body
    ))

    story.append(Paragraph("RECUERDA:", heading))
    story.append(Paragraph(
        "Usar siempre los Elementos de Proteccion Personal (EPP). Reportar condiciones inseguras. "
        "Participar en las capacitaciones de SST. Tu salud es lo mas importante.",
        ParagraphStyle("recuerda", parent=body, textColor=colors.HexColor("#065F46"), fontName="Helvetica-Bold")
    ))

    story.append(Spacer(1, 1*cm))
    story.append(Paragraph("ARL SURA | Programa SST | Material divulgativo - No es un certificado medico | 2026", footer))

    doc.build(story)
    return path


def gen_no_medico_factura():
    """Factura comercial - debe ser rechazada inmediatamente."""
    doc, path = make_doc("8_no_medico_factura_comercial.pdf")
    title, entity, heading, body, lbl, val, footer = styles()
    story = []

    story.append(Paragraph("DISTRIBUIDORA COMERCIAL DEL PACIFICO S.A.S.", entity))
    story.append(Paragraph("NIT 900.456.123-5 | Tel: (604) 448-2200 | Cali, Colombia", ParagraphStyle("nit", parent=entity, fontSize=8, textColor=colors.grey)))
    story.append(Spacer(1, 0.3*cm))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#475569")))
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph("FACTURA DE VENTA ELECTRONICA", title))
    story.append(Paragraph("No. FE-2026-007423 | CUFE: a3f9b2c1d4e5...", ParagraphStyle("num", parent=entity, fontSize=8, textColor=colors.grey)))
    story.append(Spacer(1, 0.5*cm))

    story.append(Paragraph("CLIENTE", heading))
    data = [
        [Paragraph("Razon social:", lbl),    Paragraph("Supermercados La Economia Ltda.", val)],
        [Paragraph("NIT:", lbl),              Paragraph("805.002.311-7", val)],
        [Paragraph("Direccion:", lbl),        Paragraph("Cra 15 No. 23-45, Cali", val)],
        [Paragraph("Fecha factura:", lbl),    Paragraph("15 de mayo de 2026", val)],
        [Paragraph("Fecha vencimiento:", lbl),Paragraph("15 de junio de 2026", val)],
    ]
    t = Table(data, colWidths=[5*cm, 10*cm])
    t.setStyle(TableStyle([("VALIGN", (0,0), (-1,-1), "TOP"), ("TOPPADDING", (0,0), (-1,-1), 3)]))
    story.append(t)

    story.append(Paragraph("DETALLE DE PRODUCTOS", heading))
    items = [
        [Paragraph("<b>Descripcion</b>", body), Paragraph("<b>Cant.</b>", body), Paragraph("<b>V. Unitario</b>", body), Paragraph("<b>Total</b>", body)],
        [Paragraph("Arroz Diana x 500g", body),   Paragraph("200", body), Paragraph("$2.800", body), Paragraph("$560.000", body)],
        [Paragraph("Aceite Palma 1L", body),       Paragraph("150", body), Paragraph("$8.500", body), Paragraph("$1.275.000", body)],
        [Paragraph("Azucar blanca x 1kg", body),   Paragraph("300", body), Paragraph("$3.200", body), Paragraph("$960.000", body)],
        [Paragraph("Leche Colanta 1L", body),       Paragraph("500", body), Paragraph("$3.100", body), Paragraph("$1.550.000", body)],
    ]
    ti = Table(items, colWidths=[7*cm, 2*cm, 3.5*cm, 3.5*cm])
    ti.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#E2E8F0")),
        ("GRID", (0,0), (-1,-1), 0.5, colors.lightgrey),
        ("ALIGN", (1,0), (-1,-1), "RIGHT"),
        ("TOPPADDING", (0,0), (-1,-1), 4),
    ]))
    story.append(ti)

    totals = [
        [Paragraph("Subtotal:", lbl),  Paragraph("$4.345.000", val)],
        [Paragraph("IVA 19%:", lbl),   Paragraph("$825.550", val)],
        [Paragraph("<b>TOTAL:</b>", lbl), Paragraph("<b>$5.170.550</b>", val)],
    ]
    tt = Table(totals, colWidths=[12*cm, 4*cm])
    tt.setStyle(TableStyle([
        ("ALIGN", (1,0), (1,-1), "RIGHT"),
        ("TOPPADDING", (0,0), (-1,-1), 3),
        ("LINEABOVE", (0,2), (-1,2), 1, colors.black),
    ]))
    story.append(tt)

    story.append(Paragraph("Forma de pago: Credito 30 dias | Banco Bogota Cta. 456-234567-8", body))
    story.append(Paragraph("Documento tributario valido con firma y sello | DIAN | Resolucion 18764000366847 del 2024", footer))

    doc.build(story)
    return path


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    generators = [
        ("1_valido_enfermedad_comun.pdf",        gen_valido_enfermedad_comun),
        ("2_valido_accidente_laboral.pdf",        gen_valido_accidente_laboral),
        ("3_incompleto_sin_fechas.pdf",           gen_incompleto_sin_fechas),
        ("4_incompleto_sin_codigo_cie10.pdf",     gen_incompleto_sin_cie10),
        ("5_incompleto_fechas_inconsistentes.pdf",gen_fechas_inconsistentes),
        ("6_no_medico_practica_laboratorio.pdf",  gen_no_medico_practica_laboratorio),
        ("7_no_medico_poster_prevencion_arl.pdf", gen_no_medico_poster_prevencion),
        ("8_no_medico_factura_comercial.pdf",     gen_no_medico_factura),
    ]

    print("\nGenerando documentos de ejemplo para Nomisalud...")
    print(f"Carpeta de salida: {OUTPUT_DIR}\n")

    for name, fn in generators:
        try:
            path = fn()
            print(f"  [OK] {name}")
        except Exception as e:
            print(f"  [ERROR] {name}: {e}")

    print(f"\nListo. {len(generators)} archivos generados en static/ejemplos/")
    print("\nRESUMEN DE COMPORTAMIENTO ESPERADO EN NOMISALUD:")
    print("  VALIDOS (alta confianza, EN_VERIFICACION):")
    print("    1_valido_enfermedad_comun.pdf      - CIE-10 + fechas + paciente + cedula + medico")
    print("    2_valido_accidente_laboral.pdf     - Igual, origen laboral, ARL SURA")
    print("  CON ADVERTENCIAS (pasan pero con alerta naranja):")
    print("    3_incompleto_sin_fechas.pdf        - Tiene CIE-10 y paciente, faltan fechas y dias")
    print("    4_incompleto_sin_codigo_cie10.pdf  - Tiene fechas y paciente, falta CIE-10")
    print("    5_incompleto_fechas_inconsistentes.pdf - 15 dias declarados pero fechas = 7 dias")
    print("  RECHAZADOS (OTRO, REQUIERE_CORRECCION):")
    print("    6_no_medico_practica_laboratorio.pdf  - Informe academico de quimica")
    print("    7_no_medico_poster_prevencion_arl.pdf - Poster SST que menciona ARL pero sin campos")
    print("    8_no_medico_factura_comercial.pdf     - Factura de venta, sin relacion medica")
