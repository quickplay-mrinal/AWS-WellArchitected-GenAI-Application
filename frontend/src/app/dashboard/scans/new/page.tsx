'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { useQuery, useMutation } from '@tanstack/react-query'
import { scanAPI, credentialsAPI } from '@/lib/api'
import Link from 'next/link'

export default function NewScanPage() {
  const router = useRouter()
  const [formData, setFormData] = useState({
    scan_name: '',
    credential_id: '',
  })

  const { data: credentials, isLoading } = useQuery({
    queryKey: ['credentials'],
    queryFn: async () => {
      const response = await credentialsAPI.list()
      return response.data
    },
  })

  const createMutation = useMutation({
    mutationFn: scanAPI.create,
    onSuccess: (response) => {
      router.push(`/dashboard/scans/${response.data.id}`)
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
            <h1 className="text-3xl font-bold text-gray-900">New Scan</h1>
            <Link
              href="/dashboard"
              className="rounded-md bg-gray-600 px-4 py-2 text-white hover:bg-gray-700"
            >
              Cancel
            </Link>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-3xl px-4 py-8 sm:px-6 lg:px-8">
        <div className="rounded-lg bg-white p-8 shadow">
          <h2 className="mb-6 text-2xl font-semibold">Start AWS Well-Architected Assessment</h2>

          {isLoading ? (
            <p>Loading credentials...</p>
          ) : !credentials || credentials.length === 0 ? (
            <div className="text-center py-8">
              <p className="text-gray-600 mb-4">
                You need to add AWS credentials before starting a scan
              </p>
              <Link
                href="/dashboard/credentials"
                className="inline-block rounded-md bg-primary px-4 py-2 text-white hover:bg-primary/90"
              >
                Add Credentials
              </Link>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-gray-700">Scan Name</label>
                <input
                  type="text"
                  required
                  value={formData.scan_name}
                  onChange={(e) => setFormData({ ...formData, scan_name: e.target.value })}
                  placeholder="e.g., Production Account Assessment"
                  className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">
                  AWS Credential
                </label>
                <select
                  required
                  value={formData.credential_id}
                  onChange={(e) => setFormData({ ...formData, credential_id: e.target.value })}
                  className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2"
                >
                  <option value="">Select a credential</option>
                  {credentials.map((cred: any) => (
                    <option key={cred.id} value={cred.id}>
                      {cred.credential_name}
                    </option>
                  ))}
                </select>
              </div>

              <div className="rounded-md bg-blue-50 p-4">
                <h3 className="text-sm font-medium text-blue-800">What will be scanned?</h3>
                <ul className="mt-2 list-disc list-inside text-sm text-blue-700 space-y-1">
                  <li>All enabled AWS regions</li>
                  <li>EC2, RDS, Lambda, S3, VPC, IAM resources</li>
                  <li>Security configurations</li>
                  <li>Cost optimization opportunities</li>
                  <li>Performance and reliability metrics</li>
                </ul>
              </div>

              <div className="rounded-md bg-yellow-50 p-4">
                <h3 className="text-sm font-medium text-yellow-800">Note</h3>
                <p className="mt-1 text-sm text-yellow-700">
                  The scan may take 5-15 minutes depending on the number of resources and regions.
                  AI recommendations will be generated using AWS Bedrock Claude Sonnet 4.
                </p>
              </div>

              <button
                type="submit"
                disabled={createMutation.isPending}
                className="w-full rounded-md bg-primary px-4 py-3 text-white font-semibold hover:bg-primary/90 disabled:opacity-50"
              >
                {createMutation.isPending ? 'Starting Scan...' : 'Start Scan'}
              </button>

              {createMutation.isError && (
                <div className="rounded-md bg-red-50 p-4 text-sm text-red-800">
                  Failed to start scan. Please try again.
                </div>
              )}
            </form>
          )}
        </div>
      </main>
    </div>
  )
}
