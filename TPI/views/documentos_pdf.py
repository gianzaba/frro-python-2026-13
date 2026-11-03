"""Generación de documentos PDF (boleta de cobro y presupuesto de reclamos).

Pertenece a la capa de presentación: solo formatea datos que ya resolvió la capa de negocio.
"""
from io import BytesIO

from reportlab.graphics.barcode import code128
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

COLOR_PRIMARIO = colors.HexColor("#1e3a8a")
COLOR_SUAVE = colors.HexColor("#eef2ff")


def _estilos() -> dict:
    base = getSampleStyleSheet()
    return {
        "titulo": ParagraphStyle("titulo", parent=base["Title"], textColor=COLOR_PRIMARIO, fontSize=18),
        "sub": ParagraphStyle("sub", parent=base["Normal"], textColor=colors.HexColor("#475569"), fontSize=9),
        "h2": ParagraphStyle("h2", parent=base["Heading2"], textColor=COLOR_PRIMARIO, fontSize=12, spaceBefore=8),
        "normal": ParagraphStyle("normal", parent=base["Normal"], fontSize=10, leading=14),
        "chico": ParagraphStyle("chico", parent=base["Normal"], fontSize=8, textColor=colors.HexColor("#64748b")),
    }


def _dinero(valor: float) -> str:
    return "$ {:,.2f}".format(valor or 0.0).replace(",", "X").replace(".", ",").replace("X", ".")


def _tabla(filas: list, anchos: list, cabecera: bool = False) -> Table:
    tabla = Table(filas, colWidths=anchos)
    estilo = [
        ("FONTSIZE", (0, 0), (-1, -1), 9.5),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cbd5e1")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BACKGROUND", (0, 0), (0, -1), COLOR_SUAVE),
        ("PADDING", (0, 0), (-1, -1), 5),
    ]
    if cabecera:
        estilo += [
            ("BACKGROUND", (0, 0), (-1, 0), COLOR_PRIMARIO),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("BACKGROUND", (0, 1), (0, -1), colors.white),
        ]
    tabla.setStyle(TableStyle(estilo))
    return tabla


def _documento(historia: list) -> bytes:
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm,
                            topMargin=15 * mm, bottomMargin=15 * mm)
    doc.build(historia)
    return buffer.getvalue()


def generar_boleta_pdf(datos: dict) -> bytes:
    """Aviso de cobro mensual con vencimientos, datos bancarios y código de barras."""
    e = _estilos()
    cliente, propiedad = datos["cliente"], datos["propiedad"]
    banco = datos["datos_bancarios"]
    historia = [
        Paragraph("InmoGestión — Aviso de Cobro", e["titulo"]),
        Paragraph(f"Contrato N° {datos['nro_contrato']} · "
                  f"Período {datos['mes']}", e["sub"]),
        Spacer(1, 6 * mm),
        Paragraph("Datos del locatario e inmueble", e["h2"]),
        _tabla([
            ["Locatario", cliente.nombre_completo if cliente else "-"],
            ["Inmueble", propiedad.direccion if propiedad else "-"],
            ["Agente a cargo", datos["agente"].nombre_completo if datos.get("agente") else "-"],
        ], [45 * mm, 125 * mm]),
        Paragraph("Detalle de vencimientos", e["h2"]),
        _tabla([
            ["Concepto", "Vencimiento", "Importe"],
            ["1° vencimiento (sin recargo)", datos["fecha_1er_vencimiento"].strftime("%d/%m/%Y"),
             _dinero(datos["monto_base"])],
            ["2° vencimiento (recargo por mora 0,2% diario)",
             datos["fecha_2do_vencimiento"].strftime("%d/%m/%Y"), _dinero(datos["total_2do_vencimiento"])],
        ], [90 * mm, 35 * mm, 45 * mm], cabecera=True),
        Spacer(1, 2 * mm),
        Paragraph("Pasado el día 10 se aplica un recargo diario del 0,2% sobre el canon.", e["chico"]),
        Paragraph("Datos para transferencia bancaria", e["h2"]),
        _tabla([
            ["Banco", banco["banco"]],
            ["Titular", banco["titular"]],
            ["CBU", banco["cbu"]],
            ["Alias", banco["alias"]],
        ], [45 * mm, 125 * mm]),
        Spacer(1, 5 * mm),
    ]
    pago = datos.get("pago_registrado")
    if pago:
        historia.append(Paragraph(
            f"<b>PAGO REGISTRADO</b> el {pago.fecha_pago.strftime('%d/%m/%Y')} por "
            f"{_dinero(pago.monto_total_abonado)} "
            f"({'a término' if pago.dias_retraso == 0 else str(pago.dias_retraso) + ' días de mora'}).",
            e["normal"]))
    historia += [
        Spacer(1, 5 * mm),
        Paragraph("Código de seguimiento", e["h2"]),
        code128.Code128(datos["codigo_barras_ref"], barHeight=14 * mm, barWidth=0.5 * mm),
        Paragraph(datos["codigo_barras_ref"], e["chico"]),
        Spacer(1, 4 * mm),
        Paragraph(f"Enviar el comprobante indicando contrato #{datos['nro_contrato']} y mes {datos['mes']}.",
                  e["chico"]),
    ]
    return _documento(historia)


def generar_presupuesto_pdf(detalle: dict) -> bytes:
    """Informe formal de presupuesto de reparación para autorización del propietario."""
    e = _estilos()
    reclamo, propiedad = detalle["reclamo"], detalle["propiedad"]
    propietario, cliente, contrato = detalle["propietario"], detalle["cliente"], detalle["contrato"]
    historia = [
        Paragraph("Informe de Presupuesto de Reparación", e["titulo"]),
        Paragraph(f"Reclamo #{reclamo.id} · Emitido el {reclamo.fecha_reclamo.strftime('%d/%m/%Y')} · "
                  f"Urgencia: {reclamo.urgencia}", e["sub"]),
        Spacer(1, 6 * mm),
        Paragraph("Propietario", e["h2"]),
        _tabla([
            ["Nombre", propietario.nombre_completo if propietario else "-"],
            ["Documento", f"{propietario.tipo_doc} {propietario.nro_doc}" if propietario else "-"],
            ["Contacto", f"{propietario.email} · {propietario.telefono}" if propietario else "-"],
        ], [45 * mm, 125 * mm]),
        Paragraph("Inmueble y contrato", e["h2"]),
        _tabla([
            ["Dirección", propiedad.direccion if propiedad else "-"],
            ["Zona / Tipo", f"{propiedad.zona} ({propiedad.tipo})" if propiedad else "-"],
            ["Contrato", f"#{contrato.nro_contrato}" if contrato else "-"],
            ["Inquilino", cliente.nombre_completo if cliente else "-"],
        ], [45 * mm, 125 * mm]),
        Paragraph("Avería informada", e["h2"]),
        _tabla([
            ["Rubro", reclamo.tipo_dano],
            ["Descripción", Paragraph(reclamo.descripcion, e["normal"])],
            ["Presupuesto estimado", _dinero(reclamo.presupuesto_estimado)],
        ], [45 * mm, 125 * mm]),
    ]
    if reclamo.observaciones_resolucion:
        historia.append(Paragraph(f"Observaciones: {reclamo.observaciones_resolucion}", e["normal"]))
    historia += [
        Spacer(1, 22 * mm),
        _tabla([["Firma y aclaración del propietario (autorización)", "Fecha"]], [120 * mm, 50 * mm]),
        Spacer(1, 3 * mm),
        Paragraph("La firma implica la autorización para ejecutar el trabajo por el monto cotizado.", e["chico"]),
    ]
    return _documento(historia)
