import {TROVE_PREVIEW,verifyTrovePreview} from "./trove-preview";
import {getAddress} from "viem";
import {mountTroveRisk} from "./trove-panel";
import {mountTroveProtection} from "./trove-protection-panel";
import "./style.css";
import { mountMezoDex } from "./mezo-dex-panel";
import {mountMezoSalePlanner} from "./mezo-sale-panel";
import { MEZO, MUSD, NETWORK_CONFIG, NETWORK_LABEL, TOKEN_LABEL } from "./network.ts";
import { mountMezoFinance } from "./mezo-finance-panel";
import { ApiFailure, createQuote, getCapabilities, getEvidence, getQuote, getReport, getRequest } from "./api";
import { canPay, paymentNotice, walletStatus } from "./browser-flow";
import { executePaymentAttempt, executeRecovery } from "./browser-orchestration";
import { quoteIsPayable, receiptMatchesQuote, reportMatchesQuote, type Capabilities, type Delivery, type Quote, type RequestStatus, type Side } from "./contracts";
import { capability, clearFlow, loadFlow, saveFlow, type SavedFlow } from "./session";
import { injectedWallet, switchToMezo, walletAccount, walletError, walletOnMezo, type Eip1193Provider } from "./wallet";
import { createWalletListenerOwner, type WalletState } from "./wallet-events";
import { createWalletModal } from "./wallet-modal";
import { discoverWalletChoices, walletChoices, walletStore, type WalletChoice } from "./wallet-discovery";
import { installProductionX402Adapter, requestPaidReport, x402Available, X402CancelledBeforeSubmission } from "./x402";
import { formatHistoricalDate, HISTORICAL_DEMO, verifyHistoricalAssets } from "./historical-demo";

installProductionX402Adapter();

const app = document.querySelector<HTMLDivElement>("#app");
if (!app) throw new Error("App root missing.");

