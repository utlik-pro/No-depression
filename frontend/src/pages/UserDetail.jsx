import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { usersApi } from '../api/users'
import { ArrowLeft, User, Calendar, MapPin, CheckCircle, Clock } from 'lucide-react'

function ScoreIndicator({ score, type }) {
  let severity, color
  if (type === 'depression') {
    if (score <= 7) { severity = 'Норма'; color = 'text-green-600 bg-green-100' }
    else if (score <= 10) { severity = 'Субклинический'; color = 'text-yellow-600 bg-yellow-100' }
    else { severity = 'Клинический'; color = 'text-red-600 bg-red-100' }
  } else {
    if (score <= 9) { severity = 'Норма'; color = 'text-green-600 bg-green-100' }
    else if (score <= 18) { severity = 'Умеренный'; color = 'text-yellow-600 bg-yellow-100' }
    else if (score <= 29) { severity = 'Средний'; color = 'text-orange-600 bg-orange-100' }
    else { severity = 'Высокий'; color = 'text-red-600 bg-red-100' }
  }

  return (
    <div className={`px-3 py-2 rounded-lg ${color}`}>
      <div className="text-2xl font-bold">{score}</div>
      <div className="text-sm">{severity}</div>
    </div>
  )
}

export default function UserDetail() {
  const { userId } = useParams()
  const [user, setUser] = useState(null)
  const [events, setEvents] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadUser()
  }, [userId])

  const loadUser = async () => {
    try {
      const [userData, eventsData] = await Promise.all([
        usersApi.getUser(userId),
        usersApi.getUserEvents(userId)
      ])
      setUser(userData)
      setEvents(eventsData)
    } catch (error) {
      console.error('Error loading user:', error)
    } finally {
      setLoading(false)
    }
  }

  const getEventLabel = (event) => {
    const labels = {
      session_start: 'Начал тест',
      phase_complete: `Завершил этап: ${event.phase}`,
      question_answered: `Ответил на вопрос ${event.question_index + 1} (${event.question_type})`,
      test_completed: 'Завершил тест',
      dropoff: 'Покинул тест'
    }
    return labels[event.event_type] || event.event_type
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  if (!user) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500">Пользователь не найден</p>
        <Link to="/users" className="text-blue-600 hover:underline mt-4 inline-block">
          Вернуться к списку
        </Link>
      </div>
    )
  }

  return (
    <div>
      <Link to="/users" className="inline-flex items-center text-gray-600 hover:text-gray-800 mb-6">
        <ArrowLeft className="h-4 w-4 mr-2" />
        Назад к списку
      </Link>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* User Info Card */}
        <div className="lg:col-span-1">
          <div className="bg-white rounded-xl shadow-sm p-6">
            <div className="text-center mb-6">
              <div className="inline-flex items-center justify-center w-20 h-20 bg-blue-100 rounded-full mb-4">
                <User className="h-10 w-10 text-blue-600" />
              </div>
              <h2 className="text-xl font-bold">{user.first_name} {user.last_name}</h2>
              <p className="text-gray-500">@{user.username || 'нет username'}</p>
            </div>

            <div className="space-y-4">
              <div className="flex items-center text-gray-600">
                <User className="h-5 w-5 mr-3" />
                <span>{user.gender || 'Пол не указан'}</span>
              </div>
              <div className="flex items-center text-gray-600">
                <Calendar className="h-5 w-5 mr-3" />
                <span>{user.age_group || 'Возраст не указан'}</span>
              </div>
              <div className="flex items-center text-gray-600">
                <MapPin className="h-5 w-5 mr-3" />
                <span>{user.location || 'Регион не указан'}</span>
              </div>
              <div className="flex items-center text-gray-600">
                <Clock className="h-5 w-5 mr-3" />
                <span>{user.created_at ? new Date(user.created_at).toLocaleString('ru-RU') : '—'}</span>
              </div>
            </div>

            {/* Status */}
            <div className="mt-6 pt-6 border-t">
              <div className="flex items-center">
                {user.test_completed ? (
                  <>
                    <CheckCircle className="h-5 w-5 text-green-500 mr-2" />
                    <span className="text-green-600 font-medium">Тест завершен</span>
                  </>
                ) : (
                  <>
                    <Clock className="h-5 w-5 text-yellow-500 mr-2" />
                    <span className="text-yellow-600 font-medium">
                      Этап: {user.current_phase}
                    </span>
                  </>
                )}
              </div>
            </div>
          </div>

          {/* Scores */}
          {user.test_completed && (
            <div className="bg-white rounded-xl shadow-sm p-6 mt-6">
              <h3 className="font-semibold mb-4">Результаты</h3>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-gray-500 mb-2">Депрессия</p>
                  <ScoreIndicator score={user.depression_score} type="depression" />
                </div>
                <div>
                  <p className="text-sm text-gray-500 mb-2">Тревожность</p>
                  <ScoreIndicator score={user.anxiety_score} type="anxiety" />
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Events Timeline */}
        <div className="lg:col-span-2">
          <div className="bg-white rounded-xl shadow-sm p-6">
            <h3 className="font-semibold mb-6">История событий</h3>

            {events.length > 0 ? (
              <div className="space-y-4">
                {events.map((event, index) => (
                  <div key={event.id || index} className="flex items-start">
                    <div className="flex-shrink-0 w-2 h-2 mt-2 rounded-full bg-blue-500"></div>
                    <div className="ml-4 flex-1">
                      <p className="text-gray-800">{getEventLabel(event)}</p>
                      <p className="text-sm text-gray-400">
                        {new Date(event.created_at).toLocaleString('ru-RU')}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-400 text-center py-8">Нет событий</p>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
