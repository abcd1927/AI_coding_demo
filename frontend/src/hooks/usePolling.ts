import { useEffect, useRef, useCallback } from 'react';
import { useAppContext } from '../context/AppContext';
import { pollStatus } from '../services/api';

const POLL_INTERVAL = 1000;

export function usePolling() {
  const { state, dispatch } = useAppContext();
  const stateRef = useRef(state);

  useEffect(() => {
    stateRef.current = state;
  }, [state]);

  const fetchStatus = useCallback(async () => {
    const current = stateRef.current;
    if (!current.sessionId) return;

    try {
      const afterIndex = current.actions.length > 0
        ? current.actions[current.actions.length - 1].index
        : undefined;

      const response = await pollStatus(current.sessionId, afterIndex);

      const newActions = response.new_actions || response.actions || [];
      if (newActions.length > 0) {
        dispatch({ type: 'ADD_ACTIONS', actions: newActions });
      }

      if (response.status !== current.sessionStatus) {
        dispatch({ type: 'SET_SESSION_STATUS', status: response.status });
      }

      if (response.final_reply && !current.finalReply) {
        dispatch({ type: 'SET_FINAL_REPLY', reply: response.final_reply });
      }
    } catch {
      // 轮询失败静默忽略，下次重试
    }
  }, [dispatch]);

  useEffect(() => {
    if (state.sessionStatus !== 'running') return;

    fetchStatus();
    const timer = setInterval(fetchStatus, POLL_INTERVAL);
    return () => clearInterval(timer);
  }, [state.sessionStatus, fetchStatus]);
}
