"""
Export Utilities for Study Tools
Supports PDF, Markdown, and Presentation formats
"""
import json
from datetime import datetime
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)

class ExportUtils:
    
    @staticmethod
    def export_to_markdown(content: Dict, include_metadata: bool = True) -> str:
        """Export content to Markdown format"""
        md_lines = []
        
        if include_metadata:
            md_lines.append(f"---")
            md_lines.append(f"title: {content.get('title', 'Untitled')}")
            md_lines.append(f"created: {content.get('created_at', datetime.now().isoformat())}")
            md_lines.append(f"tags: {', '.join(content.get('tags', []))}")
            md_lines.append(f"---\n")
        
        md_lines.append(f"# {content.get('title', 'Untitled')}\n")
        
        if content.get('description'):
            md_lines.append(f"{content['description']}\n")
        
        # Cornell notes format
        if content.get('note_type') == 'cornell':
            md_lines.append("## Cue Column\n")
            md_lines.append(f"{content.get('cue_column', '')}\n")
            
            md_lines.append("## Notes\n")
            md_lines.append(f"{content.get('notes_column', '')}\n")
            
            md_lines.append("## Summary\n")
            md_lines.append(f"{content.get('summary', '')}\n")
        
        # Regular content
        elif content.get('content'):
            md_lines.append(f"{content['content']}\n")
        
        # Citations
        if content.get('citations'):
            md_lines.append("## References\n")
            for citation in content['citations']:
                md_lines.append(f"- {citation}\n")
        
        return '\n'.join(md_lines)
    
    @staticmethod
    def export_to_pdf_html(content: Dict) -> str:
        """Generate HTML for PDF conversion"""
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{content.get('title', 'Untitled')}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 800px;
            margin: 40px auto;
            padding: 20px;
            line-height: 1.6;
            color: #333;
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #34495e;
            margin-top: 30px;
        }}
        .metadata {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 30px;
        }}
        .cornell-notes {{
            display: grid;
            grid-template-columns: 1fr 2fr;
            gap: 20px;
            margin: 20px 0;
        }}
        .cue-column {{
            background: #fff3cd;
            padding: 15px;
            border-radius: 5px;
        }}
        .notes-column {{
            background: #d1ecf1;
            padding: 15px;
            border-radius: 5px;
        }}
        .summary {{
            background: #d4edda;
            padding: 15px;
            border-radius: 5px;
            margin-top: 20px;
        }}
        .citations {{
            margin-top: 30px;
            padding-top: 20px;
            border-top: 2px solid #dee2e6;
        }}
        .citation {{
            margin: 10px 0;
            padding-left: 20px;
        }}
    </style>
</head>
<body>
    <div class="metadata">
        <strong>Created:</strong> {content.get('created_at', 'N/A')}<br>
        <strong>Tags:</strong> {', '.join(content.get('tags', []))}
    </div>
    
    <h1>{content.get('title', 'Untitled')}</h1>
"""
        
        if content.get('description'):
            html += f"<p>{content['description']}</p>"
        
        # Cornell notes
        if content.get('note_type') == 'cornell':
            html += '<div class="cornell-notes">'
            html += f'<div class="cue-column"><h3>Cues</h3>{content.get("cue_column", "")}</div>'
            html += f'<div class="notes-column"><h3>Notes</h3>{content.get("notes_column", "")}</div>'
            html += '</div>'
            html += f'<div class="summary"><h3>Summary</h3>{content.get("summary", "")}</div>'
        
        # Regular content
        elif content.get('content'):
            html += f"<div>{content['content']}</div>"
        
        # Citations
        if content.get('citations'):
            html += '<div class="citations"><h2>References</h2>'
            for citation in content['citations']:
                html += f'<div class="citation">{citation}</div>'
            html += '</div>'
        
        html += """
