import "./style.css";
import { MEZO_TESTNET, MUSD_TESTNET } from "@liqvera/mezo-protocol";
import { ApiFailure, createQuote, getCapabilities, getEvidence, getQuote, getReport, getRequest } from "./api";
import { quoteIsPayable, receiptMatchesQuote, type Capabilities, type Delivery, type Quote, type RequestStatus, type Side } from "./contracts";
import { capability, clearFlow, loadFlow, saveFlow, type SavedFlow } from "./session";
import { injectedWallet, switchToMezo, walletAccount, walletError, walletOnMezo, type Eip1193Provider } from "./wallet";
import { requestPaidReport, x402Available, X402CancelledBeforeSubmission } from "./x402";

const app = document.querySelector<HTMLDivElement>("#app");
if (!app) throw new Error("App root missing.");

app.innerHTML = `
  <a class="skip-link" href="#workspace">Skip to report workspace</a>
  <div class="page-shell">
    <header class="site-header">
      <a class="brand" href="/" aria-label="Liqvera home"><span class="brand-mark" aria-hidden="true">L</span><span>Liqvera</span></a>
      <div class="header-right"><span class="network-chip"><span class="pulse-dot" aria-hidden="true"></span> MEZO TESTNET ONLY</span><span class="header-caption">Market reports you can verify.</span></div>
    </header>
    <main id="workspace">
      <section class="hero" aria-labelledby="hero-title">
        <div class="hero-copy"><p class="eyebrow">PUBLIC MARKET DATA · PRIVATE ACCESS</p><h1 id="hero-title">A clearer view of the <em>available</em> book.</h1><p class="lead">Explore a hypothetical sweep of a public Hyperliquid BTC perpetual snapshot. Review the evidence before trusting the calculation.</p></div>
        <div class="hero-aside" aria-label="Product boundaries"><div class="aside-label">REPORT BOUNDARIES</div><p>Read-only analytics</p><p>No exchange order or execution</p><p>Mezo Testnet payment only</p></div>
      </section>
      <div class="workspace-grid">
        <section class="panel request-panel" aria-labelledby="request-title">
          <div class="panel-heading"><span class="step">01</span><div><p class="eyebrow">BUILD A REPORT</p><h2 id="request-title">Set your snapshot question</h2></div></div>
          <p class="supporting">This is a calculation over the available snapshot depth, not a complete exchange book or guaranteed execution.</p>
          <div class="instrument"><span class="instrument-icon" aria-hidden="true">₿</span><span><strong>BTC linear perpetual</strong><small>Hyperliquid public order book</small></span><span class="readonly-tag">READ ONLY</span></div>
          <form id="report-form" novalidate>
            <fieldset><legend>Hypothetical side</legend><div class="segment"><label><input type="radio" name="side" value="BUY" checked /><span>BUY</span></label><label><input type="radio" name="side" value="SELL" /><span>SELL</span></label></div></fieldset>
            <label class="field-label" for="quantity">Quantity <span>BTC</span></label><input id="quantity" name="quantity" type="text" inputmode="decimal" autocomplete="off" spellcheck="false" value="0.15" aria-describedby="quantity-hint" /><p id="quantity-hint" class="field-hint">A positive decimal string, up to 8 places. The report shows a hypothetical sweep.</p>
            <div class="wallet-box"><div><span class="eyebrow">EXPECTED PAYER</span><strong id="wallet-label">No wallet connected</strong><span id="chain-label">Connect an EVM wallet on Mezo Testnet.</span></div><div class="wallet-actions"><button id="connect-button" type="button" class="text-button">Connect wallet</button><button id="switch-button" type="button" class="text-button hidden">Switch network</button></div></div>
            <button id="create-button" class="primary-button" type="submit" disabled>Request a report <span aria-hidden="true">↗</span></button>
            <p id="create-note" class="form-note">Checking service capabilities…</p>
          </form>
        </section>
        <section class="panel result-panel" aria-labelledby="result-title">
          <div class="panel-heading"><span class="step">02</span><div><p class="eyebrow">STATUS & DELIVERY</p><h2 id="result-title">Your report</h2></div></div>
          <div id="announcement" class="announcement" role="status" aria-live="polite">Checking capabilities and saved session…</div>
          <div id="capability-status" class="capability-status"></div>
          <div id="result-content" class="result-content"><div class="empty-state"><div class="empty-graphic" aria-hidden="true"><span></span><span></span><span></span><span></span></div><h3>Waiting for a question</h3><p>Connect your wallet and ask for a snapshot report. A quote appears only after the source and evidence are prepared.</p></div></div>
          <div class="result-actions"><button id="refresh-button" class="secondary-button hidden" type="button">Check status</button><button id="new-button" class="text-button hidden" type="button">Start another report</button></div>
        </section>
      </div>
      <section class="boundary-strip" aria-label="Important context"><div><span>01</span><p><strong>Snapshot, not a signal.</strong> Available levels support the arithmetic; they do not establish a trading opportunity.</p></div><div><span>02</span><p><strong>Verifiable evidence.</strong> A downloadable bundle supports offline recalculation after entitlement.</p></div><div><span>03</span><p><strong>No execution authority.</strong> No orders, custody, live trading, or guaranteed fills.</p></div></section>
    </main>
    <footer><span>Liqvera · Market reports you can verify.</span><span>Built for MEZO ₿ · Testnet experience</span></footer>
  </div>`;

