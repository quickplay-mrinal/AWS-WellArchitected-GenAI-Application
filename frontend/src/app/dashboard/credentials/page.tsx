'use client'

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { credentialsAPI } from '@/lib/api'
import Link from 'next/link'

export default function CredentialsPage() {
  const queryClient = useQueryClient()
  const [showForm, setShowForm] = useState(false)
  const [formData, setFormData] = useState({
    credential_name: '',
    access_key: '',
    secret_key: '',
  })

  const { data: credentials, isLoading } = useQuery({
    queryKey: ['credentials'],
    queryFn: async () => {
      const response = await credentialsAPI.list()
      return response.data
    },
  })

  const createMutation = useMutation({
    mutationFn: credentialsAPI.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['credentials'] })
      setShowForm(false)
      setFormData({ credential_name: '', access_key: '', secret_key: '' })
    },
  })

  const deleteMutation = useMutation({
    mutationFn: credentialsAPI.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['credentials'] })
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    createMutation.mutate(formData)
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow">
        <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between">
            <h1 className="text-3xl font-bold text-gray-900">AWS Credentials</h1>
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
        <div className="mb-6">
          <button
            onClick={() => setShowForm(!showForm)}
            className="rounded-md bg-primary px-4 py-2 text-white hover:bg-primary/90"
          >
            {showForm ? 'Cancel' : 'Add New Credential'}
          </button>
        </div>

        {showForm && (
          <div className="mb-8 rounded-lg bg-white p-6 shadow">
            <h2 className="mb-4 text-xl font-semibold">Add AWS Credential</h2>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Credential Name
                </label>
                <input
                  type="text"
                  required
                  value={formData.credential_name}
                  onChange={(e) =>
                    setFormData({ ...formData, credential_name: e.target.value })
                  }
                  className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">
                  AWS Access Key
                </label>
                <input
                  type="text"
                  required
                  value={formData.access_key}
                  onChange={(e) => setFormData({ ...formData, access_key: e.target.value })}
                  className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">
                  AWS Secret Key
                </label>
                <input
                  type="password"
                  required
                  value={formData.secret_key}
                  onChange={(e) => setFormData({ ...formData, secret_key: e.target.value })}
                  className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2"
                />
              </div>
              <button
                type="submit"
                disabled={createMutation.isPending}
                className="rounded-md bg-primary px-4 py-2 text-white hover:bg-primary/90 disabled:opacity-50"
              >
                {createMutation.isPending ? 'Saving...' : 'Save Credential'}
              </button>
            </form>
          </div>
        )}

        <div className="rounded-lg bg-white shadow">
          <div className="border-b border-gray-200 px-6 py-4">
            <h2 className="text-xl font-semibold">Your Credentials</h2>
          </div>
          <div className="p-6">
            {isLoading ? (
              <p>Loading...</p>
            ) : credentials && credentials.length > 0 ? (
              <div className="space-y-4">
                {credentials.map((cred: any) => (
                  <div
                    key={cred.id}
                    className="flex items-center justify-between rounded-lg border border-gray-200 p-4"
                  >
                    <div>
                      <h3 className="font-semibold">{cred.credential_name}</h3>
                      <p className="text-sm text-gray-600">
                        Created: {new Date(cred.created_at).toLocaleDateString()}
                      </p>
                    </div>
                    <button
                      onClick={() => deleteMutation.mutate(cred.id)}
                      disabled={deleteMutation.isPending}
                      className="rounded-md bg-red-600 px-4 py-2 text-white hover:bg-red-700 disabled:opacity-50"
                    >
                      Delete
                    </button>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-600">No credentials yet</p>
            )}
          </div>
        </div>
      </main>
    </div>
  )
}
