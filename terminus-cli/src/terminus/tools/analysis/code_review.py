import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Tuple

from pydantic_ai import RunContext
from terminus.core.session import session
from .code_reviewer import CodeAnalyzer, CodeIssue

log = logging.getLogger(__name__)

async def review_code(ctx: RunContext, path: str = ".") -> str:
    """Comprehensive code review for a file or directory."""
    log.debug(f"review_code called with path: {path}")
    
    # Resolve path relative to session working directory
    resolved_path = session.resolve_path(path)
    
    if ctx.deps and ctx.deps.display_tool_status:
        await ctx.deps.display_tool_status("Reviewing", str(resolved_path))
    
    if resolved_path.is_file():
        return await _review_single_file(resolved_path)
    elif resolved_path.is_dir():
        return await _review_directory(resolved_path)
    else:
        return f"Error: Path {path} not found or is not a file/directory"


async def _review_single_file(file_path: Path) -> str:
    """Review a single file."""
    analyzer = CodeAnalyzer()
    issues, metrics = analyzer.analyze_file(str(file_path))
    
    if "error" in metrics:
        return f"Error reviewing {file_path}: {metrics['error']}"
    
    return _generate_single_file_review(str(file_path), issues, metrics)


async def _review_directory(dir_path: Path) -> str:
    """Review all code files in a directory."""
    # Find all code files
    code_extensions = {'.py', '.js', '.ts', '.jsx', '.tsx'}
    code_files = []
    
    for ext in code_extensions:
        code_files.extend(dir_path.rglob(f"*{ext}"))
    
    # Filter out common directories to ignore
    ignore_dirs = {'.git', '.vscode', 'node_modules', '__pycache__', '.pytest_cache', 'build', 'dist'}
    code_files = [f for f in code_files if not any(part in ignore_dirs for part in f.parts)]
    
    if not code_files:
        return f"No code files found in {dir_path}"
    
    # Limit to reasonable number of files to avoid overwhelming output
    if len(code_files) > 20:
        code_files = code_files[:20]
        truncated_message = f"\n*Note: Limited to first 20 files. Found {len(code_files)} total.*"
    else:
        truncated_message = ""
    
    # Analyze all files
    all_issues = []
    all_metrics = {}
    file_summaries = []
    
    analyzer = CodeAnalyzer()
    
    for file_path in code_files:
        try:
            issues, metrics = analyzer.analyze_file(str(file_path))
            if "error" not in metrics:
                all_issues.extend(issues)
                all_metrics[str(file_path)] = metrics
                
                # Create file summary
                issue_count = len(issues)
                critical_count = len([i for i in issues if i.severity == 'critical'])
                major_count = len([i for i in issues if i.severity == 'major'])
                
                file_summaries.append({
                    'path': str(file_path),
                    'total_issues': issue_count,
                    'critical_issues': critical_count,
                    'major_issues': major_count,
                    'metrics': metrics.get('file_metrics', {})
                })
        except Exception as e:
            log.error(f"Error analyzing {file_path}: {e}")
    
    return _generate_directory_review(str(dir_path), all_issues, all_metrics, file_summaries) + truncated_message


def _generate_single_file_review(file_path: str, issues: List[CodeIssue], metrics: Dict) -> str:
    """Generate a focused single-file review."""
    if not issues:
        return f"✅ **Code Review: {file_path}**\n\nGreat! No issues found. Code quality looks good!"
    
    # Sort issues by severity
    severity_order = {'critical': 0, 'major': 1, 'minor': 2, 'info': 3}
    sorted_issues = sorted(issues, key=lambda x: (severity_order[x.severity], x.line_number))
    
    # Count by severity
    issue_counts = {}
    for issue in issues:
        issue_counts[issue.severity] = issue_counts.get(issue.severity, 0) + 1
    
    # Generate report
    report_lines = [
        f"🔍 **Code Review: {Path(file_path).name}**",
        "",
        f"📋 **Summary**: {len(issues)} issues found"
    ]
    
    # Add severity breakdown
    severity_emojis = {'critical': '🔴', 'major': '🟠', 'minor': '🟡', 'info': '🔵'}
    for severity in ['critical', 'major', 'minor', 'info']:
        if severity in issue_counts:
            count = issue_counts[severity]
            emoji = severity_emojis[severity]
            report_lines.append(f"- {emoji} {severity.title()}: {count}")
    
    report_lines.extend(["", "🎯 **Top Priority Issues**", ""])
    
    # Show top 5 most important issues
    top_issues = sorted_issues[:5]
    for i, issue in enumerate(top_issues, 1):
        function_info = f" in `{issue.function_name}()`" if issue.function_name else ""
        metric_info = f" ({issue.metric_value})" if issue.metric_value else ""
        
        report_lines.extend([
            f"**{i}. Line {issue.line_number}**{function_info}{metric_info}",
            f"   {issue.message}",
            f"   💡 {issue.suggestion}",
            ""
        ])
    
    if len(issues) > 5:
        report_lines.append(f"*({len(issues) - 5} more issues found. Use `suggest_refactor {file_path}` for full details)*")
    
    return "\n".join(report_lines)


