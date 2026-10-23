import assert from 'node:assert/strict';
import test from 'node:test';
import {Interface} from 'ethers';
import * as p from '@liqvera/mezo-protocol';
import {prepareNextSalePart,submitSaleAction} from '../src/mezo-trade-execution.ts';
const router=new Interface(p.MEZO_TESTNET_ROUTER_ABI),pool=new Interface(p.MEZO_TESTNET_POOL_ABI),factory=new Interface(p.MEZO_TESTNET_POOL_FACTORY_ABI),token=new Interface(p.MEZO_TESTNET_ERC20_TRADE_ABI);
const owner='0x1111111111111111111111111111111111111111';let allowance=0n;let sent=[];
const amount=10n**18n,reserveBtc=1000n*10n**18n,reserveMusd=500000n*10n**18n,fee=4n;
function quote(a){const net=a-a*fee/10000n;return reserveMusd*net/(reserveBtc+net);}
const provider={request:async({method,params=[]})=>{
 if(method==='eth_chainId')return '0x7b7b';if(method==='eth_blockNumber')return '0x1234';if(method==='eth_accounts')return [owner];if(method==='eth_sendTransaction'){sent.push(params[0]);return `0x${'ab'.repeat(32)}`;}
 if(method!=='eth_call')throw Error(method);const tx=params[0],to=tx.to.toLowerCase();const data=tx.data;
 if(to===p.MEZO_TESTNET_DEX.musdBtcPool.toLowerCase()){const x=pool.parseTransaction({data});if(x.name==='token0')return pool.encodeFunctionResult('token0',[p.MUSD_TESTNET.address]);if(x.name==='token1')return pool.encodeFunctionResult('token1',[p.MEZO_TESTNET_DEX.btcToken]);if(x.name==='getAmountOut')return pool.encodeFunctionResult('getAmountOut',[quote(BigInt(x.args[0]))]);}
 if(to===p.MEZO_TESTNET_DEX.poolFactory.toLowerCase())return factory.encodeFunctionResult('getFee',[fee]);
 if(to===p.MEZO_TESTNET_DEX.router.toLowerCase()){const x=router.parseTransaction({data});if(x.name==='getReserves')return router.encodeFunctionResult('getReserves',[reserveBtc,reserveMusd]);if(x.name==='getAmountsOut')return router.encodeFunctionResult('getAmountsOut',[[x.args[0],quote(BigInt(x.args[0]))]]);if(x.name==='swapExactTokensForTokens')return router.encodeFunctionResult('swapExactTokensForTokens',[[x.args[0],quote(BigInt(x.args[0]))]]);}
 if(to===p.MEZO_TESTNET_DEX.btcToken.toLowerCase()){const x=token.parseTransaction({data});if(x.name==='allowance')return token.encodeFunctionResult('allowance',[allowance]);if(x.name==='balanceOf')return token.encodeFunctionResult('balanceOf',[100n*amount]);if(x.name==='approve')return token.encodeFunctionResult('approve',[true]);}
 throw Error(`Unexpected call ${tx.to} ${data}`);
}};
test('sale requires exact token approval and subsequent explicit swap preparation',async()=>{
 allowance=0n;sent=[];const approval=await prepareNextSalePart(provider,owner,amount,100);assert.equal(approval.kind,'approve');assert.equal(token.parseTransaction({data:approval.data}).args[1],amount);assert.equal(sent.length,0);
 allowance=amount;const swap=await prepareNextSalePart(provider,owner,amount,100);assert.equal(swap.kind,'swap');const args=router.parseTransaction({data:swap.data}).args;assert.equal(args[0],amount);assert.equal(args[1],swap.minOut);assert.equal(args[2][0].from,p.MEZO_TESTNET_DEX.btcToken);assert.equal(args[2][0].to,p.MUSD_TESTNET.address);assert.equal(swap.minOut,swap.quoted*9900n/10000n);assert.equal(swap.feeBps,4n);assert.equal(swap.feeBtc,amount*4n/10000n);
 await submitSaleAction(provider,swap);assert.equal(sent.length,1);assert.equal(sent[0].to,p.MEZO_TESTNET_DEX.router);
});
test('sale submission stops on changed chain or account before wallet request',async()=>{
 sent=[];await assert.rejects(()=>submitSaleAction({request:async({method})=>method==='eth_chainId'?'0x1':[]},{account:owner,kind:'swap',amount,quoted:1n,minOut:1n,feeBps:4n,feeBtc:1n,data:'0x',to:p.MEZO_TESTNET_DEX.router,value:'0x0',impactBps:1}),/network changed/i);assert.equal(sent.length,0);
});
import {createHash} from 'node:crypto';
import {readFile} from 'node:fs/promises';
const lock=JSON.parse(await readFile(new URL('../../../packages/mezo-protocol/source-lock.json',import.meta.url),'utf8'));
test('BTC token approval ABI is source-locked to the documented Mezo Testnet token',async()=>{
 const record=lock.sources.testnet_explorer.contracts.find(x=>x.name==='BTC');assert.ok(record);assert.equal(record.address,p.MEZO_TESTNET_DEX.btcToken);assert.equal(record.chain_id,31611);
 for(const [path,hash] of [[record.local_path,record.sha256],[record.source_response.local_path,record.source_response.sha256]]){const bytes=await readFile(new URL(`../../../packages/mezo-protocol/${path}`,import.meta.url));assert.equal(createHash('sha256').update(bytes).digest('hex'),hash);}
 const abi=JSON.parse(await readFile(new URL(`../../../packages/mezo-protocol/${record.local_path}`,import.meta.url),'utf8'));const tokenArtifact=new Interface(abi);for(const signature of ['approve(address,uint256)','allowance(address,address)','balanceOf(address)'])assert.ok(tokenArtifact.getFunction(signature));
});

test('sale send transport errors stay confirm-only and stale app context cannot prompt',async()=>{
 const action={account:owner,kind:'swap',amount,quoted:1n,minOut:1n,feeBps:4n,feeBtc:1n,data:'0x',to:p.MEZO_TESTNET_DEX.router,value:'0x0',impactBps:1};
 await assert.rejects(()=>submitSaleAction({...provider,request:async({method,params})=>method==='eth_sendTransaction'?Promise.reject(new Error('socket timeout')):provider.request({method,params})},action),/outcome is unknown/i);
 await assert.rejects(()=>submitSaleAction(provider,action,()=>false),/selected wallet changed/i);
 const rejected=Object.assign(new Error('User rejected the request'),{code:4001});await assert.rejects(()=>submitSaleAction({...provider,request:async({method,params})=>method==='eth_sendTransaction'?Promise.reject(rejected):provider.request({method,params})},action),error=>error===rejected);
});
