import { BrowserRouter, Routes, Route, useNavigate, useLocation } from 'react-router-dom';
import { Layout, Menu, Button } from 'antd';
import { AppProvider } from './context/AppContext';
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
        <Button disabled>清空会话</Button>
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
