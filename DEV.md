# DEV.md — Indes Portal (ambiente local)

Guia do ambiente de desenvolvimento local do **Indes Portal**, o antigo
"ONG Course Platform" com a identidade visual do INDES (indes.org.br).

Este documento descreve **apenas a execução local**. A produção continua usando
PostgreSQL, Gunicorn e Docker (`ong_platform/settings.py` não foi alterado).

---

## O que é esta build

- Base: branch `Indes_Prod` (commit `0c6c0c5`) do checkout existente
  `Site/CourseApp`, clonado para `Indes/indes-portal`.
- Branch de trabalho: **`feature/indes-portal-ui`**.
- O objetivo é uma build **local-first**: SQLite, sem Docker, servidor de
  desenvolvimento do Django na porta **9000**, com dados de demonstração em
  pt-BR e a identidade visual do INDES aplicada.
- Nenhum app, model, view, URL ou migration foi removido. Rotas de loja
  (`/courses/acquire/`, `/cart/`, `/checkout/`) continuam funcionando, mas não
  aparecem na navegação.

---

## Pré-requisitos

| Item | Versão usada | Observação |
| --- | --- | --- |
| Windows + PowerShell | 5.1 | comandos abaixo são para PowerShell |
| Python | 3.11.0 (`python` no PATH) | `python --version` |
| Git | 2.49 | |
| Docker | **não é necessário** | o daemon pode estar parado |
| Banco | SQLite (arquivo `db.sqlite3`) | criado no primeiro `migrate` |
| Porta livre | **9000** | configurável em `run-dev.ps1 -Port` |

---

## Setup do zero (primeira vez)

```powershell
git clone <checkout-existente> C:\Users\User\Documents\Projetos\Indes\indes-portal
cd C:\Users\User\Documents\Projetos\Indes\indes-portal
git checkout feature/indes-portal-ui

python -m venv .venv
.venv\Scripts\python -m pip install --upgrade pip
.venv\Scripts\python -m pip install -r requirements.txt

Copy-Item .env.example .env      # depois ajuste os valores locais
.venv\Scripts\python manage.py migrate  --settings=ong_platform.settings_dev
.venv\Scripts\python manage.py seed_demo --settings=ong_platform.settings_dev
```

O `.env` deste checkout já vem preenchido para desenvolvimento (chave descartável,
backend de e-mail no console) e **está no `.gitignore`** — nunca commitar.

---

## Como rodar

```powershell
.\run-dev.ps1
```

O script:

1. entra na raiz do repositório;
2. usa `.venv\Scripts\python.exe` (cria o venv e instala as dependências se
   ainda não existirem);
3. avisa se faltar `.env` ou `db.sqlite3`;
4. sobe o servidor com `--settings=ong_platform.settings_dev`.

Equivalente manual:

```powershell
.venv\Scripts\python manage.py runserver 0.0.0.0:9000 --settings=ong_platform.settings_dev
```

Acesse **http://localhost:9000/** (ou `http://127.0.0.1:9000/`).

Outras portas / recarga automática:

```powershell
.\run-dev.ps1 -Port 9100
.\run-dev.ps1 -NoReload
```

---

## Credenciais de demonstração (somente dev)

| Papel | E-mail | Senha |
| --- | --- | --- |
| Administrador (superuser, `/admin/`) | `admin@indes.dev` | `indesdev2026` |
| Professor | `professor@indes.dev` | `indesdev2026` |
| Aluno (vê "Minhas aulas" e "Classes") | `aluno@indes.dev` | `indesdev2026` |
| Aluna | `beatriz@indes.dev` | `indesdev2026` |
| Aluno | `carlos@indes.dev` | `indesdev2026` |

> Essas contas existem **apenas** no banco SQLite local. Não são criadas em
> produção e a senha é pública de propósito.

---

## Dados de demonstração (`seed_demo`)

O comando é **idempotente** (`get_or_create`; rodar de novo não duplica nada) e
imprime um resumo do que criou.

| Item | Quantidade |
| --- | --- |
| Usuários | 1 admin + 1 professor + 3 alunos |
| Organizações (orgs) | 2 — "Associação Inclusão para Todos", "Instituto Semear" |
| Cursos | 3 — Inclusão Escolar na Prática; Comunicação Alternativa e Acessibilidade; Autonomia e Vida Independente |
| Módulos | 6 (2 por curso, publicados) |
| Aulas | 12 (2 aulas com vídeo do YouTube; as demais com texto em HTML pt-BR) |
| Turmas (Classes) | 6 — 2 por curso ("Turma Manhã" e "Turma Noite") |
| Matrículas | 4 (+1 do admin) — `aluno@indes.dev` vê 2 cursos |
| Chamada aberta | 1 — na turma da manhã do primeiro curso (permite testar presença) |

Por que não `loaddata data.json`: o fixture da raiz está em **UTF-16** e cita
modelos que não existem mais (`checkout.order`), então `loaddata` falha nas duas
etapas. O `seed_demo` foi escrito para o schema atual.

---

## Settings de desenvolvimento

