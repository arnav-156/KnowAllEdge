"""
Study Tools API Routes
Handles calendar, notes, citations, exports, and integrations
"""
from flask import Blueprint, request, jsonify, send_file
from functools import wraps
import logging
from study_tools_db import StudyToolsDB
from export_utils import ExportUtils
import io
import json

logger = logging.getLogger(__name__)

study_tools_bp = Blueprint('study_tools', __name__, url_prefix='/api/study-tools')
study_tools_db = StudyToolsDB()
export_utils = ExportUtils()

def require_user_id(f):
    """Decorator to require user_id in request"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = request.headers.get('X-User-ID') or request.args.get('user_id')
        if not user_id:
            return jsonify({'error': 'User ID required'}), 401
        return f(user_id, *args, **kwargs)
    return decorated_function

# ==================== CALENDAR ENDPOINTS ====================

@study_tools_bp.route('/calendar/events', methods=['GET'])
@require_user_id
def get_events(user_id):
    """Get user's calendar events"""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        events = study_tools_db.get_user_events(user_id, start_date, end_date)
        
        return jsonify({
            'success': True,
            'events': events,
            'count': len(events)
        })
    except Exception as e:
        logger.error(f"Error getting events: {e}")
        return jsonify({'error': str(e)}), 500

@study_tools_bp.route('/calendar/events', methods=['POST'])
@require_user_id
def create_event(user_id):
    """Create a calendar event"""
    try:
        data = request.get_json()
        
        if not data.get('title') or not data.get('start_time') or not data.get('end_time'):
            return jsonify({'error': 'Title, start_time, and end_time are required'}), 400
        
        event = study_tools_db.create_event(user_id, data)
        
        return jsonify({
            'success': True,
            'event': event
        })
    except Exception as e:
        logger.error(f"Error creating event: {e}")
        return jsonify({'error': str(e)}), 500

@study_tools_bp.route('/calendar/events/<event_id>', methods=['GET'])
def get_event(event_id):
    """Get a specific event"""
    try:
        event = study_tools_db.get_event(event_id)
        
        if not event:
            return jsonify({'error': 'Event not found'}), 404
        
        return jsonify({
            'success': True,
            'event': event
        })
    except Exception as e:
        logger.error(f"Error getting event: {e}")
        return jsonify({'error': str(e)}), 500

@study_tools_bp.route('/calendar/events/<event_id>', methods=['PUT'])
def update_event(event_id):
    """Update a calendar event"""
    try:
        data = request.get_json()
        event = study_tools_db.update_event(event_id, data)
        
        return jsonify({
            'success': True,
            'event': event
        })
    except Exception as e:
        logger.error(f"Error updating event: {e}")
        return jsonify({'error': str(e)}), 500

@study_tools_bp.route('/calendar/events/<event_id>', methods=['DELETE'])
def delete_event(event_id):
    """Delete a calendar event"""
    try:
        deleted = study_tools_db.delete_event(event_id)
        
        if deleted:
            return jsonify({'success': True, 'message': 'Event deleted'})
        else:
            return jsonify({'error': 'Event not found'}), 404
    except Exception as e:
        logger.error(f"Error deleting event: {e}")
        return jsonify({'error': str(e)}), 500

# ==================== NOTES ENDPOINTS ====================

@study_tools_bp.route('/notes', methods=['GET'])
@require_user_id
def get_notes(user_id):
    """Get user's notes"""
    try:
        topic_id = request.args.get('topic_id')
        notes = study_tools_db.get_user_notes(user_id, topic_id)
        
        return jsonify({
            'success': True,
            'notes': notes,
            'count': len(notes)
        })
    except Exception as e:
        logger.error(f"Error getting notes: {e}")
        return jsonify({'error': str(e)}), 500

@study_tools_bp.route('/notes', methods=['POST'])
@require_user_id
def create_note(user_id):
    """Create a note"""
    try:
        data = request.get_json()
        
        if not data.get('title'):
            return jsonify({'error': 'Title is required'}), 400
        
        note = study_tools_db.create_note(user_id, data)
        
        return jsonify({
            'success': True,
            'note': note
        })
    except Exception as e:
        logger.error(f"Error creating note: {e}")
        return jsonify({'error': str(e)}), 500

@study_tools_bp.route('/notes/<note_id>', methods=['GET'])
def get_note(note_id):
    """Get a specific note"""
    try:
        note = study_tools_db.get_note(note_id)
        
        if not note:
            return jsonify({'error': 'Note not found'}), 404
        
        return jsonify({
            'success': True,
            'note': note
        })
    except Exception as e:
        logger.error(f"Error getting note: {e}")
        return jsonify({'error': str(e)}), 500

