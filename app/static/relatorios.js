let dadosAtivos = null;
let graficoAtivo = null;
let tipoGrafico  = "barras";

const btnGerar  = document.getElementById("btn-gerar");
const btnBaixar = document.getElementById("btn-baixar");
const fPeriodo  = document.getElementById("f-periodo");
const grupoCustom = document.getElementById("grupo-custom");

// ── Período ──
fPeriodo.addEventListener("change", () => {
    grupoCustom.style.display = fPeriodo.value === "custom" ? "flex" : "none";
});

function calcularDatas() {
    const val = fPeriodo.value;
    if (val === "custom") {
        return {
            data_de:  document.getElementById("f-data-de").value  || null,
            data_ate: document.getElementById("f-data-ate").value || null,
        };
    }
    const ate = new Date();
    const de  = new Date();
    de.setDate(de.getDate() - parseInt(val));
    return {
        data_de:  de.toISOString().split("T")[0],
        data_ate: ate.toISOString().split("T")[0],
    };
}

// ── Gerar relatório ──
btnGerar.addEventListener("click", async () => {
    btnGerar.disabled = true;
    btnGerar.textContent = "Carregando...";

    const { data_de, data_ate } = calcularDatas();
    const categoria = document.getElementById("f-categoria").value;
    const nome      = document.getElementById("f-nome").value.trim();

    const params = new URLSearchParams();
    if (data_de)  params.set("data_de",   data_de);
    if (data_ate) params.set("data_ate",  data_ate);
    if (categoria) params.set("categoria", categoria);
    if (nome)     params.set("nome",      nome);

    try {
        const resp = await fetch(`/api/relatorio/dados?${params}`);
        if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
        dadosAtivos = await resp.json();
        renderizar(dadosAtivos);
        btnBaixar.disabled = false;
    } catch (e) {
        alert("Erro ao gerar relatório: " + e.message);
    } finally {
        btnGerar.disabled = false;
        btnGerar.textContent = "Gerar";
    }
});

// ── Baixar PDF ──
btnBaixar.addEventListener("click", () => {
    const { data_de, data_ate } = calcularDatas();
    const categoria = document.getElementById("f-categoria").value;
    const nome      = document.getElementById("f-nome").value.trim();

    const params = new URLSearchParams();
    if (data_de)   params.set("data_de",   data_de);
    if (data_ate)  params.set("data_ate",  data_ate);
    if (categoria) params.set("categoria", categoria);
    if (nome)      params.set("nome",      nome);

    window.open(`/api/relatorio/pdf?${params}`, "_blank");
});

// ── Renderizar ──
function renderizar(dados) {
    // cards
    document.getElementById("relatorio-cards").style.display = "grid";
    document.getElementById("card-total").textContent       = dados.total;
    document.getElementById("card-recebidos").textContent   = dados.recebidos_mes;
    document.getElementById("card-consertados").textContent = dados.consertados_mes;
    document.getElementById("card-doados").textContent      = dados.doados;

    // gráfico
    document.getElementById("area-grafico").style.display = "block";
    renderizarGrafico(tipoGrafico, dados);

    // tabela
    const temItens = dados.itens && dados.itens.length > 0;
    document.getElementById("area-tabela").style.display   = temItens ? "block" : "none";
    document.getElementById("relatorio-vazio").style.display = temItens ? "none" : "block";

    if (temItens) {
        document.getElementById("label-contagem").textContent = `${dados.itens.length} item(s) encontrado(s)`;
        const tbody = document.getElementById("tabela-itens");
        tbody.innerHTML = "";
        dados.itens.forEach(i => {
            const tr = document.createElement("tr");
            const entrada = i.data_entrada ? formatarData(i.data_entrada) : "—";
            tr.innerHTML = `
                <td class="td-nome">${i.nome || "—"}</td>
                <td class="td-secundario">${i.marca || "—"}</td>
                <td>${badgeCategoria(i.categoria)}</td>
                <td>${badgeStatus(i.status)}</td>
                <td class="td-secundario">${entrada}</td>
            `;
            tbody.appendChild(tr);
        });
    }
}