def _generate_directory_review(dir_path: str, all_issues: List[CodeIssue], all_metrics: Dict, file_summaries: List[Dict]) -> str:
    """Generate a comprehensive directory-wide review."""
    if not all_issues:
        return f"✅ **Project Code Review: {dir_path}**\n\nExcellent! No issues found across all code files."
    
    # Calculate project-wide statistics
    total_files = len(file_summaries)
    files_with_issues = len([f for f in file_summaries if f['total_issues'] > 0])
    total_issues = len(all_issues)
    
    # Group issues by severity
    issue_counts = {}
    for issue in all_issues:
        issue_counts[issue.severity] = issue_counts.get(issue.severity, 0) + 1
    
    # Find most problematic files
    problematic_files = sorted(file_summaries, 
                              key=lambda x: (x['critical_issues'] * 3 + x['major_issues'] * 2 + x['total_issues']), 
                              reverse=True)[:10]
    
    # Find most common issue types
    issue_types = {}
    for issue in all_issues:
        issue_types[issue.type] = issue_types.get(issue.type, 0) + 1
    
    common_issues = sorted(issue_types.items(), key=lambda x: x[1], reverse=True)[:5]
    
    # Generate report
    report_lines = [
        f"🏗️ **Project Code Review: {Path(dir_path).name}**",
        "",
        "📊 **Project Overview**",
        f"- Files analyzed: {total_files}",
        f"- Files with issues: {files_with_issues}",
        f"- Total issues: {total_issues}",
        "",
        "🚨 **Issues by Severity**"
    ]
    
    # Add severity breakdown
    severity_emojis = {'critical': '🔴', 'major': '🟠', 'minor': '🟡', 'info': '🔵'}
    for severity in ['critical', 'major', 'minor', 'info']:
        if severity in issue_counts:
            count = issue_counts[severity]
            percentage = round(count / total_issues * 100, 1)
            emoji = severity_emojis[severity]
            report_lines.append(f"- {emoji} {severity.title()}: {count} ({percentage}%)")
    
    # Most problematic files
    if problematic_files:
        report_lines.extend([
            "",
            "⚠️ **Files Needing Attention**",
            ""
        ])
        
        for i, file_info in enumerate(problematic_files[:5], 1):
            file_name = Path(file_info['path']).name
            critical = file_info['critical_issues']
            major = file_info['major_issues']
            total = file_info['total_issues']
            
            if total > 0:
                issue_str = f"{total} issues"
                if critical > 0:
                    issue_str = f"{critical} critical, {major} major, {total} total"
                elif major > 0:
                    issue_str = f"{major} major, {total} total"
                
                report_lines.append(f"{i}. **{file_name}** - {issue_str}")
    
    # Common issue patterns
    if common_issues:
        report_lines.extend([
            "",
            "🔍 **Common Issues Across Project**",
            ""
        ])
        
        for issue_type, count in common_issues:
            percentage = round(count / total_issues * 100, 1)
            type_name = issue_type.replace('_', ' ').title()
            report_lines.append(f"- {type_name}: {count} occurrences ({percentage}%)")
    
    # Project-wide recommendations
    report_lines.extend([
        "",
        "🎯 **Recommended Actions**",
        ""
    ])
    
    if issue_counts.get('critical', 0) > 0:
        report_lines.append(f"1. **Immediate**: Address {issue_counts['critical']} critical issues first")
    
    if issue_counts.get('major', 0) > 0:
        report_lines.append(f"2. **High Priority**: Fix {issue_counts['major']} major issues")
    
    if common_issues:
        top_issue_type = common_issues[0][0]
        top_issue_count = common_issues[0][1]
        report_lines.append(f"3. **Pattern**: Focus on {top_issue_type.replace('_', ' ')} issues ({top_issue_count} occurrences)")
    
    report_lines.extend([
        "",
        "💡 **Next Steps**",
        f"- Run `suggest_refactor <filename>` on problematic files for detailed analysis",
        f"- Consider implementing code quality gates in your CI/CD pipeline",
        f"- Set up automated linting to catch issues early",
        ""
    ])
    
    return "\n".join(report_lines)


async def find_complex_functions(ctx: RunContext, path: str = ".", min_complexity: int = 10) -> str:
    """Find functions with high complexity across the codebase."""
    log.debug(f"find_complex_functions called with path: {path}, min_complexity: {min_complexity}")
    
    resolved_path = session.resolve_path(path)
    
    if ctx.deps and ctx.deps.display_tool_status:
        await ctx.deps.display_tool_status("Finding complex functions", str(resolved_path))
    
    if resolved_path.is_file():
        files_to_analyze = [resolved_path]
    else:
        # Find all Python and JavaScript files
        code_extensions = {'.py', '.js', '.ts', '.jsx', '.tsx'}
        files_to_analyze = []
        for ext in code_extensions:
            files_to_analyze.extend(resolved_path.rglob(f"*{ext}"))
        
        # Filter out common directories to ignore
        ignore_dirs = {'.git', '.vscode', 'node_modules', '__pycache__', '.pytest_cache', 'build', 'dist'}
        files_to_analyze = [f for f in files_to_analyze if not any(part in ignore_dirs for part in f.parts)]
    
    complex_functions = []
    analyzer = CodeAnalyzer()
    
    for file_path in files_to_analyze:
        try:
            issues, metrics = analyzer.analyze_file(str(file_path))
            
            if "function_metrics" in metrics:
                for func_name, func_metrics in metrics["function_metrics"].items():
                    if func_metrics.cyclomatic_complexity >= min_complexity:
                        complex_functions.append({
                            'file': str(file_path),
                            'function': func_name,
                            'complexity': func_metrics.cyclomatic_complexity,
                            'cognitive_complexity': func_metrics.cognitive_complexity,
                            'lines': func_metrics.lines_of_code,
                            'maintainability': func_metrics.maintainability_index
                        })
        except Exception as e:
            log.error(f"Error analyzing {file_path}: {e}")
    
    if not complex_functions:
        return f"✅ No functions found with complexity >= {min_complexity}"
    
    # Sort by complexity
    complex_functions.sort(key=lambda x: x['complexity'], reverse=True)
    
    # Generate report
    report_lines = [
        f"🔍 **Complex Functions Report (Complexity >= {min_complexity})**",
        "",
        f"Found {len(complex_functions)} complex functions",
        ""
    ]
    
    for i, func in enumerate(complex_functions[:15], 1):  # Top 15
        file_name = Path(func['file']).name
        report_lines.extend([
            f"**{i}. {func['function']}()** in {file_name}",
            f"   - Cyclomatic Complexity: {func['complexity']}",
            f"   - Cognitive Complexity: {func['cognitive_complexity']}",
            f"   - Lines of Code: {func['lines']}",
            f"   - Maintainability Index: {func['maintainability']}",
            ""
        ])
    
    if len(complex_functions) > 15:
        report_lines.append(f"*({len(complex_functions) - 15} more complex functions found)*")
    
    report_lines.extend([
        "",
        "💡 **Recommendations**",
        "- Focus on functions with complexity > 15 first",
        "- Break large functions into smaller, focused functions",
        "- Use early returns to reduce nesting",
        "- Extract complex logic into helper functions"
    ])
    
    return "\n".join(report_lines)


async def find_code_duplicates(ctx: RunContext, path: str = ".") -> str:
    """Find code duplication patterns across the project."""
    log.debug(f"find_code_duplicates called with path: {path}")
    
    resolved_path = session.resolve_path(path)
    
    if ctx.deps and ctx.deps.display_tool_status:
        await ctx.deps.display_tool_status("Finding duplicates", str(resolved_path))
    
    # Find all code files
    code_extensions = {'.py', '.js', '.ts', '.jsx', '.tsx'}
    files_to_analyze = []
    
    if resolved_path.is_file():
        files_to_analyze = [resolved_path]
    else:
        for ext in code_extensions:
            files_to_analyze.extend(resolved_path.rglob(f"*{ext}"))
        
        # Filter out common directories to ignore
        ignore_dirs = {'.git', '.vscode', 'node_modules', '__pycache__', '.pytest_cache', 'build', 'dist'}
        files_to_analyze = [f for f in files_to_analyze if not any(part in ignore_dirs for part in f.parts)]
    
    duplicates = []
    analyzer = CodeAnalyzer()
    
    for file_path in files_to_analyze:
        try:
            issues, metrics = analyzer.analyze_file(str(file_path))
            
            # Find duplication issues
            duplication_issues = [issue for issue in issues if issue.type == 'duplication']
            for issue in duplication_issues:
                duplicates.append({
                    'file': str(file_path),
                    'line': issue.line_number,
                    'message': issue.message,
                    'suggestion': issue.suggestion
                })
        except Exception as e:
            log.error(f"Error analyzing {file_path}: {e}")
    
    if not duplicates:
        return "✅ No code duplication detected!"
    
    # Generate report
    report_lines = [
        f"🔍 **Code Duplication Report**",
        "",
        f"Found {len(duplicates)} duplication patterns",
        ""
    ]
    
    for i, dup in enumerate(duplicates, 1):
        file_name = Path(dup['file']).name
        report_lines.extend([
            f"**{i}. {file_name}** (Line {dup['line']})",
            f"   {dup['message']}",
            f"   💡 {dup['suggestion']}",
            ""
        ])
    
    report_lines.extend([
        " **Refactoring Tips**",
        "- Extract common code into shared functions",
        "- Use inheritance or composition for similar classes",
        "- Consider using configuration objects for similar patterns",
        "- Look for opportunities to create reusable utilities"
    ])
    
    return "\n".join(report_lines)
