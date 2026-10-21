/** Read-only MUSD funding checks. */
const MAX_UINT256 = (1n << 256n) - 1n;
const UNIT = 10n ** 18n;
const BORROW_DOCS = 'https://mezo.org/docs/users/borrow/mint-musd/';

function address(value) {
  return typeof value === 'string' && /^0x[0-9a-f]{40}$/i.test(value) && !/^0x0{40}$/i.test(value);
}

function atomic(value, positive = false) {
  if (typeof value !== 'string' || !/^(0|[1-9][0-9]{0,77})$/.test(value)) {
    throw new Error('Amounts must be canonical unsigned atomic decimal strings.');
  }
  const result = BigInt(value);
  if (result > MAX_UINT256 || (positive && result === 0n)) throw new Error('Amount is outside the supported range.');
  return result;
}

function validateNetwork(network) {
  const known = {
    testnet: { chainId: 31611, asset: '0x118917a40FAF1CD7a13dB0Ef56C86De7973Ac503' },
    mainnet: { chainId: 31612, asset: '0xdD468A1DDc392dcdbEf6db6e34E89AA338F9F186' },
  };
  const expected = network && Object.hasOwn(known, network.name) ? known[network.name] : null;
  if (!expected || network.chainId !== expected.chainId || network.decimals !== 18 ||
      !address(network.asset) || network.asset.toLowerCase() !== expected.asset.toLowerCase()) {
    throw new Error('Unsupported or mismatched Mezo network configuration.');
  }
}

export function financeLinks(name) {
  if (name !== 'testnet' && name !== 'mainnet') throw new Error('Unsupported Mezo environment.');
  return Object.freeze({
    borrow: name === 'testnet' ? 'https://testnet.mezo.org/feature/borrow' : 'https://mezo.org/feature/borrow',
    borrowDocs: BORROW_DOCS,
  });
}

export function fundingEligibility(context, now = Date.now()) {
  const blocked = reason => ({ allowed: false, reason, requiredAtomic: 0n });
  try {
    validateNetwork(context.network);
    if (context.busy) return blocked('Wait for the current checkout action.');
    if (context.paymentGuard !== 'clear') return blocked('Check the existing payment outcome before funding or retrying.');
    if (!address(context.account)) return blocked('Connect the expected payer wallet.');
    if (!context.onMezo) return blocked('Select the configured Mezo network, then check the balance again.');
    const quote = context.quote;
    if (!quote || quote.state !== 'READY') return blocked('Prepare a fresh, unpaid report quote first.');
    const terms = quote.terms;
    if (!address(terms.expected_payer) || terms.expected_payer.toLowerCase() !== context.account.toLowerCase()) {
      return blocked('The connected account is not the quoted payer.');
    }
    if (terms.chain_id !== context.network.chainId || terms.network !== `eip155:${context.network.chainId}` ||
        !address(terms.asset) || terms.asset.toLowerCase() !== context.network.asset.toLowerCase() || terms.decimals !== 18) {
      return blocked('Quote network or MUSD asset does not match this application.');
    }
    const expires = Date.parse(terms.expires_at);
    if (!Number.isFinite(now) || !Number.isFinite(expires) || now >= expires) return blocked('This quote has expired. Request a new quote; do not retry an unknown payment.');
    return { allowed: true, reason: '', requiredAtomic: atomic(terms.amount_atomic, true) };
  } catch {
    return blocked('Funding is unavailable because the quote or network configuration is invalid.');
  }
}

export function formatMusd(value) {
  if (typeof value !== 'bigint' || value < 0n || value > MAX_UINT256) throw new Error('Invalid atomic MUSD amount.');
  const fraction = (value % UNIT).toString().padStart(18, '0').replace(/0+$/, '');
  return `${value / UNIT}${fraction ? `.${fraction}` : ''}`;
}

async function boundedRequest(provider, request, timeoutMs) {
  let timer;
  try {
    return await Promise.race([
      Promise.resolve().then(() => provider.request(request)),
      new Promise((_, reject) => { timer = setTimeout(() => reject(new Error('Wallet read timed out.')), timeoutMs); }),
    ]);
  } finally {
    clearTimeout(timer);
  }
}

