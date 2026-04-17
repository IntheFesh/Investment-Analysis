import { useState } from 'react';
import { Card, CardHeader } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Tabs } from '@/components/ui/Tabs';
import { Toggle } from '@/components/ui/Toggle';
import { portfolioService } from '@/services/portfolioService';
import { useTaskRunner } from '@/hooks/useTaskPolling';
import { useAppContext } from '@/context/AppContext';
import { ApiError } from '@/lib/apiTypes';
import type { PortfolioExportPack } from '@/services/types';

interface Props {
  data: PortfolioExportPack;
}

const ALL_FORMATS: Array<{ id: string; label: string }> = [
  { id: 'JSON', label: 'JSON' },
  { id: 'Markdown', label: 'Markdown' },
  { id: 'CSV', label: 'CSV' },
  { id: 'PNG', label: 'PNG 图表' },
];

export function PortfolioAIExportTab({ data }: Props) {
  const { portfolioId } = useAppContext();
  const runner = useTaskRunner();
  const [formats, setFormats] = useState<string[]>(['JSON', 'Markdown', 'CSV']);
  const [viewTab, setViewTab] = useState('markdown');
  const [error, setError] = useState<string | null>(null);

  const triggerExport = async () => {
    setError(null);
    try {
      const res = await portfolioService.requestExport(portfolioId, formats);
      runner.start(res.data.task_id);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : '后端拒绝了导出任务');
    }
  };

  const toggleFormat = (id: string) => {
    setFormats((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
    );
  };

  const state = runner.task?.state;
  const downloadLink =
    (runner.task?.result as { download_link?: string } | undefined)?.download_link ?? null;

  const tabs = [
    { id: 'markdown', label: 'Markdown' },
    { id: 'csv', label: 'CSV' },
    { id: 'json', label: 'JSON' },
    { id: 'prompt', label: 'AI 提示词' },
  ];

  const content =
    viewTab === 'markdown'
      ? data.formats.markdown
      : viewTab === 'csv'
        ? data.formats.csv
        : viewTab === 'json'
          ? JSON.stringify(data.formats.json, null, 2)
          : data.recommendation_prompt;

  return (
    <div className="grid grid-cols-1 lg:grid-cols-[1fr_1.4fr] gap-4">
      <Card>
        <CardHeader
          title="导出配置"
          subtitle="选择交付格式，后端生成包并返回下载链接。演示环境仅提供占位下载。"
        />
        <div className="mt-3 flex flex-col gap-2">
          {ALL_FORMATS.map((f) => (
            <Toggle
              key={f.id}
              checked={formats.includes(f.id)}
              onChange={() => toggleFormat(f.id)}
              label={f.label}
              description={
                f.id === 'PNG' ? '真实部署需由导出服务渲染静态图表' : undefined
              }
            />
          ))}
        </div>
        <div className="mt-4 flex items-center gap-2">
          <Button
            variant="primary"
            size="sm"
            onClick={triggerExport}
            loading={runner.isRunning}
            disabled={formats.length === 0}
          >
            生成并提交任务
          </Button>
          {state === 'succeeded' && downloadLink ? (
            <a
              href={downloadLink}
              target="_blank"
              rel="noreferrer"
              className="text-body-sm text-brand hover:underline"
            >
              下载 {downloadLink.split('/').pop()}
            </a>
          ) : null}
        </div>
        {runner.task ? (
          <div className="mt-3 flex items-center gap-2">
            <Badge tone={state === 'failed' ? 'down' : state === 'succeeded' ? 'up' : 'info'} size="sm">
              {state}
            </Badge>
            <div className="text-caption text-text-secondary">
              {runner.task.message}（{Math.round(runner.task.progress * 100)}%）
            </div>
          </div>
        ) : null}
        {error ? <div className="text-caption text-danger mt-2">{error}</div> : null}
      </Card>

      <Card>
        <CardHeader title="预览" subtitle="四种视图对应 Markdown / CSV / JSON 与可直接粘贴的 AI 提示词。" />
        <div className="mt-3">
          <Tabs
            variant="segment"
            value={viewTab}
            onChange={setViewTab}
            items={tabs}
            size="sm"
          />
        </div>
        <pre className="mt-3 max-h-[420px] overflow-auto rounded-md border border-border bg-surface-sunken p-3 text-body-sm text-text-primary font-mono whitespace-pre-wrap">
          {content}
        </pre>
      </Card>
    </div>
  );
}
