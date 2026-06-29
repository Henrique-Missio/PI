const listaVoluntarios = document.getElementById("lista-voluntarios");

async function verificarAdmin() {
    const resp = await fetch("/api/me");
    if (!resp.ok) { window.location.href = "/login"; return; }
    const usuario = await resp.json();
    if (usuario.tipo !== "administrador") { window.location.href = "/"; return; }
}

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

(async () => {
    await verificarAdmin();
    await carregarVoluntarios();
})();
