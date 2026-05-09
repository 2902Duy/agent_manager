import { Card, Table, Tag, Space, Typography } from 'antd'
import {
  ToolOutlined, CheckCircleOutlined, CloseCircleOutlined,
} from '@ant-design/icons'
import { useQuery } from '@tanstack/react-query'
import { fetchTools } from '../api/client'

const { Title } = Typography

interface ToolItem {
  id: string
  name: string
  group: string
  status: string
  module: string
  class: string
}

const statusConfig: Record<string, { color: string; icon: React.ReactNode; label: string }> = {
  implemented: { color: 'green', icon: <CheckCircleOutlined />, label: 'Implemented' },
  available: { color: 'blue', icon: <CheckCircleOutlined />, label: 'Available' },
  not_implemented: { color: 'red', icon: <CloseCircleOutlined />, label: 'Not Implemented' },
}

function ToolRegistry() {
  const { data: tools = [], isLoading } = useQuery<ToolItem[]>({
    queryKey: ['tools'],
    queryFn: fetchTools,
  })

  const columns = [
    {
      title: 'Tool ID',
      dataIndex: 'id',
      key: 'id',
      render: (id: string) => <code style={{ fontWeight: 600 }}>{id}</code>,
    },
    { title: 'Name', dataIndex: 'name', key: 'name' },
    {
      title: 'Group',
      dataIndex: 'group',
      key: 'group',
      render: (group: string) => <Tag color="blue">{group}</Tag>,
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => {
        const cfg = statusConfig[status] || { color: 'default', icon: null, label: status }
        return <Tag color={cfg.color} icon={cfg.icon}>{cfg.label}</Tag>
      },
    },
    {
      title: 'Module',
      dataIndex: 'module',
      key: 'module',
      render: (mod: string) => <code style={{ fontSize: 12 }}>{mod}</code>,
      responsive: ['lg' as const],
    },
    {
      title: 'Class',
      dataIndex: 'class',
      key: 'class',
      render: (cls: string) => <code style={{ fontSize: 12 }}>{cls}</code>,
      responsive: ['lg' as const],
    },
  ]

  return (
    <div>
      <Title level={3}>
        <ToolOutlined /> Tool Registry
      </Title>

      <Card>
        <Space style={{ marginBottom: 16 }}>
          <Tag color="green">{tools.filter(t => t.status === 'implemented').length} Implemented</Tag>
          <Tag color="default">Total: {tools.length}</Tag>
        </Space>

        <Table
          dataSource={tools}
          columns={columns}
          rowKey="id"
          loading={isLoading}
          pagination={false}
          scroll={{ x: 800 }}
          size="small"
        />
      </Card>
    </div>
  )
}

export default ToolRegistry
