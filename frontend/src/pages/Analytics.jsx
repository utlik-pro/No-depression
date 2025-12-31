import { useState, useEffect } from 'react'
import { analyticsApi } from '../api/analytics'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Legend
} from 'recharts'

const COLORS = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#EC4899', '#06B6D4']

export default function Analytics() {
  const [funnel, setFunnel] = useState([])
  const [scores, setScores] = useState({ depression: {}, anxiety: {} })
  const [demographics, setDemographics] = useState({ gender: {}, age: {}, location: {} })
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      const [funnelData, scoresData, demographicsData] = await Promise.all([
        analyticsApi.getFunnel(),
        analyticsApi.getScoreDistribution(),
        analyticsApi.getDemographics()
      ])
      setFunnel(funnelData)
      setScores(scoresData)
      setDemographics(demographicsData)
    } catch (error) {
      console.error('Error loading analytics:', error)
    } finally {
      setLoading(false)
    }
  }

  const formatPieData = (data) => {
    return Object.entries(data).map(([name, value]) => ({ name, value }))
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
      <h1 className="text-2xl font-bold text-gray-800 mb-6">Аналитика</h1>

      {/* Funnel */}
      <div className="bg-white rounded-xl shadow-sm p-6 mb-6">
        <h2 className="text-lg font-semibold mb-4">Воронка конверсии</h2>
        {funnel.length > 0 ? (
          <div className="space-y-4">
            {funnel.map((stage, index) => (
              <div key={stage.stage}>
                <div className="flex items-center justify-between mb-1">
                  <span className="text-sm font-medium">{stage.stage}</span>
                  <span className="text-sm text-gray-500">{stage.count} ({stage.percentage}%)</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-8">
                  <div
                    className="bg-blue-500 h-8 rounded-full flex items-center justify-end pr-3"
                    style={{ width: `${stage.percentage}%` }}
                  >
                    {stage.percentage > 10 && (
                      <span className="text-xs text-white font-medium">{stage.count}</span>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-gray-400 text-center py-8">Нет данных</p>
        )}
      </div>

      {/* Score Distribution */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        <div className="bg-white rounded-xl shadow-sm p-6">
          <h2 className="text-lg font-semibold mb-4">Распределение: Депрессия</h2>
          {Object.keys(scores.depression).length > 0 ? (
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={formatPieData(scores.depression)}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" tick={{ fontSize: 12 }} />
                <YAxis />
                <Tooltip />
                <Bar dataKey="value" fill="#8B5CF6" name="Кол-во" />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-64 flex items-center justify-center text-gray-400">Нет данных</div>
          )}
        </div>

        <div className="bg-white rounded-xl shadow-sm p-6">
          <h2 className="text-lg font-semibold mb-4">Распределение: Тревожность</h2>
          {Object.keys(scores.anxiety).length > 0 ? (
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={formatPieData(scores.anxiety)}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" tick={{ fontSize: 12 }} />
                <YAxis />
                <Tooltip />
                <Bar dataKey="value" fill="#F59E0B" name="Кол-во" />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-64 flex items-center justify-center text-gray-400">Нет данных</div>
          )}
        </div>
      </div>

      {/* Demographics */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="bg-white rounded-xl shadow-sm p-6">
          <h2 className="text-lg font-semibold mb-4">По полу</h2>
          {Object.keys(demographics.gender).length > 0 ? (
            <ResponsiveContainer width="100%" height={200}>
              <PieChart>
                <Pie
                  data={formatPieData(demographics.gender)}
                  cx="50%"
                  cy="50%"
                  innerRadius={40}
                  outerRadius={80}
                  paddingAngle={2}
                  dataKey="value"
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                >
                  {formatPieData(demographics.gender).map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-52 flex items-center justify-center text-gray-400">Нет данных</div>
          )}
        </div>

        <div className="bg-white rounded-xl shadow-sm p-6">
          <h2 className="text-lg font-semibold mb-4">По возрасту</h2>
          {Object.keys(demographics.age).length > 0 ? (
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={formatPieData(demographics.age)} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis type="number" />
                <YAxis dataKey="name" type="category" width={60} tick={{ fontSize: 12 }} />
                <Tooltip />
                <Bar dataKey="value" fill="#10B981" name="Кол-во" />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-52 flex items-center justify-center text-gray-400">Нет данных</div>
          )}
        </div>

        <div className="bg-white rounded-xl shadow-sm p-6">
          <h2 className="text-lg font-semibold mb-4">По региону</h2>
          {Object.keys(demographics.location).length > 0 ? (
            <div className="space-y-2 max-h-52 overflow-y-auto">
              {formatPieData(demographics.location)
                .sort((a, b) => b.value - a.value)
                .map((item, index) => (
                  <div key={item.name} className="flex items-center justify-between">
                    <span className="text-sm text-gray-600 truncate">{item.name}</span>
                    <span className="text-sm font-medium ml-2">{item.value}</span>
                  </div>
                ))}
            </div>
          ) : (
            <div className="h-52 flex items-center justify-center text-gray-400">Нет данных</div>
          )}
        </div>
      </div>
    </div>
  )
}
