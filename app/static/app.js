const modal = document.getElementById("modal");
const modalTitulo = document.getElementById("modal-titulo");
const modalConteudo = document.getElementById("modal-conteudo");
const modalFechar = document.getElementById("modal-fechar");
const modalEditar = document.getElementById("modal-editar");
const modalExcluir = document.getElementById("modal-excluir");
let itemAtual = null;
let usuarioAtual = null;

const mensagemLogin = sessionStorage.getItem("mensagem-login");
if (mensagemLogin) {
  const aviso = document.createElement("div");
  aviso.className = "mensagem sucesso mensagem-topo";
  aviso.textContent = mensagemLogin;
  document.body.insertBefore(aviso, document.body.firstChild);
  sessionStorage.removeItem("mensagem-login");

  setTimeout(() => aviso.remove(), 3000);
}

modalFechar.addEventListener("click", () => modal.style.display = "none");
modal.addEventListener("click", (e) => { if (e.target === modal) modal.style.display = "none"; });

function abrirModal(item) {
  itemAtual = item;
  modalTitulo.textContent = `${item.nome} — ${item.marca}`;
  modalConteudo.innerHTML = "";

  const campos = [
    { rotulo: "Categoria", chave: "categoria" },
    { rotulo: "Status", chave: "status" },
    { rotulo: "Informações", chave: "informacoes" },
    { rotulo: "Problema", chave: "problema" },
    { rotulo: "Data de Entrada", chave: "data_entrada" },
    { rotulo: "Data de Saída", chave: "data_saida" },
  ];

  for (const campo of campos) {
    const valor = item[campo.chave];
    if (valor === null || valor === undefined) continue;

    const linha = document.createElement("div");
    linha.className = "modal-linha";

    const rotulo = document.createElement("span");
    rotulo.className = "modal-rotulo";
    rotulo.textContent = campo.rotulo + ":";

    const valor_el = document.createElement("span");
    if (campo.chave === "categoria" && valor) {
      valor_el.textContent = valor.charAt(0).toUpperCase() + valor.slice(1);
    } else {
      valor_el.textContent = valor || "—";
    }

    linha.appendChild(rotulo);
    linha.appendChild(valor_el);
    modalConteudo.appendChild(linha);
  }

  document.querySelector(".modal-acoes").style.display = "flex";
  modal.style.display = "flex";

  modalExcluir.onclick = async () => {
    if (!itemAtual) return;

    if (!usuarioAtual) {
      const conteudo = document.getElementById("modal-conteudo");
      if (!conteudo.querySelector(".aviso-login")) {
        const aviso = document.createElement("p");
        aviso.className = "mensagem erro aviso-login";
        aviso.textContent = "Você precisa estar logado para excluir.";
        conteudo.appendChild(aviso);
        setTimeout(() => aviso.remove(), 3000);
      }
      return;
    }

    if (!confirm(`Excluir "${itemAtual.nome}"? Esta ação não pode ser desfeita.`)) return;

    const rota = itemAtual.categoria === "aparelho"
      ? `aparelhos/${itemAtual.id}`
      : `pecas/${itemAtual.id}`;

    try {
      const resposta = await fetch(`/api/${rota}`, { method: "DELETE" });
      if (!resposta.ok) throw new Error(`HTTP ${resposta.status}`);
      modal.style.display = "none";
      await carregar(tipoAtual);
    } catch (erro) {
      alert(`Erro ao excluir: ${erro.message}`);
    }
  };

  modalEditar.onclick = () => {
    if (!itemAtual) return;
    modalConteudo.innerHTML = "";
    document.querySelector(".modal-acoes").style.display = "none";

    const campos = itemAtual.categoria === "aparelho" ? CAMPOS_APARELHO : CAMPOS_PECA;

    const form = document.createElement("form");
    form.id = "form-editar";

    for (const campo of campos) {
      const wrapper = document.createElement("div");
      wrapper.className = "campo";

      const label = document.createElement("label");
      label.textContent = campo.rotulo + (campo.obrigatorio ? " *" : "");
      wrapper.appendChild(label);

      if (campo.tipo === "select") {
        const select = document.createElement("select");
        select.name = campo.nome;
        if (campo.obrigatorio) select.required = true;

        campo.opcoes.forEach(op => {
          const option = document.createElement("option");
          option.value = op;
          option.textContent = op;
          if (itemAtual[campo.nome] === op) option.selected = true;
          select.appendChild(option);
        });

        wrapper.appendChild(select);
      } else {
        const input = document.createElement("input");
        input.type = campo.tipo || "text";
        input.name = campo.nome;
        if (campo.obrigatorio) input.required = true;

        if (campo.tipo === "date" && itemAtual[campo.nome]) {
          const partes = itemAtual[campo.nome].split("-");
          input.value = partes.length === 3 ? `${partes[2]}-${partes[1]}-${partes[0]}` : itemAtual[campo.nome];
        } else {
          input.value = itemAtual[campo.nome] || "";
        }

        wrapper.appendChild(input);
      }

      form.appendChild(wrapper);
    }

    const acoes = document.createElement("div");
    acoes.className = "modal-acoes";

    const botaoSalvar = document.createElement("button");
    botaoSalvar.textContent = "Salvar";
    botaoSalvar.className = "botao-primario";
    botaoSalvar.type = "button";

    const botaoCancelar = document.createElement("button");
    botaoCancelar.textContent = "Cancelar";
    botaoCancelar.type = "button";
    botaoCancelar.addEventListener("click", () => abrirModal(itemAtual));

    acoes.appendChild(botaoSalvar);
    acoes.appendChild(botaoCancelar);
    form.appendChild(acoes);
    modalConteudo.appendChild(form);

    botaoSalvar.addEventListener("click", async () => {
      const dados = {};
      for (const campo of campos) {
        const elemento = form.elements[campo.nome];
        if (!elemento) continue;
        const valor = elemento.value.trim();

        if (campo.obrigatorio && !valor) {
          alert(`Preencha o campo "${campo.rotulo}".`);
          elemento.focus();
          return;
        }

        if (valor !== "") {
          if (campo.tipo === "date") {
            const [ano, mes, dia] = valor.split("-");
            dados[campo.nome] = `${dia}-${mes}-${ano}`;
          } else {
            dados[campo.nome] = valor;
          }
        }
      }

      const rota = itemAtual.categoria === "aparelho"
        ? `aparelhos/${itemAtual.id}`
        : `pecas/${itemAtual.id}`;

      try {
        const resposta = await fetch(`/api/${rota}`, {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(dados),
        });

        const corpo = await resposta.json().catch(() => ({}));
        if (!resposta.ok) throw new Error(corpo.erro || `HTTP ${resposta.status}`);

        itemAtual = { ...itemAtual, ...dados };
        modal.style.display = "none";
        await carregar(tipoAtual);
      } catch (erro) {
        alert(`Erro ao salvar: ${erro.message}`);
      }
    });
  };
}

