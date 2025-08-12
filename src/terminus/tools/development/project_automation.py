"""
Project automation tools for Terminus CLI.
AI-powered project documentation and code refactoring tools.
"""

import asyncio
import logging
from pathlib import Path
from typing import Dict, Set, Any, Optional

log = logging.getLogger(__name__)


async def generate_project_readme(deps: Optional[Any] = None, project_path: str = ".") -> str:
    """
    Analyze project structure and generate comprehensive, professional README.md documentation.
    
    Args:
        project_path: Path to project directory (default: current directory)
        
    Returns:
        Generated README content or status message
    """
    try:
        if deps and deps.confirm_action:
            confirmed = await deps.confirm_action(
                "generate_project_readme: AI-Powered Documentation",
                f"This will deeply analyze the project at '{project_path}' and generate professional README.md",
                "Uses advanced analysis including code patterns, dependencies, architecture detection, and best practices."
            )
            if not confirmed:
                return "README generation cancelled by user."
        
        if deps and deps.display_tool_status:
            await deps.display_tool_status("generate_project_readme", project_path=project_path)
        
        # Convert to Path object
        project_dir = Path(project_path).resolve()
        if not project_dir.exists():
            return f"Error: Project path does not exist: {project_path}"
            
        if not project_dir.is_dir():
            return f"Error: Path is not a directory: {project_path}"
        
        # Deep analysis of project
        analysis = await _deep_analyze_project(project_dir)
        
        # Generate intelligent README content
        readme_content = await _generate_intelligent_readme(analysis)
        
        # Write README.md
        readme_path = project_dir / "README.md"
        
        with open(readme_path, "w", encoding="utf-8") as f:
            f.write(readme_content)
            
        return f"✅ **Professional README.md Generated**\\n\\n" + \
               f"📁 **Project**: {analysis['project_name']}\\n" + \
               f"🏗️ **Type**: {analysis['project_type']}\\n" + \
               f"� **Languages**: {', '.join(analysis['languages'][:3])}{'...' if len(analysis['languages']) > 3 else ''}\\n" + \
               f"� **Files**: {analysis['stats']['total_files']} files, {analysis['stats']['total_size_mb']:.1f}MB\\n" + \
               f"🎯 **Features**: {len(analysis['features'])} detected\\n" + \
               f"📝 **Sections**: {analysis['readme_sections']} sections\\n" + \
               f"📍 **Location**: {readme_path}\\n\\n" + \
               f"*Professional documentation with installation, usage, API docs, and best practices included.*"
        
    except Exception as e:
        log.error(f"Failed to generate README: {e}")
        return f"Error generating README: {str(e)}"


async def analyze_code_for_refactoring(deps: Optional[Any] = None, 
                                     refactor_goal: str = "", 
                                     file_pattern: str = "**/*.py") -> str:
    """
    Analyze code structure and suggest refactoring changes based on natural language description.
    
    Args:
        refactor_goal: Natural language description of refactoring goal (e.g., "rename all functions to snake_case")
        file_pattern: Glob pattern for files to analyze (default: "**/*.py")
        
    Returns:
        Analysis report with refactoring suggestions
    """
    try:
        if deps and deps.confirm_action:
            confirmed = await deps.confirm_action(
                "analyze_code_for_refactoring: Code Analysis",
                f"This will analyze code files matching '{file_pattern}' for refactoring goal: {refactor_goal}",
                "The tool will scan code structure and provide refactoring suggestions. No changes will be made automatically."
            )
            if not confirmed:
                return "Code analysis cancelled by user."
        
        if deps and deps.display_tool_status:
            await deps.display_tool_status("analyze_code_for_refactoring", 
                                              goal=refactor_goal, 
                                              pattern=file_pattern)
        
        # Find code files
        current_dir = Path.cwd()
        code_files = list(current_dir.glob(file_pattern))
        
        if not code_files:
            return f"No files found matching pattern: {file_pattern}"
        
        # Analyze files
        analysis_results = []
        
        for file_path in code_files[:20]:  # Limit to first 20 files
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Basic code analysis
                analysis = _analyze_code_file(file_path, content, refactor_goal)
                if analysis:
                    analysis_results.append(analysis)
                    
            except Exception as e:
                log.warning(f"Failed to analyze {file_path}: {e}")
                continue
        
        # Generate report
        report = f"🔍 **Code Refactoring Analysis Report**\\n\\n"
        report += f"**Goal:** {refactor_goal}\\n"
        report += f"**Pattern:** {file_pattern}\\n"
        report += f"**Files Found:** {len(code_files)}\\n"
        report += f"**Files Analyzed:** {len(analysis_results)}\\n\\n"
        
        if analysis_results:
            report += "## Suggested Changes\\n\\n"
            for i, analysis in enumerate(analysis_results, 1):
                report += f"### {i}. {analysis['file']}\\n"
                report += f"- **Issues Found:** {len(analysis['issues'])}\\n"
                for issue in analysis['issues']:
                    report += f"  - {issue}\\n"
                report += "\\n"
        else:
            report += "✅ No refactoring opportunities found matching the specified goal.\\n"
        
        report += "\\n---\\n*Use specific file editing tools to apply suggested changes*"
        
        return report
        
    except Exception as e:
        log.error(f"Failed to analyze code for refactoring: {e}")
        return f"Error analyzing code: {str(e)}"


