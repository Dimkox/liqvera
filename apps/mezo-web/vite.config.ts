import { defineConfig, loadEnv } from "vite";

export default defineConfig(({mode}) => ({
  define: { __LIQVERA_NETWORK__: JSON.stringify(loadEnv(mode, ".", "").LIQVERA_NETWORK ?? "testnet") },
  base: "/",
  server: { proxy: { "/v1": "http://127.0.0.1:8080" } },
  build: { outDir: "dist", emptyOutDir: true },
}));
