import { useAppContext } from '@/context/AppContext';
import { SegmentedControl } from '@/components/ui/SegmentedControl';

/**
 * Research-mode switch — wired end-to-end to AppContext. Toggling updates
 * CSS density, compact/relaxed layouts, and stays in URL + localStorage.
 */
export function ResearchModeSwitch() {
  const { researchMode, setResearchMode } = useAppContext();
  return (
    <SegmentedControl
      value={researchMode}
      onChange={(v) => setResearchMode(v)}
      options={[
        { value: 'research', label: '研究模式', hint: '紧凑密度，信息最大化' },
        { value: 'light', label: '轻量模式', hint: '宽松密度，面向展示' },
      ]}
      size="sm"
    />
  );
}
