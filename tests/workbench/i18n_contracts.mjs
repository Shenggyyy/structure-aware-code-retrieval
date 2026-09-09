// Run the shipped translation runtime in an isolated browser-shaped VM.
// No DOM libraries, network, model services, or browser state are required.
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import vm from "node:vm";
import test from "node:test";

const directory = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../../src/structure_aware_retrieval/workbench/static");
const source = fs.readFileSync(path.join(directory, "i18n.js"), "utf8");
const html = fs.readFileSync(path.join(directory, "index.html"), "utf8");
const app = fs.readFileSync(path.join(directory, "app.js"), "utf8");
const storageKey = "sacr.workbench.language";

class Element {
  constructor(attributes = {}, text = "") {
    this.attributes = new Map(Object.entries(attributes));
    this.textContent = text;
    this.children = [];
    this.value = "";
    this.listeners = new Map();
    this.validity = { valid: true };
    this.classList = { toggle() {} };
    this.scrollLeft = 0;
  }
  getAttribute(name) { return this.attributes.get(name) ?? null; }
  hasAttribute(name) { return this.attributes.has(name); }
  setAttribute(name, value) { this.attributes.set(name, String(value)); }
  removeAttribute(name) { this.attributes.delete(name); }
  append(...items) { this.children.push(...items); }
  prepend(...items) { this.children.unshift(...items); }
  replaceChildren(...items) { this.children = [...items]; }
  get firstChild() { return this.children[0] ?? null; }
  get childElementCount() { return this.children.length; }
  setCustomValidity(message) { this.validity.customError = Boolean(message); }
  scrollIntoView() {}
  showModal() { this.open = true; }
  close() { this.open = false; }
  get dataset() {
    return Object.fromEntries([...this.attributes].filter(([key]) => key.startsWith("data-")).map(([key, value]) => [key.slice(5).replace(/-([a-z])/g, (_, letter) => letter.toUpperCase()), value]));
  }
  matches(selector) {
    return selector.split(",").some(part => {
      const attribute = part.trim().match(/^\[([^=\]]+)(?:=["']?([^\]"']+)["']?)?\]$/);
      if (attribute) return this.hasAttribute(attribute[1]) && (attribute[2] === undefined || this.getAttribute(attribute[1]) === attribute[2]);
      if (part.trim().startsWith("#")) return this.getAttribute("id") === part.trim().slice(1);
      if (part.trim().startsWith(".")) return this.className?.split(" ").includes(part.trim().slice(1)) ?? false;
      return this.tagName?.toLowerCase() === part.trim();
    });
  }
  querySelectorAll(selector) {
    return this.children.flatMap(child => [...(child.matches(selector) ? [child] : []), ...child.querySelectorAll(selector)]);
  }
  querySelector(selector) { return this.querySelectorAll(selector)[0] ?? null; }
  addEventListener(name, callback) { this.listeners.set(name, callback); }
  set innerHTML(_value) { throw new Error("Translation must use textContent, never innerHTML"); }
}

function runtime({ stored, languages, language = "en-US", blockedStorage = false, elements = [], fetch: suppliedFetch } = {}) {
  const values = new Map(stored === undefined ? [] : [[storageKey, stored]]);
  const events = [];
  const listeners = new Map();
  let networkCalls = 0;
  const document = new Element();
  document.children = elements;
  document.documentElement = new Element();
  document.readyState = "complete";
  document.getElementById = id => document.querySelector(`#${id}`);
  document.createElement = tag => Object.assign(new Element(), { tagName: tag });
  document.addEventListener = (_name, callback) => callback();
  const context = {
    document,
    navigator: { languages, language },
    console,
    CustomEvent: class { constructor(type, detail) { this.type = type; this.detail = detail?.detail; } },
    AbortSignal,
    setTimeout,
    clearTimeout,
    location: { hash: "" },
    history: { replaceState() {} },
    dispatchEvent: event => {
      events.push(event);
      for (const callback of listeners.get(event.type) ?? []) callback(event);
      return true;
    },
    addEventListener(name, callback) { listeners.set(name, [...(listeners.get(name) ?? []), callback]); },
    fetch(...args) {
      networkCalls += 1;
      if (suppliedFetch) return suppliedFetch(...args);
      throw new Error("Changing language must never use the network");
    },
  };
  Object.defineProperty(context, "localStorage", {
    get() {
      if (blockedStorage) throw new Error("Storage is disabled");
      return {
        getItem: key => values.get(key) ?? null,
        setItem: (key, value) => values.set(key, value),
      };
    },
  });
  context.window = context;
  vm.createContext(context);
  vm.runInContext(source, context, { filename: "i18n.js", timeout: 1000 });
  return { api: context.WorkbenchI18n, document, context, events, values, networkCalls: () => networkCalls };
}

