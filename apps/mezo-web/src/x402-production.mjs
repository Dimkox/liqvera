import { x402Client, x402HTTPClient } from "@x402/core/client";
import { ExactEvmScheme } from "@x402/evm";

export function createProductionProtocol(signer, rpcUrl) {
  return new x402HTTPClient(new x402Client().register("eip155:31611", new ExactEvmScheme(signer, { rpcUrl })));
}

export function requirePermit2Challenge(required, permit) {
  if (required.accepts.length !== 1 || required.accepts[0]?.extra?.assetTransferMethod !== permit.assetTransferMethod ||
    required.accepts[0]?.extra?.name !== permit.domainName || required.accepts[0]?.extra?.version !== permit.domainVersion ||
    !required.extensions || Object.keys(required.extensions).length !== 1 || !(permit.requiredExtension in required.extensions))
    throw new Error("Permit2 EIP-2612 sponsorship is required. No payment was submitted.");
}

export function requireSponsoredPayment(payment, permit) {
  if (payment.accepted.extra?.assetTransferMethod !== permit.assetTransferMethod || !payment.extensions ||
    Object.keys(payment.extensions).length !== 1 || !(permit.requiredExtension in payment.extensions))
    throw new Error("Wallet did not produce the required gas-sponsored payment. No payment was submitted.");
}
