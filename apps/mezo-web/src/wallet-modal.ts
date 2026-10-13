import type { Eip1193Provider } from "./wallet.ts";

interface WalletModal {
  subscribeProviders(callback: (providers: { eip155?: unknown }) => void): () => void;
  getWalletProvider(): unknown;
  open(): Promise<unknown>;
  switchNetwork(): Promise<void>;
}

// AppKit owns discovery, pairing and session persistence. This bridge only passes
// its selected EIP-1193 provider to the existing Liqvera payment flow.
export function createWalletModal(load: () => Promise<WalletModal>, selected: (provider: Eip1193Provider | null) => void) {
  let loading: Promise<WalletModal> | undefined;
  const update = (provider: unknown): void => {
    selected(provider && typeof (provider as Eip1193Provider).request === "function" ? provider as Eip1193Provider : null);
  };
  const restore = (): Promise<WalletModal> => {
    loading ??= load().then(modal => {
      modal.subscribeProviders(providers => update(providers.eip155));
      update(modal.getWalletProvider());
      return modal;
    }).catch(error => { loading = undefined; throw error; });
    return loading;
  };
  return {
    restore,
    async open(): Promise<void> { await (await restore()).open(); },
    async switchNetwork(): Promise<void> { await (await restore()).switchNetwork(); },
  };
}
