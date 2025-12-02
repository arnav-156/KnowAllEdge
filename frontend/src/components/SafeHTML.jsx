/**
 * SafeHTML Component
 * Renders sanitized HTML content safely
 * 
 * Requirements: 5.6 - Integrate DOMPurify for HTML sanitization
 */

import React from 'react';
import PropTypes from 'prop-types';
import htmlSanitizer from '../utils/htmlSanitizer';

const SafeHTML = ({ html, tag = 'div', className = '', ...props }) => {
  const sanitizedHTML = React.useMemo(() => {
    return htmlSanitizer.sanitize(html);
  }, [html]);

  const Tag = tag;

  return (
    <Tag
      className={className}
      dangerouslySetInnerHTML={{ __html: sanitizedHTML }}
      {...props}
    />
  );
};

SafeHTML.propTypes = {
  html: PropTypes.string.isRequired,
  tag: PropTypes.string,
  className: PropTypes.string
};

export default SafeHTML;
