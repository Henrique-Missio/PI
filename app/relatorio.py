"""
relatorio.py — Geração de relatório PDF do estoque Pids Tech
"""
from datetime import date, timedelta
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT

from sqlalchemy import select
from app.database import SessionLocal
from app.models import Aparelhos, Pecas


# ── Cores do sistema ──
TEAL = colors.HexColor("#0D9488")
DARK = colors.HexColor("#0F172A")
SLATE = colors.HexColor("#64748B")
LIGHT = colors.HexColor("#F1F5F9")
WHITE = colors.white
RED = colors.HexColor("#EF4444")
YELLOW = colors.HexColor("#F59E0B")
BLUE = colors.HexColor("#3B82F6")
GRAY = colors.HexColor("#94A3B8")


def _parse_data(valor):
    """AAAA-MM-DD → date"""
    if not valor:
        return None
    try:
        return date.fromisoformat(str(valor))
    except ValueError:
        return None


def gerar_dados_relatorio(data_de=None, data_ate=None, categoria=None, nome=None):
    """
    Retorna dict com métricas e listas filtradas.
    data_de / data_ate: strings 'AAAA-MM-DD'
    categoria: 'aparelho' | 'peca' | None
    nome: substring do nome do item
    """
    session = SessionLocal()
    try:
        aparelhos = session.scalars(select(Aparelhos)).all()
        pecas = session.scalars(select(Pecas)).all()

        # montar lista unificada
        itens = []
        for a in aparelhos:
            itens.append({**a.to_dict(), "categoria": "aparelho"})
        for p in pecas:
            itens.append({**p.to_dict(), "categoria": "peca"})

        # filtrar
        de = _parse_data(data_de)
        ate = _parse_data(data_ate)

        def dentro_periodo(item):
            entrada = _parse_data(item.get("data_entrada"))
            if not entrada:
                return True
            if de and entrada < de:
                return False
            if ate and entrada > ate:
                return False
            return True

        filtrado = [i for i in itens if (
            (not categoria or i["categoria"] == categoria) and
            (not nome or nome.lower() in (i.get("nome") or "").lower()) and
            dentro_periodo(i)
        )]

        # métricas
        hoje = date.today()
        inicio_mes = hoje.replace(day=1)

        total = len(filtrado)
        recebidos = sum(1 for i in filtrado if _parse_data(
            i.get("data_entrada")) and _parse_data(i.get("data_entrada")) >= inicio_mes)
        doados = sum(1 for i in filtrado if i.get("status") == "Doado")
        consertados = sum(1 for i in filtrado if i.get("status") == "Funcional" and _parse_data(
            i.get("data_entrada")) and _parse_data(i.get("data_entrada")) >= inicio_mes)

        # contagem por status
        status_count = {}
        for i in filtrado:
            s = i.get("status") or "—"
            status_count[s] = status_count.get(s, 0) + 1

        # recebimentos por mês (últimos 6 meses)
        por_mes = {}
        for i in filtrado:
            entrada = _parse_data(i.get("data_entrada"))
            if entrada:
                chave = entrada.strftime("%Y-%m")
                por_mes[chave] = por_mes.get(chave, 0) + 1

        return {
            "gerado_em":   hoje.strftime("%d/%m/%Y"),
            "periodo_de":  data_de or "—",
            "periodo_ate": data_ate or "—",
            "categoria":   categoria or "Todos",
            "nome_filtro": nome or "—",
            "total":       total,
            "recebidos_mes": recebidos,
            "doados":      doados,
            "consertados_mes": consertados,
            "status_count": status_count,
            "por_mes":     dict(sorted(por_mes.items())),
            "itens":       filtrado,
        }
    finally:
        session.close()


