import { ReactNode } from 'react';
import Head from 'next/head';
import { Sidebar } from './Sidebar';
import { TopBar } from './TopBar';
import { SourceFootnote } from '@/components/ui/SourceFootnote';
import type { ApiMeta, EnvelopeStatus } from '@/lib/apiTypes';

interface LayoutProps {
  children: ReactNode;
  title?: string;
  subtitle?: string;
  meta?: ApiMeta;
  /** Envelope-level status when available — drives the freshness badge. */
  status?: EnvelopeStatus;
  /** When true, renders a default source footnote under the main content
   *  using ``meta``. Round-0 pages set this so every data view shows the
   *  "数据来源 · 延迟 · 截止 · 仅供研究" line without individual wiring. */
  showSourceFootnote?: boolean;
  actions?: ReactNode;
  showPortfolio?: boolean;
  showMarket?: boolean;
  rightSlot?: ReactNode;
}

export function Layout({
  children,
  title,
  subtitle,
  meta,
  status,
  showSourceFootnote,
  actions,
  showPortfolio,
  showMarket,
  rightSlot,
}: LayoutProps) {
  return (
    <div className="min-h-screen bg-surface-base text-text-primary">
      <Head>
        <title>{title ? `${title} · 投研工作台` : '投研工作台'}</title>
        <meta name="viewport" content="width=device-width, initial-scale=1" />
      </Head>
      <div className="flex">
        <Sidebar />
        <div className="flex-1 flex flex-col min-w-0">
          <TopBar
            meta={meta}
            status={status}
            rightSlot={rightSlot}
            showPortfolio={showPortfolio}
            showMarket={showMarket}
          />
          <main className="flex-1 px-6 py-5">
            {(title || subtitle || actions) && (
              <div className="flex items-start justify-between gap-4 mb-4">
                <div>
                  {title && <h1 className="text-display-md text-text-primary">{title}</h1>}
                  {subtitle && (
                    <p className="text-body-md text-text-secondary mt-1 max-w-3xl">{subtitle}</p>
                  )}
                </div>
                {actions ? <div className="shrink-0 flex items-center gap-2">{actions}</div> : null}
              </div>
            )}
            <div className="space-y-4 animate-fade-in">{children}</div>
            {showSourceFootnote ? (
              <div className="mt-6 border-t border-border/60 pt-3">
                <SourceFootnote meta={meta} />
              </div>
            ) : null}
          </main>
        </div>
      </div>
    </div>
  );
}
