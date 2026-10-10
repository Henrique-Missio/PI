Chart.defaults.maintainAspectRatio = false;
let dadosAtivos = null;
let graficoAtivo = null;
let tipoGrafico  = "barras";

const btnGerar    = document.getElementById("btn-gerar");
const btnBaixar   = document.getElementById("btn-baixar");
const fPeriodo    = document.getElementById("f-periodo");
const grupoCustom = document.getElementById("grupo-custom");
const btnReset    = document.getElementById("btn-reset");

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
    if (val === "all") return { data_de: null, data_ate: null };

    const ate = new Date();
    const de  = new Date();
    de.setDate(de.getDate() - parseInt(val));
    return {
        data_de:  de.toISOString().split("T")[0],
        data_ate: ate.toISOString().split("T")[0],
    };
}

function montarParams() {
    const { data_de, data_ate } = calcularDatas();
    const categoria = document.getElementById("f-categoria").value;
    const status    = document.getElementById("f-status").value;
    const marca     = document.getElementById("f-marca").value.trim();
    const nome      = document.getElementById("f-nome").value.trim();

    const params = new URLSearchParams();
    if (data_de)   params.set("data_de",   data_de);
    if (data_ate)  params.set("data_ate",  data_ate);
    if (categoria) params.set("categoria", categoria);
    if (status)    params.set("status",    status);
    if (marca)     params.set("marca",     marca);
    if (nome)      params.set("nome",      nome);
    return params;
}

// ── Gerar relatório ──
btnGerar.addEventListener("click", async () => {
    btnGerar.disabled = true;
    btnGerar.textContent = "Carregando...";

    const params = montarParams();

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
    const params = montarParams();
    window.open(`/api/relatorio/pdf?${params}`, "_blank");
});

// ── Reset ──
btnReset.addEventListener("click", () => {
    fPeriodo.value = "30";
    grupoCustom.style.display = "none";
    document.getElementById("f-data-de").value  = "";
    document.getElementById("f-data-ate").value = "";
    document.getElementById("f-categoria").value = "";
    document.getElementById("f-status").value    = "";
    document.getElementById("f-marca").value     = "";
    document.getElementById("f-nome").value      = "";
    btnGerar.click();
});

// ── Renderizar ──
function renderizar(dados) {
    // cards
    document.getElementById("relatorio-cards").classList.remove("oculto");
    document.getElementById("card-total").textContent       = dados.total;
    document.getElementById("card-recebidos").textContent   = dados.recebidos_mes;
    document.getElementById("card-consertados").textContent = dados.consertados_mes;
    document.getElementById("card-doados").textContent      = dados.doados;

    // gráfico
    document.getElementById("area-grafico").classList.remove("oculto");
    renderizarGrafico(tipoGrafico, dados);

    // tabela
    const temItens = dados.itens && dados.itens.length > 0;
    document.getElementById("area-tabela").classList.toggle("oculto", !temItens);
    document.getElementById("relatorio-vazio").classList.toggle("oculto", temItens);

    if (temItens) {
        document.getElementById("label-contagem").textContent = `${dados.itens.length} item(s) encontrado(s)`;
        const tbody = document.getElementById("tabela-itens");
        tbody.innerHTML = "";
        dados.itens.forEach(i => {
            const tr = document.createElement("tr");
            const entrada = i.data_entrada ? formatarData(i.data_entrada) : "—";
            tr.innerHTML = `
                <td class="td-secundario">${codigoItem(i)}</td>
                <td class="td-nome">${i.nome || "—"}</td>
                <td>${badgeCategoria(i.categoria)}</td>
                <td class="td-secundario col-marca">${i.marca || "—"}</td>
                <td class="col-status">${badgeStatus(i.status)}</td>
                <td class="td-secundario col-entrada">${entrada}</td>
            `;
            tbody.appendChild(tr);
        });
    }
}

function codigoItem(i) {
    return (i.categoria === "aparelho" ? "AP-" : "PC-") + String(i.id).padStart(4, "0");
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
        const todosStatus = ["Funcional","Não funcional","Em conserto","Reservado"];
        const sc = dados.status_count || {};
        const labels = todosStatus;
        const values = todosStatus.map(s => sc[s] || 0);
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

    } else if (tipo === "categoria") {
        const cc = dados.categoria_count || {};
        const labels = Object.keys(cc);
        const values = labels.map(l => cc[l]);
        graficoAtivo = new Chart(canvas, {
            type: "bar",
            data: {
                labels,
                datasets: [{
                    label: "Quantidade",
                    data: values,
                    backgroundColor: ["#0369A1", "#9D174D"],
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

    } else if (tipo === "doacoes") {
        const pm = dados.por_mes_doacoes || {};
        const meses = Object.keys(pm).length ? Object.keys(pm) : [];
        const values = meses.map(m => pm[m]);
        if (!meses.length) {
            meses.push(new Date().toISOString().slice(0,7));
            values.push(0);
        }
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
                    label: "Doações",
                    data: values,
                    borderColor: "#7C3AED",
                    backgroundColor: "rgba(124,58,237,.12)",
                    tension: 0.4,
                    fill: true,
                    pointBackgroundColor: "#7C3AED",
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
    } else if (tipo === "proporcao") {
        graficoAtivo = new Chart(canvas, {
            type: "doughnut",
            data: {
                labels: ["Em estoque", "Doado"],
                datasets: [{
                    data: [dados.total, dados.doados],
                    backgroundColor: ["#0D9488", "#7C3AED"],
                    borderWidth: 0,
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: { position: "bottom" },
                    tooltip: { callbacks: { label: ctx => ` ${ctx.label}: ${ctx.parsed} item(s)` } }
                }
            }
        });

    } else {
        const pm = dados.por_mes || {};
        const meses = Object.keys(pm).length ? Object.keys(pm) : [];
        const values = meses.map(m => pm[m]);
        if (!meses.length) {
            // placeholder vazio
            meses.push(new Date().toISOString().slice(0,7));
            values.push(0);
        }
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
