'use client'

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { s3API } from '@/lib/api'
import Link from 'next/link'

export default function DocumentsPage() {
  const queryClient = useQueryClient()
  const [uploading, setUploading] = useState(false)

  const { data: documents, isLoading } = useQuery({
    queryKey: ['documents'],
    queryFn: async () => {
      const response = await s3API.listDocuments()
      return response.data.documents
    },
  })

  const deleteMutation = useMutation({
    mutationFn: s3API.deleteDocument,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] })
    },
  })

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    setUploading(true)
    try {
      await s3API.uploadDocument(file)
      queryClient.invalidateQueries({ queryKey: ['documents'] })
      e.target.value = ''
    } catch (error) {
      alert('Failed to upload file')
    } finally {
      setUploading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow">
        <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between">
            <h1 className="text-3xl font-bold text-gray-900">Well-Architected Documents</h1>
            <Link
              href="/dashboard"
              className="rounded-md bg-gray-600 px-4 py-2 text-white hover:bg-gray-700"
            >
              Back to Dashboard
            </Link>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        <div className="mb-8 rounded-lg bg-blue-50 p-6">
          <h2 className="text-lg font-semibold text-blue-900">About Document Upload</h2>
          <p className="mt-2 text-sm text-blue-800">
            Upload AWS Well-Architected Framework documentation (6 Pillars) to enhance AI
            recommendations. Supported formats: PDF, TXT, MD, DOCX
          </p>
        </div>

        <div className="mb-6">
          <label className="inline-block cursor-pointer rounded-md bg-primary px-6 py-3 text-white hover:bg-primary/90">
            {uploading ? 'Uploading...' : 'Upload Document'}
            <input
              type="file"
              accept=".pdf,.txt,.md,.docx"
              onChange={handleFileUpload}
              disabled={uploading}
              className="hidden"
            />
          </label>
        </div>

        <div className="rounded-lg bg-white shadow">
          <div className="border-b border-gray-200 px-6 py-4">
            <h2 className="text-xl font-semibold">Uploaded Documents</h2>
          </div>
          <div className="p-6">
            {isLoading ? (
              <p>Loading documents...</p>
            ) : documents && documents.length > 0 ? (
              <div className="space-y-4">
                {documents.map((doc: any) => (
                  <div
                    key={doc.s3_key}
                    className="flex items-center justify-between rounded-lg border border-gray-200 p-4"
                  >
                    <div>
                      <h3 className="font-semibold">{doc.file_name}</h3>
                      <p className="text-sm text-gray-600">
                        Size: {(doc.size / 1024).toFixed(2)} KB | Last modified:{' '}
                        {new Date(doc.last_modified).toLocaleDateString()}
                      </p>
                    </div>
                    <button
                      onClick={() => deleteMutation.mutate(doc.file_name)}
                      disabled={deleteMutation.isPending}
                      className="rounded-md bg-red-600 px-4 py-2 text-white hover:bg-red-700 disabled:opacity-50"
                    >
                      Delete
                    </button>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-600">No documents uploaded yet</p>
            )}
          </div>
        </div>
      </main>
    </div>
  )
}
