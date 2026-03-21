const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export interface TunnelMessage {
  id: string;
  timestamp: string;
  session_id: string;
  protocol: string;
  sender_ip: string;
  payload: string;
  chunks_received: number;
  decode_time_ms: number;
}

export interface ReceiveStatus {
  listening: boolean;
  port: number;
  lan_ip: string;
  shareable_url: string;
}

export interface ReceiveStartResponse {
  status: string;
  port: number;
  lan_ip: string;
  shareable_url: string;
}

export const startReceiving = async (port: number): Promise<ReceiveStartResponse> => {
  const response = await fetch(`${API_BASE}/api/tunnel/receive/start`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ port }),
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to start receiver');
  }
  return response.json();
};

export const stopReceiving = async (): Promise<void> => {
  const response = await fetch(`${API_BASE}/api/tunnel/receive/stop`, {
    method: 'POST',
  });
  if (!response.ok) throw new Error('Failed to stop receiver');
};

export const getMessages = async (): Promise<{ messages: TunnelMessage[]; count: number }> => {
  const response = await fetch(`${API_BASE}/api/tunnel/receive/messages`);
  if (!response.ok) throw new Error('Failed to fetch messages');
  return response.json();
};

export const getReceiveStatus = async (): Promise<ReceiveStatus> => {
  const response = await fetch(`${API_BASE}/api/tunnel/receive/status`);
  if (!response.ok) throw new Error('Failed to get receiver status');
  return response.json();
};

export const clearMessages = async (): Promise<void> => {
  const response = await fetch(`${API_BASE}/api/tunnel/receive/messages`, {
    method: 'DELETE',
  });
  if (!response.ok) throw new Error('Failed to clear messages');
};