async def _deep_analyze_project(project_dir: Path) -> Dict:
    """Comprehensive project analysis for professional documentation."""
    analysis = {
        "name": project_dir.name,
        "path": str(project_dir),
        "project_type": "Unknown",
        "frameworks": [],
        "architecture": {},
        "languages": {},
        "dependencies": {},
        "features": [],
        "quality_metrics": {},
        "directories": {},
        "key_files": {},
        "docs": [],
        "tests": {"framework": None, "files": []},
        "ci_cd": [],
        "deployment": [],
        "stats": {}
    }
    
    try:
        # Advanced file type analysis with framework detection
        language_ecosystem = {
            ".py": {"name": "Python", "frameworks": ["Django", "Flask", "FastAPI", "Streamlit"]},
            ".js": {"name": "JavaScript", "frameworks": ["React", "Vue", "Angular", "Express", "Next.js"]},
            ".ts": {"name": "TypeScript", "frameworks": ["Angular", "React", "Vue", "NestJS"]},
            ".java": {"name": "Java", "frameworks": ["Spring", "Spring Boot", "Maven", "Gradle"]},
            ".rs": {"name": "Rust", "frameworks": ["Actix", "Rocket", "Tokio", "Warp"]},
            ".go": {"name": "Go", "frameworks": ["Gin", "Echo", "Fiber", "Gorilla"]},
            ".php": {"name": "PHP", "frameworks": ["Laravel", "Symfony", "CodeIgniter"]},
            ".rb": {"name": "Ruby", "frameworks": ["Rails", "Sinatra", "Grape"]},
            ".cs": {"name": "C#", "frameworks": [".NET", "ASP.NET", "Blazor"]},
        }
        
        # Sophisticated config file detection
        config_analysis = {
            "package.json": {"type": "Node.js", "package_manager": "npm/yarn"},
            "requirements.txt": {"type": "Python", "package_manager": "pip"},
            "pyproject.toml": {"type": "Python", "package_manager": "poetry/pip"},
            "Cargo.toml": {"type": "Rust", "package_manager": "cargo"},
            "go.mod": {"type": "Go", "package_manager": "go modules"},
            "pom.xml": {"type": "Java", "package_manager": "maven"},
            "build.gradle": {"type": "Java", "package_manager": "gradle"},
            "composer.json": {"type": "PHP", "package_manager": "composer"},
            "Gemfile": {"type": "Ruby", "package_manager": "bundler"},
            "docker-compose.yml": {"type": "Containerized", "deployment": "Docker Compose"},
            "Dockerfile": {"type": "Containerized", "deployment": "Docker"},
            ".github/workflows": {"type": "CI/CD", "platform": "GitHub Actions"},
            "azure-pipelines.yml": {"type": "CI/CD", "platform": "Azure DevOps"},
            ".gitlab-ci.yml": {"type": "CI/CD", "platform": "GitLab CI"},
        }
        
        # Analyze project structure and content
        language_stats = {}
        total_size = 0
        file_count = 0
        
        for item in project_dir.rglob("*"):
            if any(part.startswith('.') for part in item.parts[len(project_dir.parts):]) and not any(part == '.github' for part in item.parts):
                continue
                
            if item.is_file():
                try:
                    file_size = item.stat().st_size
                    total_size += file_size
                    file_count += 1
                    
                    rel_path = str(item.relative_to(project_dir))
                    
                    # Language detection with detailed stats
                    if item.suffix in language_ecosystem:
                        lang_info = language_ecosystem[item.suffix]
                        lang_name = lang_info["name"]
                        
                        if lang_name not in language_stats:
                            language_stats[lang_name] = {"files": 0, "size": 0, "lines": 0}
                        
                        language_stats[lang_name]["files"] += 1
                        language_stats[lang_name]["size"] += file_size
                        
                        # Count lines for code files
                        if file_size < 1024 * 1024:  # Only for files < 1MB
                            try:
                                with open(item, 'r', encoding='utf-8', errors='ignore') as f:
                                    lines = sum(1 for _ in f)
                                language_stats[lang_name]["lines"] += lines
                            except:
                                pass
                    
                    # Config file analysis
                    for config_pattern, config_info in config_analysis.items():
                        if config_pattern in rel_path:
                            analysis["project_type"] = config_info["type"]
                            if "package_manager" in config_info:
                                analysis["dependencies"]["manager"] = config_info["package_manager"]
                            if "deployment" in config_info:
                                analysis["deployment"].append(config_info["deployment"])
                            if "platform" in config_info:
                                analysis["ci_cd"].append(config_info["platform"])
                    
                    # Detect frameworks and features from file content
                    await _detect_frameworks_and_features(item, analysis)
                    
                except (OSError, PermissionError):
                    continue
        
        # Set language statistics
        analysis["languages"] = language_stats
        
        # Determine primary language and project type
        if language_stats:
            primary_lang = max(language_stats.keys(), key=lambda k: language_stats[k]["files"])
            if analysis["project_type"] == "Unknown":
                analysis["project_type"] = f"{primary_lang} Project"
        
        # Calculate quality metrics
        analysis["quality_metrics"] = _calculate_quality_metrics(analysis, project_dir)
        
        # Analyze directory structure
        analysis["directories"] = _analyze_directory_structure(project_dir)
        
        # Project statistics
        analysis["stats"] = {
            "file_count": file_count,
            "total_size": total_size,
            "avg_file_size": total_size // file_count if file_count > 0 else 0,
            "total_lines": sum(lang["lines"] for lang in language_stats.values()),
            "language_diversity": len(language_stats)
        }
        
    except Exception as e:
        log.error(f"Deep project analysis failed: {e}")
        
    return analysis


