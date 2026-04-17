import { Card, CardHeader } from '@/components/ui/Card';
import { BarChart } from '@/components/charts/BarChart';
import { EmptyState } from '@/components/ui/EmptyState';
import { formatCompact } from '@/utils/format';
import type { FundFlows } from '@/services/types';

interface Props {
  data: FundFlows;
}

export function FundFlowsPanel({ data }: Props) {
  const combined = [
    ...data.top_inflows.map((x) => ({ ...x, kind: 'in' as const })),
    ...data.top_outflows.map((x) => ({ ...x, kind: 'out' as const })),
  ];
  const categories = combined.map((x) => x.sector);
  const values = combined.map((x) => x.value);

  return (
    <Card>
      <CardHeader
        title="资金偏好（代理成交量 × 板块收益）"
        subtitle="由 /market/fund-flows 计算；正值代表潜在流入，负值代表流出。单位对齐后端成交量量级。"
      />
      {combined.length === 0 ? (
        <EmptyState compact title="无资金流数据" description="当前窗口内成交量样本不足。" />
      ) : (
        <div className="mt-4">
          <BarChart
            categories={categories}
            values={values}
            horizontal
            signedColors
            valueFormatter={(v) => formatCompact(v)}
            height={260}
          />
        </div>
      )}
    </Card>
  );
}
