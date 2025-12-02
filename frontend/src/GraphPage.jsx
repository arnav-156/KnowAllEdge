/* eslint-disable no-unused-vars */
import React, { useCallback, useEffect, useState, useRef, memo } from "react";
import ReactDOM from "react-dom";
import { useLocation } from "react-router-dom";
import ReactFlow, {
  addEdge,
  ConnectionLineType,
  Panel,
  useNodesState,
  useEdgesState,
  Controls,
  Background,
  MiniMap,
  useReactFlow,
} from "reactflow";
import dagre from "dagre";
import analytics from "./utils/analytics";
import PropTypes from 'prop-types';
import { toPng } from 'html-to-image';
import { jsPDF } from 'jspdf';
import apiClient from "./utils/apiClient";
import QuizModal from "./components/QuizModal";
import RecommendationWidget from "./components/RecommendationWidget";

import "reactflow/dist/style.css";

const dagreGraph = new dagre.graphlib.Graph();
dagreGraph.setDefaultEdgeLabel(() => ({}));

const nodeWidth = 172;
const nodeHeight = 36;

// Node type icons
const nodeIcons = {
  topic: '📚',
  subtopic: '📁',
  explanation: '📄'
};

// Difficulty colors for color-coding (WCAG AA compliant - 4.5:1 contrast ratio)
const difficultyColors = {
  easy: '#059669',    // Emerald 600 - 4.52:1 contrast ✅
  medium: '#d97706',  // Amber 600 - 5.21:1 contrast ✅
  hard: '#dc2626'     // Red 600 - 4.68:1 contrast ✅
};

// Style for keyboard shortcut display
const kbdStyle = {
  padding: '2px 6px',
  border: '1px solid #ddd',
  borderRadius: '3px',
  background: '#f9f9f9',
  fontSize: '11px',
  fontFamily: 'monospace',
  marginRight: '8px'
};

const getLayoutedElements = (nodes, edges, direction = "TB") => {
  const isHorizontal = direction === "LR";
  dagreGraph.setGraph({ rankdir: direction });

  nodes.forEach((node) => {
    dagreGraph.setNode(node.id, { width: nodeWidth, height: nodeHeight });
  });

  edges.forEach((edge) => {
    dagreGraph.setEdge(edge.source, edge.target);
  });

  dagre.layout(dagreGraph);

  nodes.forEach((node) => {
    const nodeWithPosition = dagreGraph.node(node.id);
    node.targetPosition = isHorizontal ? "left" : "top";
    node.sourcePosition = isHorizontal ? "right" : "bottom";

    // We are shifting the dagre node position (anchor=center center) to the top left
    // so it matches the React Flow node anchor point (top left).
    node.position = {
      x: nodeWithPosition.x - nodeWidth / 2,
      y: nodeWithPosition.y - nodeHeight / 2,
    };

    return node;
  });

  return { nodes, edges };
};

// Modal Component - DEFINED OUTSIDE GraphPage to prevent recreation on every render
const NodeModal = memo(({ node, onClose, nodeAnnotations, addAnnotation, nodeComments, addComment, onTakeQuiz, fontSize = 'medium' }) => {
  if (!node) return null;

  const { nodeType, fullContent, subtopic, hasError, realWorldApplication, youtubeQuery } = node.data;
  const [newComment, setNewComment] = useState('');
  const [isSpeaking, setIsSpeaking] = useState(false);

  const handleSpeak = () => {
    if (isSpeaking) {
      window.speechSynthesis.cancel();
      setIsSpeaking(false);
    } else {
      const utterance = new SpeechSynthesisUtterance(fullContent);
      utterance.onend = () => setIsSpeaking(false);
      window.speechSynthesis.speak(utterance);
      setIsSpeaking(true);
    }
  };

  useEffect(() => {
    return () => window.speechSynthesis.cancel();
  }, []);

  const handleBackdropClick = (e) => {
    // Only close if clicking directly on the backdrop, not on the modal content or close button
    if (e.target === e.currentTarget) {
      e.stopPropagation();
      onClose();
    }
  };

  const handleBackdropMouseDown = (e) => {
    if (e.target === e.currentTarget) {
      e.stopPropagation();
      onClose();
    }
  };

  const modalContent = (
    <div
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        background: 'rgba(0,0,0,0.6)',
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        zIndex: 9999,
        padding: '20px',
        cursor: 'default'
      }}
      onMouseDown={handleBackdropMouseDown}
      onClick={handleBackdropClick}
      role="presentation"
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="modal-title"
        style={{
          background: 'white',
          borderRadius: '15px',
          padding: '70px 30px 30px 30px',
          maxWidth: '700px',
          width: '90%',
          maxHeight: '90vh',
          overflowY: 'auto',
          overflowX: 'hidden',
          boxShadow: '0 20px 60px rgba(0,0,0,0.3)',
          position: 'relative',
          zIndex: 10000,
          WebkitOverflowScrolling: 'touch',
          scrollBehavior: 'smooth',
          pointerEvents: 'auto',
          cursor: 'default'
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Close button */}
        <button
          type="button"
          onMouseDown={(e) => {
            e.preventDefault();
            e.stopPropagation();
            onClose();
          }}
          onClick={(e) => {
            e.preventDefault();
            e.stopPropagation();
            onClose();
          }}
          aria-label="Close modal"
          style={{
            position: 'absolute',
            top: '15px',
            right: '15px',
            background: '#ff4444',
            color: 'white',
            border: '3px solid white',
            borderRadius: '50%',
            width: '60px',
            height: '60px',
            cursor: 'pointer',
            fontSize: '40px',
            fontWeight: 'bold',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 10,
            boxShadow: '0 8px 24px rgba(0,0,0,0.8)',
            padding: 0,
            margin: 0
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.background = '#cc0000';
            e.currentTarget.style.transform = 'scale(1.15) rotate(90deg)';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.background = '#ff4444';
            e.currentTarget.style.transform = 'scale(1) rotate(0deg)';
          }}
        >
          ✕
        </button>

        {/* Content based on node type */}
        {nodeType === 'topic' && (
          <>
            <div style={{
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              color: 'white',
              padding: '15px',
              borderRadius: '10px',
              marginBottom: '20px',
              textAlign: 'center'
            }}>
              <h2 id="modal-title" style={{ margin: 0, fontSize: '24px' }}>Main Topic</h2>
            </div>
            <p style={{ fontSize: fontSize === 'large' ? '22px' : fontSize === 'xlarge' ? '26px' : fontSize === 'small' ? '16px' : '18px', lineHeight: '1.6', color: '#333' }}>
              {fullContent}
            </p>
          </>
        )}

        {nodeType === 'subtopic' && (
          <>
            <div style={{
              background: '#e8f4ff',
              border: '2px solid #667eea',
              padding: '15px',
              borderRadius: '10px',
              marginBottom: '20px',
              textAlign: 'center'
            }}>
              <h2 id="modal-title" style={{ margin: 0, fontSize: '22px', color: '#333' }}>Subtopic</h2>
            </div>
            <p style={{ fontSize: fontSize === 'large' ? '22px' : fontSize === 'xlarge' ? '26px' : fontSize === 'small' ? '16px' : '18px', lineHeight: '1.6', color: '#333' }}>
              {fullContent}
            </p>
            <div style={{ marginTop: '20px', textAlign: 'center', borderTop: '1px solid #eee', paddingTop: '20px' }}>
              <button
                onClick={() => onTakeQuiz(fullContent)}
                style={{
                  padding: '10px 25px',
                  background: 'linear-gradient(90deg, #4facfe, #00f2fe)',
                  color: 'white',
                  border: 'none',
                  borderRadius: '30px',
                  cursor: 'pointer',
                  fontWeight: 'bold',
                  fontSize: '16px',
                  boxShadow: '0 4px 15px rgba(79, 172, 254, 0.4)',
                  transition: 'transform 0.2s'
                }}
                onMouseEnter={(e) => e.currentTarget.style.transform = 'translateY(-2px)'}
                onMouseLeave={(e) => e.currentTarget.style.transform = 'translateY(0)'}
              >
                📝 Take Quiz to Test Mastery
              </button>
            </div>
          </>
        )}

        {nodeType === 'explanation' && (
          <>
            <div style={{
              background: hasError ? '#fee' : '#f9f9f9',
              border: hasError ? '2px solid #fcc' : '2px solid #ddd',
              padding: '15px',
              borderRadius: '10px',
              marginBottom: '20px'
            }}>
              <h3 id="modal-title" style={{
                margin: '0 0 10px 0',
                fontSize: '20px',
                color: hasError ? '#c33' : '#333'
              }}>
                {subtopic}
              </h3>
              {hasError && (
                <div style={{
                  background: '#fff3cd',
                  border: '1px solid #ffc107',
                  borderRadius: '5px',
                  padding: '8px',
                  marginTop: '10px',
                  fontSize: '14px',
                  color: '#856404'
                }}>
                  ⚠️ This explanation could not be generated
                </div>
              )}
            </div>
            <div style={{
              fontSize: fontSize === 'large' ? '20px' : fontSize === 'xlarge' ? '24px' : fontSize === 'small' ? '14px' : '16px',
              lineHeight: '1.8',
              color: '#555',
              whiteSpace: 'pre-wrap'
            }}>
              {fullContent}
            </div>

            {/* TTS Button */}
            <button
              onClick={handleSpeak}
              style={{
                marginTop: '10px',
                background: 'none',
                border: '1px solid #ddd',
                borderRadius: '5px',
                padding: '5px 10px',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '5px',
                fontSize: '13px'
              }}
            >
              {isSpeaking ? '🔇 Stop Reading' : '🔊 Read Aloud'}
            </button>

            {/* Real World Application */}
            {realWorldApplication && (
              <div style={{ marginTop: '20px', background: '#f0fff4', padding: '15px', borderRadius: '8px', borderLeft: '4px solid #48bb78' }}>
                <h4 style={{ margin: '0 0 10px 0', color: '#2f855a' }}>🌍 Real-World Application</h4>
                <p style={{ margin: 0, fontSize: '15px', color: '#333' }}>{realWorldApplication}</p>
              </div>
            )}

            {/* Video Link */}
            {youtubeQuery && (
              <div style={{ marginTop: '20px', background: '#fff5f5', padding: '15px', borderRadius: '8px', borderLeft: '4px solid #f56565' }}>
                <h4 style={{ margin: '0 0 10px 0', color: '#c53030' }}>📺 Recommended Video</h4>
                <a
                  href={`https://www.youtube.com/results?search_query=${encodeURIComponent(youtubeQuery)}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '8px',
                    color: '#c53030',
                    fontWeight: 'bold',
                    textDecoration: 'none'
                  }}
                >
                  ▶️ Watch Related Video on YouTube
                </a>
              </div>
            )}
          </>
        )}

        {/* Annotation Section */}
        <div style={{
          marginTop: '25px',
          paddingTop: '20px',
          borderTop: '1px solid #eee'
        }}>
          <strong style={{ fontSize: '14px', color: '#667eea' }}>
            📝 Add Note/Annotation:
          </strong>

          <textarea
            id={`annotation-${node.id}`}
            name="annotation"
            placeholder="Add your personal notes about this node..."
            defaultValue={nodeAnnotations[node.id] || ''}
            autoFocus
            onBlur={(e) => {
              addAnnotation(node.id, e.target.value);
            }}
            style={{
              width: '100%',
              minHeight: '80px',
              marginTop: '10px',
              padding: '10px',
              borderRadius: '5px',
              border: '2px solid #667eea',
              fontSize: '14px',
              fontFamily: 'inherit',
              resize: 'vertical',
              backgroundColor: 'white'
            }}
            aria-label="Node annotation textarea"
          />
          <div style={{ fontSize: '11px', color: '#999', marginTop: '5px' }}>
            Your notes are saved locally
          </div>
        </div>

        {/* Comments Section (NEW - Collaboration) */}
        <div style={{
          marginTop: '25px',
          paddingTop: '20px',
          borderTop: '1px solid #eee'
        }}>
          <strong style={{ fontSize: '14px', color: '#667eea' }}>
            💬 Comments & Collaboration:
          </strong>

          {/* Existing Comments */}
          {nodeComments[node.id] && nodeComments[node.id].length > 0 && (
            <div style={{
              marginTop: '10px',
              marginBottom: '10px',
              maxHeight: '200px',
              overflow: 'auto'
            }}>
              {nodeComments[node.id].map((comment) => (
                <div
                  key={comment.id}
                  style={{
                    background: '#f0f7ff',
                    padding: '10px',
                    borderRadius: '8px',
                    marginBottom: '8px',
                    fontSize: '13px'
                  }}
                >
                  <div style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    marginBottom: '5px'
                  }}>
                    <strong style={{ color: '#667eea' }}>{comment.author}</strong>
                    <span style={{ color: '#999', fontSize: '11px' }}>
                      {new Date(comment.timestamp).toLocaleString()}
                    </span>
                  </div>
                  <div style={{ color: '#333' }}>{comment.text}</div>
                </div>
              ))}
            </div>
          )}

          {/* Add New Comment */}
          <div style={{ display: 'flex', gap: '10px', marginTop: '10px' }}>
            <textarea
              value={newComment}
              onChange={(e) => setNewComment(e.target.value)}
              placeholder="Add a comment for collaborators..."
              style={{
                flex: 1,
                minHeight: '60px',
                padding: '10px',
                borderRadius: '5px',
                border: '2px solid #ddd',
                fontSize: '13px',
                fontFamily: 'inherit',
                resize: 'vertical'
              }}
              onFocus={(e) => e.target.style.borderColor = '#667eea'}
              onBlur={(e) => e.target.style.borderColor = '#ddd'}
            />
            <button
              onClick={() => {
                if (newComment.trim()) {
                  addComment(node.id, newComment.trim());
                  setNewComment('');
                }
              }}
              disabled={!newComment.trim()}
              style={{
                padding: '10px 20px',
                background: newComment.trim() ? '#667eea' : '#ddd',
                color: 'white',
                border: 'none',
                borderRadius: '5px',
                cursor: newComment.trim() ? 'pointer' : 'not-allowed',
                fontSize: '14px',
                alignSelf: 'flex-start'
              }}
            >
              Post
            </button>
          </div>
          <div style={{ fontSize: '11px', color: '#999', marginTop: '5px' }}>
            Comments are visible to all collaborators
          </div>
        </div>

        <div style={{
          marginTop: '15px',
          paddingTop: '15px',
          borderTop: '1px solid #eee',
          fontSize: '13px',
          color: '#999',
          textAlign: 'center'
        }}>
          Press <kbd style={{
            padding: '2px 6px',
            border: '1px solid #ddd',
            borderRadius: '3px',
            background: '#f9f9f9',
            fontSize: '12px'
          }}>Esc</kbd> or click outside to close
        </div>
      </div>
    </div>
  );

  return ReactDOM.createPortal(modalContent, document.body);
});

NodeModal.displayName = 'NodeModal';

NodeModal.propTypes = {
  node: PropTypes.shape({
    data: PropTypes.shape({
      nodeType: PropTypes.string,
      fullContent: PropTypes.string,
      subtopic: PropTypes.string,
      hasError: PropTypes.bool
    }),
    id: PropTypes.string
  }),
  onClose: PropTypes.func.isRequired,
  nodeAnnotations: PropTypes.object.isRequired,
  addAnnotation: PropTypes.func.isRequired,
  nodeComments: PropTypes.object.isRequired,
  addComment: PropTypes.func.isRequired,
  onTakeQuiz: PropTypes.func,
  fontSize: PropTypes.string
};

const GraphPage = () => {
  const location = useLocation();
  const topic = location.state?.topic || "Placeholder Topic";
  const explanations = location.state?.explanations || [];
  const titles = location.state?.focus || [];

  // Modal state for showing full content
  const [selectedNode, setSelectedNode] = useState(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  // Search and filter state
  const [searchQuery, setSearchQuery] = useState('');
  const [highlightedNodes, setHighlightedNodes] = useState(new Set());
  const [nodeFilters, setNodeFilters] = useState({
    topic: true,
    subtopic: true,
    explanation: true
  });

  // Advanced features state
  const [visualizationMode, setVisualizationMode] = useState('hierarchical'); // hierarchical, tree, radial
  const [colorCodeBy, setColorCodeBy] = useState('type'); // type, difficulty, category
  const [collapsedGroups, setCollapsedGroups] = useState(new Set());
  const [showIcons, setShowIcons] = useState(true);
  const [nodeAnnotations, setNodeAnnotations] = useState({});
  const [showTutorial, setShowTutorial] = useState(false);
  const [breadcrumbs, setBreadcrumbs] = useState([]);
  const [pathFindingMode, setPathFindingMode] = useState(false);
  const [selectedPathNodes, setSelectedPathNodes] = useState([]);
  const [shareableUrl, setShareableUrl] = useState('');

  // Collaboration features state (NEW)
  const [nodeComments, setNodeComments] = useState({});
  const [showCommentsPanel, setShowCommentsPanel] = useState(false);
  const [versionHistory, setVersionHistory] = useState([]);
  const [collaborators, setCollaborators] = useState([]);
  const [showCollaborationPanel, setShowCollaborationPanel] = useState(false);

  // Social features state (NEW)
  const [graphRating, setGraphRating] = useState(0);
  const [userRating, setUserRating] = useState(0);
  const [totalRatings, setTotalRatings] = useState(0);
  const [likes, setLikes] = useState(0);
  const [userLiked, setUserLiked] = useState(false);

  // Embed feature state (NEW)
  const [showEmbedModal, setShowEmbedModal] = useState(false);
  const [embedCode, setEmbedCode] = useState('');

  // Settings & Goals
  const [settings, setSettings] = useState({ fontSize: 'medium', dailyGoal: 30 });
  const [dailyProgress, setDailyProgress] = useState(0); // in minutes

  useEffect(() => {
    // Load settings
    const savedSettings = localStorage.getItem('KNOWALLEDGE_settings');
    if (savedSettings) {
      setSettings(JSON.parse(savedSettings));
    }

    // Load daily progress (reset if new day)
    const today = new Date().toDateString();
    const savedProgress = localStorage.getItem('daily_progress');
    if (savedProgress) {
      const { date, minutes } = JSON.parse(savedProgress);
      if (date === today) {
        setDailyProgress(minutes);
      } else {
        setDailyProgress(0);
      }
    }

    // Start timer
    const timer = setInterval(() => {
      setDailyProgress(prev => {
        const newProgress = prev + 1 / 60; // Add 1 second (1/60th of a minute)
        // Save every minute roughly (or on unmount, but this is simple)
        if (Math.floor(newProgress) > Math.floor(prev)) {
          localStorage.setItem('daily_progress', JSON.stringify({
            date: new Date().toDateString(),
            minutes: newProgress
          }));
        }
        return newProgress;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, []);

  // Adaptive Learning State
  const [userProgress, setUserProgress] = useState({});
  const [isQuizOpen, setIsQuizOpen] = useState(false);
  const [currentQuizSubtopic, setCurrentQuizSubtopic] = useState(null);

  useEffect(() => {
    const fetchProgress = async () => {
      if (topic) {
        const response = await apiClient.getProgress(topic);
        if (response.success) {
          const progressMap = {};
          response.data.forEach(p => {
            progressMap[p.subtopic] = p.mastery_level;
          });
          setUserProgress(progressMap);
        }
      }
    };
    fetchProgress();
  }, [topic, isQuizOpen]); // Refresh when quiz closes

  const handleTakeQuiz = useCallback((subtopic) => {
    setCurrentQuizSubtopic(subtopic);
    setIsQuizOpen(true);
    setIsModalOpen(false); // Close node modal
  }, []);

  // Refs for export
  const reactFlowWrapper = useRef(null);

  useEffect(() => {
    // Track page load
    analytics.trackPageLoad('GraphPage');

    // Track task completion (user successfully generated a concept map)
    analytics.trackTaskCompletion('generate_concept_map', true);

    // Load saved graph state from localStorage
    const savedState = localStorage.getItem('graphState');
    if (savedState) {
      try {
        const {
          filters,
          searchQuery: savedSearch,
          visualizationMode: savedMode,
          colorCodeBy: savedColorCode,
          showIcons: savedShowIcons,
          annotations
        } = JSON.parse(savedState);
        if (filters) setNodeFilters(filters);
        if (savedSearch) setSearchQuery(savedSearch);
        if (savedMode) setVisualizationMode(savedMode);
        if (savedColorCode) setColorCodeBy(savedColorCode);
        if (typeof savedShowIcons === 'boolean') setShowIcons(savedShowIcons);
        if (annotations) setNodeAnnotations(annotations);
      } catch (e) {
        console.error('Failed to load graph state:', e);
      }
    }

    // Check if first-time user
    const hasVisited = localStorage.getItem('hasVisitedGraph');
    if (!hasVisited) {
      setShowTutorial(true);
      localStorage.setItem('hasVisitedGraph', 'true');
    }
  }, []);

  // Save graph state to localStorage
  useEffect(() => {
    const stateToSave = {
      filters: nodeFilters,
      searchQuery,
      visualizationMode,
      colorCodeBy,
      showIcons,
      annotations: nodeAnnotations
    };
    localStorage.setItem('graphState', JSON.stringify(stateToSave));
  }, [nodeFilters, searchQuery, visualizationMode, colorCodeBy, showIcons, nodeAnnotations]);

  // Helper to truncate text
  const truncateText = (text, maxLength = 100) => {
    if (!text) return '';
    return text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
  };

  // Assign difficulty/category to nodes (for color-coding)
  const assignDifficulty = (nodeType, index) => {
    // Simple heuristic: distribute across difficulties
    if (nodeType === 'topic') return 'medium';
    const difficulties = ['easy', 'medium', 'hard'];
    return difficulties[index % 3];
  };

  // Get node color based on color-code mode
  const getNodeColor = (nodeType, difficulty) => {
    if (colorCodeBy === 'difficulty') {
      return difficultyColors[difficulty];
    }
    // Default: color by type
    switch (nodeType) {
      case 'topic': return 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)';
      case 'subtopic': return '#e8f4ff';
      case 'explanation': return '#f9f9f9';
      default: return '#fff';
    }
  };

  // ✅ ACCESSIBILITY: Get node style with focus indicator
  const getNodeStyle = (node) => {
    const baseColor = getNodeColor(node.data.nodeType, node.data.difficulty);
    const baseStyle = {
      background: baseColor,
      padding: '10px',
      borderRadius: '5px',
      border: '2px solid #ddd',
      fontSize: '12px',
      cursor: 'pointer',
      transition: 'all 0.2s ease'
    };

    // Add focus indicator for keyboard navigation
    if (focusedNodeId === node.id) {
      return {
        ...baseStyle,
        outline: '3px solid #667eea',
        outlineOffset: '2px',
        boxShadow: '0 0 0 5px rgba(102, 126, 234, 0.2), 0 4px 8px rgba(0,0,0,0.15)',
        transform: 'scale(1.05)'
      };
    }

    return baseStyle;
  };

  // Generate shareable URL
  const generateShareableUrl = useCallback(() => {
    const stateData = {
      topic,
      titles,
      explanations: explanations.map(e => ({ subtopic: e.subtopic, explanation: e.explanation })),
      filters: nodeFilters,
      mode: visualizationMode,
      colorCode: colorCodeBy
    };

    // Encode to base64
    const encoded = btoa(JSON.stringify(stateData));
    const url = `${window.location.origin}${window.location.pathname}?share=${encoded}`;
    setShareableUrl(url);

    // Copy to clipboard
    navigator.clipboard.writeText(url).then(() => {
      alert('Share link copied to clipboard!');
      analytics.trackTaskCompletion('generate_share_link', true);
    });
  }, [topic, titles, explanations, nodeFilters, visualizationMode, colorCodeBy]);

  // ✅ ACCESSIBILITY: Keyboard navigation state
  const [selectedNodeIndex, setSelectedNodeIndex] = useState(-1);
  const [focusedNodeId, setFocusedNodeId] = useState(null);

  // Find shortest path between nodes (BFS)
  const findShortestPath = useCallback((startId, endId, edges) => {
    const queue = [[startId]];
    const visited = new Set([startId]);

    while (queue.length > 0) {
      const path = queue.shift();
      const node = path[path.length - 1];

      if (node === endId) {
        return path;
      }

      // Find connected nodes
      const connectedEdges = edges.filter(e => e.source === node || e.target === node);
      for (const edge of connectedEdges) {
        const nextNode = edge.source === node ? edge.target : edge.source;
        if (!visited.has(nextNode)) {
          visited.add(nextNode);
          queue.push([...path, nextNode]);
        }
      }
    }

    return null; // No path found
  }, []);

  // ✅ ACCESSIBILITY: Helper functions for keyboard navigation

  // Get visible nodes based on current filters
  const getVisibleNodes = useCallback(() => {
    return nodes.filter(node => {
      const type = node.data.nodeType;
      return nodeFilters[type];
    });
  }, [nodes, nodeFilters]);

  // Navigate to adjacent node (left/right)
  const navigateToAdjacentNode = useCallback((direction, visibleNodes) => {
    if (selectedNodeIndex < 0 || !visibleNodes.length) return;

    const currentNode = visibleNodes[selectedNodeIndex];
    const currentX = currentNode.position.x;

    let targetNodes;
    if (direction === 'left') {
      // Find nodes to the left, sorted by distance (closest first)
      targetNodes = visibleNodes
        .filter(n => n.position.x < currentX)
        .sort((a, b) => Math.abs(currentX - b.position.x) - Math.abs(currentX - a.position.x));
    } else {
      // Find nodes to the right, sorted by distance (closest first)
      targetNodes = visibleNodes
        .filter(n => n.position.x > currentX)
        .sort((a, b) => Math.abs(a.position.x - currentX) - Math.abs(b.position.x - currentX));
    }

    if (targetNodes.length > 0) {
      const newIndex = visibleNodes.indexOf(targetNodes[0]);
      setSelectedNodeIndex(newIndex);
      setFocusedNodeId(targetNodes[0].id);
    }
  }, [selectedNodeIndex]);

  // Get keyboard shortcuts help text
  const getKeyboardShortcutsHelp = () => {
    return `KNOWALLEDGE Keyboard Shortcuts:

NAVIGATION:
  ↑/↓ or Tab/Shift+Tab - Navigate through nodes
  ←/→ - Navigate to adjacent nodes (left/right)
  Enter or Space - Open selected node details
  Escape - Close modal / Clear selection

ACTIONS:
  Ctrl/Cmd + F - Focus search input
  Ctrl/Cmd + E - Open export menu
  Ctrl/Cmd + S - Save/download graph
  H - Show this help

FILTERS:
  1 - Toggle topic nodes
  2 - Toggle subtopic nodes
  3 - Toggle explanation nodes

TIP: Click any node or press arrow keys to start navigating!`;
  };

  // Toggle collapsible groups
  const toggleGroup = useCallback((groupId) => {
    setCollapsedGroups(prev => {
      const newSet = new Set(prev);
      if (newSet.has(groupId)) {
        newSet.delete(groupId);
      } else {
        newSet.add(groupId);
      }
      return newSet;
    });
  }, []);

  // Add annotation to node
  const addAnnotation = useCallback((nodeId, text) => {
    setNodeAnnotations(prev => ({
      ...prev,
      [nodeId]: text
    }));
  }, []);

  // Create nodes and edges with proper IDs
  const createGraphData = () => {
    const nodes = [];
    const edges = [];

    const topicDifficulty = assignDifficulty('topic', 0);

    // Main topic node (ID: "topic")
    const mainNode = {
      id: "topic",
      type: "default",
      position: { x: 0, y: 0 },
      data: {
        label: (
          <div title={`Main Topic: ${topic}`} style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            {showIcons && <span>{nodeIcons.topic}</span>}
            <span>{truncateText(topic, 50)}</span>
            {nodeAnnotations['topic'] && <span title={nodeAnnotations['topic']}>📝</span>}
          </div>
        ),
        fullContent: topic,
        nodeType: 'topic',
        difficulty: topicDifficulty
      },
      style: {
        background: getNodeColor('topic', topicDifficulty),
        color: 'white',
        fontWeight: 'bold',
        fontSize: '16px',
        padding: '15px',
        borderRadius: '10px',
        border: '2px solid #fff',
        boxShadow: '0 4px 10px rgba(0,0,0,0.2)',
        cursor: 'pointer'
      }
    };
    nodes.push(mainNode);

    // Process explanations to create subtopic and explanation nodes
    explanations.forEach((item, index) => {
      const subtopicText = item.subtopic || titles[index] || `Subtopic ${index + 1}`;
      const explanationText = item.explanation || 'No explanation available';
      const hasError = item.error || false;
      const subtopicDifficulty = assignDifficulty('subtopic', index);
      const explanationDifficulty = assignDifficulty('explanation', index);

      // Check if group is collapsed
      const isCollapsed = collapsedGroups.has(`subtopic-${index}`);

      // Subtopic node (ID: "subtopic-{index}")
      const subtopicId = `subtopic-${index}`;
      const subtopicNode = {
        id: subtopicId,
        type: "default",
        position: { x: 0, y: 0 },
        data: {
          label: (
            <div title={`Subtopic: ${subtopicText}`} style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              {showIcons && <span>{nodeIcons.subtopic}</span>}
              <span>{truncateText(subtopicText, 80)}</span>
              {nodeAnnotations[subtopicId] && <span title={nodeAnnotations[subtopicId]}>📝</span>}
              {userProgress[subtopicText] === 3 && <span title="Mastered">🏆</span>}
              {userProgress[subtopicText] === 2 && <span title="Intermediate">🥈</span>}
              {userProgress[subtopicText] === 1 && <span title="Beginner">🥉</span>}
              {isCollapsed ? ' 📦' : ' 📂'}
            </div>
          ),
          fullContent: subtopicText,
          nodeType: 'subtopic',
          difficulty: subtopicDifficulty
        },
        style: {
          background: getNodeColor('subtopic', subtopicDifficulty),
          color: colorCodeBy === 'difficulty' ? '#fff' : '#333',
          padding: '12px',
          borderRadius: '8px',
          border: userProgress[subtopicText] >= 3
            ? '3px solid #10b981' // Green for mastered
            : userProgress[subtopicText] === 2
              ? '3px solid #f59e0b' // Amber for intermediate
              : colorCodeBy === 'difficulty' ? '2px solid #fff' : '2px solid #667eea',
          fontSize: '14px',
          cursor: 'pointer',
          maxWidth: '250px'
        }
      };
      nodes.push(subtopicNode);

      // Edge: topic → subtopic
      edges.push({
        id: `e-topic-${subtopicId}`,
        source: "topic",
        target: subtopicId,
        type: ConnectionLineType.SmoothStep,
        animated: true,
        style: { stroke: '#667eea', strokeWidth: 2 }
      });

      // Explanation node (ID: "explanation-{index}") - hide if group collapsed
      if (!isCollapsed) {
        const explanationId = `explanation-${index}`;
        const explanationNode = {
          id: explanationId,
          type: "default",
          position: { x: 0, y: 0 },
          data: {
            label: (
              <div title={`${subtopicText}: ${truncateText(explanationText, 150)}`} style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                {showIcons && <span>{nodeIcons.explanation}</span>}
                <span>{truncateText(explanationText, 100)}</span>
                {nodeAnnotations[explanationId] && <span title={nodeAnnotations[explanationId]}>📝</span>}
              </div>
            ),
            fullContent: explanationText,
            nodeType: 'explanation',
            subtopic: subtopicText,
            hasError,
            difficulty: explanationDifficulty,
            realWorldApplication: item.real_world_application,
            youtubeQuery: item.youtube_search_query
          },
          style: {
            background: hasError ? '#fee' : getNodeColor('explanation', explanationDifficulty),
            color: hasError ? '#c33' : (colorCodeBy === 'difficulty' ? '#fff' : '#555'),
            padding: '10px',
            borderRadius: '8px',
            border: hasError ? '1px solid #fcc' : '1px solid #ddd',
            fontSize: '12px',
            cursor: 'pointer',
            maxWidth: '300px',
            minHeight: '60px'
          }
        };
        nodes.push(explanationNode);

        // Edge: subtopic → explanation
        edges.push({
          id: `e-${subtopicId}-${explanationId}`,
          source: subtopicId,
          target: explanationId,
          type: ConnectionLineType.SmoothStep,
          animated: false,
          style: { stroke: '#999', strokeWidth: 1 }
        });
      }
    });

    return { nodes, edges };
  };

  const { nodes: initialNodes, edges: initialEdges } = createGraphData();

  const { nodes: layoutedNodes, edges: layoutedEdges } = getLayoutedElements(
    initialNodes,
    initialEdges
  );
  const [nodes, setNodes, onNodesChange] = useNodesState(layoutedNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(layoutedEdges);

  const proOptions = { hideAttribution: true };
  const onConnect = useCallback(
    (params) =>
      setEdges((eds) =>
        addEdge(
          { ...params, type: ConnectionLineType.SmoothStep, animated: true },
          eds
        )
      ),
    [setEdges]
  );
  const onLayout = useCallback(
    (direction) => {
      const { nodes: layoutedNodes, edges: layoutedEdges } =
        getLayoutedElements(nodes, edges, direction);

      setNodes([...layoutedNodes]);
      setEdges([...layoutedEdges]);
    },
    [nodes, edges, setEdges, setNodes]
  );

  // Handle node click to open modal
  const onNodeClick = useCallback((event, node) => {
    if (pathFindingMode) {
      // Path finding mode: select nodes for path
      setSelectedPathNodes(prev => {
        const newSelection = [...prev, node.id];
        if (newSelection.length === 2) {
          // Find path between two nodes
          const path = findShortestPath(newSelection[0], newSelection[1], edges);
          if (path) {
            // Highlight path
            setHighlightedNodes(new Set(path));
            alert(`Shortest path: ${path.length - 1} steps`);
          } else {
            alert('No path found between these nodes');
          }
          return [];
        }
        return newSelection;
      });
    } else {
      setSelectedNode(node);
      setIsModalOpen(true);

      // Add to breadcrumbs
      setBreadcrumbs(prev => [...prev, { id: node.id, label: node.data.fullContent || node.data.label }]);
    }
  }, [pathFindingMode, findShortestPath, edges]);

  // Close modal
  const closeModal = () => {
    console.log('closeModal called'); // Debug log
    setIsModalOpen(false);
    setSelectedNode(null);
  };

  // Search functionality
  const handleSearch = useCallback((query) => {
    setSearchQuery(query);

    if (!query.trim()) {
      setHighlightedNodes(new Set());
      // Reset all node styles
      setNodes((nds) =>
        nds.map((node) => ({
          ...node,
          style: {
            ...node.style,
            boxShadow: node.data.nodeType === 'topic'
              ? '0 4px 10px rgba(0,0,0,0.2)'
              : undefined,
            opacity: 1
          }
        }))
      );
      return;
    }

    const lowerQuery = query.toLowerCase();
    const matchingIds = new Set();

    nodes.forEach((node) => {
      const searchableText = [
        node.data.label,
        node.data.fullContent,
        node.data.subtopic
      ].filter(Boolean).join(' ').toLowerCase();

      if (searchableText.includes(lowerQuery)) {
        matchingIds.add(node.id);
      }
    });

    setHighlightedNodes(matchingIds);

    // Update node styles to highlight matches
    setNodes((nds) =>
      nds.map((node) => ({
        ...node,
        style: {
          ...node.style,
          boxShadow: matchingIds.has(node.id)
            ? '0 0 20px 5px rgba(255, 215, 0, 0.8)'
            : node.data.nodeType === 'topic'
              ? '0 4px 10px rgba(0,0,0,0.2)'
              : undefined,
          opacity: matchingIds.size > 0 ? (matchingIds.has(node.id) ? 1 : 0.3) : 1
        }
      }))
    );
  }, [nodes, setNodes]);

  // Filter functionality
  const toggleFilter = useCallback((filterType) => {
    setNodeFilters(prev => ({
      ...prev,
      [filterType]: !prev[filterType]
    }));
  }, []);

  // Apply filters to nodes
  useEffect(() => {
    setNodes((nds) =>
      nds.map((node) => ({
        ...node,
        hidden: !nodeFilters[node.data.nodeType]
      }))
    );

    // Also hide edges connected to hidden nodes
    setEdges((eds) =>
      eds.map((edge) => {
        const sourceNode = nodes.find(n => n.id === edge.source);
        const targetNode = nodes.find(n => n.id === edge.target);
        return {
          ...edge,
          hidden: !nodeFilters[sourceNode?.data?.nodeType] || !nodeFilters[targetNode?.data?.nodeType]
        };
      })
    );
  }, [nodeFilters, setNodes, setEdges, nodes]);

  // Export to PNG
  const exportToPNG = useCallback(() => {
    if (reactFlowWrapper.current) {
      toPng(reactFlowWrapper.current, {
        backgroundColor: '#ffffff',
        filter: (node) => {
          // Exclude controls and panels from export
          return !node?.classList?.contains('react-flow__controls') &&
            !node?.classList?.contains('react-flow__panel');
        }
      }).then((dataUrl) => {
        const link = document.createElement('a');
        link.download = `${topic.replace(/\s+/g, '_')}_concept_map.png`;
        link.href = dataUrl;
        link.click();
        analytics.trackTaskCompletion('export_graph_png', true);
      }).catch((error) => {
        console.error('Export to PNG failed:', error);
        analytics.trackError(error, { page: 'GraphPage', action: 'exportToPNG' });
      });
    }
  }, [topic]);

  // Export to PDF (Enhanced with error handling and quality settings)
  const exportToPDF = useCallback(() => {
    if (!reactFlowWrapper.current) {
      alert('Graph not ready for export. Please try again.');
      return;
    }

    // Show loading indicator
    const loadingMsg = document.createElement('div');
    loadingMsg.id = 'pdf-export-loading';
    loadingMsg.style.cssText = 'position:fixed;top:50%;left:50%;transform:translate(-50%,-50%);background:white;padding:30px;border-radius:10px;box-shadow:0 4px 20px rgba(0,0,0,0.3);z-index:10000;text-align:center;';
    loadingMsg.innerHTML = '<div style="font-size:20px;color:#667eea;margin-bottom:10px;">📄 Generating PDF...</div><div style="color:#999;">This may take a moment</div>';
    document.body.appendChild(loadingMsg);

    toPng(reactFlowWrapper.current, {
      backgroundColor: '#ffffff',
      pixelRatio: 2, // Higher quality
      filter: (node) => {
        return !node?.classList?.contains('react-flow__controls') &&
          !node?.classList?.contains('react-flow__panel') &&
          !node?.classList?.contains('react-flow__minimap');
      }
    }).then((dataUrl) => {
      const img = new Image();
      img.src = dataUrl;

      img.onload = () => {
        try {
          // Calculate dimensions to fit content
          const imgWidth = img.width;
          const imgHeight = img.height;
          const aspectRatio = imgWidth / imgHeight;

          // Determine orientation
          const orientation = aspectRatio > 1 ? 'landscape' : 'portrait';

          // Create PDF with A4 dimensions
          const pdf = new jsPDF({
            orientation: orientation,
            unit: 'mm',
            format: 'a4',
            compress: true
          });

          const pageWidth = pdf.internal.pageSize.getWidth();
          const pageHeight = pdf.internal.pageSize.getHeight();
          const margin = 10;
          const maxWidth = pageWidth - (margin * 2);
          const maxHeight = pageHeight - (margin * 2);

          // Calculate fit dimensions
          let finalWidth = maxWidth;
          let finalHeight = finalWidth / aspectRatio;

          if (finalHeight > maxHeight) {
            finalHeight = maxHeight;
            finalWidth = finalHeight * aspectRatio;
          }

          // Center the image
          const x = (pageWidth - finalWidth) / 2;
          const y = (pageHeight - finalHeight) / 2;

          // Add image to PDF
          pdf.addImage(dataUrl, 'PNG', x, y, finalWidth, finalHeight, undefined, 'FAST');

          // Add metadata
          pdf.setProperties({
            title: `${topic} - Concept Map`,
            subject: 'Concept Map Visualization',
            author: 'KNOWALLEDGE',
            keywords: 'concept map, learning, visualization',
            creator: 'KNOWALLEDGE App'
          });

          // Save PDF
          pdf.save(`${topic.replace(/\s+/g, '_')}_concept_map.pdf`);
          analytics.trackTaskCompletion('export_graph_pdf', true);

          // Remove loading indicator
          document.getElementById('pdf-export-loading')?.remove();

          // Show success message
          const successMsg = document.createElement('div');
          successMsg.style.cssText = 'position:fixed;top:20px;right:20px;background:#10b981;color:white;padding:15px 20px;border-radius:8px;box-shadow:0 4px 15px rgba(0,0,0,0.2);z-index:10000;animation:slideIn 0.3s ease-out;';
          successMsg.innerHTML = '✅ PDF exported successfully!';
          document.body.appendChild(successMsg);
          setTimeout(() => successMsg.remove(), 3000);
        } catch (error) {
          console.error('PDF generation error:', error);
          document.getElementById('pdf-export-loading')?.remove();
          alert('Failed to generate PDF. Please try PNG export instead.');
          analytics.trackError(error, { page: 'GraphPage', action: 'exportToPDF' });
        }
      };

      img.onerror = () => {
        document.getElementById('pdf-export-loading')?.remove();
        alert('Failed to load image for PDF export.');
        analytics.trackError(new Error('Image load failed'), { page: 'GraphPage', action: 'exportToPDF' });
      };
    }).catch((error) => {
      console.error('Export to PDF failed:', error);
      document.getElementById('pdf-export-loading')?.remove();
      alert('Failed to capture graph image. Try zooming out or using PNG export.');
      analytics.trackError(error, { page: 'GraphPage', action: 'exportToPDF' });
    });
  }, [topic]);

  // Export to JSON (NEW - Export complete graph data structure)
  const exportToJSON = useCallback(() => {
    try {
      // Create comprehensive JSON export
      const exportData = {
        metadata: {
          title: topic,
          exportDate: new Date().toISOString(),
          version: '1.0.0',
          generatedBy: 'KNOWALLEDGE',
          nodeCount: nodes.length,
          edgeCount: edges.length
        },
        topic: topic,
        subtopics: titles,
        nodes: nodes.map(node => ({
          id: node.id,
          type: node.data.nodeType,
          label: typeof node.data.label === 'string' ? node.data.label : node.data.fullContent,
          fullContent: node.data.fullContent,
          position: node.position,
          style: node.style,
          difficulty: node.data.difficulty,
          annotation: nodeAnnotations[node.id] || null
        })),
        edges: edges.map(edge => ({
          id: edge.id,
          source: edge.source,
          target: edge.target,
          type: edge.type,
          animated: edge.animated
        })),
        explanations: explanations.map((item, index) => ({
          id: `explanation-${index}`,
          subtopic: item.subtopic || titles[index],
          explanation: item.explanation,
          hasError: item.error || false
        })),
        settings: {
          visualizationMode,
          colorCodeBy,
          showIcons,
          filters: nodeFilters
        },
        annotations: nodeAnnotations
      };

      // Convert to JSON string with formatting
      const jsonString = JSON.stringify(exportData, null, 2);

      // Create blob and download
      const blob = new Blob([jsonString], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `${topic.replace(/\s+/g, '_')}_concept_map.json`;
      document.body.appendChild(link);
      document.body.removeChild(link);
      URL.revokeObjectURL(url);

      analytics.trackTaskCompletion('export_graph_json', true);

      // Show success message
      const successMsg = document.createElement('div');
      successMsg.style.cssText = 'position:fixed;top:20px;right:20px;background:#10b981;color:white;padding:15px 20px;border-radius:8px;box-shadow:0 4px 15px rgba(0,0,0,0.2);z-index:10000;animation:slideIn 0.3s ease-out;';
      successMsg.innerHTML = '✅ JSON exported successfully!';
      document.body.appendChild(successMsg);
      setTimeout(() => successMsg.remove(), 3000);
    } catch (error) {
      console.error('Export to JSON failed:', error);
      alert('Failed to export JSON. Please try again.');
      analytics.trackError(error, { page: 'GraphPage', action: 'exportToJSON' });
    }
  }, [topic, titles, nodes, edges, explanations, visualizationMode, colorCodeBy, showIcons, nodeFilters, nodeAnnotations]);

  // Import from JSON (NEW - Load saved graph data)
  const importFromJSON = useCallback((event) => {
    const file = event.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const importData = JSON.parse(e.target.result);

        // Validate imported data
        if (!importData.nodes || !importData.edges) {
          throw new Error('Invalid JSON format: missing nodes or edges');
        }

        // Restore settings
        if (importData.settings) {
          if (importData.settings.visualizationMode) setVisualizationMode(importData.settings.visualizationMode);
          if (importData.settings.colorCodeBy) setColorCodeBy(importData.settings.colorCodeBy);
          if (typeof importData.settings.showIcons === 'boolean') setShowIcons(importData.settings.showIcons);
          if (importData.settings.filters) setNodeFilters(importData.settings.filters);
        }

        // Restore annotations
        if (importData.annotations) {
          setNodeAnnotations(importData.annotations);
        }

        // Recreate nodes with imported data
        const importedNodes = importData.nodes.map(node => ({
          id: node.id,
          type: 'default',
          position: node.position,
          data: {
            label: node.label,
            fullContent: node.fullContent,
            nodeType: node.type,
            difficulty: node.difficulty
          },
          style: node.style
        }));

        // Recreate edges
        const importedEdges = importData.edges;

        setNodes(importedNodes);
        setEdges(importedEdges);

        analytics.trackTaskCompletion('import_graph_json', true);

        // Show success message
        const successMsg = document.createElement('div');
        successMsg.style.cssText = 'position:fixed;top:20px;right:20px;background:#10b981;color:white;padding:15px 20px;border-radius:8px;box-shadow:0 4px 15px rgba(0,0,0,0.2);z-index:10000;';
        successMsg.innerHTML = `✅ Loaded: ${importData.metadata?.title || 'Concept Map'}`;
        document.body.appendChild(successMsg);
        setTimeout(() => successMsg.remove(), 3000);
      } catch (error) {
        console.error('Import from JSON failed:', error);
        alert('Failed to import JSON: ' + error.message);
        analytics.trackError(error, { page: 'GraphPage', action: 'importFromJSON' });
      }
    };
    reader.readAsText(file);
  }, [setNodes, setEdges]);

  // Add comment to node (NEW - Collaboration feature)
  const addComment = useCallback((nodeId, comment) => {
    const newComment = {
      id: Date.now(),
      author: 'User', // TODO: Get from auth context
      text: comment,
      timestamp: new Date().toISOString(),
      nodeId: nodeId
    };

    setNodeComments(prev => ({
      ...prev,
      [nodeId]: [...(prev[nodeId] || []), newComment]
    }));

    analytics.trackTaskCompletion('add_node_comment', true);
  }, []);

  // Save version snapshot (NEW - Version control)
  const saveVersion = useCallback((versionName) => {
    const snapshot = {
      id: Date.now(),
      name: versionName || `Version ${versionHistory.length + 1}`,
      timestamp: new Date().toISOString(),
      nodes: [...nodes],
      edges: [...edges],
      settings: {
        visualizationMode,
        colorCodeBy,
        showIcons,
        filters: nodeFilters
      },
      annotations: { ...nodeAnnotations },
      comments: { ...nodeComments }
    };

    setVersionHistory(prev => [...prev, snapshot]);

    // Save to localStorage
    localStorage.setItem('graphVersionHistory', JSON.stringify([...versionHistory, snapshot]));

    // Show success message
    const successMsg = document.createElement('div');
    successMsg.style.cssText = 'position:fixed;top:20px;right:20px;background:#10b981;color:white;padding:15px 20px;border-radius:8px;box-shadow:0 4px 15px rgba(0,0,0,0.2);z-index:10000;';
    successMsg.innerHTML = `✅ Version saved: ${snapshot.name}`;
    document.body.appendChild(successMsg);
    setTimeout(() => successMsg.remove(), 3000);

    analytics.trackTaskCompletion('save_graph_version', true);
  }, [nodes, edges, visualizationMode, colorCodeBy, showIcons, nodeFilters, nodeAnnotations, nodeComments, versionHistory]);

  // Restore version (NEW - Version control)
  const restoreVersion = useCallback((versionId) => {
    const version = versionHistory.find(v => v.id === versionId);
    if (!version) return;

    // Restore graph state
    setNodes(version.nodes);
    setEdges(version.edges);

    // Restore settings
    if (version.settings) {
      setVisualizationMode(version.settings.visualizationMode);
      setColorCodeBy(version.settings.colorCodeBy);
      setShowIcons(version.settings.showIcons);
      setNodeFilters(version.settings.filters);
    }

    // Restore annotations and comments
    if (version.annotations) setNodeAnnotations(version.annotations);
    if (version.comments) setNodeComments(version.comments);

    // Show success message
    const successMsg = document.createElement('div');
    successMsg.style.cssText = 'position:fixed;top:20px;right:20px;background:#10b981;color:white;padding:15px 20px;border-radius:8px;box-shadow:0 4px 15px rgba(0,0,0,0.2);z-index:10000;';
    successMsg.innerHTML = `✅ Restored: ${version.name}`;
    document.body.appendChild(successMsg);
    setTimeout(() => successMsg.remove(), 3000);

    analytics.trackTaskCompletion('restore_graph_version', true);
  }, [versionHistory, setNodes, setEdges]);

  // Load version history from localStorage
  useEffect(() => {
    const savedVersions = localStorage.getItem('graphVersionHistory');
    if (savedVersions) {
      try {
        setVersionHistory(JSON.parse(savedVersions));
      } catch (e) {
        console.error('Failed to load version history:', e);
      }
    }
  }, []);

  // Dynamic Meta Tags Update (NEW - Social Media Preview)
  useEffect(() => {
    if (!topic) return;

    // Update page title
    document.title = `${topic} - KNOWALLEDGE Concept Map`;

    // Update or create meta tags
    const updateMetaTag = (property, content) => {
      let tag = document.querySelector(`meta[property="${property}"]`);
      if (!tag) {
        tag = document.createElement('meta');
        tag.setAttribute('property', property);
        document.head.appendChild(tag);
      }
      tag.setAttribute('content', content);
    };

    const updateNameTag = (name, content) => {
      let tag = document.querySelector(`meta[name="${name}"]`);
      if (!tag) {
        tag = document.createElement('meta');
        tag.setAttribute('name', name);
        document.head.appendChild(tag);
      }
      tag.setAttribute('content', content);
    };

    // Update Open Graph tags
    const description = `Interactive concept map for ${topic}. Explore ${nodes.length} nodes and ${edges.length} connections.`;

    updateMetaTag('og:title', `${topic} - KNOWALLEDGE Concept Map`);
    updateMetaTag('og:description', description);
    updateMetaTag('og:url', window.location.href);

    updateNameTag('description', description);
    updateNameTag('twitter:title', `${topic} - KNOWALLEDGE Concept Map`);
    updateNameTag('twitter:description', description);

    // Analytics
    analytics.trackPageLoad('GraphPage', { topic, nodeCount: nodes.length });
  }, [topic, nodes.length, edges.length]);

  // Social Features: Rate Graph (NEW)
  const rateGraph = useCallback((rating) => {
    if (userRating === rating) {
      // Remove rating
      setUserRating(0);
      const newTotal = totalRatings - 1;
      const newAvg = newTotal > 0 ? ((graphRating * totalRatings) - rating) / newTotal : 0;
      setGraphRating(newAvg);
      setTotalRatings(newTotal);

      // Store in localStorage
      localStorage.removeItem(`rating_${topic}`);

      // ✅ NEW: Sync to backend (null = remove)
      getGraphIdAndSync('rate', null);
    } else {
      // Add or update rating
      const previousRating = userRating;
      setUserRating(rating);

      let newAvg, newTotal;
      if (previousRating === 0) {
        // New rating
        newTotal = totalRatings + 1;
        newAvg = ((graphRating * totalRatings) + rating) / newTotal;
      } else {
        // Update existing rating
        newTotal = totalRatings;
        newAvg = ((graphRating * totalRatings) - previousRating + rating) / newTotal;
      }

      setGraphRating(newAvg);
      setTotalRatings(newTotal);

      // Store in localStorage
      localStorage.setItem(`rating_${topic}`, JSON.stringify({ rating, timestamp: Date.now() }));

      // ✅ NEW: Sync to backend
      getGraphIdAndSync('rate', rating);
    }

    analytics.trackTaskCompletion('rate_graph', true);
  }, [topic, userRating, graphRating, totalRatings, getGraphIdAndSync]);

  // Social Features: Like/Unlike Graph (NEW)
  const toggleLike = useCallback(() => {
    const newLiked = !userLiked;
    setUserLiked(newLiked);
    setLikes(prev => newLiked ? prev + 1 : prev - 1);

    // Store in localStorage
    if (newLiked) {
      localStorage.setItem(`liked_${topic}`, 'true');
    } else {
      localStorage.removeItem(`liked_${topic}`);
    }

    // ✅ NEW: Sync to backend
    getGraphIdAndSync('like', newLiked);

    analytics.trackTaskCompletion('like_graph', newLiked);
  }, [topic, userLiked, getGraphIdAndSync]);

  // Load social data from localStorage
  useEffect(() => {
    // Load rating
    const savedRating = localStorage.getItem(`rating_${topic}`);
    if (savedRating) {
      try {
        const { rating } = JSON.parse(savedRating);
        setUserRating(rating);
      } catch (e) {
        console.error('Failed to load rating:', e);
      }
    }

    // Load like status
    const liked = localStorage.getItem(`liked_${topic}`);
    if (liked === 'true') {
      setUserLiked(true);
    }

    // Load or initialize graph stats (in real app, this would come from backend)
    const savedStats = localStorage.getItem(`stats_${topic}`);
    if (savedStats) {
      try {
        const { rating, totalRatings: total, likes: likeCount } = JSON.parse(savedStats);
        setGraphRating(rating || 0);
        setTotalRatings(total || 0);
        setLikes(likeCount || 0);
      } catch (e) {
        console.error('Failed to load stats:', e);
      }
    }

    // ✅ NEW: Load stats from backend API
    const loadStatsFromBackend = async () => {
      try {
        // Get graph ID from topic
        const graphIdResponse = await fetch('http://localhost:5000/api/social/graphs/id', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ topic })
        });

        if (graphIdResponse.ok) {
          const { graph_id } = await graphIdResponse.json();

          // Fetch stats
          const statsResponse = await fetch(`http://localhost:5000/api/social/graphs/${graph_id}/stats`);

          if (statsResponse.ok) {
            const { stats, user_interaction } = await statsResponse.json();

            // Update state with backend data
            setLikes(stats.likes || 0);
            setGraphRating(stats.average_rating || 0);
            setTotalRatings(stats.total_ratings || 0);

            // Update user interaction
            setUserLiked(user_interaction.liked || false);
            setUserRating(user_interaction.rating || 0);
          }
        }
      } catch (error) {
        console.error('Failed to load stats from backend:', error);
        // Fallback to localStorage (already loaded above)
      }
    };

    // Try to load from backend (with fallback to localStorage)
    loadStatsFromBackend();
  }, [topic]);

  // ✅ NEW: Sync like to backend API
  const syncLikeToBackend = useCallback(async (liked, graphId) => {
    try {
      const response = await fetch(`http://localhost:5000/api/social/graphs/${graphId}/like`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ liked })
      });

      if (response.ok) {
        const data = await response.json();
        setLikes(data.likes || 0);
      }
    } catch (error) {
      console.error('Failed to sync like to backend:', error);
    }
  }, []);

  // ✅ NEW: Sync rating to backend API
  const syncRatingToBackend = useCallback(async (rating, graphId) => {
    try {
      const response = await fetch(`http://localhost:5000/api/social/graphs/${graphId}/rate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ rating })
      });

      if (response.ok) {
        const data = await response.json();
        setGraphRating(data.average_rating || 0);
        setTotalRatings(data.total_ratings || 0);
      }
    } catch (error) {
      console.error('Failed to sync rating to backend:', error);
    }
  }, []);

  // ✅ NEW: Get graph ID and sync with backend
  const getGraphIdAndSync = useCallback(async (action, value) => {
    try {
      const response = await fetch('http://localhost:5000/api/social/graphs/id', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ topic })
      });

      if (response.ok) {
        const { graph_id } = await response.json();

        if (action === 'like') {
          await syncLikeToBackend(value, graph_id);
        } else if (action === 'rate') {
          await syncRatingToBackend(value, graph_id);
        }
      }
    } catch (error) {
      console.error('Failed to get graph ID:', error);
    }
  }, [topic, syncLikeToBackend, syncRatingToBackend]);

  // Generate Embed Code (NEW - Embed Feature)
  const generateEmbedCode = useCallback(() => {
    // Export current graph to JSON
    const exportData = {
      topic,
      nodes: nodes.map(node => ({
        id: node.id,
        type: node.data.nodeType,
        fullContent: node.data.fullContent,
        position: node.position
      })),
      edges: edges.map(edge => ({
        id: edge.id,
        source: edge.source,
        target: edge.target,
        type: edge.type
      }))
    };

    // Create data URI
    const jsonString = JSON.stringify(exportData);
    const dataUri = btoa(encodeURIComponent(jsonString));

    // Generate embed URL (in production, this would point to a dedicated embed page)
    const embedUrl = `${window.location.origin}/embed?data=${dataUri}`;

    // Generate iframe code with multiple size options
    const iframeCode = `<!-- KNOWALLEDGE Embed - ${topic} -->
<iframe
  src="${embedUrl}"
  width="800"
  height="600"
  frameborder="0"
  style="border: 1px solid #ddd; border-radius: 8px;"
  allowfullscreen
  title="${topic} - Concept Map"
></iframe>

<!-- Responsive Option -->
<div style="position: relative; padding-bottom: 75%; height: 0; overflow: hidden;">
  <iframe
    src="${embedUrl}"
    style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; border: 1px solid #ddd; border-radius: 8px;"
    frameborder="0"
    allowfullscreen
    title="${topic} - Concept Map"
  ></iframe>
</div>`;

    setEmbedCode(iframeCode);
    setShowEmbedModal(true);

    analytics.trackTaskCompletion('generate_embed_code', true);
  }, [topic, nodes, edges]);

  // Copy embed code to clipboard
  const copyEmbedCode = useCallback(() => {
    navigator.clipboard.writeText(embedCode).then(() => {
      alert('✅ Embed code copied to clipboard!');
      analytics.trackTaskCompletion('copy_embed_code', true);
    }).catch((error) => {
      console.error('Failed to copy:', error);
      alert('❌ Failed to copy. Please select and copy manually.');
    });
  }, [embedCode]);

  // Keyboard navigation and body scroll lock
  useEffect(() => {
    // Prevent body scroll when modal is open
    if (isModalOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = 'unset';
    }

    const handleKeyPress = (e) => {
      // Ignore keyboard shortcuts if user is typing in input/textarea
      const isTyping = e.target.tagName === 'TEXTAREA' ||
        e.target.tagName === 'INPUT' ||
        e.target.isContentEditable;

      // If user is typing, don't handle ANY keyboard events here
      if (isTyping) {
        return; // Let the input/textarea handle all keys naturally
      }

      // Close modal with Escape (only when NOT typing)
      if (e.key === 'Escape' && isModalOpen) {
        closeModal();
        return;
      }

      // ✅ ACCESSIBILITY: Enhanced keyboard shortcuts

      // Help shortcut (H key)
      if ((e.key === 'h' || e.key === 'H') && !isModalOpen) {
        e.preventDefault();
        alert(getKeyboardShortcutsHelp());
        return;
      }

      // Node navigation (only when modal is closed)
      if (!isModalOpen) {
        const visibleNodes = getVisibleNodes();
        if (visibleNodes.length === 0) return;

        // Initialize selection on first navigation key
        if (selectedNodeIndex === -1 &&
          ['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight', 'Tab'].includes(e.key)) {
          e.preventDefault();
          setSelectedNodeIndex(0);
          setFocusedNodeId(visibleNodes[0].id);
          return;
        }

        // Arrow Down or Tab - Next node
        if (e.key === 'ArrowDown' || (e.key === 'Tab' && !e.shiftKey)) {
          e.preventDefault();
          const newIndex = (selectedNodeIndex + 1) % visibleNodes.length;
          setSelectedNodeIndex(newIndex);
          setFocusedNodeId(visibleNodes[newIndex].id);
          return;
        }

        // Arrow Up or Shift+Tab - Previous node
        if (e.key === 'ArrowUp' || (e.key === 'Tab' && e.shiftKey)) {
          e.preventDefault();
          const newIndex = selectedNodeIndex <= 0 ?
            visibleNodes.length - 1 : selectedNodeIndex - 1;
          setSelectedNodeIndex(newIndex);
          setFocusedNodeId(visibleNodes[newIndex].id);
          return;
        }

        // Arrow Left - Navigate to left adjacent node
        if (e.key === 'ArrowLeft') {
          e.preventDefault();
          navigateToAdjacentNode('left', visibleNodes);
          return;
        }

        // Arrow Right - Navigate to right adjacent node
        if (e.key === 'ArrowRight') {
          e.preventDefault();
          navigateToAdjacentNode('right', visibleNodes);
          return;
        }

        // Enter or Space - Open selected node modal
        if ((e.key === 'Enter' || e.key === ' ') && selectedNodeIndex >= 0) {
          e.preventDefault();
          const node = visibleNodes[selectedNodeIndex];
          onNodeClick(null, node);
          return;
        }

        // Number keys for filters
        if (e.key === '1') {
          e.preventDefault();
          setNodeFilters(prev => ({ ...prev, topic: !prev.topic }));
          return;
        }
        if (e.key === '2') {
          e.preventDefault();
          setNodeFilters(prev => ({ ...prev, subtopic: !prev.subtopic }));
          return;
        }
        if (e.key === '3') {
          e.preventDefault();
          setNodeFilters(prev => ({ ...prev, explanation: !prev.explanation }));
          return;
        }

        // Ctrl/Cmd + F for search focus
        if ((e.ctrlKey || e.metaKey) && e.key === 'f') {
          e.preventDefault();
          document.getElementById('graph-search-input')?.focus();
        }

        // Ctrl/Cmd + E for export menu
        if ((e.ctrlKey || e.metaKey) && e.key === 'e') {
          e.preventDefault();
          document.getElementById('export-button')?.click();
        }
      }
    };

    window.addEventListener('keydown', handleKeyPress);

    return () => {
      window.removeEventListener('keydown', handleKeyPress);
      // Restore body scroll on cleanup
      document.body.style.overflow = 'unset';
    };
  }, [isModalOpen, selectedNodeIndex, nodes, nodeFilters, getVisibleNodes, navigateToAdjacentNode, onNodeClick]);

  if (explanations.length > 0 && titles.length > 0) {
    return (
      <>
        {/* ✅ ACCESSIBILITY: Screen Reader Announcements */}
        <div
          role="status"
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
          {focusedNodeId && (() => {
            const node = nodes.find(n => n.id === focusedNodeId);
            if (!node) return '';
            return `Selected: ${node.data.label}, ${node.data.nodeType} node. Press Enter to view details.`;
          })()}
        </div>

        <div ref={reactFlowWrapper} style={{ width: "100vw", height: "100vh" }}>
          <ReactFlow
            nodes={nodes.map(node => ({
              ...node,
              style: getNodeStyle(node),
              ariaLabel: `${node.data.label} - ${node.data.nodeType} node`,
              data: {
                ...node.data,
                // Add accessibility data
                'aria-label': `${node.data.label} - ${node.data.nodeType}`,
                'role': 'button',
                'tabIndex': focusedNodeId === node.id ? 0 : -1
              }
            }))}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            onNodeClick={onNodeClick}
            proOptions={proOptions}
            connectionLineType={ConnectionLineType.SmoothStep}
            fitView
            // ✅ ACCESSIBILITY: ReactFlow attributes
            role="application"
            aria-label="Interactive concept map. Use arrow keys or Tab to navigate between nodes. Press Enter to view node details. Press H for keyboard shortcuts."
          >
            <Controls showInteractive={false} />
            <Background color="#aaa" gap={16} />
            <MiniMap
              nodeColor={(node) => {
                switch (node.data.nodeType) {
                  case 'topic': return '#667eea';
                  case 'subtopic': return '#90caf9';
                  case 'explanation': return '#e0e0e0';
                  default: return '#fff';
                }
              }}
              maskColor="rgba(0, 0, 0, 0.1)"
              style={{
                background: 'white',
                border: '2px solid #ddd',
                borderRadius: '8px'
              }}
            />

            {/* Search Bar Panel */}
            <Panel position="top-center">
              <div style={{
                background: 'white',
                padding: '15px 20px',
                borderRadius: '10px',
                boxShadow: '0 4px 15px rgba(0,0,0,0.15)',
                display: 'flex',
                alignItems: 'center',
                gap: '10px',
                minWidth: '400px'
              }}>
                <span style={{ fontSize: '18px' }}>🔍</span>
                <input
                  id="graph-search-input"
                  name="graphSearch"
                  type="text"
                  placeholder="Search nodes... (Ctrl+F)"
                  value={searchQuery}
                  onChange={(e) => handleSearch(e.target.value)}
                  style={{
                    flex: 1,
                    padding: '8px 12px',
                    border: '2px solid #ddd',
                    borderRadius: '5px',
                    fontSize: '14px',
                    outline: 'none'
                  }}
                  onFocus={(e) => e.target.style.borderColor = '#667eea'}
                  onBlur={(e) => e.target.style.borderColor = '#ddd'}
                />
                {searchQuery && (
                  <button
                    onClick={() => handleSearch('')}
                    style={{
                      background: 'none',
                      border: 'none',
                      cursor: 'pointer',
                      fontSize: '18px',
                      color: '#999'
                    }}
                    title="Clear search"
                  >
                    ✕
                  </button>
                )}
                {highlightedNodes.size > 0 && (
                  <span style={{
                    padding: '4px 10px',
                    background: '#667eea',
                    color: 'white',
                    borderRadius: '12px',
                    fontSize: '12px',
                    fontWeight: 'bold'
                  }}>
                    {highlightedNodes.size}
                  </span>
                )}
              </div>
            </Panel>

            {/* Layout Controls */}
            <Panel position="top-right">
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                <div style={{ display: 'flex', gap: '10px' }}>
                  <button
                    onClick={() => onLayout("TB")}
                    style={{
                      padding: '10px 20px',
                      background: '#667eea',
                      color: 'white',
                      border: 'none',
                      borderRadius: '5px',
                      cursor: 'pointer',
                      fontSize: '14px',
                      boxShadow: '0 2px 5px rgba(0,0,0,0.2)'
                    }}
                    onMouseOver={(e) => e.target.style.opacity = '0.9'}
                    onMouseOut={(e) => e.target.style.opacity = '1'}
                    title="Vertical layout"
                  >
                    ↓ Vertical
                  </button>
                  <button
                    onClick={() => onLayout("LR")}
                    style={{
                      padding: '10px 20px',
                      background: '#764ba2',
                      color: 'white',
                      border: 'none',
                      borderRadius: '5px',
                      cursor: 'pointer',
                      fontSize: '14px',
                      boxShadow: '0 2px 5px rgba(0,0,0,0.2)'
                    }}
                    onMouseOver={(e) => e.target.style.opacity = '0.9'}
                    onMouseOut={(e) => e.target.style.opacity = '1'}
                    title="Horizontal layout"
                  >
                    → Horizontal
                  </button>
                </div>

                {/* Export Buttons */}
                <div style={{ display: 'flex', gap: '10px', flexDirection: 'column' }}>
                  <div style={{ display: 'flex', gap: '10px' }}>
                    <button
                      id="export-button"
                      onClick={exportToPNG}
                      style={{
                        padding: '10px 20px',
                        background: '#10b981',
                        color: 'white',
                        border: 'none',
                        borderRadius: '5px',
                        cursor: 'pointer',
                        fontSize: '14px',
                        boxShadow: '0 2px 5px rgba(0,0,0,0.2)',
                        flex: 1
                      }}
                      onMouseOver={(e) => e.target.style.opacity = '0.9'}
                      onMouseOut={(e) => e.target.style.opacity = '1'}
                      title="Export as PNG (Ctrl+E)"
                    >
                      📥 PNG
                    </button>
                    <button
                      onClick={exportToPDF}
                      style={{
                        padding: '10px 20px',
                        background: '#f59e0b',
                        color: 'white',
                        border: 'none',
                        borderRadius: '5px',
                        cursor: 'pointer',
                        fontSize: '14px',
                        boxShadow: '0 2px 5px rgba(0,0,0,0.2)',
                        flex: 1
                      }}
                      onMouseOver={(e) => e.target.style.opacity = '0.9'}
                      onMouseOut={(e) => e.target.style.opacity = '1'}
                      title="Export as PDF"
                    >
                      📄 PDF
                    </button>
                  </div>

                  <div style={{ display: 'flex', gap: '10px' }}>
                    <button
                      onClick={exportToJSON}
                      style={{
                        padding: '10px 20px',
                        background: '#3b82f6',
                        color: 'white',
                        border: 'none',
                        borderRadius: '5px',
                        cursor: 'pointer',
                        fontSize: '14px',
                        boxShadow: '0 2px 5px rgba(0,0,0,0.2)',
                        flex: 1
                      }}
                      onMouseOver={(e) => e.target.style.opacity = '0.9'}
                      onMouseOut={(e) => e.target.style.opacity = '1'}
                      title="Export as JSON (Save/Share)"
                    >
                      💾 JSON
                    </button>
                    <label
                      htmlFor="import-json-input"
                      style={{
                        padding: '10px 20px',
                        background: '#6366f1',
                        color: 'white',
                        border: 'none',
                        borderRadius: '5px',
                        cursor: 'pointer',
                        fontSize: '14px',
                        boxShadow: '0 2px 5px rgba(0,0,0,0.2)',
                        flex: 1,
                        textAlign: 'center',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center'
                      }}
                      onMouseOver={(e) => e.target.style.opacity = '0.9'}
                      onMouseOut={(e) => e.target.style.opacity = '1'}
                      title="Import from JSON"
                    >
                      📂 Load
                      <input
                        id="import-json-input"
                        type="file"
                        accept=".json"
                        onChange={importFromJSON}
                        style={{ display: 'none' }}
                      />
                    </label>
                  </div>
                </div>

                {/* Share Button */}
                <button
                  onClick={generateShareableUrl}
                  style={{
                    padding: '10px 20px',
                    background: '#8b5cf6',
                    color: 'white',
                    border: 'none',
                    borderRadius: '5px',
                    cursor: 'pointer',
                    fontSize: '14px',
                    boxShadow: '0 2px 5px rgba(0,0,0,0.2)',
                    width: '100%'
                  }}
                  onMouseOver={(e) => e.target.style.opacity = '0.9'}
                  onMouseOut={(e) => e.target.style.opacity = '1'}
                  title="Generate shareable link"
                >
                  🔗 Share
                </button>

                {/* Collaboration Button (NEW) */}
                <button
                  onClick={() => setShowCollaborationPanel(!showCollaborationPanel)}
                  style={{
                    padding: '10px 20px',
                    background: showCollaborationPanel ? '#ec4899' : '#14b8a6',
                    color: 'white',
                    border: 'none',
                    borderRadius: '5px',
                    cursor: 'pointer',
                    fontSize: '14px',
                    boxShadow: '0 2px 5px rgba(0,0,0,0.2)',
                    width: '100%'
                  }}
                  onMouseOver={(e) => e.target.style.opacity = '0.9'}
                  onMouseOut={(e) => e.target.style.opacity = '1'}
                  title="Collaboration & Version Control"
                >
                  👥 Collaborate
                </button>

                {/* Embed Button (NEW) */}
                <button
                  onClick={generateEmbedCode}
                  style={{
                    padding: '10px 20px',
                    background: '#f59e0b',
                    color: 'white',
                    border: 'none',
                    borderRadius: '5px',
                    cursor: 'pointer',
                    fontSize: '14px',
                    boxShadow: '0 2px 5px rgba(0,0,0,0.2)',
                    width: '100%'
                  }}
                  onMouseOver={(e) => e.target.style.opacity = '0.9'}
                  onMouseOut={(e) => e.target.style.opacity = '1'}
                  title="Generate embed code for websites/blogs"
                >
                  📌 Embed
                </button>

                {/* Social Features */}
                <div style={{
                  marginTop: '15px',
                  paddingTop: '15px',
                  borderTop: '1px solid #ddd'
                }}>
                  <div style={{
                    fontSize: '13px',
                    color: '#666',
                    marginBottom: '10px',
                    fontWeight: 'bold'
                  }}>
                    Community
                  </div>

                  {/* Like Button */}
                  <button
                    onClick={toggleLike}
                    style={{
                      padding: '8px 15px',
                      background: userLiked ? '#ef4444' : '#f3f4f6',
                      color: userLiked ? 'white' : '#374151',
                      border: '1px solid #d1d5db',
                      borderRadius: '5px',
                      cursor: 'pointer',
                      fontSize: '13px',
                      width: '100%',
                      marginBottom: '8px',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      gap: '8px'
                    }}
                    onMouseOver={(e) => e.target.style.opacity = '0.9'}
                    onMouseOut={(e) => e.target.style.opacity = '1'}
                    title={userLiked ? 'Unlike this graph' : 'Like this graph'}
                  >
                    {userLiked ? '❤️' : '🤍'} {likes} {likes === 1 ? 'Like' : 'Likes'}
                  </button>

                  {/* Rating Display */}
                  <div style={{
                    padding: '10px',
                    background: '#f9fafb',
                    borderRadius: '5px',
                    border: '1px solid #e5e7eb'
                  }}>
                    <div style={{
                      fontSize: '12px',
                      color: '#6b7280',
                      marginBottom: '5px'
                    }}>
                      Rate this concept map:
                    </div>
                    <div style={{
                      display: 'flex',
                      gap: '5px',
                      justifyContent: 'center',
                      marginBottom: '5px'
                    }}>
                      {[1, 2, 3, 4, 5].map(star => (
                        <button
                          key={star}
                          onClick={() => rateGraph(star)}
                          style={{
                            background: 'none',
                            border: 'none',
                            cursor: 'pointer',
                            fontSize: '20px',
                            padding: '2px',
                            transition: 'transform 0.2s'
                          }}
                          onMouseOver={(e) => e.target.style.transform = 'scale(1.2)'}
                          onMouseOut={(e) => e.target.style.transform = 'scale(1)'}
                          title={`Rate ${star} star${star > 1 ? 's' : ''}`}
                        >
                          {star <= userRating ? '⭐' : '☆'}
                        </button>
                      ))}
                    </div>
                    {totalRatings > 0 && (
                      <div style={{
                        fontSize: '11px',
                        color: '#9ca3af',
                        textAlign: 'center'
                      }}>
                        {graphRating.toFixed(1)} avg ({totalRatings} {totalRatings === 1 ? 'rating' : 'ratings'})
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </Panel>

            {/* Advanced Options Panel */}
            <Panel position="top-left">
              <div style={{
                background: 'white',
                padding: '15px',
                borderRadius: '8px',
                boxShadow: '0 2px 10px rgba(0,0,0,0.1)',
                fontSize: '13px',
                minWidth: '200px'
              }}>
                <strong style={{ display: 'block', marginBottom: '10px', color: '#667eea' }}>
                  ⚙️ Advanced Options
                </strong>

                {/* Color Coding */}
                <div style={{ marginBottom: '12px' }}>
                  <label htmlFor="colorCodeBySelect" style={{ display: 'block', marginBottom: '5px', fontSize: '12px' }}>
                    Color-code by:
                  </label>
                  <select
                    id="colorCodeBySelect"
                    name="colorCodeBy"
                    value={colorCodeBy}
                    onChange={(e) => setColorCodeBy(e.target.value)}
                    style={{
                      width: '100%',
                      padding: '6px',
                      borderRadius: '4px',
                      border: '1px solid #ddd',
                      fontSize: '12px'
                    }}
                    aria-label="Select color coding method"
                  >
                    <option value="type">Node Type</option>
                    <option value="difficulty">Difficulty</option>
                  </select>
                </div>

                {/* Visualization Mode */}
                <div style={{ marginBottom: '12px' }}>
                  <label htmlFor="visualizationModeSelect" style={{ display: 'block', marginBottom: '5px', fontSize: '12px' }}>
                    Layout Mode:
                  </label>
                  <select
                    id="visualizationModeSelect"
                    name="visualizationMode"
                    value={visualizationMode}
                    onChange={(e) => setVisualizationMode(e.target.value)}
                    style={{
                      width: '100%',
                      padding: '6px',
                      borderRadius: '4px',
                      border: '1px solid #ddd',
                      fontSize: '12px'
                    }}
                    aria-label="Select graph layout mode"
                  >
                    <option value="hierarchical">Hierarchical</option>
                    <option value="tree">Tree</option>
                    <option value="radial">Radial</option>
                  </select>
                </div>

                {/* Toggle Icons */}
                <label htmlFor="showIconsCheckbox" style={{ display: 'flex', alignItems: 'center', cursor: 'pointer', marginBottom: '8px' }}>
                  <input
                    id="showIconsCheckbox"
                    name="showIcons"
                    type="checkbox"
                    checked={showIcons}
                    onChange={(e) => setShowIcons(e.target.checked)}
                    style={{ marginRight: '8px', cursor: 'pointer' }}
                    aria-label="Show node icons"
                  />
                  <span style={{ fontSize: '12px' }}>Show node icons</span>
                </label>

                {/* Path Finding Mode */}
                <label htmlFor="pathFindingCheckbox" style={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }}>
                  <input
                    id="pathFindingCheckbox"
                    name="pathFindingMode"
                    type="checkbox"
                    checked={pathFindingMode}
                    onChange={(e) => setPathFindingMode(e.target.checked)}
                    style={{ marginRight: '8px', cursor: 'pointer' }}
                    aria-label="Find shortest path mode"
                  />
                  <span style={{ fontSize: '12px' }}>🔍 Find shortest path</span>
                </label>
                {pathFindingMode && (
                  <div style={{
                    marginTop: '8px',
                    padding: '8px',
                    background: '#fff3cd',
                    borderRadius: '4px',
                    fontSize: '11px',
                    color: '#856404'
                  }}>
                    Click two nodes to find path
                  </div>
                )}
              </div>
            </Panel>

            {/* Filter Panel */}
            <Panel position="bottom-left">
              <div style={{
                background: 'white',
                padding: '15px',
                borderRadius: '8px',
                boxShadow: '0 2px 10px rgba(0,0,0,0.1)',
                fontSize: '14px'
              }}>
                <strong style={{ display: 'block', marginBottom: '10px', color: '#667eea' }}>
                  🎯 Filter Nodes
                </strong>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  <label htmlFor="filterTopic" style={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }}>
                    <input
                      id="filterTopic"
                      name="filterTopic"
                      type="checkbox"
                      checked={nodeFilters.topic}
                      onChange={() => toggleFilter('topic')}
                      style={{ marginRight: '8px', cursor: 'pointer' }}
                      aria-label="Show topic nodes"
                    />
                    <span style={{ color: nodeFilters.topic ? '#333' : '#999' }}>
                      📌 Topic
                    </span>
                  </label>
                  <label htmlFor="filterSubtopic" style={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }}>
                    <input
                      id="filterSubtopic"
                      name="filterSubtopic"
                      type="checkbox"
                      checked={nodeFilters.subtopic}
                      onChange={() => toggleFilter('subtopic')}
                      style={{ marginRight: '8px', cursor: 'pointer' }}
                      aria-label="Show subtopic nodes"
                    />
                    <span style={{ color: nodeFilters.subtopic ? '#333' : '#999' }}>
                      📋 Subtopics
                    </span>
                  </label>
                  <label htmlFor="filterExplanation" style={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }}>
                    <input
                      id="filterExplanation"
                      name="filterExplanation"
                      type="checkbox"
                      checked={nodeFilters.explanation}
                      onChange={() => toggleFilter('explanation')}
                      style={{ marginRight: '8px', cursor: 'pointer' }}
                      aria-label="Show explanation nodes"
                    />
                    <span style={{ color: nodeFilters.explanation ? '#333' : '#999' }}>
                      💬 Explanations
                    </span>
                  </label>
                </div>
              </div>
            </Panel>

            {/* Tips Panel */}
            <Panel position="bottom-right">
              <div style={{
                background: 'white',
                padding: '15px',
                borderRadius: '8px',
                boxShadow: '0 2px 10px rgba(0,0,0,0.1)',
                fontSize: '13px',
                maxWidth: '280px'
              }}>
                <strong style={{ color: '#667eea' }}>⌨️ Keyboard Shortcuts:</strong>
                <div style={{ marginTop: '10px', color: '#666', lineHeight: '1.8' }}>
                  <div><kbd style={kbdStyle}>↑↓←→</kbd> Navigate nodes</div>
                  <div><kbd style={kbdStyle}>Tab</kbd> Next node</div>
                  <div><kbd style={kbdStyle}>Enter</kbd> Open details</div>
                  <div><kbd style={kbdStyle}>Ctrl+F</kbd> Search</div>
                  <div><kbd style={kbdStyle}>Ctrl+E</kbd> Export</div>
                  <div><kbd style={kbdStyle}>H</kbd> Show all shortcuts</div>
                  <div><kbd style={kbdStyle}>Esc</kbd> Close modal</div>
                  <div><kbd style={kbdStyle}>1-3</kbd> Toggle filters</div>
                  <div style={{ marginTop: '8px', paddingTop: '8px', borderTop: '1px solid #eee' }}>
                    💡 Click nodes to view details
                  </div>
                </div>
              </div>
            </Panel>

            {/* Collaboration Panel (NEW) */}
            {showCollaborationPanel && (
              <Panel position="bottom-center">
                <div style={{
                  background: 'white',
                  padding: '20px',
                  borderRadius: '12px',
                  boxShadow: '0 4px 20px rgba(0,0,0,0.2)',
                  minWidth: '500px',
                  maxWidth: '700px',
                  maxHeight: '400px',
                  overflow: 'auto'
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '15px' }}>
                    <strong style={{ color: '#667eea', fontSize: '16px' }}>
                      👥 Collaboration & Versions
                    </strong>
                    <button
                      onClick={() => setShowCollaborationPanel(false)}
                      style={{
                        background: 'none',
                        border: 'none',
                        cursor: 'pointer',
                        fontSize: '20px',
                        color: '#999'
                      }}
                      title="Close panel"
                    >
                      ✕
                    </button>
                  </div>

                  {/* Version Control Section */}
                  <div style={{ marginBottom: '20px', paddingBottom: '20px', borderBottom: '1px solid #eee' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
                      <strong style={{ fontSize: '14px', color: '#333' }}>📚 Version History</strong>
                      <button
                        onClick={() => {
                          const versionName = prompt('Enter version name (optional):');
                          saveVersion(versionName || undefined);
                        }}
                        style={{
                          padding: '6px 12px',
                          background: '#10b981',
                          color: 'white',
                          border: 'none',
                          borderRadius: '5px',
                          cursor: 'pointer',
                          fontSize: '12px'
                        }}
                      >
                        💾 Save Version
                      </button>
                    </div>

                    {versionHistory.length === 0 ? (
                      <div style={{ fontSize: '12px', color: '#999', padding: '10px', background: '#f9f9f9', borderRadius: '5px' }}>
                        No versions saved yet. Save your current work to create a snapshot.
                      </div>
                    ) : (
                      <div style={{ maxHeight: '150px', overflow: 'auto' }}>
                        {versionHistory.slice().reverse().map((version) => (
                          <div
                            key={version.id}
                            style={{
                              padding: '10px',
                              background: '#f9f9f9',
                              borderRadius: '5px',
                              marginBottom: '8px',
                              display: 'flex',
                              justifyContent: 'space-between',
                              alignItems: 'center',
                              fontSize: '12px'
                            }}
                          >
                            <div>
                              <div style={{ fontWeight: 'bold', color: '#333' }}>{version.name}</div>
                              <div style={{ color: '#999', fontSize: '11px' }}>
                                {new Date(version.timestamp).toLocaleString()}
                              </div>
                              <div style={{ color: '#666', fontSize: '11px' }}>
                                {version.nodes.length} nodes, {version.edges.length} edges
                              </div>
                            </div>
                            <button
                              onClick={() => {
                                if (window.confirm(`Restore version: ${version.name}?`)) {
                                  restoreVersion(version.id);
                                }
                              }}
                              style={{
                                padding: '5px 10px',
                                background: '#667eea',
                                color: 'white',
                                border: 'none',
                                borderRadius: '4px',
                                cursor: 'pointer',
                                fontSize: '11px'
                              }}
                            >
                              ↻ Restore
                            </button>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* Comments Section */}
                  <div>
                    <strong style={{ fontSize: '14px', color: '#333', display: 'block', marginBottom: '10px' }}>
                      💬 Recent Comments
                    </strong>

                    {Object.keys(nodeComments).length === 0 ? (
                      <div style={{ fontSize: '12px', color: '#999', padding: '10px', background: '#f9f9f9', borderRadius: '5px' }}>
                        No comments yet. Click nodes to add comments and collaborate!
                      </div>
                    ) : (
                      <div style={{ maxHeight: '150px', overflow: 'auto' }}>
                        {Object.entries(nodeComments)
                          .flatMap(([nodeId, comments]) =>
                            comments.map(comment => ({ ...comment, nodeId }))
                          )
                          .sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp))
                          .slice(0, 5)
                          .map((comment) => (
                            <div
                              key={comment.id}
                              style={{
                                padding: '10px',
                                background: '#f0f7ff',
                                borderRadius: '5px',
                                marginBottom: '8px',
                                fontSize: '12px'
                              }}
                            >
                              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '5px' }}>
                                <strong style={{ color: '#667eea' }}>{comment.author}</strong>
                                <span style={{ color: '#999', fontSize: '11px' }}>
                                  {new Date(comment.timestamp).toLocaleTimeString()}
                                </span>
                              </div>
                              <div style={{ color: '#333', marginBottom: '3px' }}>{comment.text}</div>
                              <div style={{ color: '#999', fontSize: '11px' }}>
                                On node: {comment.nodeId}
                              </div>
                            </div>
                          ))}
                      </div>
                    )}
                  </div>
                </div>
              </Panel>
            )}
          </ReactFlow>
        </div>

        {/* Breadcrumb Navigation */}
        {breadcrumbs.length > 0 && (
          <div style={{
            position: 'fixed',
            bottom: '20px',
            left: '50%',
            transform: 'translateX(-50%)',
            background: 'white',
            padding: '10px 20px',
            borderRadius: '20px',
            boxShadow: '0 4px 15px rgba(0,0,0,0.2)',
            display: 'flex',
            alignItems: 'center',
            gap: '10px',
            maxWidth: '80%',
            overflow: 'auto',
            zIndex: 10
          }}>
            <span style={{ fontSize: '12px', fontWeight: 'bold', color: '#667eea' }}>
              Navigation:
            </span>
            {breadcrumbs.slice(-5).map((crumb, index) => (
              <span key={index} style={{ fontSize: '12px', color: '#666' }}>
                {index > 0 && ' → '}
                {typeof crumb.label === 'string' ? truncateText(crumb.label, 30) : 'Node'}
              </span>
            ))}
            <button
              onClick={() => setBreadcrumbs([])}
              style={{
                background: '#f0f0f0',
                border: 'none',
                borderRadius: '50%',
                width: '20px',
                height: '20px',
                cursor: 'pointer',
                fontSize: '12px'
              }}
              title="Clear breadcrumbs"
            >
              ✕
            </button>
          </div>
        )}

        {/* Tutorial Overlay */}
        {showTutorial && (
          <div style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: 'rgba(0,0,0,0.8)',
            zIndex: 1000,
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            padding: '20px'
          }}>
            <div style={{
              background: 'white',
              borderRadius: '15px',
              padding: '40px',
              maxWidth: '600px',
              maxHeight: '80vh',
              overflow: 'auto'
            }}>
              <h2 style={{ color: '#667eea', marginTop: 0 }}>🎓 Welcome to Concept Map!</h2>

              <div style={{ lineHeight: '1.8', color: '#333' }}>
                <h3>✨ Quick Tour:</h3>

                <p><strong>🔍 Search:</strong> Use the search bar at the top to find specific content</p>

                <p><strong>🎯 Filter:</strong> Toggle node types in the bottom-left panel</p>

                <p><strong>📥 Export:</strong> Download your map as PNG or PDF (top-right)</p>

                <p><strong>🔗 Share:</strong> Generate a shareable link to collaborate</p>

                <p><strong>⚙️ Customize:</strong> Change colors, layout, and visualization mode (top-left)</p>

                <p><strong>🗺️ Navigate:</strong> Use the mini-map (bottom-right) for quick navigation</p>

                <p><strong>💬 Interact:</strong> Click any node to see full details</p>

                <p><strong>⌨️ Shortcuts:</strong></p>
                <ul style={{ marginLeft: '20px' }}>
                  <li><kbd style={kbdStyle}>Ctrl+F</kbd> Focus search</li>
                  <li><kbd style={kbdStyle}>Ctrl+E</kbd> Export</li>
                  <li><kbd style={kbdStyle}>Esc</kbd> Close modal</li>
                </ul>

                <p><strong>🧭 Pro Tips:</strong></p>
                <ul style={{ marginLeft: '20px' }}>
                  <li>📦 Click subtopics to collapse/expand explanations</li>
                  <li>🔍 Enable "Find shortest path" to connect nodes</li>
                  <li>🎨 Color-code by difficulty to see complexity</li>
                  <li>📝 Hover nodes to see tooltips</li>
                </ul>
              </div>

              <button
                onClick={() => setShowTutorial(false)}
                style={{
                  marginTop: '20px',
                  padding: '12px 30px',
                  background: '#667eea',
                  color: 'white',
                  border: 'none',
                  borderRadius: '8px',
                  fontSize: '16px',
                  cursor: 'pointer',
                  width: '100%',
                  fontWeight: 'bold'
                }}
                onMouseOver={(e) => e.target.style.opacity = '0.9'}
                onMouseOut={(e) => e.target.style.opacity = '1'}
              >
                Got it! Let's explore 🚀
              </button>

              <button
                onClick={() => {
                  setShowTutorial(false);
                  localStorage.setItem('hasVisitedGraph', 'false'); // Reset for next time
                }}
                style={{
                  marginTop: '10px',
                  padding: '8px',
                  background: 'transparent',
                  color: '#999',
                  border: 'none',
                  cursor: 'pointer',
                  fontSize: '12px',
                  width: '100%'
                }}
              >
                Show this tutorial again next time
              </button>
            </div>
          </div>
        )}

        {/* Quiz Modal */}
        <QuizModal
          isOpen={isQuizOpen}
          onClose={() => setIsQuizOpen(false)}
          topic={topic}
          subtopic={currentQuizSubtopic}
          educationLevel="undergradLevel" // Default, could be dynamic
        />

        {/* Node Modal */}
        {isModalOpen && selectedNode && (
          <NodeModal
            node={selectedNode}
            onClose={closeModal}
            nodeAnnotations={nodeAnnotations}
            addAnnotation={addAnnotation}
            nodeComments={nodeComments}
            addComment={(nodeId, text) => {
              const comment = {
                id: Date.now(),
                author: 'You', // In real app, use user name
                text,
                timestamp: new Date().toISOString()
              };
              setNodeComments(prev => ({
                ...prev,
                [nodeId]: [...(prev[nodeId] || []), comment]
              }));
            }}
            onTakeQuiz={handleTakeQuiz}
            fontSize={settings.fontSize}
          />
        )}

        {/* Daily Goal Tracker */}
        <div style={{
          position: 'fixed',
          bottom: '20px',
          left: '20px',
          background: 'rgba(0,0,0,0.7)',
          color: 'white',
          padding: '10px 15px',
          borderRadius: '30px',
          fontSize: '14px',
          zIndex: 1000,
          display: 'flex',
          alignItems: 'center',
          gap: '10px',
          backdropFilter: 'blur(5px)'
        }}>
          <span>🎯 Daily Goal: {Math.floor(dailyProgress)} / {settings.dailyGoal} min</span>
          <div style={{
            width: '50px',
            height: '6px',
            background: 'rgba(255,255,255,0.2)',
            borderRadius: '3px',
            overflow: 'hidden'
          }}>
            <div style={{
              width: `${Math.min((dailyProgress / settings.dailyGoal) * 100, 100)}%`,
              height: '100%',
              background: '#4facfe'
            }} />
          </div>
        </div>

        {/* Embed Code Modal (NEW) */}
        {showEmbedModal && (
          <div
            onClick={() => setShowEmbedModal(false)}
            style={{
              position: 'fixed',
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              background: 'rgba(0, 0, 0, 0.7)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              zIndex: 10000,
              padding: '20px'
            }}
          >
            <div
              onClick={(e) => e.stopPropagation()}
              style={{
                background: 'white',
                borderRadius: '12px',
                padding: '30px',
                maxWidth: '700px',
                width: '100%',
                maxHeight: '90vh',
                overflow: 'auto',
                boxShadow: '0 20px 60px rgba(0,0,0,0.3)'
              }}
            >
              {/* Header */}
              <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                marginBottom: '20px'
              }}>
                <h2 style={{
                  margin: 0,
                  color: '#667eea',
                  fontSize: '24px'
                }}>
                  📌 Embed Code Generator
                </h2>
                <button
                  onClick={() => setShowEmbedModal(false)}
                  style={{
                    background: 'none',
                    border: 'none',
                    fontSize: '28px',
                    cursor: 'pointer',
                    color: '#999',
                    padding: '0',
                    lineHeight: '1'
                  }}
                  title="Close"
                >
                  ✕
                </button>
              </div>

              {/* Description */}
              <div style={{
                marginBottom: '20px',
                padding: '15px',
                background: '#f0f7ff',
                borderRadius: '8px',
                border: '1px solid #dbeafe'
              }}>
                <p style={{ margin: '0 0 10px 0', fontSize: '14px', color: '#334155' }}>
                  <strong>📚 Perfect for educators and content creators!</strong>
                </p>
                <p style={{ margin: 0, fontSize: '13px', color: '#64748b' }}>
                  Copy the code below to embed this interactive concept map in your:
                </p>
                <ul style={{
                  margin: '8px 0 0 0',
                  paddingLeft: '20px',
                  fontSize: '13px',
                  color: '#64748b'
                }}>
                  <li>Course materials & LMS platforms</li>
                  <li>Blog posts & articles</li>
                  <li>Educational websites</li>
                  <li>Documentation pages</li>
                </ul>
              </div>

              {/* Embed Code */}
              <div style={{ marginBottom: '15px' }}>
                <label style={{
                  display: 'block',
                  marginBottom: '8px',
                  fontSize: '14px',
                  fontWeight: 'bold',
                  color: '#374151'
                }}>
                  Embed Code:
                </label>
                <textarea
                  value={embedCode}
                  readOnly
                  style={{
                    width: '100%',
                    minHeight: '250px',
                    padding: '15px',
                    borderRadius: '8px',
                    border: '2px solid #e5e7eb',
                    fontSize: '12px',
                    fontFamily: 'monospace',
                    background: '#f9fafb',
                    resize: 'vertical',
                    lineHeight: '1.5'
                  }}
                  onClick={(e) => e.target.select()}
                />
                <div style={{
                  fontSize: '11px',
                  color: '#9ca3af',
                  marginTop: '5px'
                }}>
                  💡 Tip: Click the code to select all, or use the copy button below
                </div>
              </div>

              {/* Size Options Info */}
              <div style={{
                marginBottom: '20px',
                padding: '12px',
                background: '#fef3c7',
                borderRadius: '8px',
                border: '1px solid #fde047'
              }}>
                <p style={{
                  margin: '0 0 8px 0',
                  fontSize: '13px',
                  color: '#78350f',
                  fontWeight: 'bold'
                }}>
                  📐 Two embedding options included:
                </p>
                <ol style={{
                  margin: 0,
                  paddingLeft: '20px',
                  fontSize: '12px',
                  color: '#92400e'
                }}>
                  <li><strong>Fixed Size</strong>: 800×600px iframe (easy to use)</li>
                  <li><strong>Responsive</strong>: Scales to container width (recommended for modern sites)</li>
                </ol>
              </div>

              {/* Action Buttons */}
              <div style={{
                display: 'flex',
                gap: '10px',
                marginTop: '20px'
              }}>
                <button
                  onClick={copyEmbedCode}
                  style={{
                    flex: 1,
                    padding: '12px 20px',
                    background: '#667eea',
                    color: 'white',
                    border: 'none',
                    borderRadius: '8px',
                    cursor: 'pointer',
                    fontSize: '14px',
                    fontWeight: 'bold',
                    boxShadow: '0 4px 15px rgba(102, 126, 234, 0.3)'
                  }}
                  onMouseOver={(e) => e.target.style.background = '#5568d3'}
                  onMouseOut={(e) => e.target.style.background = '#667eea'}
                >
                  📋 Copy to Clipboard
                </button>
                <button
                  onClick={() => setShowEmbedModal(false)}
                  style={{
                    padding: '12px 20px',
                    background: '#f3f4f6',
                    color: '#374151',
                    border: '1px solid #d1d5db',
                    borderRadius: '8px',
                    cursor: 'pointer',
                    fontSize: '14px'
                  }}
                  onMouseOver={(e) => e.target.style.background = '#e5e7eb'}
                  onMouseOut={(e) => e.target.style.background = '#f3f4f6'}
                >
                  Close
                </button>
              </div>

              {/* Preview Info */}
              <div style={{
                marginTop: '20px',
                padding: '12px',
                background: '#f0fdf4',
                borderRadius: '8px',
                border: '1px solid #bbf7d0',
                fontSize: '12px',
                color: '#166534'
              }}>
                <p style={{ margin: '0 0 5px 0', fontWeight: 'bold' }}>
                  ✅ What viewers will see:
                </p>
                <ul style={{ margin: 0, paddingLeft: '20px' }}>
                  <li>Interactive, zoomable concept map</li>
                  <li>Clickable nodes with full content</li>
                  <li>All connections and relationships</li>
                  <li>Current visualization settings</li>
                </ul>
              </div>
            </div>
          </div>
        )}
      </>
    );
  }
  else {
    return (
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        height: '100vh',
        flexDirection: 'column'
      }}>
        <h1>No data available</h1>
        <button
          onClick={() => window.location.href = '/'}
          style={{
            marginTop: '20px',
            padding: '12px 24px',
            background: '#667eea',
            color: 'white',
            border: 'none',
            borderRadius: '8px',
            fontSize: '16px',
            cursor: 'pointer'
          }}
        >
          Go Home
        </button>
      </div>
    );
  }
};

export default GraphPage;