const COLUNAS = {
  aparelhos: [
    { chave: "id", titulo: "ID" },
    { chave: "nome", titulo: "Nome" },
    { chave: "marca", titulo: "Marca" },
    { chave: "status", titulo: "Status" },
    { chave: "informacoes", titulo: "Informações" },
    { chave: "problema", titulo: "Problema" },
    { chave: "data_entrada", titulo: "Data de Entrada" },
    { chave: "data_saida", titulo: "Data de Saída" },
  ],
  pecas: [
    { chave: "id", titulo: "ID" },
    { chave: "nome", titulo: "Nome" },
    { chave: "marca", titulo: "Marca" },
    { chave: "status", titulo: "Status" },
    { chave: "informacoes", titulo: "Informações" },
    { chave: "problema", titulo: "Problema" },
    { chave: "data_entrada", titulo: "Data de Entrada" },
    { chave: "data_saida", titulo: "Data de Saída" },
  ],
  estoque: [
    { chave: "categoria", titulo: "Categoria" },
    { chave: "nome", titulo: "Nome" },
    { chave: "marca", titulo: "Marca" },
    { chave: "status", titulo: "Status" },
    { chave: "informacoes", titulo: "Informações" },
    { chave: "problema", titulo: "Problema" },
    { chave: "data_entrada", titulo: "Data de Entrada" },
    { chave: "data_saida", titulo: "Data de Saída" },
  ],
};

const TITULOS = {
  aparelhos: { lista: "Aparelhos", form: "Novo item" },
  pecas: { lista: "Peças", form: "Novo item" },
  estoque: { lista: "Estoque Geral", form: "Novo item" },
};

const CAMPOS_APARELHO = [
  { nome: "nome", rotulo: "Nome", obrigatorio: true },
  { nome: "marca", rotulo: "Marca", obrigatorio: true },
  { nome: "informacoes", rotulo: "Informações", obrigatorio: true },
  { nome: "problema", rotulo: "Problema", obrigatorio: true },
  { nome: "status", rotulo: "Status", obrigatorio: true, tipo: "select", opcoes: ["Funcional", "Não funcional", "Em conserto", "Reservado", "Doado"] },
  { nome: "data_entrada", rotulo: "Data de Entrada", tipo: "date" },
  { nome: "data_saida", rotulo: "Data de Saída", tipo: "date" },
];

