import { Routes, Route, Navigate } from 'react-router-dom'
import { Layout } from 'antd'
import AppSidebar from './components/AppSidebar'
import Dashboard from './pages/Dashboard'
import AgentManager from './pages/AgentManager'
import ToolRegistry from './pages/ToolRegistry'
import OutputViewer from './pages/OutputViewer'
import TraceAudit from './pages/TraceAudit'

const { Content } = Layout

function App() {
  return (
    <Layout style={{ minHeight: '100vh' }}>
      <AppSidebar />
      <Layout>
        <Content style={{ margin: '24px', overflow: 'auto' }}>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/agents" element={<AgentManager />} />
            <Route path="/tools" element={<ToolRegistry />} />
            <Route path="/outputs" element={<OutputViewer />} />
            <Route path="/trace" element={<TraceAudit />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </Content>
      </Layout>
    </Layout>
  )
}

export default App
