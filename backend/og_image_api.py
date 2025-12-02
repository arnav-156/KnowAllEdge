"""
Open Graph Image Generator
Generates preview images for concept maps to be used in social media sharing
"""

from flask import Blueprint, request, jsonify, send_file
from PIL import Image, ImageDraw, ImageFont
import io
import os
import hashlib
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Create Blueprint
og_image_api = Blueprint('og_image_api', __name__)

# Cache directory for generated images
CACHE_DIR = os.path.join(os.path.dirname(__file__), 'data', 'og_images')
os.makedirs(CACHE_DIR, exist_ok=True)

# Image dimensions (Facebook/Twitter recommended)
OG_IMAGE_WIDTH = 1200
OG_IMAGE_HEIGHT = 630

# Colors
BACKGROUND_COLOR = (255, 255, 255)
PRIMARY_COLOR = (102, 126, 234)  # #667eea
SECONDARY_COLOR = (51, 51, 51)   # #333
TEXT_COLOR = (85, 85, 85)        # #555
BORDER_COLOR = (219, 222, 239)   # #dbdeef


def get_image_cache_path(topic: str, node_count: int, edge_count: int) -> str:
    """Generate cache file path for image"""
    cache_key = f"{topic}_{node_count}_{edge_count}"
    hash_key = hashlib.sha256(cache_key.encode()).hexdigest()[:16]
    return os.path.join(CACHE_DIR, f"{hash_key}.png")


def is_cache_valid(cache_path: str, max_age_hours: int = 24) -> bool:
    """Check if cached image is still valid"""
    if not os.path.exists(cache_path):
        return False
    
    # Check file age
    file_time = datetime.fromtimestamp(os.path.getmtime(cache_path))
    age = datetime.now() - file_time
    
    return age < timedelta(hours=max_age_hours)


