import {
  financeLinks, formatMusd, fundingEligibility, readFundingObservation,
  type FinanceContext, type FinanceNetwork, type FinanceProvider, type FundingObservation,
} from './mezo-finance.mjs';

interface PanelContext extends Omit<FinanceContext, 'network'> {
  provider: FinanceProvider | null;
}
interface Options {
  host: HTMLElement;
  network: FinanceNetwork;
  getContext: () => PanelContext;
}

/** Assisted external-app funding; it never owns payment authority. */
export function mountMezoFinance(options: Options): { update(): void; dispose(): void } {
  const links = financeLinks(options.network.name);
  function element<K extends keyof HTMLElementTagNameMap>(tag: K, text = '', id = ''): HTMLElementTagNameMap[K] {
    const result = document.createElement(tag);
    result.textContent = text;
    if (id) result.id = id;
    return result;
  }
  function external(text: string, url: string, id = ''): HTMLAnchorElement {
    const result = element('a', text, id);
    result.href = url;
    result.target = '_blank';
    result.rel = 'noopener noreferrer';
    return result;
  }
  const root = element('details');
  root.className = 'status-card funding-panel';
  root.append(element('summary', 'MUSD funding for this report'));
  const borrow = element('section');
  borrow.append(element('h3', 'Borrow before payment'));
  borrow.append(element('p', 'Optional: use the official Mezo application to borrow MUSD against BTC, then return here. This is not a loan for the report price.'));
  const status = element('p', '', 'mezo-balance-status');
  status.setAttribute('role', 'status');
  status.setAttribute('aria-live', 'polite');
  const check = element('button', 'Check MUSD balance / refresh after borrowing', 'mezo-balance-check');
  check.type = 'button'; check.className = 'secondary-button';
  const blockStatus = element('p', '', 'mezo-balance-block');
  blockStatus.className = 'subtle breakable';
  const download = element('a', 'Download funding check JSON', 'mezo-observation-download');
  download.className = 'text-button';
  download.download = 'liqvera-musd-funding-check.json';
  const risk = element('p', 'Mezo documents a minimum new borrowed debt of 1,800 MUSD plus a 200 MUSD gas deposit, before other applicable fees. Review current terms. Loans carry interest and BTC liquidation risk. Funding an individual report does not require opening a loan.');
  const label = element('label');
  label.className = 'funding-acknowledgement';
  const ack = element('input', '', 'mezo-borrow-ack'); ack.type = 'checkbox';
  ack.setAttribute('aria-describedby', 'mezo-borrow-help mezo-balance-status');
  label.append(ack, element('span', ' I understand this opens a separate loan application, not a report payment.'));
  const help = element('p', 'First prepare an unpaid report and check its MUSD balance. This checkbox unlocks only if there is a shortfall.', 'mezo-borrow-help');
  help.className = 'subtle';
  const link = external('Open official Mezo borrowing app ↗', links.borrow, 'mezo-borrow-link');
  link.className = 'secondary-button';
  borrow.append(status, blockStatus, check, download, risk, help, label, link, external('Read Mezo borrowing terms ↗', links.borrowDocs));
  borrow.append(element('p', 'Returning does not trigger payment. Check the balance again, refresh the quote if it expired, and confirm the existing report payment separately.'));
  root.append(borrow);

  options.host.after(root);

  let disposed = false;
  let sequence = 0;
  let reading = false;
  let lastProvider: FinanceProvider | null = null;
  let lastKey = '';
  let lastBalance: { amount: bigint; at: number } | null = null;
  let observation: Readonly<FundingObservation> | null = null;
  let downloadUrl: string | null = null;
  let notice = '';

  function clearObservation(): void {
    lastBalance = null; observation = null;
    if (downloadUrl) URL.revokeObjectURL(downloadUrl);
    downloadUrl = null;
    download.removeAttribute('href');
  }

  function current(): PanelContext & { network: FinanceNetwork } {
    return { ...options.getContext(), network: options.network };
  }
  function identity(context: PanelContext): string {
    return JSON.stringify([context.account, context.quote, context.paymentGuard, context.busy, context.onMezo]);
  }
  function synchronize(context: PanelContext): void {
    const key = identity(context);
    if (key !== lastKey || context.provider !== lastProvider) {
      sequence++; reading = false; clearObservation(); notice = ''; ack.checked = false;
      lastKey = key; lastProvider = context.provider;
    }
  }
  function update(): void {
    if (disposed) return;
    const context = current();
    synchronize(context);
    const eligibility = fundingEligibility(context);
    const fresh = lastBalance !== null && Date.now() - lastBalance.at >= 0 && Date.now() - lastBalance.at < 30000;
    if (!fresh || !eligibility.allowed) clearObservation();
    const shortfall = lastBalance && eligibility.requiredAtomic > lastBalance.amount
      ? eligibility.requiredAtomic - lastBalance.amount : 0n;
    check.disabled = reading || !context.provider || !eligibility.allowed;
    ack.disabled = !eligibility.allowed || !fresh || shortfall === 0n || reading;
    if (reading) status.textContent = 'Reading MUSD balance. No signature is requested.';
    else if (!eligibility.allowed) status.textContent = eligibility.reason;
    else if (notice) status.textContent = notice;
    else if (fresh && lastBalance) status.textContent = shortfall > 0n
      ? `Balance: ${formatMusd(lastBalance.amount)} MUSD. Shortfall: ${formatMusd(shortfall)} MUSD.`
      : `Balance: ${formatMusd(lastBalance.amount)} MUSD is sufficient for this quote. No new loan is needed. Confirm payment separately.`;
    else status.textContent = 'Check the selected wallet balance. The read does not connect another wallet or authorize payment.';
    if (fresh && observation && eligibility.allowed) {
      status.textContent += ` Budget at this quote price: ${observation.report_budget} report purchases. This is an estimate, not reserved funds.`;
      blockStatus.textContent = `Block ${observation.block_number} · ${observation.block_hash} · ${observation.observed_at}. Wallet-reported observation; not proof of a loan or payment.`;
      if (downloadUrl) download.href = downloadUrl;
    } else blockStatus.textContent = '';
    download.hidden = !download.hasAttribute('href');
    const canLeave = eligibility.allowed && fresh && shortfall > 0n && ack.checked && !reading;
    if (canLeave) link.href = links.borrow;
    else link.removeAttribute('href');
    link.setAttribute('aria-disabled', String(!canLeave));
    link.tabIndex = canLeave ? 0 : -1;
  }
  check.addEventListener('click', async () => {
    if (disposed) return;
    const context = current(); synchronize(context);
    if (reading || !context.provider || !context.account || !fundingEligibility(context).allowed) { update(); return; }
    const key = identity(context), selected = context.provider, attempt = ++sequence;
    reading = true; notice = ''; clearObservation(); ack.checked = false; update();
    const ownsResult = () => !disposed && sequence === attempt && options.getContext().provider === selected && identity(options.getContext()) === key;
    try {
      const result = await readFundingObservation(selected, options.network, context.account, context.quote!.terms.amount_atomic);
      if (ownsResult()) {
        observation = result;
        lastBalance = { amount: BigInt(result.balance_atomic), at: Date.now() };
        downloadUrl = URL.createObjectURL(new Blob([JSON.stringify({ ...result, quote_id: context.quote!.quote_id }, null, 2) + '\n'], { type: 'application/json' }));
      }
    } catch {
      if (ownsResult()) notice = 'Balance could not be verified. Check the selected wallet, Mezo network and RPC, then retry this read. No payment was submitted.';
    } finally {
      if (ownsResult()) reading = false;
      update();
    }
  });
  ack.addEventListener('change', update);
  link.addEventListener('click', event => {
    update();
    if (!link.hasAttribute('href')) event.preventDefault();
  });
  download.addEventListener('click', event => {
    update();
    if (!download.hasAttribute('href')) event.preventDefault();
  });
  // Re-evaluate expiry and read freshness without making background RPC calls.
  const timer = setInterval(update, 1000);
  update();
  return { update, dispose() { disposed = true; sequence++; clearInterval(timer); clearObservation(); root.remove(); } };
}
