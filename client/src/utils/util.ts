

export function normalizeTimestamp(timestamp: string): string {
    const parts = timestamp.match(/(\d{2})-(\d{2})-(\d{4}) (\d{2}):(\d{2}):(\d{2})/);
    if (!parts) return timestamp;

    const day = parseInt(parts[1], 10);
    const month = parseInt(parts[2], 10) - 1;
    const year = parseInt(parts[3], 10);
    const hours = parseInt(parts[4], 10);
    const minutes = parseInt(parts[5], 10);
    const seconds = parseInt(parts[6], 10);
    
    const utcDate = new Date(Date.UTC(year, month, day, hours, minutes, seconds));
    
    return utcDate.toUTCString();
}
