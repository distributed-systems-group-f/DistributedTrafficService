import api from './client'

export const getDashboard = () => api.get('/analytics/dashboard')
export const getCapacityReport = () => api.get('/analytics/reports/capacity')
