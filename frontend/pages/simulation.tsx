import { useEffect, useMemo, useState } from 'react';
import { Layout } from '@/components/shell/Layout';
import { SkeletonChart } from '@/components/ui/Skeleton';
import { EmptyState } from '@/components/ui/EmptyState';
import { ApiError } from '@/lib/apiTypes';
import {
  useSimulationPresets,
  useSimulationMutation,
  useHistoricalEvents,
} from '@/hooks/useSimulation';
import { useTaskRunner } from '@/hooks/useTaskPolling';
import { useAppContext } from '@/context/AppContext';
import {
  SimulationForm,
  type SimulationMode,
} from '@/components/pages/simulation/SimulationForm';
import { StatisticalResult } from '@/components/pages/simulation/StatisticalResult';
import { ScenarioResult } from '@/components/pages/simulation/ScenarioResult';
import { HistoricalResult } from '@/components/pages/simulation/HistoricalResult';
import type {
  SimulationResult,
  StatisticalSimulationResult,
  ScenarioSimulationResult,
  HistoricalSimulationResult,
} from '@/services/types';

export default function SimulationPage() {
  const { portfolioId, marketView } = useAppContext();
  const presetsQuery = useSimulationPresets();
  const historicalQuery = useHistoricalEvents();
  const mutation = useSimulationMutation();
  const runner = useTaskRunner();

  const [mode, setMode] = useState<SimulationMode>('statistical');
  const [stat, setStat] = useState({
    horizonDays: 60,
    numPaths: 500,
    confidenceInterval: 0.95,
    bootstrap: true,
  });
  const [selectedPresets, setSelectedPresets] = useState<string[]>([]);
  const [selectedEventId, setSelectedEventId] = useState<string | null>(null);
  const [useSentimentStress, setUseSentimentStress] = useState<boolean>(true);
  const [submitError, setSubmitError] = useState<string | null>(null);

  useEffect(() => {
    const events = historicalQuery.data?.data;
    if (events && events.length > 0 && !selectedEventId) {
      setSelectedEventId(events[0].id);
    }
  }, [historicalQuery.data, selectedEventId]);

  const submit = async () => {
    setSubmitError(null);
    runner.reset();
    try {
      if (mode === 'statistical') {
        const res = await mutation.mutateAsync({
          mode: 'statistical',
          portfolio_id: portfolioId,
          horizon_days: stat.horizonDays,
          num_paths: stat.numPaths,
          confidence_interval: stat.confidenceInterval,
          bootstrap: stat.bootstrap,
          market_view: marketView,
          use_sentiment_stress: useSentimentStress,
        });
        runner.start(res.data.task_id);
      } else if (mode === 'historical') {
        if (!selectedEventId) {
          setSubmitError('请选择一个历史事件。');
          return;
        }
        const res = await mutation.mutateAsync({
          mode: 'historical',
          portfolio_id: portfolioId,
          event_id: selectedEventId,
          market_view: marketView,
          use_sentiment_stress: useSentimentStress,
        });
        runner.start(res.data.task_id);
      } else {
        if (selectedPresets.length === 0) {
          setSubmitError('请至少选择一个情景预设。');
          return;
        }
        const res = await mutation.mutateAsync({
          mode: 'scenario',
          portfolio_id: portfolioId,
          scenario_ids: selectedPresets,
          market_view: marketView,
          use_sentiment_stress: useSentimentStress,
        });
        runner.start(res.data.task_id);
      }
    } catch (e) {
      setSubmitError(e instanceof ApiError ? e.message : '后端拒绝了模拟任务');
    }
  };

  const togglePreset = (id: string) => {
    setSelectedPresets((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id],
    );
  };

  const result = useMemo<SimulationResult | null>(() => {
    if (runner.task?.state !== 'succeeded') return null;
    return (runner.task.result as SimulationResult) ?? null;
  }, [runner.task]);

  const progress = runner.task
    ? { state: runner.task.state, progress: runner.task.progress, message: runner.task.message }
    : null;

  const disableSubmit =
    mutation.isLoading ||
    Boolean(runner.task && (runner.task.state === 'running' || runner.task.state === 'pending'));

  return (
    <Layout
      title="情景模拟"
      subtitle="统计 / 历史重演 / 情景冲击 三引擎共享任务管线，可叠加当日情绪压力参数。"
      meta={presetsQuery.data?.meta}
    >
      <SimulationForm
        mode={mode}
        onModeChange={setMode}
        stat={stat}
        onStatChange={setStat}
        presets={presetsQuery.data?.data ?? []}
        selectedPresets={selectedPresets}
        onPresetToggle={togglePreset}
        historicalEvents={historicalQuery.data?.data ?? []}
        selectedEventId={selectedEventId}
        onEventChange={setSelectedEventId}
        useSentimentStress={useSentimentStress}
        onSentimentStressChange={setUseSentimentStress}
        disabled={disableSubmit}
        onSubmit={submit}
        taskProgress={progress}
        errorMessage={submitError ?? (runner.task?.error ?? null)}
      />

      {runner.task && (runner.task.state === 'running' || runner.task.state === 'pending') ? (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <SkeletonChart height={280} />
          <SkeletonChart height={280} />
        </div>
      ) : null}

      {result && result.mode === 'statistical' ? (
        <StatisticalResult result={result as StatisticalSimulationResult} />
      ) : null}

      {result && result.mode === 'scenario' ? (
        <ScenarioResult result={result as ScenarioSimulationResult} />
      ) : null}

      {result && result.mode === 'historical' ? (
        <HistoricalResult result={result as HistoricalSimulationResult} />
      ) : null}

      {!runner.task && !mutation.isLoading ? (
        <EmptyState
          title="尚未提交模拟任务"
          description="选择模式和参数后点击“提交模拟任务”——后端会立刻返回 task_id。"
        />
      ) : null}
    </Layout>
  );
}
