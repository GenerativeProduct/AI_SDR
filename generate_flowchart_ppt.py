from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN
from pptx.dml.color import RGBColor

def create_hub_flowchart():
    prs = Presentation()
    prs.slide_height = Inches(10)
    prs.slide_width = Inches(10)

    slide_layout = prs.slide_layouts[6]
    slide = prs.slides.add_slide(slide_layout)

    # Title
    txBox = slide.shapes.add_textbox(Inches(1), Inches(0.2), Inches(8), Inches(0.5))
    tf = txBox.text_frame
    p = tf.paragraphs[0]
    p.text = "AI Marketing Agent Product Architecture (7-Step Flow)"
    p.font.size = Pt(22)
    p.font.bold = True
    p.font.color.rgb = RGBColor(16, 185, 129)
    p.alignment = PP_ALIGN.CENTER

    def add_box(txt, x, y, w, h=0.6, color=(240, 248, 245), text_color=(15, 23, 42)):
        shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
        shape.fill.solid()
        shape.fill.fore_color.rgb = RGBColor(*color)
        shape.line.color.rgb = RGBColor(16, 185, 129)
        shape.line.width = Pt(1.5)
        
        tf = shape.text_frame
        tf.word_wrap = True
        
        lines = txt.split("\n")
        p1 = tf.paragraphs[0]
        p1.text = lines[0]
        p1.font.size = Pt(11)
        p1.font.bold = True
        p1.font.color.rgb = RGBColor(*text_color)
        p1.alignment = PP_ALIGN.CENTER
        
        if len(lines) > 1:
            p2 = tf.add_paragraph()
            p2.text = lines[1]
            p2.font.size = Pt(9)
            p2.font.color.rgb = RGBColor(71, 85, 105)
            p2.alignment = PP_ALIGN.CENTER
        return shape

    def add_arrow(sx, sy, ex, ey, shape_type=MSO_SHAPE.DOWN_ARROW):
        w = abs(ex - sx)
        h = abs(ey - sy)
        if w < 0.1: w = 0.15 # Minimum width for vertical arrows
        if h < 0.1: h = 0.15 # Minimum height for horizontal arrows
        
        # Calculate bounding box for the arrow
        left = min(sx, ex)
        top = min(sy, ey)

        arr = slide.shapes.add_shape(shape_type, Inches(left), Inches(top), Inches(w), Inches(h))
        arr.fill.solid()
        arr.fill.fore_color.rgb = RGBColor(15, 118, 110)
        arr.line.color.rgb = RGBColor(15, 118, 110)
        return arr

    # Coordinates
    center_x = 3.5
    w_main = 3.2
    w_sat = 2.4
    
    # Core Pipeline
    add_box("1. Event Tracking\n(clicks, form submit, views)", center_x, 1.0, w_main)
    add_arrow(center_x + w_main/2 - 0.075, 1.6, center_x + w_main/2 + 0.075, 1.85, MSO_SHAPE.DOWN_ARROW)
    
    add_box("2. Personalization Agent\n(Uses profile, events, segment)", center_x, 2.0, w_main)
    add_arrow(center_x + w_main/2 - 0.075, 2.6, center_x + w_main/2 + 0.075, 2.85, MSO_SHAPE.DOWN_ARROW)
    
    add_box("3. Lead Scoring\n(assigns behavior scores)", center_x, 3.0, w_main)
    add_arrow(center_x + w_main/2 - 0.075, 3.6, center_x + w_main/2 + 0.075, 3.85, MSO_SHAPE.DOWN_ARROW)
    
    add_box("4. Customer Profile + Segmentation\n(Bronze/Silver/Gold/Platinum rules)", center_x, 4.0, w_main, color=(219, 234, 254))
    add_arrow(center_x + w_main/2 - 0.075, 4.6, center_x + w_main/2 + 0.075, 5.0, MSO_SHAPE.DOWN_ARROW)
    
    # ORCHESTRATION HUB
    add_box("5. Campaign Orchestration Hub\nDecision center, freq control, manual/auto", center_x, 5.15, w_main, h=0.7, color=(209, 250, 229))
    
    # Hub Spacing - Channel Agents (Step 6)
    # Email Agent (Left)
    add_box("6A. Email Agent\n(Subject, body, open rates)", 0.5, 6.2, w_sat, 0.7)
    add_arrow(2.9, 5.5, 2.9, 6.2, MSO_SHAPE.DOWN_ARROW)
    
    # SMS Agent (Center)
    add_box("6B. SMS Agent\n(Short CTA, urgency copy)", center_x + 0.4, 6.2, w_sat, 0.7)
    add_arrow(center_x + w_main/2 - 0.075, 5.85, center_x + w_main/2 + 0.075, 6.2, MSO_SHAPE.DOWN_ARROW)

    # Social/Other Agent (Right)
    add_box("6C. Social Agent\n(Ads, DMs)", 7.1, 6.2, w_sat, 0.7)
    add_arrow(7.1, 5.5, 7.1, 6.2, MSO_SHAPE.DOWN_ARROW)
    
    # Step 7 CRM + Analytics Aggregation
    add_box("7. CRM & Customer Details\nHistory, lead interaction, next action", center_x, 7.8, w_main, h=0.8, color=(226, 232, 240))
    
    # Connectors from the 3 agents down into CRM
    # SMS (Center) -> CRM
    add_arrow(center_x + 0.4 + w_sat/2 - 0.075, 6.9, center_x + 0.4 + w_sat/2 + 0.075, 7.8, MSO_SHAPE.DOWN_ARROW)
    
    # We will use simple elbow connectors for Email and Social
    conn1 = slide.shapes.add_connector(
        1, # MSO_CONNECTOR_ELBOW
        Inches(0.5 + w_sat/2), Inches(6.9), Inches(center_x), Inches(8.2)
    )
    conn1.line.color.rgb = RGBColor(15, 118, 110)
    conn1.line.width = Pt(2)
    
    conn2 = slide.shapes.add_connector(
        1,
        Inches(7.1 + w_sat/2), Inches(6.9), Inches(center_x + w_main), Inches(8.2)
    )
    conn2.line.color.rgb = RGBColor(15, 118, 110)
    conn2.line.width = Pt(2)

    prs.save("AI_marketing_agent_architecture.pptx")
    print("Successfully generated AI_marketing_agent_architecture.pptx")

if __name__ == "__main__":
    create_hub_flowchart()
