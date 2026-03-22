import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import axios from 'axios';
import SettingsPanel from './SettingsPanel';
import './ChatWidget.css';

const ChatWidget = ({ clientId, apiUrl = 'http://localhost:8000', accessToken = null }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [config, setConfig] = useState(null);
  const [quickReplies, setQuickReplies] = useState([]);
  const [showSettings, setShowSettings] = useState(false);
  const [widgetSize, setWidgetSize] = useState('medium'); // small, medium, large
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const messagesEndRef = useRef(null);
  
  const userId = useRef(`user_${Math.random().toString(36).substr(2, 9)}`).current;

  // Check authentication on mount and when accessToken changes
  useEffect(() => {
    console.log('🔑 Access token:', accessToken);
    if (accessToken) {
      verifyAuth();
    } else {
      setIsAuthenticated(false);
      console.log('❌ No access token provided');
    }
  }, [accessToken]);

  const verifyAuth = async () => {
    console.log('🔍 Verifying auth with token:', accessToken);
    try {
      const response = await axios.post(`${apiUrl}/auth/verify`, {
        client_id: clientId,
        access_token: accessToken
      });
      console.log('✅ Auth verified:', response.data.valid);
      setIsAuthenticated(response.data.valid);
    } catch (error) {
      console.error('❌ Auth verification failed:', error);
      setIsAuthenticated(false);
    }
  };

  // Debug: Log authentication state changes
  useEffect(() => {
    console.log('🎯 isAuthenticated changed to:', isAuthenticated);
  }, [isAuthenticated]);

  useEffect(() => {
    const loadConfig = async () => {
      try {
        const response = await axios.get(`${apiUrl}/config/${clientId}`);
        setConfig(response.data);
        
        setMessages([{
          role: 'assistant',
          content: response.data.widget_settings.greeting,
          timestamp: new Date()
        }]);
      } catch (error) {
        console.error('Failed to load config:', error);
        setConfig({
          business_name: 'AI Assistant',
          widget_settings: {
            primary_color: '#6366f1',
            greeting: 'Hi! How can I help you today?'
          }
        });
      }
    };
    
    loadConfig();
  }, [clientId, apiUrl]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const sendMessage = async (messageText = null) => {
    const textToSend = messageText || inputValue;
    if (!textToSend.trim() || isLoading) return;

    const userMessage = {
      role: 'user',
      content: textToSend,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setQuickReplies([]);
    setIsLoading(true);

    try {
      const response = await axios.post(`${apiUrl}/chat`, {
        client_id: clientId,
        user_id: userId,
        message: textToSend,
        conversation_history: messages.map(m => ({
          role: m.role,
          content: m.content
        }))
      });

      setMessages(prev => [...prev, {
        role: 'assistant',
        content: response.data.message,
        timestamp: new Date()
      }]);
      
      if (response.data.quick_replies && response.data.quick_replies.length > 0) {
        setQuickReplies(response.data.quick_replies);
      }
    } catch (error) {
      console.error('Chat error:', error);
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.',
        timestamp: new Date()
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleQuickReply = (value) => {
    sendMessage(value);
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const widgetConfig = config || {
    business_name: 'AI Assistant',
    widget_settings: {
      primary_color: '#6366f1',
      greeting: 'Hi! How can I help you today?'
    }
  };

  const sizeClasses = {
    small: 'widget-small',
    medium: 'widget-medium',
    large: 'widget-large'
  };

  return (
    <>
      <div className={`chat-widget-modern ${sizeClasses[widgetSize]}`}>
        {/* Floating Action Buttons */}
        <AnimatePresence>
          {!isOpen && (
            <motion.div
              className="fab-container"
              initial={{ scale: 0, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0, opacity: 0 }}
              transition={{ type: 'spring', stiffness: 260, damping: 20 }}
            >
              {/* Settings Button (Authenticated Only) */}
              {/* Debug: Always show for testing */}
              {(isAuthenticated || accessToken) && (
                <motion.button
                  className="fab-settings"
                  onClick={() => {
                    console.log('⚙️ Settings button clicked!');
                    setShowSettings(true);
                  }}
                  whileHover={{ scale: 1.1 }}
                  whileTap={{ scale: 0.9 }}
                  title="Manage Settings"
                >
                  <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                    <path d="M10 12.5C11.3807 12.5 12.5 11.3807 12.5 10C12.5 8.61929 11.3807 7.5 10 7.5C8.61929 7.5 7.5 8.61929 7.5 10C7.5 11.3807 8.61929 12.5 10 12.5Z" stroke="currentColor" strokeWidth="1.5"/>
                    <path d="M16.25 10C16.25 10.625 16.75 11.125 17.375 11.125C17.625 11.125 17.875 11.25 18 11.5L18.5 12.5C18.625 12.75 18.625 13 18.5 13.25L18 14.25C17.875 14.5 17.625 14.625 17.375 14.625C16.75 14.625 16.25 15.125 16.25 15.75C16.25 16 16.125 16.25 15.875 16.375L14.875 16.875C14.625 17 14.375 17 14.125 16.875L13.125 16.375C12.875 16.25 12.625 16.25 12.375 16.375C11.875 16.625 11.25 16.625 10.625 16.375C10.375 16.25 10.125 16.25 9.875 16.375L8.875 16.875C8.625 17 8.375 17 8.125 16.875L7.125 16.375C6.875 16.25 6.625 16.125 6.625 15.875C6.625 15.25 6.125 14.75 5.5 14.75C5.25 14.75 5 14.625 4.875 14.375L4.375 13.375C4.25 13.125 4.25 12.875 4.375 12.625L4.875 11.625C5 11.375 5.25 11.25 5.5 11.25C6.125 11.25 6.625 10.75 6.625 10.125C6.625 9.875 6.75 9.625 7 9.5L8 9C8.25 8.875 8.5 8.875 8.75 9L9.75 9.5C10 9.625 10.25 9.625 10.5 9.5C11 9.25 11.625 9.25 12.25 9.5C12.5 9.625 12.75 9.625 13 9.5L14 9C14.25 8.875 14.5 8.875 14.75 9L15.75 9.5C16 9.625 16.125 9.875 16.125 10.125C16.125 10.75 16.625 11.25 17.25 11.25C17.5 11.25 17.75 11.375 17.875 11.625L18.375 12.625C18.5 12.875 18.5 13.125 18.375 13.375L17.875 14.375C17.75 14.625 17.5 14.75 17.25 14.75C16.625 14.75 16.125 15.25 16.125 15.875" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
                  </svg>
                </motion.button>
              )}
              
              {/* Debug: Show auth status in dev */}
              <div style={{
                position: 'absolute',
                top: '-30px',
                right: '0',
                fontSize: '11px',
                background: (isAuthenticated || accessToken) ? '#10b981' : '#ef4444',
                color: 'white',
                padding: '4px 8px',
                borderRadius: '4px',
                whiteSpace: 'nowrap'
              }}>
                {(isAuthenticated || accessToken) ? '🔓 Auth OK' : '🔒 No Auth'}
                {accessToken && ` (Token: ${accessToken.substring(0, 8)}...)`}
              </div>
              
              {/* Main Chat Button */}
              <motion.button
                className="fab-main"
                onClick={() => setIsOpen(true)}
                style={{ backgroundColor: widgetConfig.widget_settings.primary_color }}
                whileHover={{ scale: 1.1 }}
                whileTap={{ scale: 0.9 }}
              >
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                  <path d="M12 22C17.5228 22 22 17.5228 22 12C22 6.47715 17.5228 2 12 2C6.47715 2 2 6.47715 2 12C2 13.5997 2.37562 15.1116 3.04346 16.4525C3.22094 16.8088 3.28001 17.2161 3.17712 17.6006L2.58151 19.8267C2.32295 20.793 3.20701 21.677 4.17335 21.4185L6.39939 20.8229C6.78393 20.72 7.19121 20.7791 7.54753 20.9565C8.88837 21.6244 10.4003 22 12 22Z" stroke="currentColor" strokeWidth="1.5"/>
                  <path d="M8 12H8.01M12 12H12.01M16 12H16.01" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
                </svg>
              </motion.button>

              {/* Size Toggle (Authenticated Only) */}
              {isAuthenticated && (
                <motion.button
                  className="fab-size"
                  onClick={() => {
                    const sizes = ['small', 'medium', 'large'];
                    const currentIndex = sizes.indexOf(widgetSize);
                    setWidgetSize(sizes[(currentIndex + 1) % sizes.length]);
                  }}
                  whileHover={{ scale: 1.1 }}
                  whileTap={{ scale: 0.9 }}
                  title={`Size: ${widgetSize}`}
                >
                  <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                    <rect x="3" y="3" width="14" height="14" rx="2" stroke="currentColor" strokeWidth="1.5"/>
                    <path d="M7 7L13 13M13 7L7 13" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
                  </svg>
                </motion.button>
              )}
            </motion.div>
          )}
        </AnimatePresence>

        {/* Chat Window */}
        <AnimatePresence>
          {isOpen && (
            <motion.div
              className="chat-window-modern"
              initial={{ opacity: 0, y: 20, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: 20, scale: 0.95 }}
              transition={{ type: 'spring', stiffness: 300, damping: 30 }}
            >
              {/* Header */}
              <div 
                className="chat-header-modern"
                style={{ 
                  background: `linear-gradient(135deg, ${widgetConfig.widget_settings.primary_color} 0%, ${widgetConfig.widget_settings.primary_color}dd 100%)`
                }}
              >
                <div className="header-content">
                  {widgetConfig.logo_url && (
                    <img src={widgetConfig.logo_url} alt="Logo" className="header-logo" />
                  )}
                  <div className="header-text">
                    <h3>{widgetConfig.business_name}</h3>
                    <span className="status-indicator">
                      <span className="status-dot"></span>
                      Online
                    </span>
                  </div>
                </div>
                <button 
                  className="close-button"
                  onClick={() => setIsOpen(false)}
                >
                  <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                    <path d="M15 5L5 15M5 5L15 15" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
                  </svg>
                </button>
              </div>

              {/* Messages */}
              <div className="messages-container">
                <AnimatePresence initial={false}>
                  {messages.map((msg, idx) => (
                    <motion.div
                      key={idx}
                      className={`message-bubble ${msg.role}`}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ duration: 0.3 }}
                    >
                      <div className="message-content">
                        {msg.content}
                      </div>
                      <div className="message-time">
                        {msg.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </div>
                    </motion.div>
                  ))}
                </AnimatePresence>
                
                {isLoading && (
                  <motion.div
                    className="message-bubble assistant"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                  >
                    <div className="typing-indicator">
                      <span></span>
                      <span></span>
                      <span></span>
                    </div>
                  </motion.div>
                )}
                <div ref={messagesEndRef} />
              </div>

              {/* Quick Replies */}
              <AnimatePresence>
                {quickReplies.length > 0 && !isLoading && (
                  <motion.div
                    className="quick-replies-modern"
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: 10 }}
                  >
                    {quickReplies.map((reply, idx) => (
                      <motion.button
                        key={idx}
                        className="quick-reply-btn"
                        onClick={() => handleQuickReply(reply.value || reply.text)}
                        whileHover={{ scale: 1.05 }}
                        whileTap={{ scale: 0.95 }}
                      >
                        {reply.text}
                      </motion.button>
                    ))}
                  </motion.div>
                )}
              </AnimatePresence>

              {/* Input */}
              <div className="input-container">
                <input
                  type="text"
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="Type your message..."
                  disabled={isLoading}
                  className="message-input"
                />
                <motion.button
                  className="send-button"
                  onClick={() => sendMessage()}
                  disabled={isLoading || !inputValue.trim()}
                  style={{ backgroundColor: widgetConfig.widget_settings.primary_color }}
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                >
                  <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                    <path d="M18 2L9 11M18 2L12 18L9 11M18 2L2 8L9 11" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                  </svg>
                </motion.button>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Settings Panel */}
      {showSettings && isAuthenticated && (
        <SettingsPanel
          clientId={clientId}
          apiUrl={apiUrl}
          onClose={() => setShowSettings(false)}
        />
      )}
    </>
  );
};

export default ChatWidget;
