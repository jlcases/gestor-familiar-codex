# Nido

Una aplicación de gestión familiar compartida con Svelte, FastAPI y SQLite.

## Arranque

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
uvicorn backend.main:app --reload --port 8000
```

En otra terminal:

```bash
cd frontend
npm install
npm run dev
```

La interfaz estará en `http://localhost:5173` y la API en `http://localhost:8000/docs`.

