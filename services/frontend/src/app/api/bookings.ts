import api from './client';

export interface BookingPayload {
  origin_lat: number;
  origin_lng: number;
  destination_lat: number;
  destination_lng: number;
  departure_time: string; // ISO string
  plate_number?: string;
}

export interface BookingOut {
  booking_id: string;
  status: 'CONFIRMED' | 'REJECTED' | 'PENDING' | 'CANCELLED' | 'SAGA_IN_PROGRESS';
  estimated_duration_minutes?: number;
  created_at: string;
  segments?: { segment_id: string; region: string }[];
}

export interface RoutePreviewPayload {
  origin_lat: number;
  origin_lng: number;
  destination_lat: number;
  destination_lng: number;
  departure_time: string;
}

export interface RoutePreviewSegment {
  segment_id: string;
  segment_name: string;
  region: string;
  distance_km: number;
  duration_minutes: number;
  slot_start: string;
  slot_end: string;
  start_lat?: number;
  start_lng?: number;
  end_lat?: number;
  end_lng?: number;
}

export interface RoutePreviewOut {
  route_available: boolean;
  reason?: string | null;
  estimated_duration_minutes?: number | null;
  region_chain: string[];
  segments: RoutePreviewSegment[];
}

// POST /bookings
export const createBooking = (data: BookingPayload) =>
  api.post<BookingOut>('/bookings', data);

export const previewRoute = (data: RoutePreviewPayload) =>
  api.post<RoutePreviewOut>('/bookings/preview-route', data);

// GET /bookings/my/journeys
export const getMyJourneys = () =>
  api.get<BookingOut[]>('/bookings/my/journeys');

// GET /bookings/:id
export const getBooking = (id: string) =>
  api.get<BookingOut>(`/bookings/${id}`);

// DELETE /bookings/:id
export const cancelBooking = (id: string) =>
  api.delete<BookingOut>(`/bookings/${id}`);