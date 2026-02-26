import { useEffect, useRef, useCallback } from 'react';
import { useAppContext } from '../context/AppContext';
import { getMessages } from '../services/api';
import type { Channel } from '../types';

const CHANNELS: Channel[] = ['chat', 'downstream', 'upstream'];
const POLL_INTERVAL = 1000;

export function useMessagePolling() {
  const { state, dispatch } = useAppContext();
  const stateRef = useRef(state);

  useEffect(() => {
    stateRef.current = state;
  }, [state]);

  const fetchMessages = useCallback(async () => {
    for (const channel of CHANNELS) {
      try {
        const messages = await getMessages(channel);
        const current = stateRef.current;
        const oldCount = current.messages[channel].length;
        dispatch({ type: 'SET_MESSAGES', channel, messages });
        if (messages.length > oldCount && channel !== current.currentChannel) {
          dispatch({ type: 'MARK_UNREAD', channel });
        }
      } catch {
        // 轮询失败静默忽略，下次重试
      }
    }
  }, [dispatch]);

  useEffect(() => {
    if (state.sessionStatus !== 'running' && state.sessionStatus !== 'completed') return;

    fetchMessages();

    if (state.sessionStatus === 'running') {
      const timer = setInterval(fetchMessages, POLL_INTERVAL);
      return () => clearInterval(timer);
    }
  }, [state.sessionStatus, fetchMessages]);
}