@study_tools_bp.route('/notes/<note_id>', methods=['PUT'])
def update_note(note_id):
    """Update a note"""
    try:
        data = request.get_json()
        note = study_tools_db.update_note(note_id, data)
        
        return jsonify({
            'success': True,
            'note': note
        })
    except Exception as e:
        logger.error(f"Error updating note: {e}")
        return jsonify({'error': str(e)}), 500

@study_tools_bp.route('/notes/<note_id>', methods=['DELETE'])
def delete_note(note_id):
    """Delete a note"""
    try:
        deleted = study_tools_db.delete_note(note_id)
        
        if deleted:
            return jsonify({'success': True, 'message': 'Note deleted'})
        else:
            return jsonify({'error': 'Note not found'}), 404
    except Exception as e:
        logger.error(f"Error deleting note: {e}")
        return jsonify({'error': str(e)}), 500

# ==================== CITATIONS ENDPOINTS ====================

@study_tools_bp.route('/citations', methods=['GET'])
@require_user_id
def get_citations(user_id):
    """Get user's citations"""
    try:
        topic_id = request.args.get('topic_id')
        citations = study_tools_db.get_user_citations(user_id, topic_id)
        
        return jsonify({
            'success': True,
            'citations': citations,
            'count': len(citations)
        })
    except Exception as e:
        logger.error(f"Error getting citations: {e}")
        return jsonify({'error': str(e)}), 500

@study_tools_bp.route('/citations', methods=['POST'])
@require_user_id
def create_citation(user_id):
    """Create a citation"""
    try:
        data = request.get_json()
        
        if not data.get('title'):
            return jsonify({'error': 'Title is required'}), 400
        
        citation = study_tools_db.create_citation(user_id, data)
        formatted = study_tools_db.format_citation(citation)
        
        return jsonify({
            'success': True,
            'citation': citation,
            'formatted': formatted
        })
    except Exception as e:
        logger.error(f"Error creating citation: {e}")
        return jsonify({'error': str(e)}), 500

@study_tools_bp.route('/citations/<citation_id>', methods=['GET'])
def get_citation(citation_id):
    """Get a specific citation"""
    try:
        citation = study_tools_db.get_citation(citation_id)
        
        if not citation:
            return jsonify({'error': 'Citation not found'}), 404
        
        formatted = study_tools_db.format_citation(citation)
        
        return jsonify({
            'success': True,
            'citation': citation,
            'formatted': formatted
        })
    except Exception as e:
        logger.error(f"Error getting citation: {e}")
        return jsonify({'error': str(e)}), 500

@study_tools_bp.route('/citations/<citation_id>/format', methods=['GET'])
def format_citation(citation_id):
    """Get formatted citation in specified style"""
    try:
        style = request.args.get('style', 'APA')
        citation = study_tools_db.get_citation(citation_id)
        
        if not citation:
            return jsonify({'error': 'Citation not found'}), 404
        
        citation['citation_style'] = style
        formatted = study_tools_db.format_citation(citation)
        
        return jsonify({
            'success': True,
            'formatted': formatted,
            'style': style
        })
    except Exception as e:
        logger.error(f"Error formatting citation: {e}")
        return jsonify({'error': str(e)}), 500

# ==================== EXPORT ENDPOINTS ====================

@study_tools_bp.route('/export/markdown', methods=['POST'])
@require_user_id
def export_markdown(user_id):
    """Export content to Markdown"""
    try:
        data = request.get_json()
        markdown = export_utils.export_to_markdown(data)
        
        # Record export
        study_tools_db.record_export(user_id, {
            'export_type': 'note',
            'format': 'markdown',
            'content_id': data.get('id')
        })
        
        return jsonify({
            'success': True,
            'content': markdown,
            'format': 'markdown'
        })
    except Exception as e:
        logger.error(f"Error exporting to markdown: {e}")
        return jsonify({'error': str(e)}), 500

@study_tools_bp.route('/export/pdf', methods=['POST'])
@require_user_id
def export_pdf(user_id):
    """Export content to PDF (returns HTML for PDF conversion)"""
    try:
        data = request.get_json()
        html = export_utils.export_to_pdf_html(data)
        
        # Record export
        study_tools_db.record_export(user_id, {
            'export_type': 'note',
            'format': 'pdf',
            'content_id': data.get('id')
        })
        
        return jsonify({
            'success': True,
            'html': html,
            'format': 'pdf',
            'message': 'Use browser print or PDF converter to generate PDF'
        })
    except Exception as e:
        logger.error(f"Error exporting to PDF: {e}")
        return jsonify({'error': str(e)}), 500

@study_tools_bp.route('/export/presentation', methods=['POST'])
@require_user_id
def export_presentation(user_id):
    """Export content to presentation format"""
    try:
        data = request.get_json()
        html = export_utils.export_to_presentation(data)
        
        # Record export
        study_tools_db.record_export(user_id, {
            'export_type': 'note',
            'format': 'presentation',
            'content_id': data.get('id')
        })
        
        return jsonify({
            'success': True,
            'html': html,
            'format': 'presentation'
        })
    except Exception as e:
        logger.error(f"Error exporting to presentation: {e}")
        return jsonify({'error': str(e)}), 500

@study_tools_bp.route('/export/history', methods=['GET'])
@require_user_id
def get_export_history(user_id):
    """Get export history"""
    try:
        limit = int(request.args.get('limit', 50))
        history = study_tools_db.get_export_history(user_id, limit)
        
        return jsonify({
            'success': True,
            'history': history,
            'count': len(history)
        })
    except Exception as e:
        logger.error(f"Error getting export history: {e}")
        return jsonify({'error': str(e)}), 500

# ==================== INTEGRATION ENDPOINTS ====================

@study_tools_bp.route('/integrations', methods=['GET'])
@require_user_id
def get_integrations(user_id):
    """Get all integration settings"""
    try:
        integrations = study_tools_db.get_integration_settings(user_id)
        
        return jsonify({
            'success': True,
            'integrations': integrations
        })
    except Exception as e:
        logger.error(f"Error getting integrations: {e}")
        return jsonify({'error': str(e)}), 500

@study_tools_bp.route('/integrations/<platform>', methods=['GET'])
@require_user_id
def get_integration(user_id, platform):
    """Get integration settings for a specific platform"""
    try:
        settings = study_tools_db.get_integration_settings(user_id, platform)
        
        if not settings:
            return jsonify({'error': 'Integration not found'}), 404
        
        return jsonify({
            'success': True,
            'settings': settings
        })
    except Exception as e:
        logger.error(f"Error getting integration: {e}")
        return jsonify({'error': str(e)}), 500

@study_tools_bp.route('/integrations/<platform>', methods=['POST'])
@require_user_id
def save_integration(user_id, platform):
    """Save integration settings"""
    try:
        data = request.get_json()
        settings = study_tools_db.save_integration_settings(user_id, platform, data)
        
        return jsonify({
            'success': True,
            'settings': settings,
            'message': f'{platform} integration configured'
        })
    except Exception as e:
        logger.error(f"Error saving integration: {e}")
        return jsonify({'error': str(e)}), 500

@study_tools_bp.route('/integrations/<platform>/sync', methods=['POST'])
@require_user_id
def sync_integration(user_id, platform):
    """Sync content to integration platform"""
    try:
        data = request.get_json()
        content = data.get('content', {})
        
        # Format content for specific platform
        if platform == 'notion':
            formatted = export_utils.export_for_notion(content)
        elif platform == 'obsidian':
            formatted = export_utils.export_for_obsidian(content)
        elif platform == 'onenote':
            formatted = export_utils.export_for_onenote(content)
        else:
            return jsonify({'error': f'Unsupported platform: {platform}'}), 400
        
        # Update last sync time
        study_tools_db.update_last_sync(user_id, platform)
        
        return jsonify({
            'success': True,
            'platform': platform,
            'formatted_content': formatted,
            'message': f'Content formatted for {platform}. Use the formatted content with your {platform} API.'
        })
    except Exception as e:
        logger.error(f"Error syncing to {platform}: {e}")
        return jsonify({'error': str(e)}), 500

@study_tools_bp.route('/integrations/<platform>/test', methods=['POST'])
@require_user_id
def test_integration(user_id, platform):
    """Test integration connection"""
    try:
        settings = study_tools_db.get_integration_settings(user_id, platform)
        
        if not settings:
            return jsonify({'error': 'Integration not configured'}), 404
        
        # In a real implementation, this would test the actual API connection
        # For now, we'll just verify settings exist
        
        return jsonify({
            'success': True,
            'platform': platform,
            'status': 'connected',
            'message': f'{platform} integration is configured'
        })
    except Exception as e:
        logger.error(f"Error testing integration: {e}")
        return jsonify({'error': str(e)}), 500
