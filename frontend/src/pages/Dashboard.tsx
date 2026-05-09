import { useState, useEffect, useRef, useCallback } from 'react'
import {
  Card, Input, Button, Select, Space, Typography, Tag,
  Timeline, Divider, Alert, Row, Col, Statistic,
} from 'antd'
import {
  PlayCircleOutlined, RobotOutlined,
  ToolOutlined, CheckCircleOutlined, CloseCircleOutlined,
  LoadingOutlined, TeamOutlined, FileTextOutlined,
} from '@ant-design/icons'
import { useMutation } from '@tanstack/react-query'
import { runCrew, getCrewStatus } from '../api/client'
import { useAppStore } from '../store/appStore'

const { TextArea } = Input
const { Title, Text } = Typography

const modelOptions = [
  { value: 'google/gemini-2.0-flash', label: 'Gemini 2.0 Flash' },
  { value: 'google/gemini-3.1-flash-lite-preview', label: 'Gemini 3.1 Flash Lite' },
  { value: 'google/gemini-2.0-flash-lite', label: 'Gemini 2.0 Flash Lite' },
  { value: 'ollama/llama3.1', label: 'Ollama (local - llama3.1)' },
  { value: 'groq/llama-3.1-8b-instant', label: 'Groq (free)' },
]

const kindIcons: Record<string, React.ReactNode> = {
  crew: <PlayCircleOutlined style={{ color: '#1677ff' }} />,
  task: <FileTextOutlined style={{ color: '#fa8c16' }} />,
  agent: <RobotOutlined style={{ color: '#722ed1' }} />,
  tool: <ToolOutlined style={{ color: '#52c41a' }} />,
  delegation: <TeamOutlined style={{ color: '#13c2c2' }} />,
  error: <CloseCircleOutlined style={{ color: '#ff4d4f' }} />,
}

const kindColors: Record<string, string> = {
  crew: 'blue',
  task: 'orange',
  agent: 'purple',
  tool: 'green',
  delegation: 'cyan',
  error: 'red',
}

