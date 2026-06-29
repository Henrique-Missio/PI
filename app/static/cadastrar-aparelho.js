const mensagem   = document.getElementById("mensagem-aparelho");
const btnCadastrar = document.getElementById("btn-cadastrar");

document.getElementById("data_entrada").value = new Date().toISOString().split("T")[0];

function mostrarErro(msg) {
  mensagem.textContent = msg;
  mensagem.className = "mensagem erro";
}

function mostrarSucesso(msg) {
  mensagem.textContent = msg;
  mensagem.className = "mensagem sucesso";
}

btnCadastrar.addEventListener("click", async () => {
  const nome       = document.getElementById("nome").value.trim();
  const marca      = document.getElementById("marca").value.trim();
  const informacoes= document.getElementById("informacoes").value.trim();
  const status     = document.getElementById("status").value;
  const problema   = document.getElementById("problema").value.trim();
  const dataRaw    = document.getElementById("data_entrada").value;

  if (!nome)        { mostrarErro("Preencha o nome.");        return; }
  if (!marca)       { mostrarErro("Preencha a marca.");       return; }
  if (!informacoes) { mostrarErro("Preencha as informações."); return; }
  if (!status)      { mostrarErro("Selecione o status.");     return; }

  const dados = { nome, marca, informacoes, status, problema: problema || "Sem observações" };

  if (dataRaw) {
    const [ano, mes, dia] = dataRaw.split("-");
    dados.data_entrada = `${dia}-${mes}-${ano}`;
  }

  btnCadastrar.disabled = true;
  try {
    const resposta = await fetch("/api/aparelhos", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(dados),
    });

    const corpo = await resposta.json().catch(() => ({}));
    if (!resposta.ok) throw new Error(corpo.erro || `HTTP ${resposta.status}`);

    mostrarSucesso("Aparelho cadastrado com sucesso!");
    setTimeout(() => window.location.href = "/", 1500);
  } catch (erro) {
    mostrarErro(erro.message);
    btnCadastrar.disabled = false;
  }
});