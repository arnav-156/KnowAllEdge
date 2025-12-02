import React, { useState, useEffect } from 'react';
import './CitationManager.css';

const CitationManager = ({ userId, topicId }) => {
  const [citations, setCitations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState({
    title: '',
    authors: '',
    publication_date: '',
    url: '',
    citation_style: 'APA',
    topic_id: topicId || ''
  });
  const [selectedCitation, setSelectedCitation] = useState(null);
  const [formattedCitation, setFormattedCitation] = useState('');

  useEffect(() => {
    fetchCitations();
  }, [userId, topicId]);

  const fetchCitations = async () => {
    try {
      const url = topicId
        ? `/api/study-tools/citations?user_id=${userId}&topic_id=${topicId}`
        : `/api/study-tools/citations?user_id=${userId}`;
      
      const response = await fetch(url);
      const data = await response.json();
      
      if (data.success) {
        setCitations(data.citations);
      }
    } catch (error) {
      console.error('Error fetching citations:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateCitation = async (e) => {
    e.preventDefault();
    
    try {
      const response = await fetch('/api/study-tools/citations', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-User-ID': userId
        },
        body: JSON.stringify({
          ...formData,
          access_date: new Date().toISOString().split('T')[0]
        })
      });
      
      const data = await response.json();
      
      if (data.success) {
        fetchCitations();
        setShowForm(false);
        setFormData({
          title: '',
          authors: '',
          publication_date: '',
          url: '',
          citation_style: 'APA',
          topic_id: topicId || ''
        });
        alert('Citation created successfully!');
      }
    } catch (error) {
      console.error('Error creating citation:', error);
      alert('Failed to create citation');
    }
  };

  const handleViewFormatted = async (citation, style = null) => {
    try {
      const citationStyle = style || citation.citation_style;
      const response = await fetch(
        `/api/study-tools/citations/${citation.id}/format?style=${citationStyle}`
      );
      const data = await response.json();
      
      if (data.success) {
        setSelectedCitation(citation);
        setFormattedCitation(data.formatted);
      }
    } catch (error) {
      console.error('Error formatting citation:', error);
    }
  };

  const handleCopyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    alert('Citation copied to clipboard!');
  };

  const handleExportAll = () => {
    const allCitations = citations.map(c => 
      `${c.authors}. (${c.publication_date}). ${c.title}. ${c.url || ''}`
    ).join('\n\n');
    
    const blob = new Blob([allCitations], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'citations.txt';
    a.click();
  };

  if (loading) {
    return <div className="citation-manager-loading">Loading citations...</div>;
  }

  return (
    <div className="citation-manager">
      <div className="citation-header">
        <h2>Citation Manager</h2>
        <div className="header-actions">
          {citations.length > 0 && (
            <button className="export-btn" onClick={handleExportAll}>
              📥 Export All
            </button>
          )}
          <button className="add-citation-btn" onClick={() => setShowForm(!showForm)}>
            + Add Citation
          </button>
        </div>
      </div>

      {showForm && (
        <div className="citation-form">
          <h3>New Citation</h3>
          <form onSubmit={handleCreateCitation}>
            <div className="form-row">
              <div className="form-group">
                <label>Title *</label>
                <input
                  type="text"
                  value={formData.title}
                  onChange={(e) => setFormData({...formData, title: e.target.value})}
                  required
                  placeholder="Article or book title"
                />
              </div>

              <div className="form-group">
                <label>Citation Style *</label>
                <select
                  value={formData.citation_style}
                  onChange={(e) => setFormData({...formData, citation_style: e.target.value})}
                >
                  <option value="APA">APA</option>
                  <option value="MLA">MLA</option>
                  <option value="Chicago">Chicago</option>
                </select>
              </div>
            </div>

            <div className="form-group">
              <label>Authors *</label>
              <input
                type="text"
                value={formData.authors}
                onChange={(e) => setFormData({...formData, authors: e.target.value})}
                required
                placeholder="Last, F. M., & Last, F. M."
              />
              <small>Format: Last, F. M., & Last, F. M.</small>
            </div>

            <div className="form-row">
              <div className="form-group">
                <label>Publication Date</label>
                <input
                  type="text"
                  value={formData.publication_date}
                  onChange={(e) => setFormData({...formData, publication_date: e.target.value})}
                  placeholder="2024"
                />
              </div>

              <div className="form-group">
                <label>URL</label>
                <input
                  type="url"
                  value={formData.url}
                  onChange={(e) => setFormData({...formData, url: e.target.value})}
                  placeholder="https://example.com/article"
                />
              </div>
            </div>

            <div className="form-actions">
              <button type="submit" className="save-btn">Create Citation</button>
              <button type="button" className="cancel-btn" onClick={() => setShowForm(false)}>
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      <div className="citations-list">
        {citations.length === 0 ? (
          <div className="no-citations">
            <p>No citations yet. Add your first citation!</p>
          </div>
        ) : (
          <div className="citations-grid">
            {citations.map(citation => (
              <div key={citation.id} className="citation-card">
                <div className="citation-style-badge">{citation.citation_style}</div>
                
                <h4>{citation.title}</h4>
                <p className="citation-authors">{citation.authors}</p>
                
                <div className="citation-meta">
                  {citation.publication_date && (
                    <span>📅 {citation.publication_date}</span>
                  )}
                  {citation.url && (
                    <a href={citation.url} target="_blank" rel="noopener noreferrer">
                      🔗 View Source
                    </a>
                  )}
                </div>

                <div className="citation-actions">
                  <button onClick={() => handleViewFormatted(citation)}>
                    View Formatted
                  </button>
                  <div className="style-buttons">
                    <button 
                      className="style-btn"
                      onClick={() => handleViewFormatted(citation, 'APA')}
                      title="Format as APA"
                    >
                      APA
                    </button>
                    <button 
                      className="style-btn"
                      onClick={() => handleViewFormatted(citation, 'MLA')}
                      title="Format as MLA"
                    >
                      MLA
                    </button>
                    <button 
                      className="style-btn"
                      onClick={() => handleViewFormatted(citation, 'Chicago')}
                      title="Format as Chicago"
                    >
                      Chicago
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {selectedCitation && formattedCitation && (
        <div className="citation-modal" onClick={() => setSelectedCitation(null)}>
          <div className="citation-modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Formatted Citation</h3>
              <button className="close-btn" onClick={() => setSelectedCitation(null)}>×</button>
            </div>
            
            <div className="formatted-citation">
              <p>{formattedCitation}</p>
            </div>

            <div className="modal-actions">
              <button 
                className="copy-btn"
                onClick={() => handleCopyToClipboard(formattedCitation)}
              >
                📋 Copy to Clipboard
              </button>
              <button 
                className="close-modal-btn"
                onClick={() => setSelectedCitation(null)}
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default CitationManager;
