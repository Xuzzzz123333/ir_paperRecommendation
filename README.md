# Paper Recommender Demo

面向科研主题的论文自动检索与结构化摘要系统。

这是一个适合信息检索课程 HW3 展示的前后端分离 demo。用户输入研究主题、关键词或自然语言问题后，系统会自动从开放学术数据源检索候选论文，随后执行混合排序与结构化摘要分析，并在网页中展示推荐结果。

## Project Highlights

- Automatic academic paper retrieval from external sources instead of manual PDF upload
- Hybrid ranking with BM25 and Sentence-Transformers dense similarity
- Structured abstract analysis without calling large language models
- FastAPI backend with Swagger docs and REST API
- React + Vite + TypeScript frontend for demo-style presentation
- SQLite-based local metadata cache, no heavy database dependency

## Why This Is an IR System

这个项目符合信息检索系统的典型流程：

1. 用户输入查询主题
2. 系统从学术数据源召回候选论文
3. 对候选论文做文本处理与去重
4. 使用 BM25 进行关键词相关性建模
5. 使用 Sentence-Transformers 进行语义向量相似度建模
6. 使用混合打分完成排序
7. 输出结构化推荐理由与论文摘要分析

混合排序核心公式：

```text
final_score = alpha * dense_score + (1 - alpha) * bm25_score
```

## System Architecture

```text
paper-recommender-demo/
├── backend/      FastAPI + source APIs + ranking + cache
├── frontend/     React + Vite + TypeScript demo UI
└── docs/         Pipeline diagram and supporting docs
```

系统流程图见 [docs/system_pipeline.md](docs/system_pipeline.md)。

## Tech Stack

### Backend

- Python
- FastAPI
- httpx
- sentence-transformers
- rank-bm25
- numpy
- pandas
- pydantic
- uvicorn
- SQLite

### Frontend

- React
- Vite
- TypeScript
- CSS

## Supported Features

- Query-based academic paper retrieval
- Source selection: `arxiv`, `openalex`, `semantic_scholar`
- Optional filters: `max_results`, `alpha`, `year_from`, `year_to`, `sort_by`
- Candidate paper ranking with dense + sparse hybrid scoring
- Structured fields:
  - research problem
  - core method
  - main contribution
  - experimental evidence
  - limitations
  - recommendation reason

## Quick Start

### Backend

```bash
cd backend
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Swagger:

- `http://localhost:8000/docs`
- `http://localhost:8000/redoc`

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend default URL:

- `http://localhost:5173`

Backend default URL:

- `http://localhost:8000`

## API Overview

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `GET` | `/api/health` | Health check |
| `GET` | `/api/sources` | List supported sources |
| `POST` | `/api/papers/search` | Retrieve candidate papers |
| `POST` | `/api/papers/recommend` | Rank and recommend papers |
| `POST` | `/api/papers/analyze` | Analyze one paper into structured fields |
| `DELETE` | `/api/cache` | Clear local paper cache |

## API Examples

### Health Check

```bash
curl http://localhost:8000/api/health
```

### Search Candidate Papers

```bash
curl -X POST http://localhost:8000/api/papers/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "remote sensing change detection DINOv2",
    "max_results": 10,
    "source": "arxiv",
    "sort_by": "relevance"
  }'
```

### Recommend Papers

```bash
curl -X POST http://localhost:8000/api/papers/recommend \
  -H "Content-Type: application/json" \
  -d '{
    "query": "retrieval augmented generation reranking",
    "max_results": 10,
    "source": "arxiv",
    "alpha": 0.65,
    "sort_by": "relevance"
  }'
```

### Analyze One Paper

```bash
curl -X POST http://localhost:8000/api/papers/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "query": "semantic search for scientific papers",
    "paper": {
      "title": "Example Paper",
      "authors": ["Alice", "Bob"],
      "abstract": "This paper studies semantic search for scientific papers. We propose a hybrid retriever and show improvements on benchmark datasets.",
      "year": 2024,
      "venue": "arXiv",
      "source": "arxiv",
      "url": "https://arxiv.org/abs/1234.5678",
      "pdf_url": "https://arxiv.org/pdf/1234.5678.pdf",
      "citation_count": 12
    }
  }'
```

### Clear Cache

```bash
curl -X DELETE http://localhost:8000/api/cache
```

## Demo Flow

1. Start the backend and open Swagger.
2. Start the frontend.
3. Enter a topic such as `DINOv2 for remote sensing change detection`.
4. Select a data source and ranking parameters.
5. Click `搜索并推荐论文`.
6. Review ranking scores in the table.
7. Open the paper cards to inspect recommendation reasons and structured summaries.

## Recommended Screenshot Positions For HW3 Report

- Homepage title + search area
- Parameter panel
- Recommendation result table
- Structured paper card section
- Swagger page for `/api/papers/recommend`
- Mermaid pipeline diagram in `docs/system_pipeline.md`

## Current Limitations

- arXiv may occasionally rate-limit or timeout on repeated requests; the backend now retries and returns clearer timeout messages
- OpenAlex and Semantic Scholar are supported, but their field completeness depends on upstream APIs
- Structured summaries are extractive and rule-based, so they are more stable than generated summaries but less expressive
- Citation-based sorting is limited for arXiv because citation counts are often unavailable
- The first dense retrieval request may be slower because the embedding model needs to be loaded

## Repository Notes

- No OpenAI API
- No LangChain
- No LlamaIndex
- No heavy database
- No user login system

这个仓库适合继续扩展为课程报告中的“方案设计”和“技术路线”部分。