export async function readMusdBalance(provider, network, account, timeoutMs = 10000) {
  validateNetwork(network);
  if (!address(account)) throw new Error('Invalid wallet account.');
  if (!Number.isSafeInteger(timeoutMs) || timeoutMs < 1 || timeoutMs > 60000) throw new Error('Invalid wallet-read timeout.');
  const request = args => boundedRequest(provider, args, timeoutMs);
  const checkIdentity = async () => {
    const chain = await request({ method: 'eth_chainId' });
    if (typeof chain !== 'string' || !/^0x[0-9a-f]{1,16}$/i.test(chain) || BigInt(chain) !== BigInt(network.chainId)) {
      throw new Error('Select the configured Mezo network, then check the balance again.');
    }
    const accounts = await request({ method: 'eth_accounts' });
    if (!Array.isArray(accounts) || typeof accounts[0] !== 'string' || accounts[0].toLowerCase() !== account.toLowerCase()) {
      throw new Error('The selected wallet account changed. Check the balance again.');
    }
  };
  await checkIdentity();
  const result = await request({ method: 'eth_call', params: [{
    to: network.asset,
    data: '0x70a08231' + account.slice(2).toLowerCase().padStart(64, '0'),
  }, 'latest'] });
  if (typeof result !== 'string' || !/^0x[0-9a-f]{64}$/i.test(result)) throw new Error('The wallet returned an invalid MUSD balance.');
  await checkIdentity();
  return BigInt(result);
}

/** A wallet-reported, block-bound observation, never a settlement receipt. */
export async function readFundingObservation(provider, network, account, requiredAtomic, timeoutMs = 10000) {
  validateNetwork(network);
  const required = atomic(requiredAtomic, true);
  if (!address(account)) throw new Error('Invalid wallet account.');
  if (!Number.isSafeInteger(timeoutMs) || timeoutMs < 1 || timeoutMs > 60000) throw new Error('Invalid wallet-read timeout.');
  const deadline = Date.now() + timeoutMs;
  const request = args => {
    const remaining = deadline - Date.now();
    if (remaining <= 0) throw new Error('Wallet read timed out.');
    return boundedRequest(provider, args, remaining);
  };
  const checkIdentity = async () => {
    const chain = await request({ method: 'eth_chainId' });
    if (typeof chain !== 'string' || !/^0x[0-9a-f]{1,16}$/i.test(chain) || BigInt(chain) !== BigInt(network.chainId)) {
      throw new Error('Select the configured Mezo network, then check the balance again.');
    }
    const accounts = await request({ method: 'eth_accounts' });
    if (!Array.isArray(accounts) || typeof accounts[0] !== 'string' || accounts[0].toLowerCase() !== account.toLowerCase()) {
      throw new Error('The selected wallet account changed. Check the balance again.');
    }
  };
  const validBlock = value => value && typeof value.number === 'string' && /^0x(?:0|[1-9a-f][0-9a-f]{0,63})$/i.test(value.number) &&
    typeof value.hash === 'string' && /^0x[0-9a-f]{64}$/i.test(value.hash) && !/^0x0{64}$/i.test(value.hash);
  await checkIdentity();
  const block = await request({ method: 'eth_getBlockByNumber', params: ['latest', false] });
  if (!validBlock(block)) throw new Error('The wallet returned invalid block metadata.');
  const balance = await readMusdBalance({ request: args => request(args.method === 'eth_call'
    ? { ...args, params: [args.params[0], block.number] } : args) }, network, account, timeoutMs);
  // A number-tagged eth_call is accepted only if its canonical block stayed the same.
  const canonical = await request({ method: 'eth_getBlockByNumber', params: [block.number, false] });
  if (!validBlock(canonical) || canonical.number.toLowerCase() !== block.number.toLowerCase() || canonical.hash.toLowerCase() !== block.hash.toLowerCase()) {
    throw new Error('The observed block changed. Check the balance again.');
  }
  await checkIdentity();
  return Object.freeze({
    schema: 'liqvera-musd-funding-observation/v1',
    network: `eip155:${network.chainId}`, chain_id: network.chainId, asset: network.asset, decimals: network.decimals,
    account, block_number: BigInt(block.number).toString(), block_hash: block.hash,
    balance_atomic: balance.toString(), required_atomic: required.toString(),
    shortfall_atomic: (required > balance ? required - balance : 0n).toString(), report_budget: (balance / required).toString(),
    observed_at: new Date().toISOString(), payment_submitted: false,
  });
}