function Dashboard() {
  const [task, setTask] = useState('Giai thich RAG la gi va cach hoat dong?')
  const [model, setModel] = useState('google/gemini-2.0-flash')
  const eventsEndRef = useRef<HTMLDivElement>(null)

  const {
    isRunning, currentSessionId, events, result,
    currentAgent, currentTask, delegatedAgent,
    setRunning, setSessionId, setEvents, clearEvents, setResult,
    setCurrentAgent, setCurrentTask, setDelegatedAgent,
  } = useAppStore()

  useEffect(() => {
    eventsEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [events])

  const pollStatus = useCallback((sessionId: string) => {
    const interval = setInterval(async () => {
      try {
        const data = await getCrewStatus(sessionId)
        setEvents(data.events || [])
        setCurrentAgent(data.current_agent || '')
        setCurrentTask(data.current_task || '')
        setDelegatedAgent(data.delegated_agent || '')

        if (data.status === 'completed' || data.status === 'failed') {
          clearInterval(interval)
          setRunning(false)
          if (data.result) setResult(data.result)
          if (data.error) setResult(`ERROR: ${data.error}`)
        }
      } catch {
        clearInterval(interval)
        setRunning(false)
      }
    }, 1500)
    return interval
  }, [setEvents, setRunning, setResult, setCurrentAgent, setCurrentTask, setDelegatedAgent])

  const runMutation = useMutation({
    mutationFn: () => runCrew({ task, model }),
    onSuccess: (data) => {
      setSessionId(data.session_id)
      pollStatus(data.session_id)
    },
    onError: () => setRunning(false),
  })

  const handleRun = () => {
    if (!task.trim()) return
    clearEvents()
    setRunning(true)
    setResult(null)
    runMutation.mutate()
  }

  const getStatusTag = () => {
    if (isRunning) return <Tag icon={<LoadingOutlined spin />} color="processing">RUNNING</Tag>
    if (result?.startsWith('ERROR')) return <Tag icon={<CloseCircleOutlined />} color="error">FAILED</Tag>
    if (result) return <Tag icon={<CheckCircleOutlined />} color="success">COMPLETED</Tag>
    return <Tag color="default">IDLE</Tag>
  }

  return (
    <div>
      <Title level={3}>
        <PlayCircleOutlined /> Dashboard
      </Title>

      <Row gutter={16}>
        <Col xs={24} lg={16}>
          <Card style={{ marginBottom: 16 }}>
            <Space direction="vertical" style={{ width: '100%' }} size="middle">
              <TextArea
                rows={3}
                placeholder="Nhap cau hoi cua ban... (VD: Giai thich RAG la gi?)"
                value={task}
                onChange={(e) => setTask(e.target.value)}
                disabled={isRunning}
              />
              <Space wrap>
                <Select
                  value={model}
                  onChange={setModel}
                  options={modelOptions}
                  style={{ width: 260 }}
                  disabled={isRunning}
                />
                <Button
                  type="primary"
                  icon={<PlayCircleOutlined />}
                  onClick={handleRun}
                  loading={isRunning}
                  disabled={isRunning || !task.trim()}
                  size="large"
                >
                  Chay
                </Button>
              </Space>
            </Space>
          </Card>

          <Card title="Luong xu ly" style={{ marginBottom: 16 }}>
            {events.length === 0 ? (
              <Text type="secondary">Chua co su kien nao. Hay nhap task va nhan Chay.</Text>
            ) : (
              <Timeline
                items={[...events].reverse().map((ev, i) => ({
                  dot: kindIcons[ev.kind] || <LoadingOutlined />,
                  color: kindColors[ev.kind] || 'gray',
                  children: (
                    <div key={i}>
                      <Text type="secondary" style={{ fontSize: 12, marginRight: 8 }}>{ev.time}</Text>
                      <Text>{ev.message}</Text>
                    </div>
                  ),
                }))}
              />
            )}
            <div ref={eventsEndRef} />
          </Card>

          {result && (
            <Card title="Ket qua">
              {result.startsWith('ERROR') ? (
                <Alert type="error" message={result} showIcon />
              ) : (
                <div style={{ whiteSpace: 'pre-wrap' }}>{result}</div>
              )}
            </Card>
          )}
        </Col>

        <Col xs={24} lg={8}>
          <Card style={{ marginBottom: 16 }}>
            <Space direction="vertical" style={{ width: '100%' }}>
              <div style={{ textAlign: 'center', marginBottom: 8 }}>
                {getStatusTag()}
              </div>
              <Divider style={{ margin: '8px 0' }} />
              <Statistic
                title="Agent hien tai"
                value={currentAgent || '---'}
                prefix={<RobotOutlined style={{ color: '#722ed1' }} />}
                valueStyle={{ fontSize: 14 }}
              />
              <Divider style={{ margin: '8px 0' }} />
              <Statistic
                title="Duoc giao cho"
                value={delegatedAgent || '---'}
                prefix={<TeamOutlined style={{ color: '#13c2c2' }} />}
                valueStyle={{ fontSize: 14 }}
              />
              <Divider style={{ margin: '8px 0' }} />
              <Statistic
                title="Task hien tai"
                value={currentTask ? (currentTask.length > 80 ? currentTask.slice(0, 80) + '...' : currentTask) : '---'}
                prefix={<FileTextOutlined style={{ color: '#fa8c16' }} />}
                valueStyle={{ fontSize: 12 }}
              />
            </Space>
          </Card>

          <Card title="Thong tin">
            <Space direction="vertical">
              <Text>Session: <code>{currentSessionId || '---'}</code></Text>
              <Text>So su kien: <strong>{events.length}</strong></Text>
              <Text>Model: <code>{model}</code></Text>
            </Space>
          </Card>
        </Col>
      </Row>
    </div>
  )
}

export default Dashboard
