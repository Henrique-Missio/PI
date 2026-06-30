"""
relatorio.py — Geração de relatório PDF do estoque Pids Tech
"""
from datetime import date
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

from sqlalchemy import select
from app.database import SessionLocal
from app.models import Aparelhos, Pecas

TEAL  = colors.HexColor("#0D9488")
DARK  = colors.HexColor("#0F172A")
SLATE = colors.HexColor("#64748B")
LIGHT = colors.HexColor("#F1F5F9")
WHITE = colors.white
RED   = colors.HexColor("#EF4444")
BLUE  = colors.HexColor("#3B82F6")
GRAY  = colors.HexColor("#94A3B8")
GREEN = colors.HexColor("#10B981")


def _parse_data(valor):
    if not valor:
        return None
    try:
        return date.fromisoformat(str(valor))
    except ValueError:
        return None


def gerar_dados_relatorio(data_de=None, data_ate=None, categoria=None, nome=None):
    session = SessionLocal()
    try:
        aparelhos = session.scalars(select(Aparelhos)).all()
        pecas     = session.scalars(select(Pecas)).all()

        itens = []
        for a in aparelhos:
            itens.append({**a.to_dict(), "categoria": "aparelho"})
        for p in pecas:
            itens.append({**p.to_dict(), "categoria": "peca"})

        de  = _parse_data(data_de)
        ate = _parse_data(data_ate)

        def dentro_periodo(item):
            entrada = _parse_data(item.get("data_entrada"))
            if not entrada:
                return True
            if de  and entrada < de:  return False
            if ate and entrada > ate: return False
            return True

        filtrado = [i for i in itens if (
            (not categoria or i["categoria"] == categoria) and
            (not nome or nome.lower() in (i.get("nome") or "").lower()) and
            dentro_periodo(i)
        )]

        hoje       = date.today()
        inicio_mes = hoje.replace(day=1)

        total       = len(filtrado)
        recebidos   = sum(1 for i in filtrado
                         if _parse_data(i.get("data_entrada")) and
                            _parse_data(i.get("data_entrada")) >= inicio_mes)
        doados      = sum(1 for i in filtrado if i.get("status") == "Doado")
        consertados = sum(1 for i in filtrado
                         if i.get("status") == "Funcional" and
                            _parse_data(i.get("data_entrada")) and
                            _parse_data(i.get("data_entrada")) >= inicio_mes)

        status_count = {}
        for i in filtrado:
            s = i.get("status") or "—"
            status_count[s] = status_count.get(s, 0) + 1

        por_mes = {}
        for i in filtrado:
            entrada = _parse_data(i.get("data_entrada"))
            if entrada:
                chave = entrada.strftime("%Y-%m")
                por_mes[chave] = por_mes.get(chave, 0) + 1

        return {
            "gerado_em":       hoje.strftime("%d/%m/%Y"),
            "periodo_de":      data_de or "—",
            "periodo_ate":     data_ate or "—",
            "categoria":       categoria or "Todos",
            "nome_filtro":     nome or "—",
            "total":           total,
            "recebidos_mes":   recebidos,
            "doados":          doados,
            "consertados_mes": consertados,
            "status_count":    status_count,
            "por_mes":         dict(sorted(por_mes.items())),
            "itens":           filtrado,
        }
    finally:
        session.close()


def _num(valor, cor):
    return Paragraph(
        f"<b><font size=22>{valor}</font></b>",
        ParagraphStyle("cv", alignment=TA_CENTER, textColor=cor,
                       fontName="Helvetica-Bold", leading=30,
                       spaceBefore=8, spaceAfter=8)
    )


def _label(texto):
    return Paragraph(
        texto,
        ParagraphStyle("cl", fontSize=8, textColor=GRAY,
                       fontName="Helvetica", alignment=TA_CENTER,
                       spaceBefore=8, spaceAfter=4)
    )


