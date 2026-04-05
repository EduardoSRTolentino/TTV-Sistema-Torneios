# TTV-Torneios

Plataforma web para **inscrição e gestão de torneios de tênis de mesa**: torneios individuais ou em dupla, inscrições com limite e prazo, geração de **mata-mata** e evolução para **OAuth**, pagamentos, ranking **ELO** e API documentada.

---

## Sumário

- [Funcionalidades](#-funcionalidades)
- [Stack](#-stack)
- [Pré-requisitos](#-pré-requisitos)
- [Instalação e execução local](#-instalação-e-execução-local)
- [Variáveis de ambiente](#-variáveis-de-ambiente)
- [Documentação da API](#-documentação-da-api)
- [Testes](#-testes)
- [Docker](#-docker)
- [Estrutura do repositório](#-estrutura-do-repositório)
- [Segurança](#-segurança)
- [Licença](#-licença)

---

## Funcionalidades

| Área | Descrição |
|------|-----------|
| **Usuários** | Papéis `admin`, `organizer` e `player` com controle de acesso (RBAC) |
| **Torneios** | CRUD, status (rascunho, inscrições, fechamento, andamento), individual/duplas |
| **Inscrições** | Automáticas (sem aprovação manual), limite de vagas e prazo |
| **Chaveamento** | Mata-mata com byes e encadeamento de partidas |
| **Extras (evolução)** | OAuth Google, pagamentos com comprovante, denúncias, ranking ELO, logs administrativos |

Interface em **português**, **responsiva** (desktop e mobile), estilo inspirado em eSports (sem dark mode).

---

## Stack

| Camada | Tecnologia |
|--------|------------|
| Backend | [FastAPI](https://fastapi.tiangolo.com/), SQLAlchemy 2, PyMySQL |
| Frontend | [React](https://react.dev/) 18, [Vite](https://vitejs.dev/), TypeScript |
| Banco | [MySQL](https://www.mysql.com/) 8 |
| Auth | JWT (senha com bcrypt) + OAuth Google (opcional) |

---

## Pré-requisitos

- **Python** 3.11+ (recomendado 3.12)
- **Node.js** 20+ e npm
- **Docker** (opcional, para MySQL em desenvolvimento)
- **Git**

---

## Instalação e execução local

### 1. Clonar o repositório

```bash
git clone https://github.com/EduardoSRTolentino/TTV-Sistema-Torneios.git
cd TTV-Sistem
```

### 2. Banco de dados (MySQL)

Na raiz do projeto:

```bash
docker compose up -d
```

Isso sobe o MySQL na porta **3306** (usuário/senha padrão alinhados ao `backend/.env.example`).

### 3. Backend

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate
# Linux / macOS
# source venv/bin/activate

cp .env.example .env
pip install -r requirements.txt
python -m app.seed
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

- API: `http://127.0.0.1:8000`
- Health: `GET /health`
- Usuário inicial (seed): `admin@ttv.com` / `Admin123!` — **altere em produção**

### 4. Frontend

Em outro terminal:

```bash
cd frontend
npm install
npm run dev
```

- Aplicação: `http://localhost:5173` (proxy `/api` → backend)

### 5. Primeiro uso sugerido

1. Entrar como **admin** (credenciais do seed).
2. Criar um **organizador** via `POST /users` em [`/docs`](http://127.0.0.1:8000/docs) (autenticado).
3. Entrar como organizador e usar **Novo torneio** na interface.

---

## Variáveis de ambiente

Copie `backend/.env.example` para `backend/.env` e ajuste.

| Variável | Descrição |
|----------|-----------|
| `DATABASE_URL` | URL SQLAlchemy (ex.: `mysql+pymysql://user:pass@host:3306/db`) |
| `SECRET_KEY` | Chave para JWT e sessão OAuth — **obrigatória e secreta em produção** |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Validade do token (padrão 1440) |
| `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` | OAuth Google (opcional) |
| `OAUTH_REDIRECT_URI` | URL do **backend** no fluxo OAuth (ex.: `http://127.0.0.1:8000/auth/google/callback`) |
| `FRONTEND_URL` | URL do front para redirect pós-login OAuth (ex.: `http://localhost:5173`) |

No frontend, para **“Entrar com Google”**, defina `VITE_API_ORIGIN` (ex.: `http://127.0.0.1:8000`) — ver `frontend/.env.development`.

---

## Documentação da API

Com o backend em execução:

- **Swagger UI:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **OpenAPI JSON:** [http://127.0.0.1:8000/openapi.json](http://127.0.0.1:8000/openapi.json)

---

## Testes

```bash
cd backend
pytest tests/ -q
```

Os testes de health usam SQLite via `tests/conftest.py` (não exigem MySQL).

---

## Docker

- **Desenvolvimento:** `docker-compose.yml` — MySQL, backend e frontend com **bind mount** do código (`./backend` → `/app`, `./frontend` → `/app`). Imagens usam `Dockerfile.dev` (só dependências); hot reload: `uvicorn --reload` e Vite dev server. API em `http://localhost:8000`, front em `http://localhost:5173`. Requer rede externa `proxy_network` se você a usar no compose; caso contrário, remova-a do arquivo.
- **Referência de deploy:** `docker-compose.prod.yml` — imagem com código copiado (`Dockerfile`).

Imagens: dev — `backend/Dockerfile.dev`, `frontend/Dockerfile.dev`; produção — `backend/Dockerfile`, `frontend/Dockerfile`.

---

## Estrutura do repositório

```
TTV-Sistem/
├── backend/
│   ├── app/                 # API FastAPI (routers, models, services)
│   ├── tests/               # Pytest
│   ├── requirements.txt
│   ├── Dockerfile
│   └── Dockerfile.dev
├── frontend/
│   ├── src/
│   ├── package.json
│   ├── Dockerfile
│   └── Dockerfile.dev
├── docker-compose.yml
├── docker-compose.prod.yml
└── README.md
```

---

## Segurança

- Não commite `.env`; use apenas `.env.example` como modelo.
- Troque `SECRET_KEY` e credenciais padrão antes de qualquer deploy público.
- Em produção: HTTPS, revisão de CORS, limites de upload e políticas de senha/OAuth conforme o seu ambiente.

---

## Licença

Este projeto não define licença automaticamente. Escolha uma licença (por exemplo MIT, Apache-2.0) e adicione um arquivo `LICENSE` no repositório.

---

**TTV-Torneios** — plataforma de torneios de tênis de mesa.
