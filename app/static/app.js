const COLUNAS = {
  aparelhos: [
    { chave: "id", titulo: "ID" },
    { chave: "nome", titulo: "Nome" },
    { chave: "marca", titulo: "Marca" },
    { chave: "status", titulo: "Status" },
    { chave: "quantidade", titulo: "Quantidade" },
    { chave: "data_entrada", titulo: "Data de Entrada" },
    { chave: "data_saida", titulo: "Data de Saída" },
    { chave: "problema", titulo: "Problema" },
  ],
  pecas: [
    { chave: "id", titulo: "ID" },
    { chave: "nome", titulo: "Nome" },
    { chave: "marca", titulo: "Marca" },
    { chave: "status", titulo: "Status" },
    { chave: "quantidade", titulo: "Quantidade" },
    { chave: "data_entrada", titulo: "Data de Entrada" },
    { chave: "data_saida", titulo: "Data de Saída" },
    { chave: "problema", titulo: "Problema" },
  ],
  estoque: [
    { chave: "categoria", titulo: "Categoria" },
    { chave: "nome", titulo: "Nome" },
    { chave: "marca", titulo: "Marca" },
    { chave: "status", titulo: "Status" },
    { chave: "quantidade", titulo: "Quantidade" },
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
  { nome: "status", rotulo: "Status", obrigatorio: true },
  { nome: "quantidade", rotulo: "Quantidade", obrigatorio: true, tipo: "number" },
  { nome: "data_entrada", rotulo: "Data de Entrada", tipo: "date" },
  { nome: "data_saida", rotulo: "Data de Saída", tipo: "date" },
];

const CAMPOS_PECA = [
  { nome: "nome", rotulo: "Nome", obrigatorio: true },
  { nome: "marca", rotulo: "Marca", obrigatorio: true },
  { nome: "informacoes", rotulo: "Informações", obrigatorio: true },
  { nome: "problema", rotulo: "Problema" },
  { nome: "status", rotulo: "Status", obrigatorio: true },
  { nome: "quantidade", rotulo: "Quantidade", obrigatorio: true, tipo: "number" },
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

  // estoque não tem formulário de cadastro
  const painelForm = document.getElementById("painel-formulario");
  painelForm.style.display = tipo === "estoque" ? "none" : "block";

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

  // seletor de categoria no topo do formulário
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

  // quando muda a categoria, re-renderiza os campos
  selectCategoria.addEventListener("change", async () => {
    if (selectCategoria.value) {
      categoriaAtual = selectCategoria.value;
      await renderizarFormulario();
    }
  });

  wrapperCategoria.appendChild(labelCategoria);
  wrapperCategoria.appendChild(selectCategoria);
  elementoCampos.appendChild(wrapperCategoria);

  // campos de acordo com a categoria selecionada
  const campos = categoriaAtual === "aparelho" ? CAMPOS_APARELHO : CAMPOS_PECA;

  for (const campo of campos) {
    const wrapper = document.createElement("div");
    wrapper.className = "campo";

    const label = document.createElement("label");
    label.htmlFor = `campo-${campo.nome}`;
    label.textContent = campo.rotulo + (campo.obrigatorio ? " *" : "");
    wrapper.appendChild(label);

    const input = document.createElement("input");
    input.type = campo.tipo || "text";
    input.id = `campo-${campo.nome}`;
    input.name = campo.nome;
    if (campo.obrigatorio) input.required = true;
    if (campo.nome === "data_entrada") {
      input.value = new Date().toISOString().split("T")[0];
    }

    wrapper.appendChild(input);
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

  // envia para a rota correta dependendo da categoria
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