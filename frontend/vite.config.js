import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import path from 'node:path'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],

  resolve: {
    // Permite imports absolutos: `import Button from '@/components/ui/Button'`
    alias: { '@': path.resolve(process.cwd(), 'src') },
  },

  server: {
    port: 5173,
    strictPort: true,
    // O proxy evita CORS em desenvolvimento e mantém as chamadas em rotas
    // relativas (/api/...), então o build de produção funciona sem alteração
    // quando front e back são servidos pelo mesmo host.
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        ws: true, // necessário para o canal de notificações
      },
    },
  },

  build: {
    outDir: 'dist',
    sourcemap: false,
    rollupOptions: {
      output: {
        // Separa dependências pesadas do bundle principal.
        manualChunks: {
          vendor: ['react', 'react-dom', 'react-router-dom'],
          markdown: ['react-markdown', 'remark-gfm'],
        },
      },
    },
  },
})
