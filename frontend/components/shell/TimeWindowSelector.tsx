import { SegmentedControl } from '@/components/ui/SegmentedControl';

export const MODULE_TIME_WINDOWS = ['5D', '20D', '60D', '120D', 'YTD', '1Y'] as const;
export type ModuleTimeWindow = (typeof MODULE_TIME_WINDOWS)[number];

interface Props {
  value: string;
  onChange: (next: string) => void;
  options?: string[];
  size?: 'sm' | 'md';
}

export function TimeWindowSelector({ value, onChange, options, size = 'sm' }: Props) {
  const opts = (options ?? [...MODULE_TIME_WINDOWS]).map((w) => ({ value: w, label: w }));
  return <SegmentedControl value={value} onChange={(v) => onChange(v)} options={opts} size={size} />;
}
