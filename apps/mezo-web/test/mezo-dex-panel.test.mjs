import test from 'node:test';
import assert from 'node:assert/strict';
import {mountMezoDex} from '../src/mezo-dex-panel.ts';
class Element {
  children=[]; textContent=''; attrs={};
  constructor(tag){this.tagName=tag;}
  append(...items){this.children.push(...items);}
  setAttribute(name,value){this.attrs[name]=value;}
  addEventListener(){}
}
function text(element){return [element.textContent,...element.children.map(text)].join(' ');}
function setup(){globalThis.document={createElement:tag=>new Element(tag)};return new Element('section');}
test('old reports show an explicit missing Mezo evidence message',()=>{
  const host=setup();mountMezoDex(host,{});
  assert.match(text(host),/does not contain Mezo DEX evidence/);
});
test('comparison renders captured block, exact prices and caveats without network',()=>{
  const host=setup();
  mountMezoDex(host,{mezo_dex:{side:'SELL',quantity_btc:'1',mid_price_musd:'79000',avg_price_musd:'78597.12278611556119311',
    price_impact_bps:'10',fee_bps:4,block_number:'16319875',block_hash:'0x'+'a'.repeat(64),match:true,
    depth_ladder:[],caveats:['Testnet; excludes gas.']},venue_comparison:{hyperliquid_avg_price:'80000',mezo_avg_price:'78597.12278611556119311',spread_bps:'-175',better_venue:'hyperliquid',caveats:['Perpetual versus spot.']}});
  assert.match(text(host),/Mezo DEX vs Hyperliquid/);
  assert.match(text(host),/16319875/);
  assert.match(text(host),/78597\.12278611556119311/);
  assert.match(text(host),/Perpetual versus spot/);
});

test('BTC sale planner is available without a delivered report and still requires wallet context to quote',async()=>{
 const {mountMezoSalePlanner}=await import('../src/mezo-sale-panel.ts');
 const host=setup();mountMezoSalePlanner(host,()=>({provider:null,account:null,isCurrent:()=>true}));
 assert.match(text(host),/Plan BTC sale on Mezo/);
 assert.match(text(host),/Testnet reserves/);
});
