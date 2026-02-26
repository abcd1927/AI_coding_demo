import { BrowserRouter, Routes, Route } from 'react-router-dom';
import DemoView from './views/DemoView/DemoView';
import AdminView from './views/AdminView/AdminView';
import HistoryView from './views/HistoryView/HistoryView';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<DemoView />} />
        <Route path="/admin" element={<AdminView />} />
        <Route path="/history" element={<HistoryView />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
