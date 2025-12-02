/**
 * Skeleton Loader Components
 * Provides placeholder loading states for better UX
 */

import React from 'react';
import PropTypes from 'prop-types';
import './SkeletonLoader.css';

export const SkeletonLine = ({ width = '100%', height = '16px', margin = '8px 0' }) => (
  <div 
    className="skeleton-line" 
    style={{ width, height, margin }}
  />
);

SkeletonLine.propTypes = {
  width: PropTypes.string,
  height: PropTypes.string,
  margin: PropTypes.string
};

export const SkeletonCard = () => (
  <div className="skeleton-card">
    <SkeletonLine width="100%" height="20px" margin="0 0 12px 0" />
    <SkeletonLine width="90%" height="16px" margin="0 0 8px 0" />
    <SkeletonLine width="80%" height="16px" margin="0 0 8px 0" />
    <SkeletonLine width="85%" height="16px" margin="0" />
  </div>
);

export const SkeletonSubtopic = () => (
  <div className="skeleton-subtopic">
    <div className="skeleton-checkbox" />
    <div className="skeleton-subtopic-text">
      <SkeletonLine width="200px" height="18px" margin="0" />
    </div>
  </div>
);

export const SkeletonGraph = () => (
  <div className="skeleton-graph">
    <div className="skeleton-graph-header">
      <SkeletonLine width="250px" height="24px" margin="0 0 20px 0" />
    </div>
    <div className="skeleton-graph-body">
      <div className="skeleton-node" style={{ top: '20%', left: '50%' }} />
      <div className="skeleton-node" style={{ top: '40%', left: '30%' }} />
      <div className="skeleton-node" style={{ top: '40%', left: '70%' }} />
      <div className="skeleton-node" style={{ top: '60%', left: '20%' }} />
      <div className="skeleton-node" style={{ top: '60%', left: '50%' }} />
      <div className="skeleton-node" style={{ top: '60%', left: '80%' }} />
    </div>
  </div>
);

export const SkeletonList = ({ count = 5 }) => (
  <div className="skeleton-list">
    {Array.from({ length: count }).map((_, index) => (
      <SkeletonCard key={index} />
    ))}
  </div>
);

SkeletonList.propTypes = {
  count: PropTypes.number
};

const SkeletonLoader = ({ variant = 'card', count = 1 }) => {
  switch (variant) {
    case 'line':
      return <SkeletonLine />;
    case 'card':
      return <SkeletonCard />;
    case 'subtopic':
      return <SkeletonSubtopic />;
    case 'graph':
      return <SkeletonGraph />;
    case 'list':
      return <SkeletonList count={count} />;
    default:
      return <SkeletonCard />;
  }
};

SkeletonLoader.propTypes = {
  variant: PropTypes.oneOf(['line', 'card', 'subtopic', 'graph', 'list']),
  count: PropTypes.number
};

export default SkeletonLoader;
