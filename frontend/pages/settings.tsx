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
  useRiskProfile,
  usePreferences,
  useUpdateRiskProfile,
  useUpdatePreferences,
} from '@/hooks/useSettings';
import { useAppContext } from '@/context/AppContext';
import { ApiError } from '@/lib/apiTypes';
import type { RiskProfile, Preferences } from '@/services/settingsService';

const RISK_TYPES = [
  { value: 'conservative', label: '稳健' },
  { value: 'balanced', label: '平衡' },
  { value: 'growth', label: '进取' },
  { value: 'aggressive', label: '激进' },
];

const HORIZONS = [
  { value: '短期', label: '短期（< 1 年）' },
  { value: '中期', label: '中期（1-3 年）' },
  { value: '长期', label: '长期（> 3 年）' },
];

const EXPORT_FORMATS = ['JSON', 'Markdown', 'CSV', 'PNG'];

export default function SettingsPage() {
  const { bootstrapData } = useAppContext();
  const profileQuery = useRiskProfile();
  const prefsQuery = usePreferences();
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

  const marketOptions = useMemo(
    () =>
      bootstrapData?.markets.map((m) => ({ value: m.id, label: m.label })) ?? [
        { value: 'A股', label: 'A股' },
      ],
    [bootstrapData]
  );

  const timeOptions = useMemo(
    () =>
      bootstrapData?.time_windows.map((w) => ({ value: w, label: w })) ?? [
        { value: '20D', label: '20D' },
      ],
    [bootstrapData]
  );

  const modeOptions = useMemo(
    () =>
      bootstrapData?.research_modes.map((m) => ({ value: m.id, label: m.label })) ?? [
        { value: 'research', label: '研究模式' },
        { value: 'light', label: '轻量模式' },
      ],
    [bootstrapData]
  );

  const themeOptions = useMemo(
    () =>
      bootstrapData?.themes.map((t) => ({ value: t.id, label: t.label })) ?? [
        { value: 'system', label: '跟随系统' },
        { value: 'dark', label: '暗色' },
        { value: 'light', label: '明亮' },
      ],
    [bootstrapData]
  );

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

  const meta = profileQuery.data?.meta ?? prefsQuery.data?.meta;

  return (
    <Layout
      title="设置"
      subtitle="风险画像、研究默认视图与导出偏好——写入后端并联动全局 Context。"
      meta={meta}
      showPortfolio={false}
    >
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Card>
          <CardHeader
            title="风险画像"
            subtitle="影响组合诊断与推荐的基准阈值。"
            action={
              profile ? (
                <Badge tone="brand" size="xs">
                  {RISK_TYPES.find((r) => r.value === profile.risk_type)?.label ?? profile.risk_type}
                </Badge>
              ) : null
            }
          />
          {profileQuery.isLoading && !profile ? (
            <SkeletonChart height={200} />
          ) : profileQuery.error ? (
            <ErrorState error={profileQuery.error} onRetry={() => profileQuery.refetch()} />
          ) : profile ? (
            <div className="mt-3 grid grid-cols-1 md:grid-cols-2 gap-3">
              <Select
                label="风险类型"
                size="sm"
                value={profile.risk_type}
                onChange={(e) => setProfile({ ...profile, risk_type: e.target.value })}
                options={RISK_TYPES}
              />
              <Select
                label="投资期限"
                size="sm"
                value={profile.investment_horizon}
                onChange={(e) =>
                  setProfile({ ...profile, investment_horizon: e.target.value })
                }
                options={HORIZONS}
              />
              <Input
                label="防守仓位 (%)"
                size="sm"
                type="number"
                min={0}
                max={100}
                value={profile.defensive_ratio ?? ''}
                onChange={(e) =>
                  setProfile({
                    ...profile,
                    defensive_ratio: e.target.value === '' ? null : Number(e.target.value),
                  })
                }
              />
              <Input
                label="进攻仓位 (%)"
                size="sm"
                type="number"
                min={0}
                max={100}
                value={profile.offensive_ratio ?? ''}
                onChange={(e) =>
                  setProfile({
                    ...profile,
                    offensive_ratio: e.target.value === '' ? null : Number(e.target.value),
                  })
                }
              />
              <Input
                label="问卷评分"
                size="sm"
                type="number"
                min={0}
                max={100}
                value={profile.questionnaire_score ?? ''}
                onChange={(e) =>
                  setProfile({
                    ...profile,
                    questionnaire_score:
                      e.target.value === '' ? null : Number(e.target.value),
                  })
                }
              />
              <div className="flex items-end">
                <Button
                  variant="primary"
                  size="sm"
                  onClick={saveProfile}
                  loading={updateProfile.isLoading}
                >
                  保存风险画像
                </Button>
              </div>
              {profileError ? (
                <div className="md:col-span-2 text-caption text-danger">{profileError}</div>
              ) : null}
            </div>
          ) : null}
        </Card>

        <Card>
          <CardHeader title="研究偏好" subtitle="默认市场视角、时间窗、研究模式与主题。" />
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
                label="默认时间窗"
                size="sm"
                value={prefs.time_window}
                onChange={(e) => setPrefs({ ...prefs, time_window: e.target.value })}
                options={timeOptions}
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
                  {EXPORT_FORMATS.map((f) => (
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
                {prefsError ? (
                  <div className="text-caption text-danger">{prefsError}</div>
                ) : null}
              </div>
            </div>
          ) : null}
        </Card>
      </div>
    </Layout>
  );
}
