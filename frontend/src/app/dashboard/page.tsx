'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useQuery } from '@tanstack/react-query'
import { scanAPI, credentialsAPI, authAPI } from '@/lib/api'
import Link from 'next/link'

export default function DashboardPage() {
  const router = useRouter()
  const [user, setUser] = useState<any>(null)

  useEffect(() => {
    const token = localStorage.getItem('token')
    if (!token) {
      router.push('/login')
      return
    }

    authAPI.getMe().then((res) => setUser(res.data)).catch(() => router.push('/login'))
  }, [router])

  const { data: scans, isLoading: scansLoading } = useQuery({
    queryKey: ['scans'],
    queryFn: async () => {
      const response = await scanAPI.list()
      return response.data
    },
  })

  const { data: credentials } = useQuery({
    queryKey: ['credentials'],
    queryFn: async () => {
      const response = await credentialsAPI.list()
      return response.data
    },
  })

  const handleLogout = () => {
    localStorage.removeItem('token')
    router.push('/login')
  }

  if (!user) return <div className="flex min-h-screen items-center justify-center">Loading...</div>

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow">
        <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
              <p className="mt-1 text-sm text-gray-600">Welcome, {user.username}</p>
            </div>
            <button
              onClick={handleLogout}
              className="rounded-md bg-red-600 px-4 py-2 text-white hover:bg-red-700"
            >
              Logout
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        {/* Quick Actions */}
        <div className="mb-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <Link
            href="/dashboard/credentials"
            className="rounded-lg bg-white p-6 shadow hover:shadow-lg transition-shadow"
          >
            <h3 className="text-lg font-semibold text-gray-900">Credentials</h3>
            <p className="mt-2 text-3xl font-bold text-primary">{credentials?.length || 0}</p>
            <p className="mt-1 text-sm text-gray-600">Manage AWS credentials</p>
          </Link>

          <Link
            href="/dashboard/scans/new"
            className="rounded-lg bg-primary p-6 shadow hover:shadow-lg transition-shadow text-white"
          >
            <h3 className="text-lg font-semibold">New Scan</h3>
            <p className="mt-2 text-3xl font-bold">+</p>
            <p className="mt-1 text-sm">Start assessment</p>
          </Link>

          <Link
            href="/dashboard/documents"
            className="rounded-lg bg-white p-6 shadow hover:shadow-lg transition-shadow"
          >
            <h3 className="text-lg font-semibold text-gray-900">Documents</h3>
            <p className="mt-2 text-3xl font-bold text-primary">📄</p>
            <p className="mt-1 text-sm text-gray-600">Upload WA docs</p>
          </Link>

          <div className="rounded-lg bg-white p-6 shadow">
            <h3 className="text-lg font-semibold text-gray-900">Total Scans</h3>
            <p className="mt-2 text-3xl font-bold text-primary">{scans?.length || 0}</p>
            <p className="mt-1 text-sm text-gray-600">All assessments</p>
          </div>
        </div>

        {/* Recent Scans */}
        <div className="rounded-lg bg-white shadow">
          <div className="border-b border-gray-200 px-6 py-4">
            <h2 className="text-xl font-semibold text-gray-900">Recent Scans</h2>
          </div>
          <div className="p-6">
            {scansLoading ? (
              <p className="text-gray-600">Loading scans...</p>
            ) : scans && scans.length > 0 ? (
              <div className="space-y-4">
                {scans.slice(0, 5).map((scan: any) => (
                  <Link
                    key={scan.id}
                    href={`/dashboard/scans/${scan.id}`}
                    className="block rounded-lg border border-gray-200 p-4 hover:border-primary hover:shadow-md transition-all"
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <h3 className="font-semibold text-gray-900">{scan.scan_name}</h3>
                        <p className="text-sm text-gray-600">
                          {new Date(scan.created_at).toLocaleDateString()}
                        </p>
                      </div>
                      <div className="flex items-center gap-4">
                        <div className="text-right">
                          <span
                            className={`inline-block rounded-full px-3 py-1 text-sm font-semibold ${
                              scan.status === 'completed'
                                ? 'bg-green-100 text-green-800'
                                : scan.status === 'running'
                                ? 'bg-blue-100 text-blue-800'
                                : scan.status === 'failed'
                                ? 'bg-red-100 text-red-800'
                                : 'bg-gray-100 text-gray-800'
                            }`}
                          >
                            {scan.status}
                          </span>
                          {scan.status === 'running' && (
                            <p className="mt-1 text-sm text-gray-600">{scan.progress}%</p>
                          )}
                        </div>
                      </div>
                    </div>
                  </Link>
                ))}
              </div>
            ) : (
              <div className="text-center py-8">
                <p className="text-gray-600">No scans yet</p>
                <Link
                  href="/dashboard/scans/new"
                  className="mt-4 inline-block rounded-md bg-primary px-4 py-2 text-white hover:bg-primary/90"
                >
                  Start Your First Scan
                </Link>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  )
}
