#!/usr/bin/env bun
// Use Bun.build() API directly — `bun build` CLI collides with package.json `build` script on bun >=1.3.
import { $ } from "bun"

const shared = {
  target: "bun",
  format: "esm",
  external: ["@ast-grep/napi"],
}

let r = await Bun.build({ ...shared, entrypoints: ["src/index.ts"], outdir: "dist" })
if (!r.success) { console.error(r.logs); process.exit(1) }

// tsc emits declarations even when there are unrelated type errors in test
// files and CLI code that assumes a Bun runtime. We want the .d.ts output
// regardless; tolerate non-zero exit and only fail the build if the bundler
// itself fails.
try {
  await $`npx tsc --emitDeclarationOnly`
} catch (err) {
  console.warn("tsc emitted errors (continuing): declarations still written where possible")
}

r = await Bun.build({ ...shared, entrypoints: ["src/cli/index.ts"], outdir: "dist/cli" })
if (!r.success) { console.error(r.logs); process.exit(1) }

console.log("build ok")
