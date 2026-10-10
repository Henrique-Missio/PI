// ── Estado global ──
let usuarioAtual  = null;
let todosItens    = [];
let itemAtual     = null;

// ── Referências DOM ──
const corpoTabela  = document.getElementById("corpo-tabela");
const contagem     = document.getElementById("contagem");
const modal        = document.getElementById("modal");
const modalTitulo  = document.getElementById("modal-titulo");
const modalConteudo= document.getElementById("modal-conteudo");
const modalRodape  = document.getElementById("modal-rodape");
const modalFechar  = document.getElementById("modal-fechar");
const modalEditar  = document.getElementById("modal-editar");
const modalExcluir = document.getElementById("modal-excluir");

// ── Badge de status ──
function badgeStatus(status) {
  if (!status) return "—";
  const classes = {
    "Funcional":      "badge-funcional",
    "Não funcional":  "badge-nao-funcional",
    "Em conserto":    "badge-em-conserto",
    "Reservado":      "badge-reservado",
    "Doado":          "badge-doado",
  };
  const cls = classes[status] || "";
  return `<span class="badge ${cls}">${status}</span>`;
}

function badgeCategoria(cat) {
  if (!cat) return "—";
  const label = cat === "aparelho" ? "Aparelho" : "Peça";
  const cls   = cat === "aparelho" ? "badge-categoria-aparelho" : "badge-categoria-peca";
  return `<span class="badge ${cls}">${label}</span>`;
}

// ── Código do item (identificação única, ex: #0007) ──
function codigoItem(item) {
  const prefixo = item.categoria === "aparelho" ? "AP" : "PC";
  const numero  = String(item.id).padStart(4, "0");
  return `${prefixo}-${numero}`;
}

// ── Renderizar tabela ──
function renderizarTabela(itens) {
  corpoTabela.innerHTML = "";
  contagem.textContent  = itens.length;

  if (!itens.length) {
    corpoTabela.innerHTML = `<tr><td colspan="8" class="td-vazio">Nenhum item encontrado. Tente ajustar os filtros.</td></tr>`;
    return;
  }

  const ehAdmin = usuarioAtual && usuarioAtual.tipo === "administrador";
  const podeEditar = !!usuarioAtual; // mesma regra do botão "Editar" dentro do modal

  itens.forEach(item => {
    const tr = document.createElement("tr");
    tr.className = "clicavel";
    // Nota: informações e problema NÃO ficam mais em tooltip na linha —
    // só aparecem ao abrir o modal (clique na linha), como pedido na revisão.

    tr.innerHTML = `
      <td class="td-codigo">${codigoItem(item)}</td>
      <td>${badgeCategoria(item.categoria)}</td>
      <td class="td-nome">${item.nome || "—"}</td>
      <td class="td-secundario">${item.marca || "—"}</td>
      <td>${badgeStatus(item.status)}</td>
      <td class="td-secundario">${item.data_entrada || "—"}</td>
      <td class="td-secundario">${item.data_saida || "—"}</td>
      <td class="td-acoes"></td>
    `;

    tr.addEventListener("click", () => abrirModal(item));

    // Botões de ação diretos na linha, com o MESMO estilo do rodapé do modal
    // (btn-secondary-dark para editar, btn-danger para excluir), só que compactos.
    const tdAcoes = tr.querySelector(".td-acoes");
    const grupoAcoes = document.createElement("div");
    grupoAcoes.className = "acoes-linha";

    if (podeEditar) {
      const btnEditar = document.createElement("button");
      btnEditar.className = "btn btn-secondary-dark btn-sm btn-icone";
      btnEditar.title = "Editar item";
      btnEditar.setAttribute("aria-label", "Editar item");
      btnEditar.innerHTML = "✎";
      btnEditar.addEventListener("click", (e) => {
        e.stopPropagation(); // não abre o modal em modo visualização
        abrirModal(item);
        modalEditar.click();
      });
      grupoAcoes.appendChild(btnEditar);
    }

    if (ehAdmin) {
      const btnExcluir = document.createElement("button");
      btnExcluir.className = "btn btn-danger btn-sm btn-icone";
      btnExcluir.title = "Excluir item";
      btnExcluir.setAttribute("aria-label", "Excluir item");
      btnExcluir.innerHTML = "🗑";
      btnExcluir.addEventListener("click", async (e) => {
        e.stopPropagation(); // não abre o modal ao clicar em excluir
        if (!confirm(`Excluir "${item.nome}"? Esta ação não pode ser desfeita.`)) return;
        const rota = item.categoria === "aparelho" ? `aparelhos/${item.id}` : `pecas/${item.id}`;
        try {
          const resp = await fetch(`/api/${rota}`, { method: "DELETE" });
          if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
          await carregarEstoque();
        } catch (erro) {
          alert(`Erro ao excluir: ${erro.message}`);
        }
      });
      grupoAcoes.appendChild(btnExcluir);
    }

    tdAcoes.appendChild(grupoAcoes);
    corpoTabela.appendChild(tr);
  });
}

