import { MEZO } from "./network.ts";

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
  sink.applyWalletState({ account: account(accounts), onMezo: typeof chain === "string" && chain.toLowerCase() === `0x${MEZO.chainId.toString(16)}` });
}

export function bindWalletStateListeners(provider: WalletEventProvider | null, sink: WalletStateSink): () => void {
  if (!provider?.on) return () => undefined;
  let active = true;
  let revision = 0;
  let queue = Promise.resolve();
  const refresh = async (current: number): Promise<void> => {
    if (!active || current !== revision) return;
    const currentSink: WalletStateSink = {
      applyWalletState(state) { if (active && current === revision) sink.applyWalletState(state); },
    };
    try { await refreshWalletState(provider, currentSink); }
    catch {
      try { currentSink.applyWalletState({ account: null, onMezo: false }); }
      catch { /* A view failure must not poison provider event processing. */ }
    }
  };
  const listener = (): void => {
    const current = revision;
    const run = (): Promise<void> => refresh(current);
    queue = queue.then(run, run).catch(() => undefined);
  };
  const disconnect = (): void => {
    if (!active) return;
    revision++;
    sink.applyWalletState({ account: null, onMezo: false });
  };
  provider.on("accountsChanged", listener);
  provider.on("chainChanged", listener);
  provider.on("disconnect", disconnect);
  return () => {
    active = false;
    provider.removeListener?.("accountsChanged", listener);
    provider.removeListener?.("chainChanged", listener);
    provider.removeListener?.("disconnect", disconnect);
  };
}

export function createWalletListenerOwner(sink:WalletStateSink):{replace(provider:WalletEventProvider|null):void;refresh():Promise<void>;dispose():void} {
  let active:WalletEventProvider|null=null;
  let revision = 0;
  let unbind=():void=>undefined;
  return {
    replace(provider) {
      if(provider===active)return;
      revision++;
      unbind();active=provider;unbind=bindWalletStateListeners(provider, {
        applyWalletState(state) { revision++; sink.applyWalletState(state); },
      });
    },
    async refresh() {
      const current = ++revision;
      const currentSink: WalletStateSink = {
        applyWalletState(state) { if (current === revision) sink.applyWalletState(state); },
      };
      if (!active) { currentSink.applyWalletState({ account: null, onMezo: false }); return; }
      try { await refreshWalletState(active, currentSink); }
      catch { currentSink.applyWalletState({ account: null, onMezo: false }); }
    },
    dispose() { revision++; unbind();unbind=()=>undefined;active=null; },
  };
}
