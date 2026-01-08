import os
import re
import datetime
import subprocess
import sys
from pathlib import Path

# Configuration
TEMPLATE_PATH = 'template/index.html'
OUTPUT_FILE = 'index.html'
IGNORE_DIRS = {'.git', '.', 'template', '.github', '__pycache__', 'node_modules', 'dist', 'build', '.idea', '.vscode'}

def get_git_date(path):
    try:
        # Get the last commit date for the directory
        # %cI - committer date, strict ISO 8601 format
        result = subprocess.run(
            ['git', 'log', '-1', '--format=%cI', path],
            capture_output=True,
            text=True,
            check=False
        )
        if result.returncode == 0 and result.stdout.strip():
            return datetime.datetime.fromisoformat(result.stdout.strip())
    except Exception as e:
        print(f"Warning: Could not get git date for {path}: {e}")
    
    # Fallback to file system modification time
    timestamp = os.path.getmtime(path)
    return datetime.datetime.fromtimestamp(timestamp).astimezone()

def extract_tool_info(dir_path):
    index_path = os.path.join(dir_path, 'index.html')
    if not os.path.exists(index_path):
        return None

    info = {
        'path': dir_path,
        'url': f'/{dir_path}/',
        'name': dir_path.replace('-', ' ').title(),
        'description': '',
        'icon': 'art.svg' if os.path.exists(os.path.join(dir_path, 'art.svg')) else None,
        'date': get_git_date(dir_path)
    }

    try:
        with open(index_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
            # Extract title
            title_match = re.search(r'<title>(.*?)</title>', content, re.IGNORECASE)
            if title_match:
                info['name'] = title_match.group(1).split('|')[0].strip() # Take first part if piped

            # Extract description (try meta description first, then subtitle class)
            desc_match = re.search(r'<meta name="description" content="(.*?)">', content, re.IGNORECASE | re.DOTALL)
            if desc_match:
                info['description'] = desc_match.group(1)
            else:
                subtitle_match = re.search(r'<p class="subtitle">(.*?)</p>', content, re.IGNORECASE | re.DOTALL)
                if subtitle_match:
                    # Strip HTML tags
                    raw_desc = subtitle_match.group(1)
                    info['description'] = re.sub(r'<[^>]+>', '', raw_desc).strip()

    except Exception as e:
        print(f"Error reading {index_path}: {e}")

    return info

def generate_html_content(tools):
    # Read template
    try:
        with open(TEMPLATE_PATH, 'r', encoding='utf-8') as f:
            template_content = f.read()
    except Exception as e:
        print(f"Error reading template: {e}")
        return

    # 1. Update Title
    template_content = re.sub(r'<title>.*?</title>', '<title>Static Web Tools</title>', template_content)

    # 2. Inject CSS for Grid
    css_to_add = """
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
            justify-content: space-between;
        }
        
        /* Overrides for Index Page */
        body { max-width: 1000px; }
    """
    template_content = template_content.replace('</style>', f'{css_to_add}\n    </style>')

    # 3. Update Header
    header_replacement = """
    <header>
        <div class="brand">
            <h1>Static Web Tools</h1>
        </div>
        <p class="subtitle">A collection of lightweight, self-contained web tools.</p>
    </header>
    """
    # Regex to replace the entire <header>...</header> block
    template_content = re.sub(r'<header>.*?</header>', header_replacement, template_content, flags=re.DOTALL)

    # 4. Generate Cards HTML
    cards_html = '<div class="tool-grid">\n'
    
    for tool in tools:
        icon_html = ''
        if tool['icon']:
             icon_html = f'<img src="{tool["url"]}{tool["icon"]}" alt="" class="tool-card-icon">'
        else:
             # Default icon placeholder
             icon_html = '<div class="tool-card-icon" style="background:#eee"></div>'

        date_str = tool['date'].strftime('%Y-%m-%d')
        
        cards_html += f"""
        <a href="{tool['url']}" class="tool-card">
            <div class="tool-card-header">
                {icon_html}
                <h2>{tool['name']}</h2>
            </div>
            <p>{tool['description']}</p>
            <div class="tool-card-footer">
                <span>Updated: {date_str}</span>
            </div>
        </a>
        """
    
    cards_html += '</div>'

    # 5. Inject Cards into Main
    # We replace everything inside <main class="container">...</main>
    # Note: Template has <main class="container"> ... </main>
    template_content = re.sub(
        r'<main class="container">.*?</main>', 
        f'<main class="container">{cards_html}</main>', 
        template_content, 
        flags=re.DOTALL
    )

    # 6. Remove Script Logic (The template script is for the example tool)
    # We can just clear the script tag content or replace it with something minimal
    template_content = re.sub(r'<script>.*?</script>', '<script>\n        // Index page logic can go here\n    </script>', template_content, flags=re.DOTALL)

    return template_content

def main():
    tools = []
    
    # Scan directories
    for item in os.listdir('.'):
        if item in IGNORE_DIRS:
            continue
        
        if os.path.isdir(item) and not item.startswith('.'):
            tool_info = extract_tool_info(item)
            if tool_info:
                tools.append(tool_info)
    
    # Sort by date (newest first)
    tools.sort(key=lambda x: x['date'], reverse=True)
    
    # Generate HTML
    html = generate_html_content(tools)
    
    if html:
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"Successfully generated {OUTPUT_FILE} with {len(tools)} tools.")
    else:
        print("Failed to generate HTML.")

if __name__ == "__main__":
    main()
