import { useState, useCallback } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useDropzone } from 'react-dropzone'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { papersApi, citationsApi } from '@/lib/api'
import { Paper } from '@/types'
import {
  Upload,
  FileText,
  Trash2,
  Search,
  Download,
  Loader2,
  Calendar,
  User,
} from 'lucide-react'
import { cn } from '@/lib/utils'

export default function Papers() {
  const queryClient = useQueryClient()
  const [search, setSearch] = useState('')
  const [selectedPapers, setSelectedPapers] = useState<string[]>([])
  const [uploadingFiles, setUploadingFiles] = useState<string[]>([])

  const { data: papersData, isLoading } = useQuery({
    queryKey: ['papers', search],
    queryFn: () => papersApi.list({ page_size: 100, search: search || undefined }),
    select: (res) => res.data,
  })

  const uploadMutation = useMutation({
    mutationFn: papersApi.upload,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['papers'] })
    },
  })

  const deleteMutation = useMutation({
    mutationFn: papersApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['papers'] })
    },
  })

  const onDrop = useCallback(
    async (acceptedFiles: File[]) => {
      for (const file of acceptedFiles) {
        setUploadingFiles((prev) => [...prev, file.name])
        try {
          await uploadMutation.mutateAsync(file)
        } catch (error) {
          console.error('Upload failed:', error)
        } finally {
          setUploadingFiles((prev) => prev.filter((f) => f !== file.name))
        }
      }
    },
    [uploadMutation]
  )

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'application/pdf': ['.pdf'] },
    multiple: true,
  })

  const toggleSelection = (paperId: string) => {
    setSelectedPapers((prev) =>
      prev.includes(paperId)
        ? prev.filter((id) => id !== paperId)
        : [...prev, paperId]
    )
  }

  const exportBibtex = async () => {
    if (selectedPapers.length === 0) return
    try {
      const response = await citationsApi.exportBibtex(selectedPapers)
      const blob = new Blob([response.data], { type: 'text/plain' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = 'bibliography.bib'
      a.click()
      URL.revokeObjectURL(url)
    } catch (error) {
      console.error('Export failed:', error)
    }
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Paper Library</h1>
        <div className="flex gap-2">
          {selectedPapers.length > 0 && (
            <Button variant="outline" onClick={exportBibtex}>
              <Download className="h-4 w-4 mr-2" />
              Export BibTeX ({selectedPapers.length})
            </Button>
          )}
        </div>
      </div>

      <div
        {...getRootProps()}
        className={cn(
          'border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors',
          isDragActive
            ? 'border-primary bg-primary/5'
            : 'border-border hover:border-primary/50'
        )}
      >
        <input {...getInputProps()} />
        <Upload className="h-10 w-10 mx-auto text-muted-foreground mb-4" />
        {isDragActive ? (
          <p className="text-primary font-medium">Drop PDFs here...</p>
        ) : (
          <>
            <p className="font-medium">Drag & drop PDF files here</p>
            <p className="text-sm text-muted-foreground mt-1">
              or click to browse
            </p>
          </>
        )}
        {uploadingFiles.length > 0 && (
          <div className="mt-4">
            <p className="text-sm text-muted-foreground">Uploading:</p>
            {uploadingFiles.map((file) => (
              <div
                key={file}
                className="flex items-center justify-center gap-2 mt-1"
              >
                <Loader2 className="h-4 w-4 animate-spin" />
                <span className="text-sm">{file}</span>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="flex gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search papers..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-10"
          />
        </div>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-8">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      ) : papersData?.papers.length === 0 ? (
        <div className="text-center py-8">
          <FileText className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
          <p className="text-muted-foreground">No papers uploaded yet</p>
          <p className="text-sm text-muted-foreground">
            Upload PDFs to start your literature review
          </p>
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {papersData?.papers.map((paper: Paper) => (
            <Card
              key={paper.id}
              className={cn(
                'cursor-pointer transition-all hover:shadow-md',
                selectedPapers.includes(paper.id) && 'ring-2 ring-primary'
              )}
              onClick={() => toggleSelection(paper.id)}
            >
              <CardHeader className="pb-3">
                <CardTitle className="text-base line-clamp-2">
                  {paper.title}
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                {paper.authors.length > 0 && (
                  <div className="flex items-start gap-2 text-sm text-muted-foreground">
                    <User className="h-4 w-4 mt-0.5 flex-shrink-0" />
                    <span className="line-clamp-1">
                      {paper.authors.join(', ')}
                    </span>
                  </div>
                )}
                {paper.year && (
                  <div className="flex items-center gap-2 text-sm text-muted-foreground">
                    <Calendar className="h-4 w-4" />
                    <span>{paper.year}</span>
                  </div>
                )}
                {paper.abstract && (
                  <p className="text-xs text-muted-foreground line-clamp-3 mt-2">
                    {paper.abstract}
                  </p>
                )}
                <div className="flex justify-end pt-2">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={(e) => {
                      e.stopPropagation()
                      deleteMutation.mutate(paper.id)
                    }}
                  >
                    <Trash2 className="h-4 w-4 text-destructive" />
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
