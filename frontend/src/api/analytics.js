import client from './client'

export const analyticsApi = {
  getFunnel: async () => {
    const response = await client.get('/analytics/funnel')
    return response.data
  },

  getQuestionDropoff: async () => {
    const response = await client.get('/analytics/question-dropoff')
    return response.data
  },

  getScoreDistribution: async () => {
    const response = await client.get('/analytics/scores')
    return response.data
  },

  getDemographics: async () => {
    const response = await client.get('/analytics/demographics')
    return response.data
  }
}
