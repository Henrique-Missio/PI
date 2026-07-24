const mensagem = document.getElementById("mensagem-codigo");
const botaoVerificar = document.getElementById("botao-verificar");
const campoCodigo = document.getElementById("codigo");

const email = sessionStorage.getItem("email-recuperacao");
if (!email) {
    window.location.href = "/recuperar-senha";
}

function mostrarErro(msg) {
    mensagem.textContent = msg;
    mensagem.className = "mensagem erro";
}

function mostrarSucesso(msg) {
    mensagem.textContent = msg;
    mensagem.className = "mensagem sucesso";
}

campoCodigo.addEventListener("input", (e) => {
    e.target.value = e.target.value.replace(/\D/g, "").slice(0, 6);
});

const botaoReenviar = document.getElementById("botao-reenviar");
botaoReenviar.addEventListener("click", async () => {
    botaoReenviar.disabled = true;
    try {
        const resposta = await fetch("/api/recuperar-senha", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email }),
        });
        const corpo = await resposta.json().catch(() => ({}));
        if (!resposta.ok) throw new Error(corpo.erro || `HTTP ${resposta.status}`);

        mostrarSucesso("Novo código enviado!");
        campoCodigo.value = "";
        campoCodigo.focus();
    } catch (erro) {
        mostrarErro(erro.message);
    } finally {
        botaoReenviar.disabled = false;
    }
});

botaoVerificar.addEventListener("click", async () => {
    const codigo = campoCodigo.value.trim();
    if (codigo.length !== 6) {
        mostrarErro("Digite os 6 dígitos do código.");
        return;
    }

    botaoVerificar.disabled = true;
    try {
        const resposta = await fetch("/api/verificar-codigo", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email, codigo }),
        });

        const corpo = await resposta.json().catch(() => ({}));
        if (!resposta.ok) throw new Error(corpo.erro || "Código inválido.");

        sessionStorage.setItem("codigo-recuperacao", codigo);
        window.location.href = "/redefinir-senha";
    } catch (erro) {
        mostrarErro(erro.message);
        botaoVerificar.disabled = false;
    }
});

if (typeof module !== "undefined" && module.exports) {
    module.exports = {};
}
