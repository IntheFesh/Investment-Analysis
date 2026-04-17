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
  return (
    <Card padding="default">
      <div className="flex items-start justify-between gap-2">
        <div>
          <div className="text-caption text-text-tertiary uppercase tracking-wider">{factor.name}</div>
          <div className="text-metric-lg text-text-primary tabular mt-1">
            {factor.score.toFixed(1)}
          </div>
        </div>
        <Badge tone={tone} size="sm">
          <span>{directionArrow(factor.direction === 'up' ? 1 : -1)}</span>
          {factor.direction === 'up' ? '偏多' : '偏空'}
        </Badge>
      </div>
      <div className="mt-3">
        <ProgressBar value={factor.score / 100} tone={tone} size="sm" />
      </div>
      <div className="text-caption text-text-secondary mt-3 leading-5">{factor.driver}</div>
    </Card>
  );
}
