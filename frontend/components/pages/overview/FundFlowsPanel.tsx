import { Card, CardHeader } from '@/components/ui/Card';
import { BarChart } from '@/components/charts/BarChart';
import { EmptyState } from '@/components/ui/EmptyState';
import { formatCompact } from '@/utils/format';
import type { FundFlows } from '@/services/types';

interface Props {
  data: FundFlows;
}

export function FundFlowsPanel({ data }: Props) {
  // 市场语义：偏强/利好=红色，偏弱/利空=绿色；通过符号翻转与 signedColors 保持一致。
  const inflow = data.top_inflows.slice(0, 5).map((x) => ({ ...x, value: -Math.abs(x.value), display: x.value }));
  const outflow = data.top_outflows.slice(0, 5).map((x) => ({ ...x, value: Math.abs(x.value), display: x.value }));
  const combined = [...inflow, ...outflow].sort((a, b) => Math.abs(b.value) - Math.abs(a.value));
  const categories = combined.map((x) => x.sector);
  const values = combined.map((x) => x.value);

  return (
    <Card>
      <CardHeader
        title="流动性偏好"
        subtitle="以板块成交活跃度与收益动量构建的偏好强度（偏强=红，偏弱=绿）。"
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
            valueFormatter={(v) => formatCompact(Math.abs(v))}
            height={280}
          />
          <div className="mt-3 text-caption text-text-tertiary">{data.disclaimer}</div>
        </div>
      )}
    </Card>
  );
}
