"use strict";

// Repository text is always rendered as text, never as HTML or executable links.
const i18n = window.WorkbenchI18n;
const t = (key, values) => i18n.t(key, values);
const $ = (id) => document.getElementById(id);
const state = { token: null, repositories: [], history: [], busy: true, job: null, run: null, poll: null, plan: null, generation: null, submittedPlan: null, runCurrent: false, sourceView: null, notice: null };
const strategies = [
  ["bm25", "BM25", "app.strategy_bm25"],
  ["dense", "Dense", "app.strategy_dense"],
  ["hybrid", "Hybrid", "app.strategy_hybrid"],
  ["symbol", "Symbol-aware", "app.strategy_symbol"],
  ["structure", "Structure-aware", "app.strategy_structure"],
];
const labels = {
  "created": "app.status_created",
  "queued": "app.status_queued",
  "pending": "app.status_pending",
  "running": "app.status_running",
  "validating": "app.status_validating",
  "downloading": "app.status_downloading",
  "snapshotting": "app.status_snapshotting",
  "preparing": "app.status_preparing",
  "ready": "app.status_ready",
  "reused": "app.status_reused",
  "completed": "app.status_completed",
  "preview": "app.status_preview",
  "preview_complete": "app.status_preview_complete",
  "partial": "app.status_partial",
  "failed": "app.status_failed",
  "interrupted": "app.status_interrupted",
  "insufficient_context": "app.status_insufficient_context",
  "unreadable": "app.status_unreadable",
  "imported": "app.status_imported",
  "missing": "app.status_missing",
  "answered": "app.status_answered",
  "generation_complete": "app.status_generation_complete",
  "not_run": "app.status_not_run",
  "outcome_unknown": "app.status_outcome_unknown",
  "provider_error": "app.status_provider_error",
  "invalid_answer": "app.status_invalid_answer",
  "no_evidence": "app.status_no_evidence",
  "unavailable": "app.status_unavailable",
  "no_context": "app.status_no_context"
};
const finished = (status) => ["completed", "failed", "interrupted", "partial", "unreadable"].includes(status);
const statusText = (status) => Object.hasOwn(labels, status) ? t(labels[status]) : status || t("app.unknown");
const text = (value) => value === null || value === undefined ? t("app.unknown") : String(value);
const short = (value, size = 12) => value ? String(value).slice(0, size) : t("app.unknown");
const date = (value) => value && !Number.isNaN(Date.parse(value)) ? new Date(value).toLocaleString(i18n.getLanguage()) : t("app.unknownTime");
const ms = (value) => typeof value === "number" && Number.isFinite(value) ? `${value.toFixed(1)} ms` : t("app.unknown");
const money = (value) => typeof value === "number" && Number.isFinite(value) ? `US$${value.toFixed(6)}` : t("app.unknown");
const rawErrorText = (error) => typeof error === "string" ? error : error?.message || error?.type || t("app.unknownError");
const errorText = (error) => {
  const raw = String(rawErrorText(error));
  if (Object.hasOwn(i18n.catalogs.en, raw)) return t(raw);
  const known = Object.hasOwn(i18n.errorKeys, raw) ? i18n.errorKeys[raw] : null;
  return known ? t(known) : t("app.errorExternal", { detail: raw });
};
const modeText = (mode) => {
  const keys = { context_preview: "app.modePreview", model_generation: "app.modeGeneration", offline_test: "app.modeSynthetic" };
  return Object.hasOwn(keys, mode) ? t(keys[mode]) : t("app.unknownMode");
};
function node(tag, className = "", content) {
  const item = document.createElement(tag);
  if (className) item.className = className;
  if (content !== undefined) item.textContent = text(content);
  return item;
}
function notice(key = null, values = {}) {
  state.notice = key ? typeof key === "string" && Object.hasOwn(i18n.catalogs.en, key) ? { key, values } : { error: key } : null;
  renderNotice();
}
function renderNotice() {
  const item = state.notice;
  $("notice").textContent = item ? item.key ? t(item.key, { ...item.values, error: item.values.error ? errorText(item.values.error) : "" }) : errorText(item.error) : "";
  $("notice").hidden = !item;
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
  if (!response.ok) throw new Error(rawErrorText(payload.error || payload));
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
    box.append(node("p", "muted", t("app.repositoryEmpty")));
    setBusy(state.busy);
    return;
  }
  const source = repository.source || {};
  box.append(node("p", "mono", source.location || repository.repository_id));
  const version = node("div", "repo-version");
  version.append(node("span", "mono", `commit ${text(source.commit)}`));
  version.append(node("span", "muted", t("app.fileCount", { count: text(repository.file_count) })));
  box.append(version);
  if (source.working_tree) box.append(node("p", "muted", t("app.workingTree")));
  const stages = node("div", "repo-stages");
  const prepared = repository.stages || repository.preparation?.stages || {};
  for (const [key, name] of [["index", t("app.index")], ["vectors", t("app.vectors")], ["graph", t("app.graph")]]) {
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
  renderRepositoryOptions(selected);
  $("import-details").open = !$("repository-select").value;
  renderRepository();
}
function renderRepositoryOptions(selected = $("repository-select").value, autoSelect = true) {
  const select = $("repository-select");
  select.replaceChildren(node("option", "", t("app.selectRepository")));
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
  else if (autoSelect && state.repositories.length) select.value = state.repositories.find((row) => row.status !== "unreadable")?.repository_id || "";
}
function renderJob(job) {
  state.job = job;
  $("job-panel").hidden = false;
  const outcome = job.result?.preparation?.status || job.result?.status;
  $("job-status").textContent = job.status === "completed" && ["partial", "failed"].includes(outcome) ? t("app.taskFinished", { status: statusText(outcome) }) : statusText(job.status);
  $("job-id").textContent = t("app.taskId", { id: job.job_id });
  const progress = job.progress || {};
  const detail = progress.detail || {};
  const box = $("job-stages");
  box.replaceChildren();
  if (progress.phase === "import") {
    const seen = new Set((detail.events || []).map((event) => event.status));
    for (const [key, name] of [["validating", t("app.validateSource")], ["downloading", t("app.downloadSource")], ["snapshotting", t("app.saveSnapshot")]]) {
      if (seen.has(key)) box.append(stage(name, detail.status === key ? "running" : "completed"));
    }
    if (detail.cache_hit) box.append(stage(t("app.sourceCache"), "reused"));
  } else if (progress.phase === "prepare") {
    for (const [key, name] of [["index", t("app.index")], ["vectors", t("app.prepareVectors")], ["graph", t("app.graph")]]) {
      box.append(stage(name, detail.stages?.[key]?.status));
    }
  } else if (["preview", "generation"].includes(progress.phase)) {
    for (const row of detail.results || []) box.append(stage(strategies.find(([key]) => key === row.strategy)?.[1] || row.strategy, row.status));
  }
  if (!box.childElementCount) box.append(stage(["import", "prepare", "preview", "generation"].includes(job.kind) ? t("app.job_" + job.kind) : job.kind || t("app.task"), job.status));
  const errors = [];
  if (job.error) errors.push(errorText(job.error));
  if (job.recovery_warning) errors.push(errorText(job.recovery_warning));
  if (detail.error) errors.push(errorText(detail.error));
  if (detail.cleanup_error) errors.push(errorText(detail.cleanup_error));
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
    if (state.notice?.key === "app.noticePoll") notice();
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
    notice("app.noticePoll", { error });
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
    notice("app.noticeSubmit", { error });
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
function renderPlan(plan, resetApproval = true) {
  state.plan = plan;
  $("plan-content").hidden = false;
  if (resetApproval) {
    $("generation-confirm").checked = false;
    $("generation-budget").value = Math.max(0.01, Math.ceil(plan.estimated_cost_usd * 100) / 100).toFixed(2);
  }
  const summary = $("plan-summary");
  summary.replaceChildren();
  metric(summary, t("app.answerModel"), plan.model);
  metric(summary, t("app.savedQuestion"), plan.question);
  metric(summary, t("app.requestLimit"), `${text(plan.request_limit)} / ${text(plan.judge_calls)}`);
  metric(summary, t("app.totalEstimate"), money(plan.estimated_cost_usd));
  metric(summary, t("app.rates"), `US$${text(plan.pricing?.input_per_million)} / US$${text(plan.pricing?.output_per_million)}`);
  metric(summary, t("app.priceDate"), plan.pricing?.as_of);
  const rows = $("plan-rows");
  rows.replaceChildren();
  for (const item of plan.strategies || []) {
    const row = node("tr");
    for (const value of [strategies.find(([key]) => key === item.strategy)?.[1] || item.strategy, statusText(item.status), text(item.estimated_input_tokens), text(item.max_output_tokens), money(item.estimated_cost_usd)]) row.append(node("td", "", value));
    rows.append(row);
  }
  $("plan-note").textContent = t("app.planNote", { plan: plan.plan_id, preview: plan.preview_run_id });
  $("key-status").textContent = state.generation?.key_ready ? t("app.keyReady") : t("app.keyMissing");
  $("generation-confirm-label").textContent = t("app.confirmPlan", { model: plan.model, generation: plan.request_limit, judges: plan.judge_calls });
  if (resetApproval) history.replaceState(null, "", `#plan=${plan.plan_id}`);
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
  } catch (error) { notice("app.noticePlan", { error }); }
  finally { setBusy(false); }
}
function renderGenerationSummary(run, current) {
  const box = $("generation-summary");
  box.replaceChildren();
  box.hidden = run.mode === "context_preview";
  if (box.hidden) return;
  const synthetic = run.mode === "offline_test";
  box.append(node("h3", "", synthetic ? t("app.syntheticHeading") : current ? t("app.currentHeading") : t("app.historicalHeading")));
  box.append(node("p", "field-help", synthetic ? t("app.syntheticNote") : t("app.generationNote")));
  const summary = run.generation?.summary || {};
  const metrics = node("dl", "plan-summary");
  metric(metrics, t("app.configuredModel"), run.settings?.answer_model || run.generation?.settings?.model || run.generation?.model);
  metric(metrics, t("app.attemptsResponses"), `${text(summary.calls_started)} / ${text(summary.responses_received)}`);
  metric(metrics, t("app.unknownNotRun"), `${text(summary.outcome_unknown)} / ${text(summary.not_run)}`);
  metric(metrics, t("app.realCalls"), text(run.api_calls));
  box.append(metrics);
  box.append(node("p", "field-help", t("app.usageNote")));
  if (run.parent_preview_run_id) {
    const button = node("button", "button secondary", t("app.openPreview"));
    button.type = "button";
    button.addEventListener("click", () => openRun(run.parent_preview_run_id).catch((error) => notice(error)));
    box.append(button);
  }
}
function renderAnswer(body, row, name, evidence) {
  if (state.run?.mode === "context_preview") {
    body.append(node("p", "preview-label", row.qa ? t("app.previewNote") : t("app.previewMissing")));
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
        button.setAttribute("aria-label", t("app.citationLabel", { strategy: name, id, path: source?.path || t("app.sourceMissing") }));
        if (source) button.addEventListener("click", () => showSource(source, row.hits?.find((hit) => hit.chunk_id === source.chunk_id), name));
        citations.append(button);
      }
      item.append(citations);
      list.append(item);
    }
    body.append(list);
  } else {
    const messages = { insufficient_context: row.qa?.model_called ? t("app.abstention") : t("app.noModelEvidence"), outcome_unknown: t("app.unknownResponse"), not_run: t("app.notRequested"), provider_error: t("app.providerFailure"), invalid_answer: t("app.invalidAnswer") };
    body.append(node("p", "preview-label", Object.hasOwn(messages, row.status) ? messages[row.status] : t("app.answerMissing")));
  }
  if (row.qa?.raw_output !== null && row.qa?.raw_output !== undefined) {
    const raw = node("details", "extra-metrics");
    raw.append(node("summary", "", t("app.rawOutput")), node("pre", "", row.qa.raw_output));
    body.append(raw);
  }
}
function renderSourceLabels() {
  if (!state.sourceView) return;
  const { source, strategyName } = state.sourceView;
  $("source-caption").textContent = source.id ? t("app.sourceCaptionEvidence", { strategy: strategyName, id: source.id }) : t("app.sourceCaptionRank", { strategy: strategyName, rank: text(source.rank) });
  $("source-heading").textContent = source.path || t("app.unknownPath");
  $("source-name").textContent = source.qualified_name || t("app.unknownSymbol");
  $("source-range").textContent = t("app.sourceRange", { start: text(source.start_line), end: text(source.end_line), truncated: source.truncated ? t("app.truncated") : "" });
  if (!String(source.text ?? "").trim() && $("source-code").querySelector("p")) $("source-code").querySelector("p").textContent = t("app.sourceTextMissing");
}
function showSource(source, hit, strategyName) {
  state.sourceView = { source, hit, strategyName };
  renderSourceLabels();
  const code = $("source-code");
  code.replaceChildren();
  const lines = String(source.text ?? "").split("\n");
  if (lines.at(-1) === "") lines.pop();
  lines.forEach((line, index) => {
    const row = node("div", "code-line");
    row.append(node("span", "line-number", Number.isInteger(source.start_line) ? source.start_line + index : "?"), node("code", "line-text", line || " "));
    code.append(row);
  });
  if (!lines.length) code.append(node("p", "muted", t("app.sourceTextMissing")));
  $("source-provenance").textContent = JSON.stringify({ chunk_id: source.chunk_id, symbol_id: source.symbol_id, rank: hit?.rank ?? null, score: hit?.score ?? null, components: hit?.components ?? null, provenance: hit?.provenance ?? null }, null, 2);
  $("source-details").open = false;
  $("source-dialog").showModal();
}
function renderCard(key, name, description, row) {
  const card = node("article", "strategy-card");
  card.dataset.strategy = key;
  const header = node("div", "card-header");
  header.append(node("h3", "", name), node("p", "", t(description)), node("span", `pill card-status ${row?.status || "failed"}`, row ? statusText(row.status) : t("app.resultMissing")));
  card.append(header);
  const body = node("div", "card-body");
  card.append(body);
  if (!row) { body.append(node("p", "error-text", t("app.rowMissing"))); return card; }
  if (row.error) {
    const raw = rawErrorText(row.error);
    const message = raw.startsWith("vectors resource is unavailable") ? t("app.vectorsUnavailable") : t("app.strategyFailure");
    body.append(node("p", "error-text", message));
    const failure = node("details", "extra-metrics");
    failure.append(node("summary", "", t("app.rawError")), node("pre", "", raw));
    body.append(failure);
  }
  const evidence = row.qa?.context?.evidence || [];
  renderAnswer(body, row, name, evidence);
  const grid = node("dl", "metric-grid");
  metric(grid, t("app.retrievalTime"), ms(row.timing_ms?.retrieval));
  metric(grid, t("app.contextBytes"), text(row.qa?.context?.budget?.used_context_bytes));
  metric(grid, t("app.generationTime"), ms(row.timing_ms?.generation));
  metric(grid, t("app.tokens"), `${text(row.tokens?.input)} / ${text(row.tokens?.output)}`);
  metric(grid, t("app.cost"), money(row.cost?.estimated_usd));
  metric(grid, state.run?.mode === "offline_test" ? t("app.testCalls") : t("app.modelAttempts"), text(row.cost?.model_calls));
  body.append(grid);
  body.append(node("h4", "card-subhead", t("app.contextCount", { count: evidence.length })));
  const chips = node("div", "evidence-chips");
  for (const source of evidence) {
    const button = node("button", "evidence-button", source.id);
    button.type = "button";
    button.title = `${source.path}:${source.start_line}–${source.end_line}`;
    button.setAttribute("aria-label", t("app.evidenceLabel", { strategy: name, id: source.id, path: source.path }));
    button.addEventListener("click", () => showSource(source, row.hits?.find((hit) => hit.chunk_id === source.chunk_id), name));
    chips.append(button);
  }
  if (!evidence.length) chips.append(node("p", "small muted", t("app.noContextEvidence")));
  body.append(chips);
  const checks = row.qa?.automatic_checks;
  const checkNames = { evidence_ids_valid: t("app.evidenceIds"), paths_valid: t("app.paths"), line_ranges_valid: t("app.lines"), citation_ids_valid: t("app.citationIds") };
  body.append(node("p", "automatic-note", checks ? t("app.checksNote", { checks: Object.entries(checks).filter(([, value]) => typeof value === "boolean").map(([key, value]) => t("app.checkResult", { name: Object.hasOwn(checkNames, key) ? checkNames[key] : key, result: value ? t("app.checkPassed") : t("app.checkFailed") })).join(" · ") || t("app.seeDetails") }) : t("app.checksUnknown")));
  body.append(node("h4", "card-subhead", t("app.hitCount", { count: row.hits?.length ?? 0 })));
  for (const hit of row.hits || []) {
    const button = node("button", "hit-button");
    button.type = "button";
    button.append(node("span", "hit-title", `#${text(hit.rank)}  ${hit.qualified_name || hit.path}`));
    button.append(node("span", "hit-path", `${hit.path} · L${hit.start_line}–${hit.end_line}`));
    button.append(node("span", "hit-score", `score ${typeof hit.score === "number" ? hit.score.toFixed(6) : t("app.unknown")}${hit.provenance?.length ? t("app.relationCount", { count: hit.provenance.length }) : ""}`));
    button.addEventListener("click", () => showSource(hit, hit, name));
    body.append(button);
  }
  const details = node("details", "extra-metrics");
  details.append(node("summary", "", t("app.moreInfo")), node("pre", "", JSON.stringify({ timing_ms: row.timing_ms, tokens: row.tokens, cost: row.cost, ranked_candidates: row.ranked_candidates, structure_stats: row.structure_stats, automatic_checks: checks ?? null, llm_assessment: row.qa?.llm_assessment ?? null, provider: row.qa?.provider ?? null }, null, 2)));
  body.append(details);
  return card;
}
function renderRun(run, current, resetPlan = true) {
  state.run = run;
  state.runCurrent = current;
  if (resetPlan) {
    state.plan = null;
    $("plan-content").hidden = true;
    $("generation-confirm").checked = false;
  }
  $("generation-panel").hidden = run.mode !== "context_preview" || run.status === "running";
  $("empty-results").hidden = true;
  $("results-section").hidden = false;
  $("run-mode").textContent = t(current ? "app.runCurrent" : "app.runHistorical", { mode: modeText(run.mode) });
  $("comparison-note").textContent = t(run.mode === "context_preview" ? "app.comparisonPreview" : "app.comparisonAnswers") + t("app.comparisonLimits");
  $("run-question").textContent = run.question;
  $("run-meta").replaceChildren(node("span", "", `${date(run.created_at)} · ${statusText(run.status)}`), node("span", "mono", `commit ${text(run.resources?.source?.commit)}`), node("span", "mono", `run ${run.run_id}`), node("span", "", t("app.elapsed", { duration: ms(run.elapsed_ms) })));
  $("run-meta").prepend(node("span", "", t("app.sourceLocation", { location: text(run.resources?.source?.location) })));
  renderGenerationSummary(run, current);
  $("strategy-grid").replaceChildren(...strategies.map(([key, name, description]) => renderCard(key, name, description, run.results?.find((row) => row.strategy === key))));
  $("run-config").textContent = JSON.stringify({ mode: run.mode, settings: run.settings, generation: run.generation, source: run.resources?.source, snapshot_id: run.resources?.snapshot_id, resource_id: run.resources?.resource_id, index_config: run.resources?.index_config, encoder_mode: run.encoder_mode, model_spec: run.resources?.model_spec, resolver_config: run.resources?.resolver_config, shared_setup: run.shared_setup, relevance_labels: run.relevance_labels, benchmark_metrics: run.benchmark_metrics }, null, 2);
  setBusy(state.busy);
}
async function openRun(id, current = false) {
  if (!/^[0-9a-f]{32}$/.test(id)) throw new Error("app.invalidRun");
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
  if (!/^[0-9a-f]{32}$/.test(id)) throw new Error("app.invalidPlan");
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
    description.append(node("h3", "", row.question || t("app.unreadableRecord")), node("p", "", t("app.historyMeta", { date: date(row.created_at), status: statusText(row.status), mode: modeText(row.mode) })), node("p", "mono", `run ${row.run_id} · ${repository?.source?.location || `repository ${short(row.repository_id)}`}`));
    if (row.error) description.append(node("p", "error-text", errorText(row.error)));
    const button = node("button", "button secondary", t("app.openRecord"));
    button.type = "button";
    button.disabled = row.status === "unreadable";
    button.addEventListener("click", () => openRun(row.run_id).catch((error) => notice(error)));
    item.append(description, button);
    box.append(item);
  }
  if (!records.length) box.append(node("p", "empty-state", state.history.length ? t("app.noMatchingHistory") : t("app.emptyHistory")));
}
async function refreshHistory() {
  state.history = await api("/api/history");
  $("history-count").textContent = state.history.length;
  renderHistory();
}
$("nav-workbench").addEventListener("click", () => showView("workbench"));
$("nav-history").addEventListener("click", () => { showView("history"); refreshHistory().catch((error) => notice(error)); });
$("refresh-repositories").addEventListener("click", () => refreshRepositories().catch((error) => notice(error)));
$("refresh-history").addEventListener("click", () => refreshHistory().catch((error) => notice(error)));
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
  openSavedLocation().catch((error) => notice(error));
});

