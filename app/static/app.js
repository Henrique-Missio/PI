const COLUNAS = {
  professores: [
    { chave: "id", titulo: "ID" },
    { chave: "nome", titulo: "Nome" },
    { chave: "email", titulo: "E-mail" },
  ],
  turmas: [
    { chave: "id", titulo: "ID" },
    { chave: "codigo", titulo: "Código" },
    { chave: "nome", titulo: "Nome" },
    { chave: "professor_id", titulo: "Professor" },
  ],
  alunos: [
    { chave: "id", titulo: "ID" },
    { chave: "nome", titulo: "Nome" },
    { chave: "email", titulo: "E-mail" },
    { chave: "turma_id", titulo: "Turma" },
  ],
};

const TITULOS = {
  professores: { lista: "Professores", form: "Novo professor" },
  turmas: { lista: "Turmas", form: "Nova turma" },
  alunos: { lista: "Alunos", form: "Novo aluno" },
};

const CAMPOS = {
  professores: [
    { nome: "nome", rotulo: "Nome", obrigatorio: true },
    { nome: "email", rotulo: "E-mail", tipo: "email" },
  ],
  turmas: [
    { nome: "nome", rotulo: "Nome", obrigatorio: true },
    { nome: "codigo", rotulo: "Código", obrigatorio: true },
    { nome: "professor_id", rotulo: "Professor", tipo: "select", origem: "professores", obrigatorio: true },
  ],
  alunos: [
    { nome: "nome", rotulo: "Nome", obrigatorio: true },
    { nome: "email", rotulo: "E-mail", tipo: "email" },
    { nome: "turma_id", rotulo: "Turma", tipo: "select", origem: "turmas", obrigatorio: true },
  ],
};

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

let tipoAtual = "professores";

async function buscar(tipo) {
  const resposta = await fetch(`/api/${tipo}`);
  if (!resposta.ok) throw new Error(`HTTP ${resposta.status}`);
  return resposta.json();
}

async function carregar(tipo) {
  tipoAtual = tipo;
  elementoTituloLista.textContent = TITULOS[tipo].lista;
  elementoTituloFormulario.textContent = TITULOS[tipo].form;
  limparMensagem();

  await renderizarFormulario(tipo);
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
      td.textContent = valor === null || valor === undefined ? "—" : valor;
      tr.appendChild(td);
    }
    elementoCorpo.appendChild(tr);
  }
}

async function renderizarFormulario(tipo) {
  elementoCampos.innerHTML = "";
  for (const campo of CAMPOS[tipo]) {
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
      select.appendChild(placeholder);

      try {
        const itens = await buscar(campo.origem);
        for (const item of itens) {
          const option = document.createElement("option");
          option.value = item.id;
          option.textContent = rotuloItem(campo.origem, item);
          select.appendChild(option);
        }
      } catch (erro) {
        const option = document.createElement("option");
        option.disabled = true;
        option.textContent = `Erro ao carregar: ${erro.message}`;
        select.appendChild(option);
      }

      wrapper.appendChild(select);
    } else {
      const input = document.createElement("input");
      input.type = campo.tipo || "text";
      input.id = `campo-${campo.nome}`;
      input.name = campo.nome;
      if (campo.obrigatorio) input.required = true;
      wrapper.appendChild(input);
    }

    elementoCampos.appendChild(wrapper);
  }
}

function rotuloItem(origem, item) {
  if (origem === "professores") return `${item.nome} (id ${item.id})`;
  if (origem === "turmas") return `${item.codigo} - ${item.nome}`;
  return `${item.id}`;
}

function limparMensagem() {
  mensagemFormulario.textContent = "";
  mensagemFormulario.classList.remove("sucesso", "erro");
}

async function enviarFormulario(evento) {
  evento.preventDefault();
  limparMensagem();

  const dados = {};
  for (const campo of CAMPOS[tipoAtual]) {
    const elemento = formulario.elements[campo.nome];
    const valor = elemento.value.trim();
    if (campo.obrigatorio && !valor) {
      mensagemFormulario.textContent = `Preencha ${campo.rotulo}.`;
      mensagemFormulario.classList.add("erro");
      elemento.focus();
      return;
    }
    if (valor !== "") dados[campo.nome] = valor;
  }

  const botao = formulario.querySelector("button[type=submit]");
  botao.disabled = true;
  try {
    const resposta = await fetch(`/api/${tipoAtual}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(dados),
    });

    const corpo = await resposta.json().catch(() => ({}));
    if (!resposta.ok) {
      throw new Error(corpo.erro || `HTTP ${resposta.status}`);
    }

    mensagemFormulario.textContent = "Cadastrado com sucesso.";
    mensagemFormulario.classList.add("sucesso");
    formulario.reset();
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

carregar("professores");
