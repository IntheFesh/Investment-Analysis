import { Card, CardHeader } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Select } from '@/components/ui/Select';
import { Tabs } from '@/components/ui/Tabs';
import { Badge } from '@/components/ui/Badge';

interface Preset {
  id: string;
  label: string;
}

interface HistoricalOption {
  id: string;
  label: string;
  description?: string;
}

interface StatisticalParams {
  horizonDays: number;
  numPaths: number;
  confidenceInterval: number;
  bootstrap: boolean;
}

export type SimulationMode = 'statistical' | 'scenario' | 'historical';

interface Props {
  mode: SimulationMode;
  onModeChange: (mode: SimulationMode) => void;
  stat: StatisticalParams;
  onStatChange: (next: StatisticalParams) => void;
  presets: Preset[];
  selectedPresets: string[];
  onPresetToggle: (id: string) => void;
  historicalEvents: HistoricalOption[];
  selectedEventId: string | null;
  onEventChange: (id: string) => void;
  useSentimentStress: boolean;
  onSentimentStressChange: (next: boolean) => void;
  disabled: boolean;
  onSubmit: () => void;
  taskProgress?: { state: string; progress: number; message: string } | null;
  errorMessage?: string | null;
}

const HORIZON_OPTIONS = [
  { value: '20', label: '20D' },
  { value: '60', label: '60D' },
  { value: '120', label: '120D' },
  { value: '250', label: '250D' },
];

const CONFIDENCE_OPTIONS = [
  { value: '0.90', label: '90%' },
  { value: '0.95', label: '95%' },
  { value: '0.99', label: '99%' },
];

export function SimulationForm({
  mode,
  onModeChange,
  stat,
  onStatChange,
  presets,
  selectedPresets,
  onPresetToggle,
  historicalEvents,
  selectedEventId,
  onEventChange,
  useSentimentStress,
  onSentimentStressChange,
  disabled,
  onSubmit,
  taskProgress,
  errorMessage,
}: Props) {
  const modeItems = [
    { id: 'statistical', label: '统计模拟' },
    { id: 'historical', label: '历史重演' },
    { id: 'scenario', label: '情景模拟' },
  ];

  return (
    <Card>
      <CardHeader
        title="模拟参数"
        subtitle="三引擎共享任务管线：统计 Bootstrap、历史事件重演、叙事情景冲击。"
      />
      <div className="mt-3">
        <Tabs
          variant="segment"
          value={mode}
          onChange={(v) => onModeChange(v as SimulationMode)}
          items={modeItems}
          size="sm"
        />
      </div>

      {mode === 'statistical' ? (
        <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-3">
          <Select
            label="模拟区间"
            size="sm"
            value={String(stat.horizonDays)}
            onChange={(e) => onStatChange({ ...stat, horizonDays: Number(e.target.value) })}
            options={HORIZON_OPTIONS}
          />
          <Input
            label="路径数"
            size="sm"
            type="number"
            min={100}
            max={5000}
            step={100}
            value={stat.numPaths}
            onChange={(e) => onStatChange({ ...stat, numPaths: Number(e.target.value) })}
          />
          <Select
            label="置信区间"
            size="sm"
            value={stat.confidenceInterval.toFixed(2)}
            onChange={(e) => onStatChange({ ...stat, confidenceInterval: Number(e.target.value) })}
            options={CONFIDENCE_OPTIONS}
          />
          <div className="flex flex-col gap-1">
            <div className="text-caption text-text-tertiary uppercase tracking-wide">抽样方式</div>
            <div className="flex items-center gap-2">
              <Button
                variant={stat.bootstrap ? 'primary' : 'secondary'}
                size="sm"
                onClick={() => onStatChange({ ...stat, bootstrap: true })}
              >
                Block Bootstrap
              </Button>
              <Button
                variant={!stat.bootstrap ? 'primary' : 'secondary'}
                size="sm"
                onClick={() => onStatChange({ ...stat, bootstrap: false })}
              >
                高斯
              </Button>
            </div>
          </div>
        </div>
      ) : mode === 'historical' ? (
        <div className="mt-4 flex flex-col gap-3">
          <div className="text-caption text-text-tertiary uppercase tracking-wide">
            选择历史事件（后端 /historical-events）
          </div>
          {historicalEvents.length === 0 ? (
            <div className="text-body-sm text-text-tertiary">后端未提供历史事件。</div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
              {historicalEvents.map((ev) => {
                const active = selectedEventId === ev.id;
                return (
                  <button
                    key={ev.id}
                    type="button"
                    onClick={() => onEventChange(ev.id)}
                    className={
                      'text-left rounded-md border px-3 py-2 transition-colors duration-standard ' +
                      (active
                        ? 'border-brand bg-brand/10'
                        : 'border-border hover:border-border-strong')
                    }
                  >
                    <div className="text-body-sm text-text-primary">{ev.label}</div>
                    {ev.description ? (
                      <div className="text-caption text-text-tertiary mt-1 line-clamp-2">
                        {ev.description}
                      </div>
                    ) : null}
                  </button>
                );
              })}
            </div>
          )}
        </div>
      ) : (
        <div className="mt-4">
          <div className="text-caption text-text-tertiary uppercase tracking-wide mb-2">
            勾选情景预设（支持多选）
          </div>
          {presets.length === 0 ? (
            <div className="text-body-sm text-text-tertiary">后端未返回预设。</div>
          ) : (
            <div className="flex flex-wrap gap-2">
              {presets.map((p) => {
                const active = selectedPresets.includes(p.id);
                return (
                  <button
                    key={p.id}
                    type="button"
                    onClick={() => onPresetToggle(p.id)}
                    className={
                      'rounded-full border px-3 py-1 text-body-sm transition-colors duration-standard ' +
                      (active
                        ? 'border-brand bg-brand/15 text-brand'
                        : 'border-border text-text-secondary hover:border-border-strong')
                    }
                  >
                    {p.label}
                  </button>
                );
              })}
            </div>
          )}
        </div>
      )}

      <div className="mt-4 flex items-center gap-4 text-caption">
        <label className="flex items-center gap-2 cursor-pointer select-none">
          <input
            type="checkbox"
            checked={useSentimentStress}
            onChange={(e) => onSentimentStressChange(e.target.checked)}
          />
          <span className="text-text-secondary">叠加当日情绪压力参数</span>
        </label>
      </div>

      <div className="mt-4 flex items-center gap-3">
        <Button
          variant="primary"
          size="sm"
          onClick={onSubmit}
          loading={Boolean(
            taskProgress && (taskProgress.state === 'running' || taskProgress.state === 'pending'),
          )}
          disabled={disabled}
        >
          提交模拟任务
        </Button>
        {taskProgress ? (
          <div className="flex items-center gap-2">
            <Badge
              tone={
                taskProgress.state === 'failed'
                  ? 'down'
                  : taskProgress.state === 'succeeded'
                    ? 'up'
                    : 'info'
              }
              size="sm"
            >
              {taskProgress.state}
            </Badge>
            <span className="text-caption text-text-secondary">
              {taskProgress.message}（{Math.round(taskProgress.progress * 100)}%）
            </span>
          </div>
        ) : null}
      </div>
      {errorMessage ? <div className="mt-2 text-caption text-danger">{errorMessage}</div> : null}
    </Card>
  );
}
