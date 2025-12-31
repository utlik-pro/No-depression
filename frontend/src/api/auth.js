import client from './client'

export const authApi = {
  login: async (password) => {
    const response = await client.post('/auth/login', { password })
    return response.data
  },

  logout: async () => {
    const response = await client.post('/auth/logout')
    return response.data
  },

  me: async () => {
    const response = await client.get('/auth/me')
    return response.data
  }
}
