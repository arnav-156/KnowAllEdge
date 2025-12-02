# Frontend Migration Guide

## 🔄 Changes Required in Frontend

The backend now uses `/api/` prefix for all endpoints and secure image upload. Here's what needs to change in your frontend code.

---

## 1. Update API Base URL

### In All Frontend Files:

**Before:**
```javascript
const response = await axios.post('http://127.0.0.1:5000/create_subtopics', data);
```

**After:**
```javascript
const API_BASE_URL = 'http://localhost:5000/api';
const response = await axios.post(`${API_BASE_URL}/create_subtopics`, data);
```

---

## 2. Fix Image Upload (SubtopicPage.jsx)

### Current Issue:
The image upload is broken because:
1. It uses `URL.createObjectURL()` which creates a local blob URL
2. Backend expects actual file upload, not a URL

### Fix Required:

**File: `frontend/src/SubtopicPage.jsx`**

```javascript
// BEFORE (Lines 8-18)
const [imagePath, setImageUrl] = useState("");

const handleImageUpload = (e) => {
  const file = e.target.files[0];
  if (file) {
    const imageUrl = URL.createObjectURL(file);
    setImageUrl(imageUrl);
  }
};

// ... later ...
axios.post("http://127.0.0.1:5000/image2topic", { imagePath: imagePath })
```

```javascript
// AFTER
const [imageFile, setImageFile] = useState(null);
const [imagePreview, setImagePreview] = useState("");

const handleImageUpload = (e) => {
  const file = e.target.files[0];
  if (file) {
    setImageFile(file);
    const imageUrl = URL.createObjectURL(file);
    setImagePreview(imageUrl);
  }
};

// ... in useEffect ...
if (imageFile) {
  const formData = new FormData();
  formData.append('image', imageFile);
  
  axios.post('http://localhost:5000/api/image2topic', formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
  .then((response) => {
    setGeneratedTopic(response.data.generated_topic);
  })
  .catch((error) => {
    console.error("Error: ", error);
  });
}
```

```jsx
// Update image display (Line ~90)
{imagePreview && (
  <img src={imagePreview} className="inputImage" alt="Uploaded" />
)}
```

---

## 3. Update All API Endpoints

### Create a Centralized API Client

**Create new file: `frontend/src/api/client.js`**

```javascript
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000/api';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json'
  },
  timeout: 120000 // 2 minutes
});

// Request interceptor for logging
apiClient.interceptors.request.use(
  (config) => {
    console.log(`API Request: ${config.method.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    if (error.response) {
      // Server responded with error
      console.error('API Error:', error.response.data);
      
      if (error.response.status === 429) {
        alert('Too many requests. Please wait a moment and try again.');
      } else if (error.response.status === 500) {
        alert('Server error. Please try again later.');
      }
    } else if (error.request) {
      // No response received
      console.error('No response from server');
      alert('Cannot connect to server. Please check your connection.');
    }
    return Promise.reject(error);
  }
);

export default apiClient;
```

**Create: `frontend/src/api/services.js`**

```javascript
import apiClient from './client';

export const api = {
  // Health check
  health: () => apiClient.get('/health'),

  // Create subtopics
  createSubtopics: (topic) => 
    apiClient.post('/create_subtopics', { topic }),

  // Create presentation
  createPresentation: (data) =>
    apiClient.post('/create_presentation', {
      topic: data.topic,
      educationLevel: data.educationLevel,
      levelOfDetail: data.levelOfDetail,
      focus: data.focus
    }),

  // Image to topic (multipart form data)
  imageToTopic: (imageFile) => {
    const formData = new FormData();
    formData.append('image', imageFile);
    
    return apiClient.post('/image2topic', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });
  },

  // Generate image
  generateImage: (prompt) =>
    apiClient.post('/generate_image', { prompt })
};
```

---

## 4. Update SubtopicPage.jsx

**File: `frontend/src/SubtopicPage.jsx`**

```javascript
import { useEffect, useState } from "react";
import { useLocation, Link } from "react-router-dom";
import { api } from "./api/services";