function el<T extends HTMLElement>(selector: string): T {
  const found = document.querySelector<T>(selector);
  if (!found) throw new Error(`Missing UI element: ${selector}`);
  return found;
}

function node<K extends keyof HTMLElementTagNameMap>(tag: K, className = "", content = ""): HTMLElementTagNameMap[K] {
  const element = document.createElement(tag);
  element.className = className;
  element.textContent = content;
  return element;
}

function appendField(parent: HTMLElement, label: string, value: string, className = ""): void {
  const box = node("div", `data-field ${className}`);
  box.append(node("span", "data-label", label), node("strong", "data-value", value));
  parent.append(box);
}

function announcement(message: string, kind: "normal" | "warning" | "error" = "normal"): void {
  const target = el<HTMLDivElement>("#announcement");
  target.textContent = message;
  target.dataset.kind = kind;
}

function readableError(error: unknown): string {
  if (error instanceof ApiFailure) {
    const suffix = error.requestId ? ` Reference: ${error.requestId}.` : "";
    return `${error.message} (${error.code}).${suffix}`;
  }
  if (error instanceof Error) return error.message;
  return "The request could not be completed. Check status before trying another action.";
}

function dateTime(value: string): string {
  const date = new Date(value);
  return Number.isFinite(date.getTime()) ? date.toLocaleString(undefined, { dateStyle: "medium", timeStyle: "medium", timeZoneName: "short" }) : value;
}

function snapshotAge(value: string): string {
  const elapsed = Date.now() - Date.parse(value);
  if (!Number.isFinite(elapsed)) return "Unknown age";
  if (elapsed < 0) return "Clock difference detected";
  const minutes = Math.floor(elapsed / 60000);
  return minutes < 1 ? "Less than a minute old" : `${minutes} minute${minutes === 1 ? "" : "s"} old now`;
}

let cap: Capabilities | null = null;
let bearer: string | null = null;
let provider: Eip1193Provider | null = injectedWallet();
let account: string | null = null;
let onChain = false;
let flow: SavedFlow | null = null;
let quote: Quote | null = null;
let delivery: Delivery | null = null;
let busy = false;
let polling = false;

function setBusy(value: boolean): void {
  busy = value;
  updateControls();
}

