import { MEZO } from "./network.ts";
import { CHAIN_HEX, isAddress } from "./contracts.ts";

export interface Eip1193Provider {
  request(args: { method: string; params?: unknown[] }): Promise<unknown>;
  on?(event: string, listener: (...args: unknown[]) => void): void;
  removeListener?(event: string, listener: (...args: unknown[]) => void): void;
}

declare global {
  interface Window { ethereum?: Eip1193Provider; trustwallet?: { ethereum?: Eip1193Provider } }
}

export function injectedWallet(): Eip1193Provider | null {
  return window.ethereum ?? window.trustwallet?.ethereum ?? null;
}

function firstAccount(value: unknown): string | null {
  if (!Array.isArray(value) || typeof value[0] !== "string" || !isAddress(value[0])) return null;
  return value[0];
}

export async function walletAccount(provider: Eip1193Provider, requestAccess: boolean): Promise<string | null> {
  return firstAccount(await provider.request({ method: requestAccess ? "eth_requestAccounts" : "eth_accounts" }));
}

export async function walletOnMezo(provider: Eip1193Provider): Promise<boolean> {
  const chain = await provider.request({ method: "eth_chainId" });
  if (typeof chain !== "string" || !/^0x[0-9a-f]+$/i.test(chain)) return false;
  try { return Number.parseInt(chain, 16) === MEZO.chainId; }
  catch { return false; }
}

export async function switchToMezo(provider: Eip1193Provider): Promise<void> {
  try { await provider.request({ method: "wallet_switchEthereumChain", params: [{ chainId: CHAIN_HEX }] }); }
  catch (error) {
    if(typeof error!=="object"||error===null||!("code" in error)||error.code!==4902)throw error;
    await provider.request({method:"wallet_addEthereumChain",params:[{chainId:CHAIN_HEX,chainName:MEZO.name,
      nativeCurrency:{name:"Bitcoin",symbol:"BTC",decimals:18},rpcUrls:[MEZO.rpcUrl],blockExplorerUrls:[MEZO.explorerUrl]}]});
    // Adding a chain does not select it (EIP-3085).
    if (!(await walletOnMezo(provider))) {
      await provider.request({ method: "wallet_switchEthereumChain", params: [{ chainId: CHAIN_HEX }] });
    }
  }
  if (!(await walletOnMezo(provider))) throw new Error("Wallet is still on a different network.");
}

export function walletError(error: unknown): string {
  if (typeof error === "object" && error !== null && "code" in error && error.code === 4001) {
    return "Wallet request canceled. No payment was confirmed by this action.";
  }
  return "Wallet action failed. Check your wallet and the current report status.";
}