app.innerHTML = `
  <a class="skip-link" href="#workspace">Skip to report workspace</a>
  <div class="page-shell">
    <header class="site-header">
      <a class="brand" href="/" aria-label="Liqvera home"><span class="brand-mark" aria-hidden="true">L</span><span>Liqvera</span></a>
      <div class="header-right"><span class="network-chip"><span class="pulse-dot" aria-hidden="true"></span> ${NETWORK_LABEL.toUpperCase()}</span><span class="header-caption">Market reports you can verify.</span></div>
    </header>
    <main id="workspace">
      <section class="hero" aria-labelledby="hero-title">
        <div class="hero-copy"><p class="eyebrow">PUBLIC MARKET DATA · PRIVATE ACCESS</p><h1 id="hero-title">A clearer view of the <em>available</em> book.</h1><p class="lead">Explore a hypothetical sweep of a public Hyperliquid BTC perpetual snapshot. Review the evidence before trusting the calculation.</p></div>
        <div class="hero-aside" aria-label="Product boundaries"><div class="aside-label">REPORT BOUNDARIES</div><p>Public market data</p><p>User-signed Mezo spot and Trove actions</p><p>${NETWORK_LABEL} payments</p></div>
      </section>
      <div class="workspace-grid">
        <section class="panel request-panel" aria-labelledby="request-title">
          <div class="panel-heading"><span class="step">STEP 1</span><div><p class="eyebrow">BUILD A REPORT</p><h2 id="request-title">Set your snapshot question</h2></div></div>
          <p class="supporting">This is a calculation over the available snapshot depth, not a complete exchange book or guaranteed execution.</p>
          <div class="segment product-selector" role="group" aria-label="Report product">
            <button id="market-tab" type="button" class="secondary-button" aria-pressed="true">Market depth</button>
            <button id="trove-tab" type="button" class="secondary-button" aria-pressed="false">Trove risk</button>
          </div>
          <p id="trove-availability" class="field-hint hidden">Trove creation is currently unavailable. Existing reports can still be recovered.</p>
          <div id="market-instrument" class="instrument"><span class="instrument-icon" aria-hidden="true">₿</span><span><strong>BTC linear perpetual</strong><small>Hyperliquid public order book</small></span><span class="readonly-tag">READ ONLY</span></div>
          <form id="report-form" novalidate>
            <div id="market-fields"><fieldset><legend>Hypothetical side</legend><div class="segment"><label><input type="radio" name="side" value="BUY" checked /><span>BUY</span></label><label><input type="radio" name="side" value="SELL" /><span>SELL</span></label></div></fieldset>
            <label class="field-label" for="quantity">Quantity <span>BTC</span></label><input id="quantity" name="quantity" type="text" inputmode="decimal" autocomplete="off" spellcheck="false" value="0.15" aria-describedby="quantity-hint" /><p id="quantity-hint" class="field-hint">A positive decimal string, up to 8 places. The report shows a hypothetical sweep.</p></div>
            <div id="trove-fields" class="hidden">
              <label class="field-label" for="borrower">Borrower address</label>
              <input id="borrower" type="text" autocomplete="off" spellcheck="false" placeholder="0x…" aria-describedby="trove-hint" />
              <p id="trove-hint" class="field-hint">Mezo Testnet debt, collateral and redemption queue at one block. Read only. Not financial advice.</p>
              <button id="trove-preview-button" type="button" class="secondary-button">Show sealed Trove example</button>
            </div>
            <div class="wallet-box"><div><span class="eyebrow">EXPECTED PAYER</span><strong id="wallet-label">No wallet connected</strong><span id="chain-label">Connect an EVM wallet on ${NETWORK_LABEL}.</span></div><div class="wallet-actions"><label for="wallet-provider" class="field-hint">Wallet provider</label><select id="wallet-provider" class="hidden" aria-label="Choose wallet provider"></select><button id="connect-button" type="button" class="text-button">Connect wallet</button><button id="switch-button" type="button" class="text-button hidden">Switch network</button></div></div>
            <div id="wallet-help" class="hidden">
              <p class="supporting">Use your preferred EVM wallet that supports ${NETWORK_LABEL}. On your phone, open liqvera.site in your wallet’s browser, then tap Connect wallet.</p>
              <p class="subtle">Optional shortcut for Trust Wallet users:</p>
              <a id="trust-wallet-link" class="secondary-button" href="https://link.trustwallet.com/open_url?coin_id=60&amp;url=https%3A%2F%2Fliqvera.site">Open in Trust Wallet</a>
              <p class="subtle">On a computer, enable your wallet browser extension. If several wallets are detected, choose one from the Wallet provider list.</p>
            </div>
            <details id="network-help" class="hidden">
              <summary>Set up ${NETWORK_LABEL} in your wallet</summary>
              <p class="supporting">Preparing a report does not require a network switch. To pay and unlock it, select ${NETWORK_LABEL} in your wallet. If it is missing, add a custom network with these settings:</p>
              <p class="subtle">Network: ${MEZO.name}<br />Chain ID: ${MEZO.chainId}<br />RPC: ${MEZO.rpcUrl}<br />Currency: BTC<br />Explorer: ${MEZO.explorerUrl}</p>
              <p class="subtle">After selecting the network in your wallet, tap Connect wallet to refresh.</p>
            </details>
            <button id="create-button" class="primary-button" type="submit" disabled>Request a report <span aria-hidden="true">↗</span></button>
            <p id="create-note" class="form-note">Checking service capabilities…</p>
          </form>
        </section>
        <section class="panel result-panel" aria-labelledby="result-title">
          <div class="panel-heading"><span class="step">STEP 2</span><div><p class="eyebrow">STATUS & DELIVERY</p><h2 id="result-title">Your report</h2></div></div>
          <div id="announcement" class="announcement" role="status" aria-live="polite">Checking capabilities and saved session…</div>
          <div id="capability-status" class="capability-status"></div>
          <div id="result-content" class="result-content"><div class="empty-state"><div class="empty-graphic" aria-hidden="true"><span></span><span></span><span></span><span></span></div><h3>Waiting for a question</h3><p>Connect your wallet and ask for a fresh paid report, or inspect the sealed historical live example.</p><button id="historical-button" class="secondary-button" type="button">Show latest live report</button></div></div>
          <div class="result-actions"><button id="refresh-button" class="secondary-button hidden" type="button">Check status</button><button id="new-button" class="text-button hidden" type="button">Start another report</button></div>
        </section>
      </div>
      <section class="boundary-strip" aria-label="Important context"><div><span>NOTE 1</span><p><strong>Snapshot, not a signal.</strong> Available levels support the arithmetic; they do not establish a trading opportunity.</p></div><div><span>NOTE 2</span><p><strong>Verifiable evidence.</strong> A downloadable bundle supports offline recalculation after entitlement.</p></div><div><span>NOTE 3</span><p><strong>User signed actions.</strong> Mezo spot swaps and Trove updates require your wallet; no perpetual orders or custody.</p></div></section>
    </main>
    <footer><span>Liqvera v0.0.5 · Market reports you can verify.</span><span>Built for MEZO ₿ · ${NETWORK_LABEL} · <a href="https://github.com/Dimkox/liqvera" target="_blank" rel="noopener noreferrer" aria-label="Liqvera project repository on GitHub">Project repository ↗</a> · <a href="https://github.com/Dimkox/liqvera/releases" target="_blank" rel="noopener noreferrer" aria-label="Liqvera releases on GitHub">Project releases ↗</a> · <a href="https://github.com/Dimkox/Getzilla" target="_blank" rel="noopener noreferrer" aria-label="Getzilla project repository on GitHub">Getzilla ↗</a></span></footer>
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

function snapshotAge(value: string): string {
  const elapsed = Date.now() - Date.parse(value);
  if (!Number.isFinite(elapsed)) return "Unknown age";
  if (elapsed < 0) return "Clock difference detected";
  const minutes = Math.floor(elapsed / 60000);
  return minutes < 1 ? "Less than a minute old" : `${minutes} minute${minutes === 1 ? "" : "s"} old now`;
}

let historicalDownloadUrl:string|null=null;
async function showHistoricalReport():Promise<void> {
  const target=el<HTMLDivElement>("#result-content");
  target.replaceChildren(node("p","status-card","Loading sealed historical report…"));
  announcement("Loading sealed historical report. No wallet or payment is required.");
  try {
    const [reportResponse,bundleResponse]=await Promise.all([
      fetch(HISTORICAL_DEMO.reportUrl,{credentials:"omit",redirect:"error"}),
      fetch(HISTORICAL_DEMO.bundleUrl,{credentials:"omit",redirect:"error"}),
    ]);
    if(!reportResponse.ok||!bundleResponse.ok)throw new Error("Historical preview could not be loaded.");
    const reportBytes=new Uint8Array(await reportResponse.arrayBuffer());
    const bundleBytes=new Uint8Array(await bundleResponse.arrayBuffer());
    const report=await verifyHistoricalAssets(reportBytes,bundleBytes);
    const card=node("div","status-card");
    card.append(node("p","eyebrow","HISTORICAL LIVE PUBLIC PREVIEW"),node("h3","",report.mezo_dex ? "Sealed Mezo DEX and Hyperliquid report" : "Sealed Hyperliquid BTC perpetual report"));
    const grid=node("div","data-grid report-grid");
    appendField(grid,"Captured at",formatHistoricalDate(HISTORICAL_DEMO.sourceAt));
    appendField(grid,"Report ID",HISTORICAL_DEMO.reportId,"breakable span-all");
    appendField(grid,"Report SHA-256",HISTORICAL_DEMO.reportSha256,"breakable span-all");
    appendField(grid,"Bundle SHA-256",HISTORICAL_DEMO.bundleSha256,"breakable span-all");
    appendField(grid,"Snapshot calculation",`${report.request.side} ${report.request.quantity_base} BTC · VWAP ${report.calculation.display.vwap}`);
    card.append(grid,node("p","safety-note","Sealed historical capture; see its timestamp above. It is not fresh market data, an execution promise, or a new run. No payment transaction exists for this public preview."));
    mountMezoDex(card, report);
    if(historicalDownloadUrl)URL.revokeObjectURL(historicalDownloadUrl);
    historicalDownloadUrl=URL.createObjectURL(new Blob([bundleBytes],{type:"application/zip"}));
    const download=document.createElement("a");download.className="secondary-button";download.href=historicalDownloadUrl;
    download.download="liqvera-historical-live-evidence.zip";download.textContent="Download evidence ZIP";
    card.append(download);target.replaceChildren(card);announcement("Historical sealed report loaded. Payment is not required.");
  } catch { target.replaceChildren(node("p","safety-note","Historical preview could not be loaded. The paid fresh-report flow is unchanged."));announcement("Historical preview could not be loaded.","error"); }
}

let cap: Capabilities | null = null;
let bearer: string | null = null;
let provider: Eip1193Provider | null = injectedWallet();
let choices:WalletChoice[]=[];
let account: string | null = null;
let onChain = false;
let flow: SavedFlow | null = null;
async function showTrovePreview():Promise<void> {
  if(flow || busy || polling) {announcement("Recover the saved report before opening another example.","warning");return;}
  setBusy(true);
  const target=el<HTMLDivElement>("#result-content");
  target.replaceChildren(node("p","status-card","Loading sealed Trove evidence…"));
  try {
    const [rr,br]=await Promise.all([fetch(TROVE_PREVIEW.reportUrl,{credentials:"omit",redirect:"error"}),
      fetch(TROVE_PREVIEW.bundleUrl,{credentials:"omit",redirect:"error"})]);
    if(!rr.ok||!br.ok)throw new Error("Trove preview could not be loaded.");
    const reportBytes=new Uint8Array(await rr.arrayBuffer()),bundleBytes=new Uint8Array(await br.arrayBuffer());
    const report=await verifyTrovePreview(reportBytes,bundleBytes);
    const card=node("div","status-card");
    card.append(node("p","eyebrow","SEALED HISTORICAL TROVE EXAMPLE"),node("p","safety-note",
      `Captured ${formatHistoricalDate(report.source.source_at)}. This retained snapshot is not current risk data. No payment was made for this public example.`));
    mountTroveRisk(card,report);
    for(const [label,url] of [["Download report JSON",TROVE_PREVIEW.reportUrl],["Download evidence ZIP",TROVE_PREVIEW.bundleUrl]] as const) {
      const link=node("a","secondary-button",label);link.href=url;link.download="";card.append(link);
    }
    appendField(card,"Report SHA-256",TROVE_PREVIEW.reportSha256,"breakable");
    appendField(card,"Evidence SHA-256",TROVE_PREVIEW.bundleSha256,"breakable");
    target.replaceChildren(card);announcement("Sealed Trove example verified. No wallet or payment required.");
  } catch(error) {target.replaceChildren(node("p","safety-note",readableError(error)));announcement("Trove preview withheld: evidence could not be verified.","error");}
  finally {setBusy(false);}
}

let product: "market_depth" | "trove_risk" = "market_depth";
let quote: Quote | null = null;
let delivery: Delivery | null = null;
let busy = false;
let polling = false;
const walletListeners=createWalletListenerOwner({applyWalletState});
declare const __LIQVERA_WALLETCONNECT_PROJECT_ID__: string;
const walletProjectId = __LIQVERA_WALLETCONNECT_PROJECT_ID__;
const walletModal = walletProjectId ? createWalletModal(
  async () => (await import("./wallet-appkit")).loadWalletAppKit(walletProjectId),
  selected => {
    if (provider === selected) return;
    walletListeners.replace(selected);
    provider = selected;
    applyWalletState({ account: null, onMezo: false });
    void refreshWallet();
  },
) : null;

const fundingPanel = mountMezoFinance({
  host: el<HTMLElement>("#result-content"),
  network: { name: NETWORK_CONFIG.name, chainId: MEZO.chainId, asset: MUSD.address, decimals: MUSD.decimals },
  getContext: () => ({ provider, account, quote, paymentGuard: flow?.paymentGuard ?? "unavailable", busy: busy || polling, onMezo: onChain }),
});
window.addEventListener("pagehide", event => { if (!event.persisted) fundingPanel.dispose(); });

function setBusy(value: boolean): void {
  busy = value;
  updateControls();
}

function updateControls(): void {
  fundingPanel.update();
  const ready = Boolean(cap?.payment_ready && cap.source_mode === "live-public");
  const productReady = product === "market_depth" || Boolean(cap?.products?.includes("trove_risk"));
  const canCreate = productReady && ready && x402Available() && Boolean(bearer && account && !flow) && !busy;
  el<HTMLButtonElement>("#create-button").disabled = !canCreate;
  el<HTMLButtonElement>("#trove-preview-button").disabled = Boolean(flow) || busy || polling;
  el<HTMLElement>("#market-fields").classList.toggle("hidden", product !== "market_depth");
  el<HTMLElement>("#market-instrument").classList.toggle("hidden", product !== "market_depth");
  el<HTMLElement>("#trove-fields").classList.toggle("hidden", product !== "trove_risk");
  el<HTMLElement>("#trove-availability").classList.toggle("hidden", product !== "trove_risk" || productReady);
  for(const [id,active] of [["market-tab",product === "market_depth"],["trove-tab",product === "trove_risk"]] as const) {
    el<HTMLButtonElement>(`#${id}`).setAttribute("aria-pressed",String(active));
    el<HTMLButtonElement>(`#${id}`).disabled = Boolean(flow) || busy || polling;
  }
  el<HTMLButtonElement>("#connect-button").textContent = walletModal && account ? "Manage wallet" : "Connect wallet";
  el<HTMLButtonElement>("#refresh-button").classList.toggle("hidden", !flow);
  el<HTMLButtonElement>("#refresh-button").disabled = busy || polling;
  const lock = flow?.paymentGuard !== "clear" || (quote && ["PAYMENT_PENDING", "PAYMENT_UNCERTAIN", "MANUAL_REVIEW"].includes(quote.state));
  el<HTMLButtonElement>("#new-button").classList.toggle("hidden", !flow || Boolean(lock));
  el<HTMLButtonElement>("#new-button").disabled = busy || polling;
  el<HTMLButtonElement>("#switch-button").classList.toggle("hidden", !provider || onChain);
  el<HTMLDetailsElement>("#network-help").classList.toggle("hidden", !account || onChain);
  el<HTMLElement>("#wallet-label").textContent = account ? `${account.slice(0, 8)}…${account.slice(-6)}` : "No wallet connected";
  el<HTMLElement>("#chain-label").textContent = walletStatus(Boolean(provider), onChain);
  el<HTMLElement>("#create-note").textContent = !cap ? "Checking service capabilities…" :
    !productReady ? "Trove creation is currently unavailable; saved reports remain recoverable." :
    !cap.payment_ready ? "Payment and new quotes are currently unavailable." :
    !x402Available() ? "The browser payment adapter awaits SDK verification; no payment can be submitted." :
    !account ? "Connect your wallet to continue." :
    flow ? "This session already has a report. Check its status or start another after it finishes." :
    !onChain ? `You can prepare a report now. Switch to ${NETWORK_LABEL} to pay and unlock it.` :
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
  fundingPanel.update();
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
  if(q.preview.product_id === "trove_risk") {
    appendField(grid,"Product","Mezo Trove risk","span-all");
    appendField(grid,"Borrower",q.preview.borrower,"breakable span-all");
    appendField(grid,"Trove status",q.preview.trove_status);
  } else {
    appendField(grid, "Instrument", "Hyperliquid BTC linear perpetual", "span-all");
    appendField(grid, "Hypothetical side", q.preview.side);
    appendField(grid, "Quantity", `${q.preview.quantity_base} BTC`);
  }
  appendField(grid, "Snapshot time", formatHistoricalDate(q.preview.snapshot_at), "span-all");
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
  terms.append(node("p", "eyebrow", `${NETWORK_LABEL.toUpperCase()} ACCESS TERMS`));
  const termsGrid = node("div", "data-grid");
  appendField(termsGrid, "Price", `${q.terms.price_musd} ${TOKEN_LABEL}`);
  appendField(termsGrid, "Atomic amount", q.terms.amount_atomic);
  appendField(termsGrid, "Network", `${NETWORK_LABEL} · ${q.terms.network}`);
  appendField(termsGrid, "Token", q.terms.asset, "breakable span-all");
  appendField(termsGrid, "Recipient", q.terms.pay_to, "breakable span-all");
  appendField(termsGrid, "Expected payer", q.terms.expected_payer, "breakable span-all");
  appendField(termsGrid, "Quote expires", formatHistoricalDate(q.terms.expires_at), "span-all");
  appendField(termsGrid, "Paid report retention", `At least ${q.retention.paid_days} days`);
  appendField(termsGrid, "Unpaid cleanup grace", `At least ${q.retention.unpaid_grace_seconds} seconds`);
  appendField(termsGrid, "Ledger retention", `At least ${q.retention.ledger_days} days`);
  terms.append(termsGrid);
  target.append(terms);
  const safetyNotice = paymentNotice(q.state, flow?.paymentGuard ?? null);
  if (safetyNotice) {
    target.append(node("p", "safety-note", safetyNotice));
  } else if (q.state === "EXPIRED") {
    target.append(node("p", "safety-note", "This quote expired. It cannot be paid. Start a new report only after the previous payment status is known."));
  } else if (q.state === "READY") {
    const paymentAllowed = canPay({ flow, quoteState: q.state, connectedAccount: account, onMezo: onChain,
      paymentReady: Boolean(cap?.payment_ready), adapterAvailable: x402Available() }) && quoteIsPayable(q, account ?? "");
    const button = node("button", "primary-button", `Confirm ${NETWORK_LABEL} payment in wallet`);
    button.type = "button";
    button.disabled = !paymentAllowed || busy;
    button.addEventListener("click", () => { void submitPayment(); });
    target.append(button);
    if (!x402Available()) target.append(node("p", "form-note", "The reviewed x402 browser adapter is not installed. No payment can be submitted from this build."));
    else if (account?.toLowerCase() !== q.terms.expected_payer.toLowerCase()) target.append(node("p", "safety-note", "The connected wallet differs from the quote payer. Reconnect the quoted wallet; this quote cannot be paid by another account."));
    else if (!onChain) target.append(node("p", "safety-note", `Switch the wallet to ${NETWORK_LABEL} before payment.`));
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
  if(report.schema === "liqvera-trove-risk-report/v1") { mountTroveRisk(target,report); mountTroveProtection(target,report,provider,account); }
  else {
    target.append(node("p", "supporting", "Hypothetical snapshot sweep over the available public order-book depth. No exchange trade occurred."));
    const grid = node("div", "data-grid report-grid");
    appendField(grid, "Side & size", `${report.request.side} ${report.request.quantity_base} BTC`);
    appendField(grid, "Snapshot time", formatHistoricalDate(report.source.source_at));
    appendField(grid, "Snapshot age now", snapshotAge(report.source.source_at));
    appendField(grid, "Sampled levels", `${report.source.available_bid_levels} bid / ${report.source.available_ask_levels} ask`);
    appendField(grid, "VWAP (display)", report.calculation.display.vwap);
    appendField(grid, "Worst price (display)", report.calculation.display.worst_price);
    appendField(grid, "Consumed levels", String(report.calculation.consumed_levels));
    appendField(grid, "Price impact (display)", `${report.calculation.display.price_impact_bps} bps`);
    appendField(grid, "Hypothetical notional", report.calculation.display.notional_quote);
    appendField(grid, "Snapshot execution authority", report.boundaries.execution_authority);
    target.append(grid);
    mountMezoDex(target, report);
    mountMezoSalePlanner(target,report,provider,account);
  }
  const limitations = node("div", "limitations");
  limitations.append(node("strong", "", "Evidence and limits"));
  const list = node("ul");
  for (const item of report.quality.limitations) list.append(node("li", "", item));
  list.append(node("li", "", "Hashes and recalculation support reproducibility; they do not prove the exchange signed the data or predict a future fill."));
  limitations.append(list);
  target.append(limitations);
  const receiptBox = node("div", "terms-box");
  receiptBox.append(node("p", "eyebrow", `${NETWORK_LABEL.toUpperCase()} RECEIPT`));
  const receiptGrid = node("div", "data-grid");
  appendField(receiptGrid, "Report SHA-256", receipt.report_sha256, "breakable span-all");
  appendField(receiptGrid, "Payment", `${q.terms.price_musd} ${TOKEN_LABEL}`);
  appendField(receiptGrid, "Confirmed", formatHistoricalDate(receipt.confirmed_at));
  appendField(receiptGrid, "Block / log", `${receipt.block_number} / ${receipt.log_index}`);
  appendField(receiptGrid, "Finality policy", receipt.finality_policy_version);
  appendField(receiptGrid, "Transaction", receipt.tx_hash, "breakable span-all");
  receiptBox.append(receiptGrid);
  if (/^0x[0-9a-f]{64}$/.test(receipt.tx_hash)) {
    const explorerBase = new URL(MEZO.explorerUrl);
    if (explorerBase.protocol === "https:" && ["https://explorer.test.mezo.org", "https://explorer.mezo.org"].includes(explorerBase.origin)) {
      const explorer = node("a", "external-link", `View ${NETWORK_LABEL} transaction ↗`);
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
  const subjectMatches = flow.version === 2 ? next.preview.product_id === "trove_risk" && next.preview.borrower === flow.borrower :
    next.preview.product_id === undefined && next.preview.side === flow.side && canonicalQuantity(next.preview.quantity_base) === canonicalQuantity(flow.quantity);
  if (!subjectMatches) {
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
  if (!receiptMatchesQuote(result.receipt, quote) || !reportMatchesQuote(result.report, quote) || result.report.report_id !== quote.report_id) {
    throw new Error("Receipt does not match the quoted report. Delivery is withheld.");
  }
  delivery = result;
  if (flow) { flow.paymentGuard = "clear"; saveFlow(flow); }
  renderDelivery();
  announcement("Paid report recovered. The receipt and evidence are available without another payment.");
  return "delivered";
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
    const recovered = await executeRecovery(flow, {
      getQuote: id => getQuote(bearer!, id),
      getRequest: id => getRequest(bearer!, id),
      createQuote: input => createQuote(bearer!, input),
      getPaidDelivery: async id => {
        const result = await getReport(bearer!, id);
        if (result === "recovering" || result === "payment-required") return null;
        return result;
      },
      onQuote: rememberQuote,
      onRequest: status => {
        if (flow && !flow.requestId) { flow.requestId = status.report_request_id; saveFlow(flow); }
        renderRequest(status);
      },
      onDelivery: paid => {
        if (!quote || !receiptMatchesQuote(paid.receipt, quote) || !reportMatchesQuote(paid.report, quote) || paid.report.report_id !== quote.report_id) {
          throw new Error("Receipt does not match the quoted report. Delivery is withheld.");
        }
        delivery = paid;
        if (flow) { flow.paymentGuard = "clear"; saveFlow(flow); }
        renderDelivery();
      },
      notice: message => announcement(message),
    });
    if (recovered.kind === "request" && recovered.request.state === "PREPARING") {
      setBusy(false); await pollRequest(); return;
    }
    if (recovered.kind === "quote" && ["PAYMENT_PENDING", "PAYMENT_UNCERTAIN"].includes(recovered.quote.state)) {
      setBusy(false); await pollQuote(); return;
    }
    if (recovered.kind === "quote" && recovered.quote.state === "PAID" && !delivery) {
      setBusy(false); await pollPaidDelivery(); return;
    }
  } catch (error) { announcement(readableError(error), "error"); }
  finally { setBusy(false); }
}

async function submitPayment(): Promise<void> {
  if (!quote || !flow || !bearer || !provider || !account || busy || !cap?.payment_ready ||
      flow.paymentGuard !== "clear" || !x402Available() || !quoteIsPayable(quote, account)) return;
  setBusy(true);
  try {
    const activeQuote = quote;
    flow = await executePaymentAttempt(flow, activeQuote, {
      validateWallet: async () => {
        if (!(await walletOnMezo(provider!)) || (await walletAccount(provider!, false))?.toLowerCase() !== activeQuote.terms.expected_payer.toLowerCase()) {
          throw new Error("Wallet network or account changed. Reconnect the quoted payer before continuing.");
        }
      },
      requestPaidReport: async () => (await requestPaidReport({ path: `/v1/reports/${activeQuote.report_id}`,
        bearerCapability: bearer!, quote: activeQuote, provider: provider!, payer: account! })) === "recovering" ? "recovering" : "submitted",
      refreshQuote: async () => {
        const latest = await getQuote(bearer!, activeQuote.quote_id);
        rememberQuote(latest);
        if (latest.state === "PAID") await recoverDelivery();
        return latest;
      },
      isPreSubmitCancellation: error => error instanceof X402CancelledBeforeSubmission,
      persist: next => { saveFlow(next as SavedFlow); renderQuote(); },
      notice: message => announcement(message, "warning"),
    });
  } finally { setBusy(false); if (delivery) renderDelivery(); else renderQuote(); }
}

async function connectWallet(): Promise<void> {
  if (walletModal) {
    try { await walletModal.open(); }
    catch { announcement("Wallet connection could not open. Check your connection and try Connect wallet again.", "warning"); }
    return;
  }
  choices=await discoverWalletChoices(walletStore,injectedWallet());
  renderProviderChoices();
  const selected=el<HTMLSelectElement>("#wallet-provider").value;
  const selectedProvider=(choices.find(item=>item.id===selected)??choices[0])?.provider??null;
  walletListeners.replace(selectedProvider);provider=selectedProvider;
  applyWalletState({account:null,onMezo:false});
  el<HTMLElement>("#wallet-help").classList.toggle("hidden", Boolean(provider));
  if (!provider) {
    announcement("Open liqvera.site in your EVM wallet’s browser, or enable a wallet extension, then connect.", "warning");
    return;
  }
  try {
    account = await walletAccount(provider, true);
    if (account) await switchToMezo(provider);
    onChain = await walletOnMezo(provider);
    if (!account) announcement("The wallet did not provide an account.", "warning");
    else if (!onChain) announcement(`Wallet could not switch to ${NETWORK_LABEL} (chain ${MEZO.chainId}).`, "warning");
    else announcement(`Wallet connected on ${NETWORK_LABEL}. No payment has been requested.`);
  } catch (error) { await refreshWallet(); announcement(walletError(error), "warning"); }
  updateControls();
  if (quote) renderQuote();
  if (delivery) renderDelivery();
}

function renderProviderChoices():void {
  const select=el<HTMLSelectElement>("#wallet-provider");const previous=select.value;select.replaceChildren();
  for(const choice of choices){const option=document.createElement("option");option.value=choice.id;option.textContent=choice.name;select.append(option);}
  if(choices.some(item=>item.id===previous))select.value=previous;
  select.classList.toggle("hidden",choices.length<=1);
}
function refreshProviderChoices():void {
  choices=walletChoices(walletStore,injectedWallet());
  renderProviderChoices();
}

async function refreshWallet(): Promise<void> {
  await walletListeners.refresh();
}

function applyWalletState(state: WalletState): void {
  account = state.account; onChain = state.onMezo;
  if(account && !el<HTMLInputElement>("#borrower").value) el<HTMLInputElement>("#borrower").value=getAddress(account.toLowerCase());
  if (flow && account && account.toLowerCase() !== flow.payer.toLowerCase()) announcement("Wallet changed. The saved quote remains bound to its original payer.", "warning");
  updateControls();
  if (quote) renderQuote();
  if (delivery) renderDelivery();
}

el<HTMLButtonElement>("#connect-button").addEventListener("click", () => { void connectWallet(); });
el<HTMLButtonElement>("#switch-button").addEventListener("click", async () => {
  if (!provider) return;
  try {
    if (walletModal) await walletModal.switchNetwork();
    else await switchToMezo(provider);
    await refreshWallet();
    announcement(`Wallet switched to ${NETWORK_LABEL}.`);
  }
  catch (error) {
    await refreshWallet();
    el<HTMLDetailsElement>("#network-help").open = true;
    announcement(`${walletError(error)} Select ${NETWORK_LABEL} in your wallet using the network settings in the report form.`, "warning");
  }
});
for(const [id,next] of [["market-tab","market_depth"],["trove-tab","trove_risk"]] as const) {
  el<HTMLButtonElement>(`#${id}`).addEventListener("click",()=>{if(flow||busy||polling)return;product=next;updateControls();});
}
el<HTMLButtonElement>("#refresh-button").addEventListener("click", () => { void resumeFlow(); });
el<HTMLButtonElement>("#trove-preview-button").addEventListener("click",()=>{void showTrovePreview();});
el<HTMLButtonElement>("#historical-button").addEventListener("click", () => { void showHistoricalReport(); });
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
  if (!cap?.payment_ready || cap.source_mode !== "live-public" || !bearer || !account || flow || busy) return;
  if(product === "trove_risk") {
    if(!cap.products?.includes("trove_risk")) return;
    try {
      const borrower=getAddress(el<HTMLInputElement>("#borrower").value.trim());
      if(/^0x0{40}$/.test(borrower)) throw new Error("Zero address");
      flow={version:2,product_id:"trove_risk",borrower,payer:account,idempotencyKey:crypto.randomUUID(),paymentGuard:"clear"};
    } catch {announcement("Enter a valid nonzero borrower address.","error");el<HTMLInputElement>("#borrower").focus();return;}
  } else {
    const quantity = el<HTMLInputElement>("#quantity").value.trim();
    if (!/^(?:0|[1-9][0-9]*)(?:\.[0-9]{1,8})?$/.test(quantity) || !/[1-9]/.test(quantity)) {
      announcement("Enter a positive BTC quantity with no more than eight decimal places.", "error");
      el<HTMLInputElement>("#quantity").focus();
      return;
    }
    const side = el<HTMLInputElement>('input[name="side"]:checked').value as Side;
    flow = { version: 1, side, quantity, payer: account, idempotencyKey: crypto.randomUUID(), paymentGuard: "clear" };
  }
  saveFlow(flow);
  announcement("Request saved in this browser session. Preparing report…");
  updateControls();
  await resumeFlow();
});

