import { MEZO_TESTNET, MEZO_TESTNET_DEX } from '@liqvera/mezo-protocol';
import type { Report } from './contracts';

/** Only text nodes and pinned explorer destinations; rendering never reads a wallet or RPC. */
export function mountMezoDex(host: HTMLElement, report: Pick<Report,'mezo_dex'|'venue_comparison'>): void {
  const section = document.createElement('section');
  section.className = 'mezo-dex-comparison limitations';
  const heading = document.createElement('h3'); heading.textContent = 'Mezo DEX vs Hyperliquid';
  section.append(heading);
  const paragraph = (value:string) => {const p=document.createElement('p');p.textContent=value;section.append(p);};
  const dex=report.mezo_dex;
  if(!dex){paragraph('This report does not contain Mezo DEX evidence. Its original evidence remains available.');host.append(section);return;}
  paragraph(`${dex.side} ${dex.quantity_btc} BTC · Mezo Testnet spot MUSD/BTC`);
  paragraph(`Mezo average: ${dex.avg_price_musd} MUSD/BTC · Mid price: ${dex.mid_price_musd} · Impact: ${dex.price_impact_bps} bps · Pool fee: ${dex.fee_bps} bps`);
  paragraph(`Captured block ${dex.block_number} · ${dex.block_hash} · Router/formula: ${dex.match?'match':'mismatch'}`);
  const links=document.createElement('p');
  const block=/^[1-9][0-9]*$/.test(dex.block_number)?dex.block_number:null;
  for(const [label,path] of [['Pool',`address/${MEZO_TESTNET_DEX.musdBtcPool}`],['Router',`address/${MEZO_TESTNET_DEX.router}`],...(block?[['Block',`block/${block}`]]:[])]){
    const a=document.createElement('a');a.textContent=`${label} ↗ `;a.href=`${MEZO_TESTNET.explorerUrl}/${path}`;
    a.target='_blank';a.rel='noopener noreferrer';links.append(a);
  }
  section.append(links);
  const comparison=report.venue_comparison;
  if(comparison)paragraph(`Hyperliquid average: ${comparison.hyperliquid_avg_price} USD/BTC · Spread: ${comparison.spread_bps} bps · Better hypothetical quote: ${comparison.better_venue}`);
  for(const point of dex.depth_ladder)paragraph(`${point.quantity_btc} BTC: ${point.status??`${point.price_impact_bps} bps impact`}`);
  for(const caveat of [...dex.caveats,...(comparison?.caveats??[])])paragraph(caveat);
  host.append(section);
}
