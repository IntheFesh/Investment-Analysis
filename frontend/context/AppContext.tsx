import { createContext, ReactNode, useContext, useEffect, useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { systemService } from '@/services/systemService';

interface AppSelectionState {
  marketView: string;
  timeWindow: string;
  portfolioId: string;
}

interface AppContextValue extends AppSelectionState {
  setMarketView: (value: string) => void;
  setTimeWindow: (value: string) => void;
  setPortfolioId: (value: string) => void;
  bootstrapData?: Awaited<ReturnType<typeof systemService.getBootstrap>>;
  bootstrapLoading: boolean;
  bootstrapError: unknown;
}

const AppContext = createContext<AppContextValue | null>(null);

const STORAGE_KEY = 'investment-analysis-selection';

export function AppContextProvider({ children }: { children: ReactNode }) {
  const [marketView, setMarketView] = useState('A股主视角');
  const [timeWindow, setTimeWindow] = useState('20D');
  const [portfolioId, setPortfolioId] = useState('pf_default');

  const bootstrapQuery = useQuery(['system-bootstrap'], systemService.getBootstrap, {
    staleTime: 30 * 60 * 1000,
    retry: 1,
    refetchOnWindowFocus: false,
  });

  useEffect(() => {
    if (typeof window === 'undefined') return;
    try {
      const raw = window.localStorage.getItem(STORAGE_KEY);
      if (!raw) return;
      const parsed = JSON.parse(raw) as Partial<AppSelectionState>;
      if (parsed.marketView) setMarketView(parsed.marketView);
      if (parsed.timeWindow) setTimeWindow(parsed.timeWindow);
      if (parsed.portfolioId) setPortfolioId(parsed.portfolioId);
    } catch {
      // ignore broken local cache
    }
  }, []);

  useEffect(() => {
    const defaults = bootstrapQuery.data?.default_settings;
    if (!defaults) return;

    setMarketView((current) => current || defaults.market_view);
    setTimeWindow((current) => current || defaults.time_window);

    const portfolios = bootstrapQuery.data?.portfolios ?? [];
    if (portfolios.length > 0) {
      setPortfolioId((current) => current || portfolios[0]);
    }
  }, [bootstrapQuery.data]);

  useEffect(() => {
    if (typeof window === 'undefined') return;
    window.localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({ marketView, timeWindow, portfolioId })
    );
  }, [marketView, timeWindow, portfolioId]);

  const value = useMemo(
    () => ({
      marketView,
      timeWindow,
      portfolioId,
      setMarketView,
      setTimeWindow,
      setPortfolioId,
      bootstrapData: bootstrapQuery.data,
      bootstrapLoading: bootstrapQuery.isLoading,
      bootstrapError: bootstrapQuery.error,
    }),
    [marketView, timeWindow, portfolioId, bootstrapQuery.data, bootstrapQuery.isLoading, bootstrapQuery.error]
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
