import Link from 'next/link';
import Layout from '@/components/Layout';

/**
 * Fund index page
 *
 * Provides links to example funds defined in the sample data.  In a real
 * application this page might allow users to search or filter funds.
 */
export default function FundIndexPage() {
  const sampleFunds = [
    { code: 'FUND001', name: '半导体成长混合' },
    { code: 'FUND002', name: '新能源先锋' },
    { code: 'FUND003', name: '金融地产优选' },
    { code: 'FUND004', name: '科技创新先锋' },
    { code: 'FUND005', name: '消费红利精选' },
  ];
  return (
    <Layout>
      <h1 className="text-2xl font-bold mb-4">单基金研究</h1>
      <p className="text-sm mb-4">请选择一只基金以查看分析：</p>
      <ul className="space-y-2">
        {sampleFunds.map((fund) => (
          <li key={fund.code}>
            <Link href={`/fund/${fund.code}`} className="text-indigo-600 hover:underline">
              {fund.code} - {fund.name}
            </Link>
          </li>
        ))}
      </ul>
    </Layout>
  );
}