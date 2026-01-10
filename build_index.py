# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "jinja2",
# ]
# ///

import os
import re
import datetime
import subprocess
import sys
from pathlib import Path
from jinja2 import Template

# Configuration
OUTPUT_FILE = 'index.html'
IGNORE_DIRS = {'.git', '.', 'template', '.github', '__pycache__', 'node_modules', 'dist', 'build', '.idea', '.vscode'}

INDEX_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="icon" type="image/svg+xml" href="art.svg">
    <title>tools.ddanieltan.dev</title>
    <style>
        /* Base Reset & Layout */
        * { box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            max-width: 1000px;
            margin: 0 auto;
            padding: 20px;
            background-color: #fdfdfd;
            color: #333;
            line-height: 1.6;
        }

        /* Header & Icon */
        header {
            display: flex;
            flex-direction: column;
            gap: 8px;
            margin-bottom: 30px;
            border-bottom: 1px solid #eee;
            padding-bottom: 20px;
        }

        .tool-icon {
            height: 4em;
            background-color: white;
            border: 2px solid #1e293b;
            border-radius: 8px;
            padding: 2px;
        }

        h1 {
            margin: 0;
            font-size: 2.5rem;
            color: #1e293b;
            letter-spacing: -0.5px;
        }

        .subtitle {
            color: #64748b;
            margin: 0;
            font-size: 1rem;
        }

        /* Common UI Components */
        .container {
            background: white;
            padding: 20px;
        }
        
        /* Tool Grid Styles */
        .tool-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }

        .tool-card {
            background: white;
            border: 1px solid #eee;
            border-radius: 8px;
            padding: 20px;
            text-decoration: none;
            color: inherit;
            display: flex;
            flex-direction: column;
            transition: transform 0.2s, box-shadow 0.2s;
            height: 100%;
        }

        .tool-card:hover {
            transform: translateY(-3px);
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
            border-color: #cbd5e1;
        }

        .tool-card-header {
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 12px;
        }

        .tool-card-icon {
            width: 40px;
            height: 40px;
            background-color: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 4px;
            flex-shrink: 0;
            object-fit: contain;
        }

        .tool-card h2 {
            margin: 0;
            font-size: 1.1rem;
            color: #1e293b;
            font-weight: 600;
        }

        .tool-card p {
            margin: 0;
            font-size: 0.9rem;
            color: #64748b;
            line-height: 1.5;
            flex-grow: 1;
        }
        
        .tool-card-footer {
            margin-top: 15px;
            padding-top: 15px;
            border-top: 1px solid #f1f5f9;
            font-size: 0.75rem;
            color: #94a3b8;
            display: flex;
            flex-direction: column;
            gap: 4px;
        }

        @media (max-width: 600px) {
            body { padding: 15px; }
            .container { padding: 15px; }
        }
    </style>
</head>
<body>
    <header>
        <div style="display: flex; align-items: center; gap: 12px;">
            <img src="art.svg" alt="tools.ddanieltan.dev icon" class="tool-icon">
            <h1>tools.ddanieltan.dev</h1>
        </div>
        <p class="subtitle">
  Lightweight tools built with LLM assistance by 
  <a href="https://github.com/ddanieltan">@ddanieltan</a>. 
  Inspired by <a href="https://tools.simonwillison.net">tools.simonwillison.net</a>.
</p>
    </header>

    <main class="container">
        <div class="tool-grid">
            {% for tool in tools %}
            <a href="{{ tool.url }}" class="tool-card">
                <div class="tool-card-header">
                    {% if tool.icon %}
                    <img src="{{ tool.url }}{{ tool.icon }}" alt="" class="tool-card-icon">
                    {% else %}
                    <div class="tool-card-icon" style="background:#eee"></div>
                    {% endif %}
                    <h2>{{ tool.name }}</h2>
                </div>
                <p>{{ tool.description }}</p>
                <div class="tool-card-footer">
                    <span>Updated: {{ tool.date.strftime('%Y-%m-%d') }}</span>
                    <span>Created: {{ tool.created_date.strftime('%Y-%m-%d') }}</span>
                </div>
            </a>
            {% endfor %}
        </div>
    </main>
</body>
</html>"""

def get_git_dates(path):
    try:
        result = subprocess.run(
            ['git', 'log', '--format=%cI', '--', str(path)],
            capture_output=True,
            text=True,
            check=False
        )
        if result.returncode == 0 and result.stdout.strip():
            lines = result.stdout.strip().split('\n')
            return (
                datetime.datetime.fromisoformat(lines[0]), # Latest
                datetime.datetime.fromisoformat(lines[-1]) # Earliest
            )
    except Exception as e:
        print(f"Warning: Could not get git dates for {path}: {e}")
    
    dt = datetime.datetime.fromtimestamp(os.path.getmtime(path)).astimezone()
    return dt, dt

def extract_tool_info(dir_path):
    index_path = dir_path / 'index.html'
    if not index_path.exists():
        return None

    info = {
        'path': str(dir_path),
        'url': f'/{dir_path.name}/',
        'name': dir_path.name.replace('-', ' ').title(),
        'description': '',
        'icon': 'art.svg' if (dir_path / 'art.svg').exists() else None,
    }

    last_date, first_date = get_git_dates(dir_path)
    info['date'] = last_date
    info['created_date'] = first_date

    try:
        content = index_path.read_text(encoding='utf-8')
        title_match = re.search(r'<title>(.*?)</title>', content, re.IGNORECASE)
        if title_match:
            info['name'] = title_match.group(1).split('|')[0].strip()

        desc_match = re.search(r'<meta name="description" content="(.*?)">', content, re.IGNORECASE | re.DOTALL)
        if desc_match:
            info['description'] = desc_match.group(1)
        else:
            subtitle_match = re.search(r'<p class="subtitle">(.*?)</p>', content, re.IGNORECASE | re.DOTALL)
            if subtitle_match:
                raw_desc = subtitle_match.group(1)
                info['description'] = re.sub(r'<[^>]+>', '', raw_desc).strip()
    except Exception as e:
        print(f"Error reading {index_path}: {e}")

    return info

def main():
    tools = []
    root_dir = Path('.')
    
    for item in root_dir.iterdir():
        if item.name in IGNORE_DIRS or item.name.startswith('.'):
            continue
        if item.is_dir():
            tool_info = extract_tool_info(item)
            if tool_info:
                tools.append(tool_info)
    
    tools.sort(key=lambda x: x['date'], reverse=True)
    
    try:
        template = Template(INDEX_TEMPLATE)
        html_output = template.render(tools=tools)
        
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            f.write(html_output)
            
        print(f"Successfully generated {OUTPUT_FILE} with {len(tools)} tools.")
    except Exception as e:
        print(f"Failed to render template: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
