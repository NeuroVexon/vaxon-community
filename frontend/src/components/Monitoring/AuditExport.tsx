import { useState } from 'react'
import { Download, FileJson, FileSpreadsheet, Loader2 } from 'lucide-react'
import clsx from 'clsx'

interface AuditExportProps {
  sessionId?: string
}

type ExportFormat = 'csv' | 'json'

export default function AuditExport({ sessionId }: AuditExportProps) {
  const [exporting, setExporting] = useState(false)
  const [format, setFormat] = useState<ExportFormat>('csv')

  const handleExport = async () => {
    setExporting(true)

    try {
      const params = new URLSearchParams()
      params.set('format', format)
      if (sessionId) params.set('session_id', sessionId)

      const url = `/api/v1/audit/export?${params}`

      if (format === 'csv') {
        // Download CSV file
        window.open(url, '_blank')
      } else {
        // Fetch JSON and download
        const response = await fetch(url)
        const data = await response.json()

        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
        const downloadUrl = URL.createObjectURL(blob)

        const a = document.createElement('a')
        a.href = downloadUrl
        a.download = `axon_audit_${new Date().toISOString().slice(0, 10)}.json`
        document.body.appendChild(a)
        a.click()
        document.body.removeChild(a)
        URL.revokeObjectURL(downloadUrl)
      }
    } catch (error) {
      console.error('Export failed:', error)
    }

    setExporting(false)
  }

  return (
    <div className="flex items-center gap-3">
      {/* Format Selection */}
      <div className="flex rounded-lg overflow-hidden border border-nv-gray-light">
        <button
          onClick={() => setFormat('csv')}
          className={clsx(
            'px-3 py-2 flex items-center gap-2 text-sm transition-colors',
            format === 'csv'
              ? 'bg-nv-accent text-nv-black'
              : 'bg-nv-black-lighter text-gray-400 hover:text-white'
          )}
        >
          <FileSpreadsheet className="w-4 h-4" />
          CSV
        </button>
        <button
          onClick={() => setFormat('json')}
          className={clsx(
            'px-3 py-2 flex items-center gap-2 text-sm transition-colors',
            format === 'json'
              ? 'bg-nv-accent text-nv-black'
              : 'bg-nv-black-lighter text-gray-400 hover:text-white'
          )}
        >
          <FileJson className="w-4 h-4" />
          JSON
        </button>
      </div>

      {/* Export Button */}
      <button
        onClick={handleExport}
        disabled={exporting}
        className="px-4 py-2 bg-nv-accent text-nv-black font-semibold rounded-lg
                   hover:bg-opacity-90 disabled:opacity-50 disabled:cursor-not-allowed
                   flex items-center gap-2 transition-colors"
      >
        {exporting ? (
          <Loader2 className="w-4 h-4 animate-spin" />
        ) : (
          <Download className="w-4 h-4" />
        )}
        Export
      </button>
    </div>
  )
}
