import type { Plugin, Hooks } from "@opencode-ai/plugin"

import {
  createTodoContinuationEnforcer,
  createContextWindowMonitorHook,
  createToolOutputTruncatorHook,
  createSessionRecoveryHook,
  createAnthropicContextWindowLimitRecoveryHook,
  createBackgroundNotificationHook,
  createRulesInjectorHook,
  createThinkModeHook,
  createThinkingBlockValidatorHook,
  createEditErrorRecoveryHook,
  createDelegateTaskRetryHook,
} from "./hooks"
import { log, resetMessageCursor } from "./shared"
import {
  setMainSession,
  getMainSessionID,
  setSessionAgent,
  updateSessionAgent,
  clearSessionAgent,
} from "./features/claude-code-session-state"
import {
  builtinTools,
  foundryTools,
  createBackgroundOutput,
  createBackgroundCancel,
  createSkillTool,
  createSkillMcpTool,
  createSlashcommandTool,
  discoverCommandsSync,
  createDelegateTask,
  createCallVigiloAgent,
  interactive_bash,
  startBackgroundCheck,
  lspManager,
} from "./tools"
import * as providers from "./providers"
import * as confidenceScoring from "./utils/confidence-scoring"
import { BackgroundManager } from "./features/background-agent"
import { SkillMcpManager } from "./features/skill-mcp-manager"
import { initTaskToastManager } from "./features/task-toast-manager"
import {
  discoverOpencodeGlobalSkills,
  discoverOpencodeProjectSkills,
  mergeSkills,
} from "./features/opencode-skill-loader"
import { getBuiltinSkills } from "./features/builtin-skills"
import { loadVigiloConfig } from "./plugin-config"
import { createModelCacheState } from "./plugin-state"
import { createConfigHandler } from "./plugin-handlers"

