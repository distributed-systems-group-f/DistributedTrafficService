import api from './client';

export interface NotificationOut {
  id: string;
  user_id: string;
  message: string;
  channel: string;
  sent_at: string;
  read: boolean;
}

export const getNotifications = (userId: string, limit: number = 20) =>
  api.get<NotificationOut[]>(`/notifications/${userId}?limit=${limit}`);