const SubtopicPage = () => {
  const location = useLocation();
  const { topic: topic } = { topic: location.state?.topic } || { topic: "" };

  const [generatedTopic, setGeneratedTopic] = useState("");
  const [imageFile, setImageFile] = useState(location.state?.imageFile || null);
  const [imagePreview, setImagePreview] = useState("");

  const [subtopics, setSubtopics] = useState([]);
  const [focus, setFocus] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const [educationLevel, setEducationLevel] = useState("");
  const [levelOfDetail, setLevelOfDetail] = useState("");

  useEffect(() => {
    const fetchSubtopics = async () => {
      setLoading(true);
      setError("");

      try {
        // If image provided, extract topic first
        if (imageFile) {
          const imageResponse = await api.imageToTopic(imageFile);
          const extractedTopic = imageResponse.data.generated_topic;
          setGeneratedTopic(extractedTopic);
          
          // Use extracted topic
          const response = await api.createSubtopics(extractedTopic);
          setSubtopics(response.data.subtopics);
        } else {
          // Use provided topic
          const response = await api.createSubtopics(topic);
          setSubtopics(response.data.subtopics);
        }
      } catch (err) {
        console.error("Error: ", err);
        setError(err.response?.data?.error || "Failed to generate subtopics");
      } finally {
        setLoading(false);
      }
    };

    if (topic || imageFile) {
      fetchSubtopics();
    }
  }, [topic, imageFile]);

  const handleEducationLevelChange = (e) => {
    setEducationLevel(e.target.value);
  };

  const handleCheckBoxChange = (event) => {
    const { name, checked } = event.target;
    if (checked) {
      setFocus([...focus, name]);
    } else {
      setFocus(focus.filter((item) => item !== name));
    }
  };

  const handleLevelOfDetailChange = (e) => {
    setLevelOfDetail(e.target.value);
  };

  if (loading) {
    return (
      <div className="loading-container">
        <h1>Loading subtopics...</h1>
        <p>This may take a few moments</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="error-container">
        <h1>Error</h1>
        <p>{error}</p>
        <Link to="/">
          <button>Go Back</button>
        </Link>
      </div>
    );
  }

  if (subtopics.length > 0) {
    return (
      <>
        <h1>Topic Selected: {generatedTopic || topic}</h1>

        <div>
          <select value={levelOfDetail} onChange={handleLevelOfDetailChange}>
            <option value="">Level of Detail</option>
            <option value="lowDetail">Low</option>
            <option value="mediumDetail">Medium</option>
            <option value="highDetail">High</option>
          </select>

          <select value={educationLevel} onChange={handleEducationLevelChange}>
            <option value="">Education level</option>
            <option value="juniorLevel">Junior Level</option>
            <option value="highSchoolLevel">High School Level</option>
            <option value="undergradLevel">Undergrad Level</option>
          </select>

          {subtopics.map((subtopic, index) => (
            <div key={index}>
              <label>
                <input
                  name={subtopic}
                  type="checkbox"
                  onChange={handleCheckBoxChange}
                  checked={focus.includes(subtopic)}
                />
                {subtopic}
              </label>
            </div>
          ))}
        </div>

        <button 
          className="enterDropdownButton"
          disabled={!educationLevel || !levelOfDetail || focus.length === 0}
        >
          <Link
            to={{ pathname: "/Loadingscreen" }}
            state={{
              topic: generatedTopic || topic,
              educationLevel: educationLevel,
              focus: focus,
              levelOfDetail: levelOfDetail,
            }}
          >
            Generate
          </Link>
        </button>
      </>
    );
  }

  return <h1>Loading...</h1>;
};

