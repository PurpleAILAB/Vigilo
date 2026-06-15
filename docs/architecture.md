# Vigilo Architecture - Decepticon-Level Optimization

## Overview

Vigilo implements a Decepticon-level security verification pipeline with optimized architecture for maximum detection accuracy, false positive neutralization, and performance efficiency.

## Core Architecture

### Two-Network Design (Management + Sandbox Plane)

Vigilo employs a dual-network architecture matching Decepticon's security isolation model:

```
┌─────────────────────────────────────────────────────────────────────┐
│                         MANAGEMENT PLANE                                │
│                    (decepticon-net: 172.20.0.0/16)                      │
├─────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐   │
│  │  Vigilo Core    │    │  Neo4j Graph DB  │    │  Redis Cache    │   │
│  │  - Orchestrator  │    │  - Attack Chains │    │  - Session State │   │
│  │  - Validators    │    │  - Knowledge Graph│    │  - Rate Limiting │   │
│  │  - Purifier      │    │  - Evidence Map  │    │                 │   │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘   │
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    Provider Manager                            │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │   │
│  │  │ Anthropic│ │  OpenAI  │ │  Google  │ │  Mistral │       │   │
│  │  │  - 3.5   │ │  - GPT-4o│ │ - Gem1.5 │ │ - Large  │       │   │
│  │  │  - Haiku │ │  - Turbo │ │ - Flash  │ │ - Medium │       │   │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘       │   │
│  └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         SANDBOX PLANE                                   │
│                    (sandbox-net: 172.21.0.0/16)                        │
├─────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐   │
│  │  Sandbox Mgr    │    │  Execution Env   │    │  File System    │   │
│  │  - tmux sessions│    │  - Containerized │    │  - Isolated      │   │
│  │  - Lifecycle    │    │  - Resource Ltd  │    │  - Encrypted     │   │
│  │  - Cleanup      │    │  - Network Isolated│   │                 │   │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘   │
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    Code Analysis Sandbox                        │   │
│  │  - Static Analysis (Slither, MythX)                          │   │
│  │  - Dynamic Analysis (Custom Symbolic Execution)             │   │
│  │  - Fuzzing (Echidna, Foundry)                                   │   │
│  │  - POC Generation & Validation                                │   │
│  └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

### Network Isolation

- **decepticon-net (172.20.0.0/16)**: Management plane with core services
  - Vigilo orchestration
  - Neo4j knowledge graph
  - Redis caching
  - Provider API gateways

- **sandbox-net (172.21.0.0/16)**: Isolated execution environment
  - Smart contract analysis
  - POC execution
  - Fuzzing campaigns
  - External tool integration

## Component Architecture

### 1. Agent Layer

```
┌─────────────────────────────────────────────────────────────────┐
│                        AGENTS                                       │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐                │
│  │   Vigilo     │ │  Speculator  │ │  Validator   │                │
│  │  (Main)      │ │  (Static)     │ │  (Dynamic)   │                │
│  └──────────────┘ └──────────────┘ └──────────────┘                │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐                │
│  │   Explorer   │ │   Quaestor    │ │  Triager     │                │
│  │  (Discovery) │ │  (Query)      │ │  (Prioritize)│                │
│  └──────────────┘ └──────────────┘ └──────────────┘                │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐                │
│  │   Purifier   │ │  GraphBuilder │ │  SandboxMgr   │                │
│  │ (False +)    │ │  (KG)         │ │  (Isolation) │                │
│  └──────────────┘ └──────────────┘ └──────────────┘                │
└─────────────────────────────────────────────────────────────────┘
```

### 2. Evidence Hierarchy (8 Tiers)

```
┌─────────────────────────────────────────────────────────────────┐
│                    EVIDENCE HIERARCHY                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                     │
│  LEVEL 1: POC_VALIDATED        ★★★★★  Confidence: 100%             │
│  ├── Live exploit executed on testnet/mainnet                     │
│  ├── Actual funds at risk demonstrated                            │
│  └── Verified by security researcher                              │
│                                                                     │
│  LEVEL 2: STATIC_CONFIRMED      ★★★★☆  Confidence: 95%              │
│  ├── Multiple static analyzers agree                             │
│  ├── Manual code review confirmed                                 │
│  └── Clear vulnerable code pattern matched                        │
│                                                                     │
│  LEVEL 3: TRACE_CONFIRMED       ★★★☆☆  Confidence: 90%              │
│  ├── Symbolic execution confirms exploit path                     │
│  ├── Fuzzing found concrete input to trigger issue                │
│  └── Control flow analysis validated                             │
│                                                                     │
│  LEVEL 4: SYMBOLIC_CONFIRMED    ★★☆☆☆  Confidence: 85%              │
│  ├── Symbolic execution shows potential vulnerability              │
│  └── Path constraints satisfied                                   │
│                                                                     │
│  LEVEL 5: HEURISTIC_CONFIRMED   ★☆☆☆☆  Confidence: 80%              │
│  ├── Pattern matching with high confidence                        │
│  ├── Heuristic analysis detected anomaly                         │
│  └── Statistical analysis flagged as suspicious                   │
│                                                                     │
│  LEVEL 6: STATIC_SUGGESTED      ★★★☆☆  Confidence: 70%              │
│  ├── Single static analyzer flagged                               │
│  └── Requires manual verification                                 │
│                                                                     │
│  LEVEL 7: HEURISTIC_SUGGESTED    ★☆☆☆☆  Confidence: 50%              │
│  ├── Pattern matching with low confidence                          │
│  └── May be false positive                                        │
│                                                                     │
│  LEVEL 8: THEORETICAL            ☆☆☆☆☆  Confidence: 20%              │
│  ├── Theoretical possibility only                                 │
│  ├── No concrete evidence                                         │
│  └── Speculative finding                                          │
│                                                                     │
└─────────────────────────────────────────────────────────────────┘
```

### 3. Confidence Scoring System

Multi-dimensional confidence scoring with decay factors:

```
Confidence Score = 
  BaseScore 
  × TimeDecayFactor      (0.95^hours_since_detection)
  × ContextDecayFactor   (0.98^(context_tokens/1000))
  × ModelTierFactor      (HIGH: 1.0, MID: 0.9, LOW: 0.7)
  × EvidenceFactor        (POC: 1.0, STATIC: 0.95, TRACE: 0.9, ...)
  × VerificationFactor    (Verified: 1.1, Unverified: 0.9)
```

**Model Tier System:**
- **HIGH**: Claude 3.5 Sonnet, GPT-4o, Gemini 1.5 Pro
- **MID**: Claude 3 Haiku, GPT-4 Turbo, Mistral Large
- **LOW**: Llama 3.2, Grok-2, Local models

### 4. Knowledge Graph Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    NEO4J KNOWLEDGE GRAPH                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐    │
│  │   Contract    │────▶│   Function   │────▶│  Vulnerability│    │
│  │   Node        │     │    Node      │     │     Node     │    │
│  └──────────────┘     └──────────────┘     └──────────────┘    │
│          │                   │                   │                │
│          ▼                   ▼                   ▼                │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐    │
│  │  Properties:  │     │  Properties:  │     │  Properties:  │    │
│  │  - address    │     │  - name      │     │  - type      │    │
│  │  - bytecode   │     │  - selector   │     │  - severity  │    │
│  │  - verified   │     │  - modifier   │     │  - evidence  │    │
│  │  - version    │     │  - visibility │     │  - confidence│    │
│  └──────────────┘     └──────────────┘     └──────────────┘    │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                    ATTACK CHAINS                            │    │
│  │                                                             │    │
│  │  (ContractA)─[exploit]─▶(VulnerabilityX)─[leads_to]─▶        │    │
│  │                    │                                         │    │
│  │                    ▼                                         │    │
│  │  (FunctionY)──[calls]─▶(FunctionZ)──[vulnerable]─▶          │    │
│  │                    │                                         │    │
│  │                    ▼                                         │    │
│  │  (Attacker)─[can_exploit]─▶(Impact: Theft/DoS/Manipulation)   │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                     │
└─────────────────────────────────────────────────────────────────┘
```

### 5. Provider Abstraction Layer

```typescript
// Tier-based model fallback with 11 providers

interface ProviderConfig {
  name: ProviderName;
  tier: ModelTier; // HIGH | MID | LOW
  models: ModelProfile[];
  apiKey: string;
  baseURL?: string;
  timeout: number;
  rateLimit: number;
}

// Fallback chain: HIGH → MID → LOW
const FALLBACK_CHAIN: ProviderName[] = [
  "anthropic",      // HIGH
  "openai",         // HIGH
  "google",         // HIGH
  "mistral",        // MID
  "xai",            // MID
  "local",          // LOW
];

// Model profiles with capabilities
const MODEL_PROFILES: Record<ModelName, ModelProfile> = {
  "anthropic/claude-3-5-sonnet": { tier: "HIGH", maxTokens: 64000, reasoning: true },
  "anthropic/claude-3-haiku":    { tier: "HIGH", maxTokens: 64000, reasoning: false },
  "openai/gpt-4o":                { tier: "HIGH", maxTokens: 128000, reasoning: true },
  "openai/gpt-4-turbo":          { tier: "HIGH", maxTokens: 128000, reasoning: false },
  "google/gemini-1.5-pro":       { tier: "HIGH", maxTokens: 1048576, reasoning: true },
  "google/gemini-1.5-flash":     { tier: "HIGH", maxTokens: 1048576, reasoning: false },
  "mistral/mistral-large":       { tier: "MID", maxTokens: 131072, reasoning: true },
  "mistral/mistral-medium":      { tier: "MID", maxTokens: 131072, reasoning: false },
  "xai/grok-2":                  { tier: "MID", maxTokens: 131072, reasoning: true },
  "xai/grok-1":                  { tier: "MID", maxTokens: 65536, reasoning: false },
  "local/llama-3.2-11b":         { tier: "LOW", maxTokens: 32768, reasoning: false },
};
```

### 6. False Positive Neutralization (13 Patterns)

```
┌─────────────────────────────────────────────────────────────────┐
│              FALSE POSITIVE NEUTRALIZATION PATTERNS                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                     │
│  CATEGORY 1: Library Code (Safe Patterns)                         │
│  ├─ OpenZeppelin contracts (ERC20, ERC721, Ownable, etc.)         │
│  ├─ Solady libraries (SafeTransferLib, ERC4626, etc.)             │
│  └─ Solmate implementations (ERC721, SafeTransfer, etc.)           │
│                                                                     │
│  CATEGORY 2: Intentional Design Patterns                         │
│  ├─ Admin functions (onlyOwner, onlyAdmin)                        │
│  ├─ Pause mechanisms (whenNotPaused, paused)                       │
│  └─ Upgradeable patterns (proxy, implementation, upgradeTo)      │
│                                                                     │
│  CATEGORY 3: Testing Artifacts                                     │
│  ├─ Hardhat cheat codes (vm.prank, vm.deal, vm.warp)               │
│  ├─ Foundry cheat codes (stdCheats, prank, deal)                  │
│  └─ Test contracts (describe, it, beforeEach)                      │
│                                                                     │
│  CATEGORY 4: Compiler Warnings                                    │
│  ├─ SafeMath deprecation warnings                                │
│  ├─ Unused variables                                             │
│  └─ Missing NatSpec comments                                     │
│                                                                     │
│  CATEGORY 5: Gas Optimization                                     │
│  ├─ Unchecked arithmetic (intentional)                           │
│  ├─ Assembly blocks                                              │
│  └─ Storage packing optimizations                                │
│                                                                     │
│  CATEGORY 6: Style/Quality                                        │
│  ├─ Code formatting issues                                       │
│  ├─ Missing event emits                                          │
│  └─ Non-standard naming conventions                              │
│                                                                     │
└─────────────────────────────────────────────────────────────────┘
```

## Data Flow

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│  Input   │────▶│  Parser  │────▶│ Explorer │────▶│  Specu- │
│ Contract │     │          │     │          │     │  lator   │
└──────────┘     └──────────┘     └──────────┘     └──────────┘
                                                     │
                                                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                         ANALYSIS PHASE                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────────────┐    │
│  │Static Analysis│   │Dynamic Analysis│   │Symbolic Execution    │    │
│  │- Slither     │   │- POC Gen     │   │- Custom Engine       │    │
│  │- MythX       │   │- Validation   │   │- Path Exploration    │    │
│  │- Semgrep     │   └─────────────┘   └─────────────────────┘    │
│  └─────────────┘                                                     │
│        │                                                               │
│        ▼                                                               │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │                    FINDINGS AGGREGATION                        │  │
│  │                                                             │  │
│  │  [Finding1]────[Finding2]────[FindingN]                       │  │
│  │       │            │             │                            │  │
│  │       ▼            ▼             ▼                            │  │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐       │  │
│  │  │  Deduplicate │ │   Cluster    │ │   Prioritize │       │  │
│  │  │  (same issue)│ │  (related)    │ │  (by severity)│       │  │
│  │  └──────────────┘ └──────────────┘ └──────────────┘       │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                                                                     │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      VALIDATION PHASE                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────────────┐    │
│  │  Validator  │   │  Verifier   │   │   Confidence Scorer  │    │
│  │- Check POC  │   │- Verify FP   │   │- Multi-dimensional    │    │
│  │- Validate   │   │- Neutralize  │   │- Decay factors        │    │
│  │- Test POC   │   │- 13 patterns │   │- Evidence hierarchy   │    │
│  └─────────────┘   └─────────────┘   └─────────────────────┘    │
│        │                   │                   │                │
│        └───────────────────┼───────────────────┘                │
│                            ▼                                        │
│              ┌─────────────────────────────┐                       │
│              │     FINAL FINDINGS            │                       │
│              │  - Verified vulnerabilities   │                       │
│              │  - False positives filtered  │                       │
│              │  - Confidence scores assigned │                       │
│              │  - Attack chains mapped      │                       │
│              └─────────────────────────────┘                       │
│                                                                     │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      OUTPUT PHASE                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────────────┐    │
│  │  Report     │   │  Knowledge   │   │   Notifications       │    │
│  │  - Markdown │   │  Graph       │   │   - Slack/Discord     │    │
│  │  - JSON     │   │  - Neo4j     │   │   - Email            │    │
│  │  - SARIF     │   │  - Visualization│   │   - Webhooks        │    │
│  └─────────────┘   └─────────────┘   └─────────────────────┘    │
│                                                                     │
└─────────────────────────────────────────────────────────────────┘
```

## Sandbox Architecture

### Container-Based Isolation

```
┌─────────────────────────────────────────────────────────────────┐
│                    SANDBOX MANAGER                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                    TMUX SESSION MANAGEMENT                      ││
│  │                                                             ││
│  │  Session: vigilo-sandbox-{uuid}                                ││
│  │  ├─ Window 0: Code Analysis                                    ││
│  │  ├─ Window 1: POC Execution                                    ││
│  │  ├─ Window 2: Fuzzing                                          ││
│  │  └─ Window 3: Monitoring/logs                                  ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                    CONTAINER MANAGEMENT                          ││
│  │                                                             ││
│  │  Container: vigilo-analysis-{uuid}                            ││
│  │  ├─ Network: sandbox-net (isolated)                            ││
│  │  ├─ Volumes: /tmp/vigilo-sandbox (encrypted)                   ││
│  │  ├─ Limits: CPU, Memory, Disk I/O                              ││
│  │  ├─ Timeout: Configurable (default: 300s)                      ││
│  │  └─ Cleanup: Automatic on completion/failure                   ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                     │
└─────────────────────────────────────────────────────────────────┘
```

### Security Measures

1. **Network Isolation**: sandbox-net cannot access decepticon-net
2. **Filesystem Isolation**: Encrypted volumes, read-only where possible
3. **Resource Limits**: CPU, memory, disk I/O limits per container
4. **Timeout Enforcement**: Hard timeout with graceful shutdown
5. **Cleanup Guarantees**: Containers and sessions always cleaned up
6. **Audit Logging**: All sandbox operations logged

## Performance Optimization

### Caching Strategy

```
┌─────────────────────────────────────────────────────────────────┐
│                    CACHING LAYERS                                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                     │
│  LEVEL 1: In-Memory Cache (Hot Data)                              │
│  ├── Analysis results (5 minute TTL)                              │
│  ├── Confidence scores (1 hour TTL)                               │
│  └─ Finding deduplication (session lifetime)                       │
│                                                                     │
│  LEVEL 2: Redis Cache (Warm Data)                                 │
│  ├── Contract bytecode hashes (24 hour TTL)                        │
│  ├── Static analysis results (1 hour TTL)                         │
│  ├── Known vulnerability patterns (persistent)                     │
│  └─ Rate limiting state (10 minute TTL)                            │
│                                                                     │
│  LEVEL 3: Neo4j Persistent Storage (Cold Data)                     │
│  ├── Knowledge graph (persistent)                                  │
│  ├── Historical findings (persistent)                              │
│  └─ Attack chain patterns (persistent)                            │
│                                                                     │
└─────────────────────────────────────────────────────────────────┘
```

### Query Optimization

- **Batch Processing**: Multiple contracts analyzed in parallel
- **Incremental Analysis**: Only re-analyze changed code
- **Smart Caching**: Cache based on contract hash + model fingerprint
- **Lazy Loading**: Load knowledge graph data on-demand

## Scalability

### Horizontal Scaling

- **Stateless Workers**: Analysis workers can scale horizontally
- **Shared Cache**: Redis cluster for shared caching
- **Distributed Queue**: Job queue for load balancing
- **Database Sharding**: Neo4j cluster for graph data

### Vertical Scaling

- **Model Tier Fallback**: Automatically fall back to lower-tier models under load
- **Adaptive Batching**: Adjust batch size based on system resources
- **Priority Queues**: High-priority jobs processed first

## Monitoring & Observability

### Metrics

- **Analysis Metrics**: Token usage, time per analysis, findings per analysis
- **Performance Metrics**: Request latency, throughput, error rates
- **Quality Metrics**: False positive rate, false negative rate, detection rate
- **Resource Metrics**: CPU, memory, disk usage

### Logging

- **Structured Logs**: JSON-formatted logs with correlation IDs
- **Trace Context**: Distributed tracing across microservices
- **Audit Trail**: All security-relevant operations logged

### Alerting

- **Anomaly Detection**: Automatic alerts for unusual patterns
- **Threshold Alerts**: Alerts when metrics exceed thresholds
- **SLA Monitoring**: Track against Decepticon-level SLAs

## Comparison with Decepticon

| Feature | Decepticon | Vigilo | Notes |
|---------|-----------|--------|-------|
| Two-Network Architecture | ✅ | ✅ | Same design |
| Evidence Hierarchy | 8 tiers | 8 tiers | Matching levels |
| Confidence Scoring | Multi-dimensional | Multi-dimensional | With decay factors |
| Knowledge Graph | Neo4j | Neo4j | Same technology |
| Model Fallback | Tier-based | Tier-based | 11 providers |
| False Positive Filtering | Pattern-based | Pattern-based | 13 patterns |
| Sandbox Isolation | Container-based | Container-based | tmux + Docker |
| Performance Targets | Defined | Matching | Same SLAs |
| XBOW Benchmark | 102/104 | Target: 102/104 | 98.08% |

## Future Enhancements

1. **Federated Learning**: Share knowledge across installations
2. **Continuous Benchmarking**: Automated XBOW runs on every commit
3. **Adversarial Training**: Use false negatives to improve models
4. **Explainable AI**: Better explanations for findings
5. **Automated POC Generation**: Generate exploits for all findings
6. **Multi-language Support**: Expand beyond Solidity