function updateControls(): void {
  const ready = Boolean(cap?.payment_ready && cap.source_mode === "live-public");
  const canCreate = ready && x402Available() && Boolean(bearer && account && onChain && !flow) && !busy;
  el<HTMLButtonElement>("#create-button").disabled = !canCreate;
  el<HTMLButtonElement>("#refresh-button").classList.toggle("hidden", !flow);
  el<HTMLButtonElement>("#refresh-button").disabled = busy || polling;
  const lock = flow?.paymentGuard !== "clear" || (quote && ["PAYMENT_PENDING", "PAYMENT_UNCERTAIN", "MANUAL_REVIEW"].includes(quote.state));
  el<HTMLButtonElement>("#new-button").classList.toggle("hidden", !flow || Boolean(lock));
  el<HTMLButtonElement>("#new-button").disabled = busy || polling;
  el<HTMLButtonElement>("#switch-button").classList.toggle("hidden", !provider || onChain);
  el<HTMLElement>("#wallet-label").textContent = account ? `${account.slice(0, 8)}…${account.slice(-6)}` : "No wallet connected";
  el<HTMLElement>("#chain-label").textContent = !provider ? "No injected EVM wallet found." : onChain ? "Mezo Testnet · chain 31611" : "Wrong network · switch to Mezo Testnet (31611).";
  el<HTMLElement>("#create-note").textContent = !cap ? "Checking service capabilities…" :
    !cap.payment_ready ? "Payment and new quotes are currently unavailable." :
    !x402Available() ? "The browser payment adapter awaits SDK verification; no payment can be submitted." :
    !account ? "Connect an injected wallet to continue." :
    !onChain ? "Switch to Mezo Testnet to continue." :
    flow ? "This session already has a report. Check its status or start another after it finishes." :
    "The server will prepare the evidence before showing any payment terms.";
}

function renderCapability(): void {
  const target = el<HTMLDivElement>("#capability-status");
  target.replaceChildren();
  if (!cap) return;
  const badge = node("div", `status-pill ${cap.payment_ready ? "status-ready" : "status-blocked"}`, cap.payment_ready ? "Gateway payment ready" : "Gateway payment unavailable");
  target.append(badge);
  if (!cap.payment_ready) {
    const detail = node("p", "subtle", cap.blockers.length ? `Current blockers: ${cap.blockers.join(", ")}.` : "Gateway has not enabled payment.");
    target.append(detail);
  }
  if (cap.limitations.length) target.append(node("p", "subtle", cap.limitations.join(" ")));
}

function renderRequest(status: RequestStatus): void {
  const target = el<HTMLDivElement>("#result-content");
  target.replaceChildren();
  const card = node("div", "status-card");
  card.append(node("p", "eyebrow", `REQUEST ${status.state}`));
  card.append(node("h3", "", status.state === "PREPARING" ? "Preparing sealed evidence" : status.state === "REJECTED" ? "No chargeable quote" : "Report build could not complete"));
  card.append(node("p", "supporting", status.state === "PREPARING" ? "The server is capturing, checking, and retaining the snapshot. You will see terms only after it succeeds." : `Reason: ${status.reason ?? "Unavailable"}. No payment is due.`));
  target.append(card);
}

