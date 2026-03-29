import api from './client';

export interface VerificationResult {
  plate_number: string;
  is_authorized: boolean;
  booking_id?: string;
  driver_id?: string;
  status?: string;
  departure_time?: string;
  journey_window_end?: string;
  segments?: string[];
  message: string;
  source: 'cache' | 'database' | 'not_found';
  checked_at: string;
}

// GET /verify/:plate
export const verifyPlate = (plate: string) =>
  api.get<VerificationResult>(`/verify/${encodeURIComponent(plate)}`);
