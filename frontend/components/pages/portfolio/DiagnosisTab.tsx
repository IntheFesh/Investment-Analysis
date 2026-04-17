import { Card, CardHeader } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import type { PortfolioDiagnosis } from '@/services/types';

interface Props {
  data: PortfolioDiagnosis;
}

const WARNING_TONE: Record<string, 'down' | 'warn' | 'info' | 'up'> = {
  concentration: 'down',
  volatility: 'down',
  watch: 'warn',
  ok: 'up',
};

const FIT_TONE: Record<string, 'down' | 'warn' | 'up'> = {
  进攻: 'down',
  防御: 'info' as 'warn',
  均衡: 'up',
};

export function PortfolioDiagnosisTab({ data }: Props) {
  const fitTone = FIT_TONE[data.environment_fit.tone] ?? 'warn';

  return (
    <div className="grid grid-cols-1 lg:grid-cols-[1.2fr_1fr] gap-4">
      <Card>
        <CardHeader
          title="风险画像"
          subtitle={`${data.risk_profile.risk_type} · 投资周期 ${data.risk_profile.investment_horizon}`}
        />

        <div className="mt-4">
          <div className="text-caption text-text-tertiary uppercase tracking-wider mb-2">风险提示</div>
          <ul className="flex flex-col gap-2">
            {data.risk_warnings.map((w, i) => (
              <li
                key={i}
                className="flex items-start gap-2 rounded-md border border-border bg-surface-sunken/40 px-3 py-2"
              >
                <Badge tone={WARNING_TONE[w.kind] ?? 'warn'} size="sm">
                  {w.kind}
                </Badge>
                <span className="text-body-sm text-text-primary">{w.message}</span>
              </li>
            ))}
          </ul>
        </div>

        <div className="mt-4">
          <div className="text-caption text-text-tertiary uppercase tracking-wider mb-2">环境适配</div>
          <div className="rounded-md border border-border bg-surface-sunken/40 p-3">
            <div className="flex items-center gap-2 mb-1.5">
              <Badge tone={fitTone} size="sm">
                {data.environment_fit.tone}
              </Badge>
              <span className="text-caption text-text-tertiary">由组合年化波动推断</span>
            </div>
            <div className="text-body-sm text-text-primary">{data.environment_fit.message}</div>
          </div>
        </div>
      </Card>

      <Card>
        <CardHeader
          title="优化方向"
          subtitle="根据当前暴露与波动生成，为人工决策提供候选动作。"
        />
        <ol className="mt-3 flex flex-col gap-2">
          {data.optimization.map((item, i) => (
            <li
              key={i}
              className="flex items-start gap-2.5 text-body-sm text-text-primary"
            >
              <span className="shrink-0 mt-0.5 h-5 w-5 rounded-full bg-brand/15 text-brand text-caption tabular flex items-center justify-center">
                {i + 1}
              </span>
              <span>{item}</span>
            </li>
          ))}
        </ol>
        <div className="mt-4 border-t border-border pt-3">
          <div className="text-caption text-text-tertiary uppercase tracking-wider mb-2">支撑证据</div>
          <dl className="grid grid-cols-1 gap-2 text-body-sm">
            {Object.entries(data.evidence).map(([key, value]) => (
              <div key={key} className="rounded-md bg-surface-sunken/40 border border-border px-3 py-2">
                <dt className="text-caption text-text-tertiary">{key}</dt>
                <dd className="text-text-primary">{value}</dd>
              </div>
            ))}
          </dl>
        </div>
      </Card>
    </div>
  );
}
