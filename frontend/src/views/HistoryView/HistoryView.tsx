import { Empty } from 'antd';
import { HistoryOutlined } from '@ant-design/icons';

const HistoryView = () => {
  return (
    <div style={{ padding: 24, maxWidth: 1200, margin: '0 auto' }}>
      <h2 style={{ fontSize: 24, fontWeight: 600, marginBottom: 24 }}>
        <HistoryOutlined style={{ marginRight: 8 }} />
        历史记录
      </h2>
      <Empty description="暂无执行记录，完成一次演示后将在此显示" />
    </div>
  );
};

export default HistoryView;
