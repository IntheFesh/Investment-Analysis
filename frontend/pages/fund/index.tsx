import Link from 'next/link';
import { Layout } from '@/components/shell/Layout';
import { Card, CardHeader } from '@/components/ui/Card';
import { DataTable } from '@/components/ui/Table';
import { Badge } from '@/components/ui/Badge';
import { EmptyState } from '@/components/ui/EmptyState';
import { ErrorState } from '@/components/ui/ErrorState';
import { SkeletonChart } from '@/components/ui/Skeleton';
import { useFundList } from '@/hooks/useFund';

export default function FundIndexPage() {
  const { data, isLoading, error, refetch } = useFundList();

  return (
    <Layout
      title="单基金研究"
      subtitle="从基金池挑选目标产品，进入净值、风控、组合关系与研究结论。"
      meta={data?.meta}
      showPortfolio={false}
    >
      <Card>
        <CardHeader title="基金池" subtitle="由后端 /api/v1/fund/ 提供的全量列表。" />
        {isLoading ? (
          <SkeletonChart height={200} />
        ) : error ? (
          <ErrorState error={error} onRetry={() => refetch()} />
        ) : data && data.data.length ? (
          <DataTable
            dense
            columns={[
              {
                key: 'code',
                header: '代码',
                render: (r) => (
                  <Link href={`/fund/${r.code}`} className="text-brand hover:underline font-mono">
                    {r.code}
                  </Link>
                ),
              },
              {
                key: 'name',
                header: '名称',
                render: (r) => (
                  <Link href={`/fund/${r.code}`} className="text-text-primary hover:text-brand">
                    {r.name}
                  </Link>
                ),
              },
              {
                key: 'type',
                header: '类型',
                render: (r) => <Badge tone="brand" size="xs">{r.type}</Badge>,
              },
              {
                key: 'manager',
                header: '基金经理',
                render: (r) => r.manager,
              },
            ]}
            rows={data.data}
            getRowKey={(r) => r.code}
          />
        ) : (
          <EmptyState title="基金池为空" description="当前数据源未提供基金元数据。" />
        )}
      </Card>
    </Layout>
  );
}