</body>
</html>
"""
        return html

    @staticmethod
    def export_to_presentation(content: Dict) -> str:
        """Generate HTML presentation (reveal.js style)"""
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{content.get('title', 'Untitled')}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }}
        .slide {{
            width: 100vw;
            height: 100vh;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            padding: 60px;
            text-align: center;
        }}
        .slide h1 {{
            font-size: 4rem;
            margin-bottom: 30px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }}
        .slide h2 {{
            font-size: 2.5rem;
            margin-bottom: 20px;
        }}
        .slide p {{
            font-size: 1.5rem;
            line-height: 1.8;
            max-width: 800px;
        }}
        .slide ul {{
            font-size: 1.3rem;
            text-align: left;
            max-width: 700px;
        }}
        .slide li {{
            margin: 15px 0;
        }}
        .navigation {{
            position: fixed;
            bottom: 30px;
            right: 30px;
            font-size: 0.9rem;
            opacity: 0.7;
        }}
    </style>
</head>
<body>
    <div class="slide">
        <h1>{content.get('title', 'Untitled')}</h1>
        <p>{content.get('description', '')}</p>
    </div>
    
    <div class="navigation">
        Use arrow keys to navigate
    </div>
    
    <script>
        // Simple slide navigation
        let currentSlide = 0;
        const slides = document.querySelectorAll('.slide');
        
        function showSlide(n) {{
            slides.forEach((slide, i) => {{
                slide.style.display = i === n ? 'flex' : 'none';
            }});
        }}
        
        document.addEventListener('keydown', (e) => {{
            if (e.key === 'ArrowRight' && currentSlide < slides.length - 1) {{
                currentSlide++;
                showSlide(currentSlide);
            }} else if (e.key === 'ArrowLeft' && currentSlide > 0) {{
                currentSlide--;
                showSlide(currentSlide);
            }}
        }});
        
        showSlide(0);
    </script>
</body>
</html>
"""
        return html
    
    @staticmethod
    def export_for_notion(content: Dict) -> Dict:
        """Format content for Notion API"""
        blocks = []
        
        # Title
        blocks.append({
            "object": "block",
            "type": "heading_1",
            "heading_1": {
                "rich_text": [{"type": "text", "text": {"content": content.get('title', 'Untitled')}}]
            }
        })
        
        # Description
        if content.get('description'):
            blocks.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": content['description']}}]
                }
            })
        
        # Cornell notes
        if content.get('note_type') == 'cornell':
            blocks.append({
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"type": "text", "text": {"content": "Cue Column"}}]
                }
            })
            blocks.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": content.get('cue_column', '')}}]
                }
            })
            
            blocks.append({
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"type": "text", "text": {"content": "Notes"}}]
                }
            })
            blocks.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": content.get('notes_column', '')}}]
                }
            })
            
            blocks.append({
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"type": "text", "text": {"content": "Summary"}}]
                }
            })
            blocks.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": content.get('summary', '')}}]
                }
            })
        
        return {
            "parent": {"type": "page_id", "page_id": ""},  # To be filled by user
            "properties": {
                "title": {
                    "title": [{"type": "text", "text": {"content": content.get('title', 'Untitled')}}]
                }
            },
            "children": blocks
        }
    
    @staticmethod
    def export_for_obsidian(content: Dict) -> str:
        """Format content for Obsidian (enhanced Markdown)"""
        md_lines = []
        
        # Frontmatter
        md_lines.append("---")
        md_lines.append(f"title: {content.get('title', 'Untitled')}")
        md_lines.append(f"created: {content.get('created_at', datetime.now().isoformat())}")
        md_lines.append(f"tags: [{', '.join(content.get('tags', []))}]")
        md_lines.append("---\n")
        
        md_lines.append(f"# {content.get('title', 'Untitled')}\n")
        
        if content.get('description'):
            md_lines.append(f"> {content['description']}\n")
        
        # Cornell notes with callouts
        if content.get('note_type') == 'cornell':
            md_lines.append("> [!question] Cue Column")
            md_lines.append(f"> {content.get('cue_column', '')}\n")
            
            md_lines.append("> [!note] Notes")
            md_lines.append(f"> {content.get('notes_column', '')}\n")
            
            md_lines.append("> [!summary] Summary")
            md_lines.append(f"> {content.get('summary', '')}\n")
        
        # Links to related topics
        if content.get('related_topics'):
            md_lines.append("## Related Topics\n")
            for topic in content['related_topics']:
                md_lines.append(f"- [[{topic}]]")
        
        return '\n'.join(md_lines)
    
    @staticmethod
    def export_for_onenote(content: Dict) -> str:
        """Format content for OneNote (HTML format)"""
        html = f"""
<?xml version="1.0"?>
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
    <title>{content.get('title', 'Untitled')}</title>
    <meta name="created" content="{content.get('created_at', datetime.now().isoformat())}" />
</head>
<body>
    <h1>{content.get('title', 'Untitled')}</h1>
"""
        
        if content.get('description'):
            html += f"<p>{content['description']}</p>"
        
        if content.get('note_type') == 'cornell':
            html += '<table border="1" style="width:100%; border-collapse:collapse;">'
            html += '<tr><th style="width:30%; background:#fff3cd;">Cue Column</th>'
            html += '<th style="background:#d1ecf1;">Notes</th></tr>'
            html += f'<tr><td style="vertical-align:top; padding:10px;">{content.get("cue_column", "")}</td>'
            html += f'<td style="vertical-align:top; padding:10px;">{content.get("notes_column", "")}</td></tr>'
            html += '</table>'
            html += f'<div style="background:#d4edda; padding:10px; margin-top:10px;"><strong>Summary:</strong> {content.get("summary", "")}</div>'
        
        html += """
</body>
</html>
"""
        return html
