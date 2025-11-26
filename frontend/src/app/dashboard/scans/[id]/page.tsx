'use client'

import { useEffect } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { useQuery } from '@tanstack/react-query'
import { scanAPI, reportAPI } from '@/lib/api'
import { downloadBlob } from '@/lib/utils'
import Link from 'next/link'

export default function ScanDetailPage() {
  const params = useParams()
  const router = useRouter()
  const scanId = params.id as string

  const { data: scan, isLoading, refetch } = useQuery({
    queryKey: ['scan', scanId],
    queryFn: async () => {
      const response = await scanAPI.get(scanId)
      return response.data
    },
    refetchInterval: (query: any) => {
      const data = query.state.data
      return data?.status === 'running' || data?.status === 'pending' ? 3000 : false
    },
  })

  const handleDownloadPDF = async () => {
    try {
      const response = await reportAPI.downloadPDF(scanId)
      downloadBlob(response.data, `wellarchitected_report_${scanId}.pdf`)
    } catch (error) {
      alert('Failed to download PDF')
    }
  }

  const handleDownloadExcel = async () => {
    try {
      const response = await reportAPI.downloadExcel(scanId)
      downloadBlob(response.data, `wellarchitected_report_${scanId}.xlsx`)
    } catch (error) {
      alert('Failed to download Excel')
    }
  }

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <p>Loading scan details...</p>
      </div>
    )
  }

  if (!scan) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <p>Scan not found</p>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow">
        <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">{scan.scan_name}</h1>
              <p className="mt-1 text-sm text-gray-600">
                Created: {new Date(scan.created_at).toLocaleString()}
              </p>
            </div>
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
        {/* Status Card */}
        <div className="mb-8 rounded-lg bg-white p-6 shadow">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl font-semibold">Scan Status</h2>
              <p className="mt-2">
                <span
                  className={`inline-block rounded-full px-4 py-2 text-sm font-semibold ${
                    scan.status === 'completed'
                      ? 'bg-green-100 text-green-800'
                      : scan.status === 'running'
                      ? 'bg-blue-100 text-blue-800'
                      : scan.status === 'failed'
                      ? 'bg-red-100 text-red-800'
                      : 'bg-gray-100 text-gray-800'
                  }`}
                >
                  {scan.status.toUpperCase()}
                </span>
              </p>
            </div>
            {scan.status === 'completed' && (
              <div className="flex gap-4">
                <button
                  onClick={handleDownloadPDF}
                  className="rounded-md bg-red-600 px-4 py-2 text-white hover:bg-red-700"
                >
                  Download PDF
                </button>
                <button
                  onClick={handleDownloadExcel}
                  className="rounded-md bg-green-600 px-4 py-2 text-white hover:bg-green-700"
                >
                  Download Excel
                </button>
              </div>
            )}
          </div>

          {(scan.status === 'running' || scan.status === 'pending') && (
            <div className="mt-4">
              <div className="flex items-center justify-between text-sm text-gray-600">
                <span>Progress</span>
                <span>{scan.progress}%</span>
              </div>
              <div className="mt-2 h-2 w-full rounded-full bg-gray-200">
                <div
                  className="h-2 rounded-full bg-primary transition-all duration-500"
                  style={{ width: `${scan.progress}%` }}
                />
              </div>
              <p className="mt-2 text-sm text-gray-600">
                Regions scanned: {scan.regions_scanned?.length || 0}
              </p>
            </div>
          )}

          {scan.status === 'failed' && scan.error_message && (
            <div className="mt-4 rounded-md bg-red-50 p-4">
              <p className="text-sm text-red-800">{scan.error_message}</p>
            </div>
          )}
        </div>

        {/* AI Recommendations */}
        {scan.status === 'completed' && scan.ai_recommendations && (
          <div className="mb-8 rounded-lg bg-white p-6 shadow">
            <h2 className="mb-4 text-xl font-semibold">AI-Powered Recommendations</h2>
            <div className="prose max-w-none">
              <pre className="whitespace-pre-wrap text-sm text-gray-700">
                {scan.ai_recommendations}
              </pre>
            </div>
          </div>
        )}

        {/* Resource Summary */}
        {scan.status === 'completed' && scan.results && (
          <div className="rounded-lg bg-white p-6 shadow">
            <h2 className="mb-4 text-xl font-semibold">Resource Summary</h2>
            <div className="space-y-6">
              {Object.entries(scan.results).map(([region, data]: [string, any]) => (
                <div key={region} className="border-b border-gray-200 pb-4 last:border-0">
                  <h3 className="mb-3 font-semibold text-lg text-gray-900">{region}</h3>
                  <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                    <div className="rounded-lg bg-blue-50 p-4">
                      <p className="text-sm text-gray-600">EC2 Instances</p>
                      <p className="text-2xl font-bold text-blue-600">
                        {data.ec2?.count || 0}
                      </p>
                    </div>
                    <div className="rounded-lg bg-green-50 p-4">
                      <p className="text-sm text-gray-600">RDS Databases</p>
                      <p className="text-2xl font-bold text-green-600">
                        {data.rds?.count || 0}
                      </p>
                    </div>
                    <div className="rounded-lg bg-purple-50 p-4">
                      <p className="text-sm text-gray-600">Lambda Functions</p>
                      <p className="text-2xl font-bold text-purple-600">
                        {data.lambda?.count || 0}
                      </p>
                    </div>
                    <div className="rounded-lg bg-orange-50 p-4">
                      <p className="text-sm text-gray-600">S3 Buckets</p>
                      <p className="text-2xl font-bold text-orange-600">
                        {data.s3?.count || 0}
                      </p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </main>
    </div>
  )
}
