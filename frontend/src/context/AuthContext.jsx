import { createContext, useContext, useState } from 'react'
import api from '../api'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem('token'))

  const login = async (email, password) => {
    localStorage.removeItem('token')
    const { data } = await api.post('/auth/login', { email, password })
    localStorage.setItem('token', data.access_token)
    setToken(data.access_token)
    window.location.href = '/app'
  }

  const signup = async (email, password) => {
    localStorage.removeItem('token')
    const { data } = await api.post('/auth/signup', { email, password })
    localStorage.setItem('token', data.access_token)
    setToken(data.access_token)
    window.location.href = '/app'
  }

  const logout = () => {
    localStorage.removeItem('token')
    setToken(null)
    window.location.href = '/login'
  }

  return (
    <AuthContext.Provider value={{ token, login, signup, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => useContext(AuthContext)
