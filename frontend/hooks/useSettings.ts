import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  settingsService,
  type Preferences,
  type RiskProfile,
} from '@/services/settingsService';
import { queryKeys } from '@/lib/queryKeys';

export function useRiskProfile() {
  return useQuery(queryKeys.settings.profile(), settingsService.getProfile, {
    staleTime: 60 * 1000,
  });
}

export function usePreferences() {
  return useQuery(queryKeys.settings.preferences(), settingsService.getPreferences, {
    staleTime: 60 * 1000,
  });
}

export function useUpdateRiskProfile() {
  const qc = useQueryClient();
  return useMutation((profile: RiskProfile) => settingsService.updateProfile(profile), {
    onSuccess: () => qc.invalidateQueries(queryKeys.settings.profile()),
  });
}

export function useUpdatePreferences() {
  const qc = useQueryClient();
  return useMutation((prefs: Preferences) => settingsService.updatePreferences(prefs), {
    onSuccess: () => qc.invalidateQueries(queryKeys.settings.preferences()),
  });
}
