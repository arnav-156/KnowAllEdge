import React, { useEffect, useRef } from 'react';
import { ReactFlow, Background, Controls, MiniMap } from 'reactflow';
import 'reactflow/dist/style.css';
import './MindMapView.css';

const MindMapView = ({ 
  data, 
  zoomLevel, 
  currentFocus, 
  completedNodes, 
  recommendedNodes,
  highlightMode,
  onNodeClick,
  getNodeStatus 
}) => {
  const reactFlowWrapper = useRef(null);

  // Convert topic data to ReactFlow nodes and edges
  const convertToFlowData = () => {
    if (!data || !data.subtopics) return { nodes: [], edges: [] };

    const nodes = [];
    const edges = [];

    // Central node (main topic)
    nodes.push({
      id: 'root',
      type: 'default',
      data: { 
        label: data.title,
        status: 'root'
      },
      position: { x: 400, y: 300 },
      className: 'node-root',
      style: {
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        color: 'white',
        border: '3px solid #5568d3',
        borderRadius: '12px',
        padding: '20px',
        fontSize: '18px',
        fontWeight: 'bold',
        minWidth: '200px',
        textAlign: 'center'
      }
    });

    // Subtopic nodes arranged in a circle
    const radius = 300;
    const angleStep = (2 * Math.PI) / data.subtopics.length;

    data.subtopics.forEach((subtopic, index) => {
      const angle = index * angleStep;
      const x = 400 + radius * Math.cos(angle);
      const y = 300 + radius * Math.sin(angle);

      const status = getNodeStatus(subtopic.id);
      const shouldShow = 
        highlightMode === 'all' ||
        (highlightMode === 'completed' && status === 'completed') ||
        (highlightMode === 'recommended' && status === 'recommended') ||
        (highlightMode === 'incomplete' && status !== 'completed');

      if (shouldShow) {
        nodes.push({
          id: subtopic.id,
          type: 'default',
          data: { 
            label: subtopic.title,
            status: status
          },
          position: { x, y },
          className: `node-${status}`,
          style: getNodeStyle(status)
        });

        edges.push({
          id: `root-${subtopic.id}`,
          source: 'root',
          target: subtopic.id,
          animated: status === 'focused' || status === 'recommended',
          style: getEdgeStyle(status)
        });
      }
    });

    return { nodes, edges };
  };

  const getNodeStyle = (status) => {
    const baseStyle = {
      borderRadius: '8px',
      padding: '15px',
      fontSize: '14px',
      minWidth: '150px',
      textAlign: 'center',
      transition: 'all 0.3s ease'
    };

    switch (status) {
      case 'focused':
        return {
          ...baseStyle,
          background: '#ffd700',
          border: '3px solid #ffaa00',
          color: '#000',
          fontWeight: 'bold',
          transform: 'scale(1.1)',
          boxShadow: '0 0 20px rgba(255, 215, 0, 0.6)'
        };
      case 'completed':
        return {
          ...baseStyle,
          background: '#4caf50',
          border: '2px solid #45a049',
          color: 'white'
        };
      case 'recommended':
        return {
          ...baseStyle,
          background: '#ff9800',
          border: '2px solid #f57c00',
          color: 'white',
          animation: 'pulse 2s infinite'
        };
      default:
        return {
          ...baseStyle,
          background: 'white',
          border: '2px solid #ddd',
          color: '#333'
        };
    }
  };

  const getEdgeStyle = (status) => {
    switch (status) {
      case 'focused':
        return { stroke: '#ffd700', strokeWidth: 3 };
      case 'completed':
        return { stroke: '#4caf50', strokeWidth: 2 };
      case 'recommended':
        return { stroke: '#ff9800', strokeWidth: 2, strokeDasharray: '5,5' };
      default:
        return { stroke: '#b1b1b7', strokeWidth: 1 };
    }
  };

  const { nodes, edges } = convertToFlowData();

  const onNodeClickHandler = (event, node) => {
    if (node.id !== 'root') {
      const subtopic = data.subtopics.find(s => s.id === node.id);
      if (subtopic && onNodeClick) {
        onNodeClick(subtopic);
      }
    }
  };

  return (
    <div className="mindmap-view" style={{ transform: `scale(${zoomLevel})` }}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodeClick={onNodeClickHandler}
        fitView
        attributionPosition="bottom-left"
      >
        <Background color="#f0f0f0" gap={16} />
        <Controls />
        <MiniMap 
          nodeColor={(node) => {
            if (node.data.status === 'completed') return '#4caf50';
            if (node.data.status === 'recommended') return '#ff9800';
            if (node.data.status === 'focused') return '#ffd700';
            return '#ddd';
          }}
        />
      </ReactFlow>
    </div>
  );
};

export default MindMapView;
