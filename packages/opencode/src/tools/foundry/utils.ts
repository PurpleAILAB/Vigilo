import { spawn } from "../../shared"

export async function runCommand(cmdArgs: string[]): Promise<{ stdout: string; stderr: string; exitCode: number }> {
  const proc = spawn(cmdArgs, {
    stdout: "pipe",
    stderr: "pipe",
  })

  const stdout = await new Response(proc.stdout).text()
  const stderr = await new Response(proc.stderr).text()
  const exitCode = await proc.exited

  return { stdout, stderr, exitCode }
}

export function parseTestSummary(stdout: string): { passed: number; failed: number } {
  const passMatch = stdout.match(/(\d+) tests? passed/)
  const failMatch = stdout.match(/(\d+) tests? failed/)
  return {
    passed: passMatch ? parseInt(passMatch[1]) : 0,
    failed: failMatch ? parseInt(failMatch[1]) : 0,
  }
}
