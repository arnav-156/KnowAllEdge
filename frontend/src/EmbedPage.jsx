/* eslint-disable no-unused-vars */
import React, { useEffect, useState, useCallback, useRef } from 'react';
import { useSearchParams } from 'react-router-dom';
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
} from 'reactflow';
import dagre from 'dagre';
import 'reactflow/dist/style.css';

// Dagre layout configuration
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

// Get layout function
const getLayoutedElements = (nodes, edges, direction = 'TB') => {
  const isHorizontal = direction === 'LR';
  dagreGraph.setGraph({ rankdir: direction });

  nodes.forEach((node) => {
    dagreGraph.setNode(node.id, { width: nodeWidth, height: nodeHeight });
  });

  edges.forEach((edge) => {
    dagreGraph.setEdge(edge.source, edge.target);
  });

  dagre.layout(dagreGraph);

  const layoutedNodes = nodes.map((node) => {
    const nodeWithPosition = dagreGraph.node(node.id);
    return {
      ...node,
      position: {
        x: nodeWithPosition.x - nodeWidth / 2,
        y: nodeWithPosition.y - nodeHeight / 2,
      },
    };
  });

  return { nodes: layoutedNodes, edges };
};

const EmbedPage = () => {
  const [searchParams] = useSearchParams();
  const [graphData, setGraphData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedNode, setSelectedNode] = useState(null);

  useEffect(() => {
    // Parse data URI from URL
    const dataUri = searchParams.get('data');
    
    if (!dataUri) {
      setError('No data provided. Please use a valid embed URL.');
      setLoading(false);
      return;
    }

    try {
      // Decode the data URI
      const jsonString = decodeURIComponent(atob(dataUri));
      const data = JSON.parse(jsonString);
      
      if (!data.nodes || !data.edges) {
        throw new Error('Invalid graph data structure');
      }
      
      setGraphData(data);
      
      // Transform nodes to ReactFlow format
      const transformedNodes = data.nodes.map(node => ({
        id: node.id,
        type: 'default',
        data: {
          label: (
            <div style={{ 
              display: 'flex', 
              alignItems: 'center', 
              gap: '5px',
              fontSize: '12px',
              padding: '5px'
            }}>
              <span>{nodeIcons[node.type] || '📄'}</span>
              <span style={{ 
                overflow: 'hidden', 
                textOverflow: 'ellipsis',
                whiteSpace: 'nowrap',
                maxWidth: '140px'
              }}>
                {node.fullContent || node.label || 'Node'}
              </span>
            </div>
          ),
          fullContent: node.fullContent,
          nodeType: node.type
        },
        position: node.position || { x: 0, y: 0 }
      }));
      
      // Transform edges
      const transformedEdges = data.edges.map(edge => ({
        id: edge.id,
        source: edge.source,
        target: edge.target,
        type: edge.type || 'smoothstep',
        animated: edge.animated || false
      }));
      
      // Apply layout
      const { nodes: layoutedNodes, edges: layoutedEdges } = getLayoutedElements(
        transformedNodes,
        transformedEdges,
        'TB'
      );
      
      setNodes(layoutedNodes);
      setEdges(layoutedEdges);
      setLoading(false);
    } catch (error) {
      console.error('Failed to parse embed data:', error);
      setError(`Failed to load graph: ${error.message}`);
      setLoading(false);
    }
  }, [searchParams, setNodes, setEdges]);

  const onNodeClick = useCallback((event, node) => {
    setSelectedNode(node);
    setIsModalOpen(true);
  }, []);

  const closeModal = useCallback(() => {
    setIsModalOpen(false);
    setSelectedNode(null);
  }, []);

  if (loading) {
    return (
      <div style={{
        width: '100vw',
        height: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: '#f9fafb',
        fontFamily: 'system-ui, -apple-system, sans-serif'
      }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: '48px', marginBottom: '20px' }}>⏳</div>
          <div style={{ fontSize: '18px', color: '#667eea', fontWeight: 'bold' }}>
            Loading concept map...
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{
        width: '100vw',
        height: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: '#fef2f2',
        fontFamily: 'system-ui, -apple-system, sans-serif'
      }}>
        <div style={{ 
          textAlign: 'center',
          padding: '40px',
          background: 'white',
          borderRadius: '12px',
          boxShadow: '0 4px 20px rgba(0,0,0,0.1)',
          maxWidth: '500px'
        }}>
          <div style={{ fontSize: '48px', marginBottom: '20px' }}>⚠️</div>
          <div style={{ fontSize: '20px', color: '#dc2626', fontWeight: 'bold', marginBottom: '10px' }}>
            Error Loading Graph
          </div>
          <div style={{ fontSize: '14px', color: '#666' }}>
            {error}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div style={{ width: '100vw', height: '100vh', position: 'relative' }}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeClick={onNodeClick}
        fitView
        attributionPosition="bottom-right"
        style={{ background: '#f9fafb' }}
      >
        <Background color="#aaa" gap={16} />
        <Controls />
        <MiniMap 
          nodeColor={() => '#667eea'}
          maskColor="rgba(0, 0, 0, 0.1)"
        />
      </ReactFlow>

      {/* Watermark/Branding */}
      <div style={{
        position: 'absolute',
        bottom: '10px',
        left: '50%',
        transform: 'translateX(-50%)',
        background: 'rgba(255, 255, 255, 0.95)',
        padding: '8px 16px',
        borderRadius: '20px',
        boxShadow: '0 2px 10px rgba(0,0,0,0.1)',
        fontSize: '12px',
        color: '#667eea',
        fontWeight: 'bold',
        zIndex: 10,
        display: 'flex',
        alignItems: 'center',
        gap: '8px'
      }}>
        {graphData?.topic && (
          <span style={{ color: '#333' }}>{graphData.topic}</span>
        )}
        <span style={{ color: '#ddd' }}>•</span>
        <a 
          href="https://KNOWALLEDGE.com" 
          target="_blank" 
          rel="noopener noreferrer"
          style={{ 
            color: '#667eea', 
            textDecoration: 'none',
            display: 'flex',
            alignItems: 'center',
            gap: '4px'
          }}
        >
          <span>Powered by KNOWALLEDGE</span>
          <span style={{ fontSize: '10px' }}>↗</span>
        </a>
      </div>

      {/* Node Detail Modal */}
      {isModalOpen && selectedNode && (
        <div
          onClick={closeModal}
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: 'rgba(0, 0, 0, 0.5)',
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
              maxWidth: '600px',
              width: '100%',
              maxHeight: '80vh',
              overflow: 'auto',
              boxShadow: '0 20px 60px rgba(0,0,0,0.3)',
              position: 'relative'
            }}
          >
            <button
              onClick={closeModal}
              style={{
                position: 'absolute',
                top: '15px',
                right: '15px',
                background: 'none',
                border: 'none',
                fontSize: '24px',
                cursor: 'pointer',
                color: '#999',
                padding: '5px',
                lineHeight: '1'
              }}
            >
              ✕
            </button>

            <div style={{ marginBottom: '15px' }}>
              <div style={{ 
                fontSize: '20px', 
                fontWeight: 'bold',
                color: '#333',
                marginBottom: '10px'
              }}>
                {nodeIcons[selectedNode.data.nodeType] || '📄'} {selectedNode.data.nodeType || 'Node'}
              </div>
              <div style={{ 
                fontSize: '16px',
                color: '#555',
                lineHeight: '1.6'
              }}>
                {selectedNode.data.fullContent || 'No content available'}
              </div>
            </div>

            <div style={{
              marginTop: '20px',
              paddingTop: '20px',
              borderTop: '1px solid #eee',
              fontSize: '12px',
              color: '#999',
              textAlign: 'center'
            }}>
              <a 
                href="https://KNOWALLEDGE.com" 
                target="_blank" 
                rel="noopener noreferrer"
                style={{ color: '#667eea', textDecoration: 'none' }}
              >
                Create your own concept map →
              </a>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default EmbedPage;
