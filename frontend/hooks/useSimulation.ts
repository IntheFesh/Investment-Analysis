import { useMutation, useQuery } from '@tanstack/react-query';
import { simulationService, type SimulationInput } from '@/services/simulationService';
import { queryKeys } from '@/lib/queryKeys';

export function useSimulationPresets() {
  return useQuery(queryKeys.simulation.presets(), simulationService.listPresets, {
    staleTime: 30 * 60 * 1000,
  });
}

export function useSimulationMutation() {
  return useMutation(async (input: SimulationInput) => simulationService.run(input));
}
