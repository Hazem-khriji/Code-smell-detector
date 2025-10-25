import os
from tree_sitter import Language, Parser
import tree_sitter_python as tspython
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict
import smell_detector


@dataclass
class CodeSmell:
    """Represents a detected code smell"""
    smell_type: str
    severity: str  # 'low', 'medium', 'high'
    location: tuple  # (line, column)
    function_name: str
    message: str
    details: Dict


class PrimitiveCodeSmellDetector(smell_detector.CodeSmellDetector):
    def __init__(self):
        super().__init__()

    def count_lines(self, node):
        """Count non-empty lines in a node"""
        start_line = node.start_point[0]
        end_line = node.end_point[0]
        return end_line - start_line + 1

    def count_parameters(self, func_node):
        """Count the number of parameters in a function"""
        for child in func_node.children:
            if child.type == 'parameters':
                # Count children that are identifiers or typed parameters
                params = [c for c in child.children
                          if c.type in ('identifier', 'typed_parameter', 'default_parameter')]
                return len(params)
        return 0

    def calculate_nesting_depth(self, node, current_depth=0):
        """Calculate maximum nesting depth of control structures"""
        max_depth = current_depth

        # These are control flow structures that increase nesting
        nesting_nodes = {'if_statement', 'for_statement', 'while_statement',
                         'with_statement', 'try_statement'}

        for child in node.children:
            if child.type in nesting_nodes:
                child_depth = self.calculate_nesting_depth(child, current_depth + 1)
                max_depth = max(max_depth, child_depth)
            else:
                child_depth = self.calculate_nesting_depth(child, current_depth)
                max_depth = max(max_depth, child_depth)

        return max_depth

    def detect_long_method(self, func_node, threshold=50):
        """Detect if a method is too long"""
        line_count = self.count_lines(func_node)

        if line_count > threshold:
            return CodeSmell(
                smell_type='long_method',
                severity='high' if line_count > 100 else 'medium',
                location=func_node.start_point,
                function_name=self.get_function_name(func_node),
                message=f'Function is {line_count} lines long (threshold: {threshold})',
                details={'line_count': line_count, 'threshold': threshold}
            )
        return None

    def detect_too_many_parameters(self, func_node, threshold=5):
        """Detect if a function has too many parameters"""
        param_count = self.count_parameters(func_node)

        if param_count > threshold:
            return CodeSmell(
                smell_type='too_many_parameters',
                severity='medium' if param_count <= 7 else 'high',
                location=func_node.start_point,
                function_name=self.get_function_name(func_node),
                message=f'Function has {param_count} parameters (threshold: {threshold})',
                details={'param_count': param_count, 'threshold': threshold}
            )
        return None

    def detect_deep_nesting(self, func_node, threshold=4):
        """Detect if a function has too deep nesting"""
        max_depth = self.calculate_nesting_depth(func_node)

        if max_depth > threshold:
            return CodeSmell(
                smell_type='deep_nesting',
                severity='high' if max_depth > 5 else 'medium',
                location=func_node.start_point,
                function_name=self.get_function_name(func_node),
                message=f'Function has nesting depth of {max_depth} (threshold: {threshold})',
                details={'nesting_depth': max_depth, 'threshold': threshold}
            )
        return None

    def analyze_file(self, file_path: str) -> List[CodeSmell]:
        """Analyze a single Python file for code smells"""
        try:
            tree, source_code = self.parse_file(file_path)
            functions = self.get_function_nodes(tree)

            smells = []

            for func in functions:
                # Run all detectors
                detectors = [
                    self.detect_long_method,
                    self.detect_too_many_parameters,
                    self.detect_deep_nesting
                ]

                for detector in detectors:
                    smell = detector(func)
                    if smell:
                        smells.append(smell)

            return smells

        except Exception as e:
            print(f"Error analyzing {file_path}: {e}")
            return []

    def analyze_directory(self, directory_path: str) -> Dict[str, List[CodeSmell]]:
        """Analyze all Python files in a directory"""
        results = {}

        path = Path(directory_path)
        for py_file in path.rglob('*.py'):
            smells = self.analyze_file(str(py_file))
            if smells:
                results[str(py_file)] = smells

        return results

    def print_report(self, results: Dict[str, List[CodeSmell]]):
        """Print a formatted report of detected code smells"""
        total_smells = sum(len(smells) for smells in results.values())

        print("\n" + "=" * 80)
        print(f"CODE SMELL DETECTION REPORT")
        print("=" * 80)
        print(f"Total files analyzed: {len(results)}")
        print(f"Total code smells found: {total_smells}")
        print("=" * 80 + "\n")

        for file_path, smells in results.items():
            print(f"\n📄 File: {file_path}")
            print(f"   Found {len(smells)} smell(s)\n")

            for smell in smells:
                severity_emoji = {'low': '🟢', 'medium': '🟡', 'high': '🔴'}
                emoji = severity_emoji.get(smell.severity, '⚪')

                print(f"   {emoji} {smell.smell_type.upper()} [{smell.severity}]")
                print(f"      Function: {smell.function_name}")
                print(f"      Location: Line {smell.location[0] + 1}, Column {smell.location[1]}")
                print(f"      Message: {smell.message}")
                print()


def main():
    """Main entry point"""
    import sys

    detector = PrimitiveCodeSmellDetector()

    # Example usage
    if len(sys.argv) < 2:
        print("Usage: python code_smell_detector.py <file_or_directory>")
        print("\nExample:")
        print("  python code_smell_detector.py my_script.py")
        print("  python code_smell_detector.py ./my_project")
        return

    target = sys.argv[1]

    if os.path.isfile(target):
        # Analyze single file
        smells = detector.analyze_file(target)
        results = {target: smells} if smells else {}
    elif os.path.isdir(target):
        # Analyze directory
        results = detector.analyze_directory(target)
    else:
        print(f"Error: {target} is not a valid file or directory")
        return

    if results:
        detector.print_report(results)
    else:
        print("✅ No code smells detected!")


if __name__ == "__main__":
    main()