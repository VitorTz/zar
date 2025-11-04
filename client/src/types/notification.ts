

export type NotificationType = 'success' | 'error' | 'info';

export interface NotificationState {
  id: number;
  message: string;
  type: NotificationType;
}