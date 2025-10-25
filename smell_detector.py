import os
from tree_sitter import Language, Parser
import tree_sitter_python as tspython
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict
import re


@dataclass
class CodeSmell:
    """Represents a detected code smell"""
    smell_type: str
    severity: str  # 'low', 'medium', 'high'
    location: tuple  # (line, column)
    function_name: str
    message: str
    details: Dict


class CodeSmellDetector:
    def __init__(self):
        self.parser = Parser()
        PY_LANGUAGE = Language(tspython.language())
        self.parser.language= PY_LANGUAGE

    def parse_file(self, file_path: str) -> tuple:
        """Parse a Python file and return the tree and source code"""
        with open(file_path, 'r', encoding='utf-8') as f:
            source_code = f.read()

        tree = self.parser.parse(bytes(source_code, 'utf8'))
        return tree, source_code

    def get_function_nodes(self, tree):
        """Extract all function definition nodes from the tree"""
        functions = []

        def traverse(node):
            if node.type == 'function_definition':
                functions.append(node)
            for child in node.children:
                traverse(child)

        traverse(tree.root_node)
        return functions

    def get_function_name(self, func_node):
        """Extract function name from function node"""
        for child in func_node.children:
            if child.type == 'identifier':
                return child.text.decode('utf8')
        return 'unknown'

    def get_class_methods(self, class_node):
        """
        Extract all method nodes from a class
        """
        methods = []

        for child in class_node.children:

            if child.type == 'block':
                for item in child.children:
                    if item.type == 'function_definition':
                        methods.append(item)

        return methods

    def _get_call_name(self, call_node):
        """
        Extract function name from a call node
        """
        for child in call_node.children:
            if child.type == 'attribute':
                for subchild in child.children:
                    if subchild.type == 'identifier':
                        return subchild.text.decode('utf8')
            elif child.type == 'identifier':
                return child.text.decode('utf8')
        return None

    def split_identifier(self, name):
        """
        Split camelCase or snake_case into words
        """
        name = name.replace('_', ' ')

        # Insert space before capital letters
        name = re.sub('([a-z])([A-Z])', r'\1 \2', name)

        # Split and lowercase
        words = name.lower().split()

        return words

    def get_class_name(self, class_node):
        """
        Extract class name from class definition node
        """
        for child in class_node.children:
            if child.type == 'identifier':
                return child.text.decode('utf8')
        return 'UnknownClass'

    def get_class_nodes(self, tree):
        """
        Extract all class definition nodes from tree
        Similar to get_function_nodes but for classes
        """
        classes = []

        def traverse(node):
            if node.type == 'class_definition':
                classes.append(node)
            for child in node.children:
                traverse(child)

        traverse(tree.root_node)
        return classes

