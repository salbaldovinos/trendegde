import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiGet, apiPost, apiPatch, apiDelete, apiPut } from "@/lib/api-client";
import {
  mockExecutionPositions,
  mockOrders,
  mockSignals,
  mockCircuitBreaker,
  mockRiskSettings,
  mockBrokerStatus,
} from "@/lib/mock-data";
import type {
  ExecutionPosition,
  Order,
  Signal,
  CircuitBreakerStatus,
  RiskSettings,
  BrokerStatus,
  ManualTradeFormData,
} from "@/types/execution";

const useMocks = process.env.NEXT_PUBLIC_USE_MOCKS === "true";

export function useExecutionPositions(status?: "OPEN" | "CLOSED") {
  return useQuery({
    queryKey: ["execution-positions", status],
    queryFn: () => {
      if (useMocks) {
        const filtered = status
          ? mockExecutionPositions.filter((p) => p.status === status)
          : mockExecutionPositions;
        return Promise.resolve(filtered);
      }
      const params = status ? `?status=${status}` : "";
      return apiGet<{ positions: ExecutionPosition[] }>(`/positions${params}`).then(
        (r) => r.positions
      );
    },
    staleTime: 10 * 1000,
  });
}

export function useOrders(status?: string) {
  return useQuery({
    queryKey: ["orders", status],
    queryFn: () => {
      if (useMocks) {
        const filtered = status
          ? mockOrders.filter((o) => o.status === status)
          : mockOrders;
        return Promise.resolve(filtered);
      }
      const params = status ? `?status=${status}` : "";
      return apiGet<{ orders: Order[] }>(`/orders${params}`).then(
        (r) => r.orders
      );
    },
    staleTime: 10 * 1000,
  });
}

export function useSignals(status?: string) {
  return useQuery({
    queryKey: ["signals", status],
    queryFn: () => {
      if (useMocks) {
        const filtered = status
          ? mockSignals.filter((s) => s.status === status)
          : mockSignals;
        return Promise.resolve(filtered);
      }
      const params = status ? `?status=${status}` : "";
      return apiGet<{ signals: Signal[] }>(`/signals${params}`).then(
        (r) => r.signals
      );
    },
    staleTime: 10 * 1000,
  });
}

export function useCircuitBreaker() {
  return useQuery({
    queryKey: ["circuit-breaker"],
    queryFn: () =>
      useMocks
        ? Promise.resolve(mockCircuitBreaker)
        : apiGet<CircuitBreakerStatus>("/circuit-breaker/status"),
    staleTime: 15 * 1000,
  });
}

export function useRiskSettings() {
  return useQuery({
    queryKey: ["risk-settings"],
    queryFn: () =>
      useMocks
        ? Promise.resolve(mockRiskSettings)
        : apiGet<RiskSettings>("/settings/risk"),
    staleTime: 60 * 1000,
  });
}

export function useBrokerStatus() {
  return useQuery({
    queryKey: ["broker-status"],
    queryFn: () =>
      useMocks
        ? Promise.resolve(mockBrokerStatus)
        : apiGet<BrokerStatus>("/broker-connections/status"),
    staleTime: 30 * 1000,
  });
}

export function useSubmitSignal() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: ManualTradeFormData) =>
      useMocks
        ? Promise.resolve({ id: `sig-manual-${Date.now()}` })
        : apiPost("/signals/manual", data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["signals"] });
    },
  });
}

export function useClosePosition() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (positionId: string) =>
      useMocks
        ? Promise.resolve({ success: true })
        : apiPost(`/positions/${positionId}/close`, {}),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["execution-positions"] });
      queryClient.invalidateQueries({ queryKey: ["orders"] });
    },
  });
}

export function useFlattenAll() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () =>
      useMocks
        ? Promise.resolve({ closed: 5 })
        : apiPost("/positions/flatten-all", {}),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["execution-positions"] });
      queryClient.invalidateQueries({ queryKey: ["orders"] });
    },
  });
}

export function useCancelOrder() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (orderId: string) =>
      useMocks
        ? Promise.resolve({ success: true })
        : apiDelete(`/orders/${orderId}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["orders"] });
    },
  });
}

export function useModifyOrder() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ orderId, data }: { orderId: string; data: Partial<Order> }) =>
      useMocks
        ? Promise.resolve({ success: true })
        : apiPatch(`/orders/${orderId}`, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["orders"] });
    },
  });
}

export function useUpdateRiskSettings() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: Partial<RiskSettings>) =>
      useMocks
        ? Promise.resolve(data)
        : apiPut("/settings/risk", data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["risk-settings"] });
    },
  });
}

export function useRejectSignal() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (signalId: string) =>
      useMocks
        ? Promise.resolve({ status: "CANCELLED" })
        : apiPatch(`/signals/${signalId}/cancel`, {}),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["signals"] });
    },
  });
}

export function useResetCircuitBreaker() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () =>
      useMocks
        ? Promise.resolve({ state: "CLOSED" })
        : apiPost("/circuit-breaker/reset", {}),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["circuit-breaker"] });
    },
  });
}
