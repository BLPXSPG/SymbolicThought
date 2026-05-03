# SymbolicThought

## Paper

This repository accompanies the ACL 2026 Demo paper:

**SymbolicThought: Integrating Language Models and Symbolic Reasoning for Consistent and Interpretable Human Relationship Understanding**

Paper links: [arXiv](https://arxiv.org/abs/2507.04189) | ACL Anthology (forthcoming).

A [screencast](https://www.youtube.com/watch?v=nb10-bDCkRU) and [online demo](http://104.168.96.23:3000/) are available.

```bibtex
@inproceedings{symbolicthought-2026-demo,
  author = {Runcong Zhao and Qinglin Zhu and Hainiu Xu and Bin Liang and Lin Gui and Yulan He},
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



## Related Works

SymbolicThought continues a line of work on narrative understanding, character relationship extraction, social reasoning, and interactive LLM-based systems.

### Conan: Understanding Complex Relationships in Detective Narratives

[Conan](https://aclanthology.org/2024.findings-acl.454/) is our ACL 2024 Findings benchmark for extracting and analysing intricate character relation graphs from detective narratives. It introduces hierarchical relationship categories and role-oriented annotations from different character perspectives, including both public and secret relationships.

- Paper: [ACL Anthology](https://aclanthology.org/2024.findings-acl.454/)
- PDF: [2024.findings-acl.454.pdf](https://aclanthology.org/2024.findings-acl.454.pdf)
- Code: [BLPXSPG/Conan](https://github.com/BLPXSPG/Conan)
```bibtex
@inproceedings{zhao-etal-2024-large,
  title = {Large Language Models Fall Short: Understanding Complex Relationships in Detective Narratives},
  author = {Zhao, Runcong and Zhu, Qinglin and Xu, Hainiu and Li, Jiazheng and Zhou, Yuxiang and He, Yulan and Gui, Lin},
  booktitle = {Findings of the Association for Computational Linguistics: ACL 2024},
  pages = {7618--7638},
  year = {2024},
  address = {Bangkok, Thailand},
  publisher = {Association for Computational Linguistics},
  doi = {10.18653/v1/2024.findings-acl.454},
  url = {https://aclanthology.org/2024.findings-acl.454/}
}
```
### PLAYER*: Enhancing LLM-based Multi-Agent Communication and Interaction in Murder Mystery Games

[PLAYER*](https://arxiv.org/abs/2404.17662) extends this research direction from detective narrative relationship understanding to multi-agent murder mystery games. It introduces **WellPlay**, a reasoning dataset for multi-agent conversational inference, and studies how LLM-based agents communicate, ask questions, infer objectives, and reason about hidden social relationships in complex game settings.

- Paper: [arXiv:2404.17662](https://arxiv.org/abs/2404.17662)
- PDF: [2404.17662.pdf](https://arxiv.org/pdf/2404.17662)
- Code: [alickzhu/PLAYER](https://github.com/alickzhu/PLAYER)
```bibtex
@misc{zhu2024player,
  title = {{PLAYER}*: Enhancing LLM-based Multi-Agent Communication and Interaction in Murder Mystery Games},
  author = {Zhu, Qinglin and Zhao, Runcong and Liang, Bin and Du, Jinhua and Gui, Lin and He, Yulan},
  year = {2024},
  eprint = {2404.17662},
  archivePrefix = {arXiv},
  primaryClass = {cs.CL},
  doi = {10.48550/arXiv.2404.17662},
  url = {https://arxiv.org/abs/2404.17662}
}
```
