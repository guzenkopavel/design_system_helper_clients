import { spawnSync } from "node:child_process"
import type { Plugin } from "@opencode-ai/plugin"

type Payload = Record<string, unknown>

function runHook(root: string, event: "pre-tool" | "post-edit", payload: Payload): void {
  const result = spawnSync(
    "python3",
    ["workflow/hooks/hook-runner.py", "--runtime", "opencode", "--event", event],
    {
      cwd: root,
      input: JSON.stringify(payload),
      encoding: "utf8",
    },
  )
  const output = result.stdout.trim()
  if (result.status === 2) {
    throw new Error(output || "Harness hook denied the operation")
  }
  if (result.status !== 0) {
    throw new Error(result.stderr.trim() || "Harness hook failed")
  }
  if (output) {
    const report = JSON.parse(output) as { decision?: string }
    if (report.decision === "warn") {
      console.warn(output)
    }
  }
}

export const HarnessHooks: Plugin = async ({ worktree }) => ({
  "tool.execute.before": async (input, output) => {
    runHook(worktree, "pre-tool", {
      ...input,
      ...output,
      tool_name: input.tool,
      tool_input: output.args,
    })
  },
  "tool.execute.after": async (input, output) => {
    runHook(worktree, "post-edit", {
      ...input,
      ...output,
      tool_name: input.tool,
      tool_input: input.args,
    })
  },
})
