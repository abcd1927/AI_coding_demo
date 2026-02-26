import { useRef, useEffect } from 'react';
import MessagePanel from './MessagePanel';
import ActionLogPanel from './ActionLogPanel';
import { usePolling } from '../../hooks/usePolling';
import { useAppContext } from '../../context/AppContext';
import OrderStatusCard from '../../components/OrderStatusCard/OrderStatusCard';
import type { OrderStatusCardRef } from '../../components/OrderStatusCard/OrderStatusCard';

const DemoView = () => {
  usePolling();
  const { state } = useAppContext();
  const orderCardRef = useRef<OrderStatusCardRef>(null);

  useEffect(() => {
    if (state.sessionStatus === 'completed' || state.sessionStatus === 'error') {
      orderCardRef.current?.refreshOrders();
    }
  }, [state.sessionStatus]);

  return (
    <div style={{ display: 'flex', height: 'calc(100vh - 57px)' }}>
      <div
        style={{
          width: '35%',
          background: '#fff',
          borderRight: '1px solid #f0f0f0',
          display: 'flex',
          flexDirection: 'column',
        }}
      >
        <MessagePanel />
      </div>
      <div
        style={{
          width: '65%',
          background: '#fff',
          display: 'flex',
          flexDirection: 'column',
        }}
      >
        <OrderStatusCard ref={orderCardRef} />
        <ActionLogPanel />
      </div>
    </div>
  );
};

export default DemoView;
