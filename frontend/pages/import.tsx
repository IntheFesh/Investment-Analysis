import { useMemo, useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { useRouter } from 'next/router';
import { Layout } from '@/components/shell/Layout';
import { Card, CardHeader } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input, Textarea } from '@/components/ui/Input';
import { Tabs } from '@/components/ui/Tabs';
import { Badge } from '@/components/ui/Badge';
import { EmptyState } from '@/components/ui/EmptyState';
import { SkeletonChart } from '@/components/ui/Skeleton';
import { importService, type FundImportEntry } from '@/services/importService';
import { useTaskRunner } from '@/hooks/useTaskPolling';
import { ApiError } from '@/lib/apiTypes';
import { CalibrationTable } from '@/components/pages/import/CalibrationTable';
import type { OcrPreviewRow } from '@/services/types';

type Mode = 'codes' | 'csv' | 'screenshot';

const MODE_TABS = [
  { id: 'codes', label: '基金代码' },
  { id: 'csv', label: 'CSV 文件' },
  { id: 'screenshot', label: '持仓截图' },
];

interface ParsedPreview {
  source: string;
  entries: FundImportEntry[];
  rejected?: string[];
  ocrConfidences?: Record<string, number>;
  needsReview: boolean;
}

export default function ImportPage() {
  const router = useRouter();
  const [mode, setMode] = useState<Mode>('codes');
  const [codesInput, setCodesInput] = useState('');
  const [csvInput, setCsvInput] = useState('');
  const [csvDelimiter, setCsvDelimiter] = useState(',');
  const [screenshots, setScreenshots] = useState<string[]>([]);
  const [preview, setPreview] = useState<ParsedPreview | null>(null);
  const [totalCost, setTotalCost] = useState('');
  const [label, setLabel] = useState('导入组合');
  const [parseError, setParseError] = useState<string | null>(null);
  const [confirmError, setConfirmError] = useState<string | null>(null);

  const ocrRunner = useTaskRunner();

  const parseCodes = useMutation(importService.parseCodes);
  const parseCsv = useMutation(
    (payload: { csv: string; delim: string }) =>
      importService.parseCsv(payload.csv, payload.delim)
  );
  const parseScreenshot = useMutation(importService.parseScreenshot);
  const confirm = useMutation(importService.confirm);

  const handleParse = async () => {
    setParseError(null);
    setPreview(null);
    ocrRunner.reset();
    try {
      if (mode === 'codes') {
        const codes = codesInput
          .split(/[\s,，;；\n]+/)
          .map((c) => c.trim())
          .filter(Boolean);
        if (!codes.length) {
          setParseError('请输入至少一个基金代码。');
          return;
        }
        const res = await parseCodes.mutateAsync(codes);
        setPreview(adaptPreview(res.data));
      } else if (mode === 'csv') {
        if (!csvInput.trim()) {
          setParseError('请粘贴 CSV 文本。');
          return;
        }
        const res = await parseCsv.mutateAsync({ csv: csvInput, delim: csvDelimiter });
        setPreview(adaptPreview(res.data));
      } else {
        if (!screenshots.length) {
          setParseError('请至少添加一张 base64 编码的截图。');
          return;
        }
        const res = await parseScreenshot.mutateAsync(screenshots);
        ocrRunner.start(res.data.task_id);
      }
    } catch (e) {
      setParseError(e instanceof ApiError ? e.message : '后端拒绝了解析请求');
    }
  };

  const ocrTaskResult = ocrRunner.task?.result as
    | { preview: OcrPreviewRow[]; needs_review: boolean; source: string }
    | undefined;

  const effectivePreview: ParsedPreview | null = useMemo(() => {
    if (preview) return preview;
    if (ocrRunner.task?.state === 'succeeded' && ocrTaskResult) {
      const entries: FundImportEntry[] = (ocrTaskResult.preview ?? []).map((p) => ({
        code: p.code,
        name: p.name,
        shares: p.shares,
        market_value: p.market_value,
      }));
      const confidences: Record<string, number> = {};
      (ocrTaskResult.preview ?? []).forEach((p) => {
        confidences[p.code] = p.confidence;
      });
      return {
        source: ocrTaskResult.source,
        entries,
        needsReview: ocrTaskResult.needs_review,
        ocrConfidences: confidences,
      };
    }
    return null;
  }, [preview, ocrRunner.task, ocrTaskResult]);

  const updateEntries = (entries: FundImportEntry[]) => {
    if (!effectivePreview) return;
    setPreview({ ...effectivePreview, entries });
  };

  const handleConfirm = async () => {
    if (!effectivePreview) return;
    setConfirmError(null);
    try {
      const cost = Number(totalCost);
      const res = await confirm.mutateAsync({
        funds: effectivePreview.entries,
        total_cost: Number.isFinite(cost) ? cost : 0,
        label,
      });
      router.push(`/portfolio?pf=${res.data.portfolio_id}`);
    } catch (e) {
      setConfirmError(e instanceof ApiError ? e.message : '后端拒绝了组合创建');
    }
  };

  const addScreenshotSlot = () => setScreenshots((s) => [...s, '']);
  const updateScreenshot = (i: number, v: string) =>
    setScreenshots((s) => s.map((x, idx) => (idx === i ? v : x)));
  const removeScreenshot = (i: number) =>
    setScreenshots((s) => s.filter((_, idx) => idx !== i));

  const isParsing = parseCodes.isLoading || parseCsv.isLoading || parseScreenshot.isLoading;
  const ocrBusy = ocrRunner.task?.state === 'running' || ocrRunner.task?.state === 'pending';

  return (
    <Layout
      title="导入持仓"
      subtitle="代码 / CSV / 截图三种来源 → 后端解析与校准 → 确认创建组合。"
      showPortfolio={false}
    >
      <Card>
        <CardHeader title="选择导入模式" subtitle="所有解析在后端完成，前端仅负责校准和确认。" />
        <div className="mt-3">
          <Tabs
            variant="segment"
            value={mode}
            onChange={(v) => setMode(v as Mode)}
            items={MODE_TABS}
            size="sm"
          />
        </div>

        {mode === 'codes' ? (
          <div className="mt-4">
            <Textarea
              label="基金代码（支持换行/逗号/空格分隔）"
              rows={4}
              placeholder="000001\n110022, 502000"
              value={codesInput}
              onChange={(e) => setCodesInput(e.target.value)}
            />
          </div>
        ) : mode === 'csv' ? (
          <div className="mt-4 flex flex-col gap-3">
            <Input
              label="分隔符"
              size="sm"
              value={csvDelimiter}
              onChange={(e) => setCsvDelimiter(e.target.value || ',')}
            />
            <Textarea
              label="CSV 文本（表头示例：code,name,shares,market_value,cost）"
              rows={6}
              placeholder="code,name,shares,market_value,cost"
              value={csvInput}
              onChange={(e) => setCsvInput(e.target.value)}
            />
          </div>
        ) : (
          <div className="mt-4 flex flex-col gap-3">
            <div className="text-caption text-text-tertiary">
              每个槽位接受 base64 编码的持仓截图。演示环境的后端会按顺序返回 OCR 预览。
            </div>
            {screenshots.map((s, i) => (
              <div key={i} className="flex items-start gap-2">
                <Textarea
                  label={`截图 #${i + 1}`}
                  rows={3}
                  value={s}
                  placeholder="data:image/png;base64,..."
                  onChange={(e) => updateScreenshot(i, e.target.value)}
                />
                <Button variant="ghost" size="sm" onClick={() => removeScreenshot(i)}>
                  删除
                </Button>
              </div>
            ))}
            <div>
              <Button variant="secondary" size="sm" onClick={addScreenshotSlot}>
                添加截图
              </Button>
            </div>
          </div>
        )}

        <div className="mt-4 flex items-center gap-3">
          <Button
            variant="primary"
            size="sm"
            onClick={handleParse}
            loading={isParsing || ocrBusy}
          >
            解析预览
          </Button>
          {ocrRunner.task ? (
            <div className="flex items-center gap-2">
              <Badge
                tone={
                  ocrRunner.task.state === 'failed'
                    ? 'down'
                    : ocrRunner.task.state === 'succeeded'
                      ? 'up'
                      : 'info'
                }
                size="sm"
              >
                {ocrRunner.task.state}
              </Badge>
              <span className="text-caption text-text-secondary">
                {ocrRunner.task.message}（{Math.round(ocrRunner.task.progress * 100)}%）
              </span>
            </div>
          ) : null}
          {parseError ? <div className="text-caption text-danger">{parseError}</div> : null}
        </div>
      </Card>

      {ocrBusy ? <SkeletonChart height={220} /> : null}

      {effectivePreview ? (
        <Card>
          <CardHeader
            title="校准与确认"
            subtitle={`来源：${effectivePreview.source}${effectivePreview.needsReview ? ' · 建议人工复核' : ''}`}
            action={
              effectivePreview.needsReview ? (
                <Badge tone="warn" size="sm">待复核</Badge>
              ) : (
                <Badge tone="up" size="sm">可提交</Badge>
              )
            }
          />
          {effectivePreview.rejected && effectivePreview.rejected.length ? (
            <div className="mt-2 text-caption text-warn">
              后端拒绝的条目：{effectivePreview.rejected.join('、')}
            </div>
          ) : null}
          <div className="mt-3">
            <CalibrationTable
              rows={effectivePreview.entries}
              onChange={updateEntries}
              showConfidence={Boolean(effectivePreview.ocrConfidences)}
              confidences={effectivePreview.ocrConfidences}
            />
          </div>
          <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-3">
            <Input
              label="组合名称"
              size="sm"
              value={label}
              onChange={(e) => setLabel(e.target.value)}
            />
            <Input
              label="总成本（用于权重归一）"
              size="sm"
              type="number"
              value={totalCost}
              onChange={(e) => setTotalCost(e.target.value)}
            />
          </div>
          <div className="mt-4 flex items-center gap-3">
            <Button
              variant="primary"
              size="sm"
              onClick={handleConfirm}
              loading={confirm.isLoading}
              disabled={effectivePreview.entries.length === 0}
            >
              确认创建组合
            </Button>
            {confirmError ? (
              <div className="text-caption text-danger">{confirmError}</div>
            ) : null}
          </div>
        </Card>
      ) : !ocrBusy ? (
        <EmptyState
          title="尚未生成校准预览"
          description="选择模式，填写代码 / CSV / 截图后点击“解析预览”。"
        />
      ) : null}
    </Layout>
  );
}

function adaptPreview(raw: unknown): ParsedPreview {
  const p = raw as {
    preview: FundImportEntry[] | { preview: FundImportEntry[] };
    needs_review?: boolean;
    source?: string;
    rejected?: string[];
  };
  let entries: FundImportEntry[] = [];
  if (Array.isArray(p.preview)) {
    entries = p.preview;
  } else if (p.preview && Array.isArray((p.preview as { preview?: unknown }).preview)) {
    entries = ((p.preview as { preview: FundImportEntry[] }).preview);
  }
  return {
    source: p.source ?? '',
    entries,
    needsReview: Boolean(p.needs_review),
    rejected: p.rejected,
  };
}
