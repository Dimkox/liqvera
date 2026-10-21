import assert from 'node:assert/strict';
import test from 'node:test';
import { mountMezoFinance } from '../src/mezo-finance-panel.ts';

test('the existing checkout has a mountable finance panel', () => {
  assert.equal(typeof mountMezoFinance, 'function');
});

class Element {
  children = []; attrs = {}; listeners = {}; textContent = ''; checked = false;
  disabled = false; value = ''; hidden = false; parent = null;
  constructor(tag) { this.tagName = tag; }
  append(...children) { for (const child of children) { this.children.push(child); if (typeof child === 'object') child.parent = this; } }
  after(child) { this.parent.append(child); }
  setAttribute(key, value) { this.attrs[key] = value; }
  hasAttribute(key) { return key === 'href' ? typeof this.href === 'string' : Object.hasOwn(this.attrs,key); }
  removeAttribute(key) { delete this.attrs[key]; if (key === 'href') delete this.href; }
  addEventListener(name, fn) { (this.listeners[name] ??= []).push(fn); }
  remove() { this.parent.children = this.parent.children.filter(x => x !== this); }
  async emit(name) { const event = { prevented: false, preventDefault() { this.prevented = true; } }; for (const fn of this.listeners[name] ?? []) await fn(event); return event; }
  find(id) { return this.id === id ? this : this.children.filter(x => typeof x === 'object').map(x => x.find(id)).find(Boolean); }
}
const account = '0x1111111111111111111111111111111111111111';
const other = '0x2222222222222222222222222222222222222222';
const network = {name:'testnet',chainId:31611,asset:'0x118917a40FAF1CD7a13dB0Ef56C86De7973Ac503',decimals:18};
function setup(read) {
  const root = new Element('div'), host = new Element('div'); root.append(host);
  const calls = [];
  const provider = { async request({method}) { calls.push(method); if (method === 'eth_chainId') return '0x7b7b'; if (method === 'eth_accounts') return [account]; if (method === 'eth_getBlockByNumber') return {number:'0x123',hash:'0x'+'a'.repeat(64)}; return read ? read() : '0x' + '0'.repeat(64); } };
  const context = { provider, account, paymentGuard:'clear', busy:false, onMezo:true,
    quote:{quote_id:'q1',state:'READY',terms:{network:'eip155:31611',chain_id:31611,asset:network.asset,decimals:18,amount_atomic:'10000000000000000',expected_payer:account,pay_to:other,expires_at:new Date(Date.now()+60000).toISOString()}} };
  globalThis.document = {createElement: tag => new Element(tag)};
  const panel = mountMezoFinance({host,network,getContext:()=>context});
  return { root, context, calls, panel, find:id=>root.find(id) };
}

if (mountMezoFinance) {
  test('mounting and updating never request accounts, sign or pay', () => {
    const s=setup(); try { s.panel.update(); assert.deepEqual(s.calls, []); } finally {s.panel.dispose();}
  });
  test('borrow is gated by a fresh read and separate acknowledgement', async () => {
    const s=setup(); try {
      assert.equal(s.find('mezo-borrow-link').href, undefined);
      await s.find('mezo-balance-check').emit('click');
      assert.match(s.find('mezo-balance-status').textContent,/Shortfall: 0\.01/);
      assert.equal(s.find('mezo-borrow-link').href, undefined);
      s.find('mezo-borrow-ack').checked=true; await s.find('mezo-borrow-ack').emit('change');
      assert.equal(s.find('mezo-borrow-link').href,'https://testnet.mezo.org/feature/borrow');
      assert.equal((await s.find('mezo-borrow-link').emit('click')).prevented,false);
      assert.deepEqual([...new Set(s.calls)].sort(),['eth_accounts','eth_call','eth_chainId','eth_getBlockByNumber'].sort());
    } finally{s.panel.dispose();}
  });
  test('expired or uncertain checkout disables a previously ready link', async () => {
    for (const change of [s=>{s.context.onMezo=false;},s=>s.context.quote.terms.expires_at='2000-01-01T00:00:00Z',s=>s.context.paymentGuard='unknown']) {
      const s=setup(); try {await s.find('mezo-balance-check').emit('click');s.find('mezo-borrow-ack').checked=true;change(s);s.panel.update();assert.equal(s.find('mezo-borrow-link').href,undefined);}finally{s.panel.dispose();}
    }
  });
  test('a replaced provider cannot publish a stale balance or error', async () => {
    for (const reject of [false,true]) {
      let settle; const pending=new Promise((resolve,no)=>{settle=reject?no:resolve;});
      const s=setup(()=>pending);
      try {const reading=s.find('mezo-balance-check').emit('click'); await new Promise(r=>setImmediate(r));
        s.context.provider={request:async()=>[]};s.panel.update();
        settle(reject?new Error('stale provider'):'0x'+'0'.repeat(64));await reading;
        assert.equal(s.find('mezo-borrow-link').href,undefined);
        assert.doesNotMatch(s.find('mezo-balance-status').textContent,/Shortfall:|stale provider/);
      }finally{s.panel.dispose();}
    }
  });
  test('having enough MUSD does not encourage a new loan', async () => {
    const s=setup(()=> '0x'+(10n**18n).toString(16).padStart(64,'0'));
    try{await s.find('mezo-balance-check').emit('click');s.find('mezo-borrow-ack').checked=true;s.panel.update();assert.equal(s.find('mezo-borrow-link').href,undefined);assert.match(s.find('mezo-balance-status').textContent,/sufficient/);}finally{s.panel.dispose();}
  });
}

test('funding panel shows exact budget and a downloadable block-bound observation', async () => {
  const s=setup(()=> '0x'+(10n**18n+1n).toString(16).padStart(64,'0'));
  try {
    await s.find('mezo-balance-check').emit('click');
    assert.match(s.find('mezo-balance-status').textContent, /100 report purchases/);
    assert.match(s.find('mezo-balance-block').textContent, /Block 291/);
    const download = s.find('mezo-observation-download');
    assert.match(download.href, /^blob:/);
    const result = await (await fetch(download.href)).json();
    assert.equal(result.balance_atomic, '1000000000000000001');
    assert.equal(result.report_budget, '100');
    assert.equal(result.quote_id, 'q1');
    assert.equal(result.payment_submitted, false);
    const oldUrl = download.href;
    s.context.paymentGuard='uncertain'; s.panel.update();
    assert.equal(download.href, undefined);
    await assert.rejects(fetch(oldUrl));
  } finally {s.panel.dispose();}
});

test('failed funding reads never expose an observation download or borrow action', async () => {
  const s=setup(()=> {throw new Error('RPC failed');});
  try {
    await s.find('mezo-balance-check').emit('click');
    assert.match(s.find('mezo-balance-status').textContent, /could not be verified/);
    assert.equal(s.find('mezo-observation-download').href, undefined);
    assert.equal(s.find('mezo-borrow-link').href, undefined);
  } finally {s.panel.dispose();}
});
