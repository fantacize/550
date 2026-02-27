import { defineConfig } from "vite";
import react from "@vitejs/plugin-react-swc";

// basic vite setup
export default defineConfig({
  server: {
    host: "::",
    port: 8080,
  },
  plugins: [react()],
});
