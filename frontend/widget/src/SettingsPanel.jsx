import { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import './SettingsPanel.css';

const SettingsPanel = ({ clientId, apiUrl, onClose }) => {
  const [step, setStep] = useState(1); // Guided steps
  const [knowledge, setKnowledge] = useState([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [result, setResult] = useState(null);
  const [uploadMethod, setUploadMethod] = useState(null); // 'website', 'document', 'manual'
  const fileInputRef = useRef(null);

  // Bot settings state
  const [botSettings, setBotSettings] = useState(null);
  const [settingsChanged, setSettingsChanged] = useState(false);

  // Website scraping state
  const [websiteUrl, setWebsiteUrl] = useState('');

  // Document upload state
  const [dragActive, setDragActive] = useState(false);
  const [uploadedFile, setUploadedFile] = useState(null);

  // Manual entry state
  const [manualData, setManualData] = useState({
    category: 'services',
    title: '',
    content: '',
    tags: ''
  });

  useEffect(() => {
    loadKnowledge();
    loadBotSettings();
  }, []);

  const loadKnowledge = async () => {
    try {
      const response = await axios.get(`${apiUrl}/knowledge/${clientId}`);
      setKnowledge(response.data.knowledge);
    } catch (error) {
      console.error('Error loading knowledge:', error);
    }
  };

  const loadBotSettings = async () => {
    try {
      const response = await axios.get(`${apiUrl}/settings/${clientId}`);
      setBotSettings(response.data);
    } catch (error) {
      console.error('Error loading settings:', error);
    }
  };

  // Helper function for placeholders
  const getCategoryPlaceholder = (category, field) => {
    const placeholders = {
      services: {
        title: 'e.g., Emergency Plumbing Service',
        content: 'Describe what this service includes, pricing, availability...'
      },
      pricing: {
        title: 'e.g., Standard Service Call',
        content: '$50 service call fee, $99/hour labor rate...'
      },
      faqs: {
        title: 'e.g., Do you offer same-day service?',
        content: 'Yes, we offer same-day service for most requests...'
      },
      company: {
        title: 'e.g., About Our Company',
        content: '20+ years serving the community, family-owned...'
      },
      contact: {
        title: 'e.g., Contact Information',
        content: 'Phone: (555) 123-4567, Email: info@business.com...'
      }
    };
    
    return placeholders[category]?.[field] || '';
  };

  // Step 1: Choose method
  const renderMethodSelection = () => (
    <div className="method-selection">
      <h2>📚 Build Your Knowledge Base</h2>
      <p className="subtitle">Choose how you'd like to add information about your business:</p>

      <div className="method-cards">
        <div 
          className={`method-card ${uploadMethod === 'website' ? 'selected' : ''}`}
          onClick={() => {
            setUploadMethod('website');
            setStep(2);
          }}
        >
          <div className="method-icon">🌐</div>
          <h3>Scrape Website</h3>
          <p>Automatically extract info from your website</p>
          <div className="method-badge">Recommended</div>
        </div>

        <div 
          className={`method-card ${uploadMethod === 'document' ? 'selected' : ''}`}
          onClick={() => {
            setUploadMethod('document');
            setStep(2);
          }}
        >
          <div className="method-icon">📄</div>
          <h3>Upload Documents</h3>
          <p>PDF, DOCX, TXT files with business info</p>
        </div>

        <div 
          className={`method-card ${uploadMethod === 'manual' ? 'selected' : ''}`}
          onClick={() => {
            setUploadMethod('manual');
            setStep(2);
          }}
        >
          <div className="method-icon">✍️</div>
          <h3>Enter Manually</h3>
          <p>Type in services, pricing, FAQs</p>
        </div>
      </div>

      {knowledge.length > 0 && (
        <button 
          className="view-existing-btn"
          onClick={() => setStep(3)}
        >
          View Existing Knowledge ({knowledge.length} items)
        </button>
      )}

      <button 
        className="settings-link-btn"
        onClick={() => setStep(4)}
      >
        ⚙️ Bot Settings & Personality
      </button>
    </div>
  );

  // Step 2: Execute chosen method
  const renderMethodExecution = () => {
    if (uploadMethod === 'website') {
      return renderWebsiteScrape();
    } else if (uploadMethod === 'document') {
      return renderDocumentUpload();
    } else if (uploadMethod === 'manual') {
      return renderManualEntry();
    }
  };

  const renderWebsiteScrape = () => (
    <div className="execution-panel">
      <button className="back-btn" onClick={() => setStep(1)}>← Back</button>
      
      <h2>🌐 Scrape Your Website</h2>
      <p className="subtitle">We'll automatically extract services, pricing, FAQs, and contact info</p>

      <div className="input-section">
        <label>Your Website URL</label>
        <input
          type="url"
          placeholder="https://yourwebsite.com"
          value={websiteUrl}
          onChange={(e) => setWebsiteUrl(e.target.value)}
          disabled={isProcessing}
          className="url-input"
        />
        
        <div className="suggestions">
          <strong>💡 Tips:</strong>
          <ul>
            <li>Use your homepage URL for best results</li>
            <li>Make sure your website is publicly accessible</li>
            <li>This will take 10-30 seconds</li>
          </ul>
        </div>

        <button 
          onClick={handleWebsiteScrape}
          disabled={isProcessing || !websiteUrl}
          className="primary-btn large"
        >
          {isProcessing ? '🔄 Scraping...' : '🕷️ Start Scraping'}
        </button>
      </div>

      {result && renderResult()}
    </div>
  );

  const renderDocumentUpload = () => (
    <div className="execution-panel">
      <button className="back-btn" onClick={() => setStep(1)}>← Back</button>
      
      <h2>📄 Upload Documents</h2>
      <p className="subtitle">Drag & drop or click to upload PDF, DOCX, or TXT files</p>

      <div
        className={`dropzone ${dragActive ? 'active' : ''} ${uploadedFile ? 'has-file' : ''}`}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,.docx,.txt,.json,.csv"
          onChange={handleFileSelect}
          style={{ display: 'none' }}
        />
        
        {!uploadedFile ? (
          <>
            <div className="dropzone-icon">📁</div>
            <p className="dropzone-text">Drag & drop your file here</p>
            <p className="dropzone-subtext">or click to browse</p>
            <p className="dropzone-formats">Supports: PDF, DOCX, TXT, JSON, CSV</p>
          </>
        ) : (
          <>
            <div className="file-preview">
              <div className="file-icon">📄</div>
              <div className="file-info">
                <div className="file-name">{uploadedFile.name}</div>
                <div className="file-size">{(uploadedFile.size / 1024).toFixed(1)} KB</div>
              </div>
              <button 
                className="remove-file-btn"
                onClick={(e) => {
                  e.stopPropagation();
                  setUploadedFile(null);
                }}
              >
                ✕
              </button>
            </div>
          </>
        )}
      </div>

      {uploadedFile && (
        <div className="suggestions">
          <strong>💡 What happens next:</strong>
          <ul>
            <li>We'll extract all text from your document</li>
            <li>Automatically categorize content (services, pricing, etc.)</li>
            <li>Break into searchable chunks</li>
            <li>Add to your knowledge base</li>
          </ul>
        </div>
      )}

      {uploadedFile && (
        <button 
          onClick={handleDocumentUpload}
          disabled={isProcessing}
          className="primary-btn large"
        >
          {isProcessing ? '🔄 Processing...' : '📤 Upload & Process'}
        </button>
      )}

      {result && renderResult()}
    </div>
  );

  const renderManualEntry = () => (
    <div className="execution-panel">
      <button className="back-btn" onClick={() => setStep(1)}>← Back</button>
      
      <h2>✍️ Add Knowledge Manually</h2>
      <p className="subtitle">Enter specific information about your business</p>

      <div className="form-section">
        <div className="form-group">
          <label>Category</label>
          <div className="category-pills">
            {['services', 'pricing', 'faqs', 'company', 'contact'].map(cat => (
              <button
                key={cat}
                className={`category-pill ${manualData.category === cat ? 'active' : ''}`}
                onClick={() => setManualData({...manualData, category: cat})}
              >
                {cat.charAt(0).toUpperCase() + cat.slice(1)}
              </button>
            ))}
          </div>
        </div>

        <div className="form-group">
          <label>Title / Question</label>
          <input
            type="text"
            placeholder={getCategoryPlaceholder(manualData.category, 'title')}
            value={manualData.title}
            onChange={(e) => setManualData({...manualData, title: e.target.value})}
          />
        </div>

        <div className="form-group">
          <label>Content / Answer</label>
          <textarea
            placeholder={getCategoryPlaceholder(manualData.category, 'content')}
            value={manualData.content}
            onChange={(e) => setManualData({...manualData, content: e.target.value})}
            rows="6"
          />
        </div>

        <div className="form-group">
          <label>Tags (optional)</label>
          <input
            type="text"
            placeholder="e.g., emergency, 24/7, urgent (comma-separated)"
            value={manualData.tags}
            onChange={(e) => setManualData({...manualData, tags: e.target.value})}
          />
        </div>

        <button 
          onClick={handleManualAdd}
          disabled={!manualData.title || !manualData.content}
          className="primary-btn large"
        >
          ➕ Add to Knowledge Base
        </button>
      </div>

      {result && renderResult()}
    </div>
  );

  // Step 3: View all knowledge
  const renderKnowledgeList = () => (
    <div className="knowledge-view">
      <button className="back-btn" onClick={() => setStep(1)}>← Back</button>
      
      <div className="knowledge-header">
        <h2>📚 Your Knowledge Base</h2>
        <div className="knowledge-stats">
          <span>{knowledge.length} items</span>
        </div>
      </div>

      {knowledge.length === 0 ? (
        <div className="empty-state">
          <div className="empty-icon">📭</div>
          <h3>No knowledge yet</h3>
          <p>Start by adding information about your business</p>
          <button className="primary-btn" onClick={() => setStep(1)}>
            Add Knowledge
          </button>
        </div>
      ) : (
        <div className="knowledge-grid">
          {knowledge.map((item) => (
            <div key={item.knowledge_id} className="knowledge-card">
              <div className="card-header">
                <span className={`category-badge ${item.category}`}>
                  {item.category}
                </span>
                <button 
                  className="delete-icon-btn"
                  onClick={() => handleDelete(item.knowledge_id)}
                  title="Delete"
                >
                  🗑️
                </button>
              </div>
              <h4>{item.title}</h4>
              <p>{item.content}</p>
              {item.tags && item.tags.length > 0 && (
                <div className="tags-row">
                  {item.tags.slice(0, 3).map((tag, idx) => (
                    <span key={idx} className="tag">{tag}</span>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );

  const renderResult = () => (
    <div className={`result-box ${result.success ? 'success' : 'error'}`}>
      {result.success ? (
        <>
          <div className="result-icon">✅</div>
          <h3>Success!</h3>
          <p>{result.message}</p>
          {result.details && (
            <div className="result-details">
              {Object.entries(result.details).map(([key, value]) => (
                <div key={key} className="detail-item">
                  <span className="detail-label">{key}:</span>
                  <span className="detail-value">{value}</span>
                </div>
              ))}
            </div>
          )}
          <button className="secondary-btn" onClick={() => setStep(3)}>
            View Knowledge Base
          </button>
        </>
      ) : (
        <>
          <div className="result-icon">❌</div>
          <h3>Error</h3>
          <p>{result.message}</p>
        </>
      )}
    </div>
  );

  // Handlers
  const handleWebsiteScrape = async () => {
    setIsProcessing(true);
    setResult(null);
    
    try {
      const response = await axios.post(
        `${apiUrl}/scrape/${clientId}?url=${encodeURIComponent(websiteUrl)}`
      );
      
      setResult({
        success: true,
        message: `Added ${response.data.items_added} knowledge items from your website!`,
        details: {
          'Services': response.data.summary.services,
          'FAQs': response.data.summary.faqs,
          'Pricing': response.data.summary.pricing
        }
      });
      
      loadKnowledge();
    } catch (error) {
      setResult({
        success: false,
        message: error.response?.data?.detail || 'Failed to scrape website'
      });
    } finally {
      setIsProcessing(false);
    }
  };

  const handleDocumentUpload = async () => {
    setIsProcessing(true);
    setResult(null);
    
    try {
      const formData = new FormData();
      formData.append('file', uploadedFile);
      
      const response = await axios.post(
        `${apiUrl}/upload/${clientId}`,
        formData,
        { headers: { 'Content-Type': 'multipart/form-data' } }
      );
      
      setResult({
        success: true,
        message: `Processed ${response.data.filename} successfully!`,
        details: {
          'Chunks added': response.data.chunks_added,
          'Categories': response.data.categories_detected.join(', ')
        }
      });
      
      setUploadedFile(null);
      loadKnowledge();
    } catch (error) {
      setResult({
        success: false,
        message: error.response?.data?.detail || 'Failed to process document'
      });
    } finally {
      setIsProcessing(false);
    }
  };

  const handleManualAdd = async () => {
    try {
      const tags = manualData.tags.split(',').map(t => t.trim()).filter(t => t);
      
      await axios.post(`${apiUrl}/knowledge/${clientId}`, {
        ...manualData,
        tags
      });
      
      setResult({
        success: true,
        message: 'Knowledge added successfully!'
      });
      
      setManualData({
        category: 'services',
        title: '',
        content: '',
        tags: ''
      });
      
      loadKnowledge();
    } catch (error) {
      setResult({
        success: false,
        message: 'Failed to add knowledge'
      });
    }
  };

  const handleDelete = async (knowledgeId) => {
    if (!confirm('Delete this knowledge item?')) return;
    
    try {
      await axios.delete(`${apiUrl}/knowledge/${clientId}/${knowledgeId}`);
      loadKnowledge();
    } catch (error) {
      console.error('Delete error:', error);
    }
  };

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setUploadedFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileSelect = (e) => {
    if (e.target.files && e.target.files[0]) {
      setUploadedFile(e.target.files[0]);
    }
  };

  // Step 4: Bot Settings
  const renderBotSettings = () => {
    if (!botSettings) return <div>Loading...</div>;

    return (
      <div className="bot-settings-view">
        <button className="back-btn" onClick={() => setStep(1)}>← Back</button>
        
        <h2>⚙️ Bot Settings & Personality</h2>
        <p className="subtitle">Customize how your AI assistant behaves and responds</p>

        <div className="settings-sections">
          {/* Personality Preset */}
          <div className="settings-section">
            <h3>🎭 Personality</h3>
            <p className="section-desc">Choose the overall personality of your bot</p>
            <div className="preset-grid">
              {[
                { id: 'professional', label: 'Professional', desc: 'Formal and precise' },
                { id: 'friendly', label: 'Friendly', desc: 'Warm and approachable' },
                { id: 'sales_focused', label: 'Sales-Focused', desc: 'Persuasive and urgent' },
                { id: 'technical', label: 'Technical', desc: 'Detailed and accurate' },
                { id: 'casual', label: 'Casual', desc: 'Laid-back and simple' }
              ].map(preset => (
                <button
                  key={preset.id}
                  className={`preset-card ${botSettings.personality === preset.id ? 'active' : ''}`}
                  onClick={() => updateSetting('personality', preset.id)}
                >
                  <div className="preset-label">{preset.label}</div>
                  <div className="preset-desc">{preset.desc}</div>
                </button>
              ))}
            </div>
          </div>

          {/* Response Length */}
          <div className="settings-section">
            <h3>📏 Response Length</h3>
            <p className="section-desc">Control how long responses should be</p>
            <div className="slider-container">
              <div className="slider-labels">
                <span className={botSettings.response_length === 'brief' ? 'active' : ''}>Brief</span>
                <span className={botSettings.response_length === 'medium' ? 'active' : ''}>Medium</span>
                <span className={botSettings.response_length === 'detailed' ? 'active' : ''}>Detailed</span>
              </div>
              <input
                type="range"
                min="1"
                max="3"
                value={botSettings.response_length === 'brief' ? 1 : botSettings.response_length === 'medium' ? 2 : 3}
                onChange={(e) => {
                  const val = parseInt(e.target.value);
                  updateSetting('response_length', val === 1 ? 'brief' : val === 2 ? 'medium' : 'detailed');
                }}
                className="length-slider"
              />
              <div className="slider-hint">
                {botSettings.response_length === 'brief' && '1-2 sentences'}
                {botSettings.response_length === 'medium' && '2-3 sentences'}
                {botSettings.response_length === 'detailed' && 'Comprehensive answers'}
              </div>
            </div>
          </div>

          {/* Tone */}
          <div className="settings-section">
            <h3>🎵 Tone</h3>
            <p className="section-desc">How formal or casual should responses be?</p>
            <div className="tone-pills">
              {['formal', 'professional', 'conversational', 'casual'].map(tone => (
                <button
                  key={tone}
                  className={`tone-pill ${botSettings.tone === tone ? 'active' : ''}`}
                  onClick={() => updateSetting('tone', tone)}
                >
                  {tone.charAt(0).toUpperCase() + tone.slice(1)}
                </button>
              ))}
            </div>
          </div>

          {/* Formality & Urgency Sliders */}
          <div className="settings-section">
            <h3>🎚️ Behavior Levels</h3>
            <div className="dual-sliders">
              <div className="slider-group">
                <label>Formality Level: {botSettings.formality_level}/10</label>
                <input
                  type="range"
                  min="1"
                  max="10"
                  value={botSettings.formality_level}
                  onChange={(e) => updateSetting('formality_level', parseInt(e.target.value))}
                  className="behavior-slider"
                />
                <div className="slider-hint">1 = Very casual, 10 = Very formal</div>
              </div>
              <div className="slider-group">
                <label>Urgency Level: {botSettings.urgency_level}/10</label>
                <input
                  type="range"
                  min="1"
                  max="10"
                  value={botSettings.urgency_level}
                  onChange={(e) => updateSetting('urgency_level', parseInt(e.target.value))}
                  className="behavior-slider"
                />
                <div className="slider-hint">1 = Relaxed, 10 = High urgency</div>
              </div>
            </div>
          </div>

          {/* Toggles */}
          <div className="settings-section">
            <h3>🔘 Features</h3>
            <div className="toggles-list">
              <div className="toggle-item">
                <div className="toggle-info">
                  <strong>Use Emojis</strong>
                  <span>Add emojis to responses for warmth</span>
                </div>
                <label className="toggle-switch">
                  <input
                    type="checkbox"
                    checked={botSettings.use_emojis}
                    onChange={(e) => updateSetting('use_emojis', e.target.checked)}
                  />
                  <span className="toggle-slider"></span>
                </label>
              </div>
              <div className="toggle-item">
                <div className="toggle-info">
                  <strong>Quick Reply Buttons</strong>
                  <span>Show clickable response options</span>
                </div>
                <label className="toggle-switch">
                  <input
                    type="checkbox"
                    checked={botSettings.enable_quick_replies}
                    onChange={(e) => updateSetting('enable_quick_replies', e.target.checked)}
                  />
                  <span className="toggle-slider"></span>
                </label>
              </div>
            </div>
          </div>

          {/* Voice Settings (Future) */}
          <div className="settings-section disabled">
            <h3>🎤 Voice Settings <span className="coming-soon">Coming Soon</span></h3>
            <p className="section-desc">Voice calling features will be available soon</p>
            <div className="voice-preview">
              <div className="voice-option disabled">
                <span>Voice Type: Professional Female</span>
              </div>
              <div className="voice-option disabled">
                <span>Speed: 1.0x</span>
              </div>
            </div>
          </div>

          {/* Custom Instructions */}
          <div className="settings-section">
            <h3>✍️ Custom Instructions</h3>
            <p className="section-desc">Add specific instructions for your bot</p>
            <textarea
              placeholder="e.g., Always mention our 10-year warranty. Never discuss competitor pricing. Emphasize same-day service availability."
              value={botSettings.custom_instructions || ''}
              onChange={(e) => updateSetting('custom_instructions', e.target.value)}
              rows="4"
              className="custom-instructions-input"
            />
          </div>

          {/* Greeting Message */}
          <div className="settings-section">
            <h3>👋 Greeting Message</h3>
            <p className="section-desc">First message customers see</p>
            <input
              type="text"
              placeholder="Hi! How can we help you today?"
              value={botSettings.greeting_message || ''}
              onChange={(e) => updateSetting('greeting_message', e.target.value)}
              className="greeting-input"
            />
          </div>
        </div>

        {settingsChanged && (
          <div className="save-bar">
            <span>You have unsaved changes</span>
            <button onClick={handleSaveSettings} className="save-btn">
              💾 Save Settings
            </button>
          </div>
        )}
      </div>
    );
  };

  const updateSetting = (key, value) => {
    setBotSettings(prev => ({ ...prev, [key]: value }));
    setSettingsChanged(true);
  };

  const handleSaveSettings = async () => {
    try {
      await axios.put(`${apiUrl}/settings/${clientId}`, botSettings);
      setSettingsChanged(false);
      setResult({
        success: true,
        message: 'Settings saved successfully! Changes will apply to new conversations.'
      });
      setTimeout(() => setResult(null), 3000);
    } catch (error) {
      setResult({
        success: false,
        message: 'Failed to save settings'
      });
    }
  };

  return (
    <div className="settings-overlay">
      <div className="settings-panel-new">
        <button className="close-btn-new" onClick={onClose}>✕</button>
        
        <div className="panel-content">
          {step === 1 && renderMethodSelection()}
          {step === 2 && renderMethodExecution()}
          {step === 3 && renderKnowledgeList()}
          {step === 4 && renderBotSettings()}
        </div>
      </div>
    </div>
  );
};

export default SettingsPanel;
