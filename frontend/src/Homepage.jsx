import { useState, useEffect } from "react";
import { Outlet, Link, useNavigate } from "react-router-dom";
import { useTranslation } from 'react-i18next';
import analytics from "./utils/analytics";
import storage from "./utils/storage";
import LoadingSpinner from "./components/LoadingSpinner";
import SkeletonLoader from "./components/SkeletonLoader";
import "./App.css";

const Homepage = () => {
  const navigate = useNavigate();
  const { t } = useTranslation();
  const [topic, changeTopic] = useState("");
  const [recentTopics, setRecentTopics] = useState([]);
  const [rememberPreferences, setRememberPreferences] = useState(false);

  const [imagePath, setImageUrl] = useState("");
  const [validationError, setValidationError] = useState("");
  const [showToast, setShowToast] = useState(false);
  const [toastMessage, setToastMessage] = useState("");
  const [toastType, setToastType] = useState("error");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [imageLoading, setImageLoading] = useState(false);
  const [imageUploadProgress, setImageUploadProgress] = useState(0);
  const [showTooltips, setShowTooltips] = useState(false);
  const [hasVisitedBefore, setHasVisitedBefore] = useState(false);
  const [fadeIn, setFadeIn] = useState(false);
  
  // Popular topics for autocomplete
  const popularTopics = [
    "Machine Learning",
    "Artificial Intelligence",
    "Quantum Physics",
    "Climate Change",
    "Blockchain Technology",
    "Neural Networks",
    "Data Science",
    "Cybersecurity",
    "Space Exploration",
    "Renewable Energy",
    "Genetics and DNA",
    "Psychology",
    "Ancient History",
    "Modern Art",
    "Programming Languages",
    "Economics",
    "Philosophy",
    "Astronomy",
    "Biology",
    "Chemistry"
  ];
  
  // Toast notification helper
  const showToastNotification = (message, type = "error") => {
    setToastMessage(message);
    setToastType(type);
    setShowToast(true);
    
    // Auto-hide after 5 seconds
    setTimeout(() => {
      setShowToast(false);
    }, 5000);
  };
  
  useEffect(() => {
    try {
      // Fade-in animation on mount
      setTimeout(() => setFadeIn(true), 100);
      
      // Track page load
      analytics.trackPageLoad('Homepage');
      
      // Check if first-time user
      const visitedBefore = localStorage.getItem('KNOWALLEDGE_visited');
      if (!visitedBefore) {
        setShowTooltips(true);
        localStorage.setItem('KNOWALLEDGE_visited', 'true');
        showToastNotification(t('notifications.welcome'), "success");
      } else {
        setHasVisitedBefore(true);
      }
      
      // Load recent topics from storage
      const topics = storage.getRecentTopics();
      setRecentTopics(topics);
      
      // Load saved preference setting
      const prefs = storage.loadPreferences();
      if (prefs) {
        setRememberPreferences(true);
      }
      
      // Keyboard navigation handler
      const handleKeyPress = (e) => {
        // Esc to clear form
        if (e.key === 'Escape') {
          changeTopic('');
          setImageUrl('');
          setValidationError('');
        }
        
        // Enter to submit (only if not in a textarea/select)
        if (e.key === 'Enter' && !['TEXTAREA', 'SELECT'].includes(e.target.tagName)) {
          if (topic.trim() || imagePath) {
            // Trigger navigation programmatically
            const generateButton = document.querySelector('.enterPromptButton');
            if (generateButton && !generateButton.disabled) {
              generateButton.click();
            }
          }
        }
      };
      
      window.addEventListener('keydown', handleKeyPress);
      
      // Track first interaction
      const handleFirstInteraction = () => {
        try {
          analytics.trackFirstInteraction();
        } catch (e) {
          console.warn('First interaction tracking failed:', e);
        }
        // Remove listeners after first interaction
        window.removeEventListener('click', handleFirstInteraction);
        window.removeEventListener('keydown', handleFirstInteraction);
      };
      
      window.addEventListener('click', handleFirstInteraction);
      window.addEventListener('keydown', handleFirstInteraction);
      
      return () => {
        window.removeEventListener('keydown', handleKeyPress);
        window.removeEventListener('click', handleFirstInteraction);
        window.removeEventListener('keydown', handleFirstInteraction);
      };
    } catch (error) {
      console.error('Analytics initialization error:', error);
    }
  }, [topic, imagePath]);

  const handleImageUpload = (e) => {
    const file = e.target.files[0];
    if (file) {
      // Validate file type
      const validTypes = ['image/png', 'image/jpeg', 'image/jpg', 'image/gif', 'image/webp'];
      if (!validTypes.includes(file.type)) {
        const errorMsg = t('homepage.imageUpload.error.invalidType');
        setValidationError(errorMsg);
        showToastNotification(errorMsg, "error");
        return;
      }
      
      // Validate file size (max 10MB)
      if (file.size > 10 * 1024 * 1024) {
        const errorMsg = t('homepage.imageUpload.error.tooLarge', { max: 10 });
        setValidationError(errorMsg);
        showToastNotification(errorMsg, "error");
        return;
      }
      
      setValidationError("");
      setImageLoading(true);
      setImageUploadProgress(0);
      
      // Simulate progressive upload with progress bar
      const progressInterval = setInterval(() => {
        setImageUploadProgress(prev => {
          if (prev >= 90) {
            clearInterval(progressInterval);
            return prev;
          }
          return prev + 10;
        });
      }, 50);
      
      // Simulate image processing
      setTimeout(() => {
        clearInterval(progressInterval);
        setImageUploadProgress(100);
        
        setTimeout(() => {
          const imageUrl = URL.createObjectURL(file);
          setImageUrl(imageUrl);
          setImageLoading(false);
          setImageUploadProgress(0);
          showToastNotification(t('notifications.success', { message: t('homepage.imageUpload.processing') + ' 🎉' }), "success");
        }, 300);
      }, 500);
    }
  };
  
  const validateTopic = (topicValue) => {
    // Clear previous errors
    setValidationError("");
    
    // Check if empty
    if (!topicValue.trim()) {
      return false;
    }
    
    // Check minimum length (at least 3 characters)
    if (topicValue.trim().length < 3) {
      const errorMsg = t('homepage.topicInput.tooShort');
      setValidationError(errorMsg);
      showToastNotification(errorMsg, "error");
      return false;
    }
    
    // Check length (3-200 characters)
    if (topicValue.length > 200) {
      const errorMsg = t('homepage.topicInput.tooLong');
      setValidationError(errorMsg);
      showToastNotification(errorMsg, "error");
      return false;
    }
    
    // Check for valid characters (alphanumeric, spaces, and basic punctuation)
    const validPattern = /^[a-zA-Z0-9\s\-.,()!?&]+$/;
    if (!validPattern.test(topicValue)) {
      const errorMsg = "Topic contains invalid characters. Please use only letters, numbers, and basic punctuation.";
      setValidationError(errorMsg);
      showToastNotification(errorMsg, "error");
      return false;
    }
    
    return true;
  };
  
  const handleTopicChange = (event) => {
    const newTopic = event.target.value;
    changeTopic(newTopic);
    
    // Validate as user types (but don't show error until they try to submit)
    if (newTopic.length > 200) {
      setValidationError("Topic must be less than 200 characters");
    } else {
      setValidationError("");
    }
  };
  
  const handleGenerateClick = (e) => {
    if (!validateTopic(topic) && !imagePath) {
      e.preventDefault();
      if (!validationError) {
        const errorMsg = "Please enter a topic (min 3 characters) or upload an image";
        setValidationError(errorMsg);
        showToastNotification(errorMsg, "error");
      }
      return;
    } else if (topic.trim() && !validateTopic(topic)) {
      e.preventDefault();
      return;
    }
    
    // Show loading state
    setIsSubmitting(true);
    
    if (topic.trim()) {
      // Save topic to recent topics
      storage.addRecentTopic(topic.trim());
      
      // Save preferences if checkbox is enabled
      if (rememberPreferences) {
        storage.savePreferences({
          rememberMe: true,
          lastTopic: topic.trim()
        });
      }
      
      showToastNotification("Generating subtopics...", "success");
    }
    
    // Navigate after a brief delay to show feedback
    setTimeout(() => {
      navigate('/SubtopicPage', { state: { topic: topic, imageUrl: imagePath } });
    }, 300);
  };
  
  const handlePreferenceToggle = (checked) => {
    setRememberPreferences(checked);
    if (!checked) {
      // Clear saved preferences when unchecked
      storage.clearAll();
    }
  };

  return (
    <>
      {/* ✅ ACCESSIBILITY: Main content section (WCAG 1.3.1 Level A) */}
      <section 
        className="top-section" 
        aria-labelledby="main-heading"
        style={{
          opacity: fadeIn ? 1 : 0,
          transform: fadeIn ? 'translateY(0)' : 'translateY(20px)',
          transition: 'opacity 0.6s ease-out, transform 0.6s ease-out'
        }}
      >
        {/* Toast Notification */}
        {showToast && (
          <div 
            role="alert"
            aria-live="polite"
            style={{
              position: 'fixed',
              top: '20px',
              right: '20px',
              zIndex: 10000,
              background: toastType === 'error' ? '#fee' : toastType === 'success' ? '#d4edda' : '#fff3cd',
              border: `2px solid ${toastType === 'error' ? '#fcc' : toastType === 'success' ? '#c3e6cb' : '#ffc107'}`,
              borderRadius: '8px',
              padding: '15px 20px',
              boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
              maxWidth: '400px',
              animation: 'slideIn 0.3s ease-out'
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <span style={{ fontSize: '20px' }}>
                  {toastType === 'error' ? '❌' : toastType === 'success' ? '✅' : '⚠️'}
                </span>
                <span style={{ 
                  color: toastType === 'error' ? '#c33' : toastType === 'success' ? '#155724' : '#856404',
                  fontSize: '14px'
                }}>
                  {toastMessage}
                </span>
              </div>
              <button
                onClick={() => setShowToast(false)}
                style={{
                  background: 'none',
                  border: 'none',
                  fontSize: '20px',
                  cursor: 'pointer',
                  color: '#999',
                  marginLeft: '10px'
                }}
                aria-label="Close notification"
              >
                ×
              </button>
            </div>
          </div>
        )}
        
        <h1 className="big-heading" id="main-heading">
          <span className="gradient-text">{t('homepage.welcome')} </span>
          <span className="gradient-text2">{t('common.appName')}.</span>
        </h1>
        <h1 className="typewriter" aria-live="polite">
          <p className="typed">
            <span className="gradient-text-container">
              <br />
              <span className="gradient-text">
                {t('homepage.tagline')}
              </span>
            </span>
          </p>
        </h1>

        <h2 id="topic-question">{t('homepage.question')}</h2>
        
        {/* Tooltip toggle button */}
        <div style={{ textAlign: 'center', marginBottom: '15px' }}>
          <button
            onClick={() => {
              setShowTooltips(!showTooltips);
              showToastNotification(
                showTooltips ? t('homepage.tooltipsHidden') : t('homepage.tooltipsEnabled'), 
                "success"
              );
            }}
            style={{
              padding: '8px 16px',
              background: showTooltips ? '#667eea' : '#f0f0f0',
              color: showTooltips ? 'white' : '#333',
              border: showTooltips ? 'none' : '1px solid #ddd',
              borderRadius: '20px',
              fontSize: '13px',
              cursor: 'pointer',
              transition: 'all 0.3s',
              fontWeight: '500'
            }}
            aria-label={showTooltips ? t('homepage.hideTooltips') : t('homepage.showTooltips')}
            title={t('homepage.toggleTooltips')}
          >
            {showTooltips ? t('homepage.tooltipsOn') : t('homepage.showHints')}
          </button>
        </div>

        {validationError && (
          <div style={{
            background: '#fff3cd',
            border: '2px solid #ffc107',
            borderRadius: '8px',
            padding: '15px',
            margin: '20px auto',
            maxWidth: '600px',
            color: '#856404',
            textAlign: 'center'
          }}>
            ⚠️ {validationError}
          </div>
        )}

        <div className="input-area">
          {recentTopics.length > 0 && (
            <div style={{ marginBottom: '15px', textAlign: 'center' }}>
              <label htmlFor="recentTopics" style={{ 
                display: 'block', 
                marginBottom: '8px',
                fontSize: '14px',
                fontWeight: 'bold',
                color: '#667eea'
              }}>
                {t('homepage.recentTopics.title')}
              </label>
              <select
                id="recentTopics"
                onChange={(e) => {
                  if (e.target.value) {
                    changeTopic(e.target.value);
                    showToastNotification(t('homepage.recentTopics.loaded', { topic: e.target.value }), "success");
                  }
                }}
                defaultValue=""
                style={{
                  padding: '10px',
                  borderRadius: '8px',
                  border: '2px solid #ddd',
                  background: 'white',
                  fontSize: '14px',
                  cursor: 'pointer',
                  minWidth: '200px',
                  transition: 'all 0.2s ease-in-out'
                }}
                aria-label="Select from previously entered topics"
                aria-describedby="recent-topics-description"
                tabIndex={0}
              >
                <option value="">{t('homepage.recentTopics.placeholder')}</option>
                {recentTopics.map((recentTopic, index) => (
                  <option key={index} value={recentTopic}>
                    {recentTopic}
                  </option>
                ))}
              </select>
              <div id="recent-topics-description" style={{ 
                fontSize: '11px', 
                color: '#999', 
                marginTop: '5px' 
              }}>
                {t('homepage.recentTopics.description', { count: recentTopics.length })} {t('homepage.recentTopics.saved')}
              </div>
            </div>
          )}

          <div className="input-container">
            <label htmlFor="topicInput" style={{
              display: 'block',
              marginBottom: '8px',
              fontSize: '14px',
              fontWeight: 'bold',
              color: '#333'
            }}>
              {t('homepage.topicInput.label')}
            </label>
            <div style={{ position: 'relative' }}>
              <input
                id="topicInput"
                name="topic"
                list="popular-topics"
                placeholder={t('homepage.topicInput.placeholder')}
                type="text"
                value={topic}
                onChange={handleTopicChange}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && topic.trim() && !isSubmitting) {
                    handleGenerateClick(e);
                  }
                }}
                maxLength={200}
                minLength={3}
                aria-label={t('homepage.topicInput.ariaLabel')}
                aria-invalid={validationError ? "true" : "false"}
                aria-describedby="topic-help-text topic-char-count"
                aria-required="true"
                tabIndex={1}
                autoFocus
                disabled={isSubmitting}
                title={showTooltips ? t('homepage.topicInput.helpText') : ""}
                style={{
                  position: 'relative'
                }}
              />
              {showTooltips && (
                <div style={{
                  position: 'absolute',
                  top: '-35px',
                  left: '0',
                  background: '#667eea',
                  color: 'white',
                  padding: '8px 12px',
                  borderRadius: '8px',
                  fontSize: '12px',
                  whiteSpace: 'nowrap',
                  boxShadow: '0 4px 8px rgba(0,0,0,0.2)',
                  zIndex: 100,
                  animation: 'tooltipBounce 0.5s ease-out'
                }}>
                  💡 Start typing to see popular topic suggestions!
                  <div style={{
                    position: 'absolute',
                    bottom: '-6px',
                    left: '20px',
                    width: 0,
                    height: 0,
                    borderLeft: '6px solid transparent',
                    borderRight: '6px solid transparent',
                    borderTop: '6px solid #667eea'
                  }} />
                </div>
              )}
            </div>
            
            {/* Autocomplete datalist */}
            <datalist id="popular-topics">
              {popularTopics.map((popularTopic, index) => (
                <option key={index} value={popularTopic} />
              ))}
            </datalist>
            
            <div id="topic-help-text" style={{ 
              fontSize: '11px', 
              color: '#666', 
              marginTop: '5px',
              marginBottom: '5px'
            }}>
              Enter a topic you want to learn about (minimum 3 characters) • {popularTopics.length} popular topics available
            </div>
            <div id="topic-char-count" style={{ fontSize: '12px', color: '#999', marginTop: '5px' }}>
              {t('homepage.topicInput.charCount', { current: topic.length, max: 200 })}
              <span style={{ marginLeft: '10px', color: '#666' }}>
                💡 Press <kbd style={{ 
                  padding: '2px 6px', 
                  border: '1px solid #ccc', 
                  borderRadius: '3px',
                  background: '#f5f5f5',
                  fontSize: '11px'
                }}>Enter</kbd> to submit, <kbd style={{ 
                  padding: '2px 6px', 
                  border: '1px solid #ccc', 
                  borderRadius: '3px',
                  background: '#f5f5f5',
                  fontSize: '11px'
                }}>Esc</kbd> to clear
              </span>
            </div>

            <div style={{ 
              marginTop: '15px', 
              display: 'flex', 
              alignItems: 'center', 
              justifyContent: 'center',
              gap: '8px'
            }}>
              <input
                type="checkbox"
                id="rememberPreferences"
                checked={rememberPreferences}
                onChange={(e) => handlePreferenceToggle(e.target.checked)}
                style={{ cursor: 'pointer', width: '18px', height: '18px' }}
                tabIndex={2}
                aria-label={t('homepage.preferences.ariaLabel')}
                aria-describedby="preference-description"
              />
              <label 
                htmlFor="rememberPreferences" 
                id="preference-description"
                style={{ 
                  cursor: 'pointer', 
                  fontSize: '14px',
                  color: '#666',
                  userSelect: 'none'
                }}
              >
                {t('homepage.preferences.remember')}
              </label>
            </div>

            <button 
              className="enterPromptButton"
              onClick={handleGenerateClick}
              disabled={(!topic.trim() && !imagePath) || isSubmitting}
              style={{
                opacity: ((!topic.trim() && !imagePath) || isSubmitting) ? 0.5 : 1,
                cursor: ((!topic.trim() && !imagePath) || isSubmitting) ? 'not-allowed' : 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '10px',
                marginTop: '20px'
              }}
              aria-label={isSubmitting ? t('homepage.generate.ariaBusy') : t('homepage.generate.ariaLabel')}
              aria-busy={isSubmitting}
              tabIndex={3}
            >
              {isSubmitting ? (
                <>
                  <LoadingSpinner size="small" />
                  <span>{t('homepage.generate.generating')}</span>
                </>
              ) : (
                <>{t('homepage.generate.button')}</>
              )}
            </button>
          </div>

          <div>
            <h2 aria-label="Alternative option">{t('common.or')}</h2>
          </div>

          <div>
            <h3 id="image-upload-label">{t('homepage.imageUpload.title')}</h3>
            <input 
              id="imageUploadInput"
              name="imageUpload"
              type="file" 
              accept="image/png,image/jpeg,image/jpg,image/gif,image/webp" 
              onChange={handleImageUpload}
              aria-label={t('homepage.imageUpload.label')}
              aria-labelledby="image-upload-label"
              aria-describedby="image-upload-description"
              disabled={isSubmitting}
              tabIndex={4}
            />
            <div id="image-upload-description" style={{ fontSize: '12px', color: '#999', marginTop: '5px' }}>
              {t('homepage.imageUpload.description')}
            </div>
            {imageLoading ? (
              <div style={{ marginTop: '15px', textAlign: 'center' }}>
                <SkeletonLoader variant="image" />
                <div style={{ marginTop: '15px', maxWidth: '300px', margin: '15px auto 0' }}>
                  {/* Progress bar */}
                  <div style={{
                    width: '100%',
                    height: '8px',
                    background: '#e0e0e0',
                    borderRadius: '10px',
                    overflow: 'hidden',
                    marginBottom: '10px'
                  }}>
                    <div style={{
                      width: `${imageUploadProgress}%`,
                      height: '100%',
                      background: 'linear-gradient(90deg, #667eea 0%, #764ba2 100%)',
                      borderRadius: '10px',
                      transition: 'width 0.3s ease-out',
                      boxShadow: imageUploadProgress > 0 ? '0 0 10px rgba(102, 126, 234, 0.5)' : 'none'
                    }} />
                  </div>
                  <div style={{ fontSize: '13px', color: '#667eea', fontWeight: 'bold' }}>
                    {t('homepage.imageUpload.progress', { percent: imageUploadProgress })}
                  </div>
                </div>
                <div style={{ marginTop: '10px', fontSize: '14px', color: '#667eea' }}>
                  <LoadingSpinner size="small" />
                </div>
              </div>
            ) : imagePath && (
              <div style={{ position: 'relative', display: 'inline-block', marginTop: '10px' }}>
                <img src={imagePath} className="inputImage" alt="Uploaded content for topic extraction" />
                <button
                  onClick={() => {
                    setImageUrl("");
                    setValidationError("");
                  }}
                  style={{
                    position: 'absolute',
                    top: '5px',
                    right: '5px',
                    background: '#ef4444',
                    color: 'white',
                    border: 'none',
                    borderRadius: '50%',
                    width: '30px',
                    height: '30px',
                    cursor: 'pointer',
                    fontSize: '18px'
                  }}
                  aria-label={t('homepage.imageUpload.remove')}
                  tabIndex={5}
                >
                  ×
                </button>
              </div>
            )}
          </div>
        </div>
        
        {/* Admin Metrics Link */}
        <div style={{ position: 'fixed', bottom: '20px', right: '20px', zIndex: 1000 }}>
          <Link to="/metrics">
            <button style={{
              padding: '10px 20px',
              background: '#667eea',
              color: 'white',
              border: 'none',
              borderRadius: '5px',
              cursor: 'pointer',
              fontSize: '14px',
              boxShadow: '0 4px 6px rgba(0,0,0,0.1)'
            }}>
              📊 Metrics Dashboard
            </button>
          </Link>
        </div>
      </section>

      {/* ✅ ACCESSIBILITY: Informational section about the platform (WCAG 1.3.1 Level A) */}
      <aside className="shadow-effect" aria-label="About KNOWALLEDGE">
        <img 
          src="logo.png" 
          className="logo" 
          alt="KNOWALLEDGE - Interactive Learning Platform Logo" 
          align="right" 
        />
        <h2>{t('homepage.about.whatIs')}</h2>
        <p>
          {t('homepage.about.description')}
          <br></br>
          <br></br>
          {t('homepage.about.cta')}
        </p>
        <h2>{t('homepage.about.why')}</h2>
        <div className="cap-width">
        <p>
          {t('homepage.about.reason')}
        </p>
        </div>
      </aside>
      
      {/* Toast animation and responsive styles */}
      <style>{`
        @keyframes slideIn {
          from {
            transform: translateX(100%);
            opacity: 0;
          }
          to {
            transform: translateX(0);
            opacity: 1;
          }
        }
        
        @keyframes tooltipBounce {
          0% {
            opacity: 0;
            transform: translateY(10px) translateX(-50%);
          }
          60% {
            opacity: 1;
            transform: translateY(-5px) translateX(-50%);
          }
          80% {
            transform: translateY(2px) translateX(-50%);
          }
          100% {
            transform: translateY(0) translateX(-50%);
          }
        }
        
        /* Responsive breakpoints */
        @media (max-width: 768px) {
          .top-section {
            padding: 20px 15px !important;
          }
          
          .big-heading {
            font-size: 2rem !important;
          }
          
          .typewriter {
            font-size: 1rem !important;
          }
          
          .input-container {
            max-width: 100% !important;
            padding: 15px !important;
          }
          
          .input-container input {
            font-size: 14px !important;
          }
          
          .enterPromptButton {
            font-size: 14px !important;
            padding: 12px 20px !important;
          }
          
          .inputImage {
            max-width: 100% !important;
            height: auto !important;
          }
          
          .shadow-effect {
            padding: 20px 15px !important;
          }
          
          .logo {
            width: 60px !important;
            height: auto !important;
          }
        }
        
        @media (min-width: 769px) and (max-width: 1024px) {
          .top-section {
            padding: 30px 25px !important;
          }
          
          .big-heading {
            font-size: 2.5rem !important;
          }
          
          .input-container {
            max-width: 600px !important;
          }
          
          .logo {
            width: 80px !important;
          }
        }
        
        @media (min-width: 1025px) {
          .top-section {
            padding: 40px 30px !important;
          }
          
          .input-container {
            max-width: 700px !important;
          }
        }
        
        /* Button loading state */
        .enterPromptButton {
          transition: all 0.3s ease !important;
        }
        
        .enterPromptButton:not(:disabled):hover {
          transform: translateY(-2px);
          box-shadow: 0 6px 20px rgba(102, 126, 234, 0.5);
        }
        
        .enterPromptButton:disabled {
          cursor: not-allowed !important;
        }
      `}</style>
    </>
  );
};

export default Homepage;
