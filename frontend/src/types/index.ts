export interface User {
  id: string
  email: string
  full_name?: string
  university?: string
  field_of_study?: string
  created_at: string
}

export interface Paper {
  id: string
  user_id: string
  title: string
  authors: string[]
  year?: number
  doi?: string
  abstract?: string
  file_path?: string
  file_size?: number
  page_count?: number
  uploaded_at: string
  metadata: Record<string, unknown>
}

export interface Message {
  id: string
  conversation_id: string
  role: 'user' | 'assistant'
  content: string
  citations: Citation[]
  created_at: string
}

export interface Conversation {
  id: string
  user_id: string
  title?: string
  created_at: string
  updated_at: string
  messages: Message[]
}

export interface Citation {
  paper_id: string
  paper_title: string
  chunk_index: number
  content_preview: string
}

export interface AuthTokens {
  access_token: string
  refresh_token: string
  token_type: string
}