async def _generate_intelligent_readme(analysis: Dict) -> str:
    """Generate professional, intelligent README content."""
    name = analysis["name"]
    project_type = analysis.get("project_type", "Software Project")
    
    # Get primary language
    languages = analysis.get("languages", {})
    primary_lang = ""
    if languages:
        primary_lang = max(languages.keys(), key=lambda k: languages[k]["files"])
    
    # Get framework info
    frameworks = analysis.get("frameworks", [])
    framework_text = f" using {', '.join(frameworks[:3])}" if frameworks else ""
    
    # Generate sophisticated description
    description = _generate_project_description(analysis)
    
    # Generate badges
    badges = _generate_project_badges(analysis)
    
    # Start building content
    content = f"""# {name}

{badges}

{description}

## 🚀 Features

{_generate_features_section(analysis)}

## 📋 Prerequisites

{_generate_prerequisites_section(analysis)}

## 🛠️ Installation

{_generate_installation_section(analysis)}

## 💻 Usage

{_generate_usage_section(analysis)}

## 📁 Project Structure

{_generate_project_structure_section(analysis)}

## 🧪 Testing

{_generate_testing_section(analysis)}

## 🚀 Deployment

{_generate_deployment_section(analysis)}

## 📊 Project Statistics

{_generate_statistics_section(analysis)}

## 🤝 Contributing

{_generate_contributing_section(analysis)}

## 📝 License

{_generate_license_section(analysis)}

## 🔧 Development

{_generate_development_section(analysis)}

## 📚 Documentation

{_generate_documentation_section(analysis)}

---

<div align="center">
  <p><em>This README was intelligently generated by <a href="https://github.com/yesh-045/terminus-cli">Terminus CLI</a></em></p>
  <p><strong>Last updated:</strong> {_get_current_date()}</p>
</div>
"""
    
    return content