def gerar_pdf(dados):
    buf = BytesIO()
    W = A4[0] - 4*cm
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm,
        topMargin=2*cm, bottomMargin=2*cm
    )

    titulo_style = ParagraphStyle(
        "titulo", fontSize=16, textColor=WHITE,
        fontName="Helvetica-Bold", alignment=TA_LEFT, leading=22
    )
    sub_style = ParagraphStyle(
        "sub", fontSize=9, textColor=GRAY,
        fontName="Helvetica", alignment=TA_RIGHT, leading=14
    )
    secao_style = ParagraphStyle(
        "secao", fontSize=11, textColor=DARK,
        fontName="Helvetica-Bold", spaceBefore=18, spaceAfter=8
    )
    normal_style = ParagraphStyle(
        "normal", fontSize=9, textColor=SLATE,
        fontName="Helvetica", spaceAfter=4
    )

    story = []

    # ── Cabeçalho ──
    header = Table(
        [[
            Paragraph("Pids<b>Tech</b> — Relatório de Estoque", titulo_style),
            Paragraph(f"Gerado em<br/>{dados['gerado_em']}", sub_style),
        ]],
        colWidths=[W * 0.65, W * 0.35]
    )
    header.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), DARK),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",    (0, 0), (-1, -1), 16),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 16),
        ("LEFTPADDING",   (0, 0), (-1, -1), 16),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 16),
    ]))
    story.append(header)
    story.append(Spacer(1, 10))

    # ── Filtros ──
    story.append(Paragraph(
        f"Período: {dados['periodo_de']} a {dados['periodo_ate']}  |  "
        f"Categoria: {dados['categoria']}  |  Nome: {dados['nome_filtro']}",
        normal_style
    ))
    story.append(HRFlowable(width="100%", thickness=1, color=LIGHT, spaceAfter=10))

    # ── Cards resumo ──
    story.append(Paragraph("Resumo", secao_style))
    col = W / 4
    cards = Table(
        [
            [_label("TOTAL NO ESTOQUE"), _label("RECEBIDOS NO MÊS"),
             _label("CONSERTADOS NO MÊS"), _label("DOADOS")],
            [_num(dados["total"], DARK), _num(dados["recebidos_mes"], TEAL),
             _num(dados["consertados_mes"], BLUE), _num(dados["doados"], GREEN)],
        ],
        colWidths=[col] * 4
    )
    cards.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), DARK),
        ("BACKGROUND", (0, 1), (-1, 1), LIGHT),
        ("ALIGN",      (0, 0), (-1, -1), "CENTER"),
        ("VALIGN",     (0, 0), (-1, -1), "MIDDLE"),
        ("GRID",       (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ("TOPPADDING",    (0, 1), (-1, 1), 12),
        ("BOTTOMPADDING", (0, 1), (-1, 1), 12),
    ]))
    story.append(cards)
    story.append(Spacer(1, 16))

    # ── Distribuição por status ──
    story.append(Paragraph("Distribuição por Status", secao_style))
    if dados["status_count"]:
        rows = [["Status", "Quantidade"]]
        for s, q in dados["status_count"].items():
            rows.append([s, str(q)])
        t = Table(rows, colWidths=[W * 0.75, W * 0.25])
        t.setStyle(TableStyle([
            ("BACKGROUND",     (0, 0), (-1, 0), DARK),
            ("TEXTCOLOR",      (0, 0), (-1, 0), WHITE),
            ("FONTNAME",       (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE",       (0, 0), (-1, -1), 9),
            ("ALIGN",          (1, 0), (1, -1), "CENTER"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT]),
            ("GRID",           (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
            ("TOPPADDING",     (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING",  (0, 0), (-1, -1), 8),
            ("LEFTPADDING",    (0, 0), (-1, -1), 12),
        ]))
        story.append(t)
    else:
        story.append(Paragraph("Nenhum dado de status para o período selecionado.", normal_style))
    story.append(Spacer(1, 16))

    # ── Recebimentos por mês ──
    story.append(Paragraph("Recebimentos por Mês", secao_style))
    if dados["por_mes"]:
        nomes_mes = ["Jan","Fev","Mar","Abr","Mai","Jun","Jul","Ago","Set","Out","Nov","Dez"]
        rows = [["Mês", "Itens recebidos"]]
        for mes, qtd in dados["por_mes"].items():
            try:
                ano, m = mes.split("-")
                label = f"{nomes_mes[int(m)-1]}/{ano}"
            except Exception:
                label = mes
            rows.append([label, str(qtd)])
        t = Table(rows, colWidths=[W * 0.75, W * 0.25])
        t.setStyle(TableStyle([
            ("BACKGROUND",     (0, 0), (-1, 0), DARK),
            ("TEXTCOLOR",      (0, 0), (-1, 0), WHITE),
            ("FONTNAME",       (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE",       (0, 0), (-1, -1), 9),
            ("ALIGN",          (1, 0), (1, -1), "CENTER"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT]),
            ("GRID",           (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
            ("TOPPADDING",     (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING",  (0, 0), (-1, -1), 8),
            ("LEFTPADDING",    (0, 0), (-1, -1), 12),
        ]))
        story.append(t)
    else:
        story.append(Paragraph("Nenhum dado de recebimento para o período selecionado.", normal_style))
    story.append(Spacer(1, 16))

    # ── Lista de itens ──
    story.append(Paragraph("Itens do Estoque", secao_style))
    if dados["itens"]:
        rows = [["Nome", "Marca", "Categoria", "Status", "Entrada"]]
        for i in dados["itens"]:
            entrada = _parse_data(i.get("data_entrada"))
            rows.append([
                i.get("nome") or "—",
                i.get("marca") or "—",
                "Aparelho" if i.get("categoria") == "aparelho" else "Peça",
                i.get("status") or "—",
                entrada.strftime("%d/%m/%Y") if entrada else "—",
            ])
        t = Table(rows, colWidths=[W*0.3, W*0.2, W*0.15, W*0.18, W*0.17])
        t.setStyle(TableStyle([
            ("BACKGROUND",     (0, 0), (-1, 0), DARK),
            ("TEXTCOLOR",      (0, 0), (-1, 0), WHITE),
            ("FONTNAME",       (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE",       (0, 0), (-1, -1), 8),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT]),
            ("GRID",           (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
            ("TOPPADDING",     (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING",  (0, 0), (-1, -1), 6),
            ("LEFTPADDING",    (0, 0), (-1, -1), 8),
        ]))
        story.append(t)
    else:
        story.append(Paragraph("Nenhum item encontrado com os filtros aplicados.", normal_style))

    # ── Rodapé ──
    story.append(Spacer(1, 20))
    story.append(HRFlowable(width="100%", thickness=1, color=LIGHT))
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        "Pids Tech — Sistema de Gestão de Eletrônicos Doados | Senac",
        ParagraphStyle("rodape", fontSize=8, textColor=GRAY, alignment=TA_CENTER)
    ))

    doc.build(story)
    buf.seek(0)
    return buf.read()
