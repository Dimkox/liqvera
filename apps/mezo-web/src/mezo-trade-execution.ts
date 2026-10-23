import {Interface,getAddress} from 'ethers';
import {MEZO_TESTNET,MEZO_TESTNET_DEX,MEZO_TESTNET_POOL_ABI,MEZO_TESTNET_POOL_FACTORY_ABI,MEZO_TESTNET_ROUTER_ABI,MEZO_TESTNET_ERC20_TRADE_ABI,MUSD_TESTNET} from '@liqvera/mezo-protocol';
import type {Eip1193Provider} from './wallet.ts';
import {minOutForQuote} from './mezo-trade-plan.ts';
const router=new Interface(MEZO_TESTNET_ROUTER_ABI),pool=new Interface(MEZO_TESTNET_POOL_ABI),factory=new Interface(MEZO_TESTNET_POOL_FACTORY_ABI),token=new Interface(MEZO_TESTNET_ERC20_TRADE_ABI);
const req=(p:Eip1193Provider,method:string,params:unknown[]=[])=>p.request({method,params});
const call=async(p:Eip1193Provider,to:string,data:string,from?:string,blockTag='latest')=>String(await req(p,'eth_call',[{to,data,...(from?{from}:{})},blockTag]));
export type SwapAction={kind:'approve'|'swap';account:string;amount:bigint;quoted:bigint;minOut:bigint;data:string;to:string;value:'0x0';impactBps:number};
export async function prepareNextSalePart(provider:Eip1193Provider,account:string,amount:bigint,slippageBps:number):Promise<SwapAction>{
 const owner=getAddress(account);if(BigInt(String(await req(provider,'eth_chainId')))!==BigInt(MEZO_TESTNET.chainId))throw new Error('Switch to Mezo Testnet before trading.');if(amount<=0n)throw new Error('Swap amount must be positive.');const blockTag=String(await req(provider,'eth_blockNumber'));
 const [btc,musd]=await Promise.all([
  call(provider,MEZO_TESTNET_DEX.musdBtcPool,pool.encodeFunctionData('token0'),undefined,blockTag),
  call(provider,MEZO_TESTNET_DEX.musdBtcPool,pool.encodeFunctionData('token1'),undefined,blockTag),
 ]);const tokens=[getAddress(pool.decodeFunctionResult('token0',btc)[0]),getAddress(pool.decodeFunctionResult('token1',musd)[0])];if(!tokens.includes(getAddress(MEZO_TESTNET_DEX.btcToken))||!tokens.includes(getAddress(MUSD_TESTNET.address)))throw new Error('Pool token identities changed.');
 const [reserves,feeRaw,routeQuote,poolQuote,allowanceRaw,balanceRaw]=await Promise.all([
  call(provider,MEZO_TESTNET_DEX.router,router.encodeFunctionData('getReserves',[MEZO_TESTNET_DEX.btcToken,MUSD_TESTNET.address,false,MEZO_TESTNET_DEX.poolFactory]),undefined,blockTag),
  call(provider,MEZO_TESTNET_DEX.poolFactory,factory.encodeFunctionData('getFee',[MEZO_TESTNET_DEX.musdBtcPool,false]),undefined,blockTag),
  call(provider,MEZO_TESTNET_DEX.router,router.encodeFunctionData('getAmountsOut',[amount,[{from:MEZO_TESTNET_DEX.btcToken,to:MUSD_TESTNET.address,stable:false,factory:MEZO_TESTNET_DEX.poolFactory}]]),undefined,blockTag),
  call(provider,MEZO_TESTNET_DEX.musdBtcPool,pool.encodeFunctionData('getAmountOut',[amount,MEZO_TESTNET_DEX.btcToken]),undefined,blockTag),
  call(provider,MEZO_TESTNET_DEX.btcToken,token.encodeFunctionData('allowance',[owner,MEZO_TESTNET_DEX.router]),undefined,blockTag),
  call(provider,MEZO_TESTNET_DEX.btcToken,token.encodeFunctionData('balanceOf',[owner]),undefined,blockTag),
 ]);
 const decodedRes=router.decodeFunctionResult('getReserves',reserves);const reserveBtc=BigInt(decodedRes[0]);const reserveMusd=BigInt(decodedRes[1]);
 const fee=BigInt(factory.decodeFunctionResult('getFee',feeRaw)[0]);if(fee>=10000n)throw new Error('Pool fee is invalid.');
 const routerAmounts=router.decodeFunctionResult('getAmountsOut',routeQuote)[0];const quoted=BigInt(routerAmounts[routerAmounts.length-1]);const direct=BigInt(pool.decodeFunctionResult('getAmountOut',poolQuote)[0]);if(!quoted||quoted!==direct)throw new Error('Router and pool quotes disagree.');
 if(BigInt(token.decodeFunctionResult('balanceOf',balanceRaw)[0])<amount)throw new Error('Wallet BTC balance is too low.');
 const minOut=minOutForQuote(quoted,slippageBps);const spotValue=amount*reserveMusd;const actualValue=quoted*reserveBtc;const impactBps=Number((spotValue-actualValue)*10000n/spotValue);
 if(BigInt(token.decodeFunctionResult('allowance',allowanceRaw)[0])<amount){const data=token.encodeFunctionData('approve',[MEZO_TESTNET_DEX.router,amount]);await req(provider,'eth_call',[{from:owner,to:MEZO_TESTNET_DEX.btcToken,data},'latest']);return {kind:'approve',account:owner,amount,quoted,minOut,data,to:MEZO_TESTNET_DEX.btcToken,value:'0x0',impactBps};}
 const deadline=Math.floor(Date.now()/1000)+300;const data=router.encodeFunctionData('swapExactTokensForTokens',[amount,minOut,[{from:MEZO_TESTNET_DEX.btcToken,to:MUSD_TESTNET.address,stable:false,factory:MEZO_TESTNET_DEX.poolFactory}],owner,deadline]);await req(provider,'eth_call',[{from:owner,to:MEZO_TESTNET_DEX.router,data},'latest']);return {kind:'swap',account:owner,amount,quoted,minOut,data,to:MEZO_TESTNET_DEX.router,value:'0x0',impactBps};
}
export async function submitSaleAction(provider:Eip1193Provider,action:SwapAction):Promise<string>{
 if(BigInt(String(await req(provider,'eth_chainId')))!==BigInt(MEZO_TESTNET.chainId))throw new Error('Wallet network changed. Refresh the sale quote.');const accounts=await req(provider,'eth_accounts') as string[];if(!accounts.some(value=>typeof value==='string'&&getAddress(value)===action.account))throw new Error('Wallet account changed. Refresh the sale quote.');
 return String(await req(provider,'eth_sendTransaction',[{from:action.account,to:action.to,data:action.data,value:action.value}]));
}

export async function waitForSaleReceipt(provider:Eip1193Provider,hash:string):Promise<void>{
 for(let i=0;i<60;i++){const receipt=await req(provider,'eth_getTransactionReceipt',[hash]) as {status?:string}|null;if(receipt){if(receipt.status==='0x0')throw new Error('Transaction reverted. Refresh the plan before continuing.');if(receipt.status!=='0x1')throw new Error('Transaction receipt has an unknown status. Check the explorer before continuing.');return;}await new Promise(resolve=>setTimeout(resolve,2000));}
 throw new Error('Transaction is still pending. Check your wallet explorer before continuing.');
}
