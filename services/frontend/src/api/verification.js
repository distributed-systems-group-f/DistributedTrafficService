import api from './client'

export const verifyPlate = (plate) => api.get(`/verify/${plate}`)
