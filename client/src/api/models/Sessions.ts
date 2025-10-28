

export type Sessions = {

    user_id: string
    issued_at: Date
    expires_at: Date
    revoked: boolean
    revoked_at: Date
    device_name: string,
    device_ip: string
    user_agent: string
    last_used_at: Date
    
}