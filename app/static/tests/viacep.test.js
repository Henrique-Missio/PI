/**
 * Testes da função buscarEnderecoPorCep do cadastro.js
 * Mocka o fetch para simular respostas do ViaCEP sem chamar a API real.
 */

// ── Monta o DOM completo ANTES do require ────────────────────────────────
// Isso é necessário porque cadastro.js executa código de topo (addEventListener)
// no momento em que é importado, e esses elementos precisam existir nesse instante.
document.body.innerHTML = `
    <input id="cpf" />
    <input id="cep" />
    <input id="telefone_celular" />
    <input id="rua" />
    <input id="bairro" />
    <input id="cidade" />
    <input id="estado" />
    <input id="numero" />
    <input id="complemento" />
    <input id="nome_completo" />
    <input id="data_nasc" />
    <select id="funcao"></select>
    <input id="email_pessoal" />
    <input id="senha" />
    <input id="confirmar_senha" />
    <button id="botao-cadastro"></button>
    <p id="mensagem-cadastro"></p>
    <div id="campo-tipo-wrapper" style="display:none">
        <select id="tipo"></select>
    </div>
`;

const cadastroExports = require("../cadastro.js");

const { buscarEnderecoPorCep } = cadastroExports;

// ── Helper: reseta os valores dos campos SEM recriar os elementos ──────────
// Importante: não usar document.body.innerHTML aqui, pois isso criaria nós
// novos e desconectaria a referência interna que cadastro.js já capturou
// para o elemento de mensagem (const mensagem = document.getElementById(...)).
function limparFormulario() {
    ["rua", "bairro", "cidade", "estado", "numero", "cep"].forEach((id) => {
        document.getElementById(id).value = "";
    });
    const mensagem = document.getElementById("mensagem-cadastro");
    mensagem.textContent = "";
    mensagem.className = "";
}

beforeEach(() => {
    limparFormulario();
});

// ── Respostas simuladas do ViaCEP ───────────────────────────────────────────
const RESPOSTA_VALIDA = {
    cep: "96810-000",
    logradouro: "Rua Sinimbu",
    bairro: "Centro",
    localidade: "Santa Cruz do Sul",
    uf: "RS",
};

const RESPOSTA_CEP_INEXISTENTE = { erro: true };

function mockFetch(jsonResposta, ok = true) {
    return jest.fn().mockResolvedValue({
        ok,
        json: () => Promise.resolve(jsonResposta),
    });
}

function mockFetchComErroDeRede() {
    return jest.fn().mockRejectedValue(new Error("Network error"));
}

