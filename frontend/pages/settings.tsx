import { useEffect, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import Layout from '@/components/Layout';
import QueryErrorState from '@/components/QueryErrorState';
import { settingsService } from '@/services/settingsService';

interface RiskProfile { risk_type: string; investment_horizon: string }
interface Preferences { market_view: string; time_window: string; research_mode: string; default_export_format: string[] }

export default function SettingsPage() {
  const queryClient = useQueryClient();
  const profileQuery = useQuery(['settings-profile'], settingsService.getProfile, { staleTime: 10 * 60 * 1000 });
  const prefsQuery = useQuery(['settings-preferences'], settingsService.getPreferences, { staleTime: 10 * 60 * 1000 });

  const [profileForm, setProfileForm] = useState<RiskProfile | null>(null);
  const [prefsForm, setPrefsForm] = useState<Preferences | null>(null);

  useEffect(() => { if (profileQuery.data && !profileForm) setProfileForm(profileQuery.data as RiskProfile); }, [profileQuery.data, profileForm]);
  useEffect(() => { if (prefsQuery.data && !prefsForm) setPrefsForm(prefsQuery.data as Preferences); }, [prefsQuery.data, prefsForm]);

  const profileMutation = useMutation((payload: RiskProfile) => settingsService.updateProfile(payload), {
    onSuccess: () => queryClient.invalidateQueries(['settings-profile']),
  });
  const prefsMutation = useMutation((payload: Preferences) => settingsService.updatePreferences(payload), {
    onSuccess: () => queryClient.invalidateQueries(['settings-preferences']),
  });

  return (
    <Layout>
      <h1 className="text-2xl font-bold mb-4">设置</h1>
      {(profileQuery.isLoading || prefsQuery.isLoading) && <p>加载中…</p>}
      {profileQuery.error && <QueryErrorState error={profileQuery.error} />}
      {prefsQuery.error && <QueryErrorState error={prefsQuery.error} />}
      {profileForm && (
        <div className="space-y-3">
          <input className="border px-2 py-1" value={profileForm.risk_type} onChange={(e) => setProfileForm({ ...profileForm, risk_type: e.target.value })} />
          <button className="px-3 py-2 bg-indigo-600 text-white rounded" onClick={() => profileMutation.mutate(profileForm)}>保存风险画像</button>
        </div>
      )}
      {prefsForm && (
        <div className="space-y-3 mt-4">
          <input className="border px-2 py-1" value={prefsForm.market_view} onChange={(e) => setPrefsForm({ ...prefsForm, market_view: e.target.value })} />
          <button className="px-3 py-2 bg-indigo-600 text-white rounded" onClick={() => prefsMutation.mutate(prefsForm)}>保存偏好</button>
        </div>
      )}
    </Layout>
  );
}
