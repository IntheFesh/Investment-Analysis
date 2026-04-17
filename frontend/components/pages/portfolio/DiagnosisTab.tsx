import { Card, CardHeader } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { EvidencePanel, type Evidence } from '@/components/ui/EvidencePanel';
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

const FIT_TONE: Record<string, 'down' | 'warn' | 'info' | 'up'> = {
  进攻: 'down',
  防御: 'info',
  均衡: 'up',
};

export function PortfolioDiagnosisTab({ data }: Props) {
  const fitTone = FIT_TONE[data.environment_fit.tone] ?? 'warn';
  const warningEvidences: Evidence[] = (data.risk_warnings ?? [])
    .map((w) => w.evidence)
    .filter((e): e is Evidence => !!e);
  const adjustmentEvidences: Evidence[] = (data.adjustments ?? [])
    .map((a) => a.evidence)
    .filter((e): e is Evidence => !!e);
  const allEvidences = [...warningEvidences, ...adjustmentEvidences];

  const profileLabel = data.risk_profile.risk_type_label ?? data.risk_profile.risk_type;
  const horizonLabel =
    data.risk_profile.investment_horizon_label ?? data.risk_profile.investment_horizon;

  return (
    <div className="flex flex-col gap-4">
      <div className="grid grid-cols-1 lg:grid-cols-[1.2fr_1fr] gap-4">
        <Card>
          <CardHeader title="风险画像" subtitle={`${profileLabel} · 投资周期 ${horizonLabel}`} />

          <div className="mt-4">
            <div className="text-caption text-text-tertiary uppercase tracking-wider mb-2">
              风险提示
            </div>
            {data.risk_warnings.length === 0 ? (
              <div className="text-caption text-text-tertiary">当前无结构性警告。</div>
            ) : (
              <ul className="flex flex-col gap-2">
                {data.risk_warnings.map((w, i) => (
                  <li
                    key={`${w.kind}-${i}`}
                    className="flex items-start gap-2 rounded-md border border-border bg-surface-sunken/40 px-3 py-2"
                  >
                    <Badge tone={WARNING_TONE[w.kind] ?? 'warn'} size="sm">
                      {w.kind}
                    </Badge>
                    <span className="text-body-sm text-text-primary">{w.message}</span>
                  </li>
                ))}
              </ul>
            )}
          </div>

          <div className="mt-4">
            <div className="text-caption text-text-tertiary uppercase tracking-wider mb-2">
              环境适配
            </div>
            <div className="rounded-md border border-border bg-surface-sunken/40 p-3">
              <div className="flex items-center gap-2 mb-1.5">
                <Badge tone={fitTone} size="sm">
                  {data.environment_fit.tone}
                </Badge>
                <span className="text-caption text-text-tertiary">
                  {data.environment_fit.sentiment_short_state
                    ? `情绪态 ${data.environment_fit.sentiment_short_state}`
                    : '由组合年化波动推断'}
                </span>
              </div>
              <div className="text-body-sm text-text-primary">{data.environment_fit.message}</div>
            </div>
          </div>
        </Card>

        <Card>
          <CardHeader title="调整路径" subtitle="每条动作附带预期效应、前置条件与副作用。" />
          {data.adjustments && data.adjustments.length > 0 ? (
            <ul className="mt-3 flex flex-col gap-3">
              {data.adjustments.map((a, i) => (
                <li
                  key={i}
                  className="rounded-md border border-border bg-surface-sunken/40 p-3 text-body-sm"
                >
                  <div className="flex items-start gap-2">
                    <span className="shrink-0 mt-0.5 h-5 w-5 rounded-full bg-brand/15 text-brand text-caption tabular flex items-center justify-center">
                      {i + 1}
                    </span>
                    <span className="text-text-primary">{a.action}</span>
                  </div>
                  <div className="mt-2 grid grid-cols-1 md:grid-cols-3 gap-2 text-caption text-text-secondary">
                    <div>
                      <div className="text-micro text-text-tertiary uppercase">预期</div>
                      <div>{a.expected_effect}</div>
                    </div>
                    <div>
                      <div className="text-micro text-text-tertiary uppercase">前置</div>
                      <div>{a.preconditions}</div>
                    </div>
                    <div>
                      <div className="text-micro text-text-tertiary uppercase">副作用</div>
                      <div>{a.side_effects}</div>
                    </div>
                  </div>
                </li>
              ))}
            </ul>
          ) : (
            <ol className="mt-3 flex flex-col gap-2">
              {data.optimization.map((item, i) => (
                <li key={i} className="flex items-start gap-2.5 text-body-sm text-text-primary">
                  <span className="shrink-0 mt-0.5 h-5 w-5 rounded-full bg-brand/15 text-brand text-caption tabular flex items-center justify-center">
                    {i + 1}
                  </span>
                  <span>{item}</span>
                </li>
              ))}
            </ol>
          )}
          <div className="mt-4 border-t border-border pt-3">
            <div className="text-caption text-text-tertiary uppercase tracking-wider mb-2">
              参考引用
            </div>
            <dl className="grid grid-cols-1 gap-2 text-body-sm">
              {Object.entries(data.evidence).map(([key, value]) => (
                <div
                  key={key}
                  className="rounded-md bg-surface-sunken/40 border border-border px-3 py-2"
                >
                  <dt className="text-caption text-text-tertiary">{key}</dt>
                  <dd className="text-text-primary">{value}</dd>
                </div>
              ))}
            </dl>
          </div>
        </Card>
      </div>

      {allEvidences.length > 0 ? (
        <EvidencePanel
          title="诊断与调整证据"
          subtitle={`${warningEvidences.length} 条风险证据 · ${adjustmentEvidences.length} 条调整证据`}
          evidences={allEvidences}
        />
      ) : null}
    </div>
  );
}
