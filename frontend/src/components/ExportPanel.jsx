import React, { useState, useEffect } from 'react';
import './ExportPanel.css';

const ExportPanel = ({ userId, contentType = 'note', contentId = null }) => {
  const [exportHistory, setExportHistory] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedFormat, setSelectedFormat] = useState('markdown');
  const [content, setContent] = useState(null);
  const [preview, setPreview] = useState('');

  useEffect(() => {
    fetchExportHistory();
    if (contentId) {
      fetchContent();
    }
  }, [userId, contentId]);

  const fetchExportHistory = async () => {
    try {
      const response = await fetch(`/api/study-tools/export/history?user_id=${userId}&limit=20`);
      const data = await response.json();
      
      if (data.success) {
        setExportHistory(data.history);
      }
    } catch (error) {
      console.error('Error fetching export history:', error);
    }
  };

  const fetchContent = async () => {
    try {
      const response = await fetch(`/api/study-tools/notes/${contentId}`);
      const data = await response.json();
      
      if (data.success) {
        setContent(data.note);
      }
    } catch (error) {
      console.error('Error fetching content:', error);
    }
  };

  const handleExport = async (format) => {
    if (!content && !contentId) {
      alert('Please select content to export');
      return;
    }

    setLoading(true);

    try {
      const endpoint = `/api/study-tools/export/${format}`;
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-User-ID': userId
        },
        body: JSON.stringify(content || { id: contentId })
      });

      const data = await response.json();

      if (data.success) {
        if (format === 'markdown') {
          downloadFile(data.content, 'export.md', 'text/markdown');
        } else if (format === 'pdf') {
          setPreview(data.html);
          alert('PDF HTML generated. Use browser print (Ctrl+P) to save as PDF');
        } else if (format === 'presentation') {
          downloadFile(data.html, 'presentation.html', 'text/html');
        }
        
        fetchExportHistory();
      }
    } catch (error) {
      console.error('Error exporting:', error);
      alert('Export failed');
    } finally {
      setLoading(false);
    }
  };

  const downloadFile = (content, filename, mimeType) => {
    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString();
  };

  return (
    <div className="export-panel">
      <div className="export-header">
        <h2>Export Tools</h2>
      </div>

      <div className="export-content">
        <div className="export-options">
          <h3>Export Format</h3>
          
          <div className="format-cards">
            <div 
              className={`format-card ${selectedFormat === 'markdown' ? 'selected' : ''}`}
              onClick={() => setSelectedFormat('markdown')}
            >
              <div className="format-icon">📝</div>
              <h4>Markdown</h4>
              <p>Clean, portable text format</p>
              <ul>
                <li>Compatible with most editors</li>
                <li>Version control friendly</li>
                <li>Easy to read and edit</li>
              </ul>
            </div>

            <div 
              className={`format-card ${selectedFormat === 'pdf' ? 'selected' : ''}`}
              onClick={() => setSelectedFormat('pdf')}
            >
              <div className="format-icon">📄</div>
              <h4>PDF</h4>
              <p>Professional document format</p>
              <ul>
                <li>Print-ready output</li>
                <li>Preserves formatting</li>
                <li>Universal compatibility</li>
              </ul>
            </div>

            <div 
              className={`format-card ${selectedFormat === 'presentation' ? 'selected' : ''}`}
              onClick={() => setSelectedFormat('presentation')}
            >
              <div className="format-icon">🎬</div>
              <h4>Presentation</h4>
              <p>Interactive HTML slides</p>
              <ul>
                <li>Keyboard navigation</li>
                <li>Full-screen mode</li>
                <li>Modern design</li>
              </ul>
            </div>
          </div>

          <div className="export-actions">
            <button 
              className="export-btn"
              onClick={() => handleExport(selectedFormat)}
              disabled={loading || !content}
            >
              {loading ? 'Exporting...' : `Export as ${selectedFormat.toUpperCase()}`}
            </button>
          </div>

          {!content && !contentId && (
            <div className="export-hint">
              <p>💡 Select a note or citation to export, or use this panel from within a note/citation view</p>
            </div>
          )}
        </div>

        <div className="export-history">
          <h3>Export History</h3>
          
          {exportHistory.length === 0 ? (
            <div className="no-history">
              <p>No exports yet</p>
            </div>
          ) : (
            <div className="history-list">
              {exportHistory.map((item, index) => (
                <div key={index} className="history-item">
                  <div className="history-icon">
                    {item.format === 'markdown' && '📝'}
                    {item.format === 'pdf' && '📄'}
                    {item.format === 'presentation' && '🎬'}
                  </div>
                  <div className="history-details">
                    <div className="history-title">
                      {item.export_type} - {item.format.toUpperCase()}
                    </div>
                    <div className="history-date">
                      {formatDate(item.created_at)}
                    </div>
                  </div>
                  <div className="history-status">
                    {item.status === 'completed' ? '✓' : '⏳'}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {preview && (
        <div className="preview-modal" onClick={() => setPreview('')}>
          <div className="preview-content" onClick={(e) => e.stopPropagation()}>
            <div className="preview-header">
              <h3>PDF Preview</h3>
              <button onClick={() => setPreview('')}>×</button>
            </div>
            <div className="preview-body">
              <iframe srcDoc={preview} title="PDF Preview" />
            </div>
            <div className="preview-actions">
              <button onClick={() => window.print()}>Print / Save as PDF</button>
              <button onClick={() => setPreview('')}>Close</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ExportPanel;
