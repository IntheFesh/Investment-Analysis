import { useEffect, useMemo, useState } from 'react';
import { Layout } from '@/components/shell/Layout';
import { Card, CardHeader } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Select } from '@/components/ui/Select';
import { Toggle } from '@/components/ui/Toggle';
import { SkeletonChart } from '@/components/ui/Skeleton';
import { ErrorState } from '@/components/ui/ErrorState';
import { Badge } from '@/components/ui/Badge';
import {
  useEnumCatalogue,
  usePreferences,
  useRiskProfile,
  useUpdatePreferences,
  useUpdateRiskProfile,
} from '@/hooks/useSettings';
import { useAppContext } from '@/context/AppContext';
import { ApiError } from '@/lib/apiTypes';
import type { Preferences, RiskProfile } from '@/services/settingsService';

export default function SettingsPage() {
  const { bootstrapData } = useAppContext();
  const profileQuery = useRiskProfile();
  const prefsQuery = usePreferences();
  const enumsQuery = useEnumCatalogue();
  const updateProfile = useUpdateRiskProfile();
  const updatePrefs = useUpdatePreferences();

  const [profile, setProfile] = useState<RiskProfile | null>(null);
  const [prefs, setPrefs] = useState<Preferences | null>(null);
  const [profileError, setProfileError] = useState<string | null>(null);
  const [prefsError, setPrefsError] = useState<string | null>(null);

  useEffect(() => {
    if (profileQuery.data && !profile) setProfile(profileQuery.data.data);
  }, [profileQuery.data, profile]);

  useEffect(() => {
    if (prefsQuery.data && !prefs) setPrefs(prefsQuery.data.data);
  }, [prefsQuery.data, prefs]);

  const enums = enumsQuery.data?.data;

  const riskOptions = useMemo(
    () =>
      enums?.risk_types.map((r) => ({ value: r.id, label: r.label_zh })) ?? [
        { value: 'balanced', label: '平衡' },
      ],
    [enums],
  );

  const horizonOptions = useMemo(
    () =>
      enums?.investment_horizons.map((h) => ({ value: h.id, label: h.label_zh })) ?? [
        { value: 'mid', label: '中期' },
      ],
    [enums],
  );

  const marketOptions = useMemo(
    () =>
      bootstrapData?.markets.map((m) => ({ value: m.id, label: m.label })) ?? [
        { value: 'cn_a', label: 'A股主视角' },
      ],
    [bootstrapData],
  );

  const modeOptions = useMemo(
    () =>
      bootstrapData?.research_modes.map((m) => ({ value: m.id, label: m.label })) ?? [
        { value: 'research', label: '研究模式' },
        { value: 'light', label: '轻量模式' },
      ],
    [bootstrapData],
  );

  const themeOptions = useMemo(
    () =>
      bootstrapData?.themes.map((t) => ({ value: t.id, label: t.label })) ?? [
        { value: 'dark', label: '深色模式' },
        { value: 'light', label: '浅色模式' },
        { value: 'system', label: '跟随系统' },
      ],
    [bootstrapData],
  );

  const liquidityOptions = useMemo(
    () =>
      (enums?.liquidity_preferences ?? ['low', 'mid', 'high']).map((id) => ({
        value: id,
        label: { low: '低换手', mid: '中等', high: '高流动性' }[id] ?? id,
      })),
    [enums],
  );

  const formatOptions = enums?.export_formats ?? ['JSON', 'Markdown', 'CSV', 'PNG'];

  const saveProfile = async () => {
    if (!profile) return;
    setProfileError(null);
    try {
      await updateProfile.mutateAsync(profile);
    } catch (e) {
      setProfileError(e instanceof ApiError ? e.message : '风险画像保存失败');
    }
  };

  const savePrefs = async () => {
    if (!prefs) return;
    setPrefsError(null);
    try {
      await updatePrefs.mutateAsync(prefs);
    } catch (e) {
      setPrefsError(e instanceof ApiError ? e.message : '偏好保存失败');
    }
  };

  const toggleFormat = (f: string) => {
    if (!prefs) return;
    const has = prefs.default_export_format.includes(f);
    setPrefs({
      ...prefs,
      default_export_format: has
        ? prefs.default_export_format.filter((x) => x !== f)
        : [...prefs.default_export_format, f],
    });
  };

  const selectedRisk = enums?.risk_types.find((r) => r.id === profile?.risk_type);

  const meta = profileQuery.data?.meta ?? prefsQuery.data?.meta;

  return (
    <Layout
      title="设置"
      subtitle="风险画像驱动组合诊断/仿真阈值；研究偏好为各模块提供默认视角。保存即写入后端并失效相关缓存。"
      meta={meta}
      showPortfolio={false}
      showMarket={false}
    >
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Card>
          <CardHeader
            title="风险画像"
            subtitle="画像决定组合目标波动区间、回撤容忍与流动性要求。"
            action={
              selectedRisk ? (
                <Badge tone="brand" size="xs">
                  {selectedRisk.label_zh} · 目标波动 {(selectedRisk.target_vol[0] * 100).toFixed(0)}-
                  {(selectedRisk.target_vol[1] * 100).toFixed(0)}%
                </Badge>
              ) : null
            }
          />
          {profileQuery.isLoading && !profile ? (
            <SkeletonChart height={220} />
          ) : profileQuery.error ? (
            <ErrorState error={profileQuery.error} onRetry={() => profileQuery.refetch()} />
          ) : profile ? (
            <div className="mt-3 grid grid-cols-1 md:grid-cols-2 gap-3">
              <Select
                label="风险类型"
                size="sm"
                value={profile.risk_type}
                onChange={(e) => setProfile({ ...profile, risk_type: e.target.value })}
                options={riskOptions}
              />
              <Select
                label="投资期限"
                size="sm"
                value={profile.investment_horizon}
                onChange={(e) => setProfile({ ...profile, investment_horizon: e.target.value })}
                options={horizonOptions}
              />
              <Select
                label="流动性偏好"
                size="sm"
                value={profile.liquidity_preference ?? ''}
                onChange={(e) =>
                  setProfile({ ...profile, liquidity_preference: e.target.value || null })
                }
                options={[{ value: '', label: '未指定' }, ...liquidityOptions]}
              />
              <Input
                label="回撤容忍 (0-0.9)"
                size="sm"
                type="number"
                step="0.01"
                min={0}
                max={0.9}
                value={profile.drawdown_tolerance ?? ''}
                onChange={(e) =>
                  setProfile({
                    ...profile,
                    drawdown_tolerance: e.target.value === '' ? null : Number(e.target.value),
                  })
                }
              />
              <Input
                label="年化收益预期 (-0.5 ~ 1.0)"
                size="sm"
                type="number"
                step="0.01"
                min={-0.5}
                max={1}
                value={profile.return_expectation ?? ''}
                onChange={(e) =>
                  setProfile({
                    ...profile,
                    return_expectation: e.target.value === '' ? null : Number(e.target.value),
                  })
                }
              />
              <Input
                label="问卷评分 (0-100)"
                size="sm"
                type="number"
                min={0}
                max={100}
                value={profile.questionnaire_score ?? ''}
                onChange={(e) =>
                  setProfile({
                    ...profile,
                    questionnaire_score: e.target.value === '' ? null : Number(e.target.value),
                  })
                }
              />
              <Input
                label="防御比例 (0-1)"
                size="sm"
                type="number"
                step="0.05"
                min={0}
                max={1}
                value={profile.defensive_ratio ?? ''}
                onChange={(e) =>
                  setProfile({
                    ...profile,
                    defensive_ratio: e.target.value === '' ? null : Number(e.target.value),
                  })
                }
              />
              <Input
                label="进攻比例 (0-1)"
                size="sm"
                type="number"
                step="0.05"
                min={0}
                max={1}
                value={profile.offensive_ratio ?? ''}
                onChange={(e) =>
                  setProfile({
                    ...profile,
                    offensive_ratio: e.target.value === '' ? null : Number(e.target.value),
                  })
                }
              />
              <div className="md:col-span-2 flex items-center gap-3">
                <Button
                  variant="primary"
                  size="sm"
                  onClick={saveProfile}
                  loading={updateProfile.isLoading}
                >
                  保存风险画像
                </Button>
                {profileError ? <span className="text-caption text-danger">{profileError}</span> : null}
                {selectedRisk ? (
                  <span className="text-caption text-text-tertiary">
                    {selectedRisk.description ?? ''}
                  </span>
                ) : null}
              </div>
            </div>
          ) : null}
        </Card>

        <Card>
          <CardHeader title="研究偏好" subtitle="默认市场视角、研究模式、主题与导出行为。" />
          {prefsQuery.isLoading && !prefs ? (
            <SkeletonChart height={260} />
          ) : prefsQuery.error ? (
            <ErrorState error={prefsQuery.error} onRetry={() => prefsQuery.refetch()} />
          ) : prefs ? (
            <div className="mt-3 grid grid-cols-1 md:grid-cols-2 gap-3">
              <Select
                label="默认市场"
                size="sm"
                value={prefs.market_view}
                onChange={(e) => setPrefs({ ...prefs, market_view: e.target.value })}
                options={marketOptions}
              />
              <Select
                label="研究模式"
                size="sm"
                value={prefs.research_mode}
                onChange={(e) => setPrefs({ ...prefs, research_mode: e.target.value })}
                options={modeOptions}
              />
              <Select
                label="主题"
                size="sm"
                value={prefs.theme}
                onChange={(e) => setPrefs({ ...prefs, theme: e.target.value })}
                options={themeOptions}
              />

              <div className="md:col-span-2">
                <div className="text-caption text-text-tertiary uppercase tracking-wide mb-2">
                  默认导出格式
                </div>
                <div className="flex flex-wrap gap-3">
                  {formatOptions.map((f) => (
                    <Toggle
                      key={f}
                      checked={prefs.default_export_format.includes(f)}
                      onChange={() => toggleFormat(f)}
                      label={f}
                    />
                  ))}
                </div>
              </div>

              <Toggle
                checked={prefs.include_global_events}
                onChange={() =>
                  setPrefs({ ...prefs, include_global_events: !prefs.include_global_events })
                }
                label="导出附带全球事件"
              />
              <Toggle
                checked={prefs.include_charts_in_export}
                onChange={() =>
                  setPrefs({
                    ...prefs,
                    include_charts_in_export: !prefs.include_charts_in_export,
                  })
                }
                label="导出附带静态图表"
              />

              <div className="md:col-span-2 flex items-center gap-3">
                <Button
                  variant="primary"
                  size="sm"
                  onClick={savePrefs}
                  loading={updatePrefs.isLoading}
                >
                  保存偏好
                </Button>
                {prefsError ? <span className="text-caption text-danger">{prefsError}</span> : null}
              </div>
            </div>
          ) : null}
        </Card>
      </div>
    </Layout>
  );
}
