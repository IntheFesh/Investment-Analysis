import { ReactNode } from 'react';
import { MarketSelector } from './MarketSelector';
import { TimeWindowSelector } from './TimeWindowSelector';
import { PortfolioSelector } from './PortfolioSelector';
import { ResearchModeSwitch } from './ResearchModeSwitch';
import { ThemeToggle } from './ThemeToggle';
import { DataSourceBadge } from '@/components/ui/DataSourceBadge';
import type { ApiMeta } from '@/lib/apiTypes';

interface TopBarProps {
  meta?: ApiMeta;
  rightSlot?: ReactNode;
  showPortfolio?: boolean;
  showMarket?: boolean;
  showTimeWindow?: boolean;
}

export function TopBar({
  meta,
  rightSlot,
  showPortfolio = true,
  showMarket = true,
  showTimeWindow = true,
}: TopBarProps) {
  return (
    <header className="sticky top-0 z-10 flex items-center gap-3 border-b border-border bg-surface-base/90 px-6 py-3 backdrop-blur">
      <div className="flex flex-1 items-center gap-3 flex-wrap">
        {showMarket && (
          <div className="flex items-center gap-2">
            <div className="text-micro uppercase tracking-wider text-text-tertiary">市场视角</div>
            <MarketSelector />
          </div>
        )}
        {showTimeWindow && (
          <div className="flex items-center gap-2">
            <div className="text-micro uppercase tracking-wider text-text-tertiary">观察窗口</div>
            <TimeWindowSelector />
          </div>
        )}
        {showPortfolio && (
          <div className="flex items-center gap-2">
            <div className="text-micro uppercase tracking-wider text-text-tertiary">组合</div>
            <PortfolioSelector />
          </div>
        )}
      </div>
      <div className="flex items-center gap-3">
        {rightSlot}
        <DataSourceBadge meta={meta} />
        <ResearchModeSwitch />
        <ThemeToggle />
      </div>
    </header>
  );
}
