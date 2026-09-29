import assert from "node:assert/strict";
import test from "node:test";

import { createProductionProtocol, requirePermit2Challenge, requireSponsoredPayment } from "../src/x402-production.mjs";

const payer="0x1111111111111111111111111111111111111111";
const boundary={assetTransferMethod:"permit2",domainName:"Mezo USD",domainVersion:"1",requiredExtension:"eip2612GasSponsoring"};
const required={x402Version:2,resource:{url:"https://liqvera.invalid/v1/reports/report",description:"report",mimeType:"application/json"},accepts:[{
  scheme:"exact",network:"eip155:31611",asset:"0x118917a40FAF1CD7a13dB0Ef56C86De7973Ac503",amount:"10000000000000000",
  payTo:"0x2222222222222222222222222222222222222222",maxTimeoutSeconds:120,
  extra:{assetTransferMethod:"permit2",name:"Mezo USD",version:"1"},
}],extensions:{eip2612GasSponsoring:{info:{description:"The facilitator accepts EIP-2612 gasless Permit to `Permit2` canonical contract.",version:"1"},schema:{type:"object"}}}};

test("production official SDK round-trip creates Permit2 plus merged EIP-2612 payload",async()=>{
  const signed=[];
  const signer={address:payer,readContract:async({functionName})=>functionName==="allowance"?0n:7n,
    signTypedData:async message=>{signed.push(message);return `0x${(signed.length===1?"A":"B").repeat(130)}`;}};
  requirePermit2Challenge(required,boundary);
  const payment=await createProductionProtocol(signer,"https://rpc.test.mezo.org").createPaymentPayload(required);
  requireSponsoredPayment(payment,boundary);
  assert.equal(payment.payload.permit2Authorization.spender.toLowerCase(),"0x402085c248eea27d92e8b30b2c58ed07f9e20001");
  assert.equal(payment.extensions.eip2612GasSponsoring.info.description,required.extensions.eip2612GasSponsoring.info.description);
  assert.equal(payment.extensions.eip2612GasSponsoring.info.spender.toLowerCase(),"0x000000000022d473030f116ddee9f6b43ac78ba3");
  assert.deepEqual(signed.map(item=>item.primaryType),["PermitWitnessTransferFrom","Permit"]);
});

test("production guards reject API drift before submission",async()=>{
  assert.throws(()=>requirePermit2Challenge({...required,extensions:{}},boundary),/sponsorship/);
  assert.throws(()=>requirePermit2Challenge({...required,accepts:[{...required.accepts[0],extra:{assetTransferMethod:"eip3009"}}]},boundary),/sponsorship/);
  assert.throws(()=>requireSponsoredPayment({accepted:required.accepts[0],extensions:{}},boundary),/gas-sponsored/);
});
