# Projeto escolar — Flask, SQLite e SQLAlchemy (didático)

Projeto de referência para aulas de **Python**, **API HTTP** e **banco de dados relacional**. O domínio é simples: **professores**, **turmas** e **alunos**. A ideia é que o aluno reconheça o mesmo vocabulário das aulas de SQL (`CREATE TABLE`, chaves estrangeiras, `SELECT`), mas agora com **Python**, **Flask** e **SQLAlchemy**.

---

## Sumário

1. [O que este projeto ensina](#1-o-que-este-projeto-ensina)
2. [Stack tecnológica](#2-stack-tecnológica)
3. [Organização das pastas e arquivos](#3-organização-das-pastas-e-arquivos)
4. [Endpoints da API](#4-endpoints-da-api)
5. [UI de cadastro](#5-ui-de-cadastro)
6. [Como o frontend conversa com o backend](#6-como-o-frontend-conversa-com-o-backend)
7. [Como o banco é criado, populado e relacionado](#7-como-o-banco-é-criado-populado-e-relacionado)
8. [Ideias que vale a pena explicar em sala](#8-ideias-que-vale-a-pena-explicar-em-sala)
9. [Pré-requisitos no Windows](#9-pré-requisitos-no-windows)
10. [Passo a passo — Prompt de Comando (CMD)](#10-passo-a-passo--prompt-de-comando-cmd)
11. [Passo a passo — PowerShell](#11-passo-a-passo--powershell)
12. [Como saber se deu certo](#12-como-saber-se-deu-certo)
13. [Relacionar com SQL “puro”](#13-relacionar-com-sql-puro)
14. [Problemas frequentes no Windows](#14-problemas-frequentes-no-windows)

---

## 1. O que este projeto ensina

| Tema | Onde aparece no código |
|------|-------------------------|
| Definir tabelas como classes Python | `models.py` |
| Conectar ao SQLite e criar sessões | `database.py` |
| Criar tabelas e inserir dados com script | `setup_database.py` |
| Separar “regra de banco” das rotas HTTP | `servicos.py` |
| Expor URLs que listam e cadastram dados (JSON) | `app/routes.py` |
| Montar a aplicação Flask | `app/__init__.py`, `run.py` |
| UI HTML/CSS/JS consumindo a API | `app/templates/index.html`, `app/static/` |

Fluxo mental para o aluno:

1. Os **modelos** descrevem o esquema (como um `CREATE TABLE` conceitual).
2. O script **`setup_database.py`** materializa esse esquema no arquivo **`instance/app.db`** e insere dados de exemplo.
3. O **Flask** recebe pedidos HTTP, pede aos **serviços** que leiam ou gravem no banco, e devolve **JSON**.
4. A **página `/`** é uma interface simples que usa `fetch` para listar e cadastrar Professor / Turma / Aluno.

---

## 2. Stack tecnológica

- **Python 3** — linguagem.
- **Flask** — framework web minimalista (rotas, respostas JSON).
- **SQLAlchemy** — camada que traduz classes Python em tabelas SQL e permite consultas orientadas a objetos (sem Flask-SQLAlchemy neste projeto, para a sessão do banco ficar explícita).
- **SQLite** — banco em um único arquivo (`instance/app.db`), ideal para laboratório.

Dependências declaradas em `requirements.txt`: **Flask** e **SQLAlchemy**.

---

## 3. Organização das pastas e arquivos

```
project-python-from-scratch/
├── README.md                 ← este guia
├── requirements.txt          ← lista de bibliotecas
├── run.py                    ← sobe o servidor de desenvolvimento
├── config.py                 ← SECRET_KEY e pasta instance
├── database.py               ← engine, SessionLocal, Base, URL do SQLite
├── models.py                 ← Professor, Turma, Aluno
├── setup_database.py         ← recria tabelas e popula dados (rode antes da API)
├── servicos.py               ← consultas e cadastros usados pelas rotas
├── app/
│   ├── __init__.py           ← factory create_app() (registra blueprints API e páginas)
│   ├── routes.py             ← URLs /api/... (GET e POST) e a rota / da UI
│   ├── templates/
│   │   └── index.html        ← página única com abas e formulários
│   └── static/
│       ├── styles.css        ← estilo da interface
│       └── app.js            ← consome /api/... com fetch
└── instance/
    └── app.db                ← criado após rodar setup_database.py (não versionar)
```

> **Nota:** a pasta `instance/` pode não existir antes do primeiro `setup_database.py`; o código cria o diretório quando necessário.

---

## 4. Endpoints da API

Todos os endpoints retornam **JSON**. Os de cadastro (`POST`) recebem `Content-Type: application/json`.

| Método | URL | O que faz | Sucesso | Erros possíveis |
|--------|-----|-----------|---------|-----------------|
| GET    | `/api/professores` | Lista todos os professores | `200` | — |
| POST   | `/api/professores` | Cadastra professor (`nome`, `email?`) | `201` | `400` campo faltando, `409` e-mail duplicado |
| GET    | `/api/turmas` | Lista todas as turmas | `200` | — |
| POST   | `/api/turmas` | Cadastra turma (`nome`, `codigo`, `professor_id`) | `201` | `400` FK inválida, `409` código duplicado |
| GET    | `/api/alunos` | Lista todos os alunos | `200` | — |
| POST   | `/api/alunos` | Cadastra aluno (`nome`, `email?`, `turma_id`) | `201` | `400` FK inválida, `409` e-mail duplicado |

Em caso de erro, a resposta é `{"erro": "mensagem"}`.

Exemplo (PowerShell):

```powershell
$dados = @{ nome = "Ana"; email = "ana@escola.example" } | ConvertTo-Json
Invoke-RestMethod -Uri http://127.0.0.1:5000/api/professores -Method Post -Body $dados -ContentType "application/json"
```

Exemplo (CMD com `curl` no Windows 10/11):

```bat
curl -X POST -H "Content-Type: application/json" -d "{\"nome\":\"Ana\"}" http://127.0.0.1:5000/api/professores
```

---

## 5. UI de cadastro

Acesse **http://127.0.0.1:5000/** com o servidor rodando. A página tem:

- **Abas** Professores / Turmas / Alunos.
- **Formulário** dinâmico acima da tabela:
  - Professor: `nome` (obrigatório), `e-mail` (opcional).
  - Turma: `nome`, `codigo`, `professor` (selecionado em uma lista).
  - Aluno: `nome`, `e-mail` (opcional), `turma` (selecionada em uma lista).
- **Botão Cadastrar** envia POST para `/api/...` e mostra mensagem **verde** (sucesso) ou **vermelha** (erro).
- **Tabela** abaixo recarrega automaticamente após cada cadastro; também há um botão **Recarregar**.

Os selects de Professor (em Turma) e Turma (em Aluno) são preenchidos por chamadas `GET /api/...` no momento da troca de aba.

---

## 6. Como o frontend conversa com o backend

Esta seção explica em detalhe **onde** e **como** o navegador (frontend) chama os endpoints da API (backend). Útil para mostrar ao aluno que `fetch` no navegador é só um cliente HTTP, igual a `curl` ou Postman.

### 6.1 Visão geral em uma figura

```
+-----------------------+   GET /                +-------------------------+
|                       |  ───────────────────▶  |                         |
|   Navegador (HTML +   |  ◀───── HTML ──────    |   Flask (app/routes.py) |
|   CSS + app.js)       |                        |                         |
|                       |   GET /api/professores |   /api  → JSON          |
|                       |  ───────────────────▶  |   /     → index.html    |
|                       |  ◀──── JSON ────────   |                         |
|                       |                        |                         |
|                       |   POST /api/professores|   chama servicos.py     |
|                       |  ───────────────────▶  |   chama database/SQLite |
|                       |  ◀── 201 / 4xx JSON ── |                         |
+-----------------------+                        +-------------------------+
```

- **Servidor único** (Flask) responde tanto pelo HTML inicial (`/`) quanto pela API (`/api/...`).
- Por estar no **mesmo host:porta**, o `fetch` do navegador pode usar caminhos relativos (`/api/professores`) sem se preocupar com CORS.

### 6.2 Quem registra cada rota

Em `app/__init__.py` o `create_app()` registra **dois blueprints**:

```python
from app.routes import bp as api_bp, paginas as paginas_bp

app.register_blueprint(api_bp)      # /api/...
app.register_blueprint(paginas_bp)  # /
```

Em `app/routes.py`:

- `bp` (prefixo `/api`): `GET` e `POST` para professores, turmas, alunos.
- `paginas` (sem prefixo): `GET /` que devolve `render_template("index.html")`.

### 6.3 Onde o HTML referencia os arquivos estáticos

Em `app/templates/index.html`:

```html
<link rel="stylesheet" href="{{ url_for('static', filename='styles.css') }}" />
...
<script src="{{ url_for('static', filename='app.js') }}"></script>
```

Quando o Flask renderiza o template, `url_for("static", filename="...")` vira `/static/styles.css` e `/static/app.js`. O navegador então faz **três requisições**: HTML, CSS e JS. A partir daí o JavaScript assume.

### 6.4 O HTML é um esqueleto vazio (quem fala com o backend é o JavaScript)

Olhando `app/templates/index.html`, **note que ele não tem dados do banco**. Os pontos onde os dados aparecem são apenas “contêineres com `id`” vazios:

```html
<div id="campos" class="grade-campos"></div>
...
<table id="tabela">
  <thead><tr id="cabecalho"></tr></thead>
  <tbody id="corpo"></tbody>
</table>
```

`campos`, `cabecalho`, `corpo` (e também `status`, `formulario`, `mensagem-formulario`, etc.) são **ganchos** — pontos onde o JavaScript vai inserir o conteúdo depois.

Quem realmente chama o backend é o `app/static/app.js`. Os pedaços-chave:

```javascript
async function buscar(tipo) {
  const resposta = await fetch(`/api/${tipo}`);   // chama o backend (GET)
  if (!resposta.ok) throw new Error(`HTTP ${resposta.status}`);
  return resposta.json();                          // converte JSON em array de objetos
}
```

```javascript
function renderizarLinhas(tipo, dados) {
  for (const item of dados) {
    const tr = document.createElement("tr");
    for (const coluna of COLUNAS[tipo]) {
      const td = document.createElement("td");
      td.textContent = item[coluna.chave];        // valor vindo do banco
      tr.appendChild(td);
    }
    elementoCorpo.appendChild(tr);                // insere no <tbody id="corpo">
  }
}
```

```javascript
const resposta = await fetch(`/api/${tipoAtual}`, {
  method: "POST",                                  // chama o backend (POST)
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify(dados),
});
```

Linha do tempo do que acontece no navegador ao abrir a página:

1. Você acessa `http://127.0.0.1:5000/`.
2. Flask devolve **`index.html`** (ainda sem dados do banco).
3. Navegador encontra `<link>` e `<script>` no HTML e baixa **CSS** e **`app.js`**.
4. `app.js` executa e chama `carregar("professores")`.
5. `carregar` faz `fetch("/api/professores")` — esta é a **primeira** chamada ao backend depois do HTML.
6. Flask roda a rota `GET /api/professores` e devolve **JSON** vindo do banco.
7. `app.js` cria `<tr>` e `<td>` e enfia dentro do `<tbody id="corpo">` que estava vazio. **Aí** os dados aparecem.

Em resumo:

- **HTML** = palco (caixas vazias com `id`).
- **`app.js`** = ator que chama `/api/...` e preenche o palco.
- **Flask + SQLAlchemy + SQLite** = quem produz os dados que o JS recebe em JSON.

Para ver isso ao vivo: abra a página, **F12** → aba **Network/Rede**, e recarregue. A ordem aparece bonitinha — `index.html`, `styles.css`, `app.js` e em seguida `api/professores`. Em **Elements/Elementos**, antes do JS rodar o `<tbody id="corpo">` está vazio; depois, ele tem uma `<tr>` para cada professor — inseridos pelo JS, não pelo HTML.

### 6.5 Ciclo de listagem (GET) — abrir a aba “Professores”

1. **Usuário** clica na aba “Professores”.  
2. `app.js` chama `carregar("professores")`, que chama `buscar("professores")`:

   ```js
   async function buscar(tipo) {
     const resposta = await fetch(`/api/${tipo}`);          // 1) requisição
     if (!resposta.ok) throw new Error(`HTTP ${resposta.status}`);
     return resposta.json();                                 // 2) parse JSON
   }
   ```

3. O Flask roteia `GET /api/professores` para `professores()` em `app/routes.py`:

   ```python
   @bp.get("/professores")
   def professores():
       return fk.jsonify(listar_professores())
   ```

4. `servicos.listar_professores()` abre `SessionLocal()`, faz `select(Professor)`, monta lista de dicts e fecha a sessão.  
5. Flask devolve `200 OK` com corpo JSON: `[{"id":1,"nome":"Maria",...}, ...]`.  
6. `app.js` recebe o array, monta a tabela e atualiza o status (“N registro(s) carregado(s).”).

### 6.6 Ciclo de cadastro (POST) — adicionar uma turma

1. **Usuário** preenche o formulário e clica em **Cadastrar**.  
2. `enviarFormulario(evento)` em `app.js`:

   ```js
   const resposta = await fetch(`/api/${tipoAtual}`, {
     method: "POST",
     headers: { "Content-Type": "application/json" },
     body: JSON.stringify(dados),
   });
   ```

   - `method: "POST"` muda o verbo HTTP (não é mais leitura).
   - `headers["Content-Type"]: "application/json"` avisa ao servidor que o corpo é JSON.
   - `body: JSON.stringify(dados)` serializa o objeto Python-like para texto JSON.

3. O Flask roteia `POST /api/turmas` para `criar_turma()`:

   ```python
   @bp.post("/turmas")
   def criar_turma():
       dados = fk.request.get_json(silent=True) or {}
       try:
           return fk.jsonify(cadastrar_turma(dados)), 201
       except ValueError as exc:
           return _erro(str(exc))
       except IntegrityError:
           return _erro("Já existe uma turma com este código.", 409)
   ```

   - `request.get_json(silent=True)` lê o corpo e devolve um dict Python.
   - `cadastrar_turma(dados)` está em `servicos.py`, valida campos, abre sessão, faz `add` + `commit` e retorna o registro como dict.
   - Códigos de status: `201` para sucesso, `400` para validação, `409` para violação de unicidade.

4. De volta ao `app.js`:

   ```js
   const corpo = await resposta.json().catch(() => ({}));
   if (!resposta.ok) {
     throw new Error(corpo.erro || `HTTP ${resposta.status}`);
   }
   ```

   - Se `resposta.ok` for `true` (status 2xx), mostra a mensagem verde e chama `carregar(tipoAtual)` para **atualizar a tabela**.
   - Se for erro, exibe a mensagem `corpo.erro` (mandada pelo Flask) em vermelho.

### 6.7 Por que selects de Professor e Turma também usam a API

Para o usuário escolher um professor ao criar uma turma, o JS precisa saber **quais professores existem**. Como toda a verdade está no banco, a UI pede de novo ao backend:

```js
const itens = await buscar(campo.origem); // GET /api/professores ou /api/turmas
```

Isso reforça o princípio “**a UI nunca inventa dados**: pergunta ao servidor”.

### 6.8 Tabela-resumo das interações

| Ação no usuário | Função no `app.js` | Requisição HTTP | Rota no Flask | Função de serviço |
|----------------|--------------------|-----------------|---------------|-------------------|
| Trocar para aba Professores | `carregar("professores")` | `GET /api/professores` | `professores()` | `listar_professores()` |
| Trocar para aba Turmas | `carregar("turmas")` | `GET /api/turmas` (+ `GET /api/professores` para o select) | `turmas()`, `professores()` | `listar_turmas()`, `listar_professores()` |
| Trocar para aba Alunos | `carregar("alunos")` | `GET /api/alunos` (+ `GET /api/turmas`) | `alunos()`, `turmas()` | `listar_alunos()`, `listar_turmas()` |
| Cadastrar professor | `enviarFormulario` | `POST /api/professores` | `criar_professor()` | `cadastrar_professor()` |
| Cadastrar turma | `enviarFormulario` | `POST /api/turmas` | `criar_turma()` | `cadastrar_turma()` |
| Cadastrar aluno | `enviarFormulario` | `POST /api/alunos` | `criar_aluno()` | `cadastrar_aluno()` |
| Clicar em Recarregar | `carregar(tipoAtual)` | mesmo `GET` da aba ativa | mesmo handler | mesmo serviço |

### 6.9 Como observar isso ao vivo no navegador

Com o servidor rodando, abra `http://127.0.0.1:5000/`, então **F12** → aba **Network** (ou “Rede”).

- Ao trocar de aba, aparecem requisições para `/api/professores`, `/api/turmas`, `/api/alunos`.
- Ao clicar em **Cadastrar**, aparece uma requisição **POST** com o JSON enviado e a resposta (status, body).
- A aba **Console** mostra `console.log` ou erros do JS.

É a forma mais didática de provar para o aluno que **frontend e backend são dois programas diferentes conversando por HTTP**, mesmo morando no mesmo PC.

---

## 7. Como o banco é criado, populado e relacionado

Esta seção explica em detalhe **como saímos das classes Python** (em `models.py`) **para tabelas reais no SQLite** e como **inserir dados** com relações entre eles. É a parte que costuma confundir quem só conhece SQL "à mão".

### 7.1 Visão geral em três passos

```
models.py   ──► Base.metadata  ──► engine (SQLite)  ──► instance/app.db
   (Python)        (catálogo)        (motor)            (arquivo no disco)
```

1. **`models.py`** descreve **as tabelas como classes Python**.  
2. **`database.py`** monta o `engine` (motor que conecta no arquivo SQLite) e o **`Base`** (catálogo que junta todas as classes que herdam dele).  
3. **`setup_database.py`** chama `Base.metadata.create_all(engine)`. **Aí sim** o SQLAlchemy gera o SQL `CREATE TABLE ...` e roda dentro do arquivo `instance/app.db`.

### 7.2 Quem cria o `engine` e o `Base`

Trecho central de [`database.py`](database.py):

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = f"sqlite:///{_db_path}"  # caminho do arquivo .db

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
```

- **`engine`** é o "motor" que sabe abrir o arquivo SQLite e mandar SQL.
- **`SessionLocal()`** cria uma **sessão** (turno de trabalho) ligada a esse engine.
- **`Base`** é a classe-mãe de todos os modelos. Cada classe que herda de `Base` é registrada num catálogo interno: `Base.metadata`.

### 7.3 As classes em `models.py` viram tabelas

Trecho de [`models.py`](models.py):

```python
class Professor(Base):
    __tablename__ = "professores"

    id = Column(Integer, primary_key=True)
    nome = Column(String(120), nullable=False)
    email = Column(String(120), unique=True, nullable=True)

    turmas = relationship("Turma", back_populates="professor")
```

Tradução para SQL (gerada pelo SQLAlchemy):

```sql
CREATE TABLE professores (
    id INTEGER PRIMARY KEY,
    nome VARCHAR(120) NOT NULL,
    email VARCHAR(120) UNIQUE
);
```

Detalhes importantes:

- **`__tablename__`** → nome da tabela no SQLite. Sem isso a tabela não existe.
- **`Column(Integer, primary_key=True)`** → `INTEGER PRIMARY KEY` (no SQLite isso autoincrementa).
- **`String(120)`** → equivale a `VARCHAR(120)`. No SQLite o tipo é flexível, mas o tamanho serve de documentação.
- **`nullable=False`** → `NOT NULL`.
- **`unique=True`** → `UNIQUE`. Se você tentar inserir o mesmo `email` duas vezes, o banco recusa (erro 409 nas APIs).
- **`relationship(...)`** **não cria coluna** no banco; é uma facilidade só do Python (ver 7.6).

### 7.4 Chaves estrangeiras (FKs) em `Turma` e `Aluno`

```python
class Turma(Base):
    __tablename__ = "turmas"

    id = Column(Integer, primary_key=True)
    nome = Column(String(120), nullable=False)
    codigo = Column(String(40), unique=True, nullable=False)
    professor_id = Column(Integer, ForeignKey("professores.id"), nullable=False)
```

```sql
CREATE TABLE turmas (
    id INTEGER PRIMARY KEY,
    nome VARCHAR(120) NOT NULL,
    codigo VARCHAR(40) UNIQUE NOT NULL,
    professor_id INTEGER NOT NULL,
    FOREIGN KEY (professor_id) REFERENCES professores (id)
);
```

A coluna **`professor_id`** guarda o `id` do professor responsável pela turma. **`ForeignKey("professores.id")`** documenta no banco que esse valor **precisa existir** em `professores.id`. O mesmo padrão é usado em `Aluno.turma_id` apontando para `turmas.id`.

Visão entidade-relacionamento (ER):

```
Professor (1) ─── (N) Turma (1) ─── (N) Aluno
```

- Um **professor** pode ter **várias turmas**.
- Uma **turma** pode ter **vários alunos**.
- Cada turma tem **exatamente um** professor (FK obrigatória).
- Cada aluno tem **exatamente uma** turma.

### 7.5 Onde as tabelas realmente nascem: `create_all`

Trecho central de [`setup_database.py`](setup_database.py):

```python
from database import Base, SessionLocal, engine
import models  # importa as classes para que elas se registrem no Base.metadata

print("Limpando e criando tabelas...")
Base.metadata.drop_all(bind=engine)    # apaga tudo (laboratório)
Base.metadata.create_all(bind=engine)  # cria tudo de novo a partir das classes
```

O `import models` é **fundamental**: ele faz o Python executar `models.py`, e cada classe que herda de `Base` se registra no `Base.metadata`. Sem esse import, `create_all` não saberia que existem `professores`, `turmas`, `alunos`.

- **`drop_all`** = `DROP TABLE alunos; DROP TABLE turmas; DROP TABLE professores;` (na ordem inversa das dependências).  
- **`create_all`** = `CREATE TABLE professores (...); CREATE TABLE turmas (...); CREATE TABLE alunos (...);` (na ordem correta).

> Dica didática: peça aos alunos para abrir `instance/app.db` no DB Browser depois desse passo. As três tabelas estarão lá, com colunas e tipos exatamente como nas classes.

### 7.6 `relationship()` — o atalho orientado a objetos

Olhe novamente os modelos:

```python
class Professor(Base):
    turmas = relationship("Turma", back_populates="professor")

class Turma(Base):
    professor = relationship("Professor", back_populates="turmas")
    alunos = relationship("Aluno", back_populates="turma")

class Aluno(Base):
    turma = relationship("Turma", back_populates="alunos")
```

Isso **não cria coluna nenhuma**; é só açúcar para o Python. Em uma sessão você pode fazer:

```python
maria = session.scalar(select(Professor).where(Professor.nome == "Maria Silva"))
print(maria.turmas)            # lista de Turma
print(maria.turmas[0].alunos)  # lista de Aluno
print(aluno.turma.professor.nome)  # navega na rede de relacionamentos
```

`back_populates` mantém os dois lados sincronizados em memória: se você adicionar uma turma a `maria.turmas`, a propriedade `turma.professor` aponta para Maria automaticamente.

### 7.7 Como funcionam os inserts (DML)

Inserir tem três passos: **criar o objeto**, **adicionar à sessão**, **commitar**. O `setup_database.py` faz isso em três blocos:

```python
session = SessionLocal()
try:
    print("Inserindo professores...")
    professores = [
        models.Professor(nome="Maria Silva", email="maria@escola.example"),
        models.Professor(nome="João Santos", email="joao.santos@escola.example"),
    ]
    session.add_all(professores)
    session.flush()  # gera os ids no banco sem fechar a transação
```

Equivalente em SQL puro:

```sql
INSERT INTO professores (nome, email) VALUES ('Maria Silva', 'maria@escola.example');
INSERT INTO professores (nome, email) VALUES ('João Santos', 'joao.santos@escola.example');
```

`session.flush()` é a hora que o SQLAlchemy **executa** os inserts pendentes para que o banco gere os `id` autoincrementáveis. Depois disso, `professores[0].id` deixa de ser `None` e podemos usá-lo na próxima inserção:

```python
turmas = [
    models.Turma(
        nome="Matemática A",
        codigo="MAT-2026-A",
        professor_id=professores[0].id,  # já existe porque demos flush
    ),
    ...
]
session.add_all(turmas)
session.flush()
```

E por fim os alunos, usando `turmas[i].id`. Quando todos os inserts estão prontos:

```python
session.commit()
```

`commit()` é o equivalente a um `COMMIT` em SQL: confirma a transação e tudo fica gravado em `instance/app.db`. Se algo der errado **antes** do commit, o `except` chama `session.rollback()` e nada é gravado — o banco volta ao estado anterior.

> Para alunos: insistam que **`add` não grava**. Ele coloca o objeto em uma lista interna ("pending"). Só `flush` ou `commit` realmente mandam para o SQLite.

### 7.8 Inserts feitos pela API (rota POST)

A mesma lógica aparece nas funções de [`servicos.py`](servicos.py), só que agora o "dado novo" vem do JSON da requisição. Exemplo:

```python
def cadastrar_turma(dados):
    nome = _texto_obrigatorio(dados.get("nome"), "nome")
    codigo = _texto_obrigatorio(dados.get("codigo"), "codigo")
    professor_id = dados.get("professor_id")
    if not professor_id:
        raise ValueError("O campo 'professor_id' é obrigatório.")

    session = SessionLocal()
    try:
        professor = session.get(Professor, int(professor_id))
        if professor is None:
            raise ValueError(f"Professor {professor_id} não encontrado.")

        turma = Turma(nome=nome, codigo=codigo, professor_id=professor.id)
        session.add(turma)
        session.commit()
        session.refresh(turma)
        return turma.to_dict()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
```

Diferenças importantes em relação ao script:

- A **FK é validada manualmente** com `session.get(Professor, ...)` antes do insert, para devolver mensagens amigáveis em vez de erro genérico do banco.
- Se a inserção falhar (FK inválida, ou `IntegrityError` por código duplicado), o `except` aciona `session.rollback()`. As rotas em `app/routes.py` capturam:

```python
except IntegrityError:
    return _erro("Já existe uma turma com este código.", 409)
```

### 7.9 Tabela-resumo do que acontece em cada momento

| Ação | Onde | O que faz |
|------|------|-----------|
| Definir tabelas | `models.py` | Classes herdam de `Base` e cada `Column` vira coluna SQL |
| Conectar ao SQLite | `database.py` | Cria `engine`, `SessionLocal`, `Base` |
| Criar arquivo `app.db` | `setup_database.py` (ou primeiro `create_all`) | `Base.metadata.create_all(engine)` |
| Apagar tabelas | `setup_database.py` | `Base.metadata.drop_all(engine)` |
| Inserir dados de seed | `setup_database.py` | `add_all` + `flush` + `commit` |
| Inserir via API | `servicos.py` (`cadastrar_*`) | `Session()` → `add` → `commit` |
| Validar duplicidade | banco SQLite + SQLAlchemy | `unique=True` levanta `IntegrityError` → rota devolve 409 |
| Validar FK | `servicos.py` (`session.get(...)` ou `IntegrityError`) | rota devolve 400 ou 409 |
| Ler dados | `servicos.py` (`listar_*`) | `session.scalars(select(Modelo))` |

### 7.10 Conferindo no SQLite "de verdade"

Depois de rodar `python setup_database.py`, abra `instance/app.db` no **DB Browser for SQLite** e rode:

```sql
SELECT * FROM professores;
SELECT * FROM turmas;
SELECT t.nome AS turma, p.nome AS professor
FROM turmas t
JOIN professores p ON p.id = t.professor_id;
SELECT a.nome AS aluno, t.nome AS turma
FROM alunos a
JOIN turmas t ON t.id = a.turma_id;
```

Os resultados batem **exatamente** com o que `models.py` declarou e com o que `setup_database.py` inseriu — fechando o ciclo **classe Python → tabela SQL → linha no arquivo `.db`**.

---

## 8. Ideias que vale a pena explicar em sala

**Engine** (`database.py`)  
Pense como o “motor” que sabe falar com o arquivo SQLite.

**SessionLocal e `session`** (`database.py`, `servicos.py`, `setup_database.py`)  
Uma **sessão** é um ciclo de trabalho: você consulta ou altera dados e depois **fecha** a sessão. Isso aproxima o aluno da ideia de transação (`commit` / `rollback`).

**Base e modelos** (`models.py`)  
Cada classe representa uma **tabela**; atributos `Column` representam **colunas** e `ForeignKey` representam **chaves estrangeiras**.

**Blueprint** (`app/routes.py`)  
Agrupa rotas: o blueprint `api` cuida de `/api/...` (JSON) e o blueprint `paginas` cuida de `/` (HTML). Sem misturar tudo num arquivo gigante.

**Separação `servicos` × `routes`**  
As rotas só dizem *qual URL* e *qual formato de resposta* (JSON ou HTML). Os serviços concentram *como* ler e gravar no banco — é o mesmo padrão de muitos projetos reais.

**Frontend `fetch` consumindo JSON** (`app/static/app.js`)  
O `app.js` mostra como JavaScript no navegador chama `/api/...` para listar e cadastrar dados, sem precisar de framework. Boa porta de entrada para a ideia de **cliente × servidor** — os detalhes do `fetch` estão na seção 6.

---

## 9. Pré-requisitos no Windows

1. **Python 3 instalado** a partir de [python.org](https://www.python.org/downloads/).
2. Durante a instalação, marque **“Add python.exe to PATH”**.
3. Abra um terminal:
   - **Prompt de Comando**: tecla Windows, digite `cmd`, Enter.
   - **PowerShell**: tecla Windows, digite `PowerShell`, Enter.

Confira se o Python responde:

```bat
python --version
```

Se aparecer erro do tipo “não é reconhecido”, teste o **launcher** oficial:

```bat
py --version
```

Daqui em diante, sempre que aparecer `python` nos comandos e no seu PC só funcionar `py`, **substitua** `python` por `py` (é comum em algumas instalações).

---

## 10. Passo a passo — Prompt de Comando (CMD)

Execute os passos **na ordem**. Troque o caminho pela pasta onde você guardou o projeto (por exemplo `Documents`).

### 10.1 Entrar na pasta do projeto

```bat
cd %USERPROFILE%\Documents\project-python-from-scratch
```

> Se o projeto estiver em outro lugar, use o caminho completo, por exemplo:  
> `cd D:\disciplinas\project-python-from-scratch`

Confira se `run.py` e `requirements.txt` estão aí:

```bat
dir run.py
dir requirements.txt
```

### 10.2 Criar o ambiente virtual (uma vez por máquina ou quando quiser ambiente limpo)

O ambiente virtual isola as bibliotecas **deste** projeto das demais instalações do Windows.

```bat
python -m venv .venv
```

(Se falhar, use `py -m venv .venv`.)

### 10.3 Ativar o ambiente virtual

```bat
.venv\Scripts\activate.bat
```

Quando estiver ativo, o prompt costuma começar com `(.venv)`.

### 10.4 Atualizar o pip (opcional, recomendado)

```bat
python -m pip install --upgrade pip
```

### 10.5 Instalar as dependências do projeto

O arquivo `requirements.txt` lista Flask e SQLAlchemy. O comando correto usa **`-r`** (traço e letra **r**) e **espaço** antes do nome do arquivo:

```bat
pip install -r requirements.txt
```

> Erro comum: digitar `-requirements` em vez de `-r requirements.txt`. O `-r` significa “ler pacotes **de** um arquivo”.

### 10.6 Criar o banco e inserir dados de exemplo

Este passo **apaga e recria** as tabelas e popula professores, turmas e alunos de laboratório:

```bat
python setup_database.py
```

Você deve ver mensagens no console (“Limpando e criando tabelas…”, “Sucesso!” etc.).  
O arquivo **`instance\app.db`** será criado ou atualizado.

### 10.7 Subir o servidor Flask

```bat
python run.py
```

Deixe essa janela **aberta**. O servidor fica escutando em **http://127.0.0.1:5000** (ou `localhost:5000`).  
A **UI de cadastro** abre em **http://127.0.0.1:5000/** e a API em **http://127.0.0.1:5000/api/...**.

Para parar o servidor: **Ctrl+C**.

---

## 11. Passo a passo — PowerShell

Os passos são os mesmos; mudam só **ativar o venv** e, às vezes, política de scripts.

### 11.1 Ir para a pasta do projeto

```powershell
cd $env:USERPROFILE\Documents\project-python-from-scratch
```

### 11.2 Criar e ativar o ambiente virtual

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Se aparecer erro de **execução de scripts**, rode uma vez (por usuário):

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Depois tente ativar de novo:

```powershell
.\.venv\Scripts\Activate.ps1
```

### 11.3 Instalar dependências, banco e servidor

```powershell
pip install -r requirements.txt
python setup_database.py
python run.py
```

---

## 12. Como saber se deu certo

### 12.1 Pela UI (com `python run.py` rodando)

Abra **http://127.0.0.1:5000/**. Você deve ver:

- Cabeçalho azul “Escola”.
- Abas **Professores / Turmas / Alunos**.
- Formulário de cadastro acima e tabela com os dados abaixo (já preenchida pelo `setup_database.py`).

Cadastre um professor, depois uma turma escolhendo esse professor, e por fim um aluno na turma. As tabelas devem se atualizar.

### 12.2 Pelo navegador acessando a API direto

Abra:

- http://127.0.0.1:5000/api/professores  
- http://127.0.0.1:5000/api/turmas  
- http://127.0.0.1:5000/api/alunos  

Você deve ver **JSON** (listas de objetos com `id`, `nome`, etc.).

### 12.3 Pelo CMD ou PowerShell (outra janela, com o servidor ainda rodando)

No **Windows 10/11** costuma existir `curl`:

```bat
curl -s http://127.0.0.1:5000/api/professores
```

No **PowerShell**, se preferir:

```powershell
(Invoke-WebRequest -Uri http://127.0.0.1:5000/api/professores -UseBasicParsing).Content
```

Cadastrando via terminal (ver exemplos completos na seção 4).

---

## 13. Relacionar com SQL “puro”

Depois de rodar `setup_database.py`, abra `instance\app.db` com o **DB Browser for SQLite** ([sqlitebrowser.org](https://sqlitebrowser.org/)) ou outra ferramenta e execute:

```sql
SELECT * FROM professores;
SELECT * FROM turmas;
SELECT * FROM alunos;
```

Isso fecha o ciclo: **modelo Python** → **arquivo SQLite** → **consulta SQL textual**.

---

## 14. Problemas frequentes no Windows

| Sintoma | O que verificar |
|---------|------------------|
| `python` não é reconhecido | Instalar Python com PATH ou usar `py` no lugar de `python`. |
| Erro ao abrir `requirements.txt` | Usar `pip install -r requirements.txt` (com `-r` e espaço). |
| Porta 5000 ocupada | Fechar outro programa que use a porta ou alterar a porta em `run.py` (argumento `port=` em `app.run`). |
| API retorna erro vazio / 500 | Rodar de novo `python setup_database.py` e conferir se `instance\app.db` existe. |
| PowerShell não ativa `.venv` | Ajustar `ExecutionPolicy` (seção 11.2). |
| Cadastro retorna `409` | E-mail ou código já existe no banco — escolha outro valor. |
| Cadastro retorna `400` | Campo obrigatório vazio ou `professor_id` / `turma_id` inválido. |

---

## Resumo em uma frase

**Instale dependências → rode `setup_database.py` → rode `run.py` → abra `http://127.0.0.1:5000/` e cadastre Professor, Turma e Aluno pela UI.**

Bons estudos.