def gerar_pdf(dados):
    """Recebe dict de gerar_dados_relatorio(), retorna bytes do PDF."""
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm,
        topMargin=2*cm, bottomMargin=2*cm
    )

    styles = getSampleStyleSheet()
    titulo_style = ParagraphStyle("titulo", fontSize=20, textColor=WHITE,
                                  fontName="Helvetica-Bold", alignment=TA_LEFT, spaceAfter=4)
    sub_style = ParagraphStyle(
        "sub", fontSize=9, textColor=GRAY, fontName="Helvetica", alignment=TA_LEFT)
    secao_style = ParagraphStyle("secao", fontSize=11, textColor=DARK,
                                 fontName="Helvetica-Bold", spaceBefore=16, spaceAfter=6)
    normal_style = ParagraphStyle(
        "normal", fontSize=9, textColor=SLATE, fontName="Helvetica", spaceAfter=4)

    story = []

    # ── Cabeçalho ──
    header_data = [[
        Paragraph("<b>Pids</b>Tech — Relatório de Estoque", titulo_style),
        Paragraph(f"Gerado em {dados['gerado_em']}", sub_style),
    ]]
    header_table = Table(header_data, colWidths=["70%", "30%"])
    header_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), DARK),
        ("VALIGN",     (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 14),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 14),
        ("LEFTPADDING",   (0, 0), (-1, -1), 16),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 16),
        ("ROUNDEDCORNERS", [6, 6, 6, 6]),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 12))

    # ── Filtros aplicados ──
    filtros_txt = (
        f"Período: {dados['periodo_de']} a {dados['periodo_ate']}  |  "
        f"Categoria: {dados['categoria']}  |  "
        f"Nome: {dados['nome_filtro']}"
    )
    story.append(Paragraph(filtros_txt, normal_style))
    story.append(HRFlowable(width="100%", thickness=1,
                 color=LIGHT, spaceAfter=12))

    # ── Cards de resumo ──
    story.append(Paragraph("Resumo", secao_style))
    cards = [
        ["Total no estoque", "Recebidos no mês", "Consertados no mês", "Doados"],
        [
            Paragraph(f"<b><font size=20>{dados['total']}</font></b>", ParagraphStyle(
                "n", alignment=TA_CENTER, textColor=DARK, fontName="Helvetica-Bold")),
            Paragraph(f"<b><font size=20>{dados['recebidos_mes']}</font></b>", ParagraphStyle(
                "n", alignment=TA_CENTER, textColor=TEAL, fontName="Helvetica-Bold")),
            Paragraph(f"<b><font size=20>{dados['consertados_mes']}</font></b>", ParagraphStyle(
                "n", alignment=TA_CENTER, textColor=BLUE, fontName="Helvetica-Bold")),
            Paragraph(f"<b><font size=20>{dados['doados']}</font></b>", ParagraphStyle(
                "n", alignment=TA_CENTER, textColor=colors.HexColor("#10B981"), fontName="Helvetica-Bold")),
        ]
    ]
    cards_table = Table(cards, colWidths=["25%"]*4)
    cards_table.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0), DARK),
        ("TEXTCOLOR",     (0, 0), (-1, 0), GRAY),
        ("FONTNAME",      (0, 0), (-1, 0), "Helvetica"),
        ("FONTSIZE",      (0, 0), (-1, 0), 8),
        ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",    (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("BACKGROUND",    (0, 1), (-1, 1), LIGHT),
        ("GRID",          (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ("ROUNDEDCORNERS", [4, 4, 4, 4]),
    ]))
    story.append(cards_table)
    story.append(Spacer(1, 16))

    # ── Distribuição por status ──
    if dados["status_count"]:
        story.append(Paragraph("Distribuição por Status", secao_style))
        status_rows = [["Status", "Quantidade"]]
        status_colors_map = {
            "Funcional":     colors.HexColor("#10B981"),
            "Não funcional": RED,
            "Em conserto":   YELLOW,
            "Reservado":     BLUE,
            "Doado":         GRAY,
        }
        for status, qtd in dados["status_count"].items():
            status_rows.append([status, str(qtd)])

        st = Table(status_rows, colWidths=["75%", "25%"])
        st.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, 0), DARK),
            ("TEXTCOLOR",     (0, 0), (-1, 0), WHITE),
            ("FONTNAME",      (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE",      (0, 0), (-1, -1), 9),
            ("ALIGN",         (1, 0), (1, -1), "CENTER"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT]),
            ("GRID",          (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
            ("TOPPADDING",    (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ("LEFTPADDING",   (0, 0), (-1, -1), 10),
        ]))
        story.append(st)
        story.append(Spacer(1, 16))

    # ── Recebimentos por mês ──
    if dados["por_mes"]:
        story.append(Paragraph("Recebimentos por Mês", secao_style))
        mes_rows = [["Mês", "Itens recebidos"]]
        for mes, qtd in dados["por_mes"].items():
            try:
                ano, m = mes.split("-")
                label = date(int(ano), int(m), 1).strftime(
                    "%b/%Y").capitalize()
            except Exception:
                label = mes
            mes_rows.append([label, str(qtd)])

        mt = Table(mes_rows, colWidths=["75%", "25%"])
        mt.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, 0), DARK),
            ("TEXTCOLOR",     (0, 0), (-1, 0), WHITE),
            ("FONTNAME",      (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE",      (0, 0), (-1, -1), 9),
            ("ALIGN",         (1, 0), (1, -1), "CENTER"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT]),
            ("GRID",          (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
            ("TOPPADDING",    (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ("LEFTPADDING",   (0, 0), (-1, -1), 10),
        ]))
        story.append(mt)
        story.append(Spacer(1, 16))

    # ── Lista de itens ──
    story.append(Paragraph("Itens do Estoque", secao_style))
    if dados["itens"]:
        item_rows = [["Nome", "Marca", "Categoria", "Status", "Entrada"]]
        for i in dados["itens"]:
            entrada = _parse_data(i.get("data_entrada"))
            item_rows.append([
                i.get("nome") or "—",
                i.get("marca") or "—",
                "Aparelho" if i.get("categoria") == "aparelho" else "Peça",
                i.get("status") or "—",
                entrada.strftime("%d/%m/%Y") if entrada else "—",
            ])
        it = Table(item_rows, colWidths=["30%", "20%", "15%", "18%", "17%"])
        it.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, 0), DARK),
            ("TEXTCOLOR",     (0, 0), (-1, 0), WHITE),
            ("FONTNAME",      (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE",      (0, 0), (-1, -1), 8),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT]),
            ("GRID",          (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
            ("TOPPADDING",    (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING",   (0, 0), (-1, -1), 8),
        ]))
        story.append(it)
    else:
        story.append(
            Paragraph("Nenhum item encontrado com os filtros aplicados.", normal_style))

    # ── Rodapé ──
    story.append(Spacer(1, 20))
    story.append(HRFlowable(width="100%", thickness=1, color=LIGHT))
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        "Pids Tech — Sistema de Gestão de Eletrônicos Doados | Senac",
        ParagraphStyle("rodape", fontSize=8,
                       textColor=GRAY, alignment=TA_CENTER)
    ))

    doc.build(story)
    buf.seek(0)
    return buf.read()
