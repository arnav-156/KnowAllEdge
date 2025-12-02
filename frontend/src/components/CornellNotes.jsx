import React, { useState, useEffect } from 'react';
import './CornellNotes.css';

const CornellNotes = ({ userId, topicId }) => {
  const [notes, setNotes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showEditor, setShowEditor] = useState(false);
  const [currentNote, setCurrentNote] = useState(null);
  const [formData, setFormData] = useState({
    title: '',
    topic_id: topicId || '',
    cue_column: '',
    notes_column: '',
    summary: '',
    tags: []
  });
  const [tagInput, setTagInput] = useState('');

  useEffect(() => {
    fetchNotes();
  }, [userId, topicId]);

  const fetchNotes = async () => {
    try {
      const url = topicId 
        ? `/api/study-tools/notes?user_id=${userId}&topic_id=${topicId}`
        : `/api/study-tools/notes?user_id=${userId}`;
      
      const response = await fetch(url);
      const data = await response.json();
      
      if (data.success) {
        setNotes(data.notes);
      }
    } catch (error) {
      console.error('Error fetching notes:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateNote = () => {
    setCurrentNote(null);
    setFormData({
      title: '',
      topic_id: topicId || '',
      cue_column: '',
      notes_column: '',
      summary: '',
      tags: []
    });
    setShowEditor(true);
  };

  const handleEditNote = (note) => {
    setCurrentNote(note);
    setFormData({
      title: note.title,
      topic_id: note.topic_id || '',
      cue_column: note.cue_column || '',
      notes_column: note.notes_column || '',
      summary: note.summary || '',
      tags: note.tags || []
    });
    setShowEditor(true);
  };

  const handleSaveNote = async (e) => {
    e.preventDefault();
    
    try {
      const url = currentNote 
        ? `/api/study-tools/notes/${currentNote.id}`
        : '/api/study-tools/notes';
      
      const method = currentNote ? 'PUT' : 'POST';
      
      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
          'X-User-ID': userId
        },
        body: JSON.stringify({
          ...formData,
          note_type: 'cornell'
        })
      });
      
      const data = await response.json();
      
      if (data.success) {
        fetchNotes();
        setShowEditor(false);
        alert(currentNote ? 'Note updated!' : 'Note created!');
      }
    } catch (error) {
      console.error('Error saving note:', error);
      alert('Failed to save note');
    }
  };

  const handleDeleteNote = async (noteId) => {
    if (!confirm('Delete this note?')) return;
    
    try {
      const response = await fetch(`/api/study-tools/notes/${noteId}`, {
        method: 'DELETE'
      });
      
      if (response.ok) {
        fetchNotes();
      }
    } catch (error) {
      console.error('Error deleting note:', error);
    }
  };

  const handleAddTag = () => {
    if (tagInput.trim() && !formData.tags.includes(tagInput.trim())) {
      setFormData({
        ...formData,
        tags: [...formData.tags, tagInput.trim()]
      });
      setTagInput('');
    }
  };

  const handleRemoveTag = (tag) => {
    setFormData({
      ...formData,
      tags: formData.tags.filter(t => t !== tag)
    });
  };

  if (loading) {
    return <div className="cornell-notes-loading">Loading notes...</div>;
  }

  return (
    <div className="cornell-notes">
      <div className="cornell-notes-header">
        <h2>Cornell Notes</h2>
        <button className="create-note-btn" onClick={handleCreateNote}>
          + New Note
        </button>
      </div>

      {showEditor ? (
        <div className="cornell-editor">
          <div className="editor-header">
            <h3>{currentNote ? 'Edit Note' : 'New Cornell Note'}</h3>
            <button className="close-btn" onClick={() => setShowEditor(false)}>×</button>
          </div>

          <form onSubmit={handleSaveNote}>
            <div className="form-group">
              <label>Title *</label>
              <input
                type="text"
                value={formData.title}
                onChange={(e) => setFormData({...formData, title: e.target.value})}
                required
                placeholder="Note title"
              />
            </div>

            <div className="cornell-layout">
              <div className="cue-section">
                <label>Cue Column</label>
                <textarea
                  value={formData.cue_column}
                  onChange={(e) => setFormData({...formData, cue_column: e.target.value})}
                  placeholder="Key questions, keywords, main ideas..."
                  rows="15"
                />
                <div className="help-text">
                  Write questions, keywords, and main ideas here
                </div>
              </div>

              <div className="notes-section">
                <label>Notes Column</label>
                <textarea
                  value={formData.notes_column}
                  onChange={(e) => setFormData({...formData, notes_column: e.target.value})}
                  placeholder="Detailed notes, explanations, examples..."
                  rows="15"
                />
                <div className="help-text">
                  Write detailed notes, explanations, and examples here
                </div>
              </div>
            </div>

            <div className="form-group">
              <label>Summary</label>
              <textarea
                value={formData.summary}
                onChange={(e) => setFormData({...formData, summary: e.target.value})}
                placeholder="Brief summary of main points..."
                rows="4"
              />
              <div className="help-text">
                Summarize the key takeaways in 2-3 sentences
              </div>
            </div>

            <div className="form-group">
              <label>Tags</label>
              <div className="tags-input">
                <input
                  type="text"
                  value={tagInput}
                  onChange={(e) => setTagInput(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), handleAddTag())}
                  placeholder="Add tag and press Enter"
                />
                <button type="button" onClick={handleAddTag}>Add</button>
              </div>
              <div className="tags-list">
                {formData.tags.map(tag => (
                  <span key={tag} className="tag">
                    {tag}
                    <button type="button" onClick={() => handleRemoveTag(tag)}>×</button>
                  </span>
                ))}
              </div>
            </div>

            <div className="form-actions">
              <button type="submit" className="save-btn">
                {currentNote ? 'Update Note' : 'Create Note'}
              </button>
              <button type="button" className="cancel-btn" onClick={() => setShowEditor(false)}>
                Cancel
              </button>
            </div>
          </form>
        </div>
      ) : (
        <div className="notes-list">
          {notes.length === 0 ? (
            <div className="no-notes">
              <p>No notes yet. Create your first Cornell note!</p>
            </div>
          ) : (
            <div className="notes-grid">
              {notes.map(note => (
                <div key={note.id} className="note-card">
                  <div className="note-card-header">
                    <h3>{note.title}</h3>
                    <div className="note-actions">
                      <button onClick={() => handleEditNote(note)}>✏️</button>
                      <button onClick={() => handleDeleteNote(note.id)}>🗑️</button>
                    </div>
                  </div>
                  
                  <div className="note-preview">
                    <div className="preview-section">
                      <strong>Cues:</strong>
                      <p>{note.cue_column?.substring(0, 100)}...</p>
                    </div>
                    <div className="preview-section">
                      <strong>Notes:</strong>
                      <p>{note.notes_column?.substring(0, 150)}...</p>
                    </div>
                    {note.summary && (
                      <div className="preview-section">
                        <strong>Summary:</strong>
                        <p>{note.summary}</p>
                      </div>
                    )}
                  </div>

                  {note.tags && note.tags.length > 0 && (
                    <div className="note-tags">
                      {note.tags.map(tag => (
                        <span key={tag} className="tag">{tag}</span>
                      ))}
                    </div>
                  )}

                  <div className="note-meta">
                    <span>Updated: {new Date(note.updated_at).toLocaleDateString()}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default CornellNotes;