def generate_og_image(topic: str, node_count: int = 0, edge_count: int = 0) -> io.BytesIO:
    """
    Generate an Open Graph image for a concept map
    
    Args:
        topic: The topic/title of the concept map
        node_count: Number of nodes in the graph
        edge_count: Number of edges in the graph
    
    Returns:
        BytesIO object containing the PNG image
    """
    # Create image
    img = Image.new('RGB', (OG_IMAGE_WIDTH, OG_IMAGE_HEIGHT), BACKGROUND_COLOR)
    draw = ImageDraw.Draw(img)
    
    # Load fonts (fallback to default if custom fonts not available)
    try:
        # Try to load custom fonts
        title_font = ImageFont.truetype("arial.ttf", 72)
        subtitle_font = ImageFont.truetype("arial.ttf", 36)
        stats_font = ImageFont.truetype("arial.ttf", 28)
        logo_font = ImageFont.truetype("arial.ttf", 48)
    except Exception:
        # Fallback to default font
        logger.warning("Custom fonts not available, using default font")
        title_font = ImageFont.load_default()
        subtitle_font = ImageFont.load_default()
        stats_font = ImageFont.load_default()
        logo_font = ImageFont.load_default()
    
    # Draw gradient-like background (simple two-tone)
    for i in range(OG_IMAGE_HEIGHT):
        alpha = i / OG_IMAGE_HEIGHT
        color = tuple(int(BACKGROUND_COLOR[j] * (1 - alpha * 0.05) + PRIMARY_COLOR[j] * alpha * 0.05) for j in range(3))
        draw.line([(0, i), (OG_IMAGE_WIDTH, i)], fill=color, width=1)
    
    # Draw border
    border_width = 10
    draw.rectangle(
        [(border_width, border_width), (OG_IMAGE_WIDTH - border_width, OG_IMAGE_HEIGHT - border_width)],
        outline=BORDER_COLOR,
        width=border_width
    )
    
    # Calculate text positions
    padding = 80
    y_position = padding
    
    # Draw logo/brand
    logo_text = "KNOWALLEDGE"
    logo_bbox = draw.textbbox((0, 0), logo_text, font=logo_font)
    logo_width = logo_bbox[2] - logo_bbox[0]
    draw.text(
        ((OG_IMAGE_WIDTH - logo_width) // 2, y_position),
        logo_text,
        fill=PRIMARY_COLOR,
        font=logo_font
    )
    
    y_position += 100
    
    # Draw title (topic) - wrap text if too long
    max_title_width = OG_IMAGE_WIDTH - (padding * 2)
    
    # Simple text wrapping
    words = topic.split()
    lines = []
    current_line = []
    
    for word in words:
        test_line = ' '.join(current_line + [word])
        bbox = draw.textbbox((0, 0), test_line, font=title_font)
        test_width = bbox[2] - bbox[0]
        
        if test_width <= max_title_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(' '.join(current_line))
            current_line = [word]
    
    if current_line:
        lines.append(' '.join(current_line))
    
    # Limit to 2 lines
    if len(lines) > 2:
        lines = lines[:2]
        lines[1] = lines[1][:40] + '...' if len(lines[1]) > 40 else lines[1]
    
    # Draw title lines
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=title_font)
        text_width = bbox[2] - bbox[0]
        draw.text(
            ((OG_IMAGE_WIDTH - text_width) // 2, y_position),
            line,
            fill=SECONDARY_COLOR,
            font=title_font
        )
        y_position += 90
    
    y_position += 40
    
    # Draw subtitle
    subtitle = "Interactive Concept Map"
    bbox = draw.textbbox((0, 0), subtitle, font=subtitle_font)
    subtitle_width = bbox[2] - bbox[0]
    draw.text(
        ((OG_IMAGE_WIDTH - subtitle_width) // 2, y_position),
        subtitle,
        fill=TEXT_COLOR,
        font=subtitle_font
    )
    
    y_position += 80
    
    # Draw stats (if provided)
    if node_count > 0 or edge_count > 0:
        stats_text = f"📊 {node_count} nodes  •  {edge_count} connections"
        bbox = draw.textbbox((0, 0), stats_text, font=stats_font)
        stats_width = bbox[2] - bbox[0]
        draw.text(
            ((OG_IMAGE_WIDTH - stats_width) // 2, y_position),
            stats_text,
            fill=TEXT_COLOR,
            font=stats_font
        )
    
    # Draw decorative elements (simple nodes)
    node_radius = 20
    node_positions = [
        (150, 150),
        (OG_IMAGE_WIDTH - 150, 150),
        (150, OG_IMAGE_HEIGHT - 150),
        (OG_IMAGE_WIDTH - 150, OG_IMAGE_HEIGHT - 150),
    ]
    
    for x, y in node_positions:
        draw.ellipse(
            [(x - node_radius, y - node_radius), (x + node_radius, y + node_radius)],
            fill=PRIMARY_COLOR,
            outline=None
        )
    
    # Save to BytesIO
    output = io.BytesIO()
    img.save(output, format='PNG', optimize=True)
    output.seek(0)
    
    return output


# ============================================================================
# API Routes
# ============================================================================

@og_image_api.route('/graphs/<graph_id>/og-image', methods=['GET'])
def get_og_image(graph_id: str):
    """
    Get or generate OG image for a graph
    GET /api/og/graphs/{graph_id}/og-image?topic=...&nodes=...&edges=...
    """
    try:
        # Get parameters
        topic = request.args.get('topic', 'Concept Map')
        node_count = int(request.args.get('nodes', 0))
        edge_count = int(request.args.get('edges', 0))
        
        # Check cache
        cache_path = get_image_cache_path(topic, node_count, edge_count)
        
        if is_cache_valid(cache_path):
            logger.info(f"Serving cached OG image for: {topic}")
            return send_file(cache_path, mimetype='image/png')
        
        # Generate new image
        logger.info(f"Generating new OG image for: {topic}")
        image_data = generate_og_image(topic, node_count, edge_count)
        
        # Save to cache
        with open(cache_path, 'wb') as f:
            f.write(image_data.getvalue())
        
        # Reset pointer
        image_data.seek(0)
        
        return send_file(image_data, mimetype='image/png')
    
    except Exception as e:
        logger.error(f"Error generating OG image: {e}")
        return jsonify({'error': str(e)}), 500


@og_image_api.route('/graphs/og-image/generate', methods=['POST'])
def generate_og_image_endpoint():
    """
    Generate OG image from JSON data
    POST /api/og/graphs/og-image/generate
    Body: { "topic": "...", "nodes": 10, "edges": 15 }
    """
    try:
        data = request.get_json() or {}
        topic = data.get('topic', 'Concept Map')
        node_count = int(data.get('nodes', 0))
        edge_count = int(data.get('edges', 0))
        
        # Generate image
        image_data = generate_og_image(topic, node_count, edge_count)
        
        return send_file(image_data, mimetype='image/png')
    
    except Exception as e:
        logger.error(f"Error generating OG image: {e}")
        return jsonify({'error': str(e)}), 500


@og_image_api.route('/graphs/og-image/cache/clear', methods=['POST'])
def clear_og_image_cache():
    """
    Clear OG image cache (admin only)
    POST /api/og/graphs/og-image/cache/clear
    """
    try:
        # Clear all cached images
        count = 0
        for filename in os.listdir(CACHE_DIR):
            if filename.endswith('.png'):
                os.remove(os.path.join(CACHE_DIR, filename))
                count += 1
        
        logger.info(f"Cleared {count} cached OG images")
        
        return jsonify({
            'success': True,
            'cleared': count
        })
    
    except Exception as e:
        logger.error(f"Error clearing OG image cache: {e}")
        return jsonify({'error': str(e)}), 500
