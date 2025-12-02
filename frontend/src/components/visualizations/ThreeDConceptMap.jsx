import React, { useState, useEffect, useRef } from 'react';
import './ThreeDConceptMap.css';

const ThreeDConceptMap = ({ 
  topicData, 
  completedNodes, 
  recommendedNodes, 
  onNodeClick,
  highlightMode 
}) => {
  const [nodes, setNodes] = useState([]);
  const [selectedNode, setSelectedNode] = useState(null);
  const [rotation, setRotation] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  const containerRef = useRef(null);

  useEffect(() => {
    if (topicData && topicData.concepts) {
      const positioned = positionNodesIn3D(topicData.concepts);
      setNodes(positioned);
    }
  }, [topicData]);

  const positionNodesIn3D = (concepts) => {
    // Position nodes in 3D space based on relationships and difficulty
    const radius = 300;
    
    return concepts.map((concept, index) => {
      const angle = (index / concepts.length) * Math.PI * 2;
      const difficulty = concept.difficulty || 'intermediate';
      
      // Z-axis based on difficulty (depth)
      let z = 0;
      if (difficulty === 'beginner') z = -100;
      else if (difficulty === 'advanced') z = 100;
      
      // Circular arrangement in X-Y plane
      const x = Math.cos(angle) * radius;
      const y = Math.sin(angle) * radius;

      return {
        id: concept.id || `concept-${index}`,
        title: concept.name || concept.title,
        description: concept.description || '',
        difficulty: difficulty,
        x, y, z,
        connections: concept.prerequisites || []
      };
    });
  };

  const getNodeStatus = (node) => {
    if (completedNodes.has(node.id)) return 'completed';
    if (recommendedNodes.has(node.id)) return 'recommended';
    return 'pending';
  };

  const project3DTo2D = (x, y, z) => {
    // Simple perspective projection
    const perspective = 1000;
    const rotatedX = x * Math.cos(rotation.y) - z * Math.sin(rotation.y);
    const rotatedZ = x * Math.sin(rotation.y) + z * Math.cos(rotation.y);
    const rotatedY = y * Math.cos(rotation.x) - rotatedZ * Math.sin(rotation.x);
    const finalZ = y * Math.sin(rotation.x) + rotatedZ * Math.cos(rotation.x);

    const scale = perspective / (perspective + finalZ);
    
    return {
      x: rotatedX * scale,
      y: rotatedY * scale,
      scale: scale,
      z: finalZ
    };
  };

  const handleMouseDown = (e) => {
    setIsDragging(true);
    setDragStart({ x: e.clientX, y: e.clientY });
  };

  const handleMouseMove = (e) => {
    if (!isDragging) return;

    const deltaX = e.clientX - dragStart.x;
    const deltaY = e.clientY - dragStart.y;

    setRotation({
      x: rotation.x + deltaY * 0.01,
      y: rotation.y + deltaX * 0.01
    });

    setDragStart({ x: e.clientX, y: e.clientY });
  };

  const handleMouseUp = () => {
    setIsDragging(false);
  };

  const handleNodeClick = (node) => {
    setSelectedNode(node);
    if (onNodeClick) {
      onNodeClick(node);
    }
  };

  const renderConnections = () => {
    return nodes.flatMap(node => {
      return node.connections.map(targetId => {
        const target = nodes.find(n => n.id === targetId);
        if (!target) return null;

        const start = project3DTo2D(node.x, node.y, node.z);
        const end = project3DTo2D(target.x, target.y, target.z);

        return (
          <line
            key={`${node.id}-${targetId}`}
            x1={start.x}
            y1={start.y}
            x2={end.x}
            y2={end.y}
            stroke="#d0d0d0"
            strokeWidth="2"
            opacity={start.z > 0 && end.z > 0 ? 0.3 : 0.6}
          />
        );
      }).filter(Boolean);
    });
  };

  // Sort nodes by z-index for proper rendering order
  const sortedNodes = [...nodes].sort((a, b) => {
    const aProj = project3DTo2D(a.x, a.y, a.z);
    const bProj = project3DTo2D(b.x, b.y, b.z);
    return aProj.z - bProj.z;
  });

  return (
    <div className="threed-concept-map" ref={containerRef}>
      <div className="map-header">
        <h3>3D Concept Map</h3>
        <p>Drag to rotate • Click nodes to explore</p>
      </div>

      <div 
        className="map-canvas"
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
      >
        <svg 
          width="100%" 
          height="100%" 
          viewBox="-400 -400 800 800"
          style={{ cursor: isDragging ? 'grabbing' : 'grab' }}
        >
          {/* Render connections */}
          <g className="connections">
            {renderConnections()}
          </g>

          {/* Render nodes */}
          <g className="nodes">
            {sortedNodes.map(node => {
              const projected = project3DTo2D(node.x, node.y, node.z);
              const status = getNodeStatus(node);
              const isHighlighted = highlightMode === 'all' || 
                (highlightMode === 'completed' && status === 'completed') ||
                (highlightMode === 'recommended' && status === 'recommended');
              const isSelected = selectedNode?.id === node.id;

              const size = 40 * projected.scale;
              const opacity = isHighlighted ? Math.max(0.3, projected.scale) : 0.2;

              let fillColor = '#e0e0e0';
              if (status === 'completed') fillColor = '#4caf50';
              else if (status === 'recommended') fillColor = '#ff9800';

              return (
                <g 
                  key={node.id}
                  transform={`translate(${projected.x}, ${projected.y})`}
                  onClick={() => handleNodeClick(node)}
                  style={{ cursor: 'pointer' }}
                  opacity={opacity}
                >
                  <circle
                    r={size / 2}
                    fill={fillColor}
                    stroke={isSelected ? '#667eea' : 'white'}
                    strokeWidth={isSelected ? 4 : 2}
                  />
                  <text
                    textAnchor="middle"
                    dy=".3em"
                    fontSize={Math.max(10, 12 * projected.scale)}
                    fill="white"
                    fontWeight="bold"
                  >
                    {status === 'completed' ? '✓' : 
                     status === 'recommended' ? '★' : '○'}
                  </text>
                  {projected.scale > 0.7 && (
                    <text
                      textAnchor="middle"
                      dy={size / 2 + 15}
                      fontSize={Math.max(8, 10 * projected.scale)}
                      fill="#2c3e50"
                      fontWeight="600"
                    >
                      {node.title.length > 15 ? node.title.substring(0, 15) + '...' : node.title}
                    </text>
                  )}
                </g>
              );
            })}
          </g>
        </svg>
      </div>

      {selectedNode && (
        <div className="node-details-panel">
          <button className="close-btn" onClick={() => setSelectedNode(null)}>×</button>
          <h4>{selectedNode.title}</h4>
          <p>{selectedNode.description}</p>
          <div className="detail-meta">
            <span className={`difficulty-badge ${selectedNode.difficulty}`}>
              {selectedNode.difficulty}
            </span>
            <span className={`status-badge ${getNodeStatus(selectedNode)}`}>
              {getNodeStatus(selectedNode)}
            </span>
          </div>
        </div>
      )}

      <div className="map-controls">
        <button onClick={() => setRotation({ x: 0, y: 0 })}>
          Reset View
        </button>
        <button onClick={() => setRotation({ x: rotation.x, y: rotation.y + 0.5 })}>
          Rotate Left
        </button>
        <button onClick={() => setRotation({ x: rotation.x, y: rotation.y - 0.5 })}>
          Rotate Right
        </button>
      </div>

      <div className="map-legend">
        <div className="legend-item">
          <div className="legend-circle completed" />
          <span>Completed</span>
        </div>
        <div className="legend-item">
          <div className="legend-circle recommended" />
          <span>Recommended</span>
        </div>
        <div className="legend-item">
          <div className="legend-circle pending" />
          <span>Pending</span>
        </div>
      </div>
    </div>
  );
};

export default ThreeDConceptMap;