`ong_platform/settings_dev.py` faz `from .settings import *` e sobrescreve
somente:

| Setting | Valor local | Motivo |
| --- | --- | --- |
| `DATABASES` | SQLite em `BASE_DIR / 'db.sqlite3'` | sem Docker/Postgres |
| `DEBUG` | `True` | arquivos estáticos e tracebacks |
| `ALLOWED_HOSTS` | `localhost`, `127.0.0.1`, `[::1]`, `testserver` | a lista de produção contém entradas como `http://127.0.0.1:9000`, que nunca casam (Django compara sem a porta) |
| `EMAIL_BACKEND` | console | e-mails aparecem no terminal |
| `CSRF_TRUSTED_ORIGINS` | `localhost:9000`, `127.0.0.1:9000` | login/forms locais |

Herdados sem alteração: `STATIC_URL` (`/static/`), `MEDIA_URL`/`MEDIA_ROOT`,
`LANGUAGE_CODE = 'pt-br'`, `TIME_ZONE = 'America/Sao_Paulo'`, `AUTH_USER_MODEL`,
apps, middleware, templates.

**Produção continua em PostgreSQL**: `settings.py` não foi modificado.

---

## Identidade visual aplicada

Tokens extraídos do kit Elementor de indes.org.br.

### Cores

| Token | Valor | Uso |
| --- | --- | --- |
| `--indes-purple` | `#310051` | primária: botões, links, nav ativa |
| `--indes-purple-deep` | `#24003C` | fundo da sidebar |
| `--indes-purple-dark` | `#461963` | tom escuro |
| `--indes-purple-light` | `#672B8D` | tom claro / hover |
| `--indes-navy` | `#2E227A` | acento navy-purple |
| `--indes-slate` | `#34365A` | acento neutro |
| `--indes-cyan` | `#4CC9F0` | destaque (ícones, sufixo "Portal") |
| `--indes-pink` | `#FF50A0` | destaque |
| `--indes-heading` | `#222222` | títulos |
| `--indes-body` | `#000000` | texto sobre branco |
| `--indes-gray-800` | `#2B2B2B` | apoio |
| `--indes-gray-600` | `#474747` | apoio |
| `--indes-surface` | `#FFFFFF` | fundo de página e cards |
| `--indes-tint` | `#F5F2F8` | separação sutil de seções |

### Tipografia (Google Fonts)

| Uso | Fonte | Pesos |
| --- | --- | --- |
| Títulos | **Poppins** | 400/500/600/700 |
| Corpo | **Lato** | 400/500/700 |
| Botões/CTAs | **Nunito** | 700/800 |

`Inter` e `Sora` foram removidos.

### Forma e layout

| Item | Valor |
| --- | --- |
| Botões | pill, `border-radius: 50px`; `#310051` + texto branco; hover inverte (fundo branco, texto `#310051`, borda roxa) |
| Cards | raio 20px, borda `#E8E1F0`, sombra suave `rgba(49,0,81,.06)` |
| Container de conteúdo | `max-width: 1140px` |
| Sidebar | 280px fixa, gradiente `#310051 → #24003C` |
| Nav ativa | pill branca com texto `#310051` (contraste; a alternativa "pill roxa em fundo roxo" ficaria ilegível) |
| Inputs | raio 14px, foco `#310051` + anel `rgba(49,0,81,.10)` |
| Quebra responsiva | 1024px (padding) e 768px (sidebar vira drawer com hamburger) |

Variáveis antigas (`--primary-purple`, `--primary-blue`, `--primary-orange`,
`--radius-full`, `--bg-dark`, `--text-gray`, …) foram mantidas como **aliases**
para os tokens novos, porque vários templates usam `style="...var(--x)"` inline.

### Assets (offline, em `core/static/core/img/`)

| Arquivo | Origem | Uso |
| --- | --- | --- |
| `indes-logo.png` (479×130) | `text4943.png` do site | login/auth, cards brancos |
| `indes-logo-compact.png` (150×41) | `cropped-text.png` | reserva/uso compacto |
| `indes-logo-light.png` (479×130) | **derivado**: mesma marca, recolorida em branco via Pillow | sidebar roxa |
| `favicon-192x192.png` | `cropped-favicon-192x192.png` | favicon / apple-touch-icon |

Decisão de logo: a marca oficial é azul-violeta (`#5147DE`), com contraste
**2,65:1** contra `#310051` — ruim para a sidebar. Por isso a sidebar usa a
versão branca derivada (contraste **16,81:1**, mesma silhueta oficial) e o
logo colorido original aparece nas telas de autenticação sobre cartão branco
(contraste **6,35:1**).

---

## Informação e navegação

- Título do produto: **Indes Portal**; padrão de `<title>`:
  `Indes Portal — <seção>` (ex.: `Indes Portal — Classes`).
- Sidebar: **Início**, **Minhas aulas** (`courses`/aulas), **Classes**
  (`courses.Turma`), **Minha conta**. Carrinho/checkout/adquirir ficam fora do
  menu (rotas preservadas).
