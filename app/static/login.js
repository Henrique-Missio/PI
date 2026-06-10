const mensagem = document.getElementById("mensagem-login");
const botaoLogin = document.getElementById("botao-login");

const mensagemCadastro = sessionStorage.getItem("mensagem-cadastro");
if (mensagemCadastro) {
    mensagem.textContent = mensagemCadastro;
    mensagem.className = "mensagem sucesso";
    sessionStorage.removeItem("mensagem-cadastro");
    setTimeout(() => {
        mensagem.textContent = "";
        mensagem.className = "mensagem";
    }, 3000);
}

function mostrarErro(msg) {
    mensagem.textContent = msg;
    mensagem.className = "mensagem erro";
}

botaoLogin.addEventListener("click", async () => {
    const email = document.getElementById("email").value.trim();
    const senha = document.getElementById("senha").value.trim();

    if (!email || !senha) {
        mostrarErro("Preencha todos os campos.");
        return;
    }

    botaoLogin.disabled = true;
    try {
        const resposta = await fetch("/api/login", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email, senha }),
        });

        const corpo = await resposta.json().catch(() => ({}));
        if (!resposta.ok) throw new Error(corpo.erro || `HTTP ${resposta.status}`);

        sessionStorage.setItem("mensagem-login", "Login realizado com sucesso!");
        window.location.href = "/";
    } catch (erro) {
        mostrarErro(erro.message);
    } finally {
        botaoLogin.disabled = false;
    }
});