// ── Filtros ──
function aplicarFiltros() {
  const fCategoria = document.getElementById("f-categoria").value.toLowerCase();
  const fStatus    = document.getElementById("f-status").value;
  const fNome      = document.getElementById("f-nome").value.toLowerCase();
  const fMarca     = document.getElementById("f-marca").value.toLowerCase();
  const fDataDe    = document.getElementById("f-data-de").value;
  const fDataAte   = document.getElementById("f-data-ate").value;

  const filtrado = todosItens.filter(item => {
    if (fCategoria && item.categoria !== fCategoria) return false;
    if (fStatus && item.status !== fStatus) return false;
    if (fNome  && !(item.nome  || "").toLowerCase().includes(fNome))  return false;
    if (fMarca && !(item.marca || "").toLowerCase().includes(fMarca)) return false;
    if (fDataDe && item.data_entrada && item.data_entrada < fDataDe) return false;
    if (fDataAte && item.data_entrada && item.data_entrada > fDataAte) return false;
    return true;
  });

  renderizarTabela(filtrado);
}

["f-categoria","f-status","f-nome","f-marca","f-data-de","f-data-ate"].forEach(id => {
  document.getElementById(id).addEventListener("input", aplicarFiltros);
  document.getElementById(id).addEventListener("change", aplicarFiltros);
});

document.getElementById("btn-limpar-filtros").addEventListener("click", () => {
  ["f-categoria","f-status","f-nome","f-marca","f-data-de","f-data-ate"]
    .forEach(id => document.getElementById(id).value = "");
  aplicarFiltros();
});

// ── Carregar estoque ──
async function carregarEstoque() {
  try {
    const resposta = await fetch("/api/estoque");
    if (!resposta.ok) throw new Error(`HTTP ${resposta.status}`);
    todosItens = await resposta.json();
    aplicarFiltros();
  } catch (erro) {
    corpoTabela.innerHTML = `<tr><td colspan="8" class="td-vazio">Erro ao carregar: ${erro.message}</td></tr>`;
  }
}

document.getElementById("btn-recarregar").addEventListener("click", carregarEstoque);

// ── Modal ──
const CAMPOS_STATUS = ["Funcional","Não funcional","Em conserto","Reservado","Doado"];

function abrirModal(item) {
  itemAtual = item;
  modalTitulo.textContent = `${codigoItem(item)} — ${item.nome || "Item"} — ${item.marca || ""}`;
  modalConteudo.innerHTML = "";

  const campos = [
    { rotulo: "Categoria",      valor: item.categoria === "aparelho" ? "Aparelho" : "Peça" },
    { rotulo: "Status",         valor: item.status },
    { rotulo: "Informações",    valor: item.informacoes },
    { rotulo: "Problema",       valor: item.problema },
    { rotulo: "Data de entrada",valor: item.data_entrada },
    { rotulo: "Data de saída",  valor: item.data_saida },
  ];

  campos.forEach(({ rotulo, valor }) => {
    if (!valor) return;
    const div = document.createElement("div");
    div.className = "modal-linha";
    div.innerHTML = `
      <span class="modal-rotulo">${rotulo}</span>
      <span class="modal-valor">${valor}</span>
    `;
    modalConteudo.appendChild(div);
  });

  // botão excluir só para admin
  modalExcluir.style.display =
    (usuarioAtual && usuarioAtual.tipo === "administrador") ? "inline-flex" : "none";

  modalRodape.style.display = "flex";
  modal.style.display = "flex";
}

function fecharModal() {
  modal.style.display = "none";
  itemAtual = null;
}

modalFechar.onclick = fecharModal;
modal.onclick = (e) => { if (e.target === modal) fecharModal(); };

