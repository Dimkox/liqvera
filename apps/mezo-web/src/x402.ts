import { MUSD_PERMIT } from "@liqvera/mezo-protocol";
import type { Delivery, Quote } from "./contracts";
import type { Eip1193Provider } from "./wallet";
import { x402Client, x402HTTPClient } from "@x402/core/client";
import { ExactEvmScheme, type ClientEvmSigner } from "@x402/evm";
import { validateDelivery } from "./api";

/**
 * Only a reviewed implementation using the installed official x402 browser SDK
 * may implement this interface. The v2 F1 pin proves the package family exists,
 * but not an EIP-1193 payment API. No caller may construct PAYMENT-SIGNATURE.
 */
export interface OfficialX402BrowserAdapter {
  readonly sdk: "@x402/paywall/2.16.0";
  requestPaidReport(input: {
    path: string;
    bearerCapability: string;
    quote: Quote;
    permitMetadata: typeof MUSD_PERMIT;
    provider: Eip1193Provider;
    payer: string;
  }): Promise<Delivery | "recovering">;
}

/** SDK implementations may use this only for a wallet rejection proven to occur before submission. */
export class X402CancelledBeforeSubmission extends Error {}

let reviewedAdapter: OfficialX402BrowserAdapter | null = null;

/** Register only after an exact SDK API/type review and payment safety review. */
export function registerReviewedX402Adapter(adapter: OfficialX402BrowserAdapter): void {
  if (adapter.sdk !== "@x402/paywall/2.16.0") throw new Error("Unreviewed x402 adapter version.");
  reviewedAdapter = adapter;
}

export function x402Available(): boolean {
  return reviewedAdapter !== null;
}

export async function requestPaidReport(input: Omit<Parameters<OfficialX402BrowserAdapter["requestPaidReport"]>[0], "permitMetadata">): Promise<Delivery | "recovering"> {
  if (!reviewedAdapter) throw new Error("The reviewed x402 browser payment adapter is not installed. No payment was submitted.");
  return reviewedAdapter.requestPaidReport({ ...input, permitMetadata: MUSD_PERMIT });
}

class ProductionX402BrowserAdapter implements OfficialX402BrowserAdapter {
  readonly sdk="@x402/paywall/2.16.0" as const;
  async requestPaidReport(input: Parameters<OfficialX402BrowserAdapter["requestPaidReport"]>[0]): Promise<Delivery|"recovering"> {
    if(input.path!==`/v1/reports/${input.quote.report_id}`||input.payer.toLowerCase()!==input.quote.terms.expected_payer||
      input.quote.terms.network!=="eip155:31611"||input.quote.terms.asset.toLowerCase()!=="0x118917a40faf1cd7a13db0ef56c86de7973ac503"||
      input.quote.terms.amount_atomic!=="10000000000000000")throw new Error("Payment terms changed. No payment was submitted.");
    const signer:ClientEvmSigner={address:input.payer as `0x${string}`,signTypedData:async message=>{
      const signature=await input.provider.request({method:"eth_signTypedData_v4",params:[input.payer,JSON.stringify(message)]});
      if(typeof signature!=="string"||!/^0x[0-9a-fA-F]{130}$/.test(signature))throw new X402CancelledBeforeSubmission();
      return signature as `0x${string}`;
    }};
    const protocol=new x402HTTPClient(new x402Client().register("eip155:31611",new ExactEvmScheme(signer)));
    const headers={Authorization:`Bearer ${input.bearerCapability}`,Accept:"application/json"};
    const controller=new AbortController();const deadline=setTimeout(()=>controller.abort(),15_000);
    try {
      const challenge=await fetch(input.path,{headers,cache:"no-store",credentials:"omit",redirect:"error",signal:controller.signal});
      if(challenge.status!==402)throw new Error("Expected an exact payment challenge. No payment was submitted.");
      const required=protocol.getPaymentRequiredResponse(name=>challenge.headers.get(name),await boundedResponseJson(challenge,65_536));
      const payment=await protocol.createPaymentPayload(required);
      const paid=await fetch(input.path,{headers:{...headers,...protocol.encodePaymentSignatureHeader(payment)},cache:"no-store",credentials:"omit",redirect:"error",signal:controller.signal});
      if(paid.status===202)return "recovering";
      if(!paid.ok)throw new Error("Payment outcome requires reconciliation.");
      await protocol.processPaymentResult(payment,name=>paid.headers.get(name),paid.status);
      return validateDelivery(await boundedResponseJson(paid,10_000_000),input.quote.report_id);
    } catch(error) {
      if(error instanceof X402CancelledBeforeSubmission)throw error;
      return "recovering";
    } finally { clearTimeout(deadline); }
  }
}

/** Production uses the exact pinned SDK; gateway readiness still requires an exact live grant. */
export function installProductionX402Adapter():void { registerReviewedX402Adapter(new ProductionX402BrowserAdapter()); }

export async function boundedResponseJson(response:Response,maximum:number):Promise<unknown>{
  const declared=response.headers.get("content-length");
  if(declared!==null&&(!/^[0-9]+$/.test(declared)||Number(declared)>maximum))throw new Error("Response exceeds the payment boundary.");
  if(!response.body)throw new Error("Payment response body missing.");
  const reader=response.body.getReader();const chunks:Uint8Array[]=[];let size=0;
  while(true){const item=await reader.read();if(item.done)break;size+=item.value.byteLength;if(size>maximum){await reader.cancel();throw new Error("Response exceeds the payment boundary.");}chunks.push(item.value);}
  const bytes=new Uint8Array(size);let offset=0;for(const chunk of chunks){bytes.set(chunk,offset);offset+=chunk.byteLength;}
  return JSON.parse(new TextDecoder("utf-8",{fatal:true}).decode(bytes));
}
