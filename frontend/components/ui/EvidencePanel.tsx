import { useState } from 'react';
import clsx from 'clsx';
import { Card, CardHeader } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';

export interface Evidence {
  conclusion: string;
  method: string;
  method_version: string;
  source_name: string;
  source_tier: string;
  truth_grade: string;
  universe: string;
  indicators: Record<string, unknown>;
  confidence: number;
  is_proxy: boolean;
  failure_conditions?: string[];
  risks?: string[];
  computed_at?: string;
}

interface EvidencePanelProps {
  title?: string;
  subtitle?: string;
  evidences: Evidence[];
  className?: string;
  dense?: boolean;
}

const GRADE_TONE: Record<string, string> = {
  A: 'text-success',
  B: 'text-info',
  C: 'text-warn',
  D: 'text-warn',
  E: 'text-text-tertiary',
};

const formatIndicator = (k: string, v: unknown): string => {
  if (v === null || v === undefined) return '—';
  if (typeof v === 'number') return Number.isInteger(v) ? String(v) : v.toFixed(4);
  if (Array.isArray(v)) return `[${v.length}]`;
  if (typeof v === 'object') return JSON.stringify(v).slice(0, 60);
  return String(v);
};

function EvidenceItem({ e, dense }: { e: Evidence; dense: boolean }) {
  const [open, setOpen] = useState(!dense);
  const grade = e.truth_grade ?? 'E';
  const gradeTone = GRADE_TONE[grade] ?? 'text-text-tertiary';
  const confidence = Math.round((e.confidence ?? 0) * 100);

  return (
    <div className="border border-border rounded-lg p-3 bg-surface-raised/60">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="w-full flex items-start gap-3 text-left"
      >
        <span className={clsx('mt-0.5 inline-flex h-5 w-5 items-center justify-center rounded border border-border font-mono text-[11px]', gradeTone)}>
          {grade}
        </span>
        <div className="flex-1 min-w-0">
          <div className="text-body-sm text-text-primary">{e.conclusion}</div>
          <div className="mt-1 flex flex-wrap gap-1 text-micro text-text-tertiary">
            <span>方法 {e.method}</span>
            <span>· 版本 {e.method_version}</span>
            <span>· 源 {e.source_name}</span>
            <span>· 置信度 {confidence}%</span>
            {e.is_proxy ? <Badge size="xs" tone="warn">代理</Badge> : null}
          </div>
        </div>
        <span className="text-caption text-text-tertiary">{open ? '收起' : '展开'}</span>
      </button>
      {open ? (
        <div className="mt-3 space-y-3 text-caption">
          {e.indicators && Object.keys(e.indicators).length > 0 ? (
            <div>
              <div className="text-micro uppercase text-text-tertiary tracking-wider mb-1">关键指标</div>
              <div className="grid grid-cols-2 gap-x-4 gap-y-1 tabular">
                {Object.entries(e.indicators).slice(0, 10).map(([k, v]) => (
                  <div key={k} className="flex items-center justify-between gap-2">
                    <span className="text-text-tertiary truncate">{k}</span>
                    <span className="text-text-primary font-medium truncate">{formatIndicator(k, v)}</span>
                  </div>
                ))}
              </div>
            </div>
          ) : null}
          {e.failure_conditions && e.failure_conditions.length > 0 ? (
            <div>
              <div className="text-micro uppercase text-text-tertiary tracking-wider mb-1">失效条件</div>
              <ul className="list-disc pl-5 space-y-0.5 text-text-secondary">
                {e.failure_conditions.map((c) => (
                  <li key={c}>{c}</li>
                ))}
              </ul>
            </div>
          ) : null}
          {e.risks && e.risks.length > 0 ? (
            <div>
              <div className="text-micro uppercase text-text-tertiary tracking-wider mb-1">风险提示</div>
              <ul className="list-disc pl-5 space-y-0.5 text-warn">
                {e.risks.map((c) => (
                  <li key={c}>{c}</li>
                ))}
              </ul>
            </div>
          ) : null}
          <div className="text-micro text-text-tertiary">
            universe={e.universe ?? '—'}
            {e.computed_at ? ` · 生成 ${e.computed_at.slice(0, 19).replace('T', ' ')}` : ''}
          </div>
        </div>
      ) : null}
    </div>
  );
}

export function EvidencePanel({
  title = '证据',
  subtitle,
  evidences,
  className,
  dense = false,
}: EvidencePanelProps) {
  if (!evidences || evidences.length === 0) return null;
  return (
    <Card className={className}>
      <CardHeader
        title={title}
        subtitle={subtitle ?? `${evidences.length} 条可追溯依据 · 点击条目展开查看指标与失效条件`}
      />
      <div className="mt-3 space-y-2">
        {evidences.map((e, idx) => (
          <EvidenceItem key={`${e.method}-${idx}`} e={e} dense={dense} />
        ))}
      </div>
    </Card>
  );
}
