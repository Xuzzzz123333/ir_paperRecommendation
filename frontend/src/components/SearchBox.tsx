interface SearchBoxProps {
  query: string;
  loading: boolean;
  onQueryChange: (value: string) => void;
  onSearch: () => void;
}

export function SearchBox({ query, loading, onQueryChange, onSearch }: SearchBoxProps) {
  return (
    <section className="panel hero-search">
      <div className="section-heading">
        <span className="eyebrow">Query</span>
        <h2>输入研究主题并自动推荐论文</h2>
        <p>系统会自动从开放论文平台拉取候选论文，完成混合排序与结构化摘要分析。</p>
      </div>
      <div className="search-row">
        <input
          className="search-input"
          value={query}
          onChange={(event) => onQueryChange(event.target.value)}
          placeholder="输入研究主题，例如：DINOv2 for remote sensing change detection"
        />
        <button className="primary-button" onClick={onSearch} disabled={loading}>
          {loading ? "检索中..." : "搜索并推荐论文"}
        </button>
      </div>
    </section>
  );
}
