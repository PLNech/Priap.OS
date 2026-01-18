// @ts-check
import { defineConfig } from 'astro/config';

// https://astro.build/config
export default defineConfig({
  site: 'https://PLNech.github.io',
  base: '/Priap.OS',
  outDir: './dist',
  build: {
    assets: '_assets'
  }
});
