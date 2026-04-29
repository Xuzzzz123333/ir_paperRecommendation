import { useEffect, useMemo, useState } from "react";
import { clearCache, fetchSources, healthCheck, recommendPapers, type RecommendRequest, type RecommendedPaper, type SourceName } from "./api";
import { FilterPanel } from "./components/FilterPanel";
import { PaperCard } from "./components/PaperCard";
import { PaperTable } from "./components/PaperTable";
import { SearchBox } from "./components/SearchBox";

const DEFAULT_FORM: RecommendRequest = {
  query: "",
  max_results: 10,
  source: "arxiv",
  alpha: 0.65,
  sort_by: "relevance",
  model_name: "sentence-transformers/all-MiniLM-L6-v2",
};

function App() {
  const [health, setHealth] = useState("checking");
  const [sources, setSources] = useState<SourceName[]>(["arxiv", "openalex", "semantic_scholar"]);
  const [form, setForm] = useState<RecommendRequest>(DEFAULT_FORM);
  const [results, setResults] = useState<RecommendedPaper[]>([]);
  const [loading, setLoading] = useState(false);
  const [clearing, setClearing] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  useEffect(() => {
    const bootstrap = async () => {
      try {
        const [healthResult, sourceResult] = await Promise.all([healthCheck(), fetchSources()]);
        setHealth(healthResult.status);
        setSources(sourceResult.sources);
      } catch (bootstrapError) {
        const detail = bootstrapError instanceof Error ? bootstrapError.message : "Backend is unavailable.";
        setHealth("offline");
        setError(detail);
      }
    };

    void bootstrap();
  }, []);

  const stats = useMemo(
    () => [
      { label: "Backend", value: health },
      { label: "Source", value: form.source },
      { label: "Results", value: String(results.length) },
      { label: "Ranking", value: `${Math.round(form.alpha * 100)}% Dense / ${Math.round((1 - form.alpha) * 100)}% BM25` },
    ],
    [form.alpha, form.source, health, results.length],
  );

  const handleFieldChange = (
    key: keyof RecommendRequest,
    value: RecommendRequest[keyof RecommendRequest],
  ) => {
    setForm((current) => ({ ...current, [key]: value }));
  };

  const handleSearch = async () => {
    if (!form.query.trim()) {
      setError("请输入研究主题后再开始检索。");
      return;
    }

    setLoading(true);
    setError("");
    setMessage("");
    try {
      const response = await recommendPapers({
        ...form,
        query: form.query.trim(),
      });
      setResults(response.papers);
      setMessage(response.message);
    } catch (searchError) {
      const detail = searchError instanceof Error ? searchError.message : "Search failed.";
      setError(detail);
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  const handleClearCache = async () => {
    setClearing(true);
    setError("");
    try {
      const response = await clearCache();
      setMessage(response.message);
    } catch (clearError) {
      const detail = clearError instanceof Error ? clearError.message : "Failed to clear cache.";
      setError(detail);
    } finally {
      setClearing(false);
    }
  };

  return (
    <div className="app-shell">
      <header className="hero">
        <div className="hero-copy">
          <span className="eyebrow">HW3 Demo</span>
          <h1>面向科研主题的论文自动检索与结构化摘要系统</h1>
          <p>
            基于开放学术数据源、BM25 与向量语义检索的混合推荐流程，自动返回候选论文、排序分数和可解释的摘要结构。
          </p>
        </div>
        <div className="hero-stats">
          {stats.map((item) => (
            <div key={item.label} className="stat-card">
              <span>{item.label}</span>
              <strong>{item.value}</strong>
            </div>
          ))}
        </div>
      </header>

      <main className="content-grid">
        <SearchBox
          query={form.query}
          loading={loading}
          onQueryChange={(value) => handleFieldChange("query", value)}
          onSearch={handleSearch}
        />

        <FilterPanel
          filters={form}
          sources={sources}
          clearing={clearing}
          onChange={handleFieldChange}
          onClearCache={handleClearCache}
        />

        {error ? <div className="feedback error">{error}</div> : null}
        {message ? <div className="feedback success">{message}</div> : null}

        <PaperTable papers={results} />

        <section className="results-panel">
          <div className="section-heading">
            <span className="eyebrow">Cards</span>
            <h2>结构化推荐卡片</h2>
          </div>
          <div className="card-list">
            {results.length ? (
              results.map((paper) => <PaperCard key={`${paper.title}-${paper.rank}`} paper={paper} />)
            ) : (
              <div className="empty-state">
                <h3>还没有推荐结果</h3>
                <p>输入研究主题后，系统会自动从论文平台检索候选论文并生成结构化分析。</p>
              </div>
            )}
          </div>
        </section>
      </main>
    </div>
  );
}

export default App;
