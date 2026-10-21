export interface FinanceNetwork {
  name: 'testnet' | 'mainnet';
  chainId: number;
  asset: string;
  decimals: number;
}
export interface FinanceProvider {
  request(args: { method: string; params?: unknown[] }): Promise<unknown>;
}
export interface FinanceQuote {
  quote_id: string;
  state: string;
  terms: {
    network: string; chain_id: number; asset: string; decimals: number;
    amount_atomic: string; expected_payer: string; pay_to: string; expires_at: string;
  };
}
export interface FinanceContext {
  network: FinanceNetwork;
  account: string | null;
  quote: FinanceQuote | null;
  paymentGuard: string;
  busy: boolean;
  onMezo: boolean;
}
export function financeLinks(name: string): Readonly<{ borrow: string; borrowDocs: string }>;
export function fundingEligibility(context: FinanceContext, now?: number): { allowed: boolean; reason: string; requiredAtomic: bigint };
export function formatMusd(value: bigint): string;
export function readMusdBalance(provider: FinanceProvider, network: FinanceNetwork, account: string, timeoutMs?: number): Promise<bigint>;
export interface FundingObservation {
  schema: 'liqvera-musd-funding-observation/v1';
  network: string; chain_id: number; asset: string; decimals: number; account: string;
  block_number: string; block_hash: string; balance_atomic: string; required_atomic: string;
  shortfall_atomic: string; report_budget: string; observed_at: string; payment_submitted: false;
}
export function readFundingObservation(provider: FinanceProvider, network: FinanceNetwork, account: string, requiredAtomic: string, timeoutMs?: number): Promise<Readonly<FundingObservation>>;