const CAMPOS_PECA = [
  { nome: "nome", rotulo: "Nome", obrigatorio: true },
  { nome: "marca", rotulo: "Marca", obrigatorio: true },
  { nome: "informacoes", rotulo: "Informações", obrigatorio: true },
  { nome: "problema", rotulo: "Problema" },
  { nome: "status", rotulo: "Status", obrigatorio: true, tipo: "select", opcoes: ["Funcional", "Não funcional", "Em conserto", "Reservado", "Doado"] },
  { nome: "data_entrada", rotulo: "Data de Entrada", tipo: "date" },
  { nome: "data_saida", rotulo: "Data de Saída", tipo: "date" },
];

const elementoStatus = document.getElementById("status");
const elementoTituloLista = document.getElementById("titulo-lista");
const elementoTituloFormulario = document.getElementById("titulo-formulario");
const elementoCabecalho = document.getElementById("cabecalho");
const elementoCorpo = document.getElementById("corpo");
const elementoCampos = document.getElementById("campos");
const formulario = document.getElementById("formulario");
const mensagemFormulario = document.getElementById("mensagem-formulario");
const botaoRecarregar = document.getElementById("botao-recarregar");
const abas = document.querySelectorAll(".aba");

let tipoAtual = "aparelhos";
let categoriaAtual = ""; // controla qual tabela o form cadastra

async function buscar(tipo) {
  const resposta = await fetch(`/api/${tipo}`);
  if (!resposta.ok) throw new Error(`HTTP ${resposta.status}`);
  return resposta.json();
}

async function carregar(tipo) {
  tipoAtual = tipo;
  elementoTituloLista.textContent = TITULOS[tipo].lista;
  limparMensagem();

  const painelForm = document.getElementById("painel-formulario");
  painelForm.style.display = tipo === "estoque" ? "none" : "block";
  categoriaAtual = tipo === "pecas" ? "peca" : tipo === "aparelhos" ? "aparelho" : "";

  if (tipo !== "estoque") {
    await renderizarFormulario();
  }

  renderizarCabecalho(tipo);
  elementoCorpo.innerHTML = "";
  elementoStatus.classList.remove("erro");
  elementoStatus.textContent = "Carregando...";

  try {
    const dados = await buscar(tipo);
    renderizarLinhas(tipo, dados);
    elementoStatus.textContent = `${dados.length} registro(s) carregado(s).`;
  } catch (erro) {
    elementoStatus.textContent = `Falha ao carregar: ${erro.message}`;
    elementoStatus.classList.add("erro");
  }
}

function renderizarCabecalho(tipo) {
  elementoCabecalho.innerHTML = "";
  for (const coluna of COLUNAS[tipo]) {
    const th = document.createElement("th");
    th.textContent = coluna.titulo;
    elementoCabecalho.appendChild(th);
  }
}

function renderizarLinhas(tipo, dados) {
  if (!dados.length) {
    const tr = document.createElement("tr");
    const td = document.createElement("td");
    td.colSpan = COLUNAS[tipo].length;
    td.className = "vazio";
    td.textContent = "Nenhum registro encontrado.";
    tr.appendChild(td);
    elementoCorpo.appendChild(tr);
    return;
  }
  for (const item of dados) {
    const tr = document.createElement("tr");

    if (tipo === "estoque") {
      tr.style.cursor = "pointer";
      tr.title = "Clique para ver detalhes";
      tr.addEventListener("click", () => abrirModal(item));
    }

    for (const coluna of COLUNAS[tipo]) {
      const td = document.createElement("td");
      const valor = item[coluna.chave];
      if (coluna.chave === "categoria" && valor) {
        td.textContent = valor.charAt(0).toUpperCase() + valor.slice(1);
      } else {
        td.textContent = valor === null || valor === undefined ? "—" : valor;
      }
      tr.appendChild(td);
    }
    elementoCorpo.appendChild(tr);
  }
}

