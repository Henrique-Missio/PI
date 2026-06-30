const listaVoluntarios = document.getElementById("lista-voluntarios");
const modal            = document.getElementById("modal-voluntario");
const btnNovo          = document.getElementById("btn-novo-voluntario");
const btnFechar        = document.getElementById("modal-fechar");
const btnCancelar      = document.getElementById("modal-cancelar");
const btnSalvar        = document.getElementById("modal-salvar");
const mMensagem        = document.getElementById("m-mensagem");

// ── Guards ──
async function verificarAdmin() {
    const resp = await fetch("/api/me");
    if (!resp.ok) { window.location.href = "/login"; return; }
    const u = await resp.json();
    if (u.tipo !== "administrador") { window.location.href = "/"; }
}

// ── Modal ──
function abrirModal() {
    limparModal();
    modal.style.display = "flex";
}

function fecharModal() {
    modal.style.display = "none";
}

function limparModal() {
    ["m-nome","m-cpf","m-data-nasc","m-email","m-telefone",
     "m-cep","m-numero","m-rua","m-bairro","m-cidade","m-estado",
     "m-complemento","m-senha","m-confirmar-senha"].forEach(id => {
        document.getElementById(id).value = "";
    });
    document.getElementById("m-funcao").value = "";
    mMensagem.textContent = "";
    mMensagem.className = "mensagem";
}

btnNovo.onclick    = abrirModal;
btnFechar.onclick  = fecharModal;
btnCancelar.onclick = fecharModal;
modal.onclick = (e) => { if (e.target === modal) fecharModal(); };

// ── Máscaras ──
document.getElementById("m-cpf").addEventListener("input", (e) => {
    let v = e.target.value.replace(/\D/g, "").slice(0, 11);
    v = v.replace(/(\d{3})(\d)/, "$1.$2");
    v = v.replace(/(\d{3})(\d)/, "$1.$2");
    v = v.replace(/(\d{3})(\d{1,2})$/, "$1-$2");
    e.target.value = v;
});

document.getElementById("m-telefone").addEventListener("input", (e) => {
    let v = e.target.value.replace(/\D/g, "").slice(0, 11);
    v = v.replace(/(\d{2})(\d)/, "($1) $2");
    v = v.replace(/(\d{5})(\d)/, "$1-$2");
    e.target.value = v;
});

document.getElementById("m-cep").addEventListener("input", (e) => {
    let v = e.target.value.replace(/\D/g, "").slice(0, 8);
    v = v.replace(/(\d{5})(\d)/, "$1-$2");
    e.target.value = v;
});

document.getElementById("m-cep").addEventListener("blur", async (e) => {
    const cep = e.target.value.replace(/\D/g, "");
    if (cep.length !== 8) return;
    try {
        const r = await fetch(`https://viacep.com.br/ws/${cep}/json/`);
        const d = await r.json();
        if (d.erro) return;
        document.getElementById("m-rua").value    = d.logradouro || "";
        document.getElementById("m-bairro").value = d.bairro || "";
        document.getElementById("m-cidade").value = d.localidade || "";
        document.getElementById("m-estado").value = d.uf || "";
    } catch { /* silencioso */ }
});

// ── Cadastrar voluntário ──
btnSalvar.onclick = async () => {
    mMensagem.textContent = "";
    mMensagem.className = "mensagem";

    const senha   = document.getElementById("m-senha").value.trim();
    const confirm = document.getElementById("m-confirmar-senha").value.trim();

    if (senha !== confirm) {
        mMensagem.textContent = "Senhas não coincidem.";
        mMensagem.className = "mensagem erro";
        return;
    }

    const dataNasc = document.getElementById("m-data-nasc").value;
    let dataNascFmt = "";
    if (dataNasc) {
        const [ano, mes, dia] = dataNasc.split("-");
        dataNascFmt = `${dia}-${mes}-${ano}`;
    }

    const dados = {
        tipo:             "voluntario",
        nome_completo:    document.getElementById("m-nome").value.trim(),
        cpf:              document.getElementById("m-cpf").value.replace(/\D/g, ""),
        data_nasc:        dataNascFmt,
        funcao:           document.getElementById("m-funcao").value,
        email_pessoal:    document.getElementById("m-email").value.trim(),
        telefone_celular: document.getElementById("m-telefone").value.replace(/\D/g, ""),
        cep:              document.getElementById("m-cep").value.replace(/\D/g, ""),
        numero:           document.getElementById("m-numero").value.trim(),
        rua:              document.getElementById("m-rua").value.trim(),
        bairro:           document.getElementById("m-bairro").value.trim(),
        cidade:           document.getElementById("m-cidade").value.trim(),
        estado:           document.getElementById("m-estado").value.trim(),
        complemento:      document.getElementById("m-complemento").value.trim(),
        senha,
    };

    btnSalvar.disabled = true;
    try {
        const resp = await fetch("/api/usuarios", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(dados),
        });
        const corpo = await resp.json().catch(() => ({}));
        if (!resp.ok) throw new Error(corpo.erro || `HTTP ${resp.status}`);

        fecharModal();
        await carregarVoluntarios();
    } catch (e) {
        mMensagem.textContent = e.message;
        mMensagem.className = "mensagem erro";
    } finally {
        btnSalvar.disabled = false;
    }
};

// ── Listar voluntários ──
async function carregarVoluntarios() {
    try {
        const resp = await fetch("/api/usuarios");
        if (!resp.ok) return;
        const usuarios = await resp.json();
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
            botao.className = "btn btn-danger btn-sm";
            botao.onclick = async () => {
                if (!confirm(`Excluir o voluntário "${v.nome_completo}"?`)) return;
                try {
                    const r = await fetch(`/api/usuarios/${v.id}`, { method: "DELETE" });
                    if (!r.ok) throw new Error("Erro ao excluir.");
                    await carregarVoluntarios();
                } catch (e) {
                    alert(e.message);
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

(async () => {
    await verificarAdmin();
    await carregarVoluntarios();
})();
