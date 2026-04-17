import { Card, CardHeader } from '@/components/ui/Card';
import { BarChart } from '@/components/charts/BarChart';
import { EmptyState } from '@/components/ui/EmptyState';
import { formatCompact } from '@/utils/format';
import type { FundFlows } from '@/services/types';

interface Props {
  data: FundFlows;
}

export function FundFlowsPanel({ data }: Props) {
  const inflow = data.top_inflows.slice(0, 5).map((x) => ({ ...x, value: Math.abs(x.value) }));
  const outflow = data.top_outflows.slice(0, 5).map((x) => ({ ...x, value: -Math.abs(x.value) }));
  const combined = [...inflow, ...outflow].sort((a, b) => b.value - a.value);
  const categories = combined.map((x) => x.sector);
  const values = combined.map((x) => x.value);

  return (
    <Card>
      <CardHeader
        title="流动性偏好"
        subtitle="以板块成交活跃度与收益动量构建的偏好强度，反映资金风格倾向。"
      />
      {combined.length === 0 ? (
        <EmptyState compact title="无偏好数据" description="当前窗口内样本不足。" />
      ) : (
        <div className="mt-4">
          <BarChart
            categories={categories}
            values={values}
            horizontal
            signedColors
            valueFormatter={(v) => formatCompact(v)}
            height={280}
          />
          <div className="mt-3 text-caption text-text-tertiary">{data.disclaimer}</div>
        </div>
      )}
    </Card>
  );
}