function renderQuote(): void {
  const target = el<HTMLDivElement>("#result-content");
  target.replaceChildren();
  if (!quote) return;
  const q = quote;
  const state = node("div", "quote-state");
  state.append(node("span", "eyebrow", "IMMUTABLE QUOTE"), node("span", `status-pill ${q.state === "READY" ? "status-ready" : "status-blocked"}`, q.state.replaceAll("_", " ")));
  target.append(state);
  const headline = node("h3", "result-heading", q.state === "READY" ? "Review before access" : q.state === "PAID" ? "Access confirmed" : "Payment recovery in progress");
  target.append(headline);
  const grid = node("div", "data-grid");
  appendField(grid, "Instrument", "Hyperliquid BTC linear perpetual", "span-all");
  appendField(grid, "Hypothetical side", q.preview.side);
  appendField(grid, "Quantity", `${q.preview.quantity_base} BTC`);
  appendField(grid, "Snapshot time", dateTime(q.preview.snapshot_at), "span-all");
  appendField(grid, "Age now", snapshotAge(q.preview.snapshot_at));
  appendField(grid, "Snapshot quality", "Valid for snapshot calculation");
  target.append(grid);
  const limits = node("div", "limitations");
  limits.append(node("strong", "", "Calculation limits"));
  const list = node("ul");
  for (const limitation of q.preview.limitations) list.append(node("li", "", limitation));
  list.append(node("li", "", "This sampled public book is not the exchange's complete order book or an execution guarantee."));
  limits.append(list);
  target.append(limits);
  const terms = node("div", "terms-box");
  terms.append(node("p", "eyebrow", "TESTNET ACCESS TERMS"));
  const termsGrid = node("div", "data-grid");
  appendField(termsGrid, "Price", `${q.terms.price_musd} test ${MUSD_TESTNET.symbol}`);
  appendField(termsGrid, "Atomic amount", q.terms.amount_atomic);
  appendField(termsGrid, "Network", `Mezo Testnet · ${q.terms.network}`);
  appendField(termsGrid, "Token", q.terms.asset, "breakable span-all");
  appendField(termsGrid, "Recipient", q.terms.pay_to, "breakable span-all");
  appendField(termsGrid, "Expected payer", q.terms.expected_payer, "breakable span-all");
  appendField(termsGrid, "Quote expires", dateTime(q.terms.expires_at), "span-all");
  appendField(termsGrid, "Paid report retention", `At least ${q.retention.paid_days} days`);
  appendField(termsGrid, "Unpaid cleanup grace", `At least ${q.retention.unpaid_grace_seconds} seconds`);
  appendField(termsGrid, "Ledger retention", `At least ${q.retention.ledger_days} days`);
  terms.append(termsGrid);
  target.append(terms);
  if (["PAYMENT_PENDING", "PAYMENT_UNCERTAIN", "MANUAL_REVIEW"].includes(q.state) || flow?.paymentGuard !== "clear") {
    target.append(node("p", "safety-note", "Checking the payment already submitted or possibly submitted. Do not pay again. Use Check status to recover this same report."));
  } else if (q.state === "EXPIRED") {
    target.append(node("p", "safety-note", "This quote expired. It cannot be paid. Start a new report only after the previous payment status is known."));
  } else if (q.state === "READY") {
    const canPay = Boolean(cap?.payment_ready && account && onChain && flow?.paymentGuard === "clear" && quoteIsPayable(q, account ?? "") && x402Available());
    const button = node("button", "primary-button", "Confirm testnet payment in wallet");
    button.type = "button";
    button.disabled = !canPay || busy;
    button.addEventListener("click", () => { void submitPayment(); });
    target.append(button);
    if (!x402Available()) target.append(node("p", "form-note", "The reviewed x402 browser adapter is not installed. No payment can be submitted from this build."));
    else if (account?.toLowerCase() !== q.terms.expected_payer.toLowerCase()) target.append(node("p", "safety-note", "The connected wallet differs from the quote payer. Reconnect the quoted wallet; this quote cannot be paid by another account."));
    else if (!onChain) target.append(node("p", "safety-note", "Switch the wallet to Mezo Testnet before payment."));
  }
}

