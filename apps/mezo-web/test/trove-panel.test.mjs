import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import test from 'node:test';
import {mountTroveRisk} from '../src/trove-panel.ts';
class Element{children=[];textContent='';constructor(tag){this.tagName=tag;}append(...values){this.children.push(...values);}}
function text(element){return [element.textContent,...element.children.map(text)].join(' ');}
const report=JSON.parse(await readFile(new URL('../../../evidence/mezo-testnet/2026-10-23-trove-risk-preview/report.json',import.meta.url),'utf8'));
test('Trove panel renders exact captured risk and pinned explorer links without RPC',()=>{
 globalThis.document={createElement:tag=>new Element(tag)};const host=new Element('div');mountTroveRisk(host,report);
 assert.match(text(host),/Mezo Trove risk/);assert.match(text(host),/16323457/);assert.ok(text(host).includes(report.trove_risk.debt_musd));
 assert.match(text(host),/not financial advice/i);
 const elements=e=>[e,...e.children.flatMap(elements)];
 const links=elements(host).filter(e=>e.tagName==='a');assert.equal(links.length,4);
 assert.ok(links.every(e=>e.href.startsWith('https://explorer.test.mezo.org/')));
});
test('inactive Trove is explicit with unavailable ratio rather than a healthy claim',()=>{
 globalThis.document={createElement:tag=>new Element(tag)};const host=new Element('div');const inactive=structuredClone(report);
 Object.assign(inactive.trove_risk,{status:'NOT_ACTIVE',icr:null,buffer_pct:null,liquidation_price_musd:null,redemption_position:null});
 mountTroveRisk(host,inactive);assert.match(text(host),/NOT_ACTIVE/);assert.match(text(host),/unavailable/i);
});
