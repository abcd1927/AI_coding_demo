import MessagePanel from './MessagePanel';
import ActionLogPanel from './ActionLogPanel';

const DemoView = () => {
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
        <ActionLogPanel />
      </div>
    </div>
  );
};

export default DemoView;
