import { useState } from 'react'
import {
  Card, Table, Button, Modal, Form, Input, Select, Switch, Tag,
  Space, Typography, Popconfirm, message,
} from 'antd'
import {
  RobotOutlined, PlusOutlined, EditOutlined, DeleteOutlined,
} from '@ant-design/icons'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { fetchAgents, createAgent, updateAgent, deleteAgent, toggleAgent } from '../api/client'

const { Title } = Typography
const { TextArea } = Input

interface Agent {
  name: string
  role: string
  goal: string
  backstory: string
  llm: string
  tool_groups: string[]
  skills: string[]
  risk_level: string
  enabled: boolean
  use_rag: boolean
  use_sql: boolean
  use_chart: boolean
}

const toolGroupOptions = [
  'local-rag', 'sqlserver-readonly', 'dataframe-analysis',
  'data-export', 'charting', 'report-export', 'evaluation',
].map(g => ({ label: g, value: g }))

const skillOptions = [
  'agent-routing', 'agent-design', 'rag-research', 'sql-analysis',
  'sqlserver-operations', 'data-quality-check', 'business-metrics',
  'chart-selection', 'report-writing', 'result-review',
  'security-review', 'export-packaging',
].map(s => ({ label: s, value: s }))

const riskColors: Record<string, string> = { low: 'green', medium: 'orange', high: 'red' }

function AgentManager() {
  const [modalOpen, setModalOpen] = useState(false)
  const [editingAgent, setEditingAgent] = useState<Agent | null>(null)
  const [form] = Form.useForm()
  const queryClient = useQueryClient()

  const { data: agents = [], isLoading } = useQuery<Agent[]>({
    queryKey: ['agents'],
    queryFn: fetchAgents,
  })

  const createMutation = useMutation({
    mutationFn: ({ name, data }: { name: string; data: Record<string, unknown> }) => createAgent(name, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['agents'] })
      setModalOpen(false)
      form.resetFields()
      message.success('Agent da duoc tao')
    },
    onError: (err: Error) => message.error(err.message),
  })

  const updateMutation = useMutation({
    mutationFn: ({ name, data }: { name: string; data: Record<string, unknown> }) => updateAgent(name, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['agents'] })
      setModalOpen(false)
      setEditingAgent(null)
      form.resetFields()
      message.success('Agent da duoc cap nhat')
    },
  })

  const deleteMutation = useMutation({
    mutationFn: deleteAgent,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['agents'] })
      message.success('Agent da bi xoa')
    },
  })

  const toggleMutation = useMutation({
    mutationFn: toggleAgent,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['agents'] }),
  })

  const handleSubmit = () => {
    form.validateFields().then((values) => {
      const name = values.name
      const data = { ...values }
      delete data.name
      if (editingAgent) {
        updateMutation.mutate({ name: editingAgent.name, data })
      } else {
        createMutation.mutate({ name, data })
      }
    })
  }

  const handleEdit = (agent: Agent) => {
    setEditingAgent(agent)
    form.setFieldsValue(agent)
    setModalOpen(true)
  }

  const handleAdd = () => {
    setEditingAgent(null)
    form.resetFields()
    setModalOpen(true)
  }

  const columns = [
    {
      title: 'Name',
      dataIndex: 'name',
      key: 'name',
      render: (name: string) => <strong>{name}</strong>,
    },
    { title: 'Role', dataIndex: 'role', key: 'role', ellipsis: true },
    {
      title: 'Tool Groups',
      dataIndex: 'tool_groups',
      key: 'tool_groups',
      render: (groups: string[]) => (
        <Space size={[0, 4]} wrap>
          {groups.map(g => <Tag key={g} color="blue">{g}</Tag>)}
        </Space>
      ),
    },
    {
      title: 'Skills',
      dataIndex: 'skills',
      key: 'skills',
      render: (skills: string[]) => (
        <Space size={[0, 4]} wrap>
          {skills.map(s => <Tag key={s} color="cyan">{s}</Tag>)}
        </Space>
      ),
      responsive: ['lg' as const],
    },
    {
      title: 'Risk',
      dataIndex: 'risk_level',
      key: 'risk_level',
      width: 80,
      render: (risk: string) => <Tag color={riskColors[risk] || 'default'}>{risk}</Tag>,
    },
    {
      title: 'Enabled',
      dataIndex: 'enabled',
      key: 'enabled',
      width: 80,
      render: (enabled: boolean, record: Agent) => (
        <Switch checked={enabled} onChange={() => toggleMutation.mutate(record.name)} />
      ),
    },
    {
      title: 'Actions',
      key: 'actions',
      width: 120,
      render: (_: unknown, record: Agent) => (
        <Space>
          <Button size="small" icon={<EditOutlined />} onClick={() => handleEdit(record)} />
          <Popconfirm title="Xoa agent nay?" onConfirm={() => deleteMutation.mutate(record.name)}>
            <Button size="small" danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      ),
    },
  ]

  return (
    <div>
      <Title level={3}>
        <RobotOutlined /> Agent Manager
      </Title>

      <Card
        extra={
          <Button type="primary" icon={<PlusOutlined />} onClick={handleAdd}>
            Tao Agent
          </Button>
        }
      >
        <Table
          dataSource={agents}
          columns={columns}
          rowKey="name"
          loading={isLoading}
          pagination={false}
          scroll={{ x: 900 }}
        />
      </Card>

      <Modal
        title={editingAgent ? `Sua Agent: ${editingAgent.name}` : 'Tao Agent moi'}
        open={modalOpen}
        onOk={handleSubmit}
        onCancel={() => { setModalOpen(false); setEditingAgent(null) }}
        width={700}
        confirmLoading={createMutation.isPending || updateMutation.isPending}
      >
        <Form form={form} layout="vertical">
          {!editingAgent && (
            <Form.Item name="name" label="Ten agent (snake_case)" rules={[{ required: true }]}>
              <Input placeholder="vd: sales_analyst" />
            </Form.Item>
          )}
          <Form.Item name="role" label="Vai tro" rules={[{ required: true }]}>
            <Input placeholder="Vai tro cua agent" />
          </Form.Item>
          <Form.Item name="goal" label="Muc tieu" rules={[{ required: true }]}>
            <TextArea rows={2} placeholder="Muc tieu cu the" />
          </Form.Item>
          <Form.Item name="backstory" label="Boi canh" rules={[{ required: true }]}>
            <TextArea rows={3} placeholder="Boi canh va nang luc" />
          </Form.Item>
          <Form.Item name="tool_groups" label="Tool Groups">
            <Select mode="multiple" options={toolGroupOptions} placeholder="Chon tool groups" />
          </Form.Item>
          <Form.Item name="skills" label="Skills">
            <Select mode="multiple" options={skillOptions} placeholder="Chon skills" />
          </Form.Item>
          <Form.Item name="risk_level" label="Risk Level" initialValue="low">
            <Select options={[
              { label: 'Low', value: 'low' },
              { label: 'Medium', value: 'medium' },
              { label: 'High', value: 'high' },
            ]} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default AgentManager
