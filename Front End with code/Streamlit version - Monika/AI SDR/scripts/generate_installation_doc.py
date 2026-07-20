import docx
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn
import os

def create_element(name):
    return OxmlElement(name)

def set_cell_shading(cell, color_hex):
    shading_xml = f'<w:shd {nsdecls("w")} w:fill="{color_hex}"/>'
    cell._tc.get_or_add_tcPr().append(parse_xml(shading_xml))

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for m, val in [('w:top', top), ('w:bottom', bottom), ('w:left', left), ('w:right', right)]:
        node = OxmlElement(m)
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)

def add_horizontal_border(paragraph, color_hex="CCCCCC", size=12):
    pPr = paragraph._p.get_or_add_pPr()
    pBdr = OxmlElement('w:pBdr')
    bottom = OxmlElement('w:bottom')
    bottom.set(qn('w:val'), 'single')
    bottom.set(qn('w:sz'), str(size))
    bottom.set(qn('w:space'), '4')
    bottom.set(qn('w:color'), color_hex)
    pBdr.append(bottom)
    pPr.append(pBdr)

def build_document():
    doc = Document()
    
    # Page setup
    section = doc.sections[0]
    section.top_margin = Inches(1)
    section.bottom_margin = Inches(1)
    section.left_margin = Inches(1)
    section.right_margin = Inches(1)
    
    # Configure style formats
    styles = doc.styles
    
    # Title Style
    title_style = styles.add_style('App Title', docx.enum.style.WD_STYLE_TYPE.PARAGRAPH)
    title_font = title_style.font
    title_font.name = 'Segoe UI'
    title_font.size = Pt(26)
    title_font.bold = True
    title_font.color.rgb = RGBColor(15, 23, 42) # Slate 900
    
    # Subtitle Style
    subtitle_style = styles.add_style('App Subtitle', docx.enum.style.WD_STYLE_TYPE.PARAGRAPH)
    sub_font = subtitle_style.font
    sub_font.name = 'Segoe UI'
    sub_font.size = Pt(14)
    sub_font.color.rgb = RGBColor(100, 116, 139) # Slate 500
    
    # Heading 1 Style
    h1_style = styles['Heading 1']
    h1_font = h1_style.font
    h1_font.name = 'Segoe UI'
    h1_font.size = Pt(18)
    h1_font.bold = True
    h1_font.color.rgb = RGBColor(30, 58, 138) # Navy Blue
    
    # Heading 2 Style
    h2_style = styles['Heading 2']
    h2_font = h2_style.font
    h2_font.name = 'Segoe UI'
    h2_font.size = Pt(14)
    h2_font.bold = True
    h2_font.color.rgb = RGBColor(13, 148, 136) # Teal
    
    # Body Style
    normal_style = styles['Normal']
    normal_font = normal_style.font
    normal_font.name = 'Calibri'
    normal_font.size = Pt(11.5)
    normal_font.color.rgb = RGBColor(55, 65, 81) # Charcoal
    
    # ------------------ COVER HEADER ------------------
    p = doc.add_paragraph('AI SDR PLATFORM', style='App Title')
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    
    ps = doc.add_paragraph('Quick Installation & Setup Guide (Windows & macOS)', style='App Subtitle')
    ps.alignment = WD_ALIGN_PARAGRAPH.LEFT
    add_horizontal_border(ps, color_hex="1E3A8A", size=24) # Thick primary color border
    
    doc.add_paragraph('\n')
    
    # ------------------ INTRODUCTION ------------------
    h = doc.add_heading('1. Overview', level=1)
    doc.add_paragraph(
        "The AI SDR Platform is a production-shaped Autonomous Sales Development Representative system. "
        "It features a FastAPI backend running AI agent workflows and a responsive React frontend dashboard. "
        "To make deployment simple, the platform runs in isolated containers using Docker. "
        "This guide walks you through the 2-click installation process for both Windows and Apple/macOS environments."
    )
    
    # ------------------ PREREQUISITES ------------------
    doc.add_heading('2. Requirements & Virtualization', level=1)
    doc.add_paragraph(
        "To run the application locally, Docker Desktop must be installed and active. "
        "The included launcher scripts are designed to automatically detect Docker, download the installer if it is missing, "
        "and handle starting up the services for you. However, you must ensure virtualization is enabled in your system's BIOS/UEFI settings."
    )
    
    # Callout Box for Windows WSL 2
    table = doc.add_table(rows=1, cols=1)
    table.alignment = docx.enum.table.WD_TABLE_ALIGNMENT.CENTER
    cell = table.cell(0, 0)
    set_cell_shading(cell, "FEF3C7") # Warm Yellow Alert
    set_cell_margins(cell, top=140, bottom=140, left=200, right=200)
    
    # Customize cell border
    tcPr = cell._tc.get_or_add_tcPr()
    tcBorders = OxmlElement('w:tcBorders')
    left_bdr = OxmlElement('w:left')
    left_bdr.set(qn('w:val'), 'single')
    left_bdr.set(qn('w:sz'), '36') # Thick border
    left_bdr.set(qn('w:color'), 'D97706') # Darker yellow/orange
    tcBorders.append(left_bdr)
    for side in ['top', 'bottom', 'right']:
        bdr = OxmlElement(f'w:{side}')
        bdr.set(qn('w:val'), 'none')
        tcBorders.append(bdr)
    tcPr.append(tcBorders)
    
    cp = cell.paragraphs[0]
    r = cp.add_run("IMPORTANT NOTE (Windows WSL 2 requirement): ")
    r.bold = True
    r.font.color.rgb = RGBColor(180, 83, 9)
    r2 = cp.add_run(
        "Windows requires the Windows Subsystem for Linux (WSL 2) to run Docker. "
        "If you do not have WSL 2 enabled, the Docker Desktop installer will prompt you to enable it and reboot. "
        "Please restart your PC when prompted, then re-run the launcher."
    )
    r2.font.color.rgb = RGBColor(120, 53, 4)
    
    doc.add_paragraph('')
    
    # ------------------ WINDOWS INSTALLATION ------------------
    doc.add_heading('3. Windows Installation (2 Clicks)', level=1)
    
    p = doc.add_paragraph()
    r1 = p.add_run("Step 1: ")
    r1.bold = True
    p.add_run("Double-click the ")
    r2 = p.add_run("start_windows.bat")
    r2.bold = True
    r2.font.color.rgb = RGBColor(30, 58, 138)
    p.add_run(" file in the project folder.")
    
    doc.add_paragraph(
        "This batch script runs a PowerShell controller script that checks if Docker Desktop is installed. "
        "If Docker is missing, it will ask for permission to download and launch the Docker installer. "
        "Once Docker is installed, the script will launch Docker Desktop and wait for it to start up."
    )
    
    p = doc.add_paragraph()
    r1 = p.add_run("Step 2: ")
    r1.bold = True
    p.add_run("Wait for the browser to launch.")
    
    doc.add_paragraph(
        "The script will automatically build and start the Docker containers for the backend API and the React frontend. "
        "Once everything is ready, it opens your default browser automatically to: "
    ).paragraph_format.space_after = Pt(2)
    
    # Bullet point link
    p_link = doc.add_paragraph(style='List Bullet')
    p_link.add_run("http://localhost:8080").bold = True
    
    # ------------------ MAC INSTALLATION ------------------
    doc.add_heading('4. macOS / Apple Installation (2 Clicks)', level=1)
    
    p = doc.add_paragraph()
    r1 = p.add_run("Step 1: ")
    r1.bold = True
    p.add_run("Double-click the ")
    r2 = p.add_run("start_mac.command")
    r2.bold = True
    r2.font.color.rgb = RGBColor(13, 148, 136)
    p.add_run(" file in the project folder.")
    
    doc.add_paragraph(
        "The macOS terminal launcher will execute. It will automatically detect your Mac architecture "
        "(Apple Silicon M1/M2/M3 or Intel CPU) and download/install Docker Desktop if it is not already in your Applications directory. "
        "It will launch the Docker app and wait until it is ready."
    )
    
    # Note on terminal permissions
    p_perm = doc.add_paragraph()
    p_perm.add_run("Note: ").bold = True
    p_perm.add_run(
        "When running a .command file for the first time, macOS Gatekeeper may ask for confirmation or "
        "prompt to grant Terminal access. Please click 'Open' and enter your user password if prompted by the installer."
    )
    
    p = doc.add_paragraph()
    r1 = p.add_run("Step 2: ")
    r1.bold = True
    p.add_run("Access the application.")
    
    doc.add_paragraph(
        "The script runs the docker-compose deployment command and launches the app in your browser at: "
    ).paragraph_format.space_after = Pt(2)
    
    p_link2 = doc.add_paragraph(style='List Bullet')
    p_link2.add_run("http://localhost:8080").bold = True
    
    # ------------------ LOGIN CREDENTIALS ------------------
    doc.add_heading('5. System Credentials & URLs', level=1)
    doc.add_paragraph("Once the installation completes, use the following details to log in to the platform:")
    
        # Create Credentials Table
    cred_table = doc.add_table(rows=5, cols=2)
    cred_table.alignment = docx.enum.table.WD_TABLE_ALIGNMENT.CENTER
    
    # Style Table Header
    hdr_cells = cred_table.rows[0].cells
    hdr_cells[0].text = 'Setting / Detail'
    hdr_cells[1].text = 'Value'
    for cell in hdr_cells:
        set_cell_shading(cell, "1E3A8A") # Dark Navy Header
        set_cell_margins(cell, top=100, bottom=100, left=150, right=150)
        cell.paragraphs[0].runs[0].font.color.rgb = RGBColor(255, 255, 255)
        cell.paragraphs[0].runs[0].bold = True
        cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.LEFT
        
    row_data = [
        ("Web Dashboard (React UI)", "http://localhost:8080"),
        ("FastAPI Swagger Docs (API)", "http://localhost:8011/docs"),
        ("Default Login Email", "admin@sdr.local"),
        ("Default Login Password", "admin123")
    ]
    
    for i, (label, val) in enumerate(row_data):
        row = cred_table.rows[i+1]
        row.cells[0].text = label
        row.cells[1].text = val
        
        # Style cell margins and background alternating coloring
        bg_color = "F1F5F9" if i % 2 == 0 else "FFFFFF"
        for cell in row.cells:
            set_cell_shading(cell, bg_color)
            set_cell_margins(cell, top=80, bottom=80, left=150, right=150)
            
            # Formatting links
            if "http://" in cell.text:
                run = cell.paragraphs[0].runs[0]
                run.font.color.rgb = RGBColor(37, 99, 235)
                run.bold = True
    
    doc.add_paragraph('\n')
    
    # ------------------ TROUBLESHOOTING ------------------
    doc.add_heading('6. Troubleshooting & FAQs', level=1)
    
    doc.add_heading("Docker is running but commands fail", level=2)
    doc.add_paragraph(
        "Make sure Docker Desktop has finished starting. On Windows, verify that the whale icon in the "
        "system tray is solid green. On Mac, check the menu bar whale icon."
    )
    
    doc.add_heading("Port 8080 or 8011 is already in use", level=2)
    doc.add_paragraph(
        "If you are running another local server on port 8080 or 8011, Docker compose will fail to bind to the port. "
        "You can stop the conflicting process or change the exposed ports in the 'docker-compose.yml' file."
    )
    
    doc.add_heading("WSL 2 installation fails or requests update", level=2)
    doc.add_paragraph(
        "If Windows prompts you to update the WSL kernel, open a Command Prompt as Administrator and run: "
        "'wsl --update'. Then restart Docker Desktop."
    )
    
    # Save the generated document
    output_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "AI_SDR_Installation_Guide.docx")
    doc.save(output_path)
    print(f"Successfully generated installation guide Word doc at: {output_path}")

if __name__ == "__main__":
    build_document()
