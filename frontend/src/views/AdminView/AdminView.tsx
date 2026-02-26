import { Card, Empty } from 'antd';
import { AppstoreOutlined, ToolOutlined } from '@ant-design/icons';

const AdminView = () => {
  return (
    <div style={{ padding: 24, maxWidth: 1200, margin: '0 auto' }}>
      <h2 style={{ fontSize: 24, fontWeight: 600, marginBottom: 24 }}>系统管理</h2>
      <div style={{ display: 'flex', gap: 24 }}>
        <Card
          title={
            <span>
              <AppstoreOutlined style={{ marginRight: 8 }} />
              Skill 列表
            </span>
          }
          style={{ flex: 1 }}
        >
          <Empty description="Skill 列表将在后续 Story 中实现" />
        </Card>
        <Card
          title={
            <span>
              <ToolOutlined style={{ marginRight: 8 }} />
              工具列表
            </span>
          }
          style={{ flex: 1 }}
        >
          <Empty description="工具列表将在后续 Story 中实现" />
        </Card>
      </div>
    </div>
  );
};

export default AdminView;
