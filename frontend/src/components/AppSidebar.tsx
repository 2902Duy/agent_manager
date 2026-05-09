import { useNavigate, useLocation } from 'react-router-dom'
import { Layout, Menu } from 'antd'
import {
  DashboardOutlined,
  RobotOutlined,
  ToolOutlined,
  FileOutlined,
  AuditOutlined,
} from '@ant-design/icons'

const { Sider } = Layout

const menuItems = [
  { key: '/', icon: <DashboardOutlined />, label: 'Dashboard' },
  { key: '/agents', icon: <RobotOutlined />, label: 'Agent Manager' },
  { key: '/tools', icon: <ToolOutlined />, label: 'Tool Registry' },
  { key: '/outputs', icon: <FileOutlined />, label: 'Outputs' },
  { key: '/trace', icon: <AuditOutlined />, label: 'Trace & Audit' },
]

function AppSidebar() {
  const navigate = useNavigate()
  const location = useLocation()

  return (
    <Sider
      breakpoint="lg"
      collapsedWidth="60"
      style={{
        overflow: 'auto',
        height: '100vh',
        position: 'sticky',
        top: 0,
        left: 0,
      }}
    >
      <div
        style={{
          height: 48,
          margin: 16,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: '#fff',
          fontSize: 18,
          fontWeight: 700,
          letterSpacing: 1,
        }}
      >
        <RobotOutlined style={{ marginRight: 8, fontSize: 22 }} />
        Agent Manager
      </div>
      <Menu
        theme="dark"
        mode="inline"
        selectedKeys={[location.pathname]}
        items={menuItems}
        onClick={({ key }) => navigate(key)}
      />
    </Sider>
  )
}

export default AppSidebar
