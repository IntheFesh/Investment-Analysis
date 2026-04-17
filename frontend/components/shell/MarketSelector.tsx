import { useAppContext } from '@/context/AppContext';
import { SegmentedControl } from '@/components/ui/SegmentedControl';

export function MarketSelector() {
  const { marketView, setMarketView, bootstrapData } = useAppContext();
  const options = (bootstrapData?.markets ?? [
    { id: 'cn_a', label: 'A股' },
    { id: 'hk', label: '港股' },
    { id: 'global', label: '全球' },
  ]).map((m) => ({ value: m.id, label: m.label }));

  return (
    <SegmentedControl
      value={marketView}
      onChange={(v) => setMarketView(v)}
      options={options}
      size="sm"
    />
  );
}
