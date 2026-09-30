import { createStore, type EIP6963ProviderDetail, type Store } from "mipd";
import type { Eip1193Provider } from "./wallet";

export interface WalletChoice { id:string; name:string; provider:Eip1193Provider; source:"eip6963"|"legacy" }
export function walletChoices(store:Pick<Store,"getProviders">,legacy:Eip1193Provider|null):WalletChoice[] {
  const announced=store.getProviders().map((detail:EIP6963ProviderDetail)=>({id:detail.info.uuid,name:detail.info.name,
    provider:detail.provider as Eip1193Provider,source:"eip6963" as const})).sort((a,b)=>a.name.localeCompare(b.name)||a.id.localeCompare(b.id));
  return announced.length?announced:(legacy?[{id:"legacy-window-ethereum",name:"Browser wallet",provider:legacy,source:"legacy"}]:[]);
}
export const walletStore=createStore();
