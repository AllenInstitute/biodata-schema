import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = dirname(fileURLToPath(import.meta.url));

export default defineConfig(({ command }) => ({
  root,
  plugins: [react()],
  server: { host: "127.0.0.1", port: 5174, strictPort: false },
  ...(command === "build" ? { define: { "process.env.NODE_ENV": JSON.stringify("production") } } : {}),
  build: {
    outDir: resolve(root, "../docs/source/_static/qc-tree-app"),
    emptyOutDir: false,
    cssCodeSplit: false,
    lib: {
      entry: resolve(root, "src/main.tsx"),
      formats: ["es"],
      fileName: () => "qc-tree-app.js",
    },
    rollupOptions: {
      output: { assetFileNames: "qc-tree-app.[ext]" },
    },
  },
}));
