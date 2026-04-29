# System Pipeline

```mermaid
flowchart LR
    A[User Query]
    B[Query Processing]
    C[Academic API Search]
    D[Candidate Paper Pool]
    E[Metadata Cleaning]
    F[BM25 Scoring]
    G[Dense Embedding Scoring]
    H[Hybrid Ranking]
    I[Structured Abstract Analysis]
    J[Recommendation Display]

    A --> B --> C --> D --> E --> F --> H
    E --> G --> H --> I --> J
```