describe("buscarEnderecoPorCep", () => {
    test("preenche rua, bairro, cidade e estado com CEP válido", async () => {
        const fetchFn = mockFetch(RESPOSTA_VALIDA);

        await buscarEnderecoPorCep("96810000", { fetchFn });

        expect(document.getElementById("rua").value).toBe("Rua Sinimbu");
        expect(document.getElementById("bairro").value).toBe("Centro");
        expect(document.getElementById("cidade").value).toBe("Santa Cruz do Sul");
        expect(document.getElementById("estado").value).toBe("RS");
    });

    test("aceita CEP com máscara (96810-000)", async () => {
        const fetchFn = mockFetch(RESPOSTA_VALIDA);

        await buscarEnderecoPorCep("96810-000", { fetchFn });

        expect(document.getElementById("rua").value).toBe("Rua Sinimbu");
    });

    test("chama a URL correta da API com o CEP limpo", async () => {
        const fetchFn = mockFetch(RESPOSTA_VALIDA);

        await buscarEnderecoPorCep("96810-000", { fetchFn });

        expect(fetchFn).toHaveBeenCalledWith(
            "https://viacep.com.br/ws/96810000/json/"
        );
    });

    test("foca no campo número após preencher o endereço", async () => {
        const fetchFn = mockFetch(RESPOSTA_VALIDA);
        const numeroInput = document.getElementById("numero");
        const focusSpy = jest.spyOn(numeroInput, "focus");

        await buscarEnderecoPorCep("96810000", { fetchFn });

        expect(focusSpy).toHaveBeenCalled();
        focusSpy.mockRestore();
    });

    test("limpa os campos antes de preencher com os novos dados", async () => {
        document.getElementById("rua").value = "Endereço Antigo";
        const fetchFn = mockFetch(RESPOSTA_VALIDA);

        await buscarEnderecoPorCep("96810000", { fetchFn });

        expect(document.getElementById("rua").value).toBe("Rua Sinimbu");
    });

    test("não preenche os campos quando CEP é inexistente", async () => {
        const fetchFn = mockFetch(RESPOSTA_CEP_INEXISTENTE);

        await buscarEnderecoPorCep("00000000", { fetchFn });

        expect(document.getElementById("rua").value).toBe("");
        expect(document.getElementById("bairro").value).toBe("");
        expect(document.getElementById("cidade").value).toBe("");
        expect(document.getElementById("estado").value).toBe("");
    });

    test("mostra mensagem de erro quando CEP é inexistente", async () => {
        const fetchFn = mockFetch(RESPOSTA_CEP_INEXISTENTE);

        await buscarEnderecoPorCep("00000000", { fetchFn });

        const mensagem = document.getElementById("mensagem-cadastro");
        expect(mensagem.textContent).toBe("CEP não encontrado.");
        expect(mensagem.className).toContain("erro");
    });

    test("mostra mensagem de erro quando a API falha (rede)", async () => {
        const fetchFn = mockFetchComErroDeRede();

        await buscarEnderecoPorCep("96810000", { fetchFn });

        const mensagem = document.getElementById("mensagem-cadastro");
        expect(mensagem.textContent).toBe("Erro ao buscar CEP. Verifique sua conexão.");
        expect(mensagem.className).toContain("erro");
    });

    test("não chama a API quando o CEP tem menos de 8 dígitos", async () => {
        const fetchFn = mockFetch(RESPOSTA_VALIDA);

        await buscarEnderecoPorCep("9681000", { fetchFn }); // 7 dígitos

        expect(fetchFn).not.toHaveBeenCalled();
    });

    test("não chama a API quando o CEP tem mais de 8 dígitos", async () => {
        const fetchFn = mockFetch(RESPOSTA_VALIDA);

        await buscarEnderecoPorCep("968100001", { fetchFn }); // 9 dígitos

        expect(fetchFn).not.toHaveBeenCalled();
    });

    test("não chama a API quando o CEP está vazio", async () => {
        const fetchFn = mockFetch(RESPOSTA_VALIDA);

        await buscarEnderecoPorCep("", { fetchFn });

        expect(fetchFn).not.toHaveBeenCalled();
    });

    test("retorna null quando o CEP é inválido (tamanho errado)", async () => {
        const fetchFn = mockFetch(RESPOSTA_VALIDA);

        const resultado = await buscarEnderecoPorCep("123", { fetchFn });

        expect(resultado).toBeNull();
    });

    test("retorna os dados do endereço quando a busca tem sucesso", async () => {
        const fetchFn = mockFetch(RESPOSTA_VALIDA);

        const resultado = await buscarEnderecoPorCep("96810000", { fetchFn });

        expect(resultado).toEqual(RESPOSTA_VALIDA);
    });

    test("retorna null quando o CEP é inexistente", async () => {
        const fetchFn = mockFetch(RESPOSTA_CEP_INEXISTENTE);

        const resultado = await buscarEnderecoPorCep("00000000", { fetchFn });

        expect(resultado).toBeNull();
    });

    test("preenche campos com string vazia quando a API retorna campo faltando", async () => {
        const respostaIncompleta = {
            cep: "96810-000",
            logradouro: "",
            bairro: "Centro",
            localidade: "Santa Cruz do Sul",
            uf: "RS",
        };
        const fetchFn = mockFetch(respostaIncompleta);

        await buscarEnderecoPorCep("96810000", { fetchFn });

        expect(document.getElementById("rua").value).toBe("");
        expect(document.getElementById("bairro").value).toBe("Centro");
    });
});