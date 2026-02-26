// 枚举类型 — 使用 string union type
export type ActionType =
  | 'intent_recognition'
  | 'skill_loaded'
  | 'tool_call'
  | 'waiting'
  | 'message_sent'
  | 'completed';

export type ActionStatus = 'running' | 'success' | 'error';

export type SessionStatus = 'idle' | 'running' | 'completed' | 'error';

export type Channel = 'chat' | 'downstream' | 'upstream';

// 核心数据模型
export interface ActionLogEntry {
  index: number;
  action_type: ActionType;
  title: string;
  summary: string;
  status: ActionStatus;
  detail: Record<string, unknown> | null;
  timestamp: string;
}

export interface ChannelMessage {
  channel: Channel;
  sender: string;
  content: string;
  timestamp: string;
}

export interface AgentExecutionState {
  session_id: string;
  status: SessionStatus;
  actions: ActionLogEntry[];
  final_reply: string | null;
  unread_channels: string[];
}

// API 专用模型
export interface SkillDefinition {
  skill_id: string;
  name: string;
  description: string;
  content: string;
}

export interface ToolDefinition {
  name: string;
  description: string;
  parameters: Record<string, unknown>;
}

export interface ExecutionHistory {
  execution_id: string;
  trigger_message: string;
  skill_name: string | null;
  status: SessionStatus;
  actions: ActionLogEntry[];
  created_at: string;
}

// 请求/响应模型
export interface ChatRequest {
  message: string;
}

export interface ChatResponse {
  session_id: string;
}

export interface StatusResponse {
  session_id: string;
  status: SessionStatus;
  new_actions?: ActionLogEntry[];
  actions?: ActionLogEntry[];
  unread_channels: string[];
  final_reply: string | null;
}

export interface ErrorResponse {
  error: true;
  error_type: string;
  message: string;
}

export interface Order {
  order_id: string;
  guest_name: string;
  hotel_name: string;
  status: string;
}
