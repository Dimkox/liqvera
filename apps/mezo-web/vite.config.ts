import { defineConfig } from "vite";

export default defineConfig({
  base: "/",
  server: { proxy: { "/v1": "http://127.0.0.1:8080" } },
  build: { outDir: "dist", emptyOutDir: true },
});
