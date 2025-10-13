
export function formatApiTimestamp(timestamp: string): string {
  if (!timestamp) return 'N/A';
  
  const parts = timestamp.match(/(\d{2})-(\d{2})-(\d{4}) (\d{2}):(\d{2}):(\d{2})/);
  if (!parts) return timestamp;

  const year = parseInt(parts[3], 10);
  const month = parseInt(parts[2], 10) - 1;
  const day = parseInt(parts[1], 10);
  const hours = parseInt(parts[4], 10);
  const minutes = parseInt(parts[5], 10);
  const seconds = parseInt(parts[6], 10);

  const dateObject = new Date(Date.UTC(year, month, day, hours, minutes, seconds));

  // Formata para data e hora de acordo com o local do usuário
  return dateObject.toLocaleString(undefined, {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
}