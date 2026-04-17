import { useAppContext } from '@/context/AppContext';
import { SegmentedControl } from '@/components/ui/SegmentedControl';

export function TimeWindowSelector() {
  const { timeWindow, setTimeWindow, bootstrapData } = useAppContext();
  const windows = (bootstrapData?.time_windows ?? ['5D', '20D', '60D', '120D', 'YTD', '1Y'])
    .filter((w) => w !== 'CUSTOM')
    .map((w) => ({ value: w, label: w }));

  return (
    <SegmentedControl
      value={timeWindow}
      onChange={(v) => setTimeWindow(v)}
      options={windows}
      size="sm"
    />
  );
}