// ── Modal: excluir ──
modalExcluir.onclick = async () => {
  if (!itemAtual) return;
  const aviso = modalConteudo.querySelector(".aviso-login");
  if (!aviso) {
    if (!confirm(`Excluir "${itemAtual.nome}"? Esta ação não pode ser desfeita.`)) return;
  }

  const rota = itemAtual.categoria === "aparelho"
    ? `aparelhos/${itemAtual.id}`
    : `pecas/${itemAtual.id}`;

  try {
    const resp = await fetch(`/api/${rota}`, { method: "DELETE" });
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    fecharModal();
    await carregarEstoque();
  } catch (erro) {
    alert(`Erro ao excluir: ${erro.message}`);
  }
};

// ── Modal: editar ──
modalEditar.onclick = () => {
  if (!itemAtual) return;
  modalConteudo.innerHTML = "";
  modalRodape.style.display = "none";

  const campos = itemAtual.categoria === "aparelho"
    ? [
        { nome: "nome",         rotulo: "Nome *",          tipo: "text",   obrigatorio: true },
        { nome: "marca",        rotulo: "Marca *",         tipo: "text",   obrigatorio: true },
        { nome: "informacoes",  rotulo: "Informações *",   tipo: "text",   obrigatorio: true },
        { nome: "problema",     rotulo: "Problema",        tipo: "text" },
        { nome: "status",       rotulo: "Status *",        tipo: "select", obrigatorio: true },
        { nome: "data_entrada", rotulo: "Data de entrada", tipo: "date" },
        { nome: "data_saida",   rotulo: "Data de saída",   tipo: "date" },
      ]
    : [
        { nome: "nome",         rotulo: "Nome *",          tipo: "text",   obrigatorio: true },
        { nome: "marca",        rotulo: "Marca *",         tipo: "text",   obrigatorio: true },
        { nome: "informacoes",  rotulo: "Informações *",   tipo: "text",   obrigatorio: true },
        { nome: "problema",     rotulo: "Problema",        tipo: "text" },
        { nome: "status",       rotulo: "Status *",        tipo: "select", obrigatorio: true },
        { nome: "data_entrada", rotulo: "Data de entrada", tipo: "date" },
        { nome: "data_saida",   rotulo: "Data de saída",   tipo: "date" },
      ];

  const form = document.createElement("div");

  campos.forEach(campo => {
    const div = document.createElement("div");
    div.className = "campo";
    div.innerHTML = `<label>${campo.rotulo}</label>`;

    let el;
    if (campo.tipo === "select") {
      el = document.createElement("select");
      el.name = campo.nome;
      CAMPOS_STATUS.forEach(op => {
        const opt = document.createElement("option");
        opt.value = op;
        opt.textContent = op;
        if (itemAtual[campo.nome] === op) opt.selected = true;
        el.appendChild(opt);
      });
    } else {
      el = document.createElement("input");
      el.type = campo.tipo;
      el.name = campo.nome;
      // data de entrada não pode ser maior que hoje (validação também existe no backend)
      if (campo.nome === "data_entrada") el.max = new Date().toISOString().split("T")[0];
      if (campo.tipo === "date" && itemAtual[campo.nome]) {
        el.value = itemAtual[campo.nome];
      } else {
        el.value = itemAtual[campo.nome] || "";
      }
    }

    div.appendChild(el);
    form.appendChild(div);
  });

  // botões
  const acoes = document.createElement("div");
  acoes.style.cssText = "display:flex;gap:.5rem;justify-content:flex-end;margin-top:.5rem";

  const btnCancelar = document.createElement("button");
  btnCancelar.textContent = "Cancelar";
  btnCancelar.className = "btn btn-ghost";
  btnCancelar.onclick = () => abrirModal(itemAtual);

  const btnSalvar = document.createElement("button");
  btnSalvar.textContent = "Salvar";
  btnSalvar.className = "btn btn-primary";
  btnSalvar.onclick = async () => {
    const dados = {};
    campos.forEach(campo => {
      const el = form.querySelector(`[name="${campo.nome}"]`);
      if (!el) return;
      const valor = el.value.trim();
      if (campo.obrigatorio && !valor) {
        alert(`Preencha o campo "${campo.rotulo}".`);
        el.focus();
        throw new Error("campo obrigatorio");
      }
      if (valor) {
        if (campo.tipo === "date") {
          const [ano, mes, dia] = valor.split("-");
          dados[campo.nome] = `${dia}-${mes}-${ano}`;
        } else {
          dados[campo.nome] = valor;
        }
      }
    });

    const rota = itemAtual.categoria === "aparelho"
      ? `aparelhos/${itemAtual.id}`
      : `pecas/${itemAtual.id}`;

    try {
      const resp = await fetch(`/api/${rota}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(dados),
      });
      const corpo = await resp.json().catch(() => ({}));
      if (!resp.ok) throw new Error(corpo.erro || `HTTP ${resp.status}`);
      fecharModal();
      await carregarEstoque();
    } catch (erro) {
      if (erro.message !== "campo obrigatorio") alert(`Erro ao salvar: ${erro.message}`);
    }
  };

  acoes.appendChild(btnCancelar);
  acoes.appendChild(btnSalvar);
  form.appendChild(acoes);
  modalConteudo.appendChild(form);
};

// ── Header dinâmico ──
function getIniciais(nomeCompleto) {
  const partes = nomeCompleto.trim().split(" ").filter(Boolean);
  if (partes.length === 1) return partes[0][0].toUpperCase();
  return (partes[0][0] + partes[partes.length - 1][0]).toUpperCase();
}

function renderizarAuth() {
  const area = document.getElementById("area-auth");
  area.innerHTML = "";

  if (usuarioAtual) {
    const iniciais = getIniciais(usuarioAtual.nome_completo);
    const isAdmin  = usuarioAtual.tipo === "administrador";

    const itensMenu = isAdmin
      ? [
          { label: "Informações", href: "/perfil" },
          { label: "Voluntários", href: "/voluntarios" },
          { label: "Relatórios",  href: "/relatorios" },
          { label: "Sair", acao: "sair" },
        ]
      : [
          { label: "Informações", href: "/perfil" },
          { label: "Sair", acao: "sair" },
        ];

    const wrapper = document.createElement("div");
    wrapper.className = "avatar-wrapper";

    const avatar = document.createElement("button");
    avatar.className = "avatar-btn";
    avatar.setAttribute("aria-label", "Menu do usuário");
    avatar.textContent = iniciais;

    const dropdown = document.createElement("div");
    dropdown.className = "avatar-dropdown";

    const nomeItem = document.createElement("div");
    nomeItem.className = "avatar-dropdown-nome";
    nomeItem.textContent = usuarioAtual.nome_completo.split(" ")[0];
    dropdown.appendChild(nomeItem);

    const separador = document.createElement("div");
    separador.className = "avatar-dropdown-sep";
    dropdown.appendChild(separador);

    itensMenu.forEach(item => {
      if (item.acao === "sair") {
        const btn = document.createElement("button");
        btn.className = "avatar-dropdown-item avatar-dropdown-sair";
        btn.textContent = item.label;
        btn.onclick = async () => {
          await fetch("/api/logout", { method: "POST" });
          window.location.href = "/login";
        };
        dropdown.appendChild(btn);
      } else {
        const a = document.createElement("a");
        a.className = "avatar-dropdown-item";
        a.href = item.href;
        a.textContent = item.label;
        dropdown.appendChild(a);
      }
    });

    avatar.onclick = (e) => {
      e.stopPropagation();
      dropdown.classList.toggle("aberto");
    };

    document.addEventListener("click", () => dropdown.classList.remove("aberto"), { capture: true });

    wrapper.appendChild(avatar);
    wrapper.appendChild(dropdown);
    area.appendChild(wrapper);

    // botões de cadastro só para logados
    document.getElementById("acoes-admin").classList.remove("oculto");
  } else {
    const btnLogin = document.createElement("a");
    btnLogin.href = "/login";
    btnLogin.className = "btn btn-secondary btn-sm";
    btnLogin.textContent = "Login";

    const btnCadastro = document.createElement("a");
    btnCadastro.href = "/cadastro";
    btnCadastro.className = "btn btn-primary btn-sm";
    btnCadastro.textContent = "Cadastro";

    area.appendChild(btnLogin);
    area.appendChild(btnCadastro);
  }
}

async function verificarSessao() {
  try {
    const resp = await fetch("/api/me");
    usuarioAtual = resp.ok ? await resp.json() : null;
  } catch {
    usuarioAtual = null;
  }
  renderizarAuth();
}

// ── Mensagem pós-login ──
const msgLogin = sessionStorage.getItem("mensagem-login");
if (msgLogin) {
  const aviso = document.createElement("div");
  aviso.className = "mensagem-topo";
  aviso.textContent = msgLogin;
  document.body.appendChild(aviso);
  sessionStorage.removeItem("mensagem-login");
  setTimeout(() => aviso.remove(), 3000);
}

// ── Init ──
(async () => {
  await verificarSessao();
  await carregarEstoque();
})();
