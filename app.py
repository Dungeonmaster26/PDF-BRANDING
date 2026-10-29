import streamlit as st
import fitz  # PyMuPDF
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import os

# --- BASE DIRECTORY FIX FOR CLOUD DEPLOYMENT ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

st.set_page_config(page_title="PDF Cleaner & Branding Tool", page_icon="📚", layout="centered")

st.title("📚 PDF Cleaner & Custom Brand Tool")
st.markdown("Easily clean academy headers, add custom YouTube footers, brand custom topic pages, and select clean-top pages.")

# --- SIDEBAR CONFIGURATION ---
st.sidebar.header("⚙️ Settings")

custom_footer_text = st.sidebar.text_input("Footer Channel Suffix", value="Hindi Tark Channel")

st.sidebar.markdown("---")
st.sidebar.info("💡 **Note:** Assets like `logo.png` and `youtube_logo.png` are loaded automatically from the application folder.")

# --- MAIN FILE UPLOAD ---
uploaded_pdf = st.file_uploader("Upload Source PDF Document", type=["pdf"])

st.markdown("---")

# --- INTERACTIVE PAGE MAPPINGS ---
st.subheader("📌 Page Customization Settings")

# 1. Topic Branded Pages Configuration
st.markdown("### 1. Branded Topic Pages")
st.markdown("Add pages that need the full custom header box, title pill, and faint background watermark.")

if 'topic_mappings' not in st.session_state:
    st.session_state.topic_mappings = {2: "Percentage"} # Default starting example

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

topic_to_remove = st.selectbox("Remove a Topic Page (Optional)", options=[None] + list(st.session_state.topic_mappings.keys()))
if topic_to_remove:
    if st.button("🗑️ Remove Selected Topic Page"):
        del st.session_state.topic_mappings[topic_to_remove]
        st.rerun()

st.markdown("---")

# 2. Clean Top Pages Configuration (Like Page 4)
st.markdown("### 2. Clean-Top Pages (Academy Banner Removal)")
st.markdown("Select or type page numbers where you want the top academy banner cleanly wiped to white without adding a branded header box.")

clean_pages_input = st.text_input("Clean-Top Page Numbers (comma-separated)", value="4")

st.markdown("---")

# --- PROCESSING LOGIC ---
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
                
            # Permanent cloud-safe asset paths
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

                    # 1. Wipe footer on all pages > 1
                    if current_page_1_indexed > 1:
                        footer_wipe_height = int(170 * scale)
                        cv2.rectangle(img_color, (0, h_img - footer_wipe_height), (w_img, h_img), (255, 255, 255), -1)

                    # 2. Wipe top header area on topic pages
                    if current_page_1_indexed > 1 and current_page_1_indexed in st.session_state.topic_mappings:
                        top_wipe_height = int(410 * scale)
                        cv2.rectangle(img_color, (0, 0), (w_img, top_wipe_height), (255, 255, 255), -1)

                    # 3. Wipe top header area cleanly on user-specified clean pages
                    if current_page_1_indexed in clean_pages_list:
                        top_wipe_height = int(119 * scale)
                        cv2.rectangle(img_color, (0, 0), (w_img, top_wipe_height), (255, 255, 255), -1)

                    # 4. Watermark on topic pages
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

                    # Fonts using absolute paths
                    try:
                        font_title = ImageFont.truetype(font_path, int(64 * scale))
                        font_pill = ImageFont.truetype(font_path, int(52 * scale))
                        font_tagline = ImageFont.truetype("arial.ttf", int(15 * scale))
                        font_page_num = ImageFont.truetype("arialbd.ttf", int(22 * scale))
                        font_footer = ImageFont.truetype("arialbd.ttf", int(36 * scale))
                    except IOError:
                        font_title = ImageFont.truetype("arial.ttf", int(56 * scale))
                        font_pill = ImageFont.truetype("arial.ttf", int(52 * scale))
                        font_tagline = ImageFont.truetype("arial.ttf", int(15 * scale))
                        font_page_num = ImageFont.truetype("arial.ttf", int(22 * scale))
                        font_footer = ImageFont.truetype("arial.ttf", int(36 * scale))

                    # Draw Topic Header elements
                    if logo_img is not None and current_page_1_indexed > 1 and current_page_1_indexed in st.session_state.topic_mappings:
                        box_left = int(150 * scale)
                        box_top = int(115 * scale)
                        box_right = int(1123 * scale)
                        box_bottom = int(340 * scale)
                        
                        draw.rounded_rectangle([box_left, box_top, box_right, box_bottom], radius=int(16 * scale), fill=(230, 230, 230), outline=(0, 0, 0), width=max(2, int(2.5 * scale)))

                        x_offset = int(955 * scale)
                        available_width = x_offset - box_left
                        available_space_center = box_left + (available_width // 2)

                        topic_title = st.session_state.topic_mappings[current_page_1_indexed]
                        topic_bbox = font_pill.getbbox(topic_title)
                        topic_width = topic_bbox[2] - topic_bbox[0]
                        topic_height = topic_bbox[3] - topic_bbox[1]
                        
                        padding_x = int(80 * scale)
                        pill_width = topic_width + padding_x
                        pill_height = int(110 * scale)
                        
                        pill_left = available_space_center - (pill_width // 2)
                        pill_top = int(205 * scale)
                        pill_right = pill_left + pill_width
                        pill_bottom = pill_top + pill_height

                        draw.rounded_rectangle([pill_left, pill_top, pill_right, pill_bottom], radius=int(16 * scale), fill=(50, 50, 50))

                        target_size = int(150 * scale)
                        logo_pil = Image.fromarray(cv2.cvtColor(logo_img, cv2.COLOR_BGRA2RGBA))
                        logo_pil = logo_pil.resize((target_size, target_size), Image.Resampling.LANCZOS)
                        pil_img.paste(logo_pil, (x_offset, int(125 * scale)), logo_pil)

                        part1, part2, part3 = "HINDI ", "TARK", " CLASSES"
                        w1 = font_title.getbbox(part1)[2] - font_title.getbbox(part1)[0]
                        w2 = font_title.getbbox(part2)[2] - font_title.getbbox(part2)[0]
                        w3 = font_title.getbbox(part3)[2] - font_title.getbbox(part3)[0]
                        total_title_width = w1 + w2 + w3

                        title_x = available_space_center - (total_title_width // 2)
                        title_y = int(124 * scale)

                        draw.text((title_x, title_y), part1, fill=(0, 0, 0), font=font_title)
                        draw.text((title_x + w1, title_y), part2, fill=(220, 140, 0), font=font_title)
                        draw.text((title_x + w1 + w2, title_y), part3, fill=(0, 0, 0), font=font_title)

                        topic_x = pill_left + ((pill_width - topic_width) // 2)
                        topic_y = pill_top + ((pill_height - topic_height) // 2) - int(8 * scale)
                        draw.text((topic_x, topic_y), topic_title, fill=(255, 255, 255), font=font_pill)

                        tagline_text = "Think Deeper. Learn Better"
                        bbox = font_tagline.getbbox(tagline_text)
                        tagline_x = (x_offset + (target_size // 2)) - ((bbox[2] - bbox[0]) // 2)
                        draw.text((tagline_x, int(285 * scale)), tagline_text, fill=(0, 0, 0), font=font_tagline)

                    # Draw Footer on pages > 1
                    if current_page_1_indexed > 1:
                        page_str = f"( {current_page_1_indexed} )"
                        mid_text = "     Join YouTube  "
                        suffix_text = f"  {custom_footer_text}"
                        
                        w_page = font_page_num.getbbox(page_str)[2] - font_page_num.getbbox(page_str)[0]
                        w_mid = font_footer.getbbox(mid_text)[2] - font_footer.getbbox(mid_text)[0]
                        w_suffix = font_footer.getbbox(suffix_text)[2] - font_footer.getbbox(suffix_text)[0]
                        
                        yt_icon_size = int(70 * scale)
                        spacing_after_icon = int(14 * scale)
                        total_footer_width = w_page + w_mid + yt_icon_size + spacing_after_icon + w_suffix
                        
                        footer_x = (w_img - total_footer_width) // 2
                        footer_y = h_img - int(120 * scale)
                        
                        line1_y = footer_y - int(16 * scale)
                        line2_y = footer_y - int(10 * scale)
                        draw.line([(int(120 * scale), line1_y), (w_img - int(120 * scale), line1_y)], fill=(160, 160, 160), width=max(1, int(1 * scale)))
                        draw.line([(int(120 * scale), line2_y), (w_img - int(120 * scale), line2_y)], fill=(160, 160, 160), width=max(1, int(1 * scale)))
                        
                        draw.text((footer_x, footer_y + int(6 * scale)), page_str, fill=(60, 60, 60), font=font_page_num)
                        current_x = footer_x + w_page
                        
                        draw.text((current_x, footer_y), mid_text, fill=(50, 50, 50), font=font_footer)
                        current_x += w_mid
                        
                        if yt_img is not None:
                            yt_pil = Image.fromarray(cv2.cvtColor(yt_img, cv2.COLOR_BGRA2RGBA))
                            yt_pil = yt_pil.resize((yt_icon_size, yt_icon_size), Image.Resampling.LANCZOS)
                            pil_img.paste(yt_pil, (current_x, footer_y - int(8 * scale)), yt_pil)
                            current_x += yt_icon_size + spacing_after_icon
                            
                        draw.text((current_x, footer_y), suffix_text, fill=(50, 50, 50), font=font_footer)

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

