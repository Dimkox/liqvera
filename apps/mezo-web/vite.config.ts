import { defineConfig, loadEnv } from "vite";
import { readFileSync } from "node:fs";

const appVersion: string = JSON.parse(readFileSync(new URL("./package.json", import.meta.url), "utf8")).version;

// Local dev/preview proxy for the frozen /v1 gateway API. Default: a local gateway on :8080.
// LIQVERA_API_PROXY=https://liqvera.site points it at the deployed Mezo Testnet gateway instead.
// The browser stays same-origin; the proxy drops Origin/Referer so the gateway treats it like a
// server-side client (it rejects unknown Origins, and localhost is not in its allowlist).
function apiProxy(mode: string) {
  const target = loadEnv(mode, ".", "").LIQVERA_API_PROXY || "http://127.0.0.1:8080";
  const url = new URL(target);
  if (!["http:", "https:"].includes(url.protocol) || url.pathname !== "/" || url.search || url.username) throw new Error("LIQVERA_API_PROXY must be a bare http(s) origin.");
  return { "/v1": { target: url.origin, changeOrigin: true, secure: true,
    configure: (proxy: { on: (event: "proxyReq", cb: (req: { removeHeader: (name: string) => void }) => void) => void }) =>
      proxy.on("proxyReq", req => { req.removeHeader("origin"); req.removeHeader("referer"); }) } };
}

export default defineConfig(({mode}) => ({
  define: {
    __LIQVERA_APP_VERSION__: JSON.stringify(appVersion),
    __LIQVERA_NETWORK__: JSON.stringify(loadEnv(mode, ".", "").LIQVERA_NETWORK ?? "testnet"),
    __LIQVERA_GUARD_WATCH_API__: JSON.stringify(loadEnv(mode, ".", "").LIQVERA_GUARD_WATCH_API ?? ""),
    __LIQVERA_WALLETCONNECT_PROJECT_ID__: JSON.stringify(loadEnv(mode, ".", "").LIQVERA_WALLETCONNECT_PROJECT_ID ?? ""),
  },
  base: "/",
  server: { proxy: apiProxy(mode) },
  preview: { proxy: apiProxy(mode) },
  build: { outDir: "dist", emptyOutDir: true },
}));
