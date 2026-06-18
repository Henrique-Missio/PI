const mensagem = document.getElementById("mensagem-perfil");
const botaoSalvar = document.getElementById("botao-salvar-perfil");
const botaoExcluir = document.getElementById("botao-excluir-conta");
const cardVoluntarios = document.getElementById("card-voluntarios");
const listaVoluntarios = document.getElementById("lista-voluntarios");

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

async function verificarAdmin() {
    try {
        const resposta = await fetch("/api/me");
        if (resposta.ok) {
            usuarioAtual = await resposta.json();
            if (usuarioAtual.tipo === "administrador") {
                cardVoluntarios.style.display = "block";
                await carregarVoluntarios();
            }
        }
    } catch {
        usuarioAtual = null;
    }
}

async function carregarVoluntarios() {
    try {
        const resposta = await fetch("/api/usuarios");
        if (!resposta.ok) return;
        const usuarios = await resposta.json();
        const voluntarios = usuarios.filter(u => u.tipo === "voluntario");

        listaVoluntarios.innerHTML = "";
        if (!voluntarios.length) {
            listaVoluntarios.innerHTML = "<p>Nenhum voluntário cadastrado.</p>";
            return;
        }

        voluntarios.forEach(v => {
            const linha = document.createElement("div");
            linha.className = "linha-voluntario";

            const nome = document.createElement("span");
            nome.textContent = `${v.nome_completo} — ${v.funcao}`;

            const botao = document.createElement("button");
            botao.textContent = "Excluir";
            botao.className = "botao-excluir";
            botao.onclick = async () => {
                if (!confirm(`Excluir o voluntário "${v.nome_completo}"?`)) return;
                try {
                    const resp = await fetch(`/api/usuarios/${v.id}`, { method: "DELETE" });
                    if (!resp.ok) throw new Error("Erro ao excluir.");
                    await carregarVoluntarios();
                } catch (erro) {
                    alert(erro.message);
                }
            };

            linha.appendChild(nome);
            linha.appendChild(botao);
            listaVoluntarios.appendChild(linha);
        });
    } catch {
        listaVoluntarios.innerHTML = "<p>Erro ao carregar voluntários.</p>";
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
    if (novaSenha) dados.senha = novaSenha;

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

carregarPerfil();
verificarAdmin();