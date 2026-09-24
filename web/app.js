"use strict";

// Credentials stay in this tab's session storage. They are never placed in a URL.
const STORAGE_KEY = "liqvera.local-demo.v1";
const INSTRUMENT_ID = "hyperliquid:BTC:perpetual";
const $ = (id) => document.getElementById(id);
const form = $("request-form");
let session = null;
let activeRun = null;
let activeReport = null;
let capabilities = null;
let busy = false;

function randomHex() {
  const bytes = new Uint8Array(32);
  crypto.getRandomValues(bytes);
  return Array.from(bytes, (byte) => byte.toString(16).padStart(2, "0")).join("");
}

function loadSession() {
  const raw = sessionStorage.getItem(STORAGE_KEY);
  if (!raw) return { capability: randomHex(), runId: null, request: null, pendingCreate: null, actionKey: null };
  try {
    const saved = JSON.parse(raw);
    if (!/^[0-9a-f]{64}$/.test(saved.capability)) throw new Error("Invalid local capability");
    return {
      capability: saved.capability,
      runId: typeof saved.runId === "string" ? saved.runId : null,
      request: saved.request && typeof saved.request === "object" ? saved.request : null,
      pendingCreate: saved.pendingCreate && typeof saved.pendingCreate === "object" ? saved.pendingCreate : null,
      actionKey: /^[0-9a-f]{64}$/.test(saved.actionKey || "") ? saved.actionKey : null,
    };
  } catch {
    throw new Error("This tab's saved demo session could not be read. Open a new tab to start a new local session.");
  }
}

function saveSession() {
  sessionStorage.setItem(STORAGE_KEY, JSON.stringify(session));
}

function setStatus(message, isError = false) {
  const notice = $("status-message");
  notice.textContent = message;
  notice.classList.toggle("error", isError);
}

function setBusy(value) {
  busy = value;
  $("create-button").disabled = value;
  $("confirm-button").disabled = value;
  $("retry-recovery").disabled = value;
  $("retry-report").disabled = value;
}

function display(value, fallback = "—") {
  if (typeof value === "string" && value.length) return value;
  if (typeof value === "number" && Number.isFinite(value)) return String(value);
  return fallback;
}

function dateDisplay(value) {
  if (typeof value !== "string" || !value) return "Timestamp unavailable";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : `${date.toLocaleString(undefined, { dateStyle: "medium", timeStyle: "long" })} (${value})`;
}

function limitationsFrom(...sources) {
  const messages = [];
  for (const source of sources) {
    if (!Array.isArray(source)) continue;
    for (const entry of source) {
      if (typeof entry === "string" && entry && !messages.includes(entry)) messages.push(entry);
    }
  }
  const list = $("limitations-list");
  list.replaceChildren();
  for (const message of messages) {
    const item = document.createElement("li");
    item.textContent = message;
    list.append(item);
  }
  $("api-limitations").hidden = messages.length === 0;
}

function errorMessage(payload, status) {
  const error = payload && payload.error;
  if (typeof error === "string") return error;
  if (error && typeof error.message === "string") return error.message;
  if (typeof payload?.message === "string") return payload.message;
  return `The local demo returned HTTP ${status}.`;
}

async function request(path, options = {}) {
  const headers = { Accept: "application/json" };
  if (options.auth !== false) headers.Authorization = `Bearer ${session.capability}`;
  if (options.body) headers["Content-Type"] = "application/json";
  if (options.createKey) headers["Idempotency-Key"] = options.createKey;
  if (options.actionKey) headers["X-Demo-Action-Key"] = options.actionKey;
  let response;
  try {
    response = await fetch(path, {
      method: options.method || "GET",
      headers,
      body: options.body ? JSON.stringify(options.body) : undefined,
      cache: "no-store",
    });
  } catch {
    throw new Error("The local demo server is unavailable. Start make mvp-web and try again.");
  }
  if (options.blob && response.ok) return response.blob();
  let payload;
  try {
    payload = await response.json();
  } catch {
    throw new Error(`The local demo returned an unreadable response (HTTP ${response.status}).`);
  }
  if (!response.ok) throw new Error(errorMessage(payload, response.status));
  return payload;
}

function renderRun(run) {
  activeRun = run;
  activeReport = null;
  const preview = run.preview || {};
  const quoteState = run.quote_state || "OFFERED";
  $("empty-state").hidden = true;
  $("run-content").hidden = false;
  $("run-id").textContent = display(run.run_id);
  $("quote-state").textContent = quoteState;
  $("snapshot-at").textContent = dateDisplay(preview.snapshot_at);
  $("preview-side").textContent = display(preview.side, "—");
  $("preview-quantity").textContent = `${display(preview.quantity_base)} BTC`;
  $("preview-instrument").textContent = display(preview.instrument_id, INSTRUMENT_ID);
  $("preview-price").textContent = display(preview.price_display || capabilities?.price_display, "Local demo · no charge");
  $("expires-at").textContent = preview.expires_at ? `Preview expires: ${dateDisplay(preview.expires_at)}` : "";
  $("confirm-section").hidden = quoteState !== "OFFERED";
  $("expired-section").hidden = quoteState !== "EXPIRED";
  $("report-section").hidden = quoteState !== "UNLOCKED";
  $("downloads").hidden = true;
  $("retry-report").hidden = true;
  $("metric-vwap").textContent = "—";
  $("metric-worst").textContent = "—";
  $("metric-notional").textContent = "—";
  $("metric-levels").textContent = "—";
  $("report-digest").textContent = display(run.report_sha256);
  $("bundle-digest").textContent = display(run.bundle_sha256);
  limitationsFrom(capabilities?.limitations, preview.limitations);
}

function renderReport(report) {
  activeReport = report;
  const calculation = report.calculation || {};
  const values = calculation.display || {};
  $("metric-vwap").textContent = display(values.vwap);
  $("metric-worst").textContent = display(values.worst_price);
  $("metric-notional").textContent = display(values.notional_quote);
  $("metric-levels").textContent = display(calculation.consumed_levels);
  $("downloads").hidden = false;
  $("retry-report").hidden = true;
  limitationsFrom(capabilities?.limitations, activeRun?.preview?.limitations, report.quality?.limitations);
}

async function loadReport() {
  if (!session.runId || busy) return;
  setBusy(true);
  $("retry-report").hidden = true;
  setStatus("Loading the unlocked local report…");
  try {
    const report = await request(`/demo/runs/${encodeURIComponent(session.runId)}/report`);
    renderReport(report);
    setStatus("Local simulated access is unlocked. Inspect the calculation and download the evidence below.");
  } catch (error) {
    $("retry-report").hidden = false;
    setStatus(error.message, true);
  } finally {
    setBusy(false);
  }
}

async function recoverRun() {
  if (!session.runId || busy) return;
  setBusy(true);
  $("retry-recovery").hidden = true;
  setStatus("Recovering the active run from this tab…");
  try {
    const run = await request(`/demo/runs/${encodeURIComponent(session.runId)}`);
    renderRun(run);
    if (run.quote_state === "UNLOCKED") {
      setBusy(false);
      await loadReport();
      return;
    }
    setStatus(run.quote_state === "EXPIRED" ? "This preview expired. Start a new scenario to continue." : "Preview restored. Confirm simulated access to inspect the report.");
  } catch (error) {
    $("retry-recovery").hidden = false;
    setStatus(`Could not restore the active run: ${error.message}`, true);
  } finally {
    setBusy(false);
  }
}

function validateForm() {
  const side = form.elements.side.value;
  const quantity = $("quantity").value.trim();
  const payer = $("payer").value.trim();
  if (!/^(?:0|[1-9]\d*)(?:\.\d+)?$/.test(quantity) || !/[1-9]/.test(quantity)) {
    $("quantity").focus();
    throw new Error("Enter a positive BTC quantity as an exact decimal, such as 0.15.");
  }
  if (!/^0x[0-9a-fA-F]{40}$/.test(payer)) {
    $("payer").focus();
    throw new Error("Enter an illustrative 0x address with 40 hexadecimal characters.");
  }
  return { instrument_id: INSTRUMENT_ID, side, quantity_base: quantity, expected_payer: payer };
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (busy || !session) return;
  let body;
  try {
    body = validateForm();
  } catch (error) {
    setStatus(error.message, true);
    return;
  }
  const serialized = JSON.stringify(body);
  if (!session.pendingCreate || JSON.stringify(session.pendingCreate.body) !== serialized) {
    session.pendingCreate = { body, key: randomHex() };
  }
  try {
    saveSession();
  } catch {
    setStatus("This browser cannot save the local session. Enable session storage and try again.", true);
    return;
  }
  setBusy(true);
  setStatus("Building a report from the fixed fixture…");
  try {
    const run = await request("/demo/runs", { method: "POST", body, createKey: session.pendingCreate.key });
    if (typeof run.run_id !== "string") throw new Error("The local demo did not return a run ID.");
    session.runId = run.run_id;
    session.request = body;
    session.pendingCreate = null;
    session.actionKey = null;
    saveSession();
    renderRun(run);
    if (run.quote_state === "UNLOCKED") {
      setBusy(false);
      await loadReport();
      return;
    }
    setStatus(run.quote_state === "EXPIRED" ? "This preview expired. Start a new scenario to continue." : "Preview ready. Review the fixture timestamp and confirm simulated access when ready.");
  } catch (error) {
    setStatus(error.message, true);
  } finally {
    setBusy(false);
  }
});