function renderDelivery(): void {
  if (!quote || !delivery) return;
  const q = quote;
  const paid = delivery;
  const target = el<HTMLDivElement>("#result-content");
  target.replaceChildren();
  const report = paid.report;
  const receipt = paid.receipt;
  target.append(node("div", "status-pill status-ready", "ENTITLED · RECEIPT CONFIRMED"));
  target.append(node("h3", "result-heading", "Your snapshot report"));
  target.append(node("p", "supporting", "Hypothetical snapshot sweep over the available public order-book depth. No exchange trade occurred."));
  const grid = node("div", "data-grid report-grid");
  appendField(grid, "Side & size", `${report.request.side} ${report.request.quantity_base} BTC`);
  appendField(grid, "Snapshot time", dateTime(report.source.source_at));
  appendField(grid, "Snapshot age now", snapshotAge(report.source.source_at));
  appendField(grid, "Sampled levels", `${report.source.available_bid_levels} bid / ${report.source.available_ask_levels} ask`);
  appendField(grid, "VWAP (display)", report.calculation.display.vwap);
  appendField(grid, "Worst price (display)", report.calculation.display.worst_price);
  appendField(grid, "Consumed levels", String(report.calculation.consumed_levels));
  appendField(grid, "Price impact (display)", `${report.calculation.display.price_impact_bps} bps`);
  appendField(grid, "Hypothetical notional", report.calculation.display.notional_quote);
  appendField(grid, "Execution authority", report.boundaries.execution_authority);
  target.append(grid);
  const limitations = node("div", "limitations");
  limitations.append(node("strong", "", "Evidence and limits"));
  const list = node("ul");
  for (const item of report.quality.limitations) list.append(node("li", "", item));
  list.append(node("li", "", "Hashes and recalculation support reproducibility; they do not prove the exchange signed the data or predict a future fill."));
  limitations.append(list);
  target.append(limitations);
  const receiptBox = node("div", "terms-box");
  receiptBox.append(node("p", "eyebrow", "TESTNET RECEIPT"));
  const receiptGrid = node("div", "data-grid");
  appendField(receiptGrid, "Report SHA-256", receipt.report_sha256, "breakable span-all");
  appendField(receiptGrid, "Payment", `${q.terms.price_musd} test ${MUSD_TESTNET.symbol}`);
  appendField(receiptGrid, "Confirmed", dateTime(receipt.confirmed_at));
  appendField(receiptGrid, "Block / log", `${receipt.block_number} / ${receipt.log_index}`);
  appendField(receiptGrid, "Finality policy", receipt.finality_policy_version);
  appendField(receiptGrid, "Transaction", receipt.tx_hash, "breakable span-all");
  receiptBox.append(receiptGrid);
  if (/^0x[0-9a-f]{64}$/.test(receipt.tx_hash)) {
    const explorerBase = new URL(MEZO_TESTNET.explorerUrl);
    if (explorerBase.protocol === "https:" && explorerBase.origin === "https://explorer.test.mezo.org") {
      const explorer = node("a", "external-link", "View testnet transaction ↗");
      explorer.href = `${explorerBase.origin}/tx/${receipt.tx_hash}`;
      explorer.target = "_blank";
      explorer.rel = "noopener noreferrer";
      receiptBox.append(explorer);
    }
  }
  target.append(receiptBox);
  const actions = node("div", "download-actions");
  const evidenceButton = node("button", "secondary-button", "Download evidence ZIP");
  evidenceButton.type = "button";
  evidenceButton.addEventListener("click", () => { void downloadEvidence(); });
  const jsonButton = node("button", "text-button", "Download readable JSON view");
  jsonButton.type = "button";
  jsonButton.addEventListener("click", () => {
    const bytes = JSON.stringify(report, null, 2) + "\n";
    saveBlob(new Blob([bytes], { type: "application/json" }), `liqvera-report-view-${report.report_id}.json`);
  });
  actions.append(evidenceButton, jsonButton);
  target.append(actions);
  target.append(node("p", "form-note", "For byte-exact report verification, use report.json inside the evidence ZIP. This readable JSON view is reformatted."));
}

function saveBlob(blob: Blob, name: string): void {
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = name;
  document.body.append(link);
  link.click();
  link.remove();
  setTimeout(() => URL.revokeObjectURL(url), 60_000);
}

async function downloadEvidence(): Promise<void> {
  if (!bearer || !quote || !delivery) return;
  try {
    announcement("Checking entitlement and downloading the immutable evidence bundle…");
    const blob = await getEvidence(bearer, quote.report_id);
    const digest = await crypto.subtle.digest("SHA-256", await blob.arrayBuffer());
    const actual = Array.from(new Uint8Array(digest), byte => byte.toString(16).padStart(2, "0")).join("");
    if (actual !== quote.bundle_sha256) throw new Error("Evidence bundle digest does not match the quote. Download was withheld.");
    saveBlob(blob, `liqvera-evidence-${quote.report_id}.zip`);
    announcement("Evidence bundle downloaded. Verify it with the offline verifier.");
  } catch (error) { announcement(readableError(error), "error"); }
}

function rememberQuote(next: Quote): void {
  if (!flow) throw new Error("No active session for this quote.");
  if (next.terms.expected_payer.toLowerCase() !== flow.payer.toLowerCase()) throw new Error("Quote payer differs from the saved request.");
  const canonicalQuantity = (value: string): string => {
    const [whole = "0", fraction = ""] = value.replace(/^\+/, "").split(".");
    const normalizedWhole = whole.replace(/^0+(?=\d)/, "");
    const normalizedFraction = fraction.replace(/0+$/, "");
    return normalizedFraction ? `${normalizedWhole}.${normalizedFraction}` : normalizedWhole;
  };
  if (next.preview.side !== flow.side || canonicalQuantity(next.preview.quantity_base) !== canonicalQuantity(flow.quantity)) {
    throw new Error("Quote subject differs from the saved request. Payment remains disabled.");
  }
  if (flow.quoteId && flow.quoteId !== next.quote_id) throw new Error("Quote identity changed. Payment remains disabled.");
  flow.quoteId = next.quote_id;
  flow.requestId = next.report_request_id;
  saveFlow(flow);
  quote = next;
  updateControls();
  renderQuote();
}

