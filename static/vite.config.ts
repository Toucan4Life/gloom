import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';
import { resolve } from 'node:path';

const rootDir = import.meta.dirname;

// Builds the app into static/dist/ with fixed, unhashed asset filenames
// (bundle.js / style.css) so the Flask Jinja template (index.html) and the
// GitHub Pages templates (gh-pages/index.html, gh-pages/404.html) can keep
// referencing them without needing a manifest.
export default defineConfig( {
  root: rootDir,
  plugins: [ react(), tailwindcss() ],
  build: {
    outDir: 'dist',
    emptyOutDir: false, // preserve dist/py (Pyodide solver sources) copied separately
    cssCodeSplit: false,
    rollupOptions: {
      input: resolve( rootDir, 'src/main.tsx' ),
      output: {
        entryFileNames: 'bundle.js',
        chunkFileNames: 'bundle-[name].js',
        assetFileNames: ( assetInfo ) => {
          const name = assetInfo.names?.[ 0 ] ?? assetInfo.name ?? '';
          return name.endsWith( '.css' ) ? 'style.css' : 'assets/[name][extname]';
        },
      },
    },
  },
} );
