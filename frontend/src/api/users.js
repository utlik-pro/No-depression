import client from './client'

export const usersApi = {
  getUsers: async (params = {}) => {
    const { page = 1, limit = 25, status, search } = params
    const queryParams = new URLSearchParams()
    queryParams.append('page', page)
    queryParams.append('limit', limit)
    if (status) queryParams.append('status', status)
    if (search) queryParams.append('search', search)

    const response = await client.get(`/users/?${queryParams}`)
    return response.data
  },

  getUser: async (userId) => {
    const response = await client.get(`/users/${userId}`)
    return response.data
  },

  getUserEvents: async (userId) => {
    const response = await client.get(`/users/${userId}/events`)
    return response.data
  },

  exportUsers: async (status) => {
    const params = status ? `?status=${status}` : ''
    const response = await client.get(`/users/export${params}`, {
      responseType: 'blob'
    })
    return response.data
  }
}