async function recoverDelivery(): Promise<"delivered" | "recovering" | "withheld"> {
  if (!quote || !bearer) return "withheld";
  const result = await getReport(bearer, quote.report_id);
  if (result === "recovering") {
    announcement("Checking the payment already submitted. Do not submit another payment.", "warning");
    return "recovering";
  }
  if (result === "payment-required") {
    if (quote.state === "PAID") announcement("Entitlement is temporarily unavailable. Check status; do not pay again.", "warning");
    return "withheld";
  }
  if (!receiptMatchesQuote(result.receipt, quote) || result.report.report_id !== quote.report_id) {
    throw new Error("Receipt does not match the quoted report. Delivery is withheld.");
  }
  delivery = result;
  if (flow) { flow.paymentGuard = "clear"; saveFlow(flow); }
  renderDelivery();
  announcement("Paid report recovered. The receipt and evidence are available without another payment.");
  return "delivered";
}

async function refreshQuote(): Promise<void> {
  if (!bearer || !flow?.quoteId) return;
  rememberQuote(await getQuote(bearer, flow.quoteId));
  if (quote?.state === "PAID") await recoverDelivery();
  else if (quote && ["PAYMENT_PENDING", "PAYMENT_UNCERTAIN", "MANUAL_REVIEW"].includes(quote.state)) announcement("Checking the payment already submitted. No second payment is offered.", "warning");
  else if (quote?.state === "EXPIRED") announcement("The quote has expired. No payment is available.", "warning");
  else announcement("Quote status updated. Review the terms and current wallet before any action.");
}

async function pollQuote(): Promise<void> {
  if (!bearer || !flow?.quoteId || polling) return;
  polling = true;
  updateControls();
  try {
    for (let attempt = 0; attempt < 12; attempt++) {
      if (attempt) await new Promise(resolve => setTimeout(resolve, 2500));
      if (!flow?.quoteId) return;
      rememberQuote(await getQuote(bearer, flow.quoteId));
      if (quote?.state === "PAID") {
        await recoverDelivery();
        return;
      }
      if (quote?.state === "MANUAL_REVIEW") {
        announcement("Payment requires operator review. This report remains locked against another payment.", "warning");
        return;
      }
      if (quote?.state !== "PAYMENT_PENDING" && quote?.state !== "PAYMENT_UNCERTAIN") {
        announcement("Quote state changed. Review it before taking another action.", "warning");
        return;
      }
      announcement(`Checking the payment already submitted… check ${attempt + 1} of 12.`, "warning");
    }
    announcement("Payment is still being checked. Use Check status later; do not pay again.", "warning");
  } finally { polling = false; updateControls(); }
}

async function pollPaidDelivery(): Promise<void> {
  if (!quote || !bearer || polling) return;
  polling = true;
  updateControls();
  try {
    for (let attempt = 0; attempt < 12; attempt++) {
      if (attempt) await new Promise(resolve => setTimeout(resolve, 2500));
      const state = await recoverDelivery();
      if (state !== "recovering") return;
      announcement(`Checking entitled delivery… check ${attempt + 1} of 12. Do not pay again.`, "warning");
    }
    announcement("Delivery is still being checked. Use Check status later; do not pay again.", "warning");
  } finally { polling = false; updateControls(); }
}

