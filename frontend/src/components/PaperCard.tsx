import type { RecommendedPaper } from "../api";

interface PaperCardProps {
  paper: RecommendedPaper;
}

export function PaperCard({ paper }: PaperCardProps) {
  const summary = paper.structured_summary;

  return (
    <article className="paper-card">
      <div className="paper-card-header">
        <div>
          <span className="paper-rank">Top {paper.rank}</span>
          <h3>{paper.title}</h3>
          <p className="paper-meta">
            {paper.authors.join(", ") || "Unknown authors"} | {paper.year ?? "Unknown year"} |{" "}
            {paper.venue || paper.source}
          </p>
        </div>
        <div className="score-badges">
          <span>Final {paper.final_score.toFixed(4)}</span>
          <span>Dense {paper.dense_score.toFixed(4)}</span>
          <span>BM25 {paper.bm25_score.toFixed(4)}</span>
        </div>
      </div>

      <p className="abstract-block">{paper.abstract || "No abstract provided by the source."}</p>

      <div className="summary-grid">
        <section>
          <h4>推荐理由</h4>
          <p>{paper.recommendation_reason}</p>
        </section>
        <section>
          <h4>研究问题</h4>
          <p>{summary.research_problem}</p>
        </section>
        <section>
          <h4>核心方法</h4>
          <p>{summary.core_method}</p>
        </section>
        <section>
          <h4>主要贡献</h4>
          <p>{summary.main_contribution}</p>
        </section>
        <section>
          <h4>实验或证据</h4>
          <p>{summary.experimental_evidence}</p>
        </section>
        <section>
          <h4>局限性</h4>
          <p>{summary.limitations}</p>
        </section>
      </div>

      <div className="link-row">
        {paper.url ? (
          <a href={paper.url} target="_blank" rel="noreferrer">
            论文链接
          </a>
        ) : (
          <span>论文链接缺失</span>
        )}
        {paper.pdf_url ? (
          <a href={paper.pdf_url} target="_blank" rel="noreferrer">
            PDF 链接
          </a>
        ) : (
          <span>PDF 链接缺失</span>
        )}
      </div>
    </article>
  );
}
