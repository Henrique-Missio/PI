const mensagem = document.getElementById("mensagem-recuperar");
const botaoEnviar = document.getElementById("botao-enviar");

function mostrarErro(msg) {
    mensagem.textContent = msg;
    mensagem.className = "mensagem erro";
}

function mostrarSucesso(msg) {
    mensagem.textContent = msg;
    mensagem.className = "mensagem sucesso";
}

botaoEnviar.addEventListener("click", async () => {
    const email = document.getElementById("email").value.trim();
    if (!email) {
        mostrarErro("Digite seu e-mail.");
        return;
    }

    botaoEnviar.disabled = true;
    try {
        const resposta = await fetch("/api/recuperar-senha", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email }),
        });

        const corpo = await resposta.json().catch(() => ({}));
        if (!resposta.ok) throw new Error(corpo.erro || `HTTP ${resposta.status}`);

        mostrarSucesso(corpo.mensagem);
        sessionStorage.setItem("email-recuperacao", email);
        setTimeout(() => window.location.href = "/verificar-codigo", 1500);
    } catch (erro) {
        mostrarErro(erro.message);
        botaoEnviar.disabled = false;
    }
});

if (typeof module !== "undefined" && module.exports) {
    module.exports = {};
}
