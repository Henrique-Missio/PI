const mensagem = document.getElementById("mensagem-cadastro");
const botaoCadastro = document.getElementById("botao-cadastro");

function mostrarErro(msg) {
    mensagem.textContent = msg;
    mensagem.className = "mensagem erro";
}

function mostrarSucesso(msg) {
    mensagem.textContent = msg;
    mensagem.className = "mensagem sucesso";
}

botaoCadastro.addEventListener("click", async () => {
    const campos = [
        "nome_completo", "cpf", "data_nasc", "funcao",
        "email_pessoal", "telefone_celular",
        "cep", "rua", "bairro", "cidade", "estado",
        "senha", "confirmar_senha"
    ];

    const dados = {};
    for (const campo of campos) {
        const valor = document.getElementById(campo).value.trim();
        if (!valor) {
            mostrarErro(`Preencha o campo "${campo.replace(/_/g, " ")}".`);
            document.getElementById(campo).focus();
            return;
        }
        dados[campo] = valor;
    }

    if (dados.senha !== dados.confirmar_senha) {
        mostrarErro("As senhas não coincidem.");
        return;
    }

    if (dados.senha.length < 6) {
        mostrarErro("A senha deve ter pelo menos 6 caracteres.");
        return;
    }

    if (dados.cpf.length !== 11 || !/^\d+$/.test(dados.cpf)) {
        mostrarErro("CPF inválido. Use apenas 11 números.");
        return;
    }

    if (dados.telefone_celular.length < 10 || !/^\d+$/.test(dados.telefone_celular)) {
        mostrarErro("Telefone inválido. Use apenas números com DDD.");
        return;
    }

    if (dados.cep.length !== 8 || !/^\d+$/.test(dados.cep)) {
        mostrarErro("CEP inválido. Use apenas 8 números.");
        return;
    }

    const [ano, mes, dia] = dados.data_nasc.split("-");
    dados.data_nasc = `${dia}-${mes}-${ano}`;

    delete dados.confirmar_senha;

    botaoCadastro.disabled = true;
    try {
        const resposta = await fetch("/api/cadastro", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(dados),
        });

        const corpo = await resposta.json().catch(() => ({}));
        if (!resposta.ok) throw new Error(corpo.erro || `HTTP ${resposta.status}`);

        mostrarSucesso("Cadastro realizado! Redirecionando para o login...");
        setTimeout(() => window.location.href = "/login", 2000);
    } catch (erro) {
        mostrarErro(erro.message);
    } finally {
        botaoCadastro.disabled = false;
    }
});