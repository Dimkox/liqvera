import type { PaymentPayload, PaymentRequired } from "@x402/core/types";
import type { ClientEvmSigner } from "@x402/evm";
import type { x402HTTPClient } from "@x402/core/client";

export interface Permit2Boundary {
  assetTransferMethod: string;
  domainName: string;
  domainVersion: string;
  requiredExtension: string;
}
export function createProductionProtocol(signer: ClientEvmSigner, rpcUrl: string): x402HTTPClient;
export function requirePermit2Challenge(required: PaymentRequired, permit: Permit2Boundary): void;
export function requireSponsoredPayment(payment: PaymentPayload, permit: Permit2Boundary): void;
