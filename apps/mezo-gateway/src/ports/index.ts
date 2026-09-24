import type { PaymentPayload, PaymentRequirements } from '@x402/core/types';
import type { Artifact, Attempt, AuthorizationIdentity, Confirmation, Quote, QuoteInput, Reason, Receipt } from '../domain/model.js';
export interface ReportService {
  healthy(): Promise<boolean>;
  build(reportId: string, input: QuoteInput, signal: AbortSignal): Promise<Artifact>;
  recover(artifact: Artifact, signal: AbortSignal): Promise<boolean>;
  cleanupReady(): boolean;
  cleanup(reportId: string, signal: AbortSignal): Promise<boolean>;
}
export interface ArtifactStore {
  healthy(): Promise<boolean>;
  read(artifact: Artifact, kind: 'report' | 'bundle'): Promise<Buffer>;
}
export interface PaymentPort {
  blockers(): Reason[];
  requirements(quote: Quote): Promise<{ header: string; value: PaymentRequirements }>;
  verify(header: string, quote: Quote): Promise<{ payload: PaymentPayload; requirements: PaymentRequirements; identity: AuthorizationIdentity }>;
  settle(payload: PaymentPayload, requirements: PaymentRequirements): Promise<{ tx_hash: string | null }>;
  confirm(quote: Quote, attempt: Attempt): Promise<Confirmation | null>;
  revalidate(quote: Quote, attempt: Attempt, receipt: Receipt): Promise<boolean>;
}
export interface AuthorizationPolicy {
  readonly reviewed: boolean;
  readonly version: string;
  identify(payload: PaymentPayload, quote: Quote): AuthorizationIdentity;
  bindsTransfer(attempt: Attempt, transaction: unknown, log: unknown): Promise<boolean>;
}
export interface FinalityPolicy {
  readonly reviewed: boolean;
  readonly version: string;
  isFinal(receipt: unknown, canonicalBlock: unknown, rpc: ReadonlyRpc): Promise<boolean>;
}
export interface ReadonlyRpc { call(method: 'eth_chainId' | 'eth_getTransactionReceipt' | 'eth_getTransactionByHash' | 'eth_getBlockByHash' | 'eth_getBlockByNumber', params: unknown[]): Promise<unknown> }
