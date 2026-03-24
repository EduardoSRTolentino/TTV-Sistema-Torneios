# TTV-Torneios

Plataforma web (SaaS) para inscrição e gestão de torneios de tênis de mesa — **FastAPI + React (Vite) + MySQL**.

## FASE 1 — MVP (local)

### Arquitetura simplificada

- **Backend**: API REST FastAPI, SQLAlchemy 2, JWT + bcrypt, geração de mata-mata em serviço dedicado.
- **Frontend**: SPA React com rotas, proxy `/api` → backend, armazenamento do token em `localStorage`.
- **Banco**: MySQL 8 (Docker recomendado).

### Estrutura de pastas

```
TTV-Sistem/
  backend/app/          # API, modelos, routers, services
  frontend/src/         # Páginas, API client, estilos
  docker-compose.yml    # MySQL dev
  docker-compose.prod.yml  # Exemplo de stack (opcional)
```

### Modelagem mínima (MySQL)

- `users` — papéis: `admin`, `organizer`, `player`
- `tournaments` — formato de jogo, status, prazo, limite
- `tournament_registrations` — individual ou dupla (`partner_user_id`)
- `bracket_matches` — mata-mata com `next_match_id`

### Como rodar localmente

1. **Subir o MySQL**

   ```bash
   docker compose up -d
   ```

2. **Backend** (na pasta `backend`)

   ```bash
   cp .env.example .env
   pip install -r requirements.txt
   python -m app.seed
   uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
   ```

3. **Frontend** (na pasta `frontend`)

   ```bash
   npm install
   npm run dev
   ```

4. Acesse `http://localhost:5173`. Credenciais de seed: `admin@ttv.local` / `admin123`.

5. **Fluxo sugerido**: login como admin → `POST /users` (Swagger em `/docs`) para criar um **organizador** → login como organizador → criar torneio na UI → cadastrar jogadores (registro) → inscrições → fechar inscrições → gerar chaveamento.

---

## FASE 2 — Produção (evolução incluída no repositório)

- **OAuth Google**: `/auth/google/start` e `/auth/google/callback` (configure `GOOGLE_*` e redirect URI no Google Cloud).
- **Pagamentos**: `POST /payments/torneios/{id}` (multipart: `amount_cents` + comprovante); confirmação: `POST /payments/{id}/confirmar`.
- **Denúncias**: `POST /reports`.
- **Ranking ELO**: `GET /ranking`; serviço `elo_service.py` para atualização por partida.
- **Auditoria**: `GET /admin/logs` (admin).
- **Repositórios**: `repositories/user_repository.py` (extensível).
- **Testes**: `pytest` em `backend/tests/` (usa SQLite de teste via `conftest.py`).
- **Docker**: `backend/Dockerfile`, `frontend/Dockerfile`, `docker-compose.prod.yml`.

### Variáveis úteis (`.env` backend)

Ver `backend/.env.example`. Para OAuth, defina `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `OAUTH_REDIRECT_URI` (URL do **backend**, ex.: `http://127.0.0.1:8000/auth/google/callback`) e `FRONTEND_URL` para o redirect final com `?token=`.

### Documentação interativa

Com o backend no ar: `http://127.0.0.1:8000/docs`
