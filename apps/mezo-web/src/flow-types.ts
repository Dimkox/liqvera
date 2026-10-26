interface FlowBase {
  readonly payer: string;
  readonly idempotencyKey: string;
  readonly requestId?: string;
  readonly quoteId?: string;
  readonly paymentAttemptId?: string;
  readonly paymentTxHash?: string;
  readonly paymentBlockNumber?: number;
  readonly paymentGuard: "clear" | "started" | "uncertain";
}
export type BrowserFlowState = FlowBase & (
  { readonly version: 1; readonly side: "BUY" | "SELL"; readonly quantity: string; readonly product_id?: never; readonly borrower?: never } |
  { readonly version: 2; readonly product_id: "trove_risk"; readonly borrower: string; readonly side?: never; readonly quantity?: never }
);
export type CreateInput = { payer: string; idempotencyKey: string } & (
  { side: "BUY" | "SELL"; quantity: string; product_id?: never; borrower?: never } |
  { product_id: "trove_risk"; borrower: string; side?: never; quantity?: never }
);
