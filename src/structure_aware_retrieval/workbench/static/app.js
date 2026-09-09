"use strict";

// Repository text is always rendered as text, never as HTML or executable links.
const $ = (id) => document.getElementById(id);
const state = { token: null, repositories: [], history: [], busy: true, job: null, run: null, poll: null, plan: null, generation: null, submittedPlan: null };
const strategies = [
  ["bm25", "BM25", "关键词与标识符匹配"],
  ["dense", "Dense", "向量语义检索"],
  ["hybrid", "Hybrid", "BM25 与 Dense 排名融合"],
  ["symbol", "Symbol-aware", "融合检索与符号特征"],
  ["structure", "Structure-aware", "融合检索与代码关系"],
];
const labels = {
  created: "已创建", queued: "等待中", pending: "尚未运行", running: "运行中",
  validating: "校验来源", downloading: "下载源码", snapshotting: "保存源码快照",
  preparing: "准备资源", ready: "已就绪", reused: "已复用", completed: "已完成",
  preview: "上下文已准备", preview_complete: "五策略预览完成", partial: "部分完成",
  failed: "失败", interrupted: "已中断", insufficient_context: "上下文不足",
  unreadable: "记录无法读取", imported: "已导入", missing: "尚未准备",
  answered: "已生成回答", generation_complete: "回答生成完成", not_run: "未运行",
  outcome_unknown: "请求结果未知", provider_error: "模型请求失败", invalid_answer: "回答格式或引用无效",
  no_evidence: "无证据，不调用模型", unavailable: "上下文不可用", no_context: "上下文不可用",
};
const finished = (status) => ["completed", "failed", "interrupted", "partial", "unreadable"].includes(status);
const statusText = (status) => labels[status] || status || "未知";
const text = (value) => value === null || value === undefined ? "未知" : String(value);
const short = (value, size = 12) => value ? String(value).slice(0, size) : "未知";
const date = (value) => value && !Number.isNaN(Date.parse(value)) ? new Date(value).toLocaleString() : "时间未知";
const ms = (value) => typeof value === "number" && Number.isFinite(value) ? `${value.toFixed(1)} ms` : "未知";
const money = (value) => typeof value === "number" && Number.isFinite(value) ? `US$${value.toFixed(6)}` : "未知";
const errorText = (error) => typeof error === "string" ? error : error?.message || error?.type || "未知错误";
const modeText = (mode) => ({ context_preview: "上下文预览", model_generation: "模型回答", offline_test: "离线测试 · 合成回答" })[mode] || "未知模式";
function node(tag, className = "", content) {
  const item = document.createElement(tag);
  if (className) item.className = className;
  if (content !== undefined) item.textContent = text(content);
  return item;
}
function notice(message = "") {
  $("notice").textContent = message;
  $("notice").hidden = !message;
}
async function api(path, body) {
  const options = { headers: {}, cache: "no-store", signal: AbortSignal.timeout(20000) };
  if (body !== undefined) {
    options.method = "POST";
    options.headers = { "Content-Type": "application/json", "X-Workbench-Token": state.token };
    options.body = JSON.stringify(body);
  }
  const response = await fetch(path, options);
  const payload = await response.json();
  if (!response.ok) throw new Error(errorText(payload.error || payload));
  return payload;
}
function setBusy(value) {
  state.busy = value;
  $("import-button").disabled = value || !state.token;
  $("prepare-button").disabled = value || !state.token;
  $("preview-button").disabled = value || !state.token || !$("repository-select").value;
  $("plan-button").disabled = value || !state.token || state.run?.mode !== "context_preview";
  updateGenerationButton();
}
function updateGenerationButton() {
  const plan = state.plan;
  const budget = Number($("generation-budget").value);
  $("generate-button").disabled = state.busy || !state.token || !plan || state.submittedPlan === plan.plan_id ||
    !$("generation-confirm").checked || !Number.isFinite(budget) || budget <= 0 || budget < plan.estimated_cost_usd;
}
function showView(name) {
  $("workbench-view").hidden = name !== "workbench";
  $("history-view").hidden = name !== "history";
  for (const view of ["workbench", "history"]) {
    $("nav-" + view).classList.toggle("active", view === name);
    if (view === name) $("nav-" + view).setAttribute("aria-current", "page");
    else $("nav-" + view).removeAttribute("aria-current");
  }
}
function stage(name, status) {
  const good = ["ready", "reused", "completed", "preview", "preview_complete", "answered", "generation_complete"].includes(status);
  const bad = ["failed", "interrupted", "unreadable", "outcome_unknown", "provider_error", "invalid_answer"].includes(status);
  return node("span", `stage${good ? " good" : bad ? " bad" : ""}`, `${name} · ${statusText(status)}`);
}
function selectedRepository() {
  return state.repositories.find((record) => record.repository_id === $("repository-select").value);
}
function renderRepository() {
  const box = $("repository-info");
  box.replaceChildren();
  const repository = selectedRepository();
  $("prepare-button").hidden = !repository || repository.status === "unreadable";
  if (!repository) {
    box.append(node("p", "muted", "导入仓库后，这里会显示实际源码版本和资源状态。"));
    setBusy(state.busy);
    return;
  }
  const source = repository.source || {};
  box.append(node("p", "mono", source.location || repository.repository_id));
  const version = node("div", "repo-version");
  version.append(node("span", "mono", `commit ${text(source.commit)}`));
  version.append(node("span", "muted", `${text(repository.file_count)} 个已保存文件`));
  box.append(version);
  if (source.working_tree) box.append(node("p", "muted", "本地工作区快照：commit 仅为版本线索；实际内容以保存的文件哈希为准，工作区清洁状态未知。"));
  const stages = node("div", "repo-stages");
  const prepared = repository.stages || repository.preparation?.stages || {};
  for (const [key, name] of [["index", "解析 / 索引"], ["vectors", "向量"], ["graph", "关系图"]]) {
    stages.append(stage(name, prepared[key]?.status || "missing"));
  }
  box.append(stages);
  if (repository.error) box.append(node("p", "error-text", errorText(repository.error)));
  for (const [key, value] of Object.entries(prepared)) {
    if (value.error) box.append(node("p", "error-text", `${key}: ${errorText(value.error)}`));
  }
  setBusy(state.busy);
}
async function refreshRepositories(preferred) {
  const selected = preferred || $("repository-select").value;
  state.repositories = await api("/api/repositories");
  const select = $("repository-select");
  select.replaceChildren(node("option", "", "选择已导入仓库…"));
  select.firstChild.value = "";
  for (const repository of state.repositories) {
    const source = repository.source || {};
    const label = `${source.location || short(repository.repository_id)} · ${short(source.commit)} · ${statusText(repository.status)}`;
    const option = node("option", "", label);
    option.value = repository.repository_id;
    option.disabled = repository.status === "unreadable";
    select.append(option);
  }
  if (state.repositories.some((row) => row.repository_id === selected)) select.value = selected;
  else if (state.repositories.length) select.value = state.repositories.find((row) => row.status !== "unreadable")?.repository_id || "";
  $("import-details").open = !select.value;
  renderRepository();
}
function renderJob(job) {
  state.job = job;
  $("job-panel").hidden = false;
  const outcome = job.result?.preparation?.status || job.result?.status;
  $("job-status").textContent = job.status === "completed" && ["partial", "failed"].includes(outcome) ? `任务结束 · ${statusText(outcome)}` : statusText(job.status);
  $("job-id").textContent = `任务 ${job.job_id}`;
  const progress = job.progress || {};
  const detail = progress.detail || {};
  const box = $("job-stages");
  box.replaceChildren();
  if (progress.phase === "import") {
    const seen = new Set((detail.events || []).map((event) => event.status));
    for (const [key, name] of [["validating", "校验来源"], ["downloading", "下载源码"], ["snapshotting", "保存快照"]]) {
      if (seen.has(key)) box.append(stage(name, detail.status === key ? "running" : "completed"));
    }
    if (detail.cache_hit) box.append(stage("源码缓存", "reused"));
  } else if (progress.phase === "prepare") {
    for (const [key, name] of [["index", "解析 / 索引"], ["vectors", "向量准备"], ["graph", "关系图"]]) {
      box.append(stage(name, detail.stages?.[key]?.status));
    }
  } else if (["preview", "generation"].includes(progress.phase)) {
    for (const row of detail.results || []) box.append(stage(strategies.find(([key]) => key === row.strategy)?.[1] || row.strategy, row.status));
  }
  if (!box.childElementCount) box.append(stage(job.kind || "任务", job.status));
  const errors = [];
  if (job.error) errors.push(errorText(job.error));
  if (job.recovery_warning) errors.push(job.recovery_warning);
  if (detail.error) errors.push(errorText(detail.error));
  if (detail.cleanup_error) errors.push(detail.cleanup_error);
  for (const [key, value] of Object.entries(detail.stages || {})) {
    if (value.error) errors.push(`${key}: ${errorText(value.error)}`);
  }
  $("job-error").textContent = [...new Set(errors)].join("\n");
  $("job-error").hidden = !errors.length;
}
async function pollJob(id) {
  clearTimeout(state.poll);
  try {
    const job = await api(`/api/jobs/${id}`);
    if ($("notice").textContent.startsWith("读取任务状态失败")) notice();
    renderJob(job);
    if (!finished(job.status)) {
      setBusy(true);
      state.poll = setTimeout(() => pollJob(id), 1000);
      return;
    }
    setBusy(false);
    await refreshRepositories(job.result?.repository_id);
    await refreshHistory();
    const runId = job.result?.run_id || (["preview", "generation"].includes(job.kind) ? job.progress?.detail?.run_id : null);
    if (runId) await openRun(runId, true);
  } catch (error) {
    notice(`读取任务状态失败：${error.message}。不会重新提交任务，正在尝试恢复状态读取。`);
    state.poll = setTimeout(() => pollJob(id), 3000);
  }
}
async function submit(path, body) {
  notice();
  setBusy(true);
  try {
    const job = await api(path, body);
    renderJob(job);
    await pollJob(job.job_id);
  } catch (error) {
    setBusy(false);
    notice(`提交未得到成功确认：${error.message}。不会自动重试；请查看任务状态或刷新页面。`);
    // Read-only discovery can recover an accepted request whose response was lost.
    try {
      const jobs = await api("/api/jobs");
      const active = jobs.find((job) => !finished(job.status));
      if (active) { setBusy(true); await pollJob(active.job_id); }
      else if (jobs.length) renderJob(jobs[0]);
    } catch { /* The original uncertainty stays visible. */ }
  }
}
function metric(grid, label, value) {
  const pair = node("div");
  pair.append(node("dt", "", label), node("dd", "", value));
  grid.append(pair);
}
function renderPlan(plan) {
  state.plan = plan;
  $("plan-content").hidden = false;
  $("generation-confirm").checked = false;
  $("generation-budget").value = Math.max(0.01, Math.ceil(plan.estimated_cost_usd * 100) / 100).toFixed(2);
  const summary = $("plan-summary");
  summary.replaceChildren();
  metric(summary, "回答模型", plan.model);
  metric(summary, "问题（使用已保存预览）", plan.question);
  metric(summary, "生成 / 评审请求上限", `${text(plan.request_limit)} / ${text(plan.judge_calls)}`);
  metric(summary, "合计保守估算", money(plan.estimated_cost_usd));
  metric(summary, "输入 / 输出单价（每百万 token）", `US$${text(plan.pricing?.input_per_million)} / US$${text(plan.pricing?.output_per_million)}`);
  metric(summary, "价格核对日期", plan.pricing?.as_of);
  const rows = $("plan-rows");
  rows.replaceChildren();
  for (const item of plan.strategies || []) {
    const row = node("tr");
    for (const value of [strategies.find(([key]) => key === item.strategy)?.[1] || item.strategy, statusText(item.status), text(item.estimated_input_tokens), text(item.max_output_tokens), money(item.estimated_cost_usd)]) row.append(node("td", "", value));
    rows.append(row);
  }
  $("plan-note").textContent = `方案 ${plan.plan_id} · 预览 ${plan.preview_run_id}。UTF-8 字节与请求格式开销用于保守估算，输出按上限计费；这不是精确 token 计数或账单。没有安排 LLM 评审。`;
  $("key-status").textContent = state.generation?.key_ready ? "服务端已检测到 OPENAI_API_KEY；密钥不会发送到浏览器。" : "服务端尚未检测到 OPENAI_API_KEY。请在启动服务的终端配置环境变量后重启服务；不要在页面或聊天中填写密钥。";
  $("generation-confirm-label").textContent = `确认使用 ${plan.model}，最多 ${plan.request_limit} 次生成、${plan.judge_calls} 次评审，并按填写的预算执行本方案。`;
  history.replaceState(null, "", `#plan=${plan.plan_id}`);
  updateGenerationButton();
}
async function prepareGenerationPlan() {
  if (state.busy || state.run?.mode !== "context_preview") return;
  const runId = state.run.run_id;
  state.plan = null;
  $("plan-content").hidden = true;
  notice();
  setBusy(true);
  try {
    const plan = await api("/api/generation-plan", { run_id: runId });
    if (state.run?.run_id === runId) renderPlan(plan);
  } catch (error) { notice(`费用方案未完成：${error.message}。未请求生成回答。`); }
  finally { setBusy(false); }
}
function renderGenerationSummary(run, current) {
  const box = $("generation-summary");
  box.replaceChildren();
  box.hidden = run.mode === "context_preview";
  if (box.hidden) return;
  const synthetic = run.mode === "offline_test";
  box.append(node("h3", "", synthetic ? "离线测试记录：合成模型输出" : current ? "本轮真实生成 · 已保存" : "历史模型回答 · 已保存结果"));
  box.append(node("p", "field-help", synthetic ? "用于验证软件流程；回答、token 数和据此计算的费用来自测试替身，不是真实 API 实验。" : "各策略共用同一模型与生成设置，回答可以相同。自动引用检查不代表语义支持；本轮没有 LLM 评审。"));
  const summary = run.generation?.summary || {};
  const metrics = node("dl", "plan-summary");
  metric(metrics, "配置模型", run.settings?.answer_model || run.generation?.settings?.model || run.generation?.model);
  metric(metrics, "已发起 / 已收到响应", `${text(summary.calls_started)} / ${text(summary.responses_received)}`);
  metric(metrics, "结果未知 / 未运行", `${text(summary.outcome_unknown)} / ${text(summary.not_run)}`);
  metric(metrics, "真实 API 调用", text(run.api_calls));
  box.append(metrics);
  box.append(node("p", "field-help", "缺失用量与费用保留为未知。费用按已报告用量和冻结单价估算，未应用缓存优惠，也不是实际账单。"));
  if (run.parent_preview_run_id) {
    const button = node("button", "button secondary", "打开原始上下文预览");
    button.type = "button";
    button.addEventListener("click", () => openRun(run.parent_preview_run_id).catch((error) => notice(error.message)));
    box.append(button);
  }
}
function renderAnswer(body, row, name, evidence) {
  if (state.run?.mode === "context_preview") {
    body.append(node("p", "preview-label", row.qa ? "尚未生成回答。以下为这项策略检索并选入上下文的代码证据。" : "此策略没有可用的上下文结果，也没有生成回答。"));
    return;
  }
  const claims = row.qa?.answer?.claims;
  if (row.status === "answered" && Array.isArray(claims) && claims.length) {
    const list = node("ol", "answer-claims");
    for (const claim of claims) {
      const item = node("li");
      item.append(node("p", "claim-text", claim.text));
      const citations = node("div", "evidence-chips");
      for (const id of claim.citations || []) {
        const source = evidence.find((value) => value.id === id);
        const button = node("button", "evidence-button", id);
        button.type = "button";
        button.disabled = !source;
        button.setAttribute("aria-label", `${name} 回答引用 ${id}${source ? ` ${source.path}` : "（来源缺失）"}`);
        if (source) button.addEventListener("click", () => showSource(source, row.hits?.find((hit) => hit.chunk_id === source.chunk_id), name));
        citations.append(button);
      }
      item.append(citations);
      list.append(item);
    }
    body.append(list);
  } else {
    const messages = { insufficient_context: row.qa?.model_called ? "模型判断上下文不足，未提供有引用的回答。" : "没有可用证据，未调用模型。", outcome_unknown: "请求已发起，但结果未知。可能已计费；不会自动重试。", not_run: "这项策略未请求生成回答。", provider_error: "模型请求失败，没有可展示的有效回答。", invalid_answer: "输出未通过格式或引用 ID 校验，不能作为有效回答展示。" };
    body.append(node("p", "preview-label", messages[row.status] || "没有可展示的有效回答；检索证据和错误记录仍保留。"));
  }
  if (row.qa?.raw_output !== null && row.qa?.raw_output !== undefined) {
    const raw = node("details", "extra-metrics");
    raw.append(node("summary", "", "查看模型原始输出（未经语义评分）"), node("pre", "", row.qa.raw_output));
    body.append(raw);
  }
}
function showSource(source, hit, strategyName) {
  $("source-caption").textContent = `${strategyName} / ${source.id ? `上下文证据 ${source.id}` : `检索排序 #${text(source.rank)}`}`;
  $("source-heading").textContent = source.path || "路径未知";
  $("source-name").textContent = source.qualified_name || "符号未知";
  $("source-range").textContent = `行 ${text(source.start_line)}–${text(source.end_line)}${source.truncated ? " · 已按上下文预算截断" : ""} · 来自已保存的源码快照`;
  const code = $("source-code");
  code.replaceChildren();
  const lines = String(source.text ?? "").split("\n");
  if (lines.at(-1) === "") lines.pop();
  lines.forEach((line, index) => {
    const row = node("div", "code-line");
    row.append(node("span", "line-number", Number.isInteger(source.start_line) ? source.start_line + index : "?"), node("code", "line-text", line || " "));
    code.append(row);
  });
  if (!lines.length) code.append(node("p", "muted", "这条记录未保存代码文本。"));
  $("source-provenance").textContent = JSON.stringify({ chunk_id: source.chunk_id, symbol_id: source.symbol_id, rank: hit?.rank ?? null, score: hit?.score ?? null, components: hit?.components ?? null, provenance: hit?.provenance ?? null }, null, 2);
  $("source-details").open = false;
  $("source-dialog").showModal();
}
function renderCard(key, name, description, row) {
  const card = node("article", "strategy-card");
  card.dataset.strategy = key;
  const header = node("div", "card-header");
  header.append(node("h3", "", name), node("p", "", description), node("span", `pill card-status ${row?.status || "failed"}`, row ? statusText(row.status) : "结果缺失"));
  card.append(header);
  const body = node("div", "card-body");
  card.append(body);
  if (!row) { body.append(node("p", "error-text", "归档中没有这项策略的结果。")); return card; }
  if (row.error) {
    const raw = errorText(row.error);
    const message = raw.startsWith("vectors resource is unavailable") ? "向量资源不可用。请先准备本地模型，再重新准备仓库。" : "这项策略未完成，已保留其他策略的结果。";
    body.append(node("p", "error-text", message));
    const failure = node("details", "extra-metrics");
    failure.append(node("summary", "", "查看原始错误"), node("pre", "", raw));
    body.append(failure);
  }
  const evidence = row.qa?.context?.evidence || [];
  renderAnswer(body, row, name, evidence);
  const grid = node("dl", "metric-grid");
  metric(grid, "已保存检索耗时", ms(row.timing_ms?.retrieval));
  metric(grid, "上下文字节", text(row.qa?.context?.budget?.used_context_bytes));
  metric(grid, "生成耗时", ms(row.timing_ms?.generation));
  metric(grid, "输入 / 输出 token", `${text(row.tokens?.input)} / ${text(row.tokens?.output)}`);
  metric(grid, "费用估算", money(row.cost?.estimated_usd));
  metric(grid, state.run?.mode === "offline_test" ? "测试替身调用" : "模型请求尝试", text(row.cost?.model_calls));
  body.append(grid);
  body.append(node("h4", "card-subhead", `上下文证据 · ${evidence.length}`));
  const chips = node("div", "evidence-chips");
  for (const source of evidence) {
    const button = node("button", "evidence-button", source.id);
    button.type = "button";
    button.title = `${source.path}:${source.start_line}–${source.end_line}`;
    button.setAttribute("aria-label", `${name} 证据 ${source.id} ${source.path}`);
    button.addEventListener("click", () => showSource(source, row.hits?.find((hit) => hit.chunk_id === source.chunk_id), name));
    chips.append(button);
  }
  if (!evidence.length) chips.append(node("p", "small muted", "没有可展示的上下文证据。"));
  body.append(chips);
  const checks = row.qa?.automatic_checks;
  const checkNames = { evidence_ids_valid: "证据 ID", paths_valid: "路径", line_ranges_valid: "行号", citation_ids_valid: "回答引用 ID" };
  body.append(node("p", "automatic-note", checks ? `自动源码位置检查：${Object.entries(checks).filter(([, value]) => typeof value === "boolean").map(([key, value]) => `${checkNames[key] || key}${value ? "通过" : "未通过"}`).join(" · ") || "见详细运行信息"}。这不表示语义正确。` : "自动源码位置检查：未知。"));
  body.append(node("h4", "card-subhead", `已保存检索结果 · ${row.hits?.length ?? 0}`));
  for (const hit of row.hits || []) {
    const button = node("button", "hit-button");
    button.type = "button";
    button.append(node("span", "hit-title", `#${text(hit.rank)}  ${hit.qualified_name || hit.path}`));
    button.append(node("span", "hit-path", `${hit.path} · L${hit.start_line}–${hit.end_line}`));
    button.append(node("span", "hit-score", `score ${typeof hit.score === "number" ? hit.score.toFixed(6) : "未知"}${hit.provenance?.length ? ` · ${hit.provenance.length} 条关系来源` : ""}`));
    button.addEventListener("click", () => showSource(hit, hit, name));
    body.append(button);
  }
  const details = node("details", "extra-metrics");
  details.append(node("summary", "", "更多运行信息"), node("pre", "", JSON.stringify({ timing_ms: row.timing_ms, tokens: row.tokens, cost: row.cost, ranked_candidates: row.ranked_candidates, structure_stats: row.structure_stats, automatic_checks: checks ?? null, llm_assessment: row.qa?.llm_assessment ?? null, provider: row.qa?.provider ?? null }, null, 2)));
  body.append(details);
  return card;
}
function renderRun(run, current) {
  state.run = run;
  state.plan = null;
  $("plan-content").hidden = true;
  $("generation-confirm").checked = false;
  $("generation-panel").hidden = run.mode !== "context_preview" || run.status === "running";
  $("empty-results").hidden = true;
  $("results-section").hidden = false;
  $("run-mode").textContent = `${current ? "本轮" : "历史"}${modeText(run.mode)} · 已保存结果`;
  $("comparison-note").textContent = `${run.mode === "context_preview" ? "当前显示检索上下文，没有生成回答。" : "回答使用原始预览的证据；检索耗时来自该预览，生成耗时来自本次执行。"}新问题没有相关性标签，因此不显示 Recall、NDCG 或回答正确率。不同策略的原始分数不能直接比较。`;
  $("run-question").textContent = run.question;
  $("run-meta").replaceChildren(node("span", "", `${date(run.created_at)} · ${statusText(run.status)}`), node("span", "mono", `commit ${text(run.resources?.source?.commit)}`), node("span", "mono", `run ${run.run_id}`), node("span", "", `总耗时 ${ms(run.elapsed_ms)}`));
  $("run-meta").prepend(node("span", "", `源码：${text(run.resources?.source?.location)}`));
  renderGenerationSummary(run, current);
  $("strategy-grid").replaceChildren(...strategies.map(([key, name, description]) => renderCard(key, name, description, run.results?.find((row) => row.strategy === key))));
  $("run-config").textContent = JSON.stringify({ mode: run.mode, settings: run.settings, generation: run.generation, source: run.resources?.source, snapshot_id: run.resources?.snapshot_id, resource_id: run.resources?.resource_id, index_config: run.resources?.index_config, encoder_mode: run.encoder_mode, model_spec: run.resources?.model_spec, resolver_config: run.resources?.resolver_config, shared_setup: run.shared_setup, relevance_labels: run.relevance_labels, benchmark_metrics: run.benchmark_metrics }, null, 2);
  setBusy(state.busy);
}
async function openRun(id, current = false) {
  if (!/^[0-9a-f]{32}$/.test(id)) throw new Error("无效的历史记录 ID");
  const run = await api(`/api/runs/${id}`);
  renderRun(run, current);
  showView("workbench");
  history.replaceState(null, "", `#run=${id}`);
  // Keep the composer on the shown source when it is still imported locally.
  if (state.repositories.some((row) => row.repository_id === run.repository_id)) {
    $("repository-select").value = run.repository_id;
    renderRepository();
  }
  $("question").value = run.question;
  $("results-section").scrollIntoView({ behavior: "smooth", block: "start" });
}
async function openPlan(id) {
  if (!/^[0-9a-f]{32}$/.test(id)) throw new Error("无效的生成方案 ID");
  const plan = await api(`/api/generation-plans/${id}`);
  await openRun(plan.preview_run_id);
  renderPlan(plan);
  $("generation-panel").scrollIntoView({ behavior: "smooth", block: "start" });
}
async function openSavedLocation() {
  const match = location.hash.match(/^#(run|plan)=([0-9a-f]{32})$/);
  if (match) await (match[1] === "plan" ? openPlan(match[2]) : openRun(match[2]));
}
function renderHistory() {
  const query = $("history-search").value.toLowerCase();
  const records = state.history.filter((row) => `${row.question || ""} ${row.run_id}`.toLowerCase().includes(query));
  const box = $("history-list");
  box.replaceChildren();
  for (const row of records) {
    const item = node("article", "history-item");
    const description = node("div");
    const repository = state.repositories.find((item) => item.repository_id === row.repository_id);
    description.append(node("h3", "", row.question || "无法读取的记录"), node("p", "", `${date(row.created_at)} · ${statusText(row.status)} · 已保存${modeText(row.mode)}`), node("p", "mono", `run ${row.run_id} · ${repository?.source?.location || `repository ${short(row.repository_id)}`}`));
    if (row.error) description.append(node("p", "error-text", errorText(row.error)));
    const button = node("button", "button secondary", "打开记录 →");
    button.type = "button";
    button.disabled = row.status === "unreadable";
    button.addEventListener("click", () => openRun(row.run_id).catch((error) => notice(error.message)));
    item.append(description, button);
    box.append(item);
  }
  if (!records.length) box.append(node("p", "empty-state", state.history.length ? "没有匹配的历史问题。" : "还没有保存的对比。完成一次预览后，记录会自动出现在这里。"));
}
async function refreshHistory() {
  state.history = await api("/api/history");
  $("history-count").textContent = state.history.length;
  renderHistory();
}
$("nav-workbench").addEventListener("click", () => showView("workbench"));
$("nav-history").addEventListener("click", () => { showView("history"); refreshHistory().catch((error) => notice(error.message)); });
$("refresh-repositories").addEventListener("click", () => refreshRepositories().catch((error) => notice(error.message)));
$("refresh-history").addEventListener("click", () => refreshHistory().catch((error) => notice(error.message)));
$("repository-select").addEventListener("change", () => {
  renderRepository();
  if (state.run && state.run.repository_id !== $("repository-select").value) {
    $("results-section").hidden = true;
    $("empty-results").hidden = false;
    history.replaceState(null, "", "#");
  }
});
$("history-search").addEventListener("input", renderHistory);
$("plan-button").addEventListener("click", prepareGenerationPlan);
$("generation-confirm").addEventListener("change", updateGenerationButton);
$("generation-budget").addEventListener("input", updateGenerationButton);
$("generation-form").addEventListener("submit", (event) => {
  event.preventDefault();
  updateGenerationButton();
  if ($("generate-button").disabled) return;
  const plan = state.plan;
  state.submittedPlan = plan.plan_id;
  submit("/api/generate", { plan_id: plan.plan_id, confirmed_model: plan.model, budget_usd: Number($("generation-budget").value), confirm: true });
});
$("close-source").addEventListener("click", () => $("source-dialog").close());
$("source-dialog").addEventListener("click", (event) => { if (event.target === $("source-dialog")) $("source-dialog").close(); });
$("import-form").addEventListener("submit", (event) => {
  event.preventDefault();
  if (!state.busy) submit("/api/import", { source: $("source").value.trim(), ref: $("ref").value.trim() || "HEAD" });
});
$("prepare-button").addEventListener("click", () => {
  if (!state.busy) submit("/api/prepare", { repository_id: $("repository-select").value });
});
$("question-form").addEventListener("submit", (event) => {
  event.preventDefault();
  if (!state.busy) submit("/api/preview", { repository_id: $("repository-select").value, question: $("question").value, top_k: Number($("top-k").value), max_context_bytes: Number($("context-bytes").value) });
});
window.addEventListener("hashchange", () => {
  openSavedLocation().catch((error) => notice(error.message));
});
async function start() {
  setBusy(true);
  try {
    const session = await api("/api/session");
    state.token = session.csrf_token;
    state.generation = session.generation || null;
    await Promise.all([refreshRepositories(), refreshHistory()]);
    const jobs = await api("/api/jobs");
    const active = jobs.find((job) => !finished(job.status));
    if (active) { setBusy(true); pollJob(active.job_id); }
    else { setBusy(false); if (jobs.length) renderJob(jobs[0]); }
    await openSavedLocation();
  } catch (error) { notice(`工作台连接失败：${error.message}。请确认本机服务仍在运行，然后刷新页面。`); }
}
start();
