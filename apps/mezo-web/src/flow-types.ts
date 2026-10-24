interface FlowBase {
  readonly payer: string;
  readonly idempotencyKey: string;
  readonly requestId?: string;
  readonly quoteId?: string;
  readonly paymentGuard: "clear" | "started" | "uncertain";
}
export type BrowserFlowState = FlowBase & (
  { readonly version: 1; readonly side: "BUY" | "SELL"; readonly quantity: string; readonly product_id?: never; readonly borrower?: never; readonly mezo_dex?: never } |
  { readonly version: 2; readonly product_id: "trove_risk"; readonly borrower: string; readonly side?: never; readonly quantity?: never; readonly mezo_dex?: never } |
  { readonly version: 3; readonly side: "BUY" | "SELL"; readonly quantity: string; readonly mezo_dex: true; readonly product_id?: never; readonly borrower?: never }
);
export type CreateInput = { payer: string; idempotencyKey: string } & (
  { side: "BUY" | "SELL"; quantity: string; mezo_dex?: true; product_id?: never; borrower?: never } |
  { product_id: "trove_risk"; borrower: string; side?: never; quantity?: never }
);