function validateField(field) {
  field.setCustomValidity("");
  const validity = field.validity;
  let message = "";
  if (validity.valueMissing) message = t("app.validationRequired");
  else if (validity.badInput) message = t("app.validationNumber");
  else if (validity.rangeUnderflow) message = t("app.validationMin", { min: field.min });
  else if (validity.rangeOverflow) message = t("app.validationMax", { max: field.max });
  else if (validity.stepMismatch) message = t("app.validationStep", { step: field.step });
  else if (validity.tooLong) message = t("app.validationLength", { max: field.maxLength });
  else if (!validity.valid) message = t("app.validationInvalid");
  field.setCustomValidity(message);
}
for (const field of document.querySelectorAll("input, textarea, select")) {
  field.addEventListener("invalid", () => validateField(field));
  field.addEventListener("input", () => field.setCustomValidity(""));
  field.addEventListener("change", () => field.setCustomValidity(""));
}
window.addEventListener("workbench-language-change", () => {
  // Repaint cached data only. Keep user input, consent, selection and open evidence.
  const resultsHidden = $("results-section").hidden;
  const emptyHidden = $("empty-results").hidden;
  const openDetails = [...$("strategy-grid").querySelectorAll("details")].map(item => item.open);
  const gridScroll = $("strategy-grid").scrollLeft;
  renderRepositoryOptions($("repository-select").value, false);
  renderRepository();
  renderHistory();
  if (state.job) renderJob(state.job);
  if (state.run) renderRun(state.run, state.runCurrent, false);
  if (state.plan) renderPlan(state.plan, false);
  $("results-section").hidden = resultsHidden;
  $("empty-results").hidden = emptyHidden;
  [...$("strategy-grid").querySelectorAll("details")].forEach((item, index) => { item.open = openDetails[index] || false; });
  $("strategy-grid").scrollLeft = gridScroll;
  renderSourceLabels();
  renderNotice();
  for (const field of document.querySelectorAll("input, textarea, select")) {
    if (field.validity.customError) validateField(field);
  }
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
  } catch (error) { notice("app.noticeConnection", { error }); }
}
start();
