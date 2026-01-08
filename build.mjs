import * as esbuild from 'esbuild';
import { copyFileSync, mkdirSync, readFileSync, writeFileSync } from 'fs';

const isWatch = process.argv.includes('--watch');

// TipTap bundle (ES module for import)
const tiptapBuild = {
  entryPoints: ['src/tiptap.js'],
  bundle: true,
  format: 'esm',
  outfile: 'static/js/vendor/tiptap.bundle.js',
  minify: true,
  sourcemap: true,
  target: ['es2020'],
};

// HTMX bundle (IIFE for global script)
const htmxBuild = {
  entryPoints: ['src/htmx.js'],
  bundle: true,
  format: 'iife',
  outfile: 'static/js/vendor/htmx.bundle.js',
  minify: true,
  sourcemap: true,
  target: ['es2020'],
};

// Alpine.js bundle (IIFE for global script)
const alpineBuild = {
  entryPoints: ['src/alpine.js'],
  bundle: true,
  format: 'iife',
  outfile: 'static/js/vendor/alpine.bundle.js',
  minify: true,
  sourcemap: true,
  target: ['es2020'],
};

// Copy Lucide icon font files
function copyLucideAssets() {
  const srcDir = 'node_modules/lucide-static/font';
  const destDir = 'static/fonts/lucide';

  // Create destination directory
  mkdirSync(destDir, { recursive: true });

  // Copy font files (woff2 for modern browsers, woff for fallback)
  copyFileSync(`${srcDir}/lucide.woff2`, `${destDir}/lucide.woff2`);
  copyFileSync(`${srcDir}/lucide.woff`, `${destDir}/lucide.woff`);

  // Read and modify CSS to use correct font paths
  let css = readFileSync(`${srcDir}/lucide.css`, 'utf8');

  // Replace the entire @font-face block with a simplified version
  // that only uses woff2 and woff (modern browsers)
  const fontFace = `@font-face {
  font-family: "lucide";
  src: url("../fonts/lucide/lucide.woff2") format("woff2"),
       url("../fonts/lucide/lucide.woff") format("woff");
}`;

  // Replace original @font-face block
  css = css.replace(/@font-face\s*\{[^}]+\}/s, fontFace);

  writeFileSync('static/css/lucide.css', css);

  console.log('Lucide assets copied:');
  console.log('  static/fonts/lucide/lucide.woff2');
  console.log('  static/fonts/lucide/lucide.woff');
  console.log('  static/css/lucide.css');
}

const builds = [tiptapBuild, htmxBuild, alpineBuild];

if (isWatch) {
  // Watch mode: create contexts for all builds
  const contexts = await Promise.all(
    builds.map(config => esbuild.context(config))
  );
  await Promise.all(contexts.map(ctx => ctx.watch()));
  console.log('Watching for changes...');
} else {
  // Build all bundles
  await Promise.all(builds.map(config => esbuild.build(config)));
  console.log('Build complete:');
  builds.forEach(b => console.log(`  ${b.outfile}`));

  // Copy Lucide assets
  copyLucideAssets();
}
