__version__ = "1.0.0"
__author__ = "Équipe SnapLearn"

from .universal_document_processor import UniversalDocumentProcessor
from .amu_knowledge_base import AMUKnowledgeBase
from .audio_script_generator import AudioScriptGenerator
from .audio_generator import AudioGenerator
from .interactive_quiz_manager import QuizManager

__all__ = [
    'UniversalDocumentProcessor',
    'AMUKnowledgeBase',
    'AudioScriptGenerator',
    'AudioGenerator',
    'QuizManager'
]
