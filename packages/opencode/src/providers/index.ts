/**
 * Model Provider Abstraction Layer - Decepticon-Level Tier-Based Fallback
 * 
 * This module provides a unified interface for LLM providers with:
 * - Tier-based model selection (HIGH, MID, LOW)
 * - Credentials-aware fallback chains
 * - Automatic failover on rate limits/errors
 * - Provider health monitoring
 */

import type {
  ModelTier,
  ModelProfile,
  ProviderName,
  ProviderConfig,
  ModelFallbackChain,
} from "../agents/types"

// =============================================================================
// PROVIDER DEFINITIONS
// =============================================================================

/** Configuration for each provider */
export const PROVIDER_DEFAULTS: Record<ProviderName, ProviderConfig> = {
  anthropic: {
    name: "anthropic",
    apiKey: process.env.ANTHROPIC_API_KEY || "",
    baseUrl: process.env.ANTHROPIC_BASE_URL || "https://api.anthropic.com",
    priority: 1,
    tier: "HIGH",
    enabled: true,
    models: [
      "claude-3-5-sonnet",
      "claude-3-haiku",
      "claude-3-opus",
      "claude-2",
    ],
  },
  openai: {
    name: "openai",
    apiKey: process.env.OPENAI_API_KEY || "",
    baseUrl: process.env.OPENAI_BASE_URL || "https://api.openai.com",
    priority: 2,
    tier: "HIGH",
    enabled: true,
    models: [
      "gpt-4o",
      "gpt-4-turbo",
      "gpt-4",
      "gpt-3.5-turbo",
    ],
  },
  google: {
    name: "google",
    apiKey: process.env.GOOGLE_API_KEY || "",
    baseUrl: process.env.GOOGLE_BASE_URL || "https://generativelanguage.googleapis.com",
    priority: 3,
    tier: "HIGH",
    enabled: true,
    models: [
      "gemini-1.5-pro",
      "gemini-1.5-flash",
      "gemini-1.0-pro",
    ],
  },
  mistral: {
    name: "mistral",
    apiKey: process.env.MISTRAL_API_KEY || "",
    baseUrl: process.env.MISTRAL_BASE_URL || "https://api.mistral.ai",
    priority: 4,
    tier: "HIGH",
    enabled: true,
    models: [
      "mistral-large",
      "mistral-small",
      "mistral-tiny",
    ],
  },
  xai: {
    name: "xai",
    apiKey: process.env.XAI_API_KEY || "",
    baseUrl: process.env.XAI_BASE_URL || "https://api.x.ai",
    priority: 5,
    tier: "MID",
    enabled: true,
    models: [
      "grok-2",
      "grok-1",
    ],
  },
  deepseek: {
    name: "deepseek",
    apiKey: process.env.DEEPSEEK_API_KEY || "",
    baseUrl: process.env.DEEPSEEK_BASE_URL || "https://api.deepseek.com",
    priority: 6,
    tier: "MID",
    enabled: true,
    models: [
      "deepseek-chat",
      "deepseek-coder",
    ],
  },
  minimax: {
    name: "minimax",
    apiKey: process.env.MINIMAX_API_KEY || "",
    baseUrl: process.env.MINIMAX_BASE_URL || "https://api.minimax.china",
    priority: 7,
    tier: "MID",
    enabled: true,
    models: [
      "glm-4",
      "glm-3-turbo",
    ],
  },
  nvidia: {
    name: "nvidia",
    apiKey: process.env.NVIDIA_API_KEY || "",
    baseUrl: process.env.NVIDIA_BASE_URL || "https://integrate.api.nvidia.com",
    priority: 8,
    tier: "MID",
    enabled: true,
    models: [
      "llama-3.1-405b",
      "llama-3.1-70b",
      "llama-3.1-8b",
    ],
  },
  openrouter: {
    name: "openrouter",
    apiKey: process.env.OPENROUTER_API_KEY || "",
    baseUrl: process.env.OPENROUTER_BASE_URL || "https://openrouter.ai/api",
    priority: 9,
    tier: "MID",
    enabled: true,
    models: [], // OpenRouter supports all models via routing
  },
  ollama: {
    name: "ollama",
    apiKey: "", // Ollama doesn't use API keys
    baseUrl: process.env.OLLAMA_BASE_URL || "http://localhost:11434",
    priority: 10,
    tier: "LOW",
    enabled: true,
    models: [
      "llama3.1",
      "mistral",
      "phi3",
    ],
  },
  local: {
    name: "local",
    apiKey: "",
    baseUrl: "http://localhost:8000",
    priority: 11,
    tier: "LOW",
    enabled: true,
    models: [
      "local-model",
    ],
  },
}

// =============================================================================
// MODEL TIER MAPPINGS
// =============================================================================

/** Map tier to specific model names for each provider */
export const MODEL_BY_TIER: Record<ProviderName, Record<ModelTier, string[]>> = {
  anthropic: {
    HIGH: ["claude-3-5-sonnet", "claude-3-opus", "claude-2"],
    MID: ["claude-3-haiku", "claude-2:1"],
    LOW: ["claude-instant-1"],
  },
  openai: {
    HIGH: ["gpt-4o", "gpt-4-turbo", "gpt-4"],
    MID: ["gpt-3.5-turbo-16k", "gpt-3.5-turbo"],
    LOW: ["gpt-3.5-turbo-instruct"],
  },
  google: {
    HIGH: ["gemini-1.5-pro", "gemini-1.5-flash"],
    MID: ["gemini-1.0-pro"],
    LOW: ["gemini-1.0-pro-001"],
  },
  mistral: {
    HIGH: ["mistral-large"],
    MID: ["mistral-small"],
    LOW: ["mistral-tiny"],
  },
  xai: {
    HIGH: ["grok-2"],
    MID: ["grok-1"],
    LOW: ["grok-1-mini"],
  },
  deepseek: {
    HIGH: ["deepseek-chat"],
    MID: ["deepseek-coder"],
    LOW: ["deepseek-chat-fast"],
  },
  minimax: {
    HIGH: ["glm-4"],
    MID: ["glm-3-turbo"],
    LOW: ["glm-3"],
  },
  nvidia: {
    HIGH: ["llama-3.1-405b", "llama-3.1-70b"],
    MID: ["llama-3.1-8b"],
    LOW: ["llama-3.1-70b-instruct"],
  },
  openrouter: {
    HIGH: ["anthropic/claude-3-5-sonnet", "openai/gpt-4o"],
    MID: ["anthropic/claude-3-haiku", "openai/gpt-3.5-turbo"],
    LOW: ["mistral/mistral-tiny"],
  },
  ollama: {
    HIGH: ["llama3.1:70b", "llama3.1:405b"],
    MID: ["llama3.1:8b", "mistral:latest"],
    LOW: ["phi3:3.8b", "llama3.1:3b"],
  },
  local: {
    HIGH: ["local-model"],
    MID: ["local-model"],
    LOW: ["local-model"],
  },
}

// =============================================================================
// PROVIDER MANAGER
// =============================================================================

/** Manages provider configurations and fallback chains */
export class ProviderManager {
  private providers: Map<ProviderName, ProviderConfig>
  private fallbackChains: Map<ModelTier, ModelFallbackChain[]>
  private healthStatus: Map<ProviderName, boolean>

  constructor() {
    this.providers = new Map()
    this.fallbackChains = new Map()
    this.healthStatus = new Map()

    // Initialize with default providers
    for (const [name, config] of Object.entries(PROVIDER_DEFAULTS)) {
      this.providers.set(name as ProviderName, config)
      this.healthStatus.set(name as ProviderName, true)
    }

    // Initialize fallback chains
    this.initializeFallbackChains()
  }

  /** Initialize fallback chains for each tier */
  private initializeFallbackChains(): void {
    // For each tier, create a priority-ordered list of providers
    for (const tier of ["HIGH", "MID", "LOW"] as ModelTier[]) {
      const chain: ModelFallbackChain[] = []

      // Get all providers that support this tier
      const tierProviders = Array.from(this.providers.entries())
        .filter(([_, config]) => config.tier === tier && config.enabled)
        .sort((a, b) => a[1].priority - b[1].priority)

      // Create primary + fallback structure
      for (let i = 0; i < tierProviders.length; i++) {
        const primary = tierProviders[i][0]
        const fallbacks = tierProviders
          .slice(i + 1)
          .map(([name]) => name)

        chain.push({
          primary,
          fallbacks,
          tier,
        })
      }

      this.fallbackChains.set(tier, chain)
    }
  }

  /**
   * Get the best model for a given tier based on availability
   */
  getModelForTier(
    tier: ModelTier,
    agentType: keyof ModelProfile
  ): { model: string; provider: ProviderName } | null {
    // Get the model profile for the agent type
    const profile = MODEL_PROFILES["eco"] // Default to eco
    const agentTier = profile[agentType]

    // Use the requested tier or the agent's configured tier
    const effectiveTier = tier

    // Get available providers for this tier
    const providersForTier = Array.from(this.providers.entries())
      .filter(
        ([_, config]) =>
          config.enabled &&
          config.tier === effectiveTier &&
          this.healthStatus.get(config.name) === true
      )
      .sort((a, b) => a[1].priority - b[1].priority)

    if (providersForTier.length === 0) {
      return null
    }

    // Get the first healthy provider
    const [providerName, providerConfig] = providersForTier[0]

    // Get models for this provider and tier
    const models = MODEL_BY_TIER[providerName]?.[effectiveTier] || []

    if (models.length === 0) {
      return null
    }

    return {
      model: models[0],
      provider: providerName,
    }
  }

  /**
   * Get the complete fallback chain for a tier
   */
  getFallbackChain(tier: ModelTier): ModelFallbackChain[] {
    return this.fallbackChains.get(tier) || []
  }

  /**
   * Get all providers sorted by priority
   */
  getProviders(): ProviderConfig[] {
    return Array.from(this.providers.values())
      .filter(c => c.enabled)
      .sort((a, b) => a.priority - b.priority)
  }

  /**
   * Get provider by name
   */
  getProvider(name: ProviderName): ProviderConfig | undefined {
    return this.providers.get(name)
  }

  /**
   * Update provider health status
   */
  updateHealthStatus(name: ProviderName, healthy: boolean): void {
    this.healthStatus.set(name, healthy)
    // Rebuild fallback chains when health changes
    this.initializeFallbackChains()
  }

  /**
   * Check if provider is healthy
   */
  isHealthy(name: ProviderName): boolean {
    return this.healthStatus.get(name) ?? false
  }

  /**
   * Add a custom provider
   */
  addProvider(config: ProviderConfig): void {
    this.providers.set(config.name, config)
    this.healthStatus.set(config.name, true)
    this.initializeFallbackChains()
  }

  /**
   * Remove a provider
   */
  removeProvider(name: ProviderName): void {
    this.providers.delete(name)
    this.healthStatus.delete(name)
    this.initializeFallbackChains()
  }

  /**
   * Enable/disable a provider
   */
  setProviderEnabled(name: ProviderName, enabled: boolean): void {
    const config = this.providers.get(name)
    if (config) {
      config.enabled = enabled
      this.providers.set(name, config)
      this.initializeFallbackChains()
    }
  }

  /**
   * Get credentials-aware model selection
   * Returns models that we actually have API keys for
   */
  getAvailableModels(): Map<ProviderName, string[]> {
    const available = new Map<ProviderName, string[]>()

    for (const [name, config] of this.providers) {
      if (!config.enabled) continue
      if (!config.apiKey && name !== "ollama" && name !== "local") continue
      if (!this.healthStatus.get(name)) continue

      const models = MODEL_BY_TIER[name]?.[config.tier] || []
      if (models.length > 0) {
        available.set(name, models)
      }
    }

    return available
  }

  /**
   * Build a tier-based model profile from available providers
   */
  buildModelProfile(): ModelProfile {
    const profile: Partial<ModelProfile> = {}

    for (const agentType of ["orchestrator", "exploitation", "verification", "analysis", "recon"] as const) {
      const modelInfo = this.getModelForTier("HIGH", agentType)
      if (modelInfo) {
        profile[agentType] = "HIGH"
      } else {
        // Fall back to lower tiers
        const midInfo = this.getModelForTier("MID", agentType)
        if (midInfo) {
          profile[agentType] = "MID"
        } else {
          profile[agentType] = "LOW"
        }
      }
    }

    return profile as ModelProfile
  }
}

