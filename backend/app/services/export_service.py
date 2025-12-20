"""
Forensic Export Service for TOR-Unveil
Generates exportable reports in multiple formats (PDF, CSV, JSON)
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from io import BytesIO, StringIO
import json
import csv

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    print("Warning: ReportLab not installed. PDF export will not be available.")

class ForensicExporter:
    """Generates forensic reports for TOR traffic analysis"""
    
    def __init__(self):
        self.styles = getSampleStyleSheet() if REPORTLAB_AVAILABLE else None
        
    def generate_pdf_report(self,
                          analysis_data: List[Dict],
                          metadata: Dict,
                          timeline_events: List[Dict] = None,
                          correlations: List[Dict] = None) -> BytesIO:
        """
        Generate PDF forensic report
        
        Args:
            analysis_data: Analysis results data
            metadata: Report metadata (timestamps, IPs, etc.)
            timeline_events: Optional timeline events
            correlations: Optional node correlations
            
        Returns:
            BytesIO buffer containing PDF
        """
        if not REPORTLAB_AVAILABLE:
            raise ImportError("ReportLab is required for PDF generation")
        
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter,
                              rightMargin=72, leftMargin=72,
                              topMargin=72, bottomMargin=18)
        
        story = []
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1a1a1a'),
            spaceAfter=30,
            alignment=TA_CENTER
        )
        title = Paragraph("TOR-Unveil Forensic Analysis Report", title_style)
        story.append(title)
        story.append(Spacer(1, 12))
        
        # Metadata section
        story.append(Paragraph("<b>Report Metadata</b>", self.styles['Heading2']))
        metadata_data = [
            ['Analysis ID:', str(metadata.get('analysis_id', 'N/A'))],
            ['Generated:', datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')],
            ['Source IP:', metadata.get('source_ip', 'N/A')],
            ['Destination IP:', metadata.get('destination_ip', 'N/A')],
            ['Guards Analyzed:', str(metadata.get('guards_analyzed', 0))]
        ]
        
        metadata_table = Table(metadata_data, colWidths=[2*inch, 4*inch])
        metadata_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f0f0f0')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey)
        ]))
        story.append(metadata_table)
        story.append(Spacer(1, 20))
        
        # Analysis Summary
        story.append(Paragraph("<b>Analysis Summary</b>", self.styles['Heading2']))
        if analysis_data and len(analysis_data) > 0:
            summary_data = [['Rank', 'Guard Fingerprint', 'Confidence', 'Country']]
            
            for idx, item in enumerate(analysis_data[:10], 1):
                summary_data.append([
                    str(idx),
                    item.get('fingerprint', 'N/A')[:20] + '...',
                    f"{item.get('confidence_score', 0):.2f}%",
                    item.get('country', 'N/A')
                ])
            
            summary_table = Table(summary_data, colWidths=[0.7*inch, 2.5*inch, 1.3*inch, 1.5*inch])
            summary_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4a90e2')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 11),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(summary_table)
        else:
            story.append(Paragraph("No analysis data available.", self.styles['Normal']))
        
        story.append(Spacer(1, 20))
        
        # Timeline Events
        if timeline_events and len(timeline_events) > 0:
            story.append(Paragraph("<b>Timeline Events</b>", self.styles['Heading2']))
            timeline_data = [['Timestamp', 'Event Type', 'Node']]
            
            for event in timeline_events[:20]:
                timeline_data.append([
                    event.get('timestamp', 'N/A')[:19],
                    event.get('event_type', 'N/A'),
                    event.get('node_fingerprint', 'N/A')[:15] + '...' if event.get('node_fingerprint') else 'N/A'
                ])
            
            timeline_table = Table(timeline_data, colWidths=[2*inch, 2*inch, 2*inch])
            timeline_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495e')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey)
            ]))
            story.append(timeline_table)
            story.append(Spacer(1, 20))
        
        # Node Correlations
        if correlations and len(correlations) > 0:
            story.append(Paragraph("<b>Node Correlations</b>", self.styles['Heading2']))
            corr_data = [['Entry Node', 'Exit Node', 'Score', 'Time Delta (s)']]
            
            for corr in correlations[:15]:
                corr_data.append([
                    corr.get('entry_fingerprint', 'N/A')[:15] + '...',
                    corr.get('exit_fingerprint', 'N/A')[:15] + '...',
                    f"{corr.get('correlation_score', 0):.3f}",
                    str(corr.get('time_delta_seconds', 'N/A'))
                ])
            
            corr_table = Table(corr_data, colWidths=[1.8*inch, 1.8*inch, 1.2*inch, 1.2*inch])
            corr_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2ecc71')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey)
            ]))
            story.append(corr_table)
        
        # Footer
        story.append(Spacer(1, 40))
        footer_style = ParagraphStyle(
            'Footer',
            parent=self.styles['Normal'],
            fontSize=8,
            textColor=colors.grey,
            alignment=TA_CENTER
        )
        footer = Paragraph(
            "This report is generated by TOR-Unveil for forensic analysis purposes.<br/>"
            "Confidential - For authorized use only.",
            footer_style
        )
        story.append(footer)
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        
        return buffer
    
    def generate_csv_report(self,
                          analysis_data: List[Dict],
                          metadata: Dict) -> StringIO:
        """
        Generate CSV forensic report
        
        Args:
            analysis_data: Analysis results data
            metadata: Report metadata
            
        Returns:
            StringIO buffer containing CSV
        """
        buffer = StringIO()
        
        # Write metadata header
        writer = csv.writer(buffer)
        writer.writerow(['# TOR-Unveil Forensic Analysis Report'])
        writer.writerow(['# Generated:', datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')])
        writer.writerow(['# Analysis ID:', metadata.get('analysis_id', 'N/A')])
        writer.writerow(['# Source IP:', metadata.get('source_ip', 'N/A')])
        writer.writerow(['# Destination IP:', metadata.get('destination_ip', 'N/A')])
        writer.writerow([])
        
        # Write analysis data
        if analysis_data and len(analysis_data) > 0:
            headers = ['Rank', 'Guard_Fingerprint', 'Confidence_Score', 'Country', 'Bandwidth', 'Probability']
            writer.writerow(headers)
            
            for idx, item in enumerate(analysis_data, 1):
                writer.writerow([
                    idx,
                    item.get('fingerprint', 'N/A'),
                    f"{item.get('confidence_score', 0):.2f}",
                    item.get('country', 'N/A'),
                    item.get('bandwidth', 'N/A'),
                    f"{item.get('probability_score', 0):.4f}"
                ])
        
        buffer.seek(0)
        return buffer
    
    def generate_json_report(self,
                           analysis_data: List[Dict],
                           metadata: Dict,
                           timeline_events: List[Dict] = None,
                           correlations: List[Dict] = None) -> str:
        """
        Generate JSON forensic report
        
        Args:
            analysis_data: Analysis results data
            metadata: Report metadata
            timeline_events: Optional timeline events
            correlations: Optional node correlations
            
        Returns:
            JSON string
        """
        report = {
            'report_metadata': {
                'generated_at': datetime.utcnow().isoformat(),
                'analysis_id': metadata.get('analysis_id'),
                'source_ip': metadata.get('source_ip'),
                'destination_ip': metadata.get('destination_ip'),
                'guards_analyzed': metadata.get('guards_analyzed', 0)
            },
            'analysis_results': analysis_data,
            'timeline_events': timeline_events or [],
            'node_correlations': correlations or [],
            'summary': {
                'total_guards': len(analysis_data),
                'top_confidence': analysis_data[0].get('confidence_score', 0) if analysis_data else 0,
                'timeline_event_count': len(timeline_events) if timeline_events else 0,
                'correlation_count': len(correlations) if correlations else 0
            }
        }
        
        return json.dumps(report, indent=2, default=str)
