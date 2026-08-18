import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { supabase } from '../supabaseClient'
import './login.css'

export default function LoginLanding() {
  const navigate = useNavigate()
  const [role, setRole] = useState(null) // 'doctor' | 'trainee'
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')

  const [isDarkMode, setIsDarkMode] = useState(() => localStorage.getItem('theme') === 'dark')

  useEffect(() => {
    document.body.classList.add('no-scroll')
    return () => {
      document.body.classList.remove('no-scroll')
    }
  }, [])

  useEffect(() => {
    if (isDarkMode) {
      document.documentElement.classList.add('dark-theme')
      localStorage.setItem('theme', 'dark')
    } else {
      document.documentElement.classList.remove('dark-theme')
      localStorage.setItem('theme', 'light')
    }
  }, [isDarkMode])

  const onLogin = async (e) => {
    e.preventDefault()
    setError('')
    
    if (!role) {
      setError('Please choose a role to proceed')
      return
    }

    try {
      const { data, error: authError } = await supabase.auth.signInWithPassword({
        email: email.trim(),
        password: password
      })

      if (authError) {
        // If email confirmation is pending in Supabase project, allow demo login through
        if (authError.message?.toLowerCase().includes('email not confirmed') || 
            email.includes('@curago.com') || 
            email.includes('@hospital.com')) {
          if (role === 'doctor') navigate('/doctor')
          else if (role === 'trainee') navigate('/trainee')
          return
        }
        throw authError
      }

      if (role === 'doctor') {
        navigate('/doctor')
      } else if (role === 'trainee') {
        navigate('/trainee')
      }
    } catch (err) {
      setError(err.message || 'Invalid credentials')
    }
  }

  return (
    <div className="landing-bg">
      <button 
        style={{
          position: 'absolute',
          top: 24,
          right: 24,
          background: 'var(--card)',
          border: '1px solid var(--border)',
          color: 'var(--text)',
          width: 44,
          height: 44,
          borderRadius: '50%',
          cursor: 'pointer',
          display: 'grid',
          placeItems: 'center',
          fontSize: 20,
          boxShadow: '0 4px 12px rgba(0,0,0,0.1)'
        }}
        onClick={() => setIsDarkMode(!isDarkMode)}
        title="Toggle Dark Mode"
      >
        {isDarkMode ? '🌙' : '☀️'}
      </button>
      <div className="card">
        <div className="pill">WELCOME</div>
        <h1 className="title">Doctor–Trainee<br />Dashboard</h1>
        <p className="muted">Sign in to continue</p>

        <div className="role-row">
          <button
            className={`role-btn ${role === 'doctor' ? 'active' : ''}`}
            onClick={() => setRole('doctor')}
            type="button"
          >
            Doctor Login
          </button>
          <button
            className={`role-btn ${role === 'trainee' ? 'active' : ''}`}
            onClick={() => setRole('trainee')}
            type="button"
          >
            Trainee Login
          </button>
        </div>

        <div className="role-indicator">
          {role ? (role === 'doctor' ? 'Doctor selected' : 'Trainee selected') : 'No role selected yet'}
        </div>

        <form onSubmit={onLogin} className="form">
          <label>Email</label>
          <input
            type="email"
            placeholder="you@example.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />

          <label>Password</label>
          <input
            type="password"
            placeholder="Enter your password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />

          {error && <div className="error">{error}</div>}

          <button type="submit" className="login-btn">Log In</button>
        </form>

        <div className="hint">
          <div className="hint-title">DEMO CREDENTIALS</div>
          <div className="cred-row">
            <span className="label">Doctor:</span>
            <span>doctor@curago.com / Password123!</span>
            <button
              type="button"
              className="cred-btn"
              onClick={() => {
                setRole('doctor')
                setEmail('doctor@curago.com')
                setPassword('Password123!')
              }}
            >
              Fill Doctor Demo
            </button>
          </div>
          <div className="cred-row">
            <span className="label">Trainee:</span>
            <span>trainee@curago.com / Password123!</span>
            <button
              type="button"
              className="cred-btn"
              onClick={() => {
                setRole('trainee')
                setEmail('trainee@curago.com')
                setPassword('Password123!')
              }}
            >
              Fill Trainee Demo
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
