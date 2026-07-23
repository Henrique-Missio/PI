const mensagem = document.getElementById("mensagem-peca");
const btnCadastrar = document.getElementById("btn-cadastrar");
const campoDataEntrada = document.getElementById("data_entrada");

const hojeISO = new Date().toISOString().split("T")[0];
campoDataEntrada.value = hojeISO;
campoDataEntrada.max = hojeISO; // não deixa escolher data futura

function adicionarContador(idCampo, limite) {
  const campo = document.getElementById(idCampo);
  const contador = document.createElement("span");
  contador.className = "contador-caracteres";
  campo.parentElement.appendChild(contador);

  function atualizar() {
    contador.textContent = `${campo.value.length}/${limite}`;
  }
  campo.addEventListener("input", atualizar);
  atualizar();
}

adicionarContador("informacoes", 1500);
adicionarContador("problema", 500);

function mostrarErro(msg) {
  mensagem.textContent = msg;
  mensagem.className = "mensagem erro";
}

function mostrarSucesso(msg) {
  mensagem.textContent = msg;
  mensagem.className = "mensagem sucesso";
}

btnCadastrar.addEventListener("click", async () => {
  const nome = document.getElementById("nome").value.trim();
  const marca = document.getElementById("marca").value.trim();
  const informacoes = document.getElementById("informacoes").value.trim();
  const status = document.getElementById("status").value;
  const problema = document.getElementById("problema").value.trim();
  const dataRaw = campoDataEntrada.value;

  if (!nome) { mostrarErro("Preencha o nome."); return; }
  if (!marca) { mostrarErro("Preencha a marca."); return; }
  if (!informacoes) { mostrarErro("Preencha as informações."); return; }
  if (!status) { mostrarErro("Selecione o status."); return; }
  if (dataRaw && dataRaw > hojeISO) { mostrarErro("A data de entrada não pode ser no futuro."); return; }

  const dados = { nome, marca, informacoes, status, problema: problema || null };

  if (dataRaw) {
    const [ano, mes, dia] = dataRaw.split("-");
    dados.data_entrada = `${dia}-${mes}-${ano}`;
  }

  btnCadastrar.disabled = true;
  try {
    const resposta = await fetch("/api/pecas", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(dados),
    });

    const corpo = await resposta.json().catch(() => ({}));
    if (!resposta.ok) throw new Error(corpo.erro || `HTTP ${resposta.status}`);

    mostrarSucesso("Peça cadastrada com sucesso!");
    setTimeout(() => window.location.href = "/", 1500);
  } catch (erro) {
    mostrarErro(erro.message);
    btnCadastrar.disabled = false;
  }
});
