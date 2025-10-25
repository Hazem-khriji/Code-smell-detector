import os

from sentence_transformers import SentenceTransformer
from tree_sitter import Language, Parser
import tree_sitter_python as tspython
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict

import smell_detector
@dataclass
class SOLIDCodeSmell:
    """Represents a detected code smell"""
    smell_type: str
    severity: str  # 'low', 'medium', 'high'
    location: tuple  # (line, column)
    function_name: str
    message: str
    details: Dict


class SOLIDCodeSmellDetector(smell_detector.CodeSmellDetector):
    def __init__(self):
        super().__init__()
        #self.embedder = SentenceTransformer('all-MiniLM-L6-v2')

