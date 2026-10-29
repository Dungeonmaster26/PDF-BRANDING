import streamlit as st
import fitz  # PyMuPDF
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

st.set_page_config(page_title="PDF Cleaner & Branding Tool", page_icon="📚", layout="centered")

st.title("📚 PDF Cleaner & Custom Brand Tool")
st.markdown("Easily clean academy headers, add custom YouTube footers, brand custom topic pages, and select clean-top pages.")

st.sidebar.header("⚙️ Settings")
custom_footer_text = st.sidebar.text_input("Footer Channel Suffix", value="Hindi Tark Channel")

uploaded_pdf = st.file_uploader("Upload Source PDF Document", type=["pdf"])

st.markdown("---")
st.subheader("📌 Page Customization Settings")

if 'topic_mappings' not in st.session_state:
    st.session_state.topic_mappings = {2: "Percentage"}

col_p1, col_t1, col_btn1 = st.columns([1, 2, 1])
with col_p1:
    new_topic_page = st.number_input("Topic Page No.", min_value=1, value=2, step=1, key="new_topic_page")
with col_t1:
    new_topic_title = st.text_input("Topic Title", value="Percentage", key="new_topic_title")
with col_btn1:
    st.text("") 
    if st.button("➕ Add Topic"):
        st.session_state.topic_mappings[int(new_topic_page)] = new_topic_title
        st.success(f"Added Page {new_topic_page}")

st.write("**Current Branded Topics:**", st.session_state.topic_mappings)

clean_pages_input = st.text_input("Clean-Top Page Numbers (comma-separated)", value="4")

if st.button("🚀 Process & Clean PDF", type="primary"):
    if uploaded_pdf is None:
        st.error("Please upload a source PDF file first!")
    else:
        with st.spinner("Processing your PDF... Please wait"):
            clean_pages_list = []
            try:
                if clean_pages_input.strip():
                    clean_pages_list = [int(p.strip()) for p in clean_pages_input.split(",") if p.strip().isdigit()]
            except Exception:
                clean_pages_list = []

            input_path = os.path.join(BASE_DIR, "temp_input.pdf")
            output_path = os.path.join(BASE_DIR, "Cleaned_Document.pdf")
            
            with open(input_path, "wb") as f:
                f.write(uploaded_pdf.getbuffer())
                
            logo_path = os.path.join(BASE_DIR, "logo.png")
            yt_logo_path = os.path.join(BASE_DIR, "youtube_logo.png")
            font_path = os.path.join(BASE_DIR, "AveriaSansLibre-Bold.ttf")

            try:
                doc = fitz.open(input_path)
                new_doc = fitz.open()

                logo_img = cv2.imread(logo_path, cv2.IMREAD_UNCHANGED)
                if logo_img is not None and logo_img.shape[2] == 3:
                    logo_img = cv2.cvtColor(logo_img, cv2.COLOR_BGR2BGRA)

                yt_img = cv2.imread(yt_logo_path, cv2.IMREAD_UNCHANGED)
                if yt_img is not None and yt_img.shape[2] == 3:
                    yt_img = cv2.cvtColor(yt_img, cv2.COLOR_BGR2BGRA)

                for p_idx in range(len(doc)):
                    page = doc[p_idx]
                    rect = page.rect
                    current_page_1_indexed = p_idx + 1
                    
                    pix = page.get_pixmap(dpi=300)
                    img_data = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.h, pix.w, pix.n)
                    
                    if pix.n == 4:
                        img = cv2.cvtColor(img_data, cv2.COLOR_RGBA2GRAY)
                    else:
                        img = cv2.cvtColor(img_data, cv2.COLOR_RGB2GRAY)

                    _, img = cv2.threshold(img, 170, 255, cv2.THRESH_BINARY)
                    img_color = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)

                    h_img, w_img = img_color.shape[:2]
                    scale = w_img / 1275.0

                    if current_page_1_indexed > 1:
                        cv2.rectangle(img_color, (0, h_img - int(170 * scale)), (w_img, h_img), (255, 255, 255), -1)

                    if current_page_1_indexed > 1 and current_page_1_indexed in st.session_state.topic_mappings:
                        cv2.rectangle(img_color, (0, 0), (w_img, int(410 * scale)), (255, 255, 255), -1)

                    if current_page_1_indexed in clean_pages_list:
                        cv2.rectangle(img_color, (0, 0), (w_img, int(119 * scale)), (255, 255, 255), -1)

                    if logo_img is not None and current_page_1_indexed > 1 and current_page_1_indexed in st.session_state.topic_mappings:
                        watermark_size = int(720 * scale)
                        resized_wm = cv2.resize(logo_img, (watermark_size, watermark_size), interpolation=cv2.INTER_AREA)
                        wm_y = (h_img - watermark_size) // 2
                        wm_x = (w_img - watermark_size) // 2
                        for c in range(0, 3):
                            alpha = (resized_wm[:, :, 3] / 255.0) * 0.10 
                            roi = img_color[wm_y:wm_y+watermark_size, wm_x:wm_x+watermark_size, c]
                            img_color[wm_y:wm_y+watermark_size, wm_x:wm_x+watermark_size, c] = (
                                alpha * resized_wm[:, :, c] + (1 - alpha) * roi
                            )

                    pil_img = Image.fromarray(cv2.cvtColor(img_color, cv2.COLOR_RGB2BGR))
                    draw = ImageDraw.Draw(pil_img)

                    # Safe Font Loading (Using your uploaded font or standard fallback)
                    try:
                        font_title = ImageFont.truetype(font_path, int(64 * scale))
                        font_pill = ImageFont.truetype(font_path, int(52 * scale))
                        font_tagline = ImageFont.truetype(font_path, int(15 * scale))
                        font_page_num = ImageFont.truetype(font_path, int(22 * scale))
                        font_footer = ImageFont.truetype(font_path, int(36 * scale))
                    except Exception:
                        font_title = ImageFont.load_default()
                        font_pill = ImageFont.load_default()
                        font_tagline = ImageFont.load_default()
                        font_page_num = ImageFont.load_default()
                        font_footer = ImageFont.load_default()

                    if logo_img is not None and current_page_1_indexed > 1 and current_page_1_indexed in st.session_state.topic_mappings:
                        box_left, box_top, box_right, box_bottom = int(150 * scale), int(115 * scale), int(1123 * scale), int(340 * scale)
                        draw.rounded_rectangle([box_left, box_top, box_right, box_bottom], radius=int(16 * scale), fill=(230, 230, 230), outline=(0, 0, 0), width=max(2, int(2.5 * scale)))

                        x_offset = int(955 * scale)
                        available_width = x_offset - box_left
                        available_space_center = box_left + (available_width // 2)

                        topic_title = st.session_state.topic_mappings[current_page_1_indexed]
                        target_size = int(150 * scale)
                        logo_pil = Image.fromarray(cv2.cvtColor(logo_img, cv2.COLOR_BGRA2RGBA))
                        logo_pil = logo_pil.resize((target_size, target_size), Image.Resampling.LANCZOS)
                        pil_img.paste(logo_pil, (x_offset, int(125 * scale)), logo_pil)

                        draw.text((available_space_center - 150, int(124 * scale)), "HINDI TARK CLASSES", fill=(0, 0, 0), font=font_title)
                        draw.text((available_space_center - 100, int(205 * scale)), topic_title, fill=(255, 255, 255), font=font_pill)

                    if current_page_1_indexed > 1:
                        page_str = f"( {current_page_1_indexed} )"
                        footer_x = (w_img // 2) - 200
                        footer_y = h_img - int(120 * scale)
                        draw.text((footer_x, footer_y), f"{page_str} Join YouTube {custom_footer_text}", fill=(50, 50, 50), font=font_footer)

                    img_color = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
                    success, encoded_img = cv2.imencode(".jpg", img_color, [cv2.IMWRITE_JPEG_QUALITY, 95])
                    if success:
                        new_page = new_doc.new_page(width=rect.width, height=rect.height)
                        new_page.insert_image(rect, stream=encoded_img.tobytes())

                new_doc.save(output_path, garbage=4, deflate=True)
                new_doc.close()
                doc.close()
                
                st.success("✅ PDF Processed Successfully!")
                with open(output_path, "rb") as file:
                    st.download_button(
                        label="📥 Download Cleaned & Branded PDF",
                        data=file,
                        file_name="Cleaned_Document.pdf",
                        mime="application/pdf"
                    )

            except Exception as e:
                st.error(f"An error occurred during processing: {e}")

