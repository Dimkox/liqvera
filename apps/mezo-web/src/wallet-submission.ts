import type {Eip1193Provider} from './wallet.ts';

export class WalletSubmissionUnknown extends Error {
  constructor(cause:unknown){super('Wallet submission outcome is unknown. Check your wallet and explorer before retrying.',{cause});this.name='WalletSubmissionUnknown';}
}
function explicitUserRejection(error:unknown):boolean{
  if(!error||typeof error!=='object')return false;const value=error as {code?:number|string;message?:string};
  return value.code===4001||value.code==='ACTION_REJECTED'||/user rejected|user denied/i.test(value.message??'');
}
export async function sendWalletTransaction(provider:Eip1193Provider,transaction:Record<string,string>):Promise<string>{
  try{const hash=String(await provider.request({method:'eth_sendTransaction',params:[transaction]}));if(!/^0x[0-9a-fA-F]{64}$/.test(hash))throw new Error('Wallet returned an invalid transaction hash.');return hash;}
  catch(error){if(explicitUserRejection(error))throw error;throw new WalletSubmissionUnknown(error);}
}