test("language preference uses saved choice, then the first browser language, then English", () => {
  for (const [options, expected] of [
    [{ stored: "en", languages: ["zh-TW"] }, "en"],
    [{ stored: "zh-CN", languages: ["en-US"] }, "zh-CN"],
    [{ stored: "invalid", languages: ["zh-HK"] }, "zh-CN"],
    [{ languages: ["en-AU", "zh-CN"] }, "en"],
    [{ languages: ["fr-FR", "zh-CN"] }, "en"],
    [{ language: "zh-CN" }, "zh-CN"],
    [{ language: "de-DE" }, "en"],
  ]) {
    const loaded = runtime(options);
    assert.equal(loaded.api.getLanguage(), expected);
    assert.equal(loaded.document.documentElement.lang, expected);
  }
});

test("disabled localStorage does not prevent initialization or changing language", () => {
  const loaded = runtime({ blockedStorage: true, languages: ["zh-CN"] });
  assert.equal(loaded.api.getLanguage(), "zh-CN");
  loaded.api.setLanguage("en");
  assert.equal(loaded.api.getLanguage(), "en");
  assert.equal(loaded.document.documentElement.lang, "en");
  assert.equal(loaded.networkCalls(), 0);
});

test("changing language persists the explicit choice and emits an event without networking", () => {
  const loaded = runtime({ languages: ["en-US"] });
  loaded.api.setLanguage("zh-CN");
  assert.equal(loaded.values.get(storageKey), "zh-CN");
  assert.equal(loaded.document.documentElement.lang, "zh-CN");
  assert.equal(loaded.events.at(-1)?.type, "workbench-language-change");
  loaded.api.setLanguage("en");
  assert.equal(loaded.values.get(storageKey), "en");
  assert.equal(loaded.networkCalls(), 0);
});

test("an unsupported language cannot overwrite the current or stored preference", () => {
  const loaded = runtime({ stored: "zh-CN" });
  try { loaded.api.setLanguage("unsupported"); } catch (error) { assert.ok(error instanceof Error || error.name === "TypeError"); }
  assert.equal(loaded.api.getLanguage(), "zh-CN");
  assert.equal(loaded.values.get(storageKey), "zh-CN");
  assert.equal(loaded.document.documentElement.lang, "zh-CN");
  assert.equal(loaded.networkCalls(), 0);
});

test("catalogs contain matching nonempty keys and interpolation parameters", () => {
  const { api } = runtime();
  const english = api.catalogs.en;
  const chinese = api.catalogs["zh-CN"];
  assert.deepEqual(Object.keys(english).sort(), Object.keys(chinese).sort());
  assert.ok(Object.keys(english).length > 50, "The whole workbench must be translated");
  const parameters = text => [...text.matchAll(/\{(\w+)\}/g)].map(match => match[1]).sort();
  for (const key of Object.keys(english)) {
    assert.equal(typeof english[key], "string", key);
    assert.equal(typeof chinese[key], "string", key);
    assert.ok(english[key].trim() && chinese[key].trim(), key);
    assert.deepEqual(parameters(english[key]), parameters(chinese[key]), key);
  }
});

