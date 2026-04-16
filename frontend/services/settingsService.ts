import { apiClient, unwrapApiData } from '@/lib/apiClient';

export const settingsService = {
  async getProfile() {
    const res = await apiClient.get('/api/v1/settings/profile');
    return unwrapApiData(res.data);
  },
  async getPreferences() {
    const res = await apiClient.get('/api/v1/settings/preferences');
    return unwrapApiData(res.data);
  },
  async updateProfile(profile: unknown) {
    const res = await apiClient.put('/api/v1/settings/profile', profile);
    return unwrapApiData(res.data);
  },
  async updatePreferences(prefs: unknown) {
    const res = await apiClient.put('/api/v1/settings/preferences', prefs);
    return unwrapApiData(res.data);
  },
};
