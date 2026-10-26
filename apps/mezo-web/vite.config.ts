import { defineConfig, loadEnv } from "vite";
import { readFileSync } from "node:fs";

const appVersion: string = JSON.parse(readFileSync(new URL("./package.json", import.meta.url), "utf8")).version;

export default defineConfig(({mode}) => ({
  define: {
    __LIQVERA_APP_VERSION__: JSON.stringify(appVersion),
    __LIQVERA_NETWORK__: JSON.stringify(loadEnv(mode, ".", "").LIQVERA_NETWORK ?? "testnet"),
    __LIQVERA_WALLETCONNECT_PROJECT_ID__: JSON.stringify(loadEnv(mode, ".", "").LIQVERA_WALLETCONNECT_PROJECT_ID ?? ""),
  },
  base: "/",
  server: { proxy: { "/v1": "http://127.0.0.1:8080" } },
  build: { outDir: "dist", emptyOutDir: true },
}));
