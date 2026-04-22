/**
 * Bun/Node runtime compat layer.
 *
 * The plugin bundle is built with `--target bun` for first-class support of
 * Bun.spawn / Bun.file / Bun.write. When the bundle is loaded under a plain
 * Node runtime (e.g. opencode packaged via `node` rather than bun), the
 * `Bun` global is undefined and those calls fail with:
 *
 *   Cannot destructure property 'spawn' of 'globalThis.Bun' as it is undefined
 *
 * This module exports small, behavior-compatible wrappers that prefer the
 * Bun implementation when available and fall back to `child_process` / `fs`
 * under Node.
 *
 * The fallbacks match only the subset of Bun APIs this plugin actually uses.
 * Do NOT expand this shim speculatively — keep it minimal.
 */

import { spawn as nodeSpawn, spawnSync as nodeSpawnSync } from "node:child_process"
import { readFile as nodeReadFile, writeFile as nodeWriteFile } from "node:fs/promises"

type SpawnOptions = {
  cwd?: string
  env?: Record<string, string>
  stdout?: "pipe" | "inherit" | "ignore"
  stderr?: "pipe" | "inherit" | "ignore"
  stdin?: "pipe" | "inherit" | "ignore"
}

export type SpawnHandle = {
  stdout: ReadableStream<Uint8Array> | null
  stderr: ReadableStream<Uint8Array> | null
  exited: Promise<number>
  exitCode: number | null
  kill: (signal?: string) => void
}

// Alias so files that import `type Subprocess` from "bun" can migrate by
// switching to this module without re-writing every callsite. Generic
// parameters are ignored — kept for source-compat with `Subprocess<I, O, E>`.
export type Subprocess<_Stdin = unknown, _Stdout = unknown, _Stderr = unknown> = SpawnHandle

function toWebStream(nodeStream: NodeJS.ReadableStream | null | undefined): ReadableStream<Uint8Array> | null {
  if (!nodeStream) return null
  // Node ≥17 has Readable.toWeb; fall back to manual pump for older runtimes.
  const asAny = nodeStream as unknown as { toWeb?: () => ReadableStream<Uint8Array> }
  if (typeof asAny.toWeb === "function") {
    return asAny.toWeb()
  }
  return new ReadableStream<Uint8Array>({
    start(controller) {
      nodeStream.on("data", (chunk: Buffer | string) => {
        controller.enqueue(typeof chunk === "string" ? new TextEncoder().encode(chunk) : chunk)
      })
      nodeStream.on("end", () => controller.close())
      nodeStream.on("error", (err: Error) => controller.error(err))
    },
  })
}

export function spawn(cmd: string[], opts: SpawnOptions = {}): SpawnHandle {
  const bun = (globalThis as { Bun?: { spawn: (cmd: string[], opts?: unknown) => unknown } }).Bun
  if (bun && typeof bun.spawn === "function") {
    return bun.spawn(cmd, opts) as SpawnHandle
  }
  const [file, ...args] = cmd
  const child = nodeSpawn(file, args, {
    cwd: opts.cwd,
    env: opts.env,
    stdio: [
      opts.stdin ?? "pipe",
      opts.stdout ?? "pipe",
      opts.stderr ?? "pipe",
    ],
  })
  let exitCode: number | null = null
  const exited = new Promise<number>((resolve) => {
    child.on("close", (code) => {
      exitCode = code ?? 0
      resolve(code ?? 0)
    })
  })
  return {
    stdout: toWebStream(child.stdout),
    stderr: toWebStream(child.stderr),
    get exitCode() {
      return exitCode
    },
    exited,
    kill: (signal?: string) => child.kill(signal as NodeJS.Signals | undefined),
  }
}

export async function readFileText(path: string): Promise<string> {
  const bun = (globalThis as { Bun?: { file: (p: string) => { text: () => Promise<string> } } }).Bun
  if (bun && typeof bun.file === "function") {
    return bun.file(path).text()
  }
  return nodeReadFile(path, "utf8")
}

type SpawnSyncResult = {
  exitCode: number | null
  stdout: Uint8Array
  stderr: Uint8Array
}

export function spawnSync(cmd: string[], opts: SpawnOptions = {}): SpawnSyncResult {
  const bun = (globalThis as { Bun?: { spawnSync: (cmd: string[], opts?: unknown) => unknown } }).Bun
  if (bun && typeof bun.spawnSync === "function") {
    return bun.spawnSync(cmd, opts) as SpawnSyncResult
  }
  const [file, ...args] = cmd
  const result = nodeSpawnSync(file, args, {
    cwd: opts.cwd,
    env: opts.env,
    stdio: [
      opts.stdin ?? "pipe",
      opts.stdout ?? "pipe",
      opts.stderr ?? "pipe",
    ],
  })
  return {
    exitCode: result.status,
    stdout: result.stdout ? new Uint8Array(result.stdout) : new Uint8Array(0),
    stderr: result.stderr ? new Uint8Array(result.stderr) : new Uint8Array(0),
  }
}

export async function writeFile(path: string, data: ArrayBuffer | Uint8Array | string): Promise<void> {
  const bun = (globalThis as { Bun?: { write: (p: string, d: unknown) => Promise<unknown> } }).Bun
  if (bun && typeof bun.write === "function") {
    await bun.write(path, data as unknown)
    return
  }
  if (data instanceof ArrayBuffer) {
    await nodeWriteFile(path, new Uint8Array(data))
  } else {
    await nodeWriteFile(path, data as Uint8Array | string)
  }
}
