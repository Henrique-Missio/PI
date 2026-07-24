const mensagem = document.getElementById("mensagem-redefinir");
const botaoRedefinir = document.getElementById("botao-redefinir");

const email = sessionStorage.getItem("email-recuperacao");
const codigo = sessionStorage.getItem("codigo-recuperacao");
if (!email || !codigo) {
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

// ── REQUISITOS DE SENHA FORTE ──
function validarRequisitosSenha(senha) {
    return {
        tamanho: senha.length >= 8,
        maiuscula: /[A-Z]/.test(senha),
        numero: /[0-9]/.test(senha),
        especial: /[^A-Za-z0-9]/.test(senha),
    };
}

const listaRequisitos = document.getElementById("requisitos-senha");
const campoSenha = document.getElementById("nova_senha");

campoSenha.addEventListener("input", () => {
    const valor = campoSenha.value;
    listaRequisitos.style.display = valor.length > 0 ? "flex" : "none";

    const status = validarRequisitosSenha(valor);
    Object.entries(status).forEach(([chave, atendido]) => {
        const item = listaRequisitos.querySelector(`[data-requisito="${chave}"]`);
        if (!item) return;
        item.classList.toggle("requisito-ok", atendido);
        item.classList.toggle("requisito-falta", !atendido);
        item.querySelector(".requisito-icone").textContent = atendido ? "✓" : "✕";
    });
});

// ── TOGGLE DE VISUALIZAÇÃO DE SENHA ──
document.addEventListener("DOMContentLoaded", () => {
    const ICONE_OLHO_ABERTO = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8Z"/><circle cx="12" cy="12" r="3"/></svg>`;
    const ICONE_OLHO_FECHADO = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a13.16 13.16 0 0 1-1.67 2.68M6.61 6.61A13.526 13.526 0 0 0 1 12s4 8 11 8a9.26 9.26 0 0 0 5.39-1.61M14.12 14.12a3 3 0 1 1-4.24-4.24"/><line x1="1" y1="1" x2="23" y2="23"/></svg>`;

    document.querySelectorAll(".toggle-senha").forEach(btn => {
        btn.addEventListener("click", () => {
            const input = document.getElementById(btn.dataset.target);
            if (!input) return;
            const mostrando = input.type === "text";
            input.type = mostrando ? "password" : "text";
            btn.innerHTML = mostrando ? ICONE_OLHO_ABERTO : ICONE_OLHO_FECHADO;
            btn.classList.toggle("ativo", !mostrando);
            btn.setAttribute("aria-label", mostrando ? "Mostrar senha" : "Ocultar senha");
        });
    });
});

// ── SALVAR ──
botaoRedefinir.addEventListener("click", async () => {
    const novaSenha = campoSenha.value;
    const confirmar = document.getElementById("confirmar_senha").value;

    if (novaSenha !== confirmar) {
        mostrarErro("As senhas não coincidem.");
        return;
    }

    const requisitos = validarRequisitosSenha(novaSenha);
    if (!Object.values(requisitos).every(Boolean)) {
        mostrarErro("A senha não atende a todos os requisitos mínimos.");
        return;
    }

    botaoRedefinir.disabled = true;
    try {
        const resposta = await fetch("/api/redefinir-senha", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email, codigo, nova_senha: novaSenha }),
        });

        const corpo = await resposta.json().catch(() => ({}));
        if (!resposta.ok) throw new Error(corpo.erro || `HTTP ${resposta.status}`);

        sessionStorage.removeItem("email-recuperacao");
        sessionStorage.removeItem("codigo-recuperacao");
        sessionStorage.setItem("mensagem-login", "Senha redefinida! Faça login com a nova senha.");
        mostrarSucesso("Senha redefinida com sucesso!");
        setTimeout(() => window.location.href = "/login", 1500);
    } catch (erro) {
        mostrarErro(erro.message);
        botaoRedefinir.disabled = false;
    }
});

if (typeof module !== "undefined" && module.exports) {
    module.exports = { validarRequisitosSenha };
}
