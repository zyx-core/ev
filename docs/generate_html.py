"""
Simple script to convert markdown to HTML for browser-based PDF generation
"""
import markdown
from pathlib import Path

def convert_md_to_html(md_file, html_file):
    """Convert markdown to styled HTML"""
    # Read markdown file
    with open(md_file, 'r', encoding='utf-8') as f:
        md_content = f.read()
    
    # Convert markdown to HTML
    html_content = markdown.markdown(
        md_content,
        extensions=['tables', 'fenced_code', 'codehilite', 'toc']
    )
    
    # CSS styling
    css_style = """
    <style>
        @media print {
            body { margin: 0; }
            @page { margin: 2cm; }
        }
        
        body {
            font-family: 'Segoe UI', 'Arial', sans-serif;
            line-height: 1.6;
            max-width: 1200px;
            margin: 40px auto;
            padding: 20px;
            color: #333;
            background: white;
        }
        
        h1 {
            color: #2c3e50;
            border-bottom: 4px solid #3498db;
            padding-bottom: 12px;
            margin-top: 40px;
            font-size: 2.5em;
        }
        
        h2 {
            color: #34495e;
            border-bottom: 2px solid #95a5a6;
            padding-bottom: 10px;
            margin-top: 35px;
            font-size: 2em;
        }
        
        h3 {
            color: #7f8c8d;
            margin-top: 25px;
            font-size: 1.5em;
        }
        
        h4 {
            color: #95a5a6;
            margin-top: 20px;
            font-size: 1.2em;
        }
        
        table {
            border-collapse: collapse;
            width: 100%;
            margin: 25px 0;
            box-shadow: 0 2px 3px rgba(0,0,0,0.1);
        }
        
        th, td {
            border: 1px solid #ddd;
            padding: 14px;
            text-align: left;
        }
        
        th {
            background-color: #3498db;
            color: white;
            font-weight: 600;
        }
        
        tr:nth-child(even) {
            background-color: #f8f9fa;
        }
        
        tr:hover {
            background-color: #e8f4f8;
        }
        
        code {
            background-color: #f4f4f4;
            padding: 3px 8px;
            border-radius: 4px;
            font-family: 'Consolas', 'Courier New', monospace;
            font-size: 0.9em;
            color: #e74c3c;
        }
        
        pre {
            background-color: #2c3e50;
            color: #ecf0f1;
            padding: 20px;
            border-radius: 6px;
            overflow-x: auto;
            line-height: 1.5;
        }
        
        pre code {
            background: none;
            color: #ecf0f1;
            padding: 0;
        }
        
        blockquote {
            border-left: 5px solid #3498db;
            padding-left: 25px;
            margin: 25px 0;
            font-style: italic;
            color: #555;
            background: #f8f9fa;
            padding: 15px 15px 15px 25px;
            border-radius: 0 4px 4px 0;
        }
        
        hr {
            border: none;
            border-top: 3px solid #ecf0f1;
            margin: 40px 0;
        }
        
        ul, ol {
            margin: 15px 0;
            padding-left: 30px;
        }
        
        li {
            margin: 8px 0;
        }
        
        a {
            color: #3498db;
            text-decoration: none;
        }
        
        a:hover {
            text-decoration: underline;
        }
        
        .toc {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 6px;
            margin: 30px 0;
        }
        
        .print-button {
            position: fixed;
            top: 20px;
            right: 20px;
            background: #3498db;
            color: white;
            padding: 12px 24px;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-size: 16px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            z-index: 1000;
        }
        
        .print-button:hover {
            background: #2980b9;
        }
        
        @media print {
            .print-button {
                display: none;
            }
        }
    </style>
    """
    
    # JavaScript for print functionality
    js_script = """
    <script>
        function printPage() {
            window.print();
        }
        
        // Auto-generate table of contents
        window.addEventListener('DOMContentLoaded', (event) => {
            const headers = document.querySelectorAll('h2');
            if (headers.length > 0) {
                const toc = document.createElement('div');
                toc.className = 'toc';
                toc.innerHTML = '<h2>Table of Contents</h2><ul></ul>';
                const ul = toc.querySelector('ul');
                
                headers.forEach((header, index) => {
                    const id = 'section-' + index;
                    header.id = id;
                    const li = document.createElement('li');
                    const a = document.createElement('a');
                    a.href = '#' + id;
                    a.textContent = header.textContent;
                    li.appendChild(a);
                    ul.appendChild(li);
                });
                
                const firstH1 = document.querySelector('h1');
                if (firstH1 && firstH1.nextSibling) {
                    firstH1.parentNode.insertBefore(toc, firstH1.nextSibling);
                }
            }
        });
    </script>
    """
    
    # Combine HTML
    full_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>IEVC-eco Project Presentation Report</title>
    {css_style}
    {js_script}
</head>
<body>
    <button class="print-button" onclick="printPage()">Print / Save as PDF</button>
    {html_content}
</body>
</html>
"""
    
    # Write HTML file
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(full_html)
    
    print(f"[SUCCESS] HTML file generated: {html_file}")
    print(f"\nTo generate PDF:")
    print(f"1. Open the HTML file in your browser")
    print(f"2. Click 'Print / Save as PDF' button (or press Ctrl+P)")
    print(f"3. Select 'Save as PDF' as the printer")
    print(f"4. Save the PDF file")

def main():
    # File paths
    script_dir = Path(__file__).parent
    md_file = script_dir / "project-presentation-report.md"
    html_file = script_dir / "project-presentation-report.html"
    
    if not md_file.exists():
        print(f"[ERROR] {md_file} not found!")
        return
    
    print(f"Converting {md_file.name} to HTML...")
    convert_md_to_html(md_file, html_file)

if __name__ == "__main__":
    main()
