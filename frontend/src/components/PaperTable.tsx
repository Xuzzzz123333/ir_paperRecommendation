import type { RecommendedPaper } from "../api";

interface PaperTableProps {
  papers: RecommendedPaper[];
}

export function PaperTable({ papers }: PaperTableProps) {
  return (
    <section className="panel">
      <div className="section-heading">
        <span className="eyebrow">Ranking</span>
        <h2>推荐结果表格</h2>
      </div>
      <div className="table-wrap">
        <table className="paper-table">
          <thead>
            <tr>
              <th>Rank</th>
              <th>Title</th>
              <th>Year</th>
              <th>Authors</th>
              <th>Final Score</th>
              <th>Dense</th>
              <th>BM25</th>
              <th>Citation Count</th>
            </tr>
          </thead>
          <tbody>
            {papers.map((paper) => (
              <tr key={`${paper.title}-${paper.rank}`}>
                <td>{paper.rank}</td>
                <td>{paper.title}</td>
                <td>{paper.year ?? "-"}</td>
                <td>{paper.authors.slice(0, 3).join(", ") || "-"}</td>
                <td>{paper.final_score.toFixed(4)}</td>
                <td>{paper.dense_score.toFixed(4)}</td>
                <td>{paper.bm25_score.toFixed(4)}</td>
                <td>{paper.citation_count ?? "-"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