async function boot(): Promise<void> {
  try { bearer = capability(); flow = loadFlow(); }
  catch (error) { announcement(readableError(error), "error"); return; }
  if(flow?.version === 2) {
    product="trove_risk";el<HTMLInputElement>("#borrower").value=flow.borrower;
  } else if (flow) {
    el<HTMLInputElement>("#quantity").value = flow.quantity;
    el<HTMLInputElement>(`input[name="side"][value="${flow.side}"]`).checked = true;
  }
  if (walletModal) {
    provider = null;
    void walletModal.restore().catch(() => announcement("Wallet connection is temporarily unavailable. Try Connect wallet again.", "warning"));
  } else {
    refreshProviderChoices();provider=choices[0]?.provider??null;walletListeners.replace(provider);
    walletStore.subscribe(()=>refreshProviderChoices());
    await refreshWallet();
  }
  try {
    cap = await getCapabilities();
    renderCapability();
    if (!cap.payment_ready) announcement("The gateway has not enabled canonical payment. Review its current blockers.", "warning");
    else if (!x402Available()) announcement("Quotes can be reviewed, but payment remains disabled until the official browser SDK binding is verified.", "warning");
    else announcement(`${NETWORK_LABEL} service is available. Connect your wallet to begin.`);
  } catch (error) { announcement(readableError(error), "error"); }
  updateControls();
  if (flow) await resumeFlow();
}

void boot();
