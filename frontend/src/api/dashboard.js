import client from './client'

export const dashboardApi = {
  getSummary: async () => {
    const response = await client.get('/dashboard/summary')
    return response.data
  },

  getTrends: async (days = 30) => {
    const response = await client.get(`/dashboard/trends?days=${days}`)
    return response.data
  },

  getRecentActivity: async (limit = 10) => {
    const response = await client.get(`/dashboard/recent?limit=${limit}`)
    return response.data
  }
}
