import { createContext, useContext, useReducer, type ReactNode } from 'react';
import type { ActionLogEntry, Channel, ChannelMessage, SessionStatus } from '../types';

export interface AppState {
  sessionId: string | null;
  sessionStatus: SessionStatus;
  actions: ActionLogEntry[];
  currentChannel: Channel;
  unreadChannels: Set<string>;
  messages: Record<Channel, ChannelMessage[]>;
  finalReply: string | null;
}

export type AppAction =
  | { type: 'SET_SESSION'; sessionId: string }
  | { type: 'SET_SESSION_STATUS'; status: SessionStatus }
  | { type: 'ADD_ACTIONS'; actions: ActionLogEntry[] }
  | { type: 'SET_CHANNEL'; channel: Channel }
  | { type: 'MARK_UNREAD'; channel: string }
  | { type: 'CLEAR_UNREAD'; channel: string }
  | { type: 'SET_MESSAGES'; channel: Channel; messages: ChannelMessage[] }
  | { type: 'SET_FINAL_REPLY'; reply: string }
  | { type: 'RESET' };

const initialState: AppState = {
  sessionId: null,
  sessionStatus: 'idle',
  actions: [],
  currentChannel: 'chat',
  unreadChannels: new Set(),
  messages: { chat: [], downstream: [], upstream: [] },
  finalReply: null,
};

function appReducer(state: AppState, action: AppAction): AppState {
  switch (action.type) {
    case 'SET_SESSION':
      return { ...state, sessionId: action.sessionId };
    case 'SET_SESSION_STATUS':
      return { ...state, sessionStatus: action.status };
    case 'ADD_ACTIONS':
      return { ...state, actions: [...state.actions, ...action.actions] };
    case 'SET_CHANNEL':
      return { ...state, currentChannel: action.channel };
    case 'MARK_UNREAD': {
      const next = new Set(state.unreadChannels);
      next.add(action.channel);
      return { ...state, unreadChannels: next };
    }
    case 'CLEAR_UNREAD': {
      const next = new Set(state.unreadChannels);
      next.delete(action.channel);
      return { ...state, unreadChannels: next };
    }
    case 'SET_MESSAGES':
      return {
        ...state,
        messages: { ...state.messages, [action.channel]: action.messages },
      };
    case 'SET_FINAL_REPLY':
      return { ...state, finalReply: action.reply };
    case 'RESET':
      return { ...initialState };
    default:
      return state;
  }
}

interface AppContextValue {
  state: AppState;
  dispatch: React.Dispatch<AppAction>;
}

const AppContext = createContext<AppContextValue | null>(null);

export function AppProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(appReducer, initialState);
  return (
    <AppContext.Provider value={{ state, dispatch }}>
      {children}
    </AppContext.Provider>
  );
}

// eslint-disable-next-line react-refresh/only-export-components
export function useAppContext(): AppContextValue {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useAppContext must be used within AppProvider');
  }
  return context;
}
