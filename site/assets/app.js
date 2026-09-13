"use strict";

const state = { data: null, scatterFilter: "all" };
const number = new Intl.NumberFormat("zh-CN");
const percent = (value, digits = 1) => `${(value * 100).toFixed(digits)}%`;
const points = (value, digits = 1) => `${value >= 0 ? "+" : ""}${(value * 100).toFixed(digits)}pp`;

function setText(id, value) {
  document.getElementById(id).textContent = value;
}

function escapeHtml(value) {
  return String(value).replace(/[&<>'"]/g, char => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;"
  })[char]);
}

function renderKpis(data) {
  const k = data.kpis;
  setText("snapshot-date", `数据快照：${data.metadata.snapshot_date} · 每日更新设计`);
  setText("kpi-games", number.format(k.game_count));
  setText("kpi-support", percent(k.simplified_chinese_support_rate));
  setText("kpi-support-count", `${number.format(k.simplified_chinese_support_count)} 款标注支持`);
  setText("kpi-cn-coverage", percent(k.chinese_review_coverage_rate));
  setText("kpi-cn-count", `${number.format(k.games_with_chinese_reviews)} 款出现中文评论`);
  setText("kpi-gap", points(k.median_chinese_vs_non_chinese_gap));
}

function renderScatter() {
  const source = state.data.games.filter(game => game.analysis_eligible);
  const games = source.filter(game => {
    if (state.scatterFilter === "supported") return game.supports_simplified_chinese;
    if (state.scatterFilter === "unsupported") return !game.supports_simplified_chinese;
    return true;
  });
  const root = document.getElementById("scatter-chart");
  const width = 920;
  const height = 500;
  const margin = { top: 24, right: 28, bottom: 60, left: 72 };
  const innerWidth = width - margin.left - margin.right;
  const innerHeight = height - margin.top - margin.bottom;
  const xMax = Math.max(0.9, Math.ceil(Math.max(...source.map(d => d.chinese_review_share)) * 10) / 10);
  const yMin = Math.min(-0.5, Math.floor(Math.min(...source.map(d => d.chinese_vs_non_chinese_gap)) * 10) / 10);
  const yMax = Math.max(0.1, Math.ceil(Math.max(...source.map(d => d.chinese_vs_non_chinese_gap)) * 10) / 10);
  const x = value => margin.left + value / xMax * innerWidth;
  const y = value => margin.top + (yMax - value) / (yMax - yMin) * innerHeight;
  const radius = count => 4 + Math.min(12, Math.log10(Math.max(10, count)) * 1.75);
  const xTicks = Array.from({ length: 6 }, (_, index) => xMax * index / 5);
  const yTicks = Array.from({ length: 7 }, (_, index) => yMin + (yMax - yMin) * index / 6);

  const grid = [
    ...xTicks.map(tick => `<line class="grid-line" x1="${x(tick)}" x2="${x(tick)}" y1="${margin.top}" y2="${height - margin.bottom}"/><text class="axis-label" text-anchor="middle" x="${x(tick)}" y="${height - 31}">${percent(tick, 0)}</text>`),
    ...yTicks.map(tick => `<line class="grid-line" x1="${margin.left}" x2="${width - margin.right}" y1="${y(tick)}" y2="${y(tick)}"/><text class="axis-label" text-anchor="end" x="${margin.left - 10}" y="${y(tick) + 4}">${points(tick, 0)}</text>`)
  ].join("");

  const circles = games.map(game => `<circle class="game-point" tabindex="0" data-appid="${game.appid}" cx="${x(game.chinese_review_share)}" cy="${y(game.chinese_vs_non_chinese_gap)}" r="${radius(game.chinese_review_count)}" fill="${game.supports_simplified_chinese ? "#2e91e8" : "#ffb547"}" fill-opacity=".67" stroke="#fff" stroke-width="1.4"/>`).join("");

  root.innerHTML = `<svg viewBox="0 0 ${width} ${height}" aria-hidden="true">
    ${grid}
    <line class="zero-line" x1="${margin.left}" x2="${width - margin.right}" y1="${y(0)}" y2="${y(0)}"/>
    ${circles}
    <text class="axis-label" text-anchor="middle" x="${margin.left + innerWidth / 2}" y="${height - 5}">简体中文评论占全部评论的比例</text>
    <text class="axis-label" text-anchor="middle" transform="translate(17 ${margin.top + innerHeight / 2}) rotate(-90)">中文好评率 − 非中文好评率</text>
  </svg>`;

  const tooltip = document.getElementById("tooltip");
  root.querySelectorAll(".game-point").forEach(circle => {
    const game = games.find(item => String(item.appid) === circle.dataset.appid);
    const show = event => {
      tooltip.innerHTML = `<strong>${escapeHtml(game.name)}</strong>中文评论占比 ${percent(game.chinese_review_share)}<br>中文评价落差 ${points(game.chinese_vs_non_chinese_gap)}<br>中文评论 ${number.format(game.chinese_review_count)} 条`;
      const clientX = event.clientX || root.getBoundingClientRect().left + root.clientWidth / 2;
      const clientY = event.clientY || root.getBoundingClientRect().top + 80;
      tooltip.style.left = `${Math.min(window.innerWidth - 290, clientX + 14)}px`;
      tooltip.style.top = `${Math.max(12, clientY - 30)}px`;
      tooltip.classList.add("visible");
    };
    circle.addEventListener("pointerenter", show);
    circle.addEventListener("pointermove", show);
    circle.addEventListener("focus", show);
    circle.addEventListener("pointerleave", () => tooltip.classList.remove("visible"));
    circle.addEventListener("blur", () => tooltip.classList.remove("visible"));
  });
}

