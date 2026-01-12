export type DocumentStatus = 'active' | 'archived'

export type DocumentItem = {
  id: number
  title: string
  description: string | null
  category: string
  tags: string | null
  file_type: string
  drive_file_id: string
  web_view_link: string
  uploaded_by_email?: string | null
  status: DocumentStatus
  ai_summary: string | null
  created_at: string
  updated_at: string
}
