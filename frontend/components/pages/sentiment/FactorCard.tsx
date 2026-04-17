import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { ProgressBar } from '@/components/ui/ProgressBar';
import { directionArrow } from '@/utils/format';
import type { SentimentFactor } from '@/services/types';

interface Props {
  factor: SentimentFactor;
}

export function FactorCard({ factor }: Props) {
  const tone: 'up' | 'down' = factor.direction === 'up' ? 'up' : 'down';
  const score = factor.short_score ?? 50;
  const mid = factor.mid_score ?? 50;
  return (
    <Card padding="default">
      <div className="flex items-start justify-between gap-2">
        <div>
          <div className="text-caption text-text-tertiary uppercase tracking-wider">
            {factor.name}
          </div>
          <div className="text-metric-lg text-text-primary tabular mt-1">{score.toFixed(1)}</div>
          <div className="text-micro text-text-tertiary mt-0.5">
            中期 {mid.toFixed(1)} · 短中差 {(score - mid >= 0 ? '+' : '') + (score - mid).toFixed(1)}
          </div>
        </div>
        <Badge tone={tone} size="sm">
          <span>{directionArrow(factor.direction === 'up' ? 1 : -1)}</span>
          {factor.direction === 'up' ? '趋紧' : '走弱'}
        </Badge>
      </div>
      <div className="mt-3">
        <ProgressBar value={score / 100} tone={tone} size="sm" />
      </div>
      <div className="text-caption text-text-secondary mt-3 leading-5">{factor.driver}</div>
      {factor.evidence?.is_proxy ? (
        <div className="mt-2">
          <Badge tone="warn" size="xs">
            代理口径
          </Badge>
        </div>
      ) : null}
    </Card>
  );
}
