interface WalletEventProvider {
  request(input: { method: string; params?: unknown[] }): Promise<unknown>;
  on?(event: string, listener: (...args: unknown[]) => void): void;
  removeListener?(event: string, listener: (...args: unknown[]) => void): void;
}

export interface WalletState {
  account: string | null;
  onMezo: boolean;
}

export interface WalletStateSink {
  applyWalletState(state: WalletState): void;
}

function account(value: unknown): string | null {
  if (!Array.isArray(value) || typeof value[0] !== "string" || !/^0x[0-9a-f]{40}$/i.test(value[0])) return null;
  return value[0];
}

export async function refreshWalletState(provider: WalletEventProvider, sink: WalletStateSink): Promise<void> {
  const [accounts, chain] = await Promise.all([
    provider.request({ method: "eth_accounts" }),
    provider.request({ method: "eth_chainId" }),
  ]);
  sink.applyWalletState({ account: account(accounts), onMezo: typeof chain === "string" && chain.toLowerCase() === "0x7b7b" });
}

export function bindWalletStateListeners(provider: WalletEventProvider | null, sink: WalletStateSink): () => void {
  if (!provider?.on) return () => undefined;
  let queue = Promise.resolve();
  const refresh = async (): Promise<void> => {
    try { await refreshWalletState(provider, sink); }
    catch {
      try { sink.applyWalletState({ account: null, onMezo: false }); }
      catch { /* A view failure must not poison provider event processing. */ }
    }
  };
  const listener = (): void => {
    queue = queue.then(refresh, refresh).catch(() => undefined);
  };
  provider.on("accountsChanged", listener);
  provider.on("chainChanged", listener);
  return () => {
    provider.removeListener?.("accountsChanged", listener);
    provider.removeListener?.("chainChanged", listener);
  };
}

export function createWalletListenerOwner(sink:WalletStateSink):{replace(provider:WalletEventProvider|null):void;dispose():void} {
  let active:WalletEventProvider|null=null;
  let unbind=():void=>undefined;
  return {
    replace(provider) {
      if(provider===active)return;
      unbind();active=provider;unbind=bindWalletStateListeners(provider,sink);
    },
    dispose() { unbind();unbind=()=>undefined;active=null; },
  };
}
