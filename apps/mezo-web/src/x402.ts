import { MUSD_PERMIT } from "@liqvera/mezo-protocol";
import type { Delivery, Quote } from "./contracts";
import type { Eip1193Provider } from "./wallet";

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
