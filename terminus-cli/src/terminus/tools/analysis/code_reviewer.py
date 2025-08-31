import ast
import logging
import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from pydantic_ai import RunContext
from terminus.core.session import session

log = logging.getLogger(__name__)

@dataclass
class CodeIssue:
    """Represents a code quality issue."""
    severity: str  # 'critical', 'major', 'minor', 'info'
    type: str      # 'complexity', 'length', 'duplication', 'smell', 'security'
    file_path: str
    line_number: int
    function_name: str
    message: str
    suggestion: str
    example: Optional[str] = None
    metric_value: Optional[int] = None

@dataclass
class CodeMetrics:
    """Code quality metrics for a function or file."""
    lines_of_code: int
    cyclomatic_complexity: int
    cognitive_complexity: int
    parameter_count: int
    nesting_depth: int
    maintainability_index: float

class CodeAnalyzer:
    """Analyzes code for quality issues and refactoring opportunities."""
    
    def __init__(self):
        self.issues = []
        self.metrics = {}
        
        # Configurable thresholds
        self.thresholds = {
            'max_function_length': 50,
            'max_complexity': 10,
            'max_cognitive_complexity': 15,
            'max_parameters': 5,
            'max_nesting': 4,
            'min_maintainability': 20
        }
    
    def analyze_file(self, file_path: str) -> Tuple[List[CodeIssue], Dict[str, Any]]:
        """Analyze a single file for code quality issues."""
        self.issues = []
        self.metrics = {}
        
        try:
            path = Path(file_path)
            if not path.exists():
                return [], {"error": f"File not found: {file_path}"}
            
            content = path.read_text(encoding='utf-8')
            file_ext = path.suffix.lower()
            
            if file_ext == '.py':
                self._analyze_python_file(content, file_path)
            elif file_ext in ['.js', '.ts', '.jsx', '.tsx']:
                self._analyze_javascript_file(content, file_path)
            else:
                return [], {"error": f"Unsupported file type: {file_ext}"}
            
            # Calculate overall file metrics
            file_metrics = self._calculate_file_metrics(content, file_path)
            
            return self.issues, {
                "file_metrics": file_metrics,
                "function_metrics": self.metrics,
                "issues_by_severity": self._group_issues_by_severity(),
                "suggestions_count": len(self.issues)
            }
            
        except Exception as e:
            log.error(f"Error analyzing file {file_path}: {e}")
            return [], {"error": str(e)}
    
    def _analyze_python_file(self, content: str, file_path: str):
        """Analyze Python file using AST."""
        try:
            tree = ast.parse(content)
            
            # Extract functions and classes
            functions = []
            classes = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    functions.append(node)
                elif isinstance(node, ast.ClassDef):
                    classes.append(node)
            
            # Analyze each function
            for func in functions:
                self._analyze_python_function(func, content, file_path)
            
            # Analyze for duplicates
            self._detect_code_duplication(content, file_path, 'python')
            
            # Analyze imports and dependencies
            self._analyze_python_imports(tree, file_path)
            
        except SyntaxError as e:
            self.issues.append(CodeIssue(
                severity='critical',
                type='syntax',
                file_path=file_path,
                line_number=e.lineno or 1,
                function_name='',
                message=f"Syntax error: {e.msg}",
                suggestion="Fix the syntax error before proceeding with analysis"
            ))
    
    def _analyze_python_function(self, func_node: ast.FunctionDef, content: str, file_path: str):
        """Analyze a Python function for quality issues."""
        func_name = func_node.name
        start_line = func_node.lineno
        
        # Calculate metrics
        func_lines = self._get_function_lines(func_node, content)
        complexity = self._calculate_cyclomatic_complexity(func_node)
        cognitive_complexity = self._calculate_cognitive_complexity(func_node)
        param_count = len(func_node.args.args)
        nesting_depth = self._calculate_nesting_depth(func_node)
        
        metrics = CodeMetrics(
            lines_of_code=len(func_lines),
            cyclomatic_complexity=complexity,
            cognitive_complexity=cognitive_complexity,
            parameter_count=param_count,
            nesting_depth=nesting_depth,
            maintainability_index=self._calculate_maintainability_index(
                len(func_lines), complexity, cognitive_complexity
            )
        )
        
        self.metrics[func_name] = metrics
        
        # Check for issues
        self._check_function_length(func_name, len(func_lines), start_line, file_path)
        self._check_complexity(func_name, complexity, start_line, file_path)
        self._check_cognitive_complexity(func_name, cognitive_complexity, start_line, file_path)
        self._check_parameter_count(func_name, param_count, start_line, file_path)
        self._check_nesting_depth(func_name, nesting_depth, start_line, file_path)
        self._check_function_naming(func_name, start_line, file_path)
        
        # Check for code smells
        self._detect_code_smells(func_node, func_name, file_path)
    
    def _analyze_javascript_file(self, content: str, file_path: str):
        """Analyze JavaScript/TypeScript file using regex patterns."""
        lines = content.split('\n')
        
        # Find functions using regex (basic analysis)
        function_pattern = r'^\s*(?:function\s+(\w+)|(?:const|let|var)\s+(\w+)\s*=\s*(?:function|\([^)]*\)\s*=>)|(\w+)\s*:\s*function|\s*(\w+)\s*\([^)]*\)\s*{)'
        
        for i, line in enumerate(lines):
            match = re.search(function_pattern, line)
            if match:
                func_name = next(group for group in match.groups() if group) or 'anonymous'
                self._analyze_js_function_block(lines, i, func_name, file_path)
        
        # Detect duplicates
        self._detect_code_duplication(content, file_path, 'javascript')
    
    def _analyze_js_function_block(self, lines: List[str], start_idx: int, func_name: str, file_path: str):
        """Analyze a JavaScript function block."""
        # Simple brace counting to find function end
        brace_count = 0
        func_lines = []
        started = False
        
        for i in range(start_idx, len(lines)):
            line = lines[i]
            if '{' in line:
                started = True
                brace_count += line.count('{')
            if started:
                func_lines.append(line)
                brace_count -= line.count('}')
                if brace_count == 0:
                    break
        
        if func_lines:
            # Basic metrics for JS
            func_length = len([line for line in func_lines if line.strip()])
            complexity = self._estimate_js_complexity(func_lines)
            
            # Check issues
            self._check_function_length(func_name, func_length, start_idx + 1, file_path)
            if complexity > self.thresholds['max_complexity']:
                self._check_complexity(func_name, complexity, start_idx + 1, file_path)
    
    def _get_function_lines(self, func_node: ast.FunctionDef, content: str) -> List[str]:
        """Get the lines of code for a function."""
        lines = content.split('\n')
        start = func_node.lineno - 1
        
        # Find the end of the function (simple heuristic)
        end = start + 1
        indent_level = len(lines[start]) - len(lines[start].lstrip())
        
        for i in range(start + 1, len(lines)):
            line = lines[i]
            if line.strip() and (len(line) - len(line.lstrip())) <= indent_level:
                break
            end = i + 1
        
        return [line for line in lines[start:end] if line.strip()]
    
    def _calculate_cyclomatic_complexity(self, node: ast.AST) -> int:
        """Calculate cyclomatic complexity of a function."""
        complexity = 1  # Base complexity
        
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1
            elif isinstance(child, (ast.With, ast.AsyncWith)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                # And/Or operators add complexity
                complexity += len(child.values) - 1
        
        return complexity
    
    def _calculate_cognitive_complexity(self, node: ast.AST) -> int:
        """Calculate cognitive complexity (how hard to understand)."""
        complexity = 0
        nesting_level = 0
        
        def visit_node(node, level):
            nonlocal complexity
            
            if isinstance(node, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1 + level
                level += 1
            elif isinstance(node, ast.ExceptHandler):
                complexity += 1 + level
                level += 1
            elif isinstance(node, ast.BoolOp):
                complexity += len(node.values) - 1
            
            for child in ast.iter_child_nodes(node):
                visit_node(child, level)
        
        for child in ast.iter_child_nodes(node):
            visit_node(child, nesting_level)
        
        return complexity
    
    def _calculate_nesting_depth(self, node: ast.AST) -> int:
        """Calculate maximum nesting depth."""
        def get_depth(node, current_depth=0):
            max_depth = current_depth
            
            if isinstance(node, (ast.If, ast.While, ast.For, ast.AsyncFor, ast.With, ast.AsyncWith, ast.Try)):
                current_depth += 1
            
            for child in ast.iter_child_nodes(node):
                child_depth = get_depth(child, current_depth)
                max_depth = max(max_depth, child_depth)
            
            return max_depth
        
        return get_depth(node)
    
    def _calculate_maintainability_index(self, loc: int, complexity: int, cognitive: int) -> float:
        """Calculate maintainability index (0-100, higher is better)."""
        if loc == 0:
            return 100.0
        
        # Simplified maintainability index
        volume = loc * 2.4  # Simplified Halstead volume
        mi = max(0, (171 - 5.2 * (volume ** 0.23) - 0.23 * complexity - 16.2 * (loc ** 0.5)) * 100 / 171)
        return round(mi, 2)
    
    def _estimate_js_complexity(self, lines: List[str]) -> int:
        """Estimate complexity for JavaScript code."""
        complexity = 1
        complexity_keywords = ['if', 'else if', 'while', 'for', 'switch', 'case', 'catch', '&&', '||']
        
        for line in lines:
            for keyword in complexity_keywords:
                if keyword in line:
                    complexity += line.count(keyword)
        
        return complexity
    
    def _check_function_length(self, func_name: str, length: int, line_num: int, file_path: str):
        """Check if function is too long."""
        if length > self.thresholds['max_function_length']:
            severity = 'critical' if length > self.thresholds['max_function_length'] * 2 else 'major'
            
            self.issues.append(CodeIssue(
                severity=severity,
                type='length',
                file_path=file_path,
                line_number=line_num,
                function_name=func_name,
                message=f"Function '{func_name}' is too long ({length} lines)",
                suggestion=f"Consider breaking this function into smaller, more focused functions. "
                          f"Aim for functions under {self.thresholds['max_function_length']} lines.",
                example="# Example refactoring:\n"
                       "def large_function():\n"
                       "    # Split into:\n"
                       "    data = prepare_data()\n"
                       "    result = process_data(data)\n"
                       "    return format_result(result)",
                metric_value=length
            ))
    
    def _check_complexity(self, func_name: str, complexity: int, line_num: int, file_path: str):
        """Check if function is too complex."""
        if complexity > self.thresholds['max_complexity']:
            severity = 'critical' if complexity > self.thresholds['max_complexity'] * 1.5 else 'major'
            
            self.issues.append(CodeIssue(
                severity=severity,
                type='complexity',
                file_path=file_path,
                line_number=line_num,
                function_name=func_name,
                message=f"Function '{func_name}' has high cyclomatic complexity ({complexity})",
                suggestion="Reduce complexity by extracting nested logic into separate functions, "
                          "using early returns, or simplifying conditional logic.",
                example="# Instead of:\n"
                       "if condition1:\n"
                       "    if condition2:\n"
                       "        if condition3:\n"
                       "            do_something()\n"
                       "# Try:\n"
                       "if not condition1:\n"
                       "    return\n"
                       "if not condition2:\n"
                       "    return\n"
                       "if condition3:\n"
                       "    do_something()",
                metric_value=complexity
            ))
    
    def _check_cognitive_complexity(self, func_name: str, cognitive: int, line_num: int, file_path: str):
        """Check cognitive complexity."""
        if cognitive > self.thresholds['max_cognitive_complexity']:
            self.issues.append(CodeIssue(
                severity='major',
                type='complexity',
                file_path=file_path,
                line_number=line_num,
                function_name=func_name,
                message=f"Function '{func_name}' has high cognitive complexity ({cognitive})",
                suggestion="Reduce cognitive load by simplifying nested conditions, "
                          "extracting complex expressions, and reducing nesting levels.",
                metric_value=cognitive
            ))
    
    def _check_parameter_count(self, func_name: str, param_count: int, line_num: int, file_path: str):
        """Check if function has too many parameters."""
        if param_count > self.thresholds['max_parameters']:
            self.issues.append(CodeIssue(
                severity='major',
                type='smell',
                file_path=file_path,
                line_number=line_num,
                function_name=func_name,
                message=f"Function '{func_name}' has too many parameters ({param_count})",
                suggestion="Consider using a configuration object, dataclass, or named parameters "
                          "to group related parameters.",
                example="# Instead of:\n"
                       "def func(a, b, c, d, e, f):\n"
                       "    pass\n"
                       "# Try:\n"
                       "@dataclass\n"
                       "class Config:\n"
                       "    a: int\n"
                       "    b: str\n"
                       "    ...\n"
                       "def func(config: Config):",
                metric_value=param_count
            ))
    
    def _check_nesting_depth(self, func_name: str, depth: int, line_num: int, file_path: str):
        """Check nesting depth."""
        if depth > self.thresholds['max_nesting']:
            self.issues.append(CodeIssue(
                severity='major',
                type='complexity',
                file_path=file_path,
                line_number=line_num,
                function_name=func_name,
                message=f"Function '{func_name}' has deep nesting ({depth} levels)",
                suggestion="Reduce nesting by using early returns, extracting nested logic, "
                          "or using guard clauses.",
                example="# Instead of deep nesting:\n"
                       "if condition1:\n"
                       "    if condition2:\n"
                       "        if condition3:\n"
                       "            return result\n"
                       "# Use guard clauses:\n"
                       "if not condition1:\n"
                       "    return None\n"
                       "if not condition2:\n"
                       "    return None\n"
                       "if condition3:\n"
                       "    return result",
                metric_value=depth
            ))
    
    def _check_function_naming(self, func_name: str, line_num: int, file_path: str):
        """Check function naming conventions."""
        issues = []
        
        # Check snake_case for Python
        if file_path.endswith('.py') and not re.match(r'^[a-z_][a-z0-9_]*$', func_name):
            if func_name != '__init__' and not func_name.startswith('__'):
                issues.append("Use snake_case for Python function names")
        
        # Check for too short names
        if len(func_name) <= 2 and func_name not in ['go', 'do', 'is', 'as']:
            issues.append("Function name is too short and not descriptive")
        
        # Check for too long names
        if len(func_name) > 50:
            issues.append("Function name is too long")
        
        for issue in issues:
            self.issues.append(CodeIssue(
                severity='minor',
                type='naming',
                file_path=file_path,
                line_number=line_num,
                function_name=func_name,
                message=f"Function '{func_name}': {issue}",
                suggestion="Use descriptive, properly formatted function names that clearly "
                          "indicate the function's purpose."
            ))
    
    def _detect_code_smells(self, func_node: ast.FunctionDef, func_name: str, file_path: str):
        """Detect common code smells."""
        # Check for empty functions
        if len(func_node.body) == 1 and isinstance(func_node.body[0], ast.Pass):
            self.issues.append(CodeIssue(
                severity='minor',
                type='smell',
                file_path=file_path,
                line_number=func_node.lineno,
                function_name=func_name,
                message=f"Function '{func_name}' is empty",
                suggestion="Implement the function or remove it if not needed."
            ))
        
        # Check for magic numbers
        for node in ast.walk(func_node):
            if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
                if node.value not in [0, 1, -1] and abs(node.value) > 1:
                    self.issues.append(CodeIssue(
                        severity='minor',
                        type='smell',
                        file_path=file_path,
                        line_number=getattr(node, 'lineno', func_node.lineno),
                        function_name=func_name,
                        message=f"Magic number {node.value} found",
                        suggestion="Replace magic numbers with named constants.",
                        example=f"# Instead of: value * {node.value}\n"
                               f"# Use: MAX_RETRIES = {node.value}\n"
                               f"#      value * MAX_RETRIES"
                    ))
    
    def _analyze_python_imports(self, tree: ast.AST, file_path: str):
        """Analyze imports for issues."""
        imports = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ''
                for alias in node.names:
                    imports.append(f"{module}.{alias.name}")
        
        # Check for unused imports (basic check)
        # This would need more sophisticated analysis in a real implementation
        
        # Check for wildcard imports
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    if alias.name == '*':
                        self.issues.append(CodeIssue(
                            severity='major',
                            type='smell',
                            file_path=file_path,
                            line_number=node.lineno,
                            function_name='',
                            message="Wildcard import found",
                            suggestion="Avoid wildcard imports. Import specific names or use qualified imports.",
                            example="# Instead of: from module import *\n"
                                   "# Use: from module import specific_function\n"
                                   "# Or: import module"
                        ))
    
    def _detect_code_duplication(self, content: str, file_path: str, language: str):
        """Detect code duplication within the file."""
        lines = content.split('\n')
        
        # Simple duplication detection: look for identical line sequences
        min_duplicate_lines = 5
        
        for i in range(len(lines) - min_duplicate_lines):
            sequence = lines[i:i + min_duplicate_lines]
            
            # Skip empty or comment-only sequences
            if all(not line.strip() or line.strip().startswith('#') for line in sequence):
                continue
            
            # Look for this sequence later in the file
            for j in range(i + min_duplicate_lines, len(lines) - min_duplicate_lines):
                if lines[j:j + min_duplicate_lines] == sequence:
                    self.issues.append(CodeIssue(
                        severity='major',
                        type='duplication',
                        file_path=file_path,
                        line_number=i + 1,
                        function_name='',
                        message=f"Code duplication detected (lines {i+1}-{i+min_duplicate_lines} and {j+1}-{j+min_duplicate_lines})",
                        suggestion="Extract duplicate code into a shared function or method.",
                        example="# Extract to a function:\n"
                               "def shared_logic():\n"
                               "    # Common code here\n"
                               "    pass\n"
                               "\n"
                               "# Call from both places:\n"
                               "shared_logic()"
                    ))
                    break
    
    def _calculate_file_metrics(self, content: str, file_path: str) -> Dict[str, Any]:
        """Calculate overall file metrics."""
        lines = content.split('\n')
        total_lines = len(lines)
        code_lines = len([line for line in lines if line.strip() and not line.strip().startswith('#')])
        comment_lines = len([line for line in lines if line.strip().startswith('#')])
        
        return {
            "total_lines": total_lines,
            "code_lines": code_lines,
            "comment_lines": comment_lines,
            "comment_ratio": round(comment_lines / max(code_lines, 1) * 100, 2),
            "blank_lines": total_lines - code_lines - comment_lines
        }
    
    def _group_issues_by_severity(self) -> Dict[str, int]:
        """Group issues by severity level."""
        groups = defaultdict(int)
        for issue in self.issues:
            groups[issue.severity] += 1
        return dict(groups)


async def suggest_refactor(ctx: RunContext, file_path: str) -> str:
    """Analyze code and suggest refactoring opportunities."""
    log.debug(f"suggest_refactor called with file_path: {file_path}")
    
    # Resolve path relative to session working directory
    resolved_path = session.resolve_path(file_path)
    
    if ctx.deps and ctx.deps.display_tool_status:
        await ctx.deps.display_tool_status("Analyzing", str(resolved_path))
    
    analyzer = CodeAnalyzer()
    issues, metrics = analyzer.analyze_file(str(resolved_path))
    
    if "error" in metrics:
        return f"Error analyzing {file_path}: {metrics['error']}"
    
    # Generate comprehensive report
    report = _generate_refactoring_report(file_path, issues, metrics)
    return report


def _generate_refactoring_report(file_path: str, issues: List[CodeIssue], metrics: Dict[str, Any]) -> str:
    """Generate a comprehensive refactoring report."""
    if not issues:
        return f"✅ Great news! No refactoring issues found in {file_path}\n\nCode quality looks good!"
    
    # Sort issues by severity and line number
    severity_order = {'critical': 0, 'major': 1, 'minor': 2, 'info': 3}
    sorted_issues = sorted(issues, key=lambda x: (severity_order[x.severity], x.line_number))
    
    report_lines = [
        f"🔍 **Code Review Report for {file_path}**",
        "",
        f"📊 **Summary**"
    ]
    
    # Add file metrics
    if "file_metrics" in metrics:
        fm = metrics["file_metrics"]
        report_lines.extend([
            f"- Total Lines: {fm['total_lines']}",
            f"- Code Lines: {fm['code_lines']}",
            f"- Comment Ratio: {fm['comment_ratio']}%"
        ])
    
    # Add issue summary
    if "issues_by_severity" in metrics:
        severity_summary = metrics["issues_by_severity"]
        report_lines.extend([
            "",
            f"🚨 **Issues Found: {len(issues)}**"
        ])
        
        for severity in ['critical', 'major', 'minor', 'info']:
            if severity in severity_summary:
                count = severity_summary[severity]
                emoji = {'critical': '🔴', 'major': '🟠', 'minor': '🟡', 'info': '🔵'}[severity]
                report_lines.append(f"- {emoji} {severity.title()}: {count}")
    
    report_lines.extend([
        "",
        "🛠️ **Detailed Issues & Suggestions**",
        ""
    ])
    
    # Add detailed issues
    current_severity = None
    for issue in sorted_issues:
        if issue.severity != current_severity:
            current_severity = issue.severity
            emoji = {'critical': '🔴', 'major': '🟠', 'minor': '🟡', 'info': '🔵'}[issue.severity]
            report_lines.append(f"{emoji} **{issue.severity.upper()} ISSUES**")
            report_lines.append("")
        
        # Format issue
        function_info = f" in `{issue.function_name}()`" if issue.function_name else ""
        metric_info = f" ({issue.metric_value})" if issue.metric_value else ""
        
        report_lines.extend([
            f"**Line {issue.line_number}**{function_info}{metric_info}",
            f"❌ {issue.message}",
            f"💡 **Suggestion**: {issue.suggestion}"
        ])
        
        if issue.example:
            report_lines.extend([
                "```",
                issue.example,
                "```"
            ])
        
        report_lines.append("")
    
    # Add function metrics if available
    if "function_metrics" in metrics and metrics["function_metrics"]:
        report_lines.extend([
            "📈 **Function Metrics**",
            ""
        ])
        
        for func_name, func_metrics in metrics["function_metrics"].items():
            report_lines.extend([
                f"**{func_name}()**",
                f"- Lines: {func_metrics.lines_of_code}",
                f"- Complexity: {func_metrics.cyclomatic_complexity}",
                f"- Cognitive Complexity: {func_metrics.cognitive_complexity}",
                f"- Parameters: {func_metrics.parameter_count}",
                f"- Nesting Depth: {func_metrics.nesting_depth}",
                f"- Maintainability Index: {func_metrics.maintainability_index}",
                ""
            ])
    
    # Add priority recommendations
    critical_issues = [i for i in issues if i.severity == 'critical']
    major_issues = [i for i in issues if i.severity == 'major']
    
    if critical_issues or major_issues:
        report_lines.extend([
            "🎯 **Priority Actions**",
            ""
        ])
        
        if critical_issues:
            report_lines.append("**Immediate attention required:**")
            for issue in critical_issues[:3]:  # Top 3 critical issues
                report_lines.append(f"- Line {issue.line_number}: {issue.message}")
            report_lines.append("")
        
        if major_issues:
            report_lines.append("**Should address soon:**")
            for issue in major_issues[:3]:  # Top 3 major issues
                report_lines.append(f"- Line {issue.line_number}: {issue.message}")
    
    return "\n".join(report_lines)
