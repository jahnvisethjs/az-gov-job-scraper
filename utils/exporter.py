"""
Export Utility - Export jobs and matches to various formats.

Supports CSV, JSON, and PDF exports.
"""

import csv
import json
from typing import List, Dict
from io import StringIO, BytesIO
from datetime import datetime


def export_to_csv(jobs: List[Dict]) -> str:
    """
    Export jobs to CSV format.
    
    Args:
        jobs: List of job dictionaries
        
    Returns:
        CSV string
    """
    if not jobs:
        return ""
    
    output = StringIO()
    
    # Define fields to export
    fieldnames = [
        "title",
        "city",
        "department",
        "salary",
        "posted_date",
        "deadline",
        "url",
        "match_score"
    ]
    
    writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction='ignore')
    writer.writeheader()
    
    for job in jobs:
        # Flatten job data
        row = {
            "title": job.get("title", ""),
            "city": job.get("city", ""),
            "department": job.get("department", ""),
            "salary": job.get("salary", ""),
            "posted_date": job.get("posted_date", ""),
            "deadline": job.get("deadline", ""),
            "url": job.get("url", ""),
            "match_score": job.get("match_score", "")
        }
        writer.writerow(row)
    
    return output.getvalue()


def export_to_json(jobs: List[Dict], pretty: bool = True) -> str:
    """
    Export jobs to JSON format.
    
    Args:
        jobs: List of job dictionaries
        pretty: Whether to format JSON prettily
        
    Returns:
        JSON string
    """
    if pretty:
        return json.dumps(jobs, indent=2, ensure_ascii=False)
    else:
        return json.dumps(jobs, ensure_ascii=False)


def export_to_pdf(jobs: List[Dict], include_descriptions: bool = False) -> bytes:
    """
    Export jobs to PDF format.
    
    Args:
        jobs: List of job dictionaries
        include_descriptions: Whether to include full job descriptions
        
    Returns:
        PDF bytes
    """
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib import colors
    except ImportError:
        raise ImportError("reportlab is required for PDF export. Install with: pip install reportlab")
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1E40AF'),
        spaceAfter=30
    )
    title = Paragraph("Arizona Government Job Matches", title_style)
    story.append(title)
    
    # Metadata
    meta_text = f"Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}<br/>Total Jobs: {len(jobs)}"
    meta = Paragraph(meta_text, styles['Normal'])
    story.append(meta)
    story.append(Spacer(1, 0.3*inch))
    
    # Jobs
    for i, job in enumerate(jobs, 1):
        # Job title
        job_title_style = ParagraphStyle(
            'JobTitle',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#1E40AF')
        )
        job_title = Paragraph(f"{i}. {job.get('title', 'Untitled')}", job_title_style)
        story.append(job_title)
        
        # Job details table
        data = [
            ["City:", job.get('city', 'N/A')],
            ["Department:", job.get('department', 'N/A')],
            ["Salary:", job.get('salary', 'N/A')],
            ["Posted:", job.get('posted_date', 'N/A')],
        ]
        
        if job.get('match_score'):
            data.append(["Match Score:", f"{job['match_score']:.1f}%"])
        
        if job.get('url'):
            data.append(["URL:", job['url'][:60] + "..."])
        
        table = Table(data, colWidths=[1.5*inch, 4.5*inch])
        table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(table)
        
        # Description (if requested)
        if include_descriptions and job.get('description'):
            desc = Paragraph(f"<b>Description:</b> {job['description'][:200]}...", styles['Normal'])
            story.append(desc)
        
        story.append(Spacer(1, 0.2*inch))
    
    # Build PDF
    doc.build(story)
    
    return buffer.getvalue()


def get_export_filename(format_type: str) -> str:
    """
    Get a default filename for exports.
    
    Args:
        format_type: 'csv', 'json', or 'pdf'
        
    Returns:
        Filename with timestamp
    """
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    return f"az_gov_jobs_{timestamp}.{format_type}"
