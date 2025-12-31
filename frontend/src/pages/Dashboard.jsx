import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { dashboardApi } from '../api/dashboard'
import { Users, CheckCircle, TrendingUp, Activity } from 'lucide-react'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer
} from 'recharts'

function StatCard({ title, value, icon: Icon, color, subtext }) {
  return (
    <div className="bg-white rounded-xl shadow-sm p-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-gray-500">{title}</p>
          <p className="text-2xl font-bold mt-1">{value}</p>
          {subtext && <p className="text-sm text-gray-400 mt-1">{subtext}</p>}
        </div>
        <div className={`p-3 rounded-full ${color}`}>
          <Icon className="h-6 w-6 text-white" />
        </div>
      </div>
    </div>
  )
}

export default function Dashboard() {
  const [summary, setSummary] = useState(null)
  const [trends, setTrends] = useState([])
  const [activity, setActivity] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      const [summaryData, trendsData, activityData] = await Promise.all([
        dashboardApi.getSummary(),
        dashboardApi.getTrends(14),
        dashboardApi.getRecentActivity(10)
      ])
      setSummary(summaryData)
      setTrends(trendsData)
      setActivity(activityData)
    } catch (error) {
      console.error('Error loading dashboard:', error)
    } finally {
      setLoading(false)
    }
  }

  const getEventLabel = (eventType) => {
    const labels = {
      session_start: 'Начал тест',
      phase_complete: 'Завершил этап',
      question_answered: 'Ответил на вопрос',
      test_completed: 'Завершил тест',
      dropoff: 'Покинул'
    }
    return labels[eventType] || eventType
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-800 mb-6">Дашборд</h1>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <StatCard
          title="Всего пользователей"
          value={summary?.total_users || 0}
          icon={Users}
          color="bg-blue-500"
        />
        <StatCard
          title="Завершили тест"
          value={summary?.completed_users || 0}
          icon={CheckCircle}
          color="bg-green-500"
        />
        <StatCard
          title="Конверсия"
          value={`${(summary?.completion_rate || 0).toFixed(1)}%`}
          icon={TrendingUp}
          color="bg-purple-500"
        />
        <StatCard
          title="Ср. балл депрессии"
          value={summary?.avg_depression_score || 0}
          icon={Activity}
          color="bg-orange-500"
          subtext={`Тревога: ${summary?.avg_anxiety_score || 0}`}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Trends Chart */}
        <div className="bg-white rounded-xl shadow-sm p-6">
          <h2 className="text-lg font-semibold mb-4">Динамика за 14 дней</h2>
          {trends.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={trends}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis
                  dataKey="date"
                  tickFormatter={(date) => new Date(date).toLocaleDateString('ru-RU', { day: 'numeric', month: 'short' })}
                />
                <YAxis />
                <Tooltip
                  labelFormatter={(date) => new Date(date).toLocaleDateString('ru-RU')}
                />
                <Line
                  type="monotone"
                  dataKey="new_users"
                  stroke="#3B82F6"
                  name="Новые"
                  strokeWidth={2}
                />
                <Line
                  type="monotone"
                  dataKey="completions"
                  stroke="#10B981"
                  name="Завершили"
                  strokeWidth={2}
                />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-64 flex items-center justify-center text-gray-400">
              Нет данных для отображения
            </div>
          )}
        </div>

        {/* Recent Activity */}
        <div className="bg-white rounded-xl shadow-sm p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold">Последняя активность</h2>
            <Link to="/users" className="text-sm text-blue-600 hover:underline">
              Все пользователи
            </Link>
          </div>

          {activity.length > 0 ? (
            <div className="space-y-4">
              {activity.map((item, index) => (
                <div key={index} className="flex items-center justify-between py-2 border-b last:border-0">
                  <div>
                    <Link
                      to={`/users/${item.user_id}`}
                      className="font-medium text-gray-800 hover:text-blue-600"
                    >
                      {item.user_name}
                    </Link>
                    <p className="text-sm text-gray-500">
                      {getEventLabel(item.event_type)}
                      {item.phase && ` (${item.phase})`}
                    </p>
                  </div>
                  <span className="text-xs text-gray-400">
                    {new Date(item.timestamp).toLocaleString('ru-RU', {
                      hour: '2-digit',
                      minute: '2-digit'
                    })}
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <div className="h-64 flex items-center justify-center text-gray-400">
              Нет активности
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
