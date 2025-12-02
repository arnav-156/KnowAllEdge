import React, { useState, useEffect } from 'react';
import './HierarchicalTreeView.css';

const HierarchicalTreeView = ({ 
  topicData, 
  completedNodes, 
  recommendedNodes, 
  onNodeClick,
  highlightMode 
}) => {
  const [treeData, setTreeData] = useState(null);
  const [expandedNodes, setExpandedNodes] = useState(new Set());

  useEffect(() => {
    if (topicData && topicData.concepts) {
      const tree = buildHierarchy(topicData.concepts);
      setTreeData(tree);
      // Expand root by default
      setExpandedNodes(new Set([tree.id]));
    }
  }, [topicData]);

  const buildHierarchy = (concepts) => {
    // Create root node
    const root = {
      id: 'root',
      title: topicData.name || 'Learning Topic',
      description: topicData.description || '',
      children: []
    };

    // Group concepts by category or difficulty
    const categories = {};
    
    concepts.forEach((concept, index) => {
      const category = concept.category || concept.difficulty || 'general';
      if (!categories[category]) {
        categories[category] = {
          id: `category-${category}`,
          title: category.charAt(0).toUpperCase() + category.slice(1),
          description: `${category} concepts`,
          children: [],
          isCategory: true
        };
      }

      categories[category].children.push({
        id: concept.id || `concept-${index}`,
        title: concept.name || concept.title,
        description: concept.description || '',
        difficulty: concept.difficulty,
        estimatedTime: concept.estimated_time || '30 min',
        children: []
      });
    });

    root.children = Object.values(categories);
    return root;
  };

  const toggleNode = (nodeId) => {
    const newExpanded = new Set(expandedNodes);
    if (newExpanded.has(nodeId)) {
      newExpanded.delete(nodeId);
    } else {
      newExpanded.add(nodeId);
    }
    setExpandedNodes(newExpanded);
  };

  const getNodeStatus = (node) => {
    if (node.isCategory) return 'category';
    if (completedNodes.has(node.id)) return 'completed';
    if (recommendedNodes.has(node.id)) return 'recommended';
    return 'pending';
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed': return '✅';
      case 'recommended': return '⭐';
      case 'category': return '📁';
      default: return '○';
    }
  };

  const calculateCategoryProgress = (category) => {
    if (!category.children || category.children.length === 0) return 0;
    const completed = category.children.filter(c => completedNodes.has(c.id)).length;
    return Math.round((completed / category.children.length) * 100);
  };

  const renderNode = (node, level = 0) => {
    const isExpanded = expandedNodes.has(node.id);
    const hasChildren = node.children && node.children.length > 0;
    const status = getNodeStatus(node);
    const isHighlighted = highlightMode === 'all' || 
      (highlightMode === 'completed' && status === 'completed') ||
      (highlightMode === 'recommended' && status === 'recommended') ||
      status === 'category';

    return (
      <div key={node.id} className="tree-node-container">
        <div 
          className={`tree-node ${status} level-${level} ${isHighlighted ? 'highlighted' : 'dimmed'}`}
          style={{ marginLeft: `${level * 2}rem` }}
          onClick={() => {
            if (hasChildren) {
              toggleNode(node.id);
            } else if (onNodeClick) {
              onNodeClick(node);
            }
          }}
        >
          <div className="node-connector">
            {level > 0 && (
              <>
                <div className="connector-vertical" />
                <div className="connector-horizontal" />
              </>
            )}
          </div>

          <div className="node-content-wrapper">
            {hasChildren && (
              <span className="expand-toggle">
                {isExpanded ? '▼' : '▶'}
              </span>
            )}

            <div className="node-icon">
              {getStatusIcon(status)}
            </div>

            <div className="node-details">
              <h4>{node.title}</h4>
              {node.description && (
                <p className="node-description">{node.description}</p>
              )}
              
              {node.isCategory && (
                <div className="category-progress">
                  <div className="progress-bar-small">
                    <div 
                      className="progress-fill-small"
                      style={{ width: `${calculateCategoryProgress(node)}%` }}
                    />
                  </div>
                  <span className="progress-text-small">
                    {calculateCategoryProgress(node)}% complete
                  </span>
                </div>
              )}

              {!node.isCategory && node.estimatedTime && (
                <div className="node-meta-small">
                  <span>⏱️ {node.estimatedTime}</span>
                  {node.difficulty && (
                    <span className={`difficulty-badge-small ${node.difficulty}`}>
                      {node.difficulty}
                    </span>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>

        {hasChildren && isExpanded && (
          <div className="node-children">
            {node.children.map(child => renderNode(child, level + 1))}
          </div>
        )}
      </div>
    );
  };

  if (!treeData) {
    return <div className="hierarchical-tree-view loading">Loading tree...</div>;
  }

  return (
    <div className="hierarchical-tree-view">
      <div className="tree-header">
        <h3>Hierarchical Tree View</h3>
        <div className="tree-controls">
          <button onClick={() => setExpandedNodes(new Set([treeData.id]))}>
            Collapse All
          </button>
          <button onClick={() => {
            const allIds = new Set([treeData.id]);
            const addIds = (node) => {
              if (node.children) {
                node.children.forEach(child => {
                  allIds.add(child.id);
                  addIds(child);
                });
              }
            };
            addIds(treeData);
            setExpandedNodes(allIds);
          }}>
            Expand All
          </button>
        </div>
      </div>

      <div className="tree-container">
        {renderNode(treeData)}
      </div>

      <div className="tree-legend">
        <div className="legend-item">
          <span>📁</span>
          <span>Category</span>
        </div>
        <div className="legend-item">
          <span>✅</span>
          <span>Completed</span>
        </div>
        <div className="legend-item">
          <span>⭐</span>
          <span>Recommended</span>
        </div>
        <div className="legend-item">
          <span>○</span>
          <span>Pending</span>
        </div>
      </div>
    </div>
  );
};

export default HierarchicalTreeView;