// =============================================================================
// SINGLETON INSTANCE
// =============================================================================

let providerManagerInstance: ProviderManager | null = null

export function getProviderManager(): ProviderManager {
  if (!providerManagerInstance) {
    providerManagerInstance = new ProviderManager()
  }
  return providerManagerInstance
}

export function resetProviderManager(): void {
  providerManagerInstance = null
}

// =============================================================================
// UTILITY FUNCTIONS
// =============================================================================

/**
 * Get the best available model for a given agent type and tier
 */
export function getModelForAgent(
  agentType: keyof ModelProfile,
  tier: ModelTier = "HIGH"
): { model: string; provider: ProviderName } | null {
  const manager = getProviderManager()
  return manager.getModelForTier(tier, agentType)
}

/**
 * Get all models available for a specific tier
 */
export function getModelsByTier(tier: ModelTier): string[] {
  const manager = getProviderManager()
  const chains = manager.getFallbackChain(tier)
  const models: string[] = []

  for (const chain of chains) {
    const provider = manager.getProvider(chain.primary)
    if (provider) {
      const tierModels = MODEL_BY_TIER[chain.primary]?.[tier] || []
      models.push(...tierModels)
    }
  }

  return models
}

/**
 * Check if we have any providers configured
 */
export function hasProviders(): boolean {
  const manager = getProviderManager()
  const available = manager.getAvailableModels()
  return available.size > 0
}

/**
 * Get provider configuration from environment
 */
export function loadProviderConfigFromEnv(): void {
  const manager = getProviderManager()

  // Check each provider for API key
  for (const name of Object.keys(PROVIDER_DEFAULTS) as ProviderName[]) {
    const config = manager.getProvider(name)
    if (config) {
      const envVar = `${name.toUpperCase()}_API_KEY` as keyof typeof process.env
      if (process.env[envVar]) {
        config.apiKey = process.env[envVar]!
        manager.addProvider(config)
      }
    }
  }
}

// =============================================================================
// MODEL ROUTER
// =============================================================================

/**
 * ModelRouter handles routing requests to the appropriate provider/model
 * based on tier, agent type, and availability
 */
export class ModelRouter {
  private manager: ProviderManager

  constructor(manager?: ProviderManager) {
    this.manager = manager || getProviderManager()
  }

  /**
   * Route a request to the best available model
   */
  route(
    agentType: keyof ModelProfile,
    tier: ModelTier = "HIGH"
  ): {
    model: string
    provider: ProviderName
    config: ProviderConfig
    isFallback: boolean
  } | null {
    const modelInfo = this.manager.getModelForTier(tier, agentType)

    if (!modelInfo) {
      return null
    }

    const config = this.manager.getProvider(modelInfo.provider)

    if (!config) {
      return null
    }

    return {
      model: modelInfo.model,
      provider: modelInfo.provider,
      config,
      isFallback: false,
    }
  }

  /**
   * Get all fallback options for a given route
   */
  getFallbacks(
    agentType: keyof ModelProfile,
    tier: ModelTier = "HIGH"
  ): Array<{
    model: string
    provider: ProviderName
    config: ProviderConfig
  }> {
    const chains = this.manager.getFallbackChain(tier)
    const results: Array<{
      model: string
      provider: ProviderName
      config: ProviderConfig
    }> = []

    for (const chain of chains) {
      const config = this.manager.getProvider(chain.primary)
      if (config) {
        const models = MODEL_BY_TIER[chain.primary]?.[tier] || []
        if (models.length > 0) {
          results.push({
            model: models[0],
            provider: chain.primary,
            config,
          })
        }
      }
    }

    return results
  }
}

// =============================================================================
// EXPORTS
// =============================================================================

export {
  PROVIDER_DEFAULTS,
  MODEL_BY_TIER,
  MODEL_PROFILES,
}
