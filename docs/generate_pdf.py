"""
Script to convert project-presentation-report.md to PDF
"""
import markdown
import os
from pathlib import Path

try:
    # Try using markdown and pdfkit
    from weasyprint import HTML, CSS
    USE_WEASYPRINT = True
except ImportError:
    USE_WEASYPRINT = False
    try:
        import pdfkit
        USE_PDFKIT = True
    except ImportError:
        USE_PDFKIT = False

def convert_md_to_pdf_weasyprint(md_file, pdf_file):
    """Convert markdown to PDF using WeasyPrint"""
    # Read markdown file
    with open(md_file, 'r', encoding='utf-8') as f:
        md_content = f.read()
    
    # Convert markdown to HTML
    html_content = markdown.markdown(
        md_content,
        extensions=['tables', 'fenced_code', 'codehilite']
    )
    
    # Add CSS styling
    css_style = """
    <style>
        body {
            font-family: 'Segoe UI', Arial, sans-serif;
            line-height: 1.6;
            margin: 40px;
            color: #333;
        }
        h1 {
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }
        h2 {
            color: #34495e;
            border-bottom: 2px solid #95a5a6;
            padding-bottom: 8px;
            margin-top: 30px;
        }
        h3 {
            color: #7f8c8d;
            margin-top: 20px;
        }
        table {
            border-collapse: collapse;
            width: 100%;
            margin: 20px 0;
        }
        th, td {
            border: 1px solid #ddd;
            padding: 12px;
            text-align: left;
        }
        th {
            background-color: #3498db;
            color: white;
        }
        tr:nth-child(even) {
            background-color: #f2f2f2;
        }
        code {
            background-color: #f4f4f4;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
        }
        pre {
            background-color: #2c3e50;
            color: #ecf0f1;
            padding: 15px;
            border-radius: 5px;
            overflow-x: auto;
        }
        blockquote {
            border-left: 4px solid #3498db;
            padding-left: 20px;
            margin: 20px 0;
            font-style: italic;
            color: #555;
        }
        hr {
            border: none;
            border-top: 2px solid #ecf0f1;
            margin: 30px 0;
        }
    </style>
    """
    
    # Combine HTML
    full_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        {css_style}
    </head>
    <body>
        {html_content}
    </body>
    </html>
    """
    
    # Convert to PDF
    HTML(string=full_html).write_pdf(pdf_file)
    print(f"[SUCCESS] PDF generated successfully: {pdf_file}")

def convert_md_to_pdf_pdfkit(md_file, pdf_file):
    """Convert markdown to PDF using pdfkit"""
    # Read markdown file
    with open(md_file, 'r', encoding='utf-8') as f:
        md_content = f.read()
    
    # Convert markdown to HTML
    html_content = markdown.markdown(
        md_content,
        extensions=['tables', 'fenced_code']
    )
    
    # Convert to PDF
    pdfkit.from_string(html_content, pdf_file)
    print(f"[SUCCESS] PDF generated successfully: {pdf_file}")

def main():
    # File paths
    script_dir = Path(__file__).parent
    md_file = script_dir / "project-presentation-report.md"
    pdf_file = script_dir / "project-presentation-report.pdf"
    
    if not md_file.exists():
        print(f"[ERROR] Error: {md_file} not found!")
        return
    
    print(f"Converting {md_file.name} to PDF...")
    
    try:
        if USE_WEASYPRINT:
            print("Using WeasyPrint...")
            convert_md_to_pdf_weasyprint(md_file, pdf_file)
        elif USE_PDFKIT:
            print("Using pdfkit...")
            convert_md_to_pdf_pdfkit(md_file, pdf_file)
        else:
            print("[ERROR] No PDF conversion library found!")
            print("Installing required packages...")
            os.system("pip install markdown weasyprint")
            print("\nPlease run this script again after installation.")
            return
    except Exception as e:
        print(f"[ERROR] Error generating PDF: {e}")
        print("\nTrying to install dependencies...")
        os.system("pip install markdown weasyprint")
        print("\nPlease run this script again after installation.")

if __name__ == "__main__":
    main()
