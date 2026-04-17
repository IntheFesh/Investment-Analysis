import {
  createContext,
  ReactNode,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from 'react';
import { useRouter } from 'next/router';
import { useQuery } from '@tanstack/react-query';
import { systemService, type BootstrapData } from '@/services/systemService';
import { queryKeys } from '@/lib/queryKeys';

export type ResearchMode = 'research' | 'light';
export type ThemeMode = 'dark' | 'light' | 'system';
export type ResolvedTheme = 'dark' | 'light';

export interface AppSelectionState {
  marketView: string;
  timeWindow: string;
  portfolioId: string;
  researchMode: ResearchMode;
  theme: ThemeMode;
}

interface AppContextValue extends AppSelectionState {
  resolvedTheme: ResolvedTheme;
  setMarketView: (value: string) => void;
  setTimeWindow: (value: string) => void;
  setPortfolioId: (value: string) => void;
  setResearchMode: (value: ResearchMode) => void;
  setTheme: (value: ThemeMode) => void;
  bootstrapData?: BootstrapData;
  bootstrapLoading: boolean;
  bootstrapError: unknown;
  isHydrated: boolean;
}

const AppContext = createContext<AppContextValue | null>(null);

const STORAGE_KEY = 'investment-analysis-selection-v2';

const DEFAULTS: AppSelectionState = {
  marketView: 'cn_a',
  timeWindow: '20D',
  portfolioId: 'pf_default',
  researchMode: 'research',
  theme: 'dark',
};

const URL_SYNC_KEYS: Array<keyof AppSelectionState> = [
  'marketView',
  'timeWindow',
  'portfolioId',
  'researchMode',
];

const URL_PARAM_MAP: Record<keyof AppSelectionState, string> = {
  marketView: 'market',
  timeWindow: 'tw',
  portfolioId: 'pf',
  researchMode: 'mode',
  theme: '__theme_unused',
};

const readLocalSelection = (): Partial<AppSelectionState> => {
  if (typeof window === 'undefined') return {};
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return {};
    return JSON.parse(raw) as Partial<AppSelectionState>;
  } catch {
    return {};
  }
};

const systemPrefersDark = (): boolean => {
  if (typeof window === 'undefined' || !window.matchMedia) return true;
  return window.matchMedia('(prefers-color-scheme: dark)').matches;
};

const resolveTheme = (mode: ThemeMode): ResolvedTheme =>
  mode === 'system' ? (systemPrefersDark() ? 'dark' : 'light') : mode;

export function AppContextProvider({ children }: { children: ReactNode }) {
  const router = useRouter();

  const [state, setState] = useState<AppSelectionState>(DEFAULTS);
  const [isHydrated, setIsHydrated] = useState(false);
  const [resolvedTheme, setResolvedTheme] = useState<ResolvedTheme>('dark');

  const bootstrapQuery = useQuery(queryKeys.system.bootstrap(), systemService.getBootstrap, {
    staleTime: 30 * 60 * 1000,
    retry: 1,
    refetchOnWindowFocus: false,
  });

  // Initial hydration from localStorage + URL.
  useEffect(() => {
    const stored = readLocalSelection();
    const queryParams = typeof window !== 'undefined' ? new URLSearchParams(window.location.search) : null;

    const next = { ...DEFAULTS, ...stored };

    if (queryParams) {
      const m = queryParams.get('market');
      const tw = queryParams.get('tw');
      const pf = queryParams.get('pf');
      const mode = queryParams.get('mode');
      if (m) next.marketView = m;
      if (tw) next.timeWindow = tw;
      if (pf) next.portfolioId = pf;
      if (mode === 'research' || mode === 'light') next.researchMode = mode;
    }

    setState(next);
    setIsHydrated(true);
  }, []);

  // Apply bootstrap defaults on top of hydrated state — only fills blanks.
  useEffect(() => {
    const data = bootstrapQuery.data;
    if (!data || !isHydrated) return;
    setState((current) => {
      const markets = data.markets.map((m) => m.id);
      const portfolios = data.portfolios.map((p) => p.id);
      const windows = data.time_windows;
      const defaults = data.default_settings;
      return {
        marketView: markets.includes(current.marketView) ? current.marketView : defaults.market_view,
        timeWindow: windows.includes(current.timeWindow) ? current.timeWindow : defaults.time_window,
        portfolioId: portfolios.includes(current.portfolioId)
          ? current.portfolioId
          : (portfolios[0] ?? defaults.market_view),
        researchMode:
          current.researchMode === 'research' || current.researchMode === 'light'
            ? current.researchMode
            : (defaults.research_mode as ResearchMode),
        theme: current.theme,
      };
    });
  }, [bootstrapQuery.data, isHydrated]);

  // Persist to localStorage.
  useEffect(() => {
    if (!isHydrated || typeof window === 'undefined') return;
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
  }, [state, isHydrated]);

  // Keep URL in sync for core filters so reloads / shares preserve state.
  useEffect(() => {
    if (!isHydrated || !router.isReady) return;
    const params = new URLSearchParams(
      Array.from(Object.entries(router.query)).flatMap(([k, v]) =>
        v === undefined ? [] : [[k, Array.isArray(v) ? v[0] : String(v)]]
      ) as Array<[string, string]>
    );
    let changed = false;
    for (const key of URL_SYNC_KEYS) {
      const urlKey = URL_PARAM_MAP[key];
      const current = params.get(urlKey);
      const next = String(state[key]);
      if (current !== next) {
        params.set(urlKey, next);
        changed = true;
      }
    }
    if (changed) {
      const newUrl = `${router.pathname}?${params.toString()}`;
      router.replace(newUrl, undefined, { shallow: true, scroll: false });
    }
  }, [state.marketView, state.timeWindow, state.portfolioId, state.researchMode, isHydrated, router.isReady]); // eslint-disable-line react-hooks/exhaustive-deps

  // Theme resolution + DOM class + data-density attribute.
  useEffect(() => {
    if (typeof document === 'undefined') return;
    const resolved = resolveTheme(state.theme);
    setResolvedTheme(resolved);
    document.documentElement.classList.toggle('dark', resolved === 'dark');
    document.documentElement.classList.toggle('light', resolved === 'light');
    document.documentElement.dataset.density = state.researchMode === 'research' ? 'research' : 'light';
  }, [state.theme, state.researchMode]);

  // Listen to system colour-scheme changes when user picks `system`.
  useEffect(() => {
    if (state.theme !== 'system' || typeof window === 'undefined' || !window.matchMedia) return;
    const media = window.matchMedia('(prefers-color-scheme: dark)');
    const handler = () => {
      const resolved = media.matches ? 'dark' : 'light';
      setResolvedTheme(resolved);
      document.documentElement.classList.toggle('dark', resolved === 'dark');
      document.documentElement.classList.toggle('light', resolved === 'light');
    };
    media.addEventListener?.('change', handler);
    return () => media.removeEventListener?.('change', handler);
  }, [state.theme]);

  const setField = useCallback(
    <K extends keyof AppSelectionState>(key: K) =>
      (value: AppSelectionState[K]) =>
        setState((prev) => (prev[key] === value ? prev : { ...prev, [key]: value })),
    []
  );

  const value = useMemo<AppContextValue>(
    () => ({
      ...state,
      resolvedTheme,
      setMarketView: setField('marketView'),
      setTimeWindow: setField('timeWindow'),
      setPortfolioId: setField('portfolioId'),
      setResearchMode: setField('researchMode'),
      setTheme: setField('theme'),
      bootstrapData: bootstrapQuery.data,
      bootstrapLoading: bootstrapQuery.isLoading,
      bootstrapError: bootstrapQuery.error,
      isHydrated,
    }),
    [state, resolvedTheme, setField, bootstrapQuery.data, bootstrapQuery.isLoading, bootstrapQuery.error, isHydrated]
  );

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
}

export const useAppContext = (): AppContextValue => {
  const ctx = useContext(AppContext);
  if (!ctx) {
    throw new Error('useAppContext must be used inside AppContextProvider');
  }
  return ctx;
};
