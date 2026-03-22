import { useState, useEffect } from 'react';
import ChatWidget from './ChatWidget';
import './App.css';

function App() {
  const [accessToken, setAccessToken] = useState(null);
  const [showLogin, setShowLogin] = useState(false);
  const [loginForm, setLoginForm] = useState({ clientId: 'demo_client', password: '' });

  const handleLogin = async () => {
    try {
      const response = await fetch('http://localhost:8000/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          client_id: loginForm.clientId,
          password: loginForm.password
        })
      });
      
      if (response.ok) {
        const data = await response.json();
        setAccessToken(data.access_token);
        setShowLogin(false);
        localStorage.setItem('client_token', data.access_token);
        alert('✅ Logged in! Settings button now available.');
      } else {
        alert('Invalid credentials. Try password: admin123');
      }
    } catch (error) {
      console.error('Login error:', error);
      alert('Login failed. Make sure backend is running.');
    }
  };

  // Check for saved token on mount
  useEffect(() => {
    const savedToken = localStorage.getItem('client_token');
    if (savedToken) {
      setAccessToken(savedToken);
    }
  }, []);

  return (
    <div className="App">
      {/* Floating Client Login Button (Top Right) */}
      {!accessToken && (
        <div style={{
          position: 'fixed',
          top: '20px',
          right: '20px',
          zIndex: 10000,
          background: 'white',
          padding: '12px',
          borderRadius: '12px',
          boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
          border: '2px solid #f59e0b'
        }}>
          {!showLogin ? (
            <button
              onClick={() => setShowLogin(true)}
              style={{
                padding: '10px 20px',
                background: '#f59e0b',
                color: 'white',
                border: 'none',
                borderRadius: '8px',
                fontSize: '14px',
                fontWeight: '600',
                cursor: 'pointer',
                fontFamily: 'Inter, sans-serif'
              }}
            >
              🔐 Client Login
            </button>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', minWidth: '200px' }}>
              <input
                type="password"
                placeholder="Password (admin123)"
                value={loginForm.password}
                onChange={(e) => setLoginForm({ ...loginForm, password: e.target.value })}
                onKeyPress={(e) => e.key === 'Enter' && handleLogin()}
                autoFocus
                style={{
                  padding: '10px',
                  border: '2px solid #d97706',
                  borderRadius: '6px',
                  fontSize: '14px',
                  fontFamily: 'Inter, sans-serif'
                }}
              />
              <div style={{ display: 'flex', gap: '6px' }}>
                <button
                  onClick={handleLogin}
                  style={{
                    flex: 1,
                    padding: '8px',
                    background: '#f59e0b',
                    color: 'white',
                    border: 'none',
                    borderRadius: '6px',
                    fontSize: '13px',
                    fontWeight: '600',
                    cursor: 'pointer'
                  }}
                >
                  Login
                </button>
                <button
                  onClick={() => setShowLogin(false)}
                  style={{
                    flex: 1,
                    padding: '8px',
                    background: 'white',
                    color: '#92400e',
                    border: '2px solid #d97706',
                    borderRadius: '6px',
                    fontSize: '13px',
                    fontWeight: '600',
                    cursor: 'pointer'
                  }}
                >
                  Cancel
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Logged In Indicator (Top Right) */}
      {accessToken && (
        <div style={{
          position: 'fixed',
          top: '20px',
          right: '20px',
          zIndex: 10000,
          background: '#10b981',
          color: 'white',
          padding: '10px 16px',
          borderRadius: '8px',
          fontSize: '13px',
          fontWeight: '600',
          boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
          display: 'flex',
          alignItems: 'center',
          gap: '12px'
        }}>
          <span>✅ Client Mode</span>
          <button
            onClick={() => {
              setAccessToken(null);
              localStorage.removeItem('client_token');
            }}
            style={{
              padding: '4px 10px',
              background: 'rgba(255,255,255,0.2)',
              color: 'white',
              border: '1px solid white',
              borderRadius: '4px',
              fontSize: '12px',
              cursor: 'pointer',
              fontWeight: '600'
            }}
          >
            Logout
          </button>
        </div>
      )}

      {/* Main Content */}
      <div style={{ padding: '40px', maxWidth: '800px', margin: '0 auto', fontFamily: 'Inter, sans-serif' }}>
        <h1 style={{ fontFamily: 'Poppins, sans-serif', fontSize: '36px', marginBottom: '16px' }}>
          🔧 Joe's Plumbing
        </h1>
        <p style={{ fontSize: '18px', lineHeight: '1.6', color: '#6b7280' }}>
          Welcome to Joe's Plumbing! Need help? Chat with our AI assistant.
        </p>
        
        <div style={{ background: '#f9fafb', padding: '24px', borderRadius: '12px', marginTop: '24px', border: '1px solid #e5e7eb' }}>
          <h2 style={{ fontFamily: 'Poppins, sans-serif', fontSize: '24px', marginBottom: '16px' }}>Our Services:</h2>
          <ul style={{ fontSize: '16px', lineHeight: '1.8', color: '#374151' }}>
            <li>24/7 Emergency Plumbing</li>
            <li>Drain Cleaning & Repair</li>
            <li>Water Heater Installation</li>
            <li>Leak Detection & Repair</li>
            <li>Pipe Repair & Replacement</li>
          </ul>
        </div>
        
        <div style={{ marginTop: '24px', padding: '20px', background: '#eff6ff', borderRadius: '12px', border: '2px solid #3b82f6' }}>
          <p style={{ margin: 0, fontSize: '16px', color: '#1e40af' }}>
            💬 <strong>Click the chat button in the bottom-right corner!</strong>
          </p>
        </div>

        {/* Instructions for Clients */}
        <div style={{ marginTop: '24px', padding: '16px', background: '#fef3c7', borderRadius: '8px', border: '1px solid #f59e0b' }}>
          <p style={{ margin: 0, fontSize: '14px', color: '#92400e' }}>
            <strong>👨‍💼 Business Owner?</strong> Click "Client Login" in the top-right corner to access settings.
          </p>
        </div>
      </div>

      {/* Chat Widget */}
      <ChatWidget 
        clientId="demo_client"
        apiUrl="http://localhost:8000"
        accessToken={accessToken}
      />
    </div>
  );
}

export default App;
