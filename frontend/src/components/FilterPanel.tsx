import type { ChangeEvent } from "react";
import type { RecommendRequest, SourceName, SortOption } from "../api";

interface FilterPanelProps {
  filters: RecommendRequest;
  sources: SourceName[];
  clearing: boolean;
  onChange: (key: keyof RecommendRequest, value: RecommendRequest[keyof RecommendRequest]) => void;
  onClearCache: () => void;
}

export function FilterPanel({ filters, sources, clearing, onChange, onClearCache }: FilterPanelProps) {
  const onNumberChange =
    (key: "max_results" | "alpha" | "year_from" | "year_to") => (event: ChangeEvent<HTMLInputElement>) => {
      const value = event.target.value.trim();
      if (!value) {
        onChange(key, undefined);
        return;
      }
      onChange(key, Number(value));
    };

  return (
    <section className="panel">
      <div className="section-heading">
        <span className="eyebrow">Parameters</span>
        <h2>检索与排序参数</h2>
      </div>
      <div className="filter-grid">
        <label>
          <span>数据源</span>
          <select
            value={filters.source}
            onChange={(event) => onChange("source", event.target.value as SourceName)}
          >
            {sources.map((source) => (
              <option key={source} value={source}>
                {source}
              </option>
            ))}
          </select>
        </label>

        <label>
          <span>max_results</span>
          <input type="number" min={1} max={50} value={filters.max_results} onChange={onNumberChange("max_results")} />
        </label>

        <label>
          <span>alpha</span>
          <input
            type="number"
            min={0}
            max={1}
            step={0.05}
            value={filters.alpha}
            onChange={onNumberChange("alpha")}
          />
        </label>

        <label>
          <span>year_from</span>
          <input
            type="number"
            min={1900}
            max={2100}
            value={filters.year_from ?? ""}
            onChange={onNumberChange("year_from")}
          />
        </label>

        <label>
          <span>year_to</span>
          <input
            type="number"
            min={1900}
            max={2100}
            value={filters.year_to ?? ""}
            onChange={onNumberChange("year_to")}
          />
        </label>

        <label>
          <span>sort_by</span>
          <select
            value={filters.sort_by}
            onChange={(event) => onChange("sort_by", event.target.value as SortOption)}
          >
            <option value="relevance">relevance</option>
            <option value="year">year</option>
            <option value="citation">citation</option>
          </select>
        </label>
      </div>
      <div className="button-row">
        <button className="secondary-button" onClick={onClearCache} disabled={clearing}>
          {clearing ? "清空中..." : "清空本地缓存"}
        </button>
      </div>
    </section>
  );
}
