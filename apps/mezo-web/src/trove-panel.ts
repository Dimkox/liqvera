import {MEZO_TESTNET,MEZO_TESTNET_TROVES} from '@liqvera/mezo-protocol';
import type {TroveReport} from './contracts.ts';

/** Render retained values as text; explorer destinations come from protocol constants. */
export function mountTroveRisk(host:HTMLElement,report:TroveReport):void {
 const risk=report.trove_risk;
 const section=document.createElement('section');section.className='trove-risk limitations';
 const paragraph=(text:string)=>{const p=document.createElement('p');p.textContent=text;section.append(p);};
 const heading=document.createElement('h3');heading.textContent='Mezo Trove risk';section.append(heading);
 paragraph('Mezo Testnet · Snapshot risk information, not financial advice. An active paid report can prepare BTC deposits and MUSD repayments for your wallet to sign.');
 paragraph(`Borrower: ${risk.borrower} · Status: ${risk.status}`);
 const grid=document.createElement('div');grid.className='data-grid report-grid';
 for(const [label,value] of [
  ['Debt (MUSD)',risk.debt_musd],['Collateral (BTC)',risk.collateral_btc],['Price (MUSD/BTC)',risk.price_musd],
  ['ICR (ratio)',risk.icr],['MCR (ratio)',risk.mcr],['TCR (ratio)',risk.tcr],
  ['MCR crossing price (MUSD/BTC)',risk.liquidation_price_musd],['Price buffer (%)',risk.buffer_pct],
  ['Redemption position',risk.redemption_position===null?null:String(risk.redemption_position)],
  ['Sorted Troves',String(risk.sorted_troves_size)],['Debt ahead (MUSD)',risk.debt_ahead_musd],
 ] as const) {
  const field=document.createElement('div');field.className='data-field';
  const title=document.createElement('span');title.className='field-name';title.textContent=label;
  const data=document.createElement('strong');data.textContent=value??'Unavailable';field.append(title,data);grid.append(field);
 }
 section.append(grid);paragraph(`Queue: ${risk.queue_status}`);
 for(const scenario of risk.scenarios)paragraph(`Price ${scenario.price_change_pct}%: ${scenario.price_musd} MUSD/BTC · ICR ${scenario.icr??'unavailable'} · ${scenario.status}`);
 paragraph(`Captured block ${risk.block_number} · ${risk.block_hash}`);
 const links=document.createElement('p');
 for(const [label,path] of [['TroveManager',`address/${MEZO_TESTNET_TROVES.troveManager}`],
  ['SortedTroves',`address/${MEZO_TESTNET_TROVES.sortedTroves}`],['PriceFeed',`address/${MEZO_TESTNET_TROVES.priceFeed}`],
  ...(/^[1-9][0-9]*$/.test(risk.block_number)?[['Block',`block/${risk.block_number}`]]:[])]) {
  const a=document.createElement('a');a.textContent=`${label} ↗ `;a.href=`${MEZO_TESTNET.explorerUrl}/${path}`;
  a.target='_blank';a.rel='noopener noreferrer';links.append(a);
 }
 section.append(links);
 for(const caveat of risk.caveats)paragraph(caveat);
 host.append(section);
}
