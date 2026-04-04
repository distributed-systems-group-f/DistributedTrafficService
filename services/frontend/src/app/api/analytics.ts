import api from './client';

export interface DashboardStats {
  total_bookings: number;
  confirmed: number;
  cancelled: number;
  failed: number;
  by_region: Record<string, number>;
  last_updated: string;
}

export interface CapacityReport {
  segment_id: string;
  region: string;
  slot_start: string;
  booked_count: number;
  max_capacity: number;
  utilization_pct: number;
}

export interface UsageReport {
  total_events: number;
  last_24h_events: number;
  by_event_type: Record<string, number>;
  by_region: Record<string, number>;
  generated_at: string;
}

export const getDashboard = () => api.get<DashboardStats>('/analytics/dashboard');

export const getCapacityReport = () =>
  api.get<CapacityReport[]>('/analytics/reports/capacity');

export const getUsageReport = () =>
  api.get<UsageReport>('/analytics/reports/usage');