test("all static markup and literal dynamic translation keys exist in both catalogs", () => {
  const { api } = runtime();
  const staticKeys = [...html.matchAll(/data-i18n(?:-placeholder|-aria-label|-title)?=["']([^"']+)["']/g)].map(match => match[1]);
  const dynamicKeys = [...app.matchAll(/["'](app\.\w+)["'](?!\s*\+)/g)].map(match => match[1]);
  dynamicKeys.push(...["import", "prepare", "preview", "generation"].map(kind => `app.job_${kind}`));
  assert.ok(staticKeys.length > 30);
  assert.ok(dynamicKeys.length > 30);
  for (const key of new Set([...staticKeys, ...dynamicKeys])) {
    assert.ok(Object.hasOwn(api.catalogs.en, key), key);
    assert.ok(Object.hasOwn(api.catalogs["zh-CN"], key), key);
  }
  const translationsScript = html.indexOf('src="/i18n.js"');
  const applicationScript = html.indexOf('src="/app.js"');
  assert.ok(translationsScript >= 0 && translationsScript < applicationScript);
});

test("translation uses text and safe attributes, leaving source and user values unchanged", () => {
  const { api } = runtime();
  const key = Object.keys(api.catalogs.en).find(value => value.startsWith("ui.") && !api.catalogs.en[value].includes("{"));
  assert.ok(key);
  const translated = new Element({ "data-i18n": key });
  const input = new Element({ "data-i18n-placeholder": key, "data-i18n-aria-label": key, "data-i18n-title": key });
  input.value = "问题 <script>fetch('/api/generate')</script>";
  const sourceCode = new Element({}, "def 中文符号(): return '<b>S1</b>'");
  const rawAnswer = new Element({}, "Original model answer with S1 citation.");
  const loaded = runtime({ elements: [translated, input, sourceCode, rawAnswer] });
  const originalValue = input.value;
  for (const language of ["zh-CN", "en"]) {
    loaded.api.setLanguage(language);
    loaded.api.apply(loaded.document);
    assert.equal(translated.textContent, loaded.api.t(key));
    assert.equal(input.getAttribute("placeholder"), loaded.api.t(key));
    assert.equal(input.getAttribute("aria-label"), loaded.api.t(key));
    assert.equal(input.getAttribute("title"), loaded.api.t(key));
    assert.equal(input.value, originalValue);
    assert.equal(sourceCode.textContent, "def 中文符号(): return '<b>S1</b>'");
    assert.equal(rawAnswer.textContent, "Original model answer with S1 citation.");
  }
  assert.equal(loaded.networkCalls(), 0);
});

test("interpolation remains literal and single-pass, and unknown keys remain visible", () => {
  const { api } = runtime();
  for (const language of ["en", "zh-CN"]) {
    api.setLanguage(language);
    const key = Object.keys(api.catalogs.en).find(value => /\{\w+\}/.test(api.catalogs.en[value]));
    assert.ok(key, "Dynamic templates must exist");
    const template = api.catalogs[language][key];
    const names = [...template.matchAll(/\{(\w+)\}/g)].map(match => match[1]);
    const payload = `<img src=x onerror=fetch('/api/generate')>{${names[0]}}`;
    const values = Object.fromEntries(names.map(name => [name, payload]));
    assert.equal(api.t(key, values), template.replace(/\{(\w+)\}/g, () => payload));
    for (const missing of ["missing.translation.key", "__proto__", "toString"]) {
      assert.equal(api.t(missing), missing);
    }
  }
});

test("a missing Chinese key falls back to English without hiding an unknown key", () => {
  const { api } = runtime({ stored: "zh-CN" });
  const key = "app.answerModel";
  delete api.catalogs["zh-CN"][key];
  assert.equal(api.t(key), api.catalogs.en[key]);
  assert.equal(api.t("app.not_defined"), "app.not_defined");
});

const criticalErrors = [
  "Confirm the exact model recorded in this generation plan",
  "Budget must be finite, positive, and cover the full plan estimate",
  "Set OPENAI_API_KEY in the server environment before generation",
  "The configured API key contains invalid characters",
  "The preview changed after the generation plan was frozen",
  "This generation plan was already started; no retry",
  "Use a public HTTPS Git URL without credentials, redirects, or extra ports",
  "Git hostname resolves to a non-public address",
  "Local source must not be a link, junction, or network share",
  "Local source must be a directory outside the workbench workspace",
  "Repository contains no included Python source files",
];

test("critical approval and import failures have direct bilingual explanations", () => {
  const { api } = runtime();
  for (const message of criticalErrors) {
    assert.ok(Object.hasOwn(api.errorKeys, message), message);
  }
  for (const [message, key] of Object.entries(api.errorKeys)) {
    assert.equal(api.catalogs.en[key], message);
    assert.match(api.catalogs["zh-CN"][key], /\p{Script=Han}/u, message);
  }
});

test("the application repaints archived plans and answers without fetching or altering consent or source", { skip: !process.env.SACR_I18N_FIXTURES }, async () => {
  const records = JSON.parse(fs.readFileSync(process.env.SACR_I18N_FIXTURES, "utf8"));
  const run = records.find(record => record.mode === "model_generation");
  const preview = records.find(record => record.mode === "context_preview");
  const plan = records.find(record => record.plan_id && !record.mode);
  assert.ok(run && preview && plan, "Use the preserved live acceptance archive");
  const originalRecords = JSON.stringify(records);
  const repository = { repository_id: run.repository_id, status: "ready", source: run.resources.source, file_count: 10 };
  const elements = [...html.matchAll(/<([a-z][a-z0-9]*)\b([^>]*\bid="[^"]+"[^>]*)>/g)].map(([, tag, attributes]) => {
    const values = Object.fromEntries([...attributes.matchAll(/([\w-]+)="([^"]*)"/g)].map(match => [match[1], match[2]]));
    return Object.assign(new Element(values), { tagName: tag, hidden: /\bhidden\b/.test(attributes) });
  });
  const loaded = runtime({ elements, fetch: async (url, options) => {
    assert.equal(options?.method, undefined, "Only read-only startup requests are allowed");
    const payloads = {
      "/api/session": { csrf_token: "offline-session", generation: { key_ready: false } },
      "/api/repositories": [repository],
      "/api/history": [run, preview],
      "/api/jobs": [],
    };
    assert.ok(Object.hasOwn(payloads, url), `Unexpected request: ${url}`);
    return { ok: true, json: async () => payloads[url] };
  } });
  vm.runInContext(app, loaded.context, { filename: "app.js", timeout: 1000 });
  await new Promise(resolve => setImmediate(resolve));
  assert.equal(loaded.networkCalls(), 4);
  assert.equal(loaded.document.getElementById("notice").textContent, "");
  assert.equal(vm.runInContext("statusText('__proto__')", loaded.context), "__proto__");
  assert.equal(vm.runInContext("modeText('toString')", loaded.context), loaded.api.t("app.unknownMode"));
  const get = id => loaded.document.getElementById(id);
  const flatten = element => [element.textContent, ...element.children.map(flatten)].join(" ");
  for (const status of ["failed", "interrupted"]) {
    loaded.context.failedImport = {
      kind: "import", job_id: "offline-import", status,
      progress: { phase: "import", detail: {
        status, events: [{ status: "validating" }, { status: "downloading" }, { status }]
      } }
    };
    vm.runInContext("renderJob(failedImport);", loaded.context);
    for (const language of ["zh-CN", "en"]) {
      loaded.api.setLanguage(language);
      const stages = get("job-stages").children.map(element => element.textContent);
      assert.deepEqual(stages, [
        `${loaded.api.t("app.validateSource")} · ${loaded.api.t("app.status_completed")}`,
        `${loaded.api.t("app.downloadSource")} · ${loaded.api.t(`app.status_${status}`)}`
      ], "The last attempted import phase must retain its terminal failure");
    }
  }
  loaded.context.archivedRun = run;
  loaded.context.archivedPreview = preview;
  loaded.context.archivedPlan = plan;
  vm.runInContext("renderRun(archivedPreview, false); renderPlan(archivedPlan);", loaded.context);
  assert.equal(get("generation-confirm").checked, false);
  assert.equal(get("generate-button").disabled, true);
  get("question").value = "未提交的问题 <script>fetch('/api/generate')</script>";
  get("source").value = "https://example.org/source.git";
  get("generation-budget").value = "0.10";
  get("generation-confirm").checked = true;
  get("history-search").value = run.question;
  const inputBefore = ["question", "source", "generation-budget", "repository-select", "history-search"].map(id => get(id).value);
  for (const language of ["zh-CN", "en"]) {
    loaded.api.setLanguage(language);
    assert.deepEqual(["question", "source", "generation-budget", "repository-select", "history-search"].map(id => get(id).value), inputBefore);
    assert.equal(get("generation-confirm").checked, true);
    assert.equal(loaded.networkCalls(), 4);
    assert.equal(JSON.stringify(records), originalRecords);
    assert.ok(flatten(get("plan-summary")).includes(plan.model));
  }
  get("repository-select").value = "";
  vm.runInContext("renderRepository();", loaded.context);
  assert.equal(get("preview-button").disabled, true);
  loaded.api.setLanguage("zh-CN");
  assert.equal(get("repository-select").value, "", "An explicit empty selection must stay empty");
  assert.equal(get("preview-button").disabled, true);
  get("repository-select").value = repository.repository_id;
  loaded.api.setLanguage("en");
  vm.runInContext("renderRun(archivedRun, false); showSource(archivedRun.results[0].qa.context.evidence[0], archivedRun.results[0].hits[0], 'BM25');", loaded.context);
  get("strategy-grid").querySelectorAll("details")[0].open = true;
  get("strategy-grid").scrollLeft = 127;
  const originalCode = flatten(get("source-code"));
  const originalProvenance = get("source-provenance").textContent;
  for (const language of ["zh-CN", "en"]) {
    loaded.api.setLanguage(language);
    assert.equal(get("source-dialog").open, true);
    assert.equal(flatten(get("source-code")), originalCode);
    assert.equal(get("source-provenance").textContent, originalProvenance);
    assert.equal(get("strategy-grid").scrollLeft, 127);
    assert.equal(get("strategy-grid").querySelectorAll("details")[0].open, true);
    for (const row of run.results) {
      assert.ok(flatten(get("strategy-grid")).includes(row.qa.answer.claims[0].text));
    }
    assert.equal(get("generation-confirm").checked, false, "Opening a different saved result clears consent");
    assert.equal(loaded.networkCalls(), 4);
    assert.equal(JSON.stringify(records), originalRecords);
  }
  for (const message of criticalErrors) {
    loaded.context.originalError = message;
    vm.runInContext("notice(new Error(originalError));", loaded.context);
    for (const language of ["zh-CN", "en"]) {
      loaded.api.setLanguage(language);
      assert.equal(get("notice").textContent, loaded.api.catalogs[language][loaded.api.errorKeys[message]]);
      assert.equal(loaded.networkCalls(), 4);
    }
  }
  const diagnostic = "Unknown provider diagnostic <img src=x onerror=fetch('/api/generate')>{model}";
  for (const language of ["zh-CN", "en"]) {
    loaded.api.setLanguage(language);
    const unusual = vm.runInContext(`renderCard("bm25", "BM25", "app.unknown", {
      status: "toString", qa: { automatic_checks: { ["__proto__"]: true } }
    })`, loaded.context);
    assert.ok(flatten(unusual).includes(loaded.api.t("app.answerMissing")));
    assert.ok(unusual.querySelector(".automatic-note").textContent.includes("__proto__"));
    assert.ok(!flatten(unusual).includes("[native code]"));
  }
  loaded.context.originalError = diagnostic;
  vm.runInContext("notice(new Error(originalError));", loaded.context);
  for (const language of ["zh-CN", "en"]) {
    loaded.api.setLanguage(language);
    assert.ok(get("notice").textContent.includes(diagnostic), "Unknown diagnostics remain literal text");
    assert.equal(loaded.networkCalls(), 4);
    assert.equal(JSON.stringify(records), originalRecords);
  }
});
