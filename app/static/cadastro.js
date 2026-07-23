const mensagem = document.getElementById("mensagem-cadastro");
const botaoCadastro = document.getElementById("botao-cadastro");
const tipoWrapper = document.getElementById("campo-tipo-wrapper");

let usuarioLogado = null;

async function verificarLogin() {
    try {
        const resposta = await fetch("/api/me");
        if (resposta.ok) {
            usuarioLogado = await resposta.json();
            if (usuarioLogado.tipo === "administrador") {
                tipoWrapper.style.display = "block";
            }
        }
    } catch {
        usuarioLogado = null;
    }
}

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

// ── VALIDADOR CPF ──
function validarCPF(cpf) {
    cpf = cpf.replace(/\D/g, "");
    if (cpf.length !== 11 || /^(\d)\1+$/.test(cpf)) return false;

    let soma = 0;
    for (let i = 0; i < 9; i++) soma += parseInt(cpf[i]) * (10 - i);
    let resto = (soma * 10) % 11;
    if (resto === 10 || resto === 11) resto = 0;
    if (resto !== parseInt(cpf[9])) return false;

    soma = 0;
    for (let i = 0; i < 10; i++) soma += parseInt(cpf[i]) * (11 - i);
    resto = (soma * 10) % 11;
    if (resto === 10 || resto === 11) resto = 0;
    return resto === parseInt(cpf[10]);
}

// ── MÁSCARA CEP ──
document.getElementById("cep").addEventListener("input", (e) => {
    let v = e.target.value.replace(/\D/g, "").slice(0, 8);
    v = v.replace(/(\d{5})(\d)/, "$1-$2");
    e.target.value = v;
});

// ── VIA CEP ──────────────────────────────────────────────────────────────
// Função extraída e exportável, para ser testável isoladamente com Jest.
async function buscarEnderecoPorCep(cep, { fetchFn = fetch, doc = document } = {}) {
    const cepLimpo = cep.replace(/\D/g, "");

    // limpa os campos antes de buscar
    ["rua", "bairro", "cidade", "estado"].forEach(id => {
        doc.getElementById(id).value = "";
    });

    if (cepLimpo.length !== 8) {
        // avisa apenas se o usuário começou a digitar algo (evita mensagem ao carregar a página)
        if (cepLimpo.length > 0) {
            mostrarErro("Digite os 8 números do CEP.");
        }
        return null;
    }

    try {
        const resposta = await fetchFn(`https://viacep.com.br/ws/${cepLimpo}/json/`);
        const dados = await resposta.json();

        if (dados.erro) {
            mostrarErro("CEP não encontrado.");
            return null;
        }

        doc.getElementById("rua").value = dados.logradouro || "";
        doc.getElementById("bairro").value = dados.bairro || "";
        doc.getElementById("cidade").value = dados.localidade || "";
        doc.getElementById("estado").value = dados.uf || "";

        doc.getElementById("numero").focus();

        return dados;
    } catch {
        mostrarErro("Erro ao buscar CEP. Verifique sua conexão.");
        return null;
    }
}

document.getElementById("cep").addEventListener("blur", async (e) => {
    await buscarEnderecoPorCep(e.target.value);
});

// ── MÁSCARA TELEFONE ──
document.getElementById("telefone_celular").addEventListener("input", (e) => {
    let v = e.target.value.replace(/\D/g, "").slice(0, 11);
    v = v.replace(/(\d{2})(\d)/, "($1) $2");
    v = v.replace(/(\d{5})(\d)/, "$1-$2");
    e.target.value = v;
});

// ── ENVIO DO FORMULÁRIO ──
botaoCadastro.addEventListener("click", async () => {
    const camposObrigatorios = [
        "nome_completo", "cpf", "data_nasc", "funcao",
        "email_pessoal", "telefone_celular",
        "cep", "rua", "bairro", "cidade", "estado",
        "numero", "senha", "confirmar_senha"
    ];

    const dados = {};
    for (const campo of camposObrigatorios) {
        const valor = document.getElementById(campo).value.trim();
        if (!valor) {
            mostrarErro(`Preencha o campo "${campo.replace(/_/g, " ")}".`);
            document.getElementById(campo).focus();
            return;
        }
        dados[campo] = valor;
    }

    const complemento = document.getElementById("complemento").value.trim();
    if (complemento) dados.complemento = complemento;

    if (dados.senha !== dados.confirmar_senha) {
        mostrarErro("As senhas não coincidem.");
        return;
    }

    if (dados.senha.length < 6) {
        mostrarErro("A senha deve ter pelo menos 6 caracteres.");
        return;
    }

    const cpfLimpo = dados.cpf.replace(/\D/g, "");
    if (!validarCPF(cpfLimpo)) {
        mostrarErro("CPF inválido.");
        return;
    }
    dados.cpf = cpfLimpo;

    const telLimpo = dados.telefone_celular.replace(/\D/g, "");
    if (telLimpo.length < 10) {
        mostrarErro("Telefone inválido. Use apenas números com DDD.");
        return;
    }
    dados.telefone_celular = telLimpo;

    const cepLimpo = dados.cep.replace(/\D/g, "");
    if (cepLimpo.length !== 8) {
        mostrarErro("CEP inválido.");
        return;
    }
    dados.cep = cepLimpo;

    const [ano, mes, dia] = dados.data_nasc.split("-");
    dados.data_nasc = `${dia}-${mes}-${ano}`;

    delete dados.confirmar_senha;

    let rota = "/api/cadastro";
    if (usuarioLogado?.tipo === "administrador") {
        dados.tipo = document.getElementById("tipo").value;
        rota = "/api/usuarios";
    }

    botaoCadastro.disabled = true;
    try {
        const resposta = await fetch(rota, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(dados),
        });

        const corpo = await resposta.json().catch(() => ({}));
        if (!resposta.ok) throw new Error(corpo.erro || `HTTP ${resposta.status}`);

        sessionStorage.setItem("mensagem-cadastro", "Cadastro realizado com sucesso!");
        window.location.href = usuarioLogado ? "/" : "/login";
    } catch (erro) {
        mostrarErro(erro.message);
    } finally {
        botaoCadastro.disabled = false;
    }
});

verificarLogin();

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

// Exporta para uso em testes (Jest) sem afetar a execução no navegador
if (typeof module !== "undefined" && module.exports) {
    module.exports = { buscarEnderecoPorCep, validarCPF };
}
