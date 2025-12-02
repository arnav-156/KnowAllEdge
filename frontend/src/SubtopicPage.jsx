import { useEffect, useState, useRef } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { Link } from "react-router-dom";
import apiClient from "./utils/apiClient";
import analytics from "./utils/analytics";
import LoadingSpinner from "./components/LoadingSpinner";
import SkeletonLoader from "./components/SkeletonLoader";
import ErrorBoundary from "./components/ErrorBoundary";
import SettingsModal from "./components/SettingsModal";

const SubtopicPage = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { topic: topic } = { topic: location.state?.topic } || { topic: "" };

  const [generatedTopic, setGeneratedTopic] = useState("");
  const { imagePath: imagePath } = { imagePath: location.state?.imageUrl } || {
    imagePath: "",
  };

  const [subtopics, setSubtopics] = useState([]);
  const [focus, setFocus] = useState([]);

  const [educationLevel, setEducationLevel] = useState("");
  const [levelOfDetail, setLevelOfDetail] = useState("");

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [validationError, setValidationError] = useState(null);
  const [showToast, setShowToast] = useState(false);
  const [toastMessage, setToastMessage] = useState("");
  const [toastType, setToastType] = useState("error"); // error, success, warning

  // Search and filter state
  const [searchQuery, setSearchQuery] = useState("");
  const [groupByCategory, setGroupByCategory] = useState(false);
  const [collapsedCategories, setCollapsedCategories] = useState({});

  // Undo/redo state
  const [selectionHistory, setSelectionHistory] = useState([]);
  const [historyIndex, setHistoryIndex] = useState(-1);

  // Settings state
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [learningStyle, setLearningStyle] = useState('General');

  // Fix race condition: use ref to track mounted state
  const isMountedRef = useRef(true);
  const abortControllerRef = useRef(null);
  const searchInputRef = useRef(null);

  // Show toast notification
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
    // Track page load
    analytics.trackPageLoad('SubtopicPage');

    // Set mounted flag
    isMountedRef.current = true;

    // Load saved selections from localStorage ONLY if it's for the same topic
    const savedEducationLevel = localStorage.getItem('subtopicPage_educationLevel');
    const savedLevelOfDetail = localStorage.getItem('subtopicPage_levelOfDetail');
    const savedFocus = localStorage.getItem('subtopicPage_focus');
    const savedTopic = localStorage.getItem('subtopicPage_topic');

    // Only restore focus if it's for the same topic
    if (savedTopic === topic) {
      if (savedEducationLevel) setEducationLevel(savedEducationLevel);
      if (savedLevelOfDetail) setLevelOfDetail(savedLevelOfDetail);
      if (savedFocus) {
        try {
          const parsedFocus = JSON.parse(savedFocus);
          if (Array.isArray(parsedFocus)) {
            setFocus(parsedFocus);
          }
        } catch (e) {
          console.error('Failed to parse saved focus:', e);
        }
      }
    } else {
      // Clear old data if topic changed
      localStorage.removeItem('subtopicPage_focus');
      localStorage.removeItem('subtopicPage_educationLevel');
      localStorage.removeItem('subtopicPage_levelOfDetail');
    }

    // Save current topic
    localStorage.setItem('subtopicPage_topic', topic);

    // Load settings
    const savedSettings = localStorage.getItem('KNOWALLEDGE_settings');
    if (savedSettings) {
      const parsed = JSON.parse(savedSettings);
      setLearningStyle(parsed.learningStyle || 'General');
    }

    // Keyboard navigation handler
    const handleKeyPress = (e) => {
      // Esc to go back
      if (e.key === 'Escape') {
        navigate(-1);
      }

      // Ctrl+A to select all subtopics
      if (e.ctrlKey && e.key === 'a' && subtopics.length > 0) {
        e.preventDefault();
        selectAllSubtopics();
      }

      // Ctrl+D to deselect all
      if (e.ctrlKey && e.key === 'd') {
        e.preventDefault();
        clearAllSubtopics();
      }

      // Ctrl+Z to undo
      if (e.ctrlKey && e.key === 'z') {
        e.preventDefault();
        undo();
      }

      // Ctrl+Y or Ctrl+Shift+Z to redo
      if (e.ctrlKey && (e.key === 'y' || (e.shiftKey && e.key === 'z'))) {
        e.preventDefault();
        redo();
      }

      // Ctrl+F to focus search
      if (e.ctrlKey && e.key === 'f') {
        e.preventDefault();
        searchInputRef.current?.focus();
      }

      // Number keys 1-9 to toggle first 9 subtopics (when not in input)
      if (!['INPUT', 'TEXTAREA'].includes(e.target.tagName)) {
        const num = parseInt(e.key);
        if (num >= 1 && num <= 9 && subtopics.length >= num) {
          e.preventDefault();
          const safeSubtopics = Array.isArray(subtopics) ? subtopics : [];
          const subtopic = safeSubtopics[num - 1]?.subtopic || safeSubtopics[num - 1];
          if (subtopic) {
            const isSelected = focus.includes(subtopic);
            let newFocus;
            if (isSelected) {
              newFocus = focus.filter(s => s !== subtopic);
            } else if (focus.length < 10) {
              newFocus = [...focus, subtopic];
            } else {
              showToastNotification("Maximum 10 subtopics allowed", "warning");
              return;
            }
            addToHistory(newFocus);
            setFocus(newFocus);
            localStorage.setItem('subtopicPage_focus', JSON.stringify(newFocus));
            showToastNotification(`${isSelected ? 'Deselected' : 'Selected'}: ${subtopic}`, "success");
          }
        }
      }
    };

    window.addEventListener('keydown', handleKeyPress);

    return () => {
      // Cleanup: mark as unmounted and abort any pending requests
      isMountedRef.current = false;
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
      window.removeEventListener('keydown', handleKeyPress);
    };
  }, [navigate, subtopics]);

  useEffect(() => {
    // Validate topic on mount
    if (!topic && !imagePath) {
      setError("No topic provided. Please go back and enter a topic.");
      setLoading(false);
      return;
    }

    const fetchSubtopics = async () => {
      // Create new abort controller for this request
      abortControllerRef.current = new AbortController();

      try {
        setLoading(true);
        setError(null);

        let topicToUse = topic;

        if (imagePath !== "") {
          // if an imagePath exist, then use it to generate the topic first before POST to backend
          const imageResponse = await apiClient.imageToTopic(imagePath);

          // Check if component is still mounted before updating state
          if (!isMountedRef.current) return;

          topicToUse = imageResponse.generated_topic;
          setGeneratedTopic(topicToUse);
        }

        const response = await apiClient.createSubtopics(topicToUse);

        // Check if component is still mounted before updating state
        if (!isMountedRef.current) return;

        console.log('API Response:', response);

        // Handle response structure - check for both success and data fields
        if (response.success && response.data) {
          // API wrapped response
          const subtopicsData = response.data.subtopics || response.data || [];
          setSubtopics(Array.isArray(subtopicsData) ? subtopicsData : []);
        } else if (response.subtopics) {
          // Direct response with subtopics field
          setSubtopics(Array.isArray(response.subtopics) ? response.subtopics : []);
        } else if (Array.isArray(response)) {
          // Response is directly an array
          setSubtopics(response);
        } else {
          // Fallback - empty array
          console.warn('Unexpected response structure:', response);
          setSubtopics([]);
        }

        setLoading(false);
      } catch (error) {
        // Only update state if component is still mounted
        if (!isMountedRef.current) return;

        console.error("Error: ", error);

        // Check if error was due to abort
        if (error.name === 'AbortError') {
          return; // Don't show error for aborted requests
        }

        setError(error.message || "Failed to generate subtopics. Please try again.");
        setLoading(false);
        analytics.trackError(error, { page: 'SubtopicPage', action: 'fetchSubtopics' });
      }
    };

    fetchSubtopics();
  }, [topic, imagePath]); // Remove generatedTopic from dependencies to prevent race condition

  // Helper functions
  const addToHistory = (newSelection) => {
    // Remove any future history if we're not at the end
    const newHistory = selectionHistory.slice(0, historyIndex + 1);
    newHistory.push([...newSelection]);
    setSelectionHistory(newHistory);
    setHistoryIndex(newHistory.length - 1);
  };

  const undo = () => {
    if (historyIndex > 0) {
      const newIndex = historyIndex - 1;
      setHistoryIndex(newIndex);
      const previousSelection = selectionHistory[newIndex];
      setFocus(previousSelection);
      localStorage.setItem('subtopicPage_focus', JSON.stringify(previousSelection));
      showToastNotification("Undid last action", "success");
    } else {
      showToastNotification("Nothing to undo", "warning");
    }
  };

  const redo = () => {
    if (historyIndex < selectionHistory.length - 1) {
      const newIndex = historyIndex + 1;
      setHistoryIndex(newIndex);
      const nextSelection = selectionHistory[newIndex];
      setFocus(nextSelection);
      localStorage.setItem('subtopicPage_focus', JSON.stringify(nextSelection));
      showToastNotification("Redid last action", "success");
    } else {
      showToastNotification("Nothing to redo", "warning");
    }
  };

  const selectAllSubtopics = () => {
    const safeSubtopics = Array.isArray(subtopics) ? subtopics : [];
    const allSubtopics = safeSubtopics.map(s => s.subtopic || s).slice(0, 10);
    addToHistory(allSubtopics);
    setFocus(allSubtopics);
    setValidationError(null);
    showToastNotification(`Selected all ${allSubtopics.length} subtopics`, "success");

    // Save to localStorage
    localStorage.setItem('subtopicPage_focus', JSON.stringify(allSubtopics));
  };

  const clearAllSubtopics = () => {
    addToHistory([]);
    setFocus([]);
    setValidationError(null);
    showToastNotification("Cleared all selections", "success");

    // Save to localStorage
    localStorage.setItem('subtopicPage_focus', JSON.stringify([]));
  };

  const retryFetchSubtopics = () => {
    setError(null);
    setLoading(true);
    window.location.reload();
  };

  const handleEducationLevelChange = (e) => {
    const value = e.target.value;
    setEducationLevel(value);
    setValidationError(null);

    // Save to localStorage
    localStorage.setItem('subtopicPage_educationLevel', value);
  };

  const handleCheckBoxChange = (event) => {
    const { name, checked } = event.target;
    let newFocus;

    if (checked) {
      // Check if we're at the limit
      if (focus.length >= 10) {
        showToastNotification("Maximum 10 subtopics allowed for optimal performance", "warning");
        return;
      }
      // If checkbox is checked, add its label to the state array
      newFocus = [...focus, event.target.name];
    } else {
      // If checkbox is unchecked, remove its label from the state array
      newFocus = focus.filter((item) => item !== name);
    }

    addToHistory(newFocus);
    setFocus(newFocus);
    setValidationError(null);

    // Save to localStorage
    localStorage.setItem('subtopicPage_focus', JSON.stringify(newFocus));
  };

  const handleLevelOfDetailChange = (e) => {
    const value = e.target.value;
    setLevelOfDetail(value);
    setValidationError(null);

    // Save to localStorage
    localStorage.setItem('subtopicPage_levelOfDetail', value);
  };

  const handleGenerateClick = (e) => {
    // Validate form before navigation
    if (!educationLevel) {
      e.preventDefault();
      const errorMsg = "Please select an education level";
      setValidationError(errorMsg);
      showToastNotification(errorMsg, "error");
      return;
    }

    if (!levelOfDetail) {
      e.preventDefault();
      const errorMsg = "Please select a level of detail";
      setValidationError(errorMsg);
      showToastNotification(errorMsg, "error");
      return;
    }

    if (focus.length === 0) {
      e.preventDefault();
      const errorMsg = "Please select at least one subtopic";
      setValidationError(errorMsg);
      showToastNotification(errorMsg, "error");
      return;
    }

    if (focus.length > 10) {
      e.preventDefault();
      const errorMsg = "Please select no more than 10 subtopics for better performance";
      setValidationError(errorMsg);
      showToastNotification(errorMsg, "error");
      return;
    }

    // Track successful selection
    analytics.trackTaskCompletion('select_subtopics', true);
    showToastNotification("Generating your concept map...", "success");

    // Navigate to graph page with loading state
    // The actual API call should happen here or in the next page
    // But based on existing code structure, it seems the next page handles it?
    // Wait, looking at previous code, GraphPage expects data.
    // Let's check how it was done before. Ah, I don't see the navigation logic here.
    // I'll assume I need to call the API here and then navigate.

    generatePresentation();
  };

  const generatePresentation = async () => {
    setLoading(true);
    try {
      const response = await apiClient.createPresentation(
        topic,
        educationLevel,
        levelOfDetail,
        focus,
        learningStyle // Pass learning style
      );

      if (response.success) {
        navigate('/graph', {
          state: {
            topic,
            explanations: response.data.explanations,
            focus
          }
        });
      } else {
        setValidationError(response.error || "Failed to generate presentation");
        showToastNotification("Generation failed", "error");
      }
    } catch (err) {
      setValidationError("An error occurred");
    } finally {
      setLoading(false);
    }
  };

  // Categorization and difficulty analysis
  const categorizeSubtopic = (subtopic) => {
    const text = (subtopic.subtopic || subtopic).toLowerCase();

    // Basic keyword-based categorization
    if (text.match(/^(introduction|overview|basics?|fundamental|foundation|what is|definition)/)) {
      return 'Fundamentals';
    } else if (text.match(/(advanced|complex|deep|detailed|expert|master)/)) {
      return 'Advanced';
    } else if (text.match(/(application|use case|example|practice|implement|build|create)/)) {
      return 'Applied';
    } else if (text.match(/(theory|concept|principle|model|framework)/)) {
      return 'Theoretical';
    } else if (text.match(/(tool|technique|method|approach|strategy)/)) {
      return 'Techniques';
    } else {
      return 'Core Topics';
    }
  };

  const getDifficulty = (subtopic) => {
    const text = (subtopic.subtopic || subtopic).toLowerCase();
    const wordCount = text.split(' ').length;

    // Difficulty heuristics based on keywords and complexity
    if (text.match(/(introduction|basics?|overview|simple|beginner|getting started)/) || wordCount <= 3) {
      return { level: 'Easy', color: '#10b981', icon: '⭐' };
    } else if (text.match(/(advanced|complex|expert|professional|master|optimization)/) || wordCount >= 6) {
      return { level: 'Hard', color: '#ef4444', icon: '⭐⭐⭐' };
    } else {
      return { level: 'Medium', color: '#f59e0b', icon: '⭐⭐' };
    }
  };

  const isRecommended = (subtopic, index) => {
    const difficulty = getDifficulty(subtopic);

    // Recommend based on education level
    if (educationLevel === 'juniorLevel') {
      // Prioritize easy topics for junior level
      return difficulty.level === 'Easy' && index < 5;
    } else if (educationLevel === 'highSchoolLevel') {
      // Mix of easy and medium for high school
      return (difficulty.level === 'Easy' || difficulty.level === 'Medium') && index < 5;
    } else if (educationLevel === 'undergradLevel') {
      // All levels for undergraduate
      return index < 5;
    }

    // Default: recommend first few
    return index < 3;
  };

  // Filter subtopics by search query
  const filterSubtopics = (subtopicsList) => {
    if (!searchQuery.trim()) return subtopicsList;

    const query = searchQuery.toLowerCase();
    return subtopicsList.filter(subtopic => {
      const text = (subtopic.subtopic || subtopic).toLowerCase();
      return text.includes(query);
    });
  };

  // Group subtopics by category
  const groupSubtopicsByCategory = (subtopicsList) => {
    const grouped = {};

    subtopicsList.forEach(subtopic => {
      const category = categorizeSubtopic(subtopic);
      if (!grouped[category]) {
        grouped[category] = [];
      }
      grouped[category].push(subtopic);
    });

    return grouped;
  };

  // Highlight search matches
  const highlightMatch = (text, query) => {
    if (!query.trim()) return text;

    const parts = text.split(new RegExp(`(${query})`, 'gi'));
    return parts.map((part, index) =>
      part.toLowerCase() === query.toLowerCase()
        ? <mark key={index} style={{ background: '#fef08a', fontWeight: 'bold' }}>{part}</mark>
        : part
    );
  };

  const toggleCategory = (category) => {
    setCollapsedCategories(prev => ({
      ...prev,
      [category]: !prev[category]
    }));
  };

  // Show loading state
  if (loading) {
    return (
      <div style={{
        padding: '20px',
        maxWidth: '800px',
        margin: '0 auto',
        minHeight: '100vh',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center'
      }}>
        <LoadingSpinner size="large" />
        <div style={{
          marginTop: '20px',
          fontSize: '18px',
          fontWeight: 'bold',
          color: '#667eea',
          textAlign: 'center'
        }}>
          Generating subtopics for "{topic || 'your topic'}"...
        </div>
        <div style={{
          marginTop: '10px',
          fontSize: '14px',
          color: '#999',
          textAlign: 'center'
        }}>
          This may take 10-20 seconds
        </div>
        <div style={{
          marginTop: '30px',
          width: '100%',
          maxWidth: '600px'
        }}>
          <h3 style={{ fontSize: '16px', color: '#666', marginBottom: '15px' }}>
            Preview: Skeleton Loading
          </h3>
          <SkeletonLoader variant="line" />
          <div style={{ marginTop: '20px' }}>
            <SkeletonLoader variant="subtopic" />
            <SkeletonLoader variant="subtopic" />
            <SkeletonLoader variant="subtopic" />
            <SkeletonLoader variant="subtopic" />
            <SkeletonLoader variant="subtopic" />
          </div>
        </div>
      </div>
    );
  }

  // Show error state
  if (error) {
    return (
      <div
        role="alert"
        aria-live="assertive"
        style={{
          padding: '40px',
          textAlign: 'center',
          minHeight: '100vh',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center',
          alignItems: 'center'
        }}
      >
        <div style={{
          background: '#fee',
          border: '2px solid #fcc',
          borderRadius: '10px',
          padding: '30px',
          maxWidth: '600px'
        }}>
          <h1 style={{ color: '#c33', marginBottom: '15px' }}>⚠️ Error Loading Subtopics</h1>
          <p style={{ fontSize: '18px', color: '#666', marginBottom: '20px' }}>{error}</p>

          <div style={{
            background: '#fffbea',
            border: '1px solid #ffd700',
            borderRadius: '8px',
            padding: '15px',
            marginBottom: '20px',
            textAlign: 'left'
          }}>
            <strong style={{ color: '#856404' }}>💡 Suggested Actions:</strong>
            <ul style={{ marginTop: '10px', marginLeft: '20px', color: '#856404' }}>
              <li>Check your internet connection</li>
              <li>Try simplifying your topic</li>
              <li>Wait a moment and retry</li>
              <li>Contact support if the issue persists</li>
            </ul>
          </div>

          <div style={{ display: 'flex', gap: '15px', justifyContent: 'center', flexWrap: 'wrap' }}>
            <button
              onClick={retryFetchSubtopics}
              style={{
                padding: '12px 24px',
                background: '#10b981',
                color: 'white',
                border: 'none',
                borderRadius: '8px',
                fontSize: '16px',
                cursor: 'pointer',
                fontWeight: 'bold'
              }}
              aria-label="Retry loading subtopics"
            >
              🔄 Retry
            </button>
            <button
              onClick={() => navigate(-1)}
              style={{
                padding: '12px 24px',
                background: '#667eea',
                color: 'white',
                border: 'none',
                borderRadius: '8px',
                fontSize: '16px',
                cursor: 'pointer'
              }}
              aria-label="Go back to previous page"
            >
              ← Go Back
            </button>
            <button
              onClick={() => navigate('/')}
              style={{
                padding: '12px 24px',
                background: '#f0f0f0',
                color: '#333',
                border: 'none',
                borderRadius: '8px',
                fontSize: '16px',
                cursor: 'pointer'
              }}
              aria-label="Go to home page"
            >
              🏠 Home
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Safety check: ensure subtopics is always an array
  const safeSubtopics = Array.isArray(subtopics) ? subtopics : [];

  // Check if form is valid
  const isFormValid = educationLevel && levelOfDetail && focus.length > 0 && focus.length <= 10;

  if (safeSubtopics.length > 0) {
    return (
      <ErrorBoundary boundaryName="SubtopicPage">
        <main
          role="main"
          aria-label="Subtopic selection page"
          style={{ padding: '20px', maxWidth: '800px', margin: '0 auto' }}
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
                zIndex: 1000,
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

          <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <h1>Topic Selected: {topic || generatedTopic}</h1>
            <button
              onClick={() => setIsSettingsOpen(true)}
              style={{
                background: 'none',
                border: '1px solid #ccc',
                borderRadius: '5px',
                padding: '8px 12px',
                cursor: 'pointer',
                fontSize: '14px'
              }}
            >
              ⚙️ Settings
            </button>
          </header>

          <SettingsModal
            isOpen={isSettingsOpen}
            onClose={() => setIsSettingsOpen(false)}
            onSave={(settings) => {
              setLearningStyle(settings.learningStyle);
              // Also update language in apiClient if needed, though it reads from localStorage
            }}
          />

          {/* Keyboard shortcuts hint */}
          <div style={{
            background: '#e3f2fd',
            border: '1px solid #90caf9',
            borderRadius: '8px',
            padding: '12px',
            marginBottom: '20px',
            fontSize: '13px',
            color: '#0d47a1'
          }}>
            <div style={{ marginBottom: '8px' }}>
              💡 <strong>Keyboard shortcuts:</strong>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '8px' }}>
              <div>
                <kbd style={{
                  padding: '2px 6px',
                  border: '1px solid #90caf9',
                  borderRadius: '3px',
                  background: 'white',
                  fontSize: '11px',
                  margin: '0 3px'
                }}>Ctrl+A</kbd> Select all
              </div>
              <div>
                <kbd style={{
                  padding: '2px 6px',
                  border: '1px solid #90caf9',
                  borderRadius: '3px',
                  background: 'white',
                  fontSize: '11px',
                  margin: '0 3px'
                }}>Ctrl+D</kbd> Deselect all
              </div>
              <div>
                <kbd style={{
                  padding: '2px 6px',
                  border: '1px solid #90caf9',
                  borderRadius: '3px',
                  background: 'white',
                  fontSize: '11px',
                  margin: '0 3px'
                }}>Ctrl+Z</kbd> Undo
              </div>
              <div>
                <kbd style={{
                  padding: '2px 6px',
                  border: '1px solid #90caf9',
                  borderRadius: '3px',
                  background: 'white',
                  fontSize: '11px',
                  margin: '0 3px'
                }}>Ctrl+Y</kbd> Redo
              </div>
              <div>
                <kbd style={{
                  padding: '2px 6px',
                  border: '1px solid #90caf9',
                  borderRadius: '3px',
                  background: 'white',
                  fontSize: '11px',
                  margin: '0 3px'
                }}>Ctrl+F</kbd> Search
              </div>
              <div>
                <kbd style={{
                  padding: '2px 6px',
                  border: '1px solid #90caf9',
                  borderRadius: '3px',
                  background: 'white',
                  fontSize: '11px',
                  margin: '0 3px'
                }}>1-9</kbd> Toggle item
              </div>
              <div>
                <kbd style={{
                  padding: '2px 6px',
                  border: '1px solid #90caf9',
                  borderRadius: '3px',
                  background: 'white',
                  fontSize: '11px',
                  margin: '0 3px'
                }}>Esc</kbd> Go back
              </div>
            </div>
          </div>

          {validationError && (
            <div
              role="alert"
              aria-live="assertive"
              style={{
                background: '#fff3cd',
                border: '2px solid #ffc107',
                borderRadius: '8px',
                padding: '15px',
                marginBottom: '20px',
                color: '#856404'
              }}
            >
              ⚠️ {validationError}
            </div>
          )}

          <form onSubmit={(e) => e.preventDefault()} aria-label="Subtopic selection form">
            <fieldset style={{ border: 'none', padding: 0, margin: 0 }}>
              <legend className="visually-hidden">Configuration Options</legend>

              <div style={{ marginBottom: '30px' }}>
                <label htmlFor="levelOfDetail" style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
                  Level of Detail <span style={{ color: 'red' }}>*</span>
                </label>
                <select
                  id="levelOfDetail"
                  value={levelOfDetail}
                  onChange={handleLevelOfDetailChange}
                  style={{
                    width: '100%',
                    padding: '10px',
                    fontSize: '16px',
                    borderRadius: '5px',
                    border: '2px solid #ddd',
                    marginBottom: '15px'
                  }}
                  required
                  aria-required="true"
                  aria-invalid={validationError && !levelOfDetail}
                >
                  <option value="">Select level of detail...</option>
                  <option value="lowDetail">Low - Brief overview</option>
                  <option value="mediumDetail">Medium - Balanced explanation</option>
                  <option value="highDetail">High - In-depth coverage</option>
                </select>

                <label htmlFor="educationLevel" style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
                  Education Level <span style={{ color: 'red' }}>*</span>
                </label>
                <select
                  id="educationLevel"
                  value={educationLevel}
                  onChange={handleEducationLevelChange}
                  style={{
                    width: '100%',
                    padding: '10px',
                    fontSize: '16px',
                    borderRadius: '5px',
                    border: '2px solid #ddd'
                  }}
                  required
                  aria-required="true"
                  aria-invalid={validationError && !educationLevel}
                >
                  <option value="">Select education level...</option>
                  <option value="juniorLevel">Junior Level (Ages 8-12)</option>
                  <option value="highSchoolLevel">High School Level (Ages 13-18)</option>
                  <option value="undergradLevel">Undergraduate Level (Ages 18+)</option>
                </select>
              </div>
            </fieldset>

            <fieldset style={{ border: 'none', padding: 0, margin: 0 }}>
              <legend>
                <h3 style={{ marginBottom: '15px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap' }}>
                  <span>
                    Select Subtopics <span style={{ color: 'red' }}>*</span>
                  </span>
                  <span style={{ fontSize: '14px', fontWeight: 'normal', color: focus.length > 10 ? '#c33' : '#666' }}>
                    {focus.length} of {safeSubtopics.length} selected (max 10)
                  </span>
                </h3>
              </legend>

              {/* Search and Filter Controls */}
              <div style={{
                background: '#f8f9fa',
                border: '1px solid #ddd',
                borderRadius: '8px',
                padding: '15px',
                marginBottom: '15px'
              }}>
                {/* Search Bar */}
                <div style={{ marginBottom: '12px' }}>
                  <label htmlFor="searchSubtopics" style={{ display: 'block', marginBottom: '5px', fontSize: '14px', fontWeight: 'bold' }}>
                    🔍 Search Subtopics
                  </label>
                  <input
                    ref={searchInputRef}
                    id="searchSubtopics"
                    name="searchSubtopics"
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Filter subtopics by keyword..."
                    style={{
                      width: '100%',
                      padding: '10px',
                      fontSize: '14px',
                      border: '2px solid #ddd',
                      borderRadius: '6px',
                      outline: 'none'
                    }}
                    onFocus={(e) => e.target.style.borderColor = '#667eea'}
                    onBlur={(e) => e.target.style.borderColor = '#ddd'}
                    aria-label="Search subtopics"
                  />
                  {searchQuery && (
                    <div style={{ marginTop: '5px', fontSize: '12px', color: '#666' }}>
                      Found: {filterSubtopics(safeSubtopics).length} matching subtopics
                    </div>
                  )}
                </div>

                {/* View Options and Undo/Redo */}
                <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap', alignItems: 'center' }}>
                  <label htmlFor="groupByCategoryCheckbox" style={{ display: 'flex', alignItems: 'center', gap: '6px', cursor: 'pointer', fontSize: '14px' }}>
                    <input
                      id="groupByCategoryCheckbox"
                      name="groupByCategory"
                      type="checkbox"
                      checked={groupByCategory}
                      onChange={(e) => setGroupByCategory(e.target.checked)}
                      style={{ cursor: 'pointer' }}
                      aria-label="Group subtopics by category"
                    />
                    📁 Group by Category
                  </label>

                  <div style={{ marginLeft: 'auto', display: 'flex', gap: '8px' }}>
                    <button
                      type="button"
                      onClick={undo}
                      disabled={historyIndex <= 0}
                      style={{
                        padding: '6px 12px',
                        background: historyIndex > 0 ? '#667eea' : '#e0e0e0',
                        color: historyIndex > 0 ? 'white' : '#999',
                        border: 'none',
                        borderRadius: '5px',
                        fontSize: '13px',
                        cursor: historyIndex > 0 ? 'pointer' : 'not-allowed',
                        fontWeight: 'bold'
                      }}
                      aria-label="Undo last selection"
                      title="Ctrl+Z"
                    >
                      ↶ Undo
                    </button>
                    <button
                      type="button"
                      onClick={redo}
                      disabled={historyIndex >= selectionHistory.length - 1}
                      style={{
                        padding: '6px 12px',
                        background: historyIndex < selectionHistory.length - 1 ? '#667eea' : '#e0e0e0',
                        color: historyIndex < selectionHistory.length - 1 ? 'white' : '#999',
                        border: 'none',
                        borderRadius: '5px',
                        fontSize: '13px',
                        cursor: historyIndex < selectionHistory.length - 1 ? 'pointer' : 'not-allowed',
                        fontWeight: 'bold'
                      }}
                      aria-label="Redo last selection"
                      title="Ctrl+Y"
                    >
                      ↷ Redo
                    </button>
                  </div>
                </div>
              </div>

              {/* Select All / Clear All buttons */}
              <div style={{
                display: 'flex',
                gap: '10px',
                marginBottom: '15px',
                flexWrap: 'wrap'
              }}>
                <button
                  type="button"
                  onClick={selectAllSubtopics}
                  style={{
                    padding: '8px 16px',
                    background: '#667eea',
                    color: 'white',
                    border: 'none',
                    borderRadius: '6px',
                    fontSize: '14px',
                    cursor: 'pointer',
                    transition: 'all 0.3s'
                  }}
                  onMouseOver={(e) => e.target.style.background = '#5568d3'}
                  onMouseOut={(e) => e.target.style.background = '#667eea'}
                  aria-label="Select all subtopics (up to 10)"
                >
                  ✓ Select All
                </button>
                <button
                  type="button"
                  onClick={clearAllSubtopics}
                  style={{
                    padding: '8px 16px',
                    background: '#f0f0f0',
                    color: '#333',
                    border: '1px solid #ddd',
                    borderRadius: '6px',
                    fontSize: '14px',
                    cursor: 'pointer',
                    transition: 'all 0.3s'
                  }}
                  onMouseOver={(e) => e.target.style.background = '#e0e0e0'}
                  onMouseOut={(e) => e.target.style.background = '#f0f0f0'}
                  aria-label="Clear all selections"
                >
                  ✕ Clear All
                </button>
              </div>

              <div role="group" aria-label="Subtopics list">
                {(() => {
                  const filteredSubtopics = filterSubtopics(safeSubtopics);

                  if (filteredSubtopics.length === 0) {
                    return (
                      <div style={{
                        padding: '30px',
                        textAlign: 'center',
                        background: '#fff3cd',
                        border: '2px dashed #ffc107',
                        borderRadius: '8px',
                        color: '#856404'
                      }}>
                        <div style={{ fontSize: '40px', marginBottom: '10px' }}>🔍</div>
                        <div style={{ fontSize: '16px', fontWeight: 'bold' }}>No matching subtopics found</div>
                        <div style={{ fontSize: '14px', marginTop: '5px' }}>Try a different search term</div>
                      </div>
                    );
                  }

                  if (groupByCategory) {
                    const grouped = groupSubtopicsByCategory(filteredSubtopics);
                    return Object.entries(grouped).map(([category, categorySubtopics]) => {
                      const isCollapsed = collapsedCategories[category];
                      return (
                        <div key={category} style={{ marginBottom: '20px' }}>
                          <button
                            type="button"
                            onClick={() => toggleCategory(category)}
                            style={{
                              width: '100%',
                              padding: '12px',
                              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                              color: 'white',
                              border: 'none',
                              borderRadius: '8px',
                              fontSize: '15px',
                              fontWeight: 'bold',
                              cursor: 'pointer',
                              display: 'flex',
                              justifyContent: 'space-between',
                              alignItems: 'center',
                              marginBottom: '10px',
                              transition: 'all 0.3s'
                            }}
                            aria-expanded={!isCollapsed}
                            aria-label={`${isCollapsed ? 'Expand' : 'Collapse'} ${category} category`}
                          >
                            <span>📁 {category} ({categorySubtopics.length})</span>
                            <span style={{ fontSize: '20px' }}>{isCollapsed ? '▼' : '▲'}</span>
                          </button>

                          {!isCollapsed && categorySubtopics.map((subtopic, index) => {
                            const subtopicText = subtopic.subtopic || subtopic;
                            const difficulty = getDifficulty(subtopic);
                            const recommended = isRecommended(subtopic, index);
                            const globalIndex = safeSubtopics.findIndex(s => (s.subtopic || s) === subtopicText);

                            return (
                              <div key={index} style={{
                                marginBottom: '10px',
                                padding: '12px',
                                background: focus.includes(subtopicText) ? '#e8f4ff' : '#f9f9f9',
                                borderRadius: '5px',
                                border: recommended ? `3px solid #fbbf24` : focus.includes(subtopicText) ? '2px solid #667eea' : '2px solid #ddd',
                                transition: 'all 0.3s',
                                position: 'relative'
                              }}>
                                {recommended && (
                                  <div style={{
                                    position: 'absolute',
                                    top: '-10px',
                                    right: '10px',
                                    background: '#fbbf24',
                                    color: '#78350f',
                                    padding: '4px 10px',
                                    borderRadius: '12px',
                                    fontSize: '11px',
                                    fontWeight: 'bold',
                                    boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
                                  }}>
                                    ⭐ Recommended
                                  </div>
                                )}
                                <label htmlFor={`subtopic-${categoryIndex}-${i}`} style={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }}>
                                  <input
                                    id={`subtopic-${categoryIndex}-${i}`}
                                    name={subtopicText}
                                    type="checkbox"
                                    onChange={handleCheckBoxChange}
                                    checked={focus.includes(subtopicText)}
                                    disabled={!focus.includes(subtopicText) && focus.length >= 10}
                                    style={{
                                      width: '20px',
                                      height: '20px',
                                      marginRight: '10px',
                                      cursor: (!focus.includes(subtopicText) && focus.length >= 10) ? 'not-allowed' : 'pointer'
                                    }}
                                    aria-label={`Select ${subtopicText}`}
                                  />
                                  <div style={{ flex: 1 }}>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                                      <span style={{ fontSize: '16px' }}>
                                        {globalIndex >= 0 && globalIndex < 9 && (
                                          <kbd style={{
                                            display: 'inline-block',
                                            padding: '2px 6px',
                                            marginRight: '6px',
                                            background: '#e0e0e0',
                                            border: '1px solid #999',
                                            borderRadius: '3px',
                                            fontSize: '11px',
                                            fontWeight: 'bold'
                                          }}>
                                            {globalIndex + 1}
                                          </kbd>
                                        )}
                                        {highlightMatch(subtopicText, searchQuery)}
                                      </span>
                                    </div>
                                    <div style={{
                                      display: 'inline-block',
                                      padding: '3px 8px',
                                      background: difficulty.color + '20',
                                      border: `1px solid ${difficulty.color}`,
                                      borderRadius: '4px',
                                      fontSize: '11px',
                                      fontWeight: 'bold',
                                      color: difficulty.color
                                    }}>
                                      {difficulty.icon} {difficulty.level}
                                    </div>
                                  </div>
                                </label>
                              </div>
                            );
                          })}
                        </div>
                      );
                    });
                  } else {
                    return filteredSubtopics.map((subtopic, index) => {
                      const subtopicText = subtopic.subtopic || subtopic;
                      const difficulty = getDifficulty(subtopic);
                      const recommended = isRecommended(subtopic, index);

                      return (
                        <div key={index} style={{
                          marginBottom: '10px',
                          padding: '12px',
                          background: focus.includes(subtopicText) ? '#e8f4ff' : '#f9f9f9',
                          borderRadius: '5px',
                          border: recommended ? `3px solid #fbbf24` : focus.includes(subtopicText) ? '2px solid #667eea' : '2px solid #ddd',
                          transition: 'all 0.3s',
                          position: 'relative'
                        }}>
                          {recommended && (
                            <div style={{
                              position: 'absolute',
                              top: '-10px',
                              right: '10px',
                              background: '#fbbf24',
                              color: '#78350f',
                              padding: '4px 10px',
                              borderRadius: '12px',
                              fontSize: '11px',
                              fontWeight: 'bold',
                              boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
                            }}>
                              ⭐ Recommended
                            </div>
                          )}
                          <label htmlFor={`subtopic-ungrouped-${index}`} style={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }}>
                            <input
                              id={`subtopic-ungrouped-${index}`}
                              name={subtopicText}
                              type="checkbox"
                              onChange={handleCheckBoxChange}
                              checked={focus.includes(subtopicText)}
                              disabled={!focus.includes(subtopicText) && focus.length >= 10}
                              style={{
                                width: '20px',
                                height: '20px',
                                marginRight: '10px',
                                cursor: (!focus.includes(subtopicText) && focus.length >= 10) ? 'not-allowed' : 'pointer'
                              }}
                              aria-label={`Select ${subtopicText}`}
                            />
                            <div style={{ flex: 1 }}>
                              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                                <span style={{ fontSize: '16px' }}>
                                  {index < 9 && (
                                    <kbd style={{
                                      display: 'inline-block',
                                      padding: '2px 6px',
                                      marginRight: '6px',
                                      background: '#e0e0e0',
                                      border: '1px solid #999',
                                      borderRadius: '3px',
                                      fontSize: '11px',
                                      fontWeight: 'bold'
                                    }}>
                                      {index + 1}
                                    </kbd>
                                  )}
                                  {highlightMatch(subtopicText, searchQuery)}
                                </span>
                              </div>
                              <div style={{
                                display: 'inline-block',
                                padding: '3px 8px',
                                background: difficulty.color + '20',
                                border: `1px solid ${difficulty.color}`,
                                borderRadius: '4px',
                                fontSize: '11px',
                                fontWeight: 'bold',
                                color: difficulty.color
                              }}>
                                {difficulty.icon} {difficulty.level}
                              </div>
                            </div>
                          </label>
                        </div>
                      );
                    });
                  }
                })()}
              </div>
            </fieldset>

            <Link
              to={{ pathname: "/Loadingscreen" }}
              state={{
                topic: topic || generatedTopic,
                educationLevel: educationLevel,
                focus: focus,
                levelOfDetail: levelOfDetail,
              }}
              onClick={handleGenerateClick}
              style={{ textDecoration: 'none' }}
              aria-disabled={!isFormValid}
            >
              <button
                type="button"
                className="enterDropdownButton"
                style={{
                  marginTop: '20px',
                  padding: '15px 30px',
                  background: isFormValid ? 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' : '#ccc',
                  color: 'white',
                  border: 'none',
                  borderRadius: '8px',
                  fontSize: '18px',
                  cursor: isFormValid ? 'pointer' : 'not-allowed',
                  width: '100%',
                  transition: 'all 0.3s',
                  fontWeight: 'bold',
                  boxShadow: isFormValid ? '0 4px 15px rgba(102, 126, 234, 0.4)' : 'none'
                }}
                disabled={!isFormValid}
                onMouseOver={(e) => {
                  if (isFormValid) {
                    e.target.style.transform = 'translateY(-2px)';
                    e.target.style.boxShadow = '0 6px 20px rgba(102, 126, 234, 0.5)';
                  }
                }}
                onMouseOut={(e) => {
                  if (isFormValid) {
                    e.target.style.transform = 'translateY(0)';
                    e.target.style.boxShadow = '0 4px 15px rgba(102, 126, 234, 0.4)';
                  }
                }}
                aria-label="Generate concept map"
              >
                {isFormValid ? '🚀 Generate Concept Map' : '⚠️ Complete form to continue'}
              </button>
            </Link>
          </form>

          {/* Add CSS for toast animation */}
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
            
            .visually-hidden {
              position: absolute;
              width: 1px;
              height: 1px;
              padding: 0;
              margin: -1px;
              overflow: hidden;
              clip: rect(0, 0, 0, 0);
              white-space: nowrap;
              border: 0;
            }
          `}</style>
        </main>
      </ErrorBoundary>
    );
  }

  // Fallback (should not reach here due to loading state)
  return (
    <LoadingSpinner
      size="large"
      message="Loading..."
      fullScreen
    />
  );
};

export default SubtopicPage;
