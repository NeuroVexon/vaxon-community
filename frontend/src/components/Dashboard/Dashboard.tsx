import { useState, useEffect } from 'react'
import { api } from '../../services/api'
import {
  BarChart3,
  MessageSquare,
  Bot,
  Wrench,
  ShieldCheck,
  Clock,
  GitBranch,
  Puzzle,
  Loader2,
  TrendingUp,
  AlertTriangle
} from 'lucide-react'
import clsx from 'clsx'
import { useTranslation } from 'react-i18next'
import type { View } from '../../types'

interface Overview {
  conversations: number
  messages: number
  agents: number
  tool_calls: number
  approval_rate: number
  active_tasks: number
  workflows: number
  active_skills: number
}

interface ToolStat {
  tool: string
  count: number
  avg_time_ms: number
  failures: number
  error_rate: number
}

interface TimelineEntry {
  date: string
  conversations: number
  tool_calls: number
}

interface DashboardProps {
  onNavigate?: (view: View) => void
}

export default function Dashboard({ onNavigate }: DashboardProps) {
  const [overview, setOverview] = useState<Overview | null>(null)
  const [tools, setTools] = useState<ToolStat[]>([])
  const [timeline, setTimeline] = useState<TimelineEntry[]>([])
  const [loading, setLoading] = useState(true)
  const { t } = useTranslation()

  useEffect(() => {
    loadDashboard()
  }, [])

  const loadDashboard = async () => {
    setLoading(true)
    try {
      const [ov, toolData, tlData] = await Promise.all([
        api.getAnalyticsOverview(),
        api.getAnalyticsTools(),
        api.getAnalyticsTimeline(30),
      ])
      setOverview(ov)
      setTools(toolData.tools)
      setTimeline(tlData.timeline)
    } catch (error) {
      console.error('Failed to load dashboard:', error)
    }
    setLoading(false)
  }

  if (loading) {
    return (
      <div className="h-full flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-nv-accent" />
      </div>
    )
  }

  const statCards = overview ? [
    { label: t('dashboard.conversations'), value: overview.conversations, icon: MessageSquare, color: 'text-blue-400', link: 'chat' as View },
    { label: t('dashboard.messages'), value: overview.messages, icon: TrendingUp, color: 'text-green-400', link: 'chat' as View },
    { label: t('dashboard.agents'), value: overview.agents, icon: Bot, color: 'text-purple-400', link: 'agents' as View },
    { label: t('dashboard.toolCalls'), value: overview.tool_calls, icon: Wrench, color: 'text-nv-accent', link: 'audit' as View },
    { label: t('dashboard.approvalRate'), value: `${overview.approval_rate}%`, icon: ShieldCheck, color: 'text-yellow-400', link: 'audit' as View },
    { label: t('dashboard.activeTasks'), value: overview.active_tasks, icon: Clock, color: 'text-orange-400', link: 'scheduler' as View },
    { label: t('dashboard.workflows'), value: overview.workflows, icon: GitBranch, color: 'text-pink-400', link: 'workflows' as View },
    { label: t('dashboard.skills'), value: overview.active_skills, icon: Puzzle, color: 'text-teal-400', link: 'skills' as View },
  ] : []

  // Einfaches Balkendiagramm fuer Timeline
  const maxToolCalls = Math.max(...timeline.map(t => t.tool_calls), 1)
  const maxConvs = Math.max(...timeline.map(t => t.conversations), 1)

  return (
    <div className="h-full overflow-auto p-8">
      <div className="max-w-6xl mx-auto">
        <div className="flex items-center gap-3 mb-8">
          <BarChart3 className="w-8 h-8 text-nv-accent" />
          <h1 className="text-2xl font-bold">{t('dashboard.title')}</h1>
        </div>

        {/* Stat Cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          {statCards.map((stat) => {
            const Icon = stat.icon
            return (
              <button
                key={stat.label}
                onClick={() => onNavigate?.(stat.link)}
                className="bg-nv-black-200 rounded-xl p-5 border border-nv-gray-light text-left
                           hover:border-nv-accent hover:bg-nv-black-lighter transition-all cursor-pointer"
              >
                <div className="flex items-center gap-2 mb-2">
                  <Icon className={clsx('w-4 h-4', stat.color)} />
                  <span className="text-xs text-gray-500 uppercase tracking-wider">{stat.label}</span>
                </div>
                <p className="text-2xl font-bold">{stat.value}</p>
              </button>
            )
          })}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Timeline Chart */}
          <div className="bg-nv-black-200 rounded-xl p-6 border border-nv-gray-light">
            <h2 className="text-lg font-semibold mb-4">{t('dashboard.timeline')}</h2>
            {timeline.length > 0 ? (
              <div>
                <div className="flex items-center gap-4 mb-3 text-xs text-gray-500">
                  <span className="flex items-center gap-1">
                    <span className="w-3 h-3 bg-nv-accent rounded-sm inline-block" /> {t('dashboard.toolCalls')}
                  </span>
                  <span className="flex items-center gap-1">
                    <span className="w-3 h-3 bg-blue-400 rounded-sm inline-block" /> {t('dashboard.conversations')}
                  </span>
                </div>
                <div className="flex items-end gap-px h-32">
                  {timeline.slice(-30).map((day, i) => (
                    <div key={i} className="flex-1 flex flex-col items-center gap-px" title={`${day.date}: ${day.conversations} Conv, ${day.tool_calls} Tools`}>
                      <div
                        className="w-full bg-nv-accent/60 rounded-t-sm"
                        style={{ height: `${(day.tool_calls / maxToolCalls) * 100}%`, minHeight: day.tool_calls > 0 ? '2px' : '0' }}
                      />
                      <div
                        className="w-full bg-blue-400/60 rounded-t-sm"
                        style={{ height: `${(day.conversations / maxConvs) * 50}%`, minHeight: day.conversations > 0 ? '2px' : '0' }}
                      />
                    </div>
                  ))}
                </div>
                <div className="flex justify-between mt-1 text-xs text-gray-600">
                  <span>{timeline.length > 0 ? timeline[0].date.slice(5) : ''}</span>
                  <span>{timeline.length > 0 ? timeline[timeline.length - 1].date.slice(5) : ''}</span>
                </div>
              </div>
            ) : (
              <p className="text-gray-500 text-sm">{t('dashboard.noData')}</p>
            )}
          </div>

          {/* Tool Usage */}
          <div className="bg-nv-black-200 rounded-xl p-6 border border-nv-gray-light">
            <h2 className="text-lg font-semibold mb-4">{t('dashboard.toolUsage')}</h2>
            {tools.length > 0 ? (
              <div className="space-y-3">
                {tools.slice(0, 8).map((tool) => {
                  const maxCount = Math.max(...tools.map(t => t.count))
                  return (
                    <div key={tool.tool}>
                      <div className="flex items-center justify-between text-sm mb-1">
                        <span className="font-mono text-gray-300">{tool.tool}</span>
                        <div className="flex items-center gap-3 text-xs text-gray-500">
                          <span>{tool.count}x</span>
                          <span>{tool.avg_time_ms}ms</span>
                          {tool.error_rate > 0 && (
                            <span className="flex items-center gap-1 text-red-400">
                              <AlertTriangle className="w-3 h-3" />
                              {tool.error_rate}%
                            </span>
                          )}
                        </div>
                      </div>
                      <div className="w-full bg-nv-black rounded-full h-2">
                        <div
                          className="bg-nv-accent h-2 rounded-full transition-all"
                          style={{ width: `${(tool.count / maxCount) * 100}%` }}
                        />
                      </div>
                    </div>
                  )
                })}
              </div>
            ) : (
              <p className="text-gray-500 text-sm">{t('dashboard.noToolCalls')}</p>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
