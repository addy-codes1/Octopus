import { create } from 'zustand'
import { Conversation, Message, Paper } from '@/types'

interface ChatState {
  currentConversation: Conversation | null
  conversations: Conversation[]
  selectedPapers: Paper[]
  isStreaming: boolean
  setCurrentConversation: (conversation: Conversation | null) => void
  setConversations: (conversations: Conversation[]) => void
  addMessage: (message: Message) => void
  setSelectedPapers: (papers: Paper[]) => void
  togglePaperSelection: (paper: Paper) => void
  setIsStreaming: (isStreaming: boolean) => void
  clearChat: () => void
}

export const useChatStore = create<ChatState>((set) => ({
  currentConversation: null,
  conversations: [],
  selectedPapers: [],
  isStreaming: false,

  setCurrentConversation: (conversation) =>
    set({ currentConversation: conversation }),

  setConversations: (conversations) => set({ conversations }),

  addMessage: (message) =>
    set((state) => ({
      currentConversation: state.currentConversation
        ? {
            ...state.currentConversation,
            messages: [...state.currentConversation.messages, message],
          }
        : null,
    })),

  setSelectedPapers: (papers) => set({ selectedPapers: papers }),

  togglePaperSelection: (paper) =>
    set((state) => {
      const isSelected = state.selectedPapers.some((p) => p.id === paper.id)
      return {
        selectedPapers: isSelected
          ? state.selectedPapers.filter((p) => p.id !== paper.id)
          : [...state.selectedPapers, paper],
      }
    }),

  setIsStreaming: (isStreaming) => set({ isStreaming }),

  clearChat: () =>
    set({
      currentConversation: null,
      selectedPapers: [],
      isStreaming: false,
    }),
}))
