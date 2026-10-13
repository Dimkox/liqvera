import { AppKit, CoreHelperUtil } from "@reown/appkit";
import { EthersAdapter } from "@reown/appkit-adapter-ethers";
import { mezo, mezoTestnet } from "@reown/appkit/networks";
import { MEZO, NETWORK_CONFIG } from "./network.ts";
import { walletOnMezo, type Eip1193Provider } from "./wallet.ts";

export async function loadWalletAppKit(projectId: string) {
  if (!/^[a-f0-9]{32}$/i.test(projectId)) throw new Error("Wallet connection is not configured. Please contact Liqvera.");
  const network = NETWORK_CONFIG.name === "mainnet" ? mezo : mezoTestnet;
  const adapters = [new EthersAdapter()];
  // The pinned SDK's public constructor exposes connection-only mode; its
  // createAppKit factory omits this option. Keep the SDK version in sync with
  // package.json and exercise the full modal when upgrading.
  const modal = new AppKit({
    // Connection-only mode also prevents dashboard feature flags from enabling
    // authentication/sign-in prompts or other unrelated wallet operations.
    basic: true,
    adapters,
    sdkVersion: CoreHelperUtil.generateSdkVersion(adapters, "html", "1.8.24"),
    networks: [network],
    defaultNetwork: network,
    projectId,
    metadata: {
      name: "Liqvera",
      description: "Market reports you can verify",
      url: "https://liqvera.site",
      icons: ["https://liqvera.site/icon.svg"],
    },
    customRpcUrls: { [`eip155:${MEZO.chainId}`]: [{ url: MEZO.rpcUrl }] },
    enableCoinbase: false,
    enableBaseAccount: false,
    features: { analytics: false, email: false, socials: false, swaps: false, onramp: false, send: false, receive: false, history: false },
    themeMode: "dark",
    themeVariables: { "--w3m-font-family": "Arial, sans-serif", "--w3m-accent": "#d6f582" },
  });
  await modal.ready();
  return {
    subscribeProviders: modal.subscribeProviders.bind(modal),
    getWalletProvider: modal.getWalletProvider.bind(modal),
    open: () => modal.open(),
    async switchNetwork(): Promise<void> {
      const provider = modal.getWalletProvider() as Eip1193Provider | undefined;
      if (!provider) throw new Error("Connect your wallet first.");
      await modal.switchNetwork(network, { throwOnFailure: true });
      if (provider !== modal.getWalletProvider()) throw new Error("Wallet changed during network selection.");
      // Some wallets add a previously unknown chain without selecting it.
      if (!(await walletOnMezo(provider))) await modal.switchNetwork(network, { throwOnFailure: true });
      if (provider !== modal.getWalletProvider() || !(await walletOnMezo(provider))) {
        throw new Error("Wallet is still on a different network.");
      }
    },
  };
}