async function renderizarFormulario() {
  elementoCampos.innerHTML = "";

  const wrapperCategoria = document.createElement("div");
  wrapperCategoria.className = "campo";
  const labelCategoria = document.createElement("label");
  labelCategoria.textContent = "Categoria *";
  const selectCategoria = document.createElement("select");
  selectCategoria.id = "campo-categoria";
  selectCategoria.name = "categoria";

  const placeholder = document.createElement("option");
  placeholder.value = "";
  placeholder.textContent = "Selecione...";
  placeholder.disabled = true;
  placeholder.selected = true;
  selectCategoria.appendChild(placeholder);

  ["aparelho", "peca"].forEach(op => {
    const option = document.createElement("option");
    option.value = op;
    option.textContent = op === "aparelho" ? "Aparelho" : "Peça";
    if (op === categoriaAtual) option.selected = true;
    selectCategoria.appendChild(option);
  });

  selectCategoria.addEventListener("change", async () => {
    if (selectCategoria.value) {
      categoriaAtual = selectCategoria.value;
      await renderizarFormulario();
    }
  });

  wrapperCategoria.appendChild(labelCategoria);
  wrapperCategoria.appendChild(selectCategoria);
  elementoCampos.appendChild(wrapperCategoria);

  const campos = categoriaAtual === "aparelho" ? CAMPOS_APARELHO : CAMPOS_PECA;

  for (const campo of campos) {
    const wrapper = document.createElement("div");
    wrapper.className = "campo";

    const label = document.createElement("label");
    label.htmlFor = `campo-${campo.nome}`;
    label.textContent = campo.rotulo + (campo.obrigatorio ? " *" : "");
    wrapper.appendChild(label);

    if (campo.tipo === "select") {
      const select = document.createElement("select");
      select.id = `campo-${campo.nome}`;
      select.name = campo.nome;
      if (campo.obrigatorio) select.required = true;

      const placeholder = document.createElement("option");
      placeholder.value = "";
      placeholder.textContent = "Selecione...";
      placeholder.disabled = true;
      placeholder.selected = true;
      select.appendChild(placeholder);

      campo.opcoes.forEach(op => {
        const option = document.createElement("option");
        option.value = op;
        option.textContent = op;
        select.appendChild(option);
      });

      wrapper.appendChild(select);
    } else {
      const input = document.createElement("input");
      input.type = campo.tipo || "text";
      input.id = `campo-${campo.nome}`;
      input.name = campo.nome;
      if (campo.obrigatorio) input.required = true;
      if (campo.nome === "data_entrada") {
        input.value = new Date().toISOString().split("T")[0];
      }
      wrapper.appendChild(input);
    }
    elementoCampos.appendChild(wrapper);
  }

  elementoTituloFormulario.textContent =
    categoriaAtual === "aparelho" ? "Novo aparelho" : "Nova peça";
}

function limparMensagem() {
  mensagemFormulario.textContent = "";
  mensagemFormulario.classList.remove("sucesso", "erro");
}

async function enviarFormulario(evento) {
  evento.preventDefault();
  limparMensagem();

  const campos = categoriaAtual === "aparelho" ? CAMPOS_APARELHO : CAMPOS_PECA;
  const dados = {};

  for (const campo of campos) {
    const elemento = formulario.elements[campo.nome];
    if (!elemento) continue;
    const valor = elemento.value.trim();

    if (campo.obrigatorio && !valor) {
      mensagemFormulario.textContent = `Preencha o campo "${campo.rotulo}".`;
      mensagemFormulario.classList.add("erro");
      elemento.focus();
      return;
    }

    if (valor !== "") {
      if (campo.tipo === "number") {
        dados[campo.nome] = Number(valor);
      } else if (campo.tipo === "date") {
        const [ano, mes, dia] = valor.split("-");
        dados[campo.nome] = `${dia}-${mes}-${ano}`;
      } else {
        dados[campo.nome] = valor;
      }
    }
  }

  const rota = categoriaAtual === "aparelho" ? "aparelhos" : "pecas";

  const botao = formulario.querySelector("button[type=submit]");
  botao.disabled = true;
  try {
    const resposta = await fetch(`/api/${rota}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(dados),
    });

    const corpo = await resposta.json().catch(() => ({}));
    if (!resposta.ok) throw new Error(corpo.erro || `HTTP ${resposta.status}`);

    mensagemFormulario.textContent = "Cadastrado com sucesso.";
    mensagemFormulario.classList.add("sucesso");
    formulario.reset();
    await renderizarFormulario();
    await carregar(tipoAtual);
  } catch (erro) {
    mensagemFormulario.textContent = erro.message;
    mensagemFormulario.classList.add("erro");
  } finally {
    botao.disabled = false;
  }
}

abas.forEach((aba) => {
  aba.addEventListener("click", () => {
    abas.forEach((a) => a.classList.remove("ativa"));
    aba.classList.add("ativa");
    carregar(aba.dataset.tipo);
  });
});

botaoRecarregar.addEventListener("click", () => carregar(tipoAtual));
formulario.addEventListener("submit", enviarFormulario);

carregar("aparelhos");

async function verificarSessao() {
  try {
    const resposta = await fetch("/api/me");
    if (resposta.ok) {
      usuarioAtual = await resposta.json();
    } else {
      usuarioAtual = null;
    }
  } catch {
    usuarioAtual = null;
  }
}

verificarSessao();
carregar("aparelhos");