"""
AI Prompt Templates with Versioning
Centralized prompt management for consistency and optimization
"""

from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class PromptTemplate:
    """Prompt template with metadata"""
    name: str
    version: str
    template: str
    created_at: str
    description: str
    few_shot_examples: Optional[list] = None
    max_tokens: int = 200


class PromptRegistry:
    """Registry for managing prompt templates"""
    
    def __init__(self):
        self.templates = {}
        self._register_default_templates()
    
    def _register_default_templates(self):
        """Register all default prompt templates"""
        
        # System context (sent once with model initialization, not per-request)
        self.system_context = (
            "You are an expert educator skilled at explaining complex topics "
            "at various education levels. Generate clear, accurate, and engaging content."
        )
        
        # Explanation generation template (optimized - removed redundant system context)
        self.register(PromptTemplate(
            name="explanation_v2",
            version="2.0",
            template=(
                "Generate a {detail} explanation of '{subtopic}' for a {education} level audience. "
                "This is part of learning about '{topic}'. "
                "Learning Style: {learning_style}. "
                "Include a real-world application example and a recommended YouTube video search query. "
                "Return JSON format: {{\"explanation\": \"...\", \"real_world_application\": \"...\", \"youtube_search_query\": \"...\"}}. "
                "Limit explanation to {max_words} words."
            ),
            created_at="2025-01-15",
            description="Optimized explanation generator with structured output",
            max_tokens=400
        ))
        
        # Legacy template (for backward compatibility)
        self.register(PromptTemplate(
            name="explanation_v1",
            version="1.0",
            template=(
                "You are an expert at a broad range of topics. Your job is to help humans learn about new topics.\n\n"
                "Generate a paragraph explaining to someone at the {education} level in {detail} detail about {subtopic}. "
                "It is part of a presentation on {topic}. Limit your response to 200 words. "
                "Respond in plain text. Do not include any markdown formatting. Do not include a title, simply generate an explanation."
            ),
            created_at="2024-01-01",
            description="Original explanation template (deprecated)",
            max_tokens=250
        ))
        
        # Subtopic generation template
        self.register(PromptTemplate(
            name="subtopics_v1",
            version="1.0",
            template=(
                "Generate {count} key subtopics for learning about '{topic}'. "
                "Return JSON array format: [\"subtopic1\", \"subtopic2\", ...]. "
                "Subtopics should be specific, relevant, and progressively build knowledge."
            ),
            created_at="2025-01-15",
            description="Subtopic generator with structured output",
            max_tokens=300
        ))
        
        # Image topic extraction (optimized)
        self.register(PromptTemplate(
            name="image_topic_v1",
            version="1.0",
            template=(
                "Identify the main topic from this image in 1-5 words. "
                "Return only the topic name, no sentences or explanations."
            ),
            created_at="2025-01-15",
            description="Extract topic from image (ultra-concise)",
            max_tokens=20
        ))

        # Quiz generation template
        self.register(PromptTemplate(
            name="quiz_generation",
            version="1.0",
            template=(
                "Generate {count} multiple-choice questions about '{subtopic}' (part of '{topic}') "
                "for a {education} level student. "
                "Return JSON array format: [{{\"question\": \"...\", \"options\": [\"...\", \"...\", \"...\", \"...\"], \"correct_answer\": \"...\", \"explanation\": \"...\"}}]. "
                "Ensure questions test understanding, not just memorization."
            ),
            created_at="2025-01-20",
            description="Quiz generator with structured output",
            max_tokens=1000
        ))

        # Adaptive explanation template
        self.register(PromptTemplate(
            name="adaptive_explanation",
            version="1.0",
            template=(
                "Explain '{subtopic}' (part of '{topic}') for a learner with {mastery_level} mastery. "
                "Current context: {context}. "
                "Learning Style: {learning_style}. "
                "Include a real-world application example and a recommended YouTube video search query. "
                "Adjust depth and complexity accordingly. "
                "Return JSON format: {{\"explanation\": \"...\", \"real_world_application\": \"...\", \"youtube_search_query\": \"...\"}}. "
                "Limit explanation to {max_words} words."
            ),
            created_at="2025-01-20",
            description="Adaptive explanation generator based on mastery",
            max_tokens=400
        ))
        
        # Recommendation template
        self.register(PromptTemplate(
            name="recommendation",
            version="1.0",
            template=(
                "Based on the user's mastery of '{topic}' (completed subtopics: {completed_subtopics}), "
                "suggest 3 next logical subtopics to learn. "
                "Return JSON array format: [{{\"subtopic\": \"...\", \"reason\": \"...\"}}]."
            ),
            created_at="2025-01-20",
            description="Personalized topic recommendation",
            max_tokens=300
        ))
    
    def register(self, template: PromptTemplate):
        """Register a new template"""
        key = f"{template.name}:{template.version}"
        self.templates[key] = template
    
    def get(self, name: str, version: Optional[str] = None) -> PromptTemplate:
        """Get template by name and version"""
        if version:
            key = f"{name}:{version}"
            if key not in self.templates:
                raise ValueError(f"Template {key} not found")
            return self.templates[key]
        else:
            # Get latest version
            matching = [k for k in self.templates.keys() if k.startswith(f"{name}:")]
            if not matching:
                raise ValueError(f"No templates found for {name}")
            latest_key = sorted(matching)[-1]  # Get latest version
            return self.templates[latest_key]
    
    def format(self, name: str, version: Optional[str] = None, **kwargs) -> str:
        """Format template with provided values"""
        template = self.get(name, version)
        return template.template.format(**kwargs)
    
    def get_system_context(self) -> str:
        """Get system context for model initialization"""
        return self.system_context
    
    def list_templates(self) -> list:
        """List all available templates"""
        return [
            {
                "name": t.name,
                "version": t.version,
                "description": t.description,
                "max_tokens": t.max_tokens,
                "created_at": t.created_at
            }
            for t in self.templates.values()
        ]


# Global registry instance
prompt_registry = PromptRegistry()


def get_prompt_registry() -> PromptRegistry:
    """Get global prompt registry"""
    return prompt_registry
