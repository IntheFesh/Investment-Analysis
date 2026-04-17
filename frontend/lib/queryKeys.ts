/**
 * Centralised React Query keys. Each key embeds every filter dimension that
 * influences the request so filter changes invalidate the correct slice
 * without polluting unrelated caches.
 */

export const queryKeys = {
  system: {
    bootstrap: () => ['system', 'bootstrap'] as const,
    health: () => ['system', 'health'] as const,
  },
  market: {
    overview: (marketView: string, timeWindow: string) =>
      ['market', 'overview', marketView, timeWindow] as const,
    indices: (marketView: string, timeWindow: string) =>
      ['market', 'indices', marketView, timeWindow] as const,
    sectorRotation: (marketView: string, timeWindow: string) =>
      ['market', 'sector-rotation', marketView, timeWindow] as const,
    fundFlows: (marketView: string, timeWindow: string) =>
      ['market', 'fund-flows', marketView, timeWindow] as const,
    breadth: (marketView: string, timeWindow: string) =>
      ['market', 'breadth', marketView, timeWindow] as const,
    explanations: (marketView: string, timeWindow: string) =>
      ['market', 'explanations', marketView, timeWindow] as const,
    crossAsset: (marketView: string, timeWindow: string) =>
      ['market', 'cross-asset', marketView, timeWindow] as const,
  },
  sentiment: {
    overview: (marketView: string, timeWindow: string) =>
      ['sentiment', 'overview', marketView, timeWindow] as const,
    snapshotLight: (marketView: string) =>
      ['sentiment', 'snapshot-light', marketView] as const,
  },
  portfolio: {
    overview: (portfolioId: string) => ['portfolio', 'overview', portfolioId] as const,
    diagnosis: (portfolioId: string, marketView: string) =>
      ['portfolio', 'diagnosis', portfolioId, marketView] as const,
    exportPack: (portfolioId: string, marketView: string) =>
      ['portfolio', 'export-pack', portfolioId, marketView] as const,
  },
  fund: {
    list: () => ['fund', 'list'] as const,
    overview: (code: string, timeWindow: string) =>
      ['fund', 'overview', code, timeWindow] as const,
    analysis: (code: string, portfolioId: string, timeWindow: string) =>
      ['fund', 'analysis', code, portfolioId, timeWindow] as const,
  },
  simulation: {
    presets: () => ['simulation', 'presets'] as const,
    historicalEvents: () => ['simulation', 'historical-events'] as const,
  },
  backtest: {
    defaults: () => ['backtest', 'defaults'] as const,
  },
  scheduler: {
    status: () => ['scheduler', 'status'] as const,
  },
  task: {
    detail: (taskId: string | undefined) => ['task', taskId] as const,
    list: (kind?: string) => ['task', 'list', kind ?? 'all'] as const,
  },
  settings: {
    profile: () => ['settings', 'profile'] as const,
    preferences: () => ['settings', 'preferences'] as const,
    enums: () => ['settings', 'enums'] as const,
  },
  exports: {
    history: () => ['exports', 'history'] as const,
  },
};
