import { useState } from 'react';
import { BrowserRouter, Routes, Route, useNavigate, useLocation } from 'react-router-dom';
import { Layout, Menu, Button, Popconfirm, message } from 'antd';
import { AppProvider, useAppContext } from './context/AppContext';
import { deleteSession } from './services/api';
import DemoView from './views/DemoView/DemoView';
import AdminView from './views/AdminView/AdminView';
import HistoryView from './views/HistoryView/HistoryView';

const { Header, Content } = Layout;

const menuItems = [
  { key: '/', label: '演示' },
  { key: '/admin', label: '管理' },
  { key: '/history', label: '历史' },
];

function AppLayout() {
  const navigate = useNavigate();
  const location = useLocation();
  const { state, dispatch } = useAppContext();
  const [clearing, setClearing] = useState(false);

  const handleClearSession = async () => {
    setClearing(true);
    try {
      await deleteSession();
      dispatch({ type: 'RESET' });
      message.success('会话已清空');
    } catch (err) {
      message.error(err instanceof Error ? err.message : '清空失败');
    } finally {
      setClearing(false);
    }
  };

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header
        style={{
          height: 56,
          lineHeight: '56px',
          padding: '0 24px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          background: '#fff',
          borderBottom: '1px solid #f0f0f0',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 24 }}>
          <span style={{ fontSize: 18, fontWeight: 600, whiteSpace: 'nowrap' }}>
            AI Agent Demo
          </span>
          <Menu
            mode="horizontal"
            selectedKeys={[location.pathname]}
            items={menuItems}
            onClick={({ key }) => navigate(key)}
            style={{ border: 'none', lineHeight: '54px' }}
          />
        </div>
        <Popconfirm
          title="确定清空当前会话？"
          description="所有消息和日志将被清除"
          onConfirm={handleClearSession}
          okText="确定"
          cancelText="取消"
        >
          <Button
            disabled={state.sessionStatus === 'running'}
            loading={clearing}
          >
            清空会话
          </Button>
        </Popconfirm>
      </Header>
      <Content style={{ background: '#f5f5f5' }}>
        <Routes>
          <Route path="/" element={<DemoView />} />
          <Route path="/admin" element={<AdminView />} />
          <Route path="/history" element={<HistoryView />} />
        </Routes>
      </Content>
    </Layout>
  );
}

function App() {
  return (
    <BrowserRouter>
      <AppProvider>
        <AppLayout />
      </AppProvider>
    </BrowserRouter>
  );
}

export default App;
