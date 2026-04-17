import { useState } from 'react';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { exportService } from '@/services/exportService';
import { useTaskRunner } from '@/hooks/useTaskPolling';
import { ApiError } from '@/lib/apiTypes';

interface ExportButtonProps {
  page: string;
  portfolioId?: string | null;
  formats?: string[];
}

export function ExportButton({ page, portfolioId = null, formats = ['JSON', 'Markdown', 'CSV'] }: ExportButtonProps) {
  const runner = useTaskRunner();
  const [error, setError] = useState<string | null>(null);

  const trigger = async () => {
    setError(null);
    try {
      const res = await exportService.exportPage({ page, portfolio_id: portfolioId, formats });
      runner.start(res.data.task_id);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : '导出失败');
    }
  };

  const state = runner.task?.state;
  const link = (runner.task?.result as { download_link?: string } | undefined)?.download_link;

  return (
    <div className="flex items-center gap-2">
      <Button
        variant="primary"
        size="sm"
        onClick={trigger}
        loading={runner.isRunning}
        leftIcon={
          <svg width="14" height="14" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.6">
            <path d="M10 3v10m0 0l-3-3m3 3l3-3" strokeLinecap="round" strokeLinejoin="round" />
            <path d="M4 16h12" strokeLinecap="round" />
          </svg>
        }
      >
        导出报告
      </Button>
      {runner.isRunning ? (
        <Badge tone="info" size="sm">
          {runner.task?.message || '排队中…'} {Math.round((runner.task?.progress ?? 0) * 100)}%
        </Badge>
      ) : null}
      {state === 'succeeded' && link ? (
        <Badge tone="up" size="sm">
          已就绪 · {link.split('/').pop()}
        </Badge>
      ) : null}
      {state === 'failed' ? <Badge tone="down" size="sm">任务失败</Badge> : null}
      {error ? <Badge tone="down" size="sm">{error}</Badge> : null}
    </div>
  );
}
