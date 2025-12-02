# Flask static asset caching configuration
# This file enables long-lived cache headers for JS, CSS, and image assets in production.
from flask import Blueprint, send_from_directory, current_app, make_response
import os

static_bp = Blueprint('static_bp', __name__)

STATIC_FOLDER = os.path.join(os.path.dirname(__file__), '../frontend/public')

@static_bp.route('/static/<path:filename>')
def serve_static(filename):
    response = make_response(send_from_directory(STATIC_FOLDER, filename))
    # Set long-lived cache headers (1 year)
    response.headers['Cache-Control'] = 'public, max-age=31536000, immutable'
    return response
