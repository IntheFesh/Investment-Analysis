import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import axios from 'axios';
import Layout from '@/components/Layout';

interface RiskProfile {
  risk_type: string;
  investment_horizon: string;
  defensive_ratio?: number;
  offensive_ratio?: number;
}
interface Preferences {
  market_view: string;
  time_window: string;
  research_mode: string;
  default_export_format: string[];
}

export default function SettingsPage() {
  const queryClient = useQueryClient();
  const { data: profileData } = useQuery(['settings-profile'], async () => {
    const res = await axios.get('/api/v1/settings/profile');
    return res.data.data as RiskProfile;
  });
  const { data: prefsData } = useQuery(['settings-preferences'], async () => {
    const res = await axios.get('/api/v1/settings/preferences');
    return res.data.data as Preferences;
  });
  const profileMutation = useMutation(
    async (profile: RiskProfile) => {
      await axios.put('/api/v1/settings/profile', profile);
    },
    {
      onSuccess: () => {
        queryClient.invalidateQueries(['settings-profile']);
        alert('风险画像更新成功');
      },
    }
  );
  const prefsMutation = useMutation(
    async (prefs: Preferences) => {
      await axios.put('/api/v1/settings/preferences', prefs);
    },
    {
      onSuccess: () => {
        queryClient.invalidateQueries(['settings-preferences']);
        alert('偏好设置更新成功');
      },
    }
  );
  // Local form states; initialize from fetched data when available
  const [profileForm, setProfileForm] = useState<RiskProfile | null>(null);
  const [prefsForm, setPrefsForm] = useState<Preferences | null>(null);
  // Populate forms when data loads
  useState(() => {
    if (profileData && !profileForm) {
      setProfileForm(profileData);
    }
    if (prefsData && !prefsForm) {
      setPrefsForm(prefsData);
    }
  });
  const riskTypes = ['保守型', '平衡型', '进攻型'];
  const horizons = ['1Y', '3Y', '5Y', '10Y'];
  const marketViews = ['A股主视角', '港股补充视角', '全球联动视角'];
  const timeWindows = ['5D', '20D', '60D', '120D'];
  const researchModes = ['轻量模式', '研究模式'];
  const formats = ['JSON', 'Markdown', 'CSV', 'PNG'];
  const handleProfileSubmit = () => {
    if (profileForm) profileMutation.mutate(profileForm);
  };
  const handlePrefsSubmit = () => {
    if (prefsForm) prefsMutation.mutate(prefsForm);
  };
  return (
    <Layout>
      <h1 className="text-2xl font-bold mb-4">设置</h1>
      {(!profileData || !prefsData || !profileForm || !prefsForm) && <p>加载中…</p>}
      {profileData && prefsData && profileForm && prefsForm && (
        <div className="space-y-8">
          <section>
            <h2 className="text-xl font-semibold mb-2">风险画像设置</h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm mb-1">风险类型</label>
                <select
                  className="border rounded-md px-2 py-1 dark:bg-gray-700 dark:border-gray-600"
                  value={profileForm.risk_type}
                  onChange={(e) => setProfileForm({ ...profileForm, risk_type: e.target.value })}
                >
                  {riskTypes.map((t) => (
                    <option key={t} value={t}>
                      {t}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm mb-1">投资周期</label>
                <select
                  className="border rounded-md px-2 py-1 dark:bg-gray-700 dark:border-gray-600"
                  value={profileForm.investment_horizon}
                  onChange={(e) => setProfileForm({ ...profileForm, investment_horizon: e.target.value })}
                >
                  {horizons.map((h) => (
                    <option key={h} value={h}>
                      {h}
                    </option>
                  ))}
                </select>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm mb-1">防御型比例</label>
                  <input
                    type="number"
                    step="0.01"
                    className="border rounded-md px-2 py-1 w-full dark:bg-gray-700 dark:border-gray-600"
                    value={profileForm.defensive_ratio ?? 0}
                    onChange={(e) =>
                      setProfileForm({ ...profileForm, defensive_ratio: parseFloat(e.target.value) })
                    }
                  />
                </div>
                <div>
                  <label className="block text-sm mb-1">进攻型比例</label>
                  <input
                    type="number"
                    step="0.01"
                    className="border rounded-md px-2 py-1 w-full dark:bg-gray-700 dark:border-gray-600"
                    value={profileForm.offensive_ratio ?? 0}
                    onChange={(e) =>
                      setProfileForm({ ...profileForm, offensive_ratio: parseFloat(e.target.value) })
                    }
                  />
                </div>
              </div>
              <button
                onClick={handleProfileSubmit}
                disabled={profileMutation.isLoading}
                className="px-4 py-2 text-sm font-medium rounded-md bg-indigo-600 text-white hover:bg-indigo-700 disabled:opacity-50"
              >
                {profileMutation.isLoading ? '保存中…' : '保存风险画像'}
              </button>
            </div>
          </section>
          <section>
            <h2 className="text-xl font-semibold mb-2">偏好设置</h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm mb-1">默认市场视角</label>
                <select
                  className="border rounded-md px-2 py-1 dark:bg-gray-700 dark:border-gray-600"
                  value={prefsForm.market_view}
                  onChange={(e) => setPrefsForm({ ...prefsForm, market_view: e.target.value })}
                >
                  {marketViews.map((m) => (
                    <option key={m} value={m}>
                      {m}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm mb-1">默认时间窗口</label>
                <select
                  className="border rounded-md px-2 py-1 dark:bg-gray-700 dark:border-gray-600"
                  value={prefsForm.time_window}
                  onChange={(e) => setPrefsForm({ ...prefsForm, time_window: e.target.value })}
                >
                  {timeWindows.map((tw) => (
                    <option key={tw} value={tw}>
                      {tw}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm mb-1">默认研究模式</label>
                <select
                  className="border rounded-md px-2 py-1 dark:bg-gray-700 dark:border-gray-600"
                  value={prefsForm.research_mode}
                  onChange={(e) => setPrefsForm({ ...prefsForm, research_mode: e.target.value })}
                >
                  {researchModes.map((rm) => (
                    <option key={rm} value={rm}>
                      {rm}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm mb-1">默认导出格式</label>
                <div className="flex flex-wrap gap-3">
                  {formats.map((fmt) => {
                    const checked = prefsForm.default_export_format.includes(fmt);
                    return (
                      <label key={fmt} className="flex items-center space-x-1">
                        <input
                          type="checkbox"
                          checked={checked}
                          onChange={(e) => {
                            let next: string[];
                            if (e.target.checked) {
                              next = [...prefsForm.default_export_format, fmt];
                            } else {
                              next = prefsForm.default_export_format.filter((f) => f !== fmt);
                            }
                            setPrefsForm({ ...prefsForm, default_export_format: next });
                          }}
                          className="form-checkbox h-4 w-4 text-indigo-600"
                        />
                        <span>{fmt}</span>
                      </label>
                    );
                  })}
                </div>
              </div>
              <button
                onClick={handlePrefsSubmit}
                disabled={prefsMutation.isLoading}
                className="px-4 py-2 text-sm font-medium rounded-md bg-indigo-600 text-white hover:bg-indigo-700 disabled:opacity-50"
              >
                {prefsMutation.isLoading ? '保存中…' : '保存偏好'}
              </button>
            </div>
          </section>
        </div>
      )}
    </Layout>
  );
}