- `/admin/` segue funcionando e ganhou cabeçalho roxo via
  `templates/admin/base_site.html` (override de templates, sem tocar no app do
  Django). O admin respeita o tema claro/escuro do sistema operacional.

---

## Verificação executada

`python manage.py check --settings=ong_platform.settings_dev` → *System check
identified no issues (0 silenced).*

Requisições HTTP reais contra `http://127.0.0.1:9000`:

| Endpoint | Status | Evidência |
| --- | --- | --- |
| `/login/` (anônimo) | 200 | HTML contém `Indes Portal`, fontes Poppins/Lato/Nunito |
| `/` (anônimo) | 302 | `Location: /login/?next=/` |
| `/static/core/css/main.css` | 200 | contém `#310051`, `border-radius: 50px` |
| `/static/core/img/indes-logo.png` etc. | 200 | PNG válido (assinatura `89504e47`) |
| `/admin/login/` | 200 | contém `Indes Portal` e `--primary: #310051` |
| `POST /login/` (aluno) | 200 | cookie `sessionid` criado, redireciona para `/` |
| `/` (logado) | 200 | nav `Início`, `Minhas aulas`, `Classes`, `Minha conta` |
| `/courses/my-courses/` | 200 | `Minhas aulas` + cursos matriculados |
| `/courses/turmas/` | 200 | `Classes` + 6 turmas |
| `/courses/turmas/1/` | 200 | `Chamada Aberta`, `Registrar Presença` |
| `/courses/turmas/2/` | 200 | estado vazio de presença |
| `/courses/1/` | 200 | `Módulo 1`, aulas listadas |
| `/courses/lesson/1/` | 200 | conteúdo da aula + `Marcar como Concluída` |
| `/courses/lesson/3/` | 200 | `youtube.com/embed/...` |
| `/account/` | 200 | formulário de conta |
| `/healthcheck/` | 200 | `healthy` |
| `/courses/acquire/` | 200 | rota viva (fora do menu) |
| `/cart/` | 200 | rota viva (fora do menu) |
| `/admin/` (logado como admin) | 200 | dashboard + lista de cursos |

Layout conferido em Chrome headless (1366px e 500px): sem rolagem horizontal,
`main.css` com container de 1140px, sidebar 280px e drawer + hamburger abaixo de
768px.

---

## Pendências conhecidas / decisões para o time

1. **Bug de correção de quiz (pré-existente, fora do escopo).**
   `courses/views.py` compara `question.question_type` com `'MC'`, `'TF'` e
   `'SA'`, mas as choices do model são `multiple_choice`, `true_false`,
   `short_answer`. Nenhuma questão é pontuada. Não há quiz nos dados de demo.
2. **`course_detail.html` mostra "Módulo X"** com `forloop.counter`, não com o
   campo `order` — funciona, mas não reflete reordenação no admin.
3. **`Turma` não tem mais FK para `Course`** (migration `0004_remove_turma_course`),
   então o nome da turma embute o curso. Trechos antigos que liam
   `turma.course` foram ajustados em `turma_list.html`; outros templates ainda
   têm `{% if turma.course %}` (renderiza vazio, sem erro).
4. **Presença:** estilos inline de `turma_detail.html`/`presence_session_detail.html`
   usam `rgba(255,255,255,...)` (herança de tema escuro) e ficam quase
   invisíveis em cards brancos. Funcional, cosmético.
5. **Vídeo:** o `<iframe>` usa `lesson.video_url` direto; só funciona com URL de
   *embed* (`/embed/…`). URLs `watch?v=` precisariam de conversão (o campo
   `embed_video_url` só trata Google Drive).
6. **Loja desativada na UI:** `/courses/acquire/`, `/cart/`, `/checkout/` exigem
   chaves Stripe para pagamento real. Com `.env` vazio, o fluxo para antes do
   pagamento.
7. **E-mail:** com o backend de console, códigos de verificação/recuperação
   aparecem no terminal — não há envio real sem `RESEND_API_KEY`.
8. **`data.json`** na raiz segue no repositório (UTF-16, schema antigo). Não é
   usado por esta build; pode ser removido em outro PR.
9. **`.env.example`** continha valores reais de `RESEND_API_KEY` e chaves Stripe
   (`pk_test_…`, `sk_test_…`) e marcadores de conflito de merge. Neste checkout
   foi reescrito sem segredos; **o repositório de origem e o histórico do Git
   ainda contêm os valores** — recomenda-se rotacionar essas chaves.
   `README.md` documenta senhas-exemplo (`password='admin123'`), sem impacto real.
10. **`DEBUG=True` e a `SECRET_KEY` descartável** são só para dev; `settings.py`
    (produção, PostgreSQL) permanece intacto.
11. **Porta 9000**: fixa no `run-dev.ps1`, em `CSRF_TRUSTED_ORIGINS` do
    `settings_dev` e na lista de `ALLOWED_HOSTS` local. Para outra porta, use
    `-Port` e ajuste `CSRF_TRUSTED_ORIGINS` se necessário.
12. **Sem testes automatizados** de UI nesta entrega; a verificação foi por
    requisições HTTP reais + screenshots em Chrome headless.