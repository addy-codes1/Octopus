import { useState, useRef, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent } from '@/components/ui/card'
import { chatApi, papersApi, conversationsApi } from '@/lib/api'
import { useChatStore } from '@/store/chat'
import { Message, Citation } from '@/types'
import { Send, Loader2, BookOpen, Plus, X } from 'lucide-react'
import { cn } from '@/lib/utils'

export default function Dashboard() {
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const {
    currentConversation,
    setCurrentConversation,
    selectedPapers,
    togglePaperSelection,
    setSelectedPapers,
  } = useChatStore()

  const { data: papers } = useQuery({
    queryKey: ['papers'],
    queryFn: () => papersApi.list({ page_size: 100 }),
    select: (res) => res.data.papers,
  })

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [currentConversation?.messages])

  const handleSend = async () => {
    if (!input.trim() || isLoading) return

    const userMessage = input.trim()
    setInput('')
    setIsLoading(true)

    const tempUserMessage: Message = {
      id: `temp-${Date.now()}`,
      conversation_id: currentConversation?.id || '',
      role: 'user',
      content: userMessage,
      citations: [],
      created_at: new Date().toISOString(),
    }

    if (currentConversation) {
      setCurrentConversation({
        ...currentConversation,
        messages: [...currentConversation.messages, tempUserMessage],
      })
    } else {
      setCurrentConversation({
        id: '',
        user_id: '',
        title: userMessage.slice(0, 50),
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        messages: [tempUserMessage],
      })
    }

    try {
      const response = await chatApi.query({
        message: userMessage,
        conversation_id: currentConversation?.id,
        paper_ids: selectedPapers.map((p) => p.id),
      })

      const { message: assistantMessage, conversation_id } = response.data

      if (!currentConversation?.id) {
        const convResponse = await conversationsApi.get(conversation_id)
        setCurrentConversation(convResponse.data)
      } else {
        setCurrentConversation({
          ...currentConversation,
          messages: [...currentConversation.messages.slice(0, -1), tempUserMessage, assistantMessage],
        })
      }
    } catch (error) {
      console.error('Chat error:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const startNewChat = () => {
    setCurrentConversation(null)
    setSelectedPapers([])
  }

  return (
    <div className="flex h-full">
      <div className="flex-1 flex flex-col">
        <div className="flex items-center justify-between p-4 border-b">
          <h1 className="text-xl font-semibold">
            {currentConversation?.title || 'New Conversation'}
          </h1>
          <Button variant="outline" size="sm" onClick={startNewChat}>
            <Plus className="h-4 w-4 mr-2" />
            New Chat
          </Button>
        </div>

        <div className="flex-1 overflow-auto p-4 space-y-4">
          {(!currentConversation || currentConversation.messages.length === 0) && (
            <div className="flex flex-col items-center justify-center h-full text-center">
              <BookOpen className="h-16 w-16 text-muted-foreground mb-4" />
              <h2 className="text-2xl font-semibold mb-2">Welcome to ScholarChat</h2>
              <p className="text-muted-foreground max-w-md">
                Ask questions about your research papers. Select papers from the sidebar
                or ask general research questions.
              </p>
              <div className="mt-6 space-y-2 text-sm text-muted-foreground">
                <p>Try asking:</p>
                <ul className="space-y-1">
                  <li>"What are the main findings in these papers?"</li>
                  <li>"Find contradictions across these studies"</li>
                  <li>"Compare the methodologies used"</li>
                  <li>"What research gaps exist?"</li>
                </ul>
              </div>
            </div>
          )}

          {currentConversation?.messages.map((message) => (
            <div
              key={message.id}
              className={cn(
                'flex',
                message.role === 'user' ? 'justify-end' : 'justify-start'
              )}
            >
              <div
                className={cn(
                  'max-w-[80%] rounded-lg p-4',
                  message.role === 'user'
                    ? 'bg-primary text-primary-foreground'
                    : 'bg-muted'
                )}
              >
                <div className="whitespace-pre-wrap">{message.content}</div>
                {message.citations.length > 0 && (
                  <div className="mt-3 pt-3 border-t border-border/50">
                    <p className="text-xs font-medium mb-2">Sources:</p>
                    <div className="space-y-2">
                      {message.citations.map((citation, i) => (
                        <div
                          key={i}
                          className="text-xs bg-background/50 p-2 rounded"
                        >
                          <span className="font-medium">[{i + 1}]</span>{' '}
                          {citation.paper_title}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          ))}

          {isLoading && (
            <div className="flex justify-start">
              <div className="bg-muted rounded-lg p-4">
                <Loader2 className="h-5 w-5 animate-spin" />
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        <div className="p-4 border-t">
          <div className="flex gap-2">
            <Input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask about your papers..."
              onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && handleSend()}
              disabled={isLoading}
            />
            <Button onClick={handleSend} disabled={isLoading || !input.trim()}>
              {isLoading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Send className="h-4 w-4" />
              )}
            </Button>
          </div>
        </div>
      </div>

      <div className="w-80 border-l p-4 overflow-auto">
        <h3 className="font-semibold mb-4">Select Papers</h3>
        <div className="space-y-2">
          {papers?.map((paper) => (
            <Card
              key={paper.id}
              className={cn(
                'cursor-pointer transition-colors',
                selectedPapers.some((p) => p.id === paper.id)
                  ? 'border-primary bg-primary/5'
                  : 'hover:bg-accent'
              )}
              onClick={() => togglePaperSelection(paper)}
            >
              <CardContent className="p-3">
                <p className="text-sm font-medium line-clamp-2">{paper.title}</p>
                <p className="text-xs text-muted-foreground mt-1">
                  {paper.authors.slice(0, 2).join(', ')}
                  {paper.authors.length > 2 && ' et al.'}
                </p>
                {paper.year && (
                  <p className="text-xs text-muted-foreground">{paper.year}</p>
                )}
              </CardContent>
            </Card>
          ))}

          {!papers?.length && (
            <p className="text-sm text-muted-foreground text-center py-4">
              No papers uploaded yet. Go to Papers to upload.
            </p>
          )}
        </div>
      </div>
    </div>
  )
}