async function pollRequest(): Promise<void> {
  if (!bearer || !flow?.requestId || polling) return;
  polling = true;
  updateControls();
  try {
    for (let attempt = 0; attempt < 12; attempt++) {
      if (attempt) await new Promise(resolve => setTimeout(resolve, 2500));
      if (!flow?.requestId) return;
      const status = await getRequest(bearer, flow.requestId);
      renderRequest(status);
      if (status.state === "READY" && status.quote_id) {
        rememberQuote(await getQuote(bearer, status.quote_id));
        announcement("Evidence is ready. Review the quote terms before paying.");
        return;
      }
      if (status.state !== "PREPARING") {
        announcement(`Report request ended: ${status.reason ?? status.state}. No payment is due.`, "warning");
        return;
      }
      announcement(`Preparing the report and sealed evidence… check ${attempt + 1} of 12.`);
    }
    announcement("The report is still preparing. Use Check status to continue; this will not create another request.", "warning");
  } finally { polling = false; updateControls(); }
}

async function resumeFlow(): Promise<void> {
  if (!flow || !bearer || busy || polling) return;
  setBusy(true);
  try {
    if (flow.quoteId) {
      await refreshQuote();
      if (quote && ["PAYMENT_PENDING", "PAYMENT_UNCERTAIN"].includes(quote.state)) {
        setBusy(false);
        await pollQuote();
        return;
      }
      if (quote?.state === "PAID" && !delivery) {
        setBusy(false);
        await pollPaidDelivery();
        return;
      }
    }
    else if (flow.requestId) {
      setBusy(false);
      await pollRequest();
      return;
    } else {
      // A network failure may have followed server commit. Reuse the same key and exact body.
      const created = await createQuote(bearer, { side: flow.side, quantity: flow.quantity, payer: flow.payer, idempotencyKey: flow.idempotencyKey });
      if (created.schema === "mee-evidence-quote/v1") {
        rememberQuote(created);
        announcement("Quote recovered with the original idempotency key.");
      } else {
        flow.requestId = created.report_request_id;
        saveFlow(flow);
        renderRequest(created);
        setBusy(false);
        await pollRequest();
        return;
      }
    }
  } catch (error) { announcement(readableError(error), "error"); }
  finally { setBusy(false); }
}

async function submitPayment(): Promise<void> {
  if (!quote || !flow || !bearer || !provider || !account || busy || !cap?.payment_ready ||
      flow.paymentGuard !== "clear" || !x402Available() || !quoteIsPayable(quote, account)) return;
  setBusy(true);
  try {
    if (!(await walletOnMezo(provider)) || (await walletAccount(provider, false))?.toLowerCase() !== quote.terms.expected_payer.toLowerCase()) {
      throw new Error("Wallet network or account changed. Reconnect the quoted payer before continuing.");
    }
    flow.paymentGuard = "started";
    saveFlow(flow);
    renderQuote();
    announcement("Opening the reviewed x402 wallet flow. Confirm only the displayed testnet terms.");
    const result = await requestPaidReport({ path: `/v1/reports/${quote.report_id}`, bearerCapability: bearer, quote, provider, payer: account });
    if (result === "recovering") {
      flow.paymentGuard = "uncertain";
      saveFlow(flow);
      announcement("Checking the payment already submitted. Do not pay again.", "warning");
    } else {
      await refreshQuote();
      if (quote?.state !== "PAID") {
        flow.paymentGuard = "uncertain";
        saveFlow(flow);
        announcement("The payment outcome is not yet confirmed. Check status; do not pay again.", "warning");
      }
    }
  } catch (error) {
    if (error instanceof X402CancelledBeforeSubmission) {
      const latest = await getQuote(bearer, quote.quote_id).catch(() => null);
      if (latest && latest.state === "READY") {
        rememberQuote(latest);
        flow.paymentGuard = "clear";
        saveFlow(flow);
        announcement("Wallet payment was canceled before submission. The quote remains unpaid.", "warning");
      } else {
        flow.paymentGuard = "uncertain";
        saveFlow(flow);
        announcement("Payment status needs checking before another wallet action.", "warning");
      }
    } else {
      flow.paymentGuard = "uncertain";
      saveFlow(flow);
      announcement(`${readableError(error)} Check status before any new payment.`, "warning");
    }
  } finally { setBusy(false); if (delivery) renderDelivery(); else renderQuote(); }
}