export default SubtopicPage;
```

---

## 5. Update Homepage.jsx

**File: `frontend/src/Homepage.jsx`**

```javascript
import { useState } from "react";
import { Link } from "react-router-dom";
import "./App.css";

const Homepage = () => {
  const [topic, changeTopic] = useState("");
  const [imageFile, setImageFile] = useState(null);
  const [imagePreview, setImagePreview] = useState("");

  const handleImageUpload = (e) => {
    const file = e.target.files[0];
    if (file) {
      // Validate file size (10MB)
      if (file.size > 10 * 1024 * 1024) {
        alert("File size must be less than 10MB");
        return;
      }

      // Validate file type
      const allowedTypes = ['image/png', 'image/jpeg', 'image/jpg', 'image/gif', 'image/webp'];
      if (!allowedTypes.includes(file.type)) {
        alert("Please upload a valid image (PNG, JPEG, GIF, or WebP)");
        return;
      }

      setImageFile(file);
      const imageUrl = URL.createObjectURL(file);
      setImagePreview(imageUrl);
    }
  };

  return (
    <>
      <div className="top-section">
        <h1 className="big-heading">
          <span className="gradient-text">Welcome to </span>
          <span className="gradient-text2">KNOWALLEDGE.</span>
        </h1>
        <h1 className="typewriter">
          <p className="typed">
            <span className="gradient-text-container">
              <br />
              <span className="gradient-text">
                Your intuitive landscape for learning.
              </span>
            </span>
          </p>
        </h1>

        <h2>What do you want to learn about today?</h2>

        <div className="input-area">
          <div className="input-container">
            <input
              placeholder="Enter a topic"
              type="text"
              value={topic}
              onChange={(event) => changeTopic(event.target.value)}
            />

            <Link
              to={{ pathname: "/SubtopicPage" }}
              state={{ topic: topic }}
            >
              <button 
                className="enterPromptButton"
                disabled={!topic.trim()}
              >
                Generate subtopics
              </button>
            </Link>
          </div>

          <div>
            <h2>OR</h2>
          </div>

          <div>
            <h3>Select an image</h3>
            <input type="file" accept="image/*" onChange={handleImageUpload} />
            {imagePreview && (
              <>
                <img src={imagePreview} className="inputImage" alt="Uploaded" />
                <Link
                  to={{ pathname: "/SubtopicPage" }}
                  state={{ imageFile: imageFile }}
                >
                  <button className="enterPromptButton">
                    Generate from image
                  </button>
                </Link>
              </>
            )}
          </div>
        </div>
      </div>

      {/* ... rest of the component ... */}
    </>
  );
};

export default Homepage;
```

---

## 6. Update Loadingscreen.jsx

**File: `frontend/src/Loadingscreen.jsx`**

```javascript
import React, { useEffect, useState } from "react";
import { useLocation, Link } from "react-router-dom";
import { api } from "./api/services";

const Loadingscreen = () => {
  const location = useLocation();
  const topic = location.state?.topic || "Placeholder Topic";
  const { educationLevel } = {
    educationLevel: location.state.educationLevel,
  } || { educationLevel: "" };
  const { levelOfDetail } = { levelOfDetail: location.state.levelOfDetail } || {
    levelOfDetail: "",
  };

  const [titles, setTitles] = useState(location.state.focus);
  const [explanation, setExplanation] = useState([]);
  const [error, setError] = useState("");
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    const fetchPresentation = async () => {
      try {
        setProgress(10);
        
        const response = await api.createPresentation({
          topic: topic,
          educationLevel: educationLevel,
          focus: titles,
          levelOfDetail: levelOfDetail,
        });

        setProgress(90);
        setExplanation(response.data.explanations);
        setProgress(100);
      } catch (err) {
        console.error("Error: ", err);
        setError(err.response?.data?.error || "Failed to generate presentation");
      }
    };

    fetchPresentation();
  }, [educationLevel, levelOfDetail, titles, topic]);

  if (error) {
    return (
      <div className="error-container">
        <h1>Error</h1>
        <p>{error}</p>
        <Link to="/">
          <button>Go Back</button>
        </Link>
      </div>
    );
  }

  if (explanation.length > 0) {
    return (
      <Link
        to={{ pathname: "/GraphPage" }}
        state={{
          topic: topic,
          focus: titles,
          explanations: explanation
        }}
      >
        <button>View Graph</button>
      </Link>
    );
  }

  return (
    <div className="loading-container">
      <h1>Generating your personalized content...</h1>
      <p>Creating {titles.length} explanations</p>
      <div className="progress-bar">
        <div className="progress-fill" style={{ width: `${progress}%` }}></div>
      </div>
      <p>This may take a few moments. Please be patient.</p>
    </div>
  );
};

