import api from './client'

export const createBooking = (data) => api.post('/bookings', data)
export const getBooking = (id) => api.get(`/bookings/${id}`)
export const cancelBooking = (id) => api.delete(`/bookings/${id}`)
export const getMyJourneys = () => api.get('/bookings/my/journeys')
