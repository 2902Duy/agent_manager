import { Card, Table, Button, Space, Typography, Tag, Image, Empty } from 'antd'
import {
  FileOutlined, DownloadOutlined, FileImageOutlined,
  FileExcelOutlined, FilePdfOutlined, FileTextOutlined,
} from '@ant-design/icons'
import { useQuery } from '@tanstack/react-query'
import { fetchOutputs, getOutputUrl } from '../api/client'

const { Title } = Typography

interface OutputFile {
  filename: string
  size: number
  type: string
  modified: number
}

const typeIcons: Record<string, React.ReactNode> = {
  png: <FileImageOutlined style={{ color: '#1677ff' }} />,
  jpg: <FileImageOutlined style={{ color: '#1677ff' }} />,
  csv: <FileExcelOutlined style={{ color: '#52c41a' }} />,
  xlsx: <FileExcelOutlined style={{ color: '#52c41a' }} />,
  pdf: <FilePdfOutlined style={{ color: '#ff4d4f' }} />,
  md: <FileTextOutlined style={{ color: '#722ed1' }} />,
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

function OutputViewer() {
  const { data: outputs = [], isLoading } = useQuery<OutputFile[]>({
    queryKey: ['outputs'],
    queryFn: fetchOutputs,
  })

  const columns = [
    {
      title: 'File',
      dataIndex: 'filename',
      key: 'filename',
      render: (name: string, record: OutputFile) => (
        <Space>
          {typeIcons[record.type] || <FileOutlined />}
          <strong>{name}</strong>
        </Space>
      ),
    },
    {
      title: 'Type',
      dataIndex: 'type',
      key: 'type',
      width: 80,
      render: (type: string) => <Tag>{type.toUpperCase()}</Tag>,
    },
    {
      title: 'Size',
      dataIndex: 'size',
      key: 'size',
      width: 100,
      render: (size: number) => formatSize(size),
    },
    {
      title: 'Modified',
      dataIndex: 'modified',
      key: 'modified',
      width: 180,
      render: (ts: number) => new Date(ts * 1000).toLocaleString(),
    },
    {
      title: 'Preview',
      key: 'preview',
      width: 120,
      render: (_: unknown, record: OutputFile) => {
        if (['png', 'jpg', 'jpeg', 'gif'].includes(record.type)) {
          return <Image src={getOutputUrl(record.filename)} width={80} />
        }
        return null
      },
    },
    {
      title: 'Actions',
      key: 'actions',
      width: 100,
      render: (_: unknown, record: OutputFile) => (
        <Button
          size="small"
          icon={<DownloadOutlined />}
          href={getOutputUrl(record.filename)}
          target="_blank"
        >
          Download
        </Button>
      ),
    },
  ]

  return (
    <div>
      <Title level={3}>
        <FileOutlined /> Output Viewer
      </Title>

      <Card>
        {outputs.length === 0 && !isLoading ? (
          <Empty description="Chua co file output. Chay task de tao output." />
        ) : (
          <Table
            dataSource={outputs}
            columns={columns}
            rowKey="filename"
            loading={isLoading}
            pagination={false}
          />
        )}
      </Card>
    </div>
  )
}

export default OutputViewer
