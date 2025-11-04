

export interface User {
  id: string;
  email: string;
  last_login_at?: string | null;
  created_at: string;
}

export interface UserSession {
  user_id: string;
  issued_at: string;
  expires_at: string;
  revoked: boolean;
  revoked_at?: string | null;
  device_name?: string | null;
  device_ip: string;
  user_agent?: string | null;
  last_used_at: string;
}