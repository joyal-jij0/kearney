# Kearney Data Chat

Turn your CSV and Excel workbooks into chat-ready knowledge bases. This project ingests structured files, stores them in SQLite, and equips a large language model with safe, read-only tools so it can answer questions about the data with full schema awareness.

## Why Structured Data Needs a Staging Database

Raw spreadsheets are inconsistent: column names rarely follow SQL rules, sheets carry hidden metadata, and files can be too large for an LLM context window. The backend solves this by:

1. **Normalising uploads** – CSV/XLS/XLSX files are parsed with pandas, cleaned, and their column names are sanitised.
2. **Persisting to SQLite** – Every upload becomes a dedicated table inside `server/data/uploads.db`, giving us ACID guarantees and a consistent schema.
3. **Tool-enabling the model** – The LLM (served through OpenRouter) receives two function-calling tools:
   - `get_database_context`: returns every table, its columns, row counts, and optional samples in a single payload.
   - `execute_select_query`: allows strictly read-only SQL so the assistant can answer questions without mutating data.
4. **Conversational analytics** – A React + Tailwind client (built with Bun) lets users upload a file, then chat with the dataset in plain English.

The result is a deterministic pipeline that keeps the model grounded in up-to-date, queryable data while preventing destructive SQL.

## Repository Layout

- `client/` – Bun-based React SPA with a drag-and-drop uploader and chat UI.
- `server/` – FastAPI application exposing file upload and AI chat endpoints.
- `server/app/services/` – Data loaders, SQLite tool implementations, and OpenRouter integration.
- `server/app/prompts/` – The system prompt that primes the model as a database analyst.
- `server/data/` – Default location for the generated SQLite database.
- `docker-compose.yml` – Optional containerised setup for bundling client + server.

## Prerequisites

| Tool                             | Purpose                                     | Minimum Version | Required For         |
| -------------------------------- | ------------------------------------------- | --------------- | -------------------- |
| Git                              | clone and version control                   | latest          | everyone             |
| Docker Desktop / Engine          | container runtime & Compose                 | latest          | preferred quickstart |
| Python                           | backend runtime                             | 3.11            | manual setup only    |
| [uv](https://docs.astral.sh/uv/) | Python package & environment manager        | 0.4+            | manual setup only    |
| [Bun](https://bun.sh/)           | JS runtime + package manager for the client | 1.1+            | manual setup only    |

## Install uv

> uv installs into `~/.local/bin` (macOS/Linux) or `%LOCALAPPDATA%\Programs\uv\` (Windows). Make sure that directory lives on your `PATH`.

**macOS / Linux**

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
uv --version
```

**Windows (PowerShell)**

```powershell
powershell -ExecutionPolicy Bypass -Command "irm https://astral.sh/uv/install.ps1 | iex"
uv --version
```

## Install Bun

**macOS / Linux**

```bash
curl -fsSL https://bun.sh/install | bash
bun --version
```

**Windows (PowerShell)**

```powershell
powershell -ExecutionPolicy Bypass -Command "irm https://bun.sh/install.ps1 | iex"
bun --version
```

## Install Docker

- **macOS**: `brew install --cask docker`, then launch Docker Desktop once so it can finish setup.
- **Windows**: Install [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop/) and enable the WSL 2 backend during setup.
- **Linux**: Follow the [Docker Engine installation guide](https://docs.docker.com/engine/install/) for your distribution, then install Compose v2 (`sudo apt-get install docker-compose-plugin` on Ubuntu).

Verify the installation with:

```bash
docker --version
docker compose version
```

## Clone the Repository

```bash
git clone https://github.com/joyal-jij0/kearney.git
cd kearney
```

## Quickstart with Docker Compose (Recommended)

1. **Set up environment variables**

   ```bash
   cp server/.env.example server/.env # if the example exists
   ```

   If `server/.env.example` is not present, create `server/.env` manually:

   ```ini
   OPENROUTER_API_KEY=sk-or-...
   OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
   MODEL_NAME=openai/gpt-4o-mini
   APP_NAME=DataAnalysisAPI
   DATABASE_PATH=data/uploads.db
   ```

2. **Launch the stack**

   ```bash
   docker compose up -d
   ```

   - Client UI: `http://localhost:3000`
   - FastAPI docs: `http://localhost:8000/docs`
   - Health check: `http://localhost:8000/health`

3. **Watch logs (optional)**

   ```bash
   docker compose logs -f server
   docker compose logs -f client
   ```

4. **Shut everything down**

   ```bash
   docker compose down
   ```

The compose file mounts your local `client/src` and `server/app` directories for hot reloading. Uploaded datasets persist inside `server/data/uploads.db` on your host machine.

## Manual Development Setup (Without Docker)

If you prefer to run the services directly on your machine, follow these steps.

### Backend (FastAPI + SQLite + OpenRouter)

1. **Enter the backend folder**

   ```bash
   cd server
   ```

2. **Create and populate the virtual environment**

   ```bash
   uv sync
   ```

   `uv sync` reads `pyproject.toml`, creates `.venv`, and installs all declared dependencies.

3. **Activate the environment**

   - macOS/Linux:
     ```bash
     source .venv/bin/activate
     ```
   - Windows (PowerShell):
     ```powershell
     .venv\Scripts\Activate.ps1
     ```

4. **Configure environment variables**

   Create `server/.env` with your OpenRouter credentials and optional overrides (same values shown above).

5. **Run the API**

   ```bash
   uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

   - Docs: `http://localhost:8000/docs`
   - Health check: `http://localhost:8000/health`

The `file_upload` endpoint writes every dataset into SQLite. The `ai_chat` endpoint delegates to `AIService`, which orchestrates OpenRouter function calls and safely executes read-only SQL through the tool layer.

### Frontend (Bun + React)

1. **Enter the client folder**

   ```bash
   cd ../client
   ```

2. **Install dependencies**

   ```bash
   bun install
   ```

3. **Start the development server**

   ```bash
   bun run dev
   ```

   By default the client serves on `http://localhost:3000` and proxies requests to the FastAPI service at `http://localhost:8000` as configured in `src/api/api.ts`.

4. **Build for production (optional)**

   ```bash
   bun run build
   ```

With those pieces in place you have a full-stack, reproducible workflow for letting an LLM analyse spreadsheet data safely and transparently.
