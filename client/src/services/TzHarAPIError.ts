

export class TzHarAPIError extends Error {
  status: number;
  details: any;

  constructor(status: number, message: string, details?: any) {
    super(message);
    this.name = 'TzHarAPIError';
    this.status = status;
    this.details = details;
  }
}