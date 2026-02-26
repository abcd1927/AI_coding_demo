import type {
  Channel,
  ChannelMessage,
  ChatResponse,
  ExecutionHistory,
  Order,
  SkillDefinition,
  StatusResponse,
  ToolDefinition,
} from '../types';

const API_BASE = 'http://localhost:8000/api';

async function request<T>(url: string, options?: RequestInit): Promise<T> {
  const response = await fetch(url, options);
  if (!response.ok) {
    let errorMessage = `请求失败 (${response.status})`;
    try {
      const data = await response.json();
      if (data.message) errorMessage = data.message;
    } catch {
      // 非 JSON 响应，使用默认错误消息
    }
    throw new Error(errorMessage);
  }
  const data = await response.json();
  if (data.error) {
    throw new Error(data.message || '请求失败');
  }
  return data as T;
}

export async function sendMessage(message: string): Promise<ChatResponse> {
  return request<ChatResponse>(`${API_BASE}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message }),
  });
}

export async function pollStatus(
  sessionId: string,
  afterIndex?: number,
): Promise<StatusResponse> {
  const params = new URLSearchParams();
  if (afterIndex !== undefined) {
    params.set('after_index', String(afterIndex));
  }
  const query = params.toString();
  const url = `${API_BASE}/status/${sessionId}${query ? `?${query}` : ''}`;
  return request<StatusResponse>(url);
}

export async function getMessages(channel: Channel): Promise<ChannelMessage[]> {
  return request<ChannelMessage[]>(`${API_BASE}/messages/${channel}`);
}

export async function getSkills(): Promise<SkillDefinition[]> {
  return request<SkillDefinition[]>(`${API_BASE}/skills`);
}

export async function getSkillDetail(skillId: string): Promise<SkillDefinition> {
  return request<SkillDefinition>(`${API_BASE}/skills/${skillId}`);
}

export async function getTools(): Promise<ToolDefinition[]> {
  return request<ToolDefinition[]>(`${API_BASE}/tools`);
}

export async function deleteSession(): Promise<void> {
  const response = await fetch(`${API_BASE}/session`, { method: 'DELETE' });
  if (!response.ok) {
    let errorMessage = `清空会话失败 (${response.status})`;
    try {
      const data = await response.json();
      if (data.message) errorMessage = data.message;
    } catch {
      // 非 JSON 响应
    }
    throw new Error(errorMessage);
  }
}

export async function getHistory(): Promise<ExecutionHistory[]> {
  return request<ExecutionHistory[]>(`${API_BASE}/history`);
}

export async function getHistoryDetail(executionId: string): Promise<ExecutionHistory> {
  return request<ExecutionHistory>(`${API_BASE}/history/${executionId}`);
}

export async function getOrders(): Promise<Order[]> {
  return request<Order[]>(`${API_BASE}/orders`);
}

export async function resetOrders(): Promise<Order[]> {
  return request<Order[]>(`${API_BASE}/orders/reset`, { method: 'POST' });
}
