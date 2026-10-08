export type Item = {
  id: string;
  en: string;
  hi: string;
  group: string;
  icon: string;
  check_clean: boolean;
};
export type Row = {
  id: string;
  en: string;
  hi: string;
  quantity: number;
  answers: { clean?: string };
};
export type RequestRecord = {
  id: string;
  items: Row[];
  language: string;
  status: string;
  version: number;
  expires_at: number;
  pickup_until?: number;
  events: { action: string; source: string; at: number }[];
  token?: string;
};
export type Route = {
  stream: string;
  eligible: boolean;
  reason: string;
  reason_hi: string;
};
