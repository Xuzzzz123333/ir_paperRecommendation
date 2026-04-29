# 面向科研主题的论文自动检索与结构化摘要系统

## 项目简介

这是一个面向信息检索课程 HW3 demo 的前后端分离项目。用户输入研究主题、关键词或自然语言问题后，系统会自动从开放学术数据源检索候选论文，随后使用 BM25 与 Sentence-Transformers 做混合排序，并基于论文摘要抽取结构化推荐信息。

主流程不依赖用户手动上传 PDF，更接近“自动论文推荐与学术检索”场景。

## 系统架构

```text
paper-recommender-demo/
├── backend/      FastAPI + academic API integration + hybrid ranking + SQLite cache
├── frontend/     React + Vite + TypeScript demo UI
└── docs/         System pipeline diagram
```

更详细流程见 [docs/system_pipeline.md](docs/system_pipeline.md)。

## 为什么这是信息检索系统

- 它以用户查询为起点，对外部论文源执行候选召回。
- 它对候选论文执行文本预处理、BM25 关键词匹配和向量语义匹配。
- 它使用 `final_score = alpha * dense_score + (1 - alpha) * bm25_score` 进行混合排序。
- 它输出结构化推荐理由，提升结果可解释性，适合作为课程中的“检索 + 排序 + 结果组织”系统 demo。

## 后端启动方式

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

Swagger 文档：

- `http://localhost:8000/docs`
- `http://localhost:8000/redoc`

## 前端启动方式

```bash
cd frontend
npm install
npm run dev
```

默认前端访问地址通常为 `http://localhost:5173`，默认后端地址为 `http://localhost:8000`。

## API 调用示例

### 1. 健康检查

```bash
curl http://localhost:8000/api/health
```

### 2. 查询候选论文

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

### 3. 推荐排序论文

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

### 4. 分析单篇论文

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

### 5. 清空缓存

```bash
curl -X DELETE http://localhost:8000/api/cache
```

## Demo 演示步骤

1. 启动后端并访问 Swagger，确认 `/api/health` 正常。
2. 启动前端页面，输入一个研究主题，例如 `DINOv2 for remote sensing change detection`。
3. 选择数据源、`max_results`、`alpha`、年份区间和排序方式。
4. 点击“搜索并推荐论文”，观察表格中的排名分数。
5. 在下方结构化卡片里展示推荐理由、研究问题、方法、贡献、实验和局限性。
6. 录屏时可以同时展示 Swagger 请求结果、前端页面和流程图。

## 适合作业报告截图的位置

- 首页标题区与参数区：展示系统功能入口。
- 推荐结果表格：展示排序分数与检索结果。
- 单篇论文卡片：展示结构化摘要与推荐理由。
- Swagger `/api/papers/recommend` 页面：展示 API 化能力。
- `docs/system_pipeline.md` 流程图：展示技术路线。

## 当前限制

- 当前主打数据源是 arXiv；OpenAlex 和 Semantic Scholar 已预留接口，但实际可用性会受到外部 API 限流和字段完整度影响。
- 结构化摘要基于摘要句子抽取与规则匹配，不是生成式总结，因此更稳但表达可能偏模板化。
- 引用数在 arXiv 数据源下通常缺失，因此 `sort_by=citation` 对 arXiv 结果影响有限。
- Sentence-Transformers 第一次加载模型会比较慢，首次推荐请求会有冷启动时间。