$("confirm-button").addEventListener("click", async () => {
  if (busy || !session?.runId || activeRun?.quote_state !== "OFFERED") return;
  if (!session.actionKey) session.actionKey = randomHex();
  try {
    saveSession();
  } catch {
    setStatus("This browser cannot save the confirmation retry key. Enable session storage and try again.", true);
    return;
  }
  setBusy(true);
  setStatus("Recording a simulated local unlock. NO TRANSFER is performed…");
  try {
    const run = await request(`/demo/runs/${encodeURIComponent(session.runId)}/confirm-simulated`, { method: "POST", actionKey: session.actionKey });
    renderRun(run);
    if (run.quote_state !== "UNLOCKED") throw new Error("The demo did not unlock this report.");
    setBusy(false);
    await loadReport();
  } catch (error) {
    setStatus(error.message, true);
  } finally {
    setBusy(false);
  }
});

async function download(kind) {
  if (!session?.runId || !activeReport || busy) return;
  const button = kind === "report" ? $("download-json") : $("download-zip");
  button.disabled = true;
  setStatus(`Preparing the ${kind === "report" ? "JSON report" : "evidence ZIP"} download…`);
  try {
    const blob = await request(`/demo/runs/${encodeURIComponent(session.runId)}/${kind}`, { blob: true });
    const objectUrl = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = objectUrl;
    link.download = `liqvera-${kind === "report" ? "report.json" : "evidence.zip"}`;
    document.body.append(link);
    link.click();
    link.remove();
    setTimeout(() => URL.revokeObjectURL(objectUrl), 60_000);
    setStatus("Download ready. This is a simulated, unverified local artifact.");
  } catch (error) {
    setStatus(error.message, true);
  } finally {
    button.disabled = false;
  }
}

$("download-json").addEventListener("click", () => download("report"));
$("download-zip").addEventListener("click", () => download("evidence"));
$("retry-recovery").addEventListener("click", recoverRun);
$("retry-report").addEventListener("click", loadReport);

async function start() {
  if (!globalThis.crypto?.getRandomValues) {
    form.querySelectorAll("input,button").forEach((element) => { element.disabled = true; });
    setStatus("Secure browser randomness is unavailable. Open this local demo on 127.0.0.1 in a modern browser.", true);
    return;
  }
  try {
    session = loadSession();
    saveSession();
  } catch (error) {
    form.querySelectorAll("input,button").forEach((element) => { element.disabled = true; });
    setStatus(error.message, true);
    return;
  }
  if (session.request) {
    $("quantity").value = display(session.request.quantity_base, "");
    $("payer").value = display(session.request.expected_payer, "");
    const side = ["BUY", "SELL"].includes(session.request.side) ? form.querySelector(`input[name="side"][value="${session.request.side}"]`) : null;
    if (side) side.checked = true;
  }
  $("empty-state").hidden = Boolean(session.runId);
  try {
    capabilities = await request("/demo/capabilities", { auth: false });
    $("market-id").textContent = display(capabilities.instrument_id, INSTRUMENT_ID);
    $("price-display").textContent = display(capabilities.price_display, "Fixed local demo · no charge");
    limitationsFrom(capabilities.limitations);
    if (!session.runId) setStatus("Local fixture demo ready. Enter a scenario to begin.");
  } catch (error) {
    setStatus(error.message, true);
  }
  if (session.runId) await recoverRun();
}

start();
