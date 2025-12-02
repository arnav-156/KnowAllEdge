"""
Content Validation Module
Validates AI-generated content for quality, relevance, and accuracy
"""

import re
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from structured_logging import get_logger

logger = get_logger(__name__)


@dataclass
class ValidationResult:
    """Result of content validation"""
    is_valid: bool
    quality_score: float  # 0.0 to 1.0
    issues: List[str]
    warnings: List[str]
    metadata: Dict


class ContentValidator:
    """Validates AI-generated content for quality and relevance"""
    
    def __init__(self):
        # Hallucination indicators
        self.hallucination_patterns = [
            r'as an ai',
            r'i cannot',
            r'i don\'t have',
            r'i apologize',
            r'i\'m sorry',
            r'according to my knowledge cutoff',
            r'i don\'t actually',
        ]
        
        # Generic/low-quality indicators
        self.generic_patterns = [
            r'this is a topic',
            r'this subject',
            r'it is important to note',
            r'in general',
            r'basically',
        ]
        
        # Minimum quality thresholds
        self.min_word_count = 20
        self.max_word_count = 500
        self.min_sentence_count = 2
        self.min_quality_score = 0.5
    
    def validate_explanation(
        self, 
        explanation: str, 
        subtopic: str, 
        topic: str,
        education_level: str
    ) -> ValidationResult:
        """
        Validate an explanation for quality and relevance
        
        Args:
            explanation: The generated explanation text
            subtopic: The subtopic being explained
            topic: The main topic
            education_level: Target education level
        
        Returns:
            ValidationResult with quality score and issues
        """
        issues = []
        warnings = []
        metadata = {}
        
        # Basic checks
        if not explanation or not explanation.strip():
            return ValidationResult(
                is_valid=False,
                quality_score=0.0,
                issues=["Empty explanation"],
                warnings=[],
                metadata={}
            )
        
        explanation_lower = explanation.lower()
        
        # Check for hallucination patterns
        hallucination_found = False
        for pattern in self.hallucination_patterns:
            if re.search(pattern, explanation_lower):
                issues.append(f"Hallucination detected: '{pattern}'")
                hallucination_found = True
        
        # Check for generic content
        generic_count = 0
        for pattern in self.generic_patterns:
            if re.search(pattern, explanation_lower):
                generic_count += 1
        
        if generic_count > 2:
            warnings.append("Content appears generic or low-quality")
        
        # Word count validation
        words = explanation.split()
        word_count = len(words)
        metadata['word_count'] = word_count
        
        if word_count < self.min_word_count:
            issues.append(f"Explanation too short ({word_count} words, minimum {self.min_word_count})")
        elif word_count > self.max_word_count:
            warnings.append(f"Explanation very long ({word_count} words)")
        
        # Sentence count validation
        sentences = re.split(r'[.!?]+', explanation)
        sentence_count = len([s for s in sentences if s.strip()])
        metadata['sentence_count'] = sentence_count
        
        if sentence_count < self.min_sentence_count:
            issues.append(f"Too few sentences ({sentence_count})")
        
        # Check relevance to subtopic
        subtopic_words = set(subtopic.lower().split())
        explanation_words = set(explanation_lower.split())
        
        # Remove common words
        common_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with'}
        subtopic_words -= common_words
        
        if subtopic_words:
            overlap = subtopic_words & explanation_words
            relevance_ratio = len(overlap) / len(subtopic_words)
            metadata['relevance_ratio'] = relevance_ratio
            
            if relevance_ratio < 0.2:
                warnings.append(f"Low relevance to subtopic (only {len(overlap)} key words match)")
        
        # Check for proper formatting
        if explanation.strip().startswith('#'):
            warnings.append("Contains markdown headers (should be plain text)")
        
        if '```' in explanation:
            warnings.append("Contains code blocks (may not be appropriate)")
        
        # Calculate quality score
        quality_score = self._calculate_quality_score(
            word_count=word_count,
            sentence_count=sentence_count,
            has_hallucination=hallucination_found,
            generic_count=generic_count,
            relevance_ratio=metadata.get('relevance_ratio', 0.5)
        )
        
        metadata['quality_score'] = quality_score
        
        # Determine if valid
        is_valid = (
            not hallucination_found and
            len(issues) == 0 and
            quality_score >= self.min_quality_score
        )
        
        return ValidationResult(
            is_valid=is_valid,
            quality_score=quality_score,
            issues=issues,
            warnings=warnings,
            metadata=metadata
        )
    
    def _calculate_quality_score(
        self,
        word_count: int,
        sentence_count: int,
        has_hallucination: bool,
        generic_count: int,
        relevance_ratio: float
    ) -> float:
        """Calculate overall quality score (0.0 to 1.0)"""
        
        if has_hallucination:
            return 0.0
        
        score = 1.0
        
        # Word count scoring (optimal range: 50-200 words)
        if word_count < self.min_word_count:
            score -= 0.5
        elif word_count < 50:
            score -= 0.2
        elif word_count > 300:
            score -= 0.1
        
        # Sentence structure scoring
        if sentence_count < 2:
            score -= 0.3
        elif sentence_count > 0:
            avg_words_per_sentence = word_count / sentence_count
            if avg_words_per_sentence < 5:
                score -= 0.2  # Too choppy
            elif avg_words_per_sentence > 40:
                score -= 0.2  # Too complex
        
        # Generic content penalty
        if generic_count > 0:
            score -= min(0.3, generic_count * 0.1)
        
        # Relevance bonus
        score += (relevance_ratio - 0.5) * 0.2  # Boost/penalize based on relevance
        
        return max(0.0, min(1.0, score))
    
    def validate_subtopics(
        self, 
        subtopics: List[str], 
        topic: str,
        expected_count: int = 15
    ) -> ValidationResult:
        """
        Validate a list of generated subtopics
        
        Args:
            subtopics: List of subtopic strings
            topic: Main topic
            expected_count: Expected number of subtopics
        
        Returns:
            ValidationResult
        """
        issues = []
        warnings = []
        metadata = {}
        
        # Check count
        actual_count = len(subtopics)
        metadata['subtopic_count'] = actual_count
        
        if actual_count < expected_count * 0.7:  # 70% threshold
            issues.append(f"Too few subtopics ({actual_count}, expected ~{expected_count})")
        elif actual_count < expected_count * 0.9:
            warnings.append(f"Fewer subtopics than requested ({actual_count}/{expected_count})")
        
        # Check for duplicates
        unique_subtopics = set(s.lower().strip() for s in subtopics)
        if len(unique_subtopics) < len(subtopics):
            duplicate_count = len(subtopics) - len(unique_subtopics)
            issues.append(f"Found {duplicate_count} duplicate subtopics")
        
        # Check for empty or very short subtopics
        short_subtopics = [s for s in subtopics if len(s.strip()) < 3]
        if short_subtopics:
            issues.append(f"Found {len(short_subtopics)} empty or too-short subtopics")
        
        # Check for overly long subtopics
        long_subtopics = [s for s in subtopics if len(s.split()) > 8]
        if long_subtopics:
            warnings.append(f"Found {len(long_subtopics)} overly long subtopics (>8 words)")
        
        # Calculate quality score
        quality_score = 1.0
        if issues:
            quality_score -= len(issues) * 0.2
        if warnings:
            quality_score -= len(warnings) * 0.1
        
        quality_score = max(0.0, min(1.0, quality_score))
        metadata['quality_score'] = quality_score
        
        is_valid = len(issues) == 0 and quality_score >= 0.6
        
        return ValidationResult(
            is_valid=is_valid,
            quality_score=quality_score,
            issues=issues,
            warnings=warnings,
            metadata=metadata
        )
    
    def validate_topic(self, topic: str) -> ValidationResult:
        """
        Validate a topic extracted from an image
        
        Args:
            topic: The extracted topic string
        
        Returns:
            ValidationResult
        """
        issues = []
        warnings = []
        metadata = {}
        
        if not topic or not topic.strip():
            return ValidationResult(
                is_valid=False,
                quality_score=0.0,
                issues=["Empty topic"],
                warnings=[],
                metadata={}
            )
        
        # Word count check
        word_count = len(topic.split())
        metadata['word_count'] = word_count
        
        if word_count < 1:
            issues.append("Topic is empty")
        elif word_count > 10:
            warnings.append(f"Topic is very long ({word_count} words)")
        
        # Check for sentence-like structure (should be short phrase)
        if topic.endswith('.') or topic.endswith('!'):
            warnings.append("Topic contains sentence punctuation (should be a phrase)")
        
        # Check for AI refusal patterns
        topic_lower = topic.lower()
        for pattern in self.hallucination_patterns:
            if re.search(pattern, topic_lower):
                issues.append("AI refusal detected in topic")
                break
        
        quality_score = 1.0 if len(issues) == 0 else 0.3
        
        return ValidationResult(
            is_valid=len(issues) == 0,
            quality_score=quality_score,
            issues=issues,
            warnings=warnings,
            metadata=metadata
        )


def get_content_validator() -> ContentValidator:
    """Get singleton content validator instance"""
    return ContentValidator()
