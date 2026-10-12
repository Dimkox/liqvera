import { mezoNetwork } from "@liqvera/mezo-protocol";
declare const __LIQVERA_NETWORK__: string;
export const NETWORK_CONFIG = mezoNetwork(typeof __LIQVERA_NETWORK__ === "undefined" ? "testnet" : __LIQVERA_NETWORK__);
export const MEZO = NETWORK_CONFIG.chain;
export const MUSD = NETWORK_CONFIG.asset;
export const NETWORK_LABEL = NETWORK_CONFIG.name === "mainnet" ? "Mezo Mainnet" : "Mezo Testnet";
export const TOKEN_LABEL = NETWORK_CONFIG.name === "mainnet" ? "MUSD" : "test MUSD";