async function connectWallet(): Promise<void> {
  provider = injectedWallet();
  if (!provider) { announcement("Install or enable an injected EVM wallet to continue.", "warning"); return; }
  try {
    account = await walletAccount(provider, true);
    onChain = await walletOnMezo(provider);
    if (!account) announcement("The wallet did not provide an account.", "warning");
    else if (!onChain) announcement("Wallet connected. Switch to Mezo Testnet (chain 31611).", "warning");
    else announcement("Wallet connected on Mezo Testnet. No payment has been requested.");
  } catch (error) { announcement(walletError(error), "warning"); }
  updateControls();
  if (quote) renderQuote();
}

async function refreshWallet(): Promise<void> {
  provider = injectedWallet();
  if (!provider) { account = null; onChain = false; }
  else {
    try { account = await walletAccount(provider, false); onChain = await walletOnMezo(provider); }
    catch { account = null; onChain = false; }
  }
  if (flow && account && account.toLowerCase() !== flow.payer.toLowerCase()) announcement("Wallet changed. The saved quote remains bound to its original payer.", "warning");
  updateControls();
  if (quote) renderQuote();
}

el<HTMLButtonElement>("#connect-button").addEventListener("click", () => { void connectWallet(); });
el<HTMLButtonElement>("#switch-button").addEventListener("click", async () => {
  if (!provider) return;
  try { await switchToMezo(provider); await refreshWallet(); announcement("Wallet switched to Mezo Testnet."); }
  catch (error) { announcement(walletError(error), "warning"); }
});
el<HTMLButtonElement>("#refresh-button").addEventListener("click", () => { void resumeFlow(); });
el<HTMLButtonElement>("#new-button").addEventListener("click", () => {
  if (!flow || flow.paymentGuard !== "clear" || busy || polling ||
      (quote && ["PAYMENT_PENDING", "PAYMENT_UNCERTAIN", "MANUAL_REVIEW"].includes(quote.state))) return;
  if (!window.confirm("Start a new report? This browser session will forget the current report link and its capability-scoped recovery record.")) return;
  clearFlow();
  flow = null; quote = null; delivery = null;
  el<HTMLDivElement>("#result-content").replaceChildren(node("p", "empty-state", "Ready for another snapshot question."));
  announcement("New report form ready. No payment was submitted.");
  updateControls();
});

el<HTMLFormElement>("#report-form").addEventListener("submit", async event => {
  event.preventDefault();
  if (!cap?.payment_ready || cap.source_mode !== "live-public" || !bearer || !account || !onChain || flow || busy) return;
  const quantity = el<HTMLInputElement>("#quantity").value.trim();
  if (!/^(?:0|[1-9][0-9]*)(?:\.[0-9]{1,8})?$/.test(quantity) || !/[1-9]/.test(quantity)) {
    announcement("Enter a positive BTC quantity with no more than eight decimal places.", "error");
    el<HTMLInputElement>("#quantity").focus();
    return;
  }
  const side = el<HTMLInputElement>('input[name="side"]:checked').value as Side;
  flow = { version: 1, side, quantity, payer: account, idempotencyKey: crypto.randomUUID(), paymentGuard: "clear" };
  saveFlow(flow);
  announcement("Request saved in this browser session. Preparing report…");
  updateControls();
  await resumeFlow();
});

async function boot(): Promise<void> {
  try { bearer = capability(); flow = loadFlow(); }
  catch (error) { announcement(readableError(error), "error"); return; }
  if (flow) {
    el<HTMLInputElement>("#quantity").value = flow.quantity;
    el<HTMLInputElement>(`input[name="side"][value="${flow.side}"]`).checked = true;
  }
  provider?.on?.("accountsChanged", () => { void refreshWallet(); });
  provider?.on?.("chainChanged", () => { void refreshWallet(); });
  await refreshWallet();
  try {
    cap = await getCapabilities();
    renderCapability();
    if (!cap.payment_ready) announcement("The gateway has not enabled canonical payment. Review its current blockers.", "warning");
    else if (!x402Available()) announcement("Quotes can be reviewed, but payment remains disabled until the official browser SDK binding is verified.", "warning");
    else announcement("Mezo Testnet service is available. Connect your wallet to begin.");
  } catch (error) { announcement(readableError(error), "error"); }
  updateControls();
  if (flow) await resumeFlow();
}

void boot();
