/* eslint-disable no-unused-vars */
import React, { useCallback, useEffect, useState, useRef } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { Link } from "react-router-dom";
import apiClient from "./utils/apiClient";
import analytics from "./utils/analytics";
import LoadingSpinner from "./components/LoadingSpinner";

const Loadingscreen = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const topic = location.state?.topic || "Placeholder Topic";
  const { educationLevel } = {
    educationLevel: location.state?.educationLevel,
  } || { educationLevel: "" };
  const { levelOfDetail } = { levelOfDetail: location.state?.levelOfDetail } || {
    levelOfDetail: "",
  };

  // Ensure titles is always an array
  const [titles, setTitles] = useState(Array.isArray(location.state?.focus) ? location.state.focus : []);
  const [explanation, setExplanation] = useState([]);
  const [error, setError] = useState(null);
  const [progress, setProgress] = useState(0);
  const [currentStatus, setCurrentStatus] = useState("Initializing...");
  const [currentSubtopic, setCurrentSubtopic] = useState(0);
  const [estimatedTimeRemaining, setEstimatedTimeRemaining] = useState(30);
  const [isCancelled, setIsCancelled] = useState(false);
  const [timedOut, setTimedOut] = useState(false);
  const [funMessage, setFunMessage] = useState("");
  const [funFact, setFunFact] = useState("");
  const [floatingKeywords, setFloatingKeywords] = useState([]);
  const [showConfetti, setShowConfetti] = useState(false);
  
  const isMountedRef = useRef(true);
  const abortControllerRef = useRef(null);
  const timeoutIdRef = useRef(null);
  const startTimeRef = useRef(Date.now());
  const audioRef = useRef(null);
  const hasFetchedRef = useRef(false); // Prevent multiple fetches
  
  // Fun loading messages
  const funMessages = [
    `Teaching AI about ${topic}...`,
    `Diving deep into ${topic}...`,
    `Consulting the knowledge universe about ${topic}...`,
    `Brewing some ${topic} magic...`,
    `Organizing ${topic} neurons...`,
    `Summoning ${topic} wisdom...`,
    `Crafting your ${topic} masterpiece...`,
    `Connecting ${topic} dots...`,
    `Unlocking ${topic} secrets...`,
    `Building your ${topic} knowledge tree...`
  ];
  
  // Fun facts for different topics
  const topicFunFacts = {
    default: [
      "💡 Did you know? The average person learns best through visual representations!",
      "🧠 Fun fact: Your brain can hold approximately 2.5 petabytes of information!",
      "📚 Studies show concept maps improve retention by up to 50%!",
      "✨ Learning something new creates new neural pathways in your brain!",
      "🎯 Breaking complex topics into smaller chunks improves understanding!",
      "🚀 The more you learn, the easier it becomes to learn new things!",
      "💪 Your brain is like a muscle - it gets stronger with use!",
      "🌟 Visualization is one of the most powerful learning techniques!"
    ]
  };

  useEffect(() => {
    isMountedRef.current = true;
    startTimeRef.current = Date.now();
    
    // Initialize fun message
    const randomMessage = funMessages[Math.floor(Math.random() * funMessages.length)];
    setFunMessage(randomMessage);
    
    // Initialize fun fact
    const facts = topicFunFacts.default;
    const randomFact = facts[Math.floor(Math.random() * facts.length)];
    setFunFact(randomFact);
    
    // Generate floating keywords from topic and titles
    const keywords = [topic, ...titles].slice(0, 8);
    setFloatingKeywords(keywords);
    
    // Rotate fun messages
    const messageInterval = setInterval(() => {
      if (isMountedRef.current && !isCancelled) {
        const newMessage = funMessages[Math.floor(Math.random() * funMessages.length)];
        setFunMessage(newMessage);
      }
    }, 5000);
    
    // Rotate fun facts
    const factInterval = setInterval(() => {
      if (isMountedRef.current && !isCancelled) {
        const facts = topicFunFacts.default;
        const newFact = facts[Math.floor(Math.random() * facts.length)];
        setFunFact(newFact);
      }
    }, 8000);
    
    // Initialize completion audio
    audioRef.current = new Audio('data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdJivrJBhNjVgodDbq2EcBj+a2/LDciUFLIHO8tiJNwgZaLvt559NEAxQp+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+DyvmwhBjKO0/LPfSwFIHTD796VRAwYZ7vq659MEg1MovDyvGchBjaR1fPOhC0FH3LB8N+UQwsVXrPs7K1aEwlFnODyt2sgBjOS0/LOgCwFI3fF8N+SRAoUXbLs66xZEwpDm+Dzul4hBjKQ0fPPgywFI3fE8N+TRAoVXrLt7KxYEwlDnODzt2wgBjKR0vPQhC0FInbD8N6UQwsVXbPs66xYFApDm+D0ulwjBjGQ0fPPfywFI3fE8N+SQwsVXrLs66xYEwlDnOHzuVwjBjGR0fPQgSwFInbE8d6UQwsVXbPr7KxZEwlDnOHzul4jBjCR0fPQgi0FI3bE8d6VQgsUXbPs7KtZFAlEnODzuF4jBjGR0fPPgiwFI3bE8d+UQgsUXbLr7KxZFAlDnN/zul4jBjCQ0fPQgiwFInbD8d6UQwsVXbLr7KtZEwlDnN/zul4jBjCR0fPPgiwFInbD8d+UQwsUXbLs7KtZEwlDnN/zuVwjBjCQ0fPPgiwFInbD8d+UQwsUXbPr7KtaEwlDnN/zuVwjBjCQ0fPPgiwFInbD8d+UQwsUXbPr7KtZEwlDnN/zuVwjBjCQ0fPPgiwFInbD8d+VQwsUXLPs7KtaEwlDnN/zuFwjBjCQ0fPPgiwFInbD8d+VQwsUXLLr7KxZFAlDm9/0uVsjBjCQ0fPPgiwFInbD8d+VQwsUXLLs7KtZEwlDm9/0ulsjBjCQ0PPPgiwFInbD8d+VQwsUXLLs66xZEwlDm9/0ul4jBi+R0PPPgiwFInbE8d+VQgsUXLPr66xZEwlDnODzul4jBjCQ0PPPgiwFInbD8d+VQgsUXLPr66xZEwlDnODzul4jBi+Q0PPPgiwFInbD8d+VQgsUXLLr66xZEwlDnODzul4jBi+Q0PPPgiwFInbD8d+VQgsUXLLr66xZEwlDnODzul4jBi+Q0PPPgiwFInbD8d+VQgsUXLLr66xZEwlDnODzul4jBi+Q0PPPgiwFInbD8d+VQgsUXLLr66xZEwlDnODzul4jBi+Q0PPPgiwFInbD8d+VQgsUXLLr66xZEwlDnODzul4jBi+Q0PPPgiwFInbD8d+VQgsUXLLr66xZEwlDnODzul4jBi+Q0PPPgiwFInbD8d+VQgsUXLLr66xZEwlDnODzul4jBi+Q0PPPgiwFInbD8d+VQgsUXLLr66xZEwlDnODzul4j');
    
    // Set up 60-second timeout
    timeoutIdRef.current = setTimeout(() => {
      if (isMountedRef.current && explanation.length === 0) {
        setTimedOut(true);
        setError("Request timed out after 60 seconds. The server may be overloaded. Please try again.");
        analytics.trackError(new Error("Request timeout"), { 
          page: 'Loadingscreen', 
          action: 'timeout',
          duration: 60
        });
        
        // Abort ongoing request
        if (abortControllerRef.current) {
          abortControllerRef.current.abort();
        }
      }
    }, 60000); // 60 seconds
    
    return () => {
      isMountedRef.current = false;
      clearInterval(messageInterval);
      clearInterval(factInterval);
      if (timeoutIdRef.current) {
        clearTimeout(timeoutIdRef.current);
      }
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, []); // Run only once on mount - removed problematic dependencies

  // Track page load only once on mount
  useEffect(() => {
    analytics.trackPageLoad('Loadingscreen');
  }, []);

  useEffect(() => {
    // Prevent multiple fetches
    if (hasFetchedRef.current) return;
    
    // Validate required data
    if (!topic || !educationLevel || !levelOfDetail || titles.length === 0) {
      setError("Missing required information. Please go back and try again.");
      analytics.trackError(new Error("Missing required data"), { 
        page: 'Loadingscreen', 
        action: 'validation' 
      });
      return;
    }
    
    hasFetchedRef.current = true; // Mark as fetched
    
    const fetchPresentation = async () => {
      try {
        // Create abort controller for cancellation
        abortControllerRef.current = new AbortController();
        
        setProgress(5);
        setCurrentStatus("Analyzing topic...");
        
        // Simulate progress updates
        const progressInterval = setInterval(() => {
          if (!isMountedRef.current || isCancelled) {
            clearInterval(progressInterval);
            return;
          }
          
          setProgress(prev => {
            if (prev < 85) {
              const increment = Math.random() * 5 + 2;
              return Math.min(prev + increment, 85);
            }
            return prev;
          });
          
          // Update estimated time
          const elapsed = (Date.now() - startTimeRef.current) / 1000;
          const avgTimePerSubtopic = 10; // seconds
          const totalEstimated = titles.length * avgTimePerSubtopic;
          const remaining = Math.max(0, Math.ceil(totalEstimated - elapsed));
          setEstimatedTimeRemaining(remaining);
        }, 1000);
        
        // Update status messages
        setTimeout(() => {
          if (isMountedRef.current) setCurrentStatus("Generating explanations...");
        }, 3000);
        
        setTimeout(() => {
          if (isMountedRef.current) setCurrentStatus("Processing subtopics...");
        }, 8000);
        
        setTimeout(() => {
          if (isMountedRef.current) setCurrentStatus("Almost done...");
        }, 15000);
        
        // Simulate subtopic processing
        const subtopicInterval = setInterval(() => {
          if (!isMountedRef.current || isCancelled) {
            clearInterval(subtopicInterval);
            return;
          }
          setCurrentSubtopic(prev => Math.min(prev + 1, titles.length));
        }, 5000);
        
        setProgress(10);
        
        const response = await apiClient.createPresentation(
          topic,
          educationLevel,
          levelOfDetail,
          titles,
          abortControllerRef.current.signal
        );
        
        // Clear intervals
        clearInterval(progressInterval);
        clearInterval(subtopicInterval);
        
        if (!isMountedRef.current || isCancelled) return;
        
        setProgress(90);
        setCurrentStatus("Finalizing...");
        
        // Ensure response has explanations
        const explanations = response.data?.explanations || response.explanations || [];
        setExplanation(Array.isArray(explanations) ? explanations : []);
        
        // Track successful generation
        analytics.trackTaskCompletion('generate_presentation', true);
        
        setProgress(100);
        setCurrentStatus("Complete!");
        setCurrentSubtopic(titles.length);
        
        // Trigger confetti animation
        setShowConfetti(true);
        
        // Play completion sound
        if (audioRef.current) {
          audioRef.current.play().catch(err => {
            console.log('Audio play failed:', err);
          });
        }
        
        // Hide confetti after 4 seconds
        setTimeout(() => {
          if (isMountedRef.current) {
            setShowConfetti(false);
          }
        }, 4000);
      } catch (error) {
        if (!isMountedRef.current) return;
        
        // Handle cancellation
        if (error.name === 'AbortError' || isCancelled) {
          console.log("Request cancelled by user");
          return;
        }
        
        console.error("Error: ", error);
        
        // Extract meaningful error message
        let errorMessage = "Failed to generate presentation. Please try again.";
        
        if (error.response) {
          // API returned an error response
          errorMessage = error.response.data?.error || 
                        error.response.data?.message || 
                        `Server error: ${error.response.status} ${error.response.statusText}`;
        } else if (error.request) {
          // Request made but no response
          errorMessage = "Network error: Unable to reach the server. Please check your internet connection.";
        } else if (error.message) {
          // Something else happened
          errorMessage = error.message;
        }
        
        setError(errorMessage);
        analytics.trackError(error, { 
          page: 'Loadingscreen', 
          action: 'fetchPresentation',
          errorMessage: errorMessage
        });
      }
    };
    
    fetchPresentation();
  }, [educationLevel, levelOfDetail, titles, topic, isCancelled]);
  
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
          <h1 style={{ color: '#c33' }}>
            {timedOut ? '⏱️ Request Timed Out' : '⚠️ Generation Failed'}
          </h1>
          <p style={{ fontSize: '18px', color: '#666', marginBottom: '10px' }}>{error}</p>
          {timedOut && (
            <p style={{ fontSize: '14px', color: '#999', fontStyle: 'italic' }}>
              Tip: Try reducing the number of subtopics or simplifying your topic.
            </p>
          )}
          <div style={{ display: 'flex', gap: '15px', justifyContent: 'center', marginTop: '20px' }}>
            <button 
              onClick={() => {
                setError(null);
                setTimedOut(false);
                setProgress(0);
                setCurrentStatus("Initializing...");
                window.location.reload();
              }}
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
              aria-label="Retry generating presentation"
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
              aria-label="Start over from home"
            >
              🏠 Start Over
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Safety check: ensure explanation is an array
  const safeExplanation = Array.isArray(explanation) ? explanation : [];

  if (safeExplanation.length > 0) {
    return (
      <div style={{ 
        textAlign: 'center', 
        padding: '40px',
        minHeight: '100vh',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
        alignItems: 'center'
      }}>
        <div style={{
          background: 'white',
          borderRadius: '15px',
          padding: '40px',
          boxShadow: '0 10px 40px rgba(0,0,0,0.1)',
          maxWidth: '600px'
        }}>
          <div style={{ fontSize: '80px', marginBottom: '20px' }}>✅</div>
          <h1 style={{ color: '#10b981', marginBottom: '15px' }}>Success!</h1>
          <p style={{ fontSize: '18px', color: '#666', marginBottom: '30px' }}>
            Your concept map has been generated successfully!
          </p>
          <Link
            to={{ pathname: "/GraphPage" }}
            state={{
              topic: topic,
              focus: titles,
              explanations: safeExplanation
            }}
            style={{ textDecoration: 'none' }}
          >
            <button style={{
              padding: '15px 40px',
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              color: 'white',
              border: 'none',
              borderRadius: '10px',
              fontSize: '18px',
              cursor: 'pointer',
              fontWeight: 'bold',
              transition: 'transform 0.3s',
              boxShadow: '0 4px 15px rgba(102, 126, 234, 0.4)'
            }}
            onMouseOver={(e) => e.target.style.transform = 'translateY(-2px)'}
            onMouseOut={(e) => e.target.style.transform = 'translateY(0)'}
            >
              View Concept Map 🗺️
            </button>
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div style={{ 
      minHeight: '100vh',
      display: 'flex',
      flexDirection: 'column',
      justifyContent: 'center',
      alignItems: 'center',
      padding: '20px'
    }}>
      {/* ARIA live region for screen readers */}
      <div 
        aria-live="polite" 
        aria-atomic="true" 
        style={{ 
          position: 'absolute', 
          left: '-10000px', 
          width: '1px', 
          height: '1px', 
          overflow: 'hidden' 
        }}
      >
        {currentStatus} - Progress: {Math.round(progress)}%
        {currentSubtopic > 0 && ` - Processing subtopic ${currentSubtopic} of ${titles.length}`}
      </div>

      <LoadingSpinner 
        size="large" 
        message={`Generating your personalized concept map...`}
      />
      
      {/* Floating keywords animation */}
      <div style={{
        position: 'absolute',
        top: 0,
        left: 0,
        width: '100%',
        height: '100%',
        pointerEvents: 'none',
        overflow: 'hidden',
        zIndex: 0
      }}>
        {floatingKeywords.map((keyword, index) => (
          <div
            key={index}
            style={{
              position: 'absolute',
              left: `${(index * 12.5) % 100}%`,
              top: `${(index * 15) % 100}%`,
              fontSize: '14px',
              color: 'rgba(102, 126, 234, 0.15)',
              fontWeight: 'bold',
              animation: `float ${8 + index}s infinite ease-in-out`,
              animationDelay: `${index * 0.5}s`,
              whiteSpace: 'nowrap',
              padding: '8px 12px',
              borderRadius: '20px',
              background: 'rgba(102, 126, 234, 0.05)'
            }}
          >
            {keyword}
          </div>
        ))}
      </div>
      
      {/* Fun message */}
      <div style={{
        marginTop: '20px',
        fontSize: '16px',
        fontStyle: 'italic',
        color: '#764ba2',
        minHeight: '25px',
        animation: 'fadeIn 0.5s ease-in',
        zIndex: 1
      }}>
        {funMessage}
      </div>
      
      {/* Status message */}
      <div style={{
        marginTop: '15px',
        fontSize: '18px',
        fontWeight: 'bold',
        color: '#667eea',
        minHeight: '30px',
        zIndex: 1
      }}>
        {currentStatus}
      </div>
      
      {/* Subtopic progress */}
      {currentSubtopic > 0 && (
        <div style={{
          marginTop: '10px',
          fontSize: '16px',
          color: '#666',
          background: '#f0f0f0',
          padding: '8px 16px',
          borderRadius: '20px'
        }}>
          Processing subtopic <strong>{Math.min(currentSubtopic, titles.length)}/{titles.length}</strong>
        </div>
      )}
      
      {/* Progress bar with percentage */}
      <div style={{
        marginTop: '20px',
        width: '400px',
        maxWidth: '90%'
      }}>
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          marginBottom: '8px',
          fontSize: '14px',
          color: '#666'
        }}>
          <span>Progress</span>
          <span style={{ fontWeight: 'bold', color: '#667eea' }}>
            {Math.round(progress)}%
          </span>
        </div>
        <div style={{
          background: '#e0e0e0',
          borderRadius: '10px',
          overflow: 'hidden',
          height: '12px',
          position: 'relative'
        }}>
          <div style={{
            height: '100%',
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            width: `${progress}%`,
            transition: 'width 0.5s ease-out',
            borderRadius: '10px',
            boxShadow: '0 2px 8px rgba(102, 126, 234, 0.4)',
            position: 'relative',
            overflow: 'hidden'
          }}>
            {/* Animated shimmer effect */}
            <div style={{
              position: 'absolute',
              top: 0,
              left: '-100%',
              width: '100%',
              height: '100%',
              background: 'linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent)',
              animation: 'shimmer 2s infinite'
            }}></div>
          </div>
        </div>
      </div>
      
      {/* Time remaining */}
      {estimatedTimeRemaining > 0 && progress < 90 && (
        <p style={{ 
          marginTop: '15px', 
          color: '#999', 
          fontSize: '14px' 
        }}>
          ⏱️ Estimated time remaining: <strong>{estimatedTimeRemaining}s</strong>
        </p>
      )}
      
      <p style={{ 
        marginTop: '10px', 
        color: '#999', 
        fontSize: '14px',
        maxWidth: '400px',
        textAlign: 'center'
      }}>
        Generating {titles.length} detailed explanation{titles.length !== 1 ? 's' : ''}
      </p>
      
      {/* Fun fact */}
      <div style={{
        marginTop: '20px',
        maxWidth: '500px',
        padding: '15px 20px',
        background: 'linear-gradient(135deg, #f0f4ff 0%, #e8f0ff 100%)',
        borderRadius: '12px',
        borderLeft: '4px solid #667eea',
        textAlign: 'center',
        animation: 'fadeIn 0.5s ease-in',
        boxShadow: '0 2px 10px rgba(102, 126, 234, 0.1)'
      }}>
        <p style={{ 
          color: '#667eea', 
          fontSize: '14px',
          lineHeight: '1.6',
          margin: 0
        }}>
          {funFact}
        </p>
      </div>
      
      {/* Cancel button */}
      <button
        onClick={() => {
          setIsCancelled(true);
          if (abortControllerRef.current) {
            abortControllerRef.current.abort();
          }
          analytics.trackInteraction('button_click', 'cancel_generation', { 
            progress: progress,
            timeElapsed: (Date.now() - startTimeRef.current) / 1000
          });
          navigate(-1);
        }}
        style={{
          marginTop: '30px',
          padding: '10px 24px',
          background: 'transparent',
          color: '#666',
          border: '2px solid #ddd',
          borderRadius: '8px',
          fontSize: '14px',
          cursor: 'pointer',
          transition: 'all 0.3s'
        }}
        onMouseOver={(e) => {
          e.target.style.borderColor = '#ff4444';
          e.target.style.color = '#ff4444';
        }}
        onMouseOut={(e) => {
          e.target.style.borderColor = '#ddd';
          e.target.style.color = '#666';
        }}
        aria-label="Cancel generation and go back"
      >
        ✕ Cancel
      </button>
      
      {/* Add CSS animation for shimmer */}
      <style>{`
        @keyframes shimmer {
          0% { left: -100%; }
          100% { left: 100%; }
        }
        
        @keyframes float {
          0%, 100% { 
            transform: translateY(0) translateX(0) rotate(0deg);
            opacity: 0.3;
          }
          25% { 
            transform: translateY(-20px) translateX(10px) rotate(5deg);
            opacity: 0.6;
          }
          50% { 
            transform: translateY(-40px) translateX(-10px) rotate(-5deg);
            opacity: 0.8;
          }
          75% { 
            transform: translateY(-20px) translateX(5px) rotate(3deg);
            opacity: 0.5;
          }
        }
        
        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(10px); }
          to { opacity: 1; transform: translateY(0); }
        }
        
        @keyframes confettiFall {
          0% {
            transform: translateY(-100vh) rotate(0deg);
            opacity: 1;
          }
          100% {
            transform: translateY(100vh) rotate(720deg);
            opacity: 0;
          }
        }
      `}</style>
      
      {/* Confetti animation */}
      {showConfetti && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          width: '100%',
          height: '100%',
          pointerEvents: 'none',
          zIndex: 9999
        }}>
          {[...Array(50)].map((_, i) => (
            <div
              key={i}
              style={{
                position: 'absolute',
                left: `${Math.random() * 100}%`,
                top: '-10px',
                width: '10px',
                height: '10px',
                background: [
                  '#667eea', '#764ba2', '#f093fb', '#4facfe', 
                  '#43e97b', '#fa709a', '#fee140', '#30cfd0'
                ][Math.floor(Math.random() * 8)],
                animation: `confettiFall ${2 + Math.random() * 2}s linear forwards`,
                animationDelay: `${Math.random() * 0.5}s`,
                borderRadius: Math.random() > 0.5 ? '50%' : '0',
                transform: `rotate(${Math.random() * 360}deg)`
              }}
            />
          ))}
        </div>
      )}
    </div>
  );
};

export default Loadingscreen;