function formatarData(str) {
    if (!str) return "—";
    const [ano, mes, dia] = str.split("-");
    return `${dia}/${mes}/${ano}`;
}

function badgeStatus(status) {
    if (!status) return "—";
    const classes = {
        "Funcional":     "badge-funcional",
        "Não funcional": "badge-nao-funcional",
        "Em conserto":   "badge-em-conserto",
        "Reservado":     "badge-reservado",
        "Doado":         "badge-doado",
    };
    return `<span class="badge ${classes[status] || ""}">${status}</span>`;
}

function badgeCategoria(cat) {
    const label = cat === "aparelho" ? "Aparelho" : "Peça";
    const cls   = cat === "aparelho" ? "badge-categoria-aparelho" : "badge-categoria-peca";
    return `<span class="badge ${cls}">${label}</span>`;
}

// ── Gráfico ──
const COR_STATUS = {
    "Funcional":     "#10B981",
    "Não funcional": "#EF4444",
    "Em conserto":   "#F59E0B",
    "Reservado":     "#3B82F6",
    "Doado":         "#94A3B8",
};

function renderizarGrafico(tipo, dados) {
    const canvas = document.getElementById("grafico-principal");
    if (graficoAtivo) { graficoAtivo.destroy(); graficoAtivo = null; }

    if (tipo === "barras") {
        const labels = Object.keys(dados.status_count);
        const values = Object.values(dados.status_count);
        const bgColors = labels.map(l => COR_STATUS[l] || "#64748B");

        graficoAtivo = new Chart(canvas, {
            type: "bar",
            data: {
                labels,
                datasets: [{
                    label: "Quantidade",
                    data: values,
                    backgroundColor: bgColors,
                    borderRadius: 6,
                    borderSkipped: false,
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: { display: false },
                    tooltip: { callbacks: { label: ctx => ` ${ctx.parsed.y} item(s)` } }
                },
                scales: {
                    y: { beginAtZero: true, ticks: { stepSize: 1 }, grid: { color: "#E2E8F0" } },
                    x: { grid: { display: false } }
                }
            }
        });
    } else {
        const meses = Object.keys(dados.por_mes);
        const values = Object.values(dados.por_mes);
        const labels = meses.map(m => {
            const [ano, mes] = m.split("-");
            const nomes = ["Jan","Fev","Mar","Abr","Mai","Jun","Jul","Ago","Set","Out","Nov","Dez"];
            return `${nomes[parseInt(mes)-1]}/${ano}`;
        });

        graficoAtivo = new Chart(canvas, {
            type: "line",
            data: {
                labels,
                datasets: [{
                    label: "Recebimentos",
                    data: values,
                    borderColor: "#0D9488",
                    backgroundColor: "rgba(13,148,136,.12)",
                    tension: 0.4,
                    fill: true,
                    pointBackgroundColor: "#0D9488",
                    pointRadius: 5,
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: { display: false },
                    tooltip: { callbacks: { label: ctx => ` ${ctx.parsed.y} item(s)` } }
                },
                scales: {
                    y: { beginAtZero: true, ticks: { stepSize: 1 }, grid: { color: "#E2E8F0" } },
                    x: { grid: { display: false } }
                }
            }
        });
    }
}

// ── Tabs do gráfico ──
document.querySelectorAll(".grafico-tab").forEach(btn => {
    btn.addEventListener("click", () => {
        document.querySelectorAll(".grafico-tab").forEach(b => b.classList.remove("ativo"));
        btn.classList.add("ativo");
        tipoGrafico = btn.dataset.tipo;
        if (dadosAtivos) renderizarGrafico(tipoGrafico, dadosAtivos);
    });
});

// ── Gerar automaticamente ao carregar ──
btnGerar.click();
