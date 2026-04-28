# SymbolicThought

## Paper

This repository accompanies the ACL 2026 Demo paper:

**SymbolicThought: Integrating Language Models and Symbolic Reasoning for Consistent and Interpretable Human Relationship Understanding**

A screencast\footnote{\url{https://www.youtube.com/watch?v=nb10-bDCkRU}} and demo\footnote{\url{http://104.168.96.23:3000/}} are available online.

Citation format:

```bibtex
@inproceedings{symbolicthought-2026-demo,
  title = {SymbolicThought: Integrating Language Models and Symbolic Reasoning for Consistent and Interpretable Human Relationship Understanding},
  booktitle = {Proceedings of the 64th Annual Meeting of the Association for Computational Linguistics: System Demonstrations},
  year = {2026}
}
```

This folder keeps only the code and data needed to run the local web app:

- `api/`: Flask backend on `http://localhost:5003`
- `frontend/`: React frontend on `http://localhost:3000`
- `api/data/stories/`: default story and metadata templates
- `api/data/upload/`: empty runtime upload/session workspace

Removed from the original project:

- `frontend/node_modules/`
- `frontend/build/`
- Flask session/cache files
- Python cache and local dependency folders
- old uploaded user data
- experiment scripts, old result files, notebooks, and unused data graphs
- real `api/.env`

## Backend

```bash
cd api
cp .envformat .env
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python main.py
```

Fill `api/.env` with Azure OpenAI values before using LLM-backed extraction:

```bash
AZURE_OPENAI_API_KEY="..."
AZURE_OPENAI_API_VERSION="2025-04-01-preview"
AZURE_OPENAI_ENDPOINT="https://<your-resource>.openai.azure.com/"
AZURE_OPENAI_CHAT_DEPLOYMENT="<chat-deployment-name>"
AZURE_OPENAI_EMBEDDING_DEPLOYMENT="<embedding-deployment-name>"
```

## Frontend

In another terminal:

```bash
cd frontend
npm install
npm start
```

The frontend proxies `/apilocal/*` to the backend through `frontend/src/setupProxy.js`.
