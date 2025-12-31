import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { usersApi } from '../api/users'
import { Search, Download, ChevronLeft, ChevronRight } from 'lucide-react'

function StatusBadge({ completed, phase }) {
  if (completed) {
    return <span className="px-2 py-1 text-xs font-medium bg-green-100 text-green-700 rounded-full">Завершен</span>
  }
  if (phase === 'consent') {
    return <span className="px-2 py-1 text-xs font-medium bg-gray-100 text-gray-600 rounded-full">Ожидание</span>
  }
  return <span className="px-2 py-1 text-xs font-medium bg-yellow-100 text-yellow-700 rounded-full">В процессе</span>
}

export default function Users() {
  const [users, setUsers] = useState([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [status, setStatus] = useState('')
  const [loading, setLoading] = useState(true)
  const limit = 25

  useEffect(() => {
    loadUsers()
  }, [page, status])

  const loadUsers = async () => {
    setLoading(true)
    try {
      const data = await usersApi.getUsers({ page, limit, status: status || undefined, search: search || undefined })
      setUsers(data.users)
      setTotal(data.total)
    } catch (error) {
      console.error('Error loading users:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleSearch = (e) => {
    e.preventDefault()
    setPage(1)
    loadUsers()
  }

  const handleExport = async () => {
    try {
      const blob = await usersApi.exportUsers(status || undefined)
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = 'users_export.csv'
      a.click()
      window.URL.revokeObjectURL(url)
    } catch (error) {
      console.error('Error exporting:', error)
    }
  }

  const totalPages = Math.ceil(total / limit)

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-800">Пользователи</h1>
        <button
          onClick={handleExport}
          className="flex items-center px-4 py-2 bg-white border rounded-lg hover:bg-gray-50 transition"
        >
          <Download className="h-4 w-4 mr-2" />
          Экспорт CSV
        </button>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-xl shadow-sm p-4 mb-6">
        <div className="flex flex-col md:flex-row gap-4">
          <form onSubmit={handleSearch} className="flex-1">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Поиск по имени или username..."
                className="w-full pl-10 pr-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
              />
            </div>
          </form>

          <select
            value={status}
            onChange={(e) => { setStatus(e.target.value); setPage(1) }}
            className="px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
          >
            <option value="">Все статусы</option>
            <option value="completed">Завершили</option>
            <option value="in_progress">В процессе</option>
            <option value="dropped">Покинули</option>
          </select>
        </div>
      </div>

      {/* Table */}
      <div className="bg-white rounded-xl shadow-sm overflow-hidden">
        {loading ? (
          <div className="flex items-center justify-center h-64">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          </div>
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Пользователь</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Демография</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Статус</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Баллы</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Дата</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {users.map((user) => (
                    <tr key={user.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4">
                        <Link to={`/users/${user.id}`} className="hover:text-blue-600">
                          <div className="font-medium text-gray-900">
                            {user.first_name} {user.last_name}
                          </div>
                          <div className="text-sm text-gray-500">
                            @{user.username || 'нет username'}
                          </div>
                        </Link>
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-500">
                        <div>{user.gender || '—'}</div>
                        <div>{user.age_group || '—'}, {user.location || '—'}</div>
                      </td>
                      <td className="px-6 py-4">
                        <StatusBadge completed={user.test_completed} phase={user.current_phase} />
                      </td>
                      <td className="px-6 py-4 text-sm">
                        {user.test_completed ? (
                          <div>
                            <span className="text-purple-600">Д: {user.depression_score}</span>
                            {' / '}
                            <span className="text-orange-600">Т: {user.anxiety_score}</span>
                          </div>
                        ) : '—'}
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-500">
                        {user.created_at ? new Date(user.created_at).toLocaleDateString('ru-RU') : '—'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="flex items-center justify-between px-6 py-4 border-t">
                <div className="text-sm text-gray-500">
                  Показано {((page - 1) * limit) + 1} - {Math.min(page * limit, total)} из {total}
                </div>
                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => setPage(p => Math.max(1, p - 1))}
                    disabled={page === 1}
                    className="p-2 rounded-lg hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <ChevronLeft className="h-5 w-5" />
                  </button>
                  <span className="text-sm">
                    Страница {page} из {totalPages}
                  </span>
                  <button
                    onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                    disabled={page === totalPages}
                    className="p-2 rounded-lg hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <ChevronRight className="h-5 w-5" />
                  </button>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}