const VigiloPlugin: Plugin = async (ctx) => {
  log("[vigilo] ENTRY - plugin loading", { directory: ctx.directory })
  
  startBackgroundCheck()

  const pluginConfig = loadVigiloConfig(ctx.directory, ctx)
  const modelCacheState = createModelCacheState()

  const contextWindowMonitor = createContextWindowMonitorHook(ctx)
  const sessionRecovery = createSessionRecoveryHook(ctx, { experimental: pluginConfig.experimental })
  const toolOutputTruncator = createToolOutputTruncatorHook(ctx, {
    experimental: pluginConfig.experimental,
  })
  const thinkMode = createThinkModeHook()
  const anthropicContextWindowLimitRecovery = createAnthropicContextWindowLimitRecoveryHook(ctx, {
    experimental: pluginConfig.experimental,
  })
  const rulesInjector = createRulesInjectorHook(ctx)
  const thinkingBlockValidator = createThinkingBlockValidatorHook()
  const editErrorRecovery = createEditErrorRecoveryHook(ctx)
  const delegateTaskRetry = createDelegateTaskRetryHook(ctx)

  const backgroundManager = new BackgroundManager(ctx)
  
  initTaskToastManager(ctx.client)
  
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const tuiClient = ctx.client as any
  if (tuiClient.tui?.showToast) {
    tuiClient.tui.showToast({
      body: {
        title: "Vigilo Loaded",
        message: "Plugin initialized successfully. delegate_task and background tools ready.",
        variant: "info",
        duration: 3000,
      },
    }).catch(() => {})
    log("[vigilo] Toast API available - sent test toast")
  } else {
    log("[vigilo] WARNING: Toast API not available (client.tui.showToast missing)")
  }

  const todoContinuationEnforcer = createTodoContinuationEnforcer(ctx, { backgroundManager })
  
  if (sessionRecovery && todoContinuationEnforcer) {
    sessionRecovery.setOnAbortCallback(todoContinuationEnforcer.markRecovering)
    sessionRecovery.setOnRecoveryCompleteCallback(todoContinuationEnforcer.markRecoveryComplete)
  }

  const backgroundNotificationHook = createBackgroundNotificationHook(backgroundManager)
  const backgroundTools = {
    background_output: createBackgroundOutput(backgroundManager, ctx.client),
    background_cancel: createBackgroundCancel(backgroundManager, ctx.client),
  }

  const delegateTask = createDelegateTask({
    manager: backgroundManager,
    client: ctx.client,
    directory: ctx.directory,
  })

  const callVigiloAgent = createCallVigiloAgent(ctx, backgroundManager)

  const builtinSkills = getBuiltinSkills()
  
  const [globalSkills, projectSkills] = await Promise.all([
    discoverOpencodeGlobalSkills(),
    discoverOpencodeProjectSkills(),
  ])
  const mergedSkills = mergeSkills(builtinSkills, undefined, [], globalSkills, [], projectSkills)
  
  const skillMcpManager = new SkillMcpManager()
  const getSessionIDForMcp = () => getMainSessionID() || ""
  const skillTool = createSkillTool({
    skills: mergedSkills,
    mcpManager: skillMcpManager,
    getSessionID: getSessionIDForMcp,
  })
  const skillMcpTool = createSkillMcpTool({
    manager: skillMcpManager,
    getLoadedSkills: () => mergedSkills,
    getSessionID: getSessionIDForMcp,
  })

  const commands = discoverCommandsSync()
  const slashcommandTool = createSlashcommandTool({
    commands,
    skills: mergedSkills,
  })

  const configHandler = createConfigHandler({
    ctx: { directory: ctx.directory, client: ctx.client },
    pluginConfig,
    modelCacheState,
  })

  log("[vigilo] hooks and tools ready")

  const hooks: Hooks = {
    tool: {
      ...builtinTools,
      ...foundryTools,
      ...backgroundTools,
      delegate_task: delegateTask,
      call_vigilo_agent: callVigiloAgent,
      skill: skillTool,
      skill_mcp: skillMcpTool,
      slashcommand: slashcommandTool,
      interactive_bash,
    },

    config: configHandler,

    event: async (input) => {
      await backgroundNotificationHook?.event(input)
      await todoContinuationEnforcer?.handler(input)
      await contextWindowMonitor?.event(input)
      await rulesInjector?.event(input)
      await thinkMode?.event(input)
      await anthropicContextWindowLimitRecovery?.event(input)

      const { event } = input
      const props = event.properties as Record<string, unknown> | undefined

      if (event.type === "session.created") {
        const sessionInfo = props?.info as { id?: string; title?: string; parentID?: string } | undefined
        log("[event] session.created", { sessionInfo, props })
        if (!sessionInfo?.parentID) {
          setMainSession(sessionInfo?.id)
        }
      }

      if (event.type === "session.deleted") {
        const sessionInfo = props?.info as { id?: string } | undefined
        if (sessionInfo?.id === getMainSessionID()) {
          setMainSession(undefined)
        }
        if (sessionInfo?.id) {
          clearSessionAgent(sessionInfo.id)
          resetMessageCursor(sessionInfo.id)
          await skillMcpManager.disconnectSession(sessionInfo.id)
        }
      }

      if (event.type === "message.updated") {
        const info = props?.info as Record<string, unknown> | undefined
        const sessionID = info?.sessionID as string | undefined
        const agent = info?.agent as string | undefined
        const role = info?.role as string | undefined
        if (sessionID && agent && role === "user") {
          updateSessionAgent(sessionID, agent)
        }
      }

      if (event.type === "session.error") {
        const sessionID = props?.sessionID as string | undefined
        const error = props?.error

        if (sessionRecovery?.isRecoverableError(error)) {
          const messageInfo = {
            id: props?.messageID as string | undefined,
            role: "assistant" as const,
            sessionID,
            error,
          }
          const recovered = await sessionRecovery.handleSessionRecovery(messageInfo)

          if (recovered && sessionID && sessionID === getMainSessionID()) {
            await ctx.client.session
              .prompt({
                path: { id: sessionID },
                body: { parts: [{ type: "text", text: "continue" }] },
                query: { directory: ctx.directory },
              })
              .catch(() => {})
          }
        }
      }
    },

    "chat.message": async (input, output) => {
      if (input.agent) {
        setSessionAgent(input.sessionID, input.agent)
      }
    },

    "experimental.chat.messages.transform": async (
      input: Record<string, never>,
      output: { messages: Array<{ info: unknown; parts: unknown[] }> }
    ) => {
      if (thinkingBlockValidator?.["experimental.chat.messages.transform"]) {
        await thinkingBlockValidator["experimental.chat.messages.transform"](
          input,
          output as never
        )
      }
    },

    "tool.execute.before": async (input, output) => {
      await rulesInjector?.["tool.execute.before"]?.(input, output)
    },

    "tool.execute.after": async (input, output) => {
      await toolOutputTruncator?.["tool.execute.after"](input, output)
      await contextWindowMonitor?.["tool.execute.after"](input, output)
      await rulesInjector?.["tool.execute.after"](input, output)
      await editErrorRecovery?.["tool.execute.after"](input, output)
      await delegateTaskRetry?.["tool.execute.after"](input, output)
    },
  }

  return hooks
}

export default VigiloPlugin

export { providers, confidenceScoring }
