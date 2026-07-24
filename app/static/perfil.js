const mensagem = document.getElementById("mensagem-perfil");
const botaoSalvar = document.getElementById("botao-salvar-perfil");
const botaoExcluir = document.getElementById("botao-excluir-conta");
let usuarioAtual = null;

function mostrarErro(msg) {
    mensagem.textContent = msg;
    mensagem.className = "mensagem erro";
}

function mostrarSucesso(msg) {
    mensagem.textContent = msg;
    mensagem.className = "mensagem sucesso";
}

// ── MÁSCARA CPF ──
document.getElementById("cpf").addEventListener("input", (e) => {
    let v = e.target.value.replace(/\D/g, "").slice(0, 11);
    v = v.replace(/(\d{3})(\d)/, "$1.$2");
    v = v.replace(/(\d{3})(\d)/, "$1.$2");
    v = v.replace(/(\d{3})(\d{1,2})$/, "$1-$2");
    e.target.value = v;
});

// ── MÁSCARA TELEFONE ──
document.getElementById("telefone_celular").addEventListener("input", (e) => {
    let v = e.target.value.replace(/\D/g, "").slice(0, 11);
    v = v.replace(/(\d{2})(\d)/, "($1) $2");
    v = v.replace(/(\d{5})(\d)/, "$1-$2");
    e.target.value = v;
});

function aplicarMascaraCPF(valor) {
    let v = valor.replace(/\D/g, "");
    v = v.replace(/(\d{3})(\d)/, "$1.$2");
    v = v.replace(/(\d{3})(\d)/, "$1.$2");
    v = v.replace(/(\d{3})(\d{1,2})$/, "$1-$2");
    return v;
}

function aplicarMascaraTelefone(valor) {
    let v = valor.replace(/\D/g, "");
    v = v.replace(/(\d{2})(\d)/, "($1) $2");
    v = v.replace(/(\d{5})(\d)/, "$1-$2");
    return v;
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

const listaRequisitos = document.getElementById("requisitos-nova-senha");
const campoSenha = document.getElementById("nova_senha"); // underscore, não hífen

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

async function carregarPerfil() {
    try {
        const resposta = await fetch("/api/perfil");
        if (!resposta.ok) {
            window.location.href = "/login";
            return;
        }
        const dados = await resposta.json();

        document.getElementById("nome_completo").value = dados.nome_completo || "";
        document.getElementById("cpf").value = aplicarMascaraCPF(dados.cpf || "");
        document.getElementById("data_nasc").value = dados.data_nasc || "";
        document.getElementById("funcao").value = dados.funcao || "";
        document.getElementById("email_pessoal").value = dados.email_pessoal || "";
        document.getElementById("telefone_celular").value = aplicarMascaraTelefone(dados.telefone_celular || "");
    } catch {
        mostrarErro("Erro ao carregar perfil.");
    }
}


botaoSalvar.onclick = async () => {
    const dados = {
        nome_completo: document.getElementById("nome_completo").value.trim(),
        cpf: document.getElementById("cpf").value.replace(/\D/g, ""),
        funcao: document.getElementById("funcao").value,
        email_pessoal: document.getElementById("email_pessoal").value.trim(),
        telefone_celular: document.getElementById("telefone_celular").value.replace(/\D/g, ""),
    };

    const dataNasc = document.getElementById("data_nasc").value;
    if (dataNasc) {
        const [ano, mes, dia] = dataNasc.split("-");
        dados.data_nasc = `${dia}-${mes}-${ano}`;
    }

    const novaSenha = document.getElementById("nova_senha").value.trim();
    if (novaSenha) {
        const requisitos = validarRequisitosSenha(novaSenha);
        if (!Object.values(requisitos).every(Boolean)) {
            mostrarErro("A nova senha não atende a todos os requisitos mínimos.");
            return;
        }
        dados.senha = novaSenha;
    }

    botaoSalvar.disabled = true;
    try {
        const resposta = await fetch("/api/perfil", {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(dados),
        });

        const corpo = await resposta.json().catch(() => ({}));
        if (!resposta.ok) throw new Error(corpo.erro || `HTTP ${resposta.status}`);

        mostrarSucesso("Dados atualizados com sucesso!");
        document.getElementById("nova_senha").value = "";
    } catch (erro) {
        mostrarErro(erro.message);
    } finally {
        botaoSalvar.disabled = false;
    }
};

botaoExcluir.onclick = async () => {
    if (!confirm("Tem certeza que deseja excluir sua conta? Esta ação não pode ser desfeita.")) return;

    try {
        const resposta = await fetch("/api/perfil", { method: "DELETE" });
        if (!resposta.ok) throw new Error("Erro ao excluir conta.");
        window.location.href = "/login";
    } catch (erro) {
        mostrarErro(erro.message);
    }
};

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

carregarPerfil();