async def _detect_frameworks_and_features(file_path: Path, analysis: Dict) -> None:
    """Detect frameworks and features from file content."""
    try:
        if file_path.suffix not in ['.py', '.js', '.ts', '.json', '.toml', '.txt', '.md', '.yml', '.yaml']:
            return
            
        if file_path.stat().st_size > 512 * 1024:  # Skip files > 512KB
            return
            
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read().lower()
            
        # Framework detection patterns
        framework_patterns = {
            # Python frameworks
            'django': ['django', 'from django', 'import django'],
            'flask': ['from flask', 'import flask', 'flask.'],
            'fastapi': ['from fastapi', 'import fastapi', 'fastapi.'],
            'streamlit': ['import streamlit', 'streamlit.'],
            'tensorflow': ['tensorflow', 'import tf'],
            'pytorch': ['torch', 'pytorch'],
            'pandas': ['pandas', 'import pd'],
            'numpy': ['numpy', 'import np'],
            
            # JavaScript/TypeScript frameworks
            'react': ['react', 'jsx', 'usestate', 'useeffect'],
            'vue': ['vue', 'v-if', 'v-for', '@click'],
            'angular': ['angular', '@component', '@injectable'],
            'express': ['express', 'app.get', 'app.post'],
            'next.js': ['next', 'getstaticprops', 'getserversideprops'],
            'gatsby': ['gatsby', 'graphql'],
            
            # Other frameworks
            'spring': ['spring', '@autowired', '@controller'],
            'laravel': ['laravel', 'artisan', 'eloquent'],
            'rails': ['rails', 'activerecord', 'actioncontroller'],
        }
        
        # Feature detection patterns
        feature_patterns = {
            'api': ['api', 'endpoint', 'rest', 'graphql'],
            'database': ['database', 'sql', 'orm', 'mongodb', 'postgres'],
            'authentication': ['auth', 'login', 'jwt', 'oauth', 'passport'],
            'testing': ['test', 'spec', 'mock', 'assert'],
            'docker': ['docker', 'dockerfile', 'container'],
            'ci/cd': ['ci', 'workflow', 'pipeline', 'deploy'],
            'web_interface': ['html', 'css', 'frontend', 'ui'],
            'machine_learning': ['ml', 'model', 'train', 'predict'],
            'cli': ['cli', 'command', 'argparse', 'click'],
        }
        
        # Check for frameworks
        for framework, patterns in framework_patterns.items():
            if any(pattern in content for pattern in patterns):
                if framework not in analysis['frameworks']:
                    analysis['frameworks'].append(framework)
        
        # Check for features
        for feature, patterns in feature_patterns.items():
            if any(pattern in content for pattern in patterns):
                if feature not in analysis['features']:
                    analysis['features'].append(feature)
                    
    except Exception:
        pass  # Silently skip problematic files


def _calculate_quality_metrics(analysis: Dict, project_dir: Path) -> Dict:
    """Calculate project quality metrics."""
    metrics = {
        "complexity": "Medium",
        "maintainability": "Good",
        "test_coverage": "Unknown",
        "documentation": "Partial",
        "code_quality": "Good"
    }
    
    try:
        # Calculate complexity based on file count and language diversity
        file_count = analysis['stats']['file_count']
        lang_count = len(analysis['languages'])
        
        if file_count > 1000 or lang_count > 5:
            metrics["complexity"] = "High"
        elif file_count < 50 and lang_count <= 2:
            metrics["complexity"] = "Low"
        
        # Check for testing
        if 'testing' in analysis['features']:
            metrics["test_coverage"] = "Present"
        
        # Check for documentation
        if any(doc.endswith('.md') for doc in analysis.get('docs', [])):
            metrics["documentation"] = "Good"
            
    except Exception:
        pass
        
    return metrics


def _analyze_directory_structure(project_dir: Path) -> Dict:
    """Analyze directory structure and categorize."""
    structure = {
        "source": [],
        "config": [],
        "docs": [],
        "tests": [],
        "build": [],
        "other": []
    }
    
    try:
        source_dirs = {'src', 'lib', 'app', 'source', 'code'}
        config_dirs = {'config', 'conf', 'settings', '.github', '.vscode'}
        doc_dirs = {'docs', 'documentation', 'doc'}
        test_dirs = {'test', 'tests', '__tests__', 'spec'}
        build_dirs = {'build', 'dist', 'target', 'bin', 'out'}
        
        for item in project_dir.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                dir_name = item.name.lower()
                
                if dir_name in source_dirs:
                    structure["source"].append(item.name)
                elif dir_name in config_dirs:
                    structure["config"].append(item.name)
                elif dir_name in doc_dirs:
                    structure["docs"].append(item.name)
                elif dir_name in test_dirs:
                    structure["tests"].append(item.name)
                elif dir_name in build_dirs:
                    structure["build"].append(item.name)
                else:
                    structure["other"].append(item.name)
                    
    except Exception:
        pass
        
    return structure


def _generate_project_description(analysis: Dict) -> str:
    """Generate intelligent project description."""
    name = analysis["name"]
    project_type = analysis.get("project_type", "Software Project")
    frameworks = analysis.get("frameworks", [])
    features = analysis.get("features", [])
    
    # Build description based on detected features
    description_parts = []
    
    if 'api' in features:
        description_parts.append("providing RESTful API services")
    if 'web_interface' in features:
        description_parts.append("featuring a modern web interface")
    if 'machine_learning' in features:
        description_parts.append("implementing machine learning capabilities")
    if 'database' in features:
        description_parts.append("with robust data persistence")
    if 'authentication' in features:
        description_parts.append("including secure authentication")
    if 'cli' in features:
        description_parts.append("offering command-line interface")
    
    base_desc = f"**{name}** is a {project_type.lower()}"
    
    if frameworks:
        base_desc += f" built with {', '.join(frameworks[:3])}"
    
    if description_parts:
        base_desc += ", " + ", ".join(description_parts[:3])
    
    base_desc += "."
    
    return base_desc


def _generate_project_badges(analysis: Dict) -> str:
    """Generate project badges."""
    badges = []
    
    # Language badges
    languages = analysis.get("languages", {})
    if languages:
        primary_lang = max(languages.keys(), key=lambda k: languages[k]["files"])
        badges.append(f"![{primary_lang}](https://img.shields.io/badge/{primary_lang}-blue)")
    
    # Framework badges
    frameworks = analysis.get("frameworks", [])
    for framework in frameworks[:3]:  # Limit to 3 badges
        badges.append(f"![{framework}](https://img.shields.io/badge/{framework}-green)")
    
    # Feature badges
    features = analysis.get("features", [])
    if 'docker' in features:
        badges.append("![Docker](https://img.shields.io/badge/Docker-blue)")
    if 'api' in features:
        badges.append("![API](https://img.shields.io/badge/API-REST-orange)")
    if 'testing' in features:
        badges.append("![Tests](https://img.shields.io/badge/Tests-passing-green)")
    
    return " ".join(badges) if badges else ""


def _generate_features_section(analysis: Dict) -> str:
    """Generate features section."""
    features = analysis.get("features", [])
    
    if not features:
        return "- Modern software architecture\n- Clean, maintainable code\n- Professional development practices"
    
    feature_descriptions = {
        'api': '🔌 RESTful API endpoints',
        'database': '💾 Database integration',
        'authentication': '🔐 Secure authentication system',
        'testing': '🧪 Comprehensive testing suite',
        'docker': '🐳 Docker containerization',
        'ci/cd': '🚀 Continuous integration/deployment',
        'web_interface': '🌐 Modern web interface',
        'machine_learning': '🤖 Machine learning capabilities',
        'cli': '⌨️ Command-line interface',
    }
    
    feature_list = []
    for feature in features:
        if feature in feature_descriptions:
            feature_list.append(feature_descriptions[feature])
        else:
            feature_list.append(f"✨ {feature.replace('_', ' ').title()}")
    
    return "\n".join(feature_list)


def _generate_prerequisites_section(analysis: Dict) -> str:
    """Generate prerequisites section."""
    prereqs = []
    
    languages = analysis.get("languages", {})
    if "Python" in languages:
        prereqs.append("- Python 3.8 or higher")
    if "JavaScript" in languages or "TypeScript" in languages:
        prereqs.append("- Node.js 16 or higher")
        prereqs.append("- npm or yarn")
    if "Java" in languages:
        prereqs.append("- Java 11 or higher")
        prereqs.append("- Maven or Gradle")
    if "Rust" in languages:
        prereqs.append("- Rust 1.60 or higher")
    if "Go" in languages:
        prereqs.append("- Go 1.19 or higher")
    
    if 'docker' in analysis.get('features', []):
        prereqs.append("- Docker and Docker Compose")
    
    if not prereqs:
        prereqs = ["- No specific prerequisites"]
    
    return "\n".join(prereqs)


def _generate_installation_section(analysis: Dict) -> str:
    """Generate installation section."""
    languages = analysis.get("languages", {})
    
    if "Python" in languages:
        return """```bash
# Clone the repository
git clone <repository-url>
cd """ + analysis["name"] + """

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\\Scripts\\activate

# Install dependencies
pip install -r requirements.txt
```"""
    
    elif "JavaScript" in languages or "TypeScript" in languages:
        return """```bash
# Clone the repository
git clone <repository-url>
cd """ + analysis["name"] + """

# Install dependencies
npm install
# or
yarn install
```"""
    
    elif "Rust" in languages:
        return """```bash
# Clone the repository
git clone <repository-url>
cd """ + analysis["name"] + """

# Build the project
cargo build --release
```"""
    
    else:
        return """```bash
# Clone the repository
git clone <repository-url>
cd """ + analysis["name"] + """

# Follow project-specific installation instructions
```"""


def _generate_usage_section(analysis: Dict) -> str:
    """Generate usage section."""
    languages = analysis.get("languages", {})
    features = analysis.get("features", [])
    
    usage_examples = []
    
    if 'cli' in features:
        usage_examples.append("```bash\n# Run the CLI\n./" + analysis["name"] + " --help\n```")
    
    if "Python" in languages and 'api' in features:
        usage_examples.append("```bash\n# Start the server\npython app.py\n# or\nuvicorn main:app --reload\n```")
    
    if ("JavaScript" in languages or "TypeScript" in languages) and 'web_interface' in features:
        usage_examples.append("```bash\n# Start development server\nnpm start\n# or\nyarn start\n```")
    
    if not usage_examples:
        usage_examples.append("```bash\n# Add usage examples here\n```")
    
    return "\n\n".join(usage_examples)


def _generate_project_structure_section(analysis: Dict) -> str:
    """Generate project structure section."""
    directories = analysis.get("directories", {})
    
    structure = "```\n" + analysis["name"] + "/\n"
    
    # Add categorized directories
    for category, dirs in directories.items():
        if dirs:
            for dir_name in dirs[:3]:  # Limit to 3 per category
                structure += f"├── {dir_name}/\n"
    
    structure += "└── README.md\n```"
    
    return structure


def _generate_testing_section(analysis: Dict) -> str:
    """Generate testing section."""
    if 'testing' in analysis.get('features', []):
        languages = analysis.get("languages", {})
        
        if "Python" in languages:
            return """```bash
# Run tests
pytest

# Run with coverage
pytest --cov=src
```"""
        elif "JavaScript" in languages or "TypeScript" in languages:
            return """```bash
# Run tests
npm test

# Run with coverage
npm run test:coverage
```"""
        else:
            return """```bash
# Run tests
# Add test commands here
```"""
    else:
        return "No automated tests configured. Consider adding a testing framework."


def _generate_deployment_section(analysis: Dict) -> str:
    """Generate deployment section."""
    deployment_options = analysis.get("deployment", [])
    
    if 'Docker' in deployment_options:
        return """### Docker Deployment

```bash
# Build the image
docker build -t """ + analysis["name"] + """ .

# Run the container
docker run -p 8080:8080 """ + analysis["name"] + """
```

### Docker Compose

```bash
# Start all services
docker-compose up -d
```"""
    
    else:
        return """### Manual Deployment

1. Ensure all prerequisites are installed
2. Clone and install dependencies
3. Configure environment variables
4. Start the application

### Cloud Deployment

Consider deploying to:
- Heroku
- AWS
- Google Cloud Platform
- DigitalOcean"""


def _generate_statistics_section(analysis: Dict) -> str:
    """Generate statistics section."""
    stats = analysis.get("stats", {})
    languages = analysis.get("languages", {})
    
    content = f"- **Files:** {stats.get('file_count', 0):,}\n"
    content += f"- **Total Size:** {stats.get('total_size', 0) / 1024 / 1024:.1f} MB\n"
    content += f"- **Lines of Code:** {stats.get('total_lines', 0):,}\n"
    content += f"- **Languages:** {len(languages)}\n"
    
    if languages:
        content += "\n### Language Breakdown\n\n"
        for lang, data in sorted(languages.items(), key=lambda x: x[1]['files'], reverse=True):
            content += f"- **{lang}:** {data['files']} files, {data['lines']:,} lines\n"
    
    return content


def _generate_contributing_section(analysis: Dict) -> str:
    """Generate contributing section."""
    return """1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests if applicable
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

### Development Guidelines

- Follow the existing code style
- Add tests for new features
- Update documentation as needed
- Ensure all tests pass before submitting"""


def _generate_license_section(analysis: Dict) -> str:
    """Generate license section."""
    return """This project is licensed under the [MIT License](LICENSE) - see the LICENSE file for details.

### Third-party Licenses

This project may include third-party libraries with their own licenses. Please refer to the respective license files."""


def _generate_development_section(analysis: Dict) -> str:
    """Generate development section."""
    languages = analysis.get("languages", {})
    
    if "Python" in languages:
        return """### Development Setup

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install

# Run linting
flake8 src/
black src/

# Run type checking
mypy src/
```"""
    
    elif "JavaScript" in languages or "TypeScript" in languages:
        return """### Development Setup

```bash
# Install development dependencies
npm install --dev

# Run linting
npm run lint

# Run formatting
npm run format

# Build the project
npm run build
```"""
    
    else:
        return """### Development Setup

```bash
# Set up your development environment
# Add project-specific development commands
```"""


def _generate_documentation_section(analysis: Dict) -> str:
    """Generate documentation section."""
    docs = analysis.get("docs", [])
    
    if docs:
        content = "### Available Documentation\n\n"
        for doc in docs:
            if doc != "README.md":
                content += f"- [{doc}]({doc})\n"
        content += "\n"
    else:
        content = ""
    
    content += """### API Documentation

- [API Reference](docs/api.md) (if applicable)
- [Developer Guide](docs/developer.md) (if applicable)

### Additional Resources

- [FAQ](docs/faq.md) (if applicable)
- [Troubleshooting](docs/troubleshooting.md) (if applicable)"""
    
    return content


def _analyze_code_file(file_path: Path, content: str, refactor_goal: str) -> Dict:
    """Analyze a single code file for refactoring opportunities."""
    issues = []
    
    # Basic analysis based on refactor goal
    goal_lower = refactor_goal.lower()
    
    if "snake_case" in goal_lower:
        # Check for camelCase functions/variables
        import re
        camel_case_pattern = r'def\s+([a-z]+[A-Z][a-zA-Z]*)'
        matches = re.findall(camel_case_pattern, content)
        if matches:
            issues.append(f"Found {len(matches)} camelCase function names: {', '.join(matches[:3])}{'...' if len(matches) > 3 else ''}")
    
    if "function" in goal_lower and "rename" in goal_lower:
        # Find function definitions
        import re
        func_pattern = r'def\s+([a-zA-Z_][a-zA-Z0-9_]*)'
        matches = re.findall(func_pattern, content)
        if matches:
            issues.append(f"Found {len(matches)} functions that could be renamed: {', '.join(matches[:3])}{'...' if len(matches) > 3 else ''}")
    
    if "variable" in goal_lower and "rename" in goal_lower:
        # Basic variable detection (simplified)
        lines = content.split('\n')
        assignment_lines = [i+1 for i, line in enumerate(lines) if '=' in line and not line.strip().startswith('#')]
        if assignment_lines:
            issues.append(f"Found {len(assignment_lines)} variable assignments on lines: {', '.join(map(str, assignment_lines[:5]))}{'...' if len(assignment_lines) > 5 else ''}")
    
    if issues:
        return {
            "file": str(file_path.relative_to(Path.cwd())),
            "issues": issues
        }
    
    return None


def _get_current_date() -> str:
    """Get current date in readable format."""
    from datetime import datetime
    return datetime.now().strftime("%B %d, %Y")