export default Loadingscreen;
```

---

## 7. Create Environment Configuration

**Create: `frontend/.env.development`**

```bash
VITE_API_URL=http://localhost:5000/api
```

**Create: `frontend/.env.production`**

```bash
VITE_API_URL=https://your-production-domain.com/api
```

---

## 8. Add Error Boundary (Optional but Recommended)

**Create: `frontend/src/components/ErrorBoundary.jsx`**

```javascript
import React from 'react';
import { Link } from 'react-router-dom';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('Error caught by boundary:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="error-container">
          <h1>Oops! Something went wrong</h1>
          <p>We're sorry for the inconvenience.</p>
          <Link to="/">
            <button>Go Home</button>
          </Link>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
```

**Update: `frontend/src/App.jsx`**

```javascript
import React from 'react';
import { BrowserRouter, Routes, Route } from "react-router-dom";
import ErrorBoundary from './components/ErrorBoundary';
import Homepage from './Homepage';
import SubtopicPage from './SubtopicPage';
import GraphPage from './GraphPage';
import Loadingscreen from './Loadingscreen';

const App = () => {
  return (
    <ErrorBoundary>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Homepage/>}/>
          <Route path="SubtopicPage" element={<SubtopicPage />} />
          <Route path="Loadingscreen" element={<Loadingscreen />} />
          <Route path="GraphPage" element={<GraphPage />} />
        </Routes>
      </BrowserRouter>
    </ErrorBoundary>
  );
};

export default App;
```

---

## 9. Summary of Frontend Changes

### Files to Create:
1. `frontend/src/api/client.js` - Axios client with interceptors
2. `frontend/src/api/services.js` - API service functions
3. `frontend/src/components/ErrorBoundary.jsx` - Error handling
4. `frontend/.env.development` - Dev environment config
5. `frontend/.env.production` - Prod environment config

### Files to Update:
1. `frontend/src/Homepage.jsx` - Fix image upload
2. `frontend/src/SubtopicPage.jsx` - Use new API, fix image handling
3. `frontend/src/Loadingscreen.jsx` - Use new API
4. `frontend/src/App.jsx` - Add ErrorBoundary

### API Endpoint Changes:
- `/create_subtopics` → `/api/create_subtopics`
- `/create_presentation` → `/api/create_presentation`
- `/image2topic` → `/api/image2topic` (now uses multipart/form-data)

---

## 🧪 Testing After Migration

1. **Test topic input:**
   - Enter "Machine Learning"
   - Should generate 15 subtopics quickly

2. **Test image upload:**
   - Upload an image
   - Should extract topic and generate subtopics

3. **Test concept map generation:**
   - Select subtopics
   - Choose education level and detail
   - Should generate explanations fast (parallel processing)

4. **Test caching:**
   - Try same topic twice
   - Second request should be instant

5. **Test error handling:**
   - Try with invalid input
   - Should show user-friendly error

---

## 📞 Need Help?

If you encounter issues:
1. Check browser console for errors
2. Check backend logs: `backend/app.log`
3. Test API directly: `http://localhost:5000/api/health`
4. Review API docs: `http://localhost:5000/api/docs`