function renderComparison(data) {
  const rows = [...data.support_comparison].sort((a, b) => Number(b.supports_simplified_chinese) - Number(a.supports_simplified_chinese));
  document.getElementById("support-comparison").innerHTML = rows.map(row => `
    <div class="comparison-row ${row.supports_simplified_chinese ? "supported" : "unsupported"}">
      <div class="comparison-label"><span>${escapeHtml(row.label)} · ${row.game_count} 款</span><strong>${percent(row.median_chinese_review_share)}</strong></div>
      <div class="comparison-track"><div class="comparison-fill" style="width:${Math.min(100, row.median_chinese_review_share * 400)}%"></div></div>
      <p class="fine-print">中文评论占比中位数；评价落差中位数 ${points(row.median_chinese_vs_non_chinese_gap)}</p>
    </div>`).join("");
  const test = data.inferential_comparison;
  setText("comparison-note", test.status === "computed"
    ? `中位数差 ${points(test.median_difference)}，95% bootstrap 区间 ${points(test.bootstrap_ci_95[0])} 至 ${points(test.bootstrap_ci_95[1])}；Mann–Whitney 双侧检验 p=${test.p_value.toFixed(4)}。只说明组间关联。`
    : "未标注中文支持的游戏数量不足，暂不进行组间推断。"
  );
}

function renderBarList(id, games, field, formatter, negative = false) {
  const max = Math.max(...games.map(game => Math.abs(game[field])));
  document.getElementById(id).innerHTML = games.slice(0, 10).map(game => `
    <div class="bar-item" title="${escapeHtml(game.name)}">
      <span class="bar-name">${escapeHtml(game.name)}</span>
      <span class="bar-track"><span class="bar-fill" style="display:block;width:${Math.abs(game[field]) / max * 100}%"></span></span>
      <span class="bar-value">${formatter(game[field])}</span>
    </div>`).join("");
}

function renderRankings(data) {
  renderBarList("share-ranking", data.top_chinese_review_share, "chinese_review_share", value => percent(value), false);
  renderBarList("gap-ranking", data.largest_negative_gaps, "chinese_vs_non_chinese_gap", value => points(value), true);
}

function renderTable() {
  const search = document.getElementById("game-search").value.trim().toLocaleLowerCase();
  const support = document.getElementById("support-filter").value;
  const chart = document.getElementById("chart-filter").value;
  const games = state.data.games.filter(game => {
    if (search && !game.name.toLocaleLowerCase().includes(search)) return false;
    if (support === "supported" && !game.supports_simplified_chinese) return false;
    if (support === "unsupported" && game.supports_simplified_chinese) return false;
    if (chart !== "all" && game.chart_membership !== chart) return false;
    return true;
  });
  document.getElementById("game-table-body").innerHTML = games.slice(0, 100).map(game => {
    const gap = game.chinese_vs_non_chinese_gap;
    const eligible = gap !== null && game.analysis_eligible;
    return `<tr>
      <td><a href="https://store.steampowered.com/app/${game.appid}" target="_blank" rel="noreferrer">${escapeHtml(game.name)}</a></td>
      <td>${game.best_chart_rank ?? "—"}</td>
      <td><span class="badge ${game.supports_simplified_chinese ? "" : "muted"}">${game.supports_simplified_chinese ? "支持" : "未标注"}</span></td>
      <td>${number.format(game.chinese_review_count)}</td>
      <td>${game.chinese_review_share === null ? "—" : percent(game.chinese_review_share)}</td>
      <td>${game.chinese_positive_rate === null ? "—" : percent(game.chinese_positive_rate)}</td>
      <td class="${eligible && gap < 0 ? "gap-negative" : "gap-positive"}">${eligible ? points(gap) : "样本不足"}</td>
    </tr>`;
  }).join("");
  setText("table-status", `符合当前筛选：${games.length} 款${games.length > 100 ? "（表格先显示前100款）" : ""}`);
}

function bindControls() {
  document.querySelectorAll("[data-scatter-filter]").forEach(button => {
    button.addEventListener("click", () => {
      document.querySelectorAll("[data-scatter-filter]").forEach(item => item.classList.remove("active"));
      button.classList.add("active");
      state.scatterFilter = button.dataset.scatterFilter;
      renderScatter();
    });
  });
  ["game-search", "support-filter", "chart-filter"].forEach(id => {
    document.getElementById(id).addEventListener(id === "game-search" ? "input" : "change", renderTable);
  });
}

async function initialize() {
  try {
    const response = await fetch("assets/data/latest.json", { cache: "no-store" });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    state.data = await response.json();
    renderKpis(state.data);
    renderScatter();
    renderComparison(state.data);
    renderRankings(state.data);
    renderTable();
    document.getElementById("limitations").innerHTML = state.data.limitations.map(item => `<li>${escapeHtml(item)}</li>`).join("");
    bindControls();
  } catch (error) {
    console.error(error);
    setText("snapshot-date", "数据载入失败，请稍后刷新");
  }
}

initialize();
