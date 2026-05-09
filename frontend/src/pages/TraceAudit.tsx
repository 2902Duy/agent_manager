import { useState } from 'react'
import {
  Card, Table, Tag, Typography, Space, Timeline, Modal,
  Statistic, Row, Col, Empty,
} from 'antd'
import {
  AuditOutlined, ClockCircleOutlined, RobotOutlined,
  ToolOutlined, EyeOutlined, CheckCircleOutlined,
  CloseCircleOutlined,
} from '@ant-design/icons'
import { useQuery } from '@tanstack/react-query'
import { fetchTraces, fetchTrace } from '../api/client'

const { Title } = Typography

interface TraceSummary {
  session_id: string
  status: string
  total_events: number
  total_tool_calls: number
  total_duration_ms: number
}

interface TraceEvent {
  id: string
  timestamp: string
  event_type: string
  agent_name: string
  tool_name: string
  message: string
  duration_ms: number
  data: Record<string, unknown>
}

interface TraceDetail {
  session_id: string
  summary: TraceSummary
  timeline: TraceEvent[]
}

function TraceAudit() {
  const [selectedSession, setSelectedSession] = useState<string | null>(null)
  const [detailOpen, setDetailOpen] = useState(false)

  const { data: traces = [], isLoading } = useQuery<TraceSummary[]>({
    queryKey: ['traces'],
    queryFn: fetchTraces,
  })

  const { data: traceDetail } = useQuery<TraceDetail>({
    queryKey: ['trace', selectedSession],
    queryFn: () => fetchTrace(selectedSession!),
    enabled: !!selectedSession,
  })

  const handleView = (sessionId: string) => {
    setSelectedSession(sessionId)
    setDetailOpen(true)
  }

  const statusColors: Record<string, string> = {
    completed: 'green',
    running: 'blue',
    failed: 'red',
    error: 'red',
    idle: 'default',
  }

  const columns = [
    {
      title: 'Session ID',
      dataIndex: 'session_id',
      key: 'session_id',
      render: (id: string) => <code>{id}</code>,
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => (
        <Tag
          color={statusColors[status] || 'default'}
          icon={status === 'completed' ? <CheckCircleOutlined /> : status === 'failed' ? <CloseCircleOutlined /> : undefined}
        >
          {status}
        </Tag>
      ),
    },
    { title: 'Events', dataIndex: 'total_events', key: 'total_events' },
    { title: 'Tool Calls', dataIndex: 'total_tool_calls', key: 'total_tool_calls' },
    {
      title: 'Actions',
      key: 'actions',
      render: (_: unknown, record: TraceSummary) => (
        <a onClick={() => handleView(record.session_id)}>
          <EyeOutlined /> Xem Timeline
        </a>
      ),
    },
  ]

  const getTimelineIcon = (type: string) => {
    if (type === 'agent') return <RobotOutlined />
    if (type === 'tool') return <ToolOutlined />
    return <ClockCircleOutlined />
  }

  const getTimelineColor = (type: string) => {
    if (type === 'error') return 'red'
    if (type === 'crew') return 'blue'
    if (type === 'task') return 'orange'
    if (type === 'agent') return 'purple'
    if (type === 'tool') return 'green'
    return 'gray'
  }

  return (
    <div>
      <Title level={3}>
        <AuditOutlined /> Trace & Audit
      </Title>

      <Card>
        {traces.length === 0 && !isLoading ? (
          <Empty description="Chua co lich su chay. Chay task tu Dashboard de bat dau." />
        ) : (
          <Table
            dataSource={traces}
            columns={columns}
            rowKey="session_id"
            loading={isLoading}
            pagination={false}
          />
        )}
      </Card>

      <Modal
        title={`Trace: ${selectedSession}`}
        open={detailOpen}
        onCancel={() => setDetailOpen(false)}
        width={800}
        footer={null}
      >
        {traceDetail && (
          <>
            <Row gutter={16} style={{ marginBottom: 24 }}>
              <Col span={8}>
                <Statistic title="Status" value={traceDetail.summary.status} />
              </Col>
              <Col span={8}>
                <Statistic title="Events" value={traceDetail.summary.total_events} />
              </Col>
              <Col span={8}>
                <Statistic title="Tool Calls" value={traceDetail.summary.total_tool_calls} />
              </Col>
            </Row>

            <Timeline
              items={traceDetail.timeline.map((evt) => ({
                dot: getTimelineIcon(evt.event_type),
                color: getTimelineColor(evt.event_type),
                children: (
                  <div>
                    <strong>{evt.message}</strong>
                    <br />
                    <Space>
                      <Tag>{evt.event_type}</Tag>
                      <span style={{ color: '#999', fontSize: 12 }}>{evt.timestamp}</span>
                    </Space>
                  </div>
                ),
              }))}
            />
          </>
        )}
      </Modal>
    </div>
  )
}

export default TraceAudit
