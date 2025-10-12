"""
DSS File Validator
Validates DSS file changes to ensure only value modifications are allowed,
not structural changes (adding/removing components).
"""

import re
import logging
from typing import Dict, List, Tuple, Any

logger = logging.getLogger(__name__)


class DSSComponent:
    """Represents a component in the DSS file"""
    def __init__(self, line_number: int, component_type: str, component_name: str, full_line: str):
        self.line_number = line_number
        self.component_type = component_type
        self.component_name = component_name
        self.full_line = full_line
        self.parameters = self._parse_parameters(full_line)

    def _parse_parameters(self, line: str) -> Dict[str, str]:
        """Parse parameters from a DSS component line"""
        params = {}
        # Remove "New ComponentType.ComponentName" part
        parts = line.split(maxsplit=1)
        if len(parts) < 2:
            return params

        param_string = parts[1] if len(parts) > 1 else ""

        # Parse parameters (format: key=value or ~key=value)
        param_pattern = r'~?\s*(\w+)\s*=\s*([^\s~]+(?:\s+[^\s~]+)*?)(?=\s+~?\s*\w+\s*=|$)'
        matches = re.findall(param_pattern, param_string)

        for key, value in matches:
            params[key.strip()] = value.strip()

        return params

    def __repr__(self):
        return f"DSSComponent({self.component_type}.{self.component_name})"


class DSSValidator:
    """Validates DSS file changes"""

    def __init__(self):
        self.errors = []
        self.warnings = []

    def parse_dss_file(self, content: str) -> Dict[str, DSSComponent]:
        """Parse DSS file and extract all components"""
        components = {}

        lines = content.split('\n')
        for i, line in enumerate(lines, start=1):
            line = line.strip()

            # Skip comments and empty lines
            if not line or line.startswith('!'):
                continue

            # Match component definitions (New ComponentType.ComponentName)
            match = re.match(r'^New\s+(\w+)\.(\S+)', line, re.IGNORECASE)
            if match:
                component_type = match.group(1)
                component_name = match.group(2)
                full_line = line

                # Handle multi-line definitions (lines starting with ~)
                j = i
                while j < len(lines):
                    next_line = lines[j].strip()
                    if next_line.startswith('~'):
                        full_line += ' ' + next_line
                        j += 1
                    else:
                        break

                component_key = f"{component_type}.{component_name}".lower()
                components[component_key] = DSSComponent(i, component_type, component_name, full_line)

        return components

    def validate_changes(self, original_content: str, new_content: str) -> Tuple[bool, List[str], List[str]]:
        """
        Validate changes between original and new DSS file content.

        Returns:
            Tuple[bool, List[str], List[str]]: (is_valid, errors, warnings)
        """
        self.errors = []
        self.warnings = []

        # Parse both files
        original_components = self.parse_dss_file(original_content)
        new_components = self.parse_dss_file(new_content)

        # Check for added components
        added_components = set(new_components.keys()) - set(original_components.keys())
        if added_components:
            self.errors.append(
                f"Cannot add new components. Found {len(added_components)} new components: "
                f"{', '.join(list(added_components)[:5])}"
            )

        # Check for removed components
        removed_components = set(original_components.keys()) - set(new_components.keys())
        if removed_components:
            self.errors.append(
                f"Cannot remove components. Found {len(removed_components)} removed components: "
                f"{', '.join(list(removed_components)[:5])}"
            )

        # Validate parameter changes for existing components
        common_components = set(original_components.keys()) & set(new_components.keys())
        for component_key in common_components:
            original_comp = original_components[component_key]
            new_comp = new_components[component_key]

            # Check if component type changed
            if original_comp.component_type.lower() != new_comp.component_type.lower():
                self.errors.append(
                    f"Component {component_key}: Cannot change component type "
                    f"from {original_comp.component_type} to {new_comp.component_type}"
                )

            # Check parameter changes
            original_params = original_comp.parameters
            new_params = new_comp.parameters

            # Check for added parameters
            added_params = set(new_params.keys()) - set(original_params.keys())
            if added_params:
                self.warnings.append(
                    f"Component {component_key}: Added new parameters: {', '.join(added_params)}"
                )

            # Check for removed parameters
            removed_params = set(original_params.keys()) - set(new_params.keys())
            if removed_params:
                self.warnings.append(
                    f"Component {component_key}: Removed parameters: {', '.join(removed_params)}"
                )

            # Validate parameter value changes
            for param_key in set(original_params.keys()) & set(new_params.keys()):
                original_value = original_params[param_key]
                new_value = new_params[param_key]

                if original_value != new_value:
                    # Log significant changes
                    logger.info(
                        f"Component {component_key}, parameter {param_key}: "
                        f"{original_value} -> {new_value}"
                    )

        # Check for non-component changes (commands like Clear, Set, Solve)
        original_commands = self._extract_commands(original_content)
        new_commands = self._extract_commands(new_content)

        if original_commands != new_commands:
            self.warnings.append(
                "DSS commands (Clear, Set, Solve, etc.) have been modified. "
                "This may affect simulation behavior."
            )

        is_valid = len(self.errors) == 0
        return is_valid, self.errors, self.warnings

    def _extract_commands(self, content: str) -> List[str]:
        """Extract DSS commands (non-component definitions)"""
        commands = []
        for line in content.split('\n'):
            line = line.strip()
            if not line or line.startswith('!'):
                continue

            # Commands are lines that don't start with "New" or "~"
            if not re.match(r'^(New|~)', line, re.IGNORECASE):
                commands.append(line.lower())

        return commands

    def validate_syntax(self, content: str) -> Tuple[bool, List[str]]:
        """
        Validate basic DSS file syntax.

        Returns:
            Tuple[bool, List[str]]: (is_valid, errors)
        """
        errors = []

        # Check if file contains at least one circuit definition
        if not re.search(r'^New\s+Circuit\.\w+', content, re.MULTILINE | re.IGNORECASE):
            errors.append("DSS file must contain at least one Circuit definition")

        # Check for balanced parentheses and brackets
        open_parens = content.count('(')
        close_parens = content.count(')')
        if open_parens != close_parens:
            errors.append(f"Unbalanced parentheses: {open_parens} '(' vs {close_parens} ')'")

        open_brackets = content.count('[')
        close_brackets = content.count(']')
        if open_brackets != close_brackets:
            errors.append(f"Unbalanced brackets: {open_brackets} '[' vs {close_brackets} ']'")

        # Check for common syntax errors
        lines = content.split('\n')
        for i, line in enumerate(lines, start=1):
            line = line.strip()
            if not line or line.startswith('!'):
                continue

            # Check for invalid characters in component names
            match = re.match(r'^New\s+(\w+)\.(\S+)', line, re.IGNORECASE)
            if match:
                component_name = match.group(2)
                if not re.match(r'^[\w\-_]+', component_name):
                    errors.append(
                        f"Line {i}: Invalid component name '{component_name}'. "
                        "Use only alphanumeric characters, hyphens, and underscores."
                    )

        is_valid = len(errors) == 0
        return is_valid, errors


def validate_dss_file_changes(original_content: str, new_content: str) -> Dict[str, Any]:
    """
    Convenience function to validate DSS file changes.

    Returns:
        Dict with validation results
    """
    validator = DSSValidator()

    # Validate syntax first
    syntax_valid, syntax_errors = validator.validate_syntax(new_content)
    if not syntax_valid:
        return {
            'valid': False,
            'errors': syntax_errors,
            'warnings': [],
            'message': 'DSS file contains syntax errors'
        }

    # Validate changes
    changes_valid, errors, warnings = validator.validate_changes(original_content, new_content)

    return {
        'valid': changes_valid,
        'errors': errors,
        'warnings': warnings,
        'message': 'Validation successful' if changes_valid else 'Validation failed'
    }
