import { createHash } from 'node:crypto';
import { AMOUNT, ASSET, CHAIN_ID, NETWORK, PublicError, type Attempt, type Quote, type Receipt } from '../domain/model.js';
import type { AuthorizationPolicy, FinalityPolicy, ReadonlyRpc } from '../ports/index.js';
import { boundedJson } from './http.js';
import { MEZO_TESTNET, MUSD_ABI, MUSD_TRANSFER_EVENT, MUSD_PERMIT, assertMezoTestnetChainId } from '@liqvera/mezo-protocol';
const RPC_URL=MEZO_TESTNET.rpcUrl;
const TRANSFER=MUSD_TRANSFER_EVENT.topic0;
// Export the provenance-backed ABI and permit metadata for reviewed policy
// bindings; the gateway never invents its own EIP-712 signing domain.
export const musdProtocol={abi:MUSD_ABI,permit:MUSD_PERMIT};
const HASH=/^0x[0-9a-f]{64}$/;
const HEX=/^0x(?:0|[1-9a-f][0-9a-f]*)$/;
const UINT=/^(?:0|[1-9][0-9]*)$/;
function object(value: unknown): Record<string,unknown> {
  if (!value || typeof value!=='object' || Array.isArray(value)) throw new PublicError('PAYMENT_UNCERTAIN',202);
  return value as Record<string,unknown>;
}
function safeInteger(value: unknown): number {
  if (typeof value!=='string'||!HEX.test(value)) throw new PublicError('PAYMENT_UNCERTAIN',202);
  const exact=BigInt(value); if (exact>BigInt(Number.MAX_SAFE_INTEGER)) throw new PublicError('PAYMENT_UNCERTAIN',202);
  return Number(exact);
}
export class MezoReadonlyRpc implements ReadonlyRpc {
  constructor(private readonly rpcUrl:URL=new URL(RPC_URL)) {
    if(rpcUrl.protocol!=='https:'||rpcUrl.username||rpcUrl.password||rpcUrl.search||rpcUrl.hash)throw new Error('RPC_URL_INVALID');
  }
  async call(method: Parameters<ReadonlyRpc['call']>[0], params: unknown[]): Promise<unknown> {
    const result=object(await boundedJson(this.rpcUrl,{method:'POST',body:JSON.stringify({jsonrpc:'2.0',id:1,method,params})},2097152));
    if (result.id!==1 || result.jsonrpc!=='2.0' || result.error || !('result' in result)) throw new PublicError('PAYMENT_UNCERTAIN',202);
    return result.result;
  }
}
export class MezoReceiptReader {
  constructor(private readonly rpc: ReadonlyRpc,private readonly identity: AuthorizationPolicy,private readonly finality: FinalityPolicy) {}
  async nativeBalanceSnapshot(buyer:string):Promise<{balance:string;block_number:string;block_hash:string}> {
    const block=object(await this.rpc.call('eth_getBlockByNumber',['latest',false]));
    if(typeof block.number!=='string'||!HEX.test(block.number)||typeof block.hash!=='string'||!HASH.test(block.hash))
      throw new PublicError('PAYMENT_UNCERTAIN',202);
    const value=await this.rpc.call('eth_getBalance',[buyer,block.number]);
    if(typeof value!=='string'||!HEX.test(value))throw new PublicError('PAYMENT_UNCERTAIN',202);
    return {balance:BigInt(value).toString(),block_number:BigInt(block.number).toString(),block_hash:block.hash};
  }
  async confirmation(quote: Quote,attempt: Attempt): Promise<Receipt|null> {
    if (!this.identity.reviewed || !this.finality.reviewed || !attempt.tx_hash || !HASH.test(attempt.tx_hash)) return null;
    try { assertMezoTestnetChainId(safeInteger(await this.rpc.call('eth_chainId',[]))); }
    catch { throw new PublicError('MANUAL_REVIEW',202); }
    const raw=await this.rpc.call('eth_getTransactionReceipt',[attempt.tx_hash]); if(raw===null)return null;
    const receipt=object(raw);
    if (receipt.status!=='0x1' || receipt.transactionHash!==attempt.tx_hash || typeof receipt.blockHash!=='string' || !HASH.test(receipt.blockHash) || !Array.isArray(receipt.logs)) throw new PublicError('MANUAL_REVIEW',202);
    const block=object(await this.rpc.call('eth_getBlockByNumber',[receipt.blockNumber,false]));
    if (block.hash!==receipt.blockHash) throw new PublicError('MANUAL_REVIEW',202);
    if (!await this.finality.isFinal(receipt,block,this.rpc)) return null;
    const latest=object(await this.rpc.call('eth_getBlockByNumber',['latest',false]));
    if(typeof latest.number!=='string'||!HEX.test(latest.number))throw new PublicError('MANUAL_REVIEW',202);
    const confirmations=BigInt(latest.number)-BigInt(String(receipt.blockNumber))+1n;
    if(confirmations<12n||confirmations>BigInt(Number.MAX_SAFE_INTEGER))throw new PublicError('MANUAL_REVIEW',202);
    const transaction=object(await this.rpc.call('eth_getTransactionByHash',[attempt.tx_hash]));
    const before=attempt.correlation.buyer_native_balance_before;
    let after:string;
    try {
      const value=await this.rpc.call('eth_getBalance',[quote.terms.expected_payer,String(receipt.blockNumber)]);
      if(typeof value!=='string'||!HEX.test(value))throw new Error('invalid balance');
      after=BigInt(value).toString();
    }
    catch { throw new PublicError('MANUAL_REVIEW',202); }
    if(typeof transaction.from!=='string'||!/^0x[0-9a-fA-F]{40}$/.test(transaction.from)||transaction.from.toLowerCase()===quote.terms.expected_payer||
      typeof before!=='string'||!UINT.test(before)||after!==before)
      throw new PublicError('MANUAL_REVIEW',202);
    const matches: Record<string,unknown>[]=[];
    for (const value of receipt.logs) {
      const log=object(value); const topics=log.topics;
      if (typeof log.address!=='string'||log.address.toLowerCase()!==ASSET.toLowerCase()||!Array.isArray(topics)||topics.length!==3||topics[0]!==TRANSFER)continue;
      if (topics[1]!==`0x${'0'.repeat(24)}${quote.terms.expected_payer.slice(2)}` || topics[2]!==`0x${'0'.repeat(24)}${quote.terms.pay_to.slice(2)}` ||
        typeof log.data!=='string'||!/^0x[0-9a-f]{64}$/.test(log.data)||BigInt(log.data)!==BigInt(AMOUNT))continue;
      if(log.removed===true||log.transactionHash!==attempt.tx_hash||log.blockHash!==receipt.blockHash)throw new PublicError('MANUAL_REVIEW',202);
      // A Transfer match alone does not identify an x402 authorization.
      if(await this.identity.bindsTransfer(attempt,transaction,log))matches.push(log);
    }
    if(matches.length!==1) return null;
    const beforeNumber=attempt.correlation.buyer_native_balance_before_block_number;
    const beforeHash=attempt.correlation.buyer_native_balance_before_block_hash;
    if(typeof beforeNumber!=='string'||!UINT.test(beforeNumber)||typeof beforeHash!=='string'||!HASH.test(beforeHash)||BigInt(beforeNumber)>BigInt(String(receipt.blockNumber)))
      throw new PublicError('MANUAL_REVIEW',202);
    const transferIdentity=createHash('sha256').update(`${attempt.authorization_identity}\n${attempt.tx_hash}\n${matches[0]!.logIndex}`).digest('hex');
    return { schema:'mee-evidence-receipt/v1',quote_id:quote.id,report_id:quote.report_id,payment_attempt_id:attempt.id,
      report_sha256:quote.report_sha256,network:NETWORK,chain_id:CHAIN_ID,asset:ASSET,amount_atomic:AMOUNT,
      payer:quote.terms.expected_payer,pay_to:quote.terms.pay_to,tx_hash:attempt.tx_hash,block_hash:receipt.blockHash,
      block_number:safeInteger(receipt.blockNumber),log_index:safeInteger(matches[0]!.logIndex),
      confirmed_at:new Date().toISOString(),finality_policy_version:this.finality.version,
      transaction_from:transaction.from.toLowerCase(),buyer_native_balance_before:before,buyer_native_balance_after:after,
      buyer_native_gas_spent:'0',observation_before_block_number:Number(beforeNumber),observation_before_block_hash:beforeHash,
      observation_after_block_number:safeInteger(receipt.blockNumber),observation_after_block_hash:receipt.blockHash,
      confirmations:Number(confirmations),authorization_identity:attempt.authorization_identity,transfer_identity:transferIdentity };
  }
}
