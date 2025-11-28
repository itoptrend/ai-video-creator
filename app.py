import streamlit as st
import time
import google.generativeai as genai 
from gtts import gTTS
import os
from PIL import Image
from openai import OpenAI
import requests 
import re
from moviepy.editor import ImageClip, AudioFileClip, VideoFileClip, vfx

# --- 1. CONFIGURATION & CUSTOM CSS (รูปแบบเดิม 100%) ---
st.set_page_config(page_title="All-in-One AI Creator", page_icon="🎬", layout="wide")

st.markdown("""
    <style>
    .stApp { background: linear-gradient(135deg, #1e1e2e 0%, #2d2b42 100%); color: #ffffff; }
    .stButton>button { background: linear-gradient(90deg, #ff8a00 0%, #e52e71 100%); color: white; border: none; border-radius: 12px; padding: 10px 24px; font-weight: bold; transition: 0.3s; }
    .stButton>button:hover { transform: scale(1.05); box-shadow: 0 0 15px rgba(229, 46, 113, 0.7); }
    .stTextInput > div > div > input { background-color: #2b2b3d; color: white; border-radius: 8px; border: 1px solid #454555; }
    .stTextArea > div > div > textarea { background-color: #2b2b3d; color: white; border-radius: 8px; }
    .stSelectbox > div > div > div { background-color: #2b2b3d; color: white; }
    div[data-testid="stTooltipHoverTarget"] > svg { color: #ff8a00; }
    .streamlit-expanderHeader { background-color: #2b2b3d; color: #ff8a00; border-radius: 8px; font-weight: bold; }
    .streamlit-expanderContent { background-color: #232333; border-radius: 0 0 8px 8px; }
    div[data-testid="stFileUploader"] section { background-color: #2b2b3d; border: 1px dashed #454555; }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { background-color: #2b2b3d; border-radius: 4px 4px 0 0; color: white; }
    .stTabs [aria-selected="true"] { background-color: #ff8a00; color: white; }
    div[role="radiogroup"] > label > div:first-child { background-color: #2b2b3d; border-color: #ff8a00; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. INITIALIZE SESSION STATE ---
if 'step' not in st.session_state: st.session_state.step = 0 
if 'script_options' not in st.session_state: st.session_state.script_options = []
if 'generated_script' not in st.session_state: st.session_state.generated_script = ""
if 'generated_prompt_th' not in st.session_state: st.session_state.generated_prompt_th = ""
if 'generated_image_url' not in st.session_state: st.session_state.generated_image_url = ""
if 'generated_video_url' not in st.session_state: st.session_state.generated_video_url = ""
if 'generated_audio_file' not in st.session_state: st.session_state.generated_audio_file = None
if 'final_video_path' not in st.session_state: st.session_state.final_video_path = None
if 'use_manual_video' not in st.session_state: st.session_state.use_manual_video = False

# --- 3. SIDEBAR ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/4712/4712009.png", width=80)
    st.title("⚙️ AI Configuration")
    st.markdown("---")
    
    keys = {}
    keys['gemini'] = st.text_input("Gemini API Key", type="password", help="🔑 Google Gemini")
    
    with st.expander("➕ เชื่อมต่อ API อื่นๆ (Multi-Model Support)"):
        keys['openai'] = st.text_input("OpenAI API Key", type="password", help="🔑 OpenAI")
        keys['grok'] = st.text_input("Grok API Key", type="password", help="🔑 xAI Grok")
        keys['kling'] = st.text_input("KlingAI API Key", type="password", help="🔑 Kling AI")

    st.markdown("---")
    st.markdown("### 🧠 Model Selection")
    
    model_chat = st.text_input("1. Text Model", value="gemini-1.5-pro-latest", help="โมเดลเขียนบท")
    model_tts = st.text_input("2. TTS Model", value="Google TTS (gTTS)", help="โมเดลเสียงพากย์")
    model_image = st.text_input("3. Image Gen Model", value="dall-e-3", help="โมเดลสร้างภาพ") 
    model_video = st.text_input("4. Video AI Model", value="veo-3.0-generate-001", help="โมเดลสร้างวิดีโอ AI")
    model_editing = st.text_input("5. Video Editing", value="Python MoviePy", help="Engine ตัดต่อ")

    st.markdown("---")
    
    with st.expander("🎨 รายละเอียดสำหรับการเขียนคำสั่ง Prompt (Prompt Settings)", expanded=True):
        st.caption("กำหนดรายละเอียดเพิ่มเติมสำหรับสร้างภาพ")
        
        st.markdown("**1. รูปแบบภาพ/คลิป**")
        col_style1, col_style2 = st.columns(2)
        with col_style1: opt_style = st.selectbox("สไตล์", ["สมจริง (Realistic)", "เหนือจินตนาการ (Surreal)"])
        with col_style2: opt_aspect = st.selectbox("อัตราส่วน", ["สี่เหลี่ยมจัตุรัส (1:1)", "แนวนอน (16:9)", "แนวตั้ง (9:16)"])
        opt_resolution = st.selectbox("ความคมชัด", ["Standard HD", "Full HD (1080p)", "4K Ultra HD Details"])
        
        st.markdown("**2. ลักษณะตัวละคร**")
        col_char1, col_char2 = st.columns(2)
        with col_char1:
            opt_gender = st.selectbox("เพศ", ["ไม่จำกัดเพศ", "เพศชาย", "เพศหญิง"])
            opt_skin = st.selectbox("สีผิว", ["ไม่ระบุ", "ผิวสีขาว", "ผิวสีขาวอมชมพู", "ผิวสีแทน", "ผิวสีคล้ำ"]) 
            opt_hair = st.selectbox("ทรงผม", ["ผมสั้น", "ผมยาว", "ไม่ระบุ"])
        with col_char2:
            opt_top = st.selectbox("เสื้อ", ["แขนสั้น", "แขนยาว", "ไม่ระบุ"])
            opt_bottom = st.selectbox("กางเกง/กระโปรง", ["กางเกงขาสั้น", "กางเกงขายาว", "กระโปรงสั้น", "กระโปรงยาว", "ไม่ระบุ"])
            opt_count = st.selectbox("จำนวนตัวละคร", ["1 คน", "2 คน", "มากกว่า 2 คน"])
            
        st.markdown("**3. การกระทำและอารมณ์**")
        opt_action = st.selectbox("การกระทำ", ["นั่ง", "ยืน", "นอน", "ไม่ระบุ"])
        opt_emotion = st.selectbox("อารมณ์", ["ยิ้มร่าเริง", "เศร้าหมอง", "เครียดปวดหัว", "ตื่นเต้น", "ตกใจ", "ปกติ"])
        
        st.markdown("**4. สถานที่**")
        opt_location = st.selectbox("เลือกสถานที่", ["ทุ่งนา", "ป่าเขาลำเนาไพร", "ทะเล", "น้ำตก", "ห้องนอน", "ห้องนั่งเล่น", "ห้องอาหารโรงแรม", "ร้านอาหาร", "ออฟฟิต", "ไม่ระบุ"], label_visibility="collapsed")
        
        st.markdown("**5. เสียงพากย์**")
        opt_voice_gender = st.selectbox("เพศของเสียง", ["เสียงผู้หญิง", "เสียงผู้ชาย"])

# --- HELPER FUNCTIONS ---
def get_thai_error_message(missing_key, model_name):
    if "openai" in missing_key.lower(): return f"❌ **ไม่พบ OpenAI Key** (สำหรับ {model_name})\nเหตุผล: โมเดลนี้ต้องใช้ Key ของ OpenAI\nคำแนะนำ: กรุณาใส่ Key ด้านซ้าย"
    if "gemini" in missing_key.lower(): return f"❌ **ไม่พบ Gemini Key** (สำหรับ {model_name})\nเหตุผล: โมเดลนี้ต้องใช้ Key ของ Google\nคำแนะนำ: กรุณาใส่ Key ด้านซ้าย"
    if "kling" in missing_key.lower(): return f"❌ **ไม่พบ KlingAI Key**"
    return f"❌ Missing {missing_key}"

def validate_model_key(model_name):
    m = model_name.lower()
    if "dall-e" in m or "gpt" in m or "tts-1" in m or "sora" in m:
        if not keys.get('openai'): return False, "OpenAI API Key"
    elif "gemini" in m or "veo" in m or "imagen" in m:
        if not keys.get('gemini'): return False, "Gemini API Key"
    elif "kling" in m:
        if not keys.get('kling'): return False, "KlingAI API Key"
    return True, None

# --- UNIVERSAL ROUTER ---
def generate_text_universal(model_name, prompt, image_inputs=None):
    m = model_name.lower()
    is_valid, missing_key = validate_model_key(model_name)
    if not is_valid: return get_thai_error_message(missing_key, model_name)

    if "gemini" in m:
        try:
            genai.configure(api_key=keys['gemini'])
            model = genai.GenerativeModel(model_name)
            content = [prompt]
            if image_inputs: content.extend(image_inputs); content.append("Context images.")
            response = model.generate_content(content)
            return response.text
        except Exception as e: return f"❌ Gemini Error: {e}"
    elif "gpt" in m:
        try:
            client = OpenAI(api_key=keys['openai'])
            res = client.chat.completions.create(model=model_name, messages=[{"role": "user", "content": prompt}])
            return res.choices[0].message.content
        except Exception as e: return f"❌ OpenAI Error: {e}"
    elif "kling" in m: return "⚠️ Kling AI ไม่รองรับ Text Gen"
    else: return f"❌ Unknown model: {model_name}"

def generate_image_universal(model_name, prompt, size_arg="1024x1024"):
    m = model_name.lower()
    is_valid, missing_key = validate_model_key(model_name)
    if not is_valid: return None, get_thai_error_message(missing_key, model_name)

    if "dall-e" in m:
        try:
            client = OpenAI(api_key=keys['openai'])
            res = client.images.generate(model=model_name, prompt=prompt, size=size_arg, n=1)
            return res.data[0].url, None
        except Exception as e: return None, f"❌ DALL-E Error: {e}"
    elif "kling" in m:
        time.sleep(1); return f"https://placehold.co/{size_arg.replace('x','/')}?text=Kling+Sim", None
    elif "imagen" in m or "gemini" in m:
        return f"https://placehold.co/{size_arg.replace('x','/')}?text=Gemini+Sim", None
    else: return f"https://placehold.co/{size_arg.replace('x','/')}?text={model_name}", None

def generate_video_ai_universal(model_name, image_path):
    m = model_name.lower()
    is_valid, missing_key = validate_model_key(model_name)
    if not is_valid: return None, get_thai_error_message(missing_key, model_name)
    if "veo" in m or "sora" in m: return None, f"⚠️ {model_name} ยังไม่เปิด Public API"
    elif "kling" in m and keys.get('kling'): return None, "⏳ Kling API ต้องรอ Async Task"
    else: return None, "❌ ไม่พบ Video AI Key"

def generate_audio_universal(model_name, text, gender_selection):
    m = model_name.lower()
    output_file = "generated_audio.mp3"
    if "openai" in m or "tts-1" in m:
        is_valid, missing_key = validate_model_key(model_name)
        if not is_valid: return None, get_thai_error_message(missing_key, model_name)

    if ("tts-1" in m or "openai" in m) and keys['openai']:
        try:
            client = OpenAI(api_key=keys['openai'])
            voice_id = "nova"
            if "ผู้ชาย" in gender_selection: voice_id = "onyx"
            response = client.audio.speech.create(model=model_name, voice=voice_id, input=text)
            response.stream_to_file(output_file)
            return output_file, None
        except Exception as e: return None, f"OpenAI TTS Error: {e}"
    else:
        try:
            tts = gTTS(text=text, lang='th')
            tts.save(output_file)
            return output_file, None
        except Exception as e: return None, f"Google TTS Error: {e}"

# --- 4. MAIN INTERFACE ---
st.title("🎬 All-in-One AI Content Generator")
col1, col2 = st.columns([1, 2])

# --- COLUMN 1: INPUTS ---
with col1:
    st.subheader("1. เลือกหัวข้อ & ข้อมูล")
    topic_options = ["1. โฆษณาสินค้า", "2. เรื่องเล่าพระเครื่อง", "3. ข่าวตามกระแส", "4. คำคมประจำวัน", "5. เมนูอาหารอร่อย", "6. สัตว์ทำอาหาร", "7. การผ่าวัตถุ", "8. อธิบายการเทรด Forex XAUUSD"]
    selected_topic = st.selectbox("เลือกธีมคอนเทนต์:", topic_options)
    
    uploaded_files = st.file_uploader("อัปโหลดภาพตัวอย่าง", type=['png', 'jpg', 'jpeg'], accept_multiple_files=True)
    image_objs = []
    if uploaded_files:
        st.caption(f"📂 อัปโหลดแล้ว {len(uploaded_files)} ไฟล์")
        cols = st.columns(3)
        for i, file in enumerate(uploaded_files):
            if i < 3: cols[i].image(file, use_container_width=True)
            image_objs.append(Image.open(file))

    st.markdown("""
    <div style="background-color: #2b2b3d; padding: 10px; border-radius: 8px; margin-bottom: 10px; font-size: 0.9em; color: #e0e0e0; border: 1px solid #454555;">
        <strong>💡 คำแนะนำสำหรับการเขียน Prompt:</strong><br>
        • <b>บรรยากาศ/อารมณ์:</b> (เช่น ตื่นเต้น, ผ่อนคลาย, ลึกลับ)<br>
        • <b>แสงและสี:</b> (เช่น แสงธรรมชาติ, นีออน, โทนอบอุ่น)<br>
        • <b>จุดเด่น:</b> (เช่น เน้นที่ตัวสินค้า, โคลสอัพใบหน้า, มุมมองโดรน)
    </div>
    """, unsafe_allow_html=True)

    user_description = st.text_area("คำอธิบายเพิ่มเติม", height=100)
    duration = st.select_slider("ความยาววิดีโอ (วินาที)", options=[5, 8, 10, 15], value=10)
    
    if st.button("✨ เริ่มเขียนบท (Start Script Generation)", use_container_width=True):
        if not any(keys.values()):
            st.warning("⚠️ กรุณาใส่ API Key อย่างน้อย 1 ค่าย")
        else:
            with st.spinner(f"🤖 กำลังสร้าง Prompt และตัวเลือกสคริปต์ด้วย {model_chat}..."):
                
                # [FIXED] รวบรวมตัวแปรจาก Sidebar ส่งไปให้ AI ตั้งแต่ Step 1
                sidebar_specs = f"""
                - สไตล์ภาพ: {opt_style}
                - เพศตัวละคร: {opt_gender}
                - สีผิว: {opt_skin}
                - ทรงผม: {opt_hair}
                - เสื้อผ้า: {opt_top} (ท่อนบน) / {opt_bottom} (ท่อนล่าง)
                - การกระทำ: {opt_action}
                - อารมณ์: {opt_emotion}
                - สถานที่: {opt_location}
                """

                prompt = f"""
                บทบาท: Creative Director. 
                
                ข้อมูลจำเพาะจากผู้ใช้ (บังคับใช้ในการบรรยายฉาก):
                หัวข้อ: '{selected_topic}'
                คำอธิบายเพิ่มเติม: '{user_description}'
                รายละเอียดตัวละครและฉาก:
                {sidebar_specs}
                
                งานที่ 1: เขียน "Prompt สำหรับสร้างภาพ" เป็นภาษาไทย ที่บรรยายฉากและตัวละครให้ตรงตาม "รายละเอียดตัวละครและฉาก" ด้านบนอย่างเคร่งครัด ให้ขึ้นต้นด้วย "IMAGE_PROMPT_TH:"
                งานที่ 2: เขียนบทพูดสั้นๆ (Voiceover only) ภาษาไทย 3 รูปแบบ (3 Options) ความยาวประมาณ {duration} วินาที ให้ขึ้นต้นด้วย "SCRIPTS:" แล้วคั่นระหว่างแต่ละแบบด้วย "|||"
                
                ***สำคัญ:*** ใส่เครื่องหมายคำพูด "..." ครอบเฉพาะส่วนที่เป็นบทพูดพากย์เสียงในสคริปต์
                """
                script_result = generate_text_universal(model_chat, prompt, image_objs if image_objs else None)
                
                if "Error" in script_result or "❌" in script_result:
                    st.error(script_result)
                else:
                    img_prompt_th = ""
                    scripts_part = script_result
                    
                    if "IMAGE_PROMPT_TH:" in script_result and "SCRIPTS:" in script_result:
                        parts = script_result.split("SCRIPTS:")
                        img_prompt_th = parts[0].replace("IMAGE_PROMPT_TH:", "").strip()
                        scripts_part = parts[1]
                    
                    options = scripts_part.split("|||")
                    options = [opt.strip() for opt in options if opt.strip()]
                    if len(options) == 0: options = [scripts_part]
                    
                    st.session_state.generated_prompt_th = img_prompt_th
                    st.session_state.script_options = options
                    st.session_state.step = 1
                    st.rerun()

# --- COLUMN 2: RESULTS (UI เดิม) ---
with col2:
    st.subheader("2. ผลลัพธ์ (Real-time)")
    step_container = st.container()

    # --- STEP 1: Script Selection ---
    with step_container:
        with st.expander(f"✅ Step 1: เลือกบทสคริปต์ (Model: {model_chat})", expanded=(st.session_state.step >= 1)):
            if st.session_state.step >= 1 and st.session_state.script_options:
                
                if st.session_state.generated_prompt_th:
                    st.markdown("##### 🖼️ ภาพรวม/Prompt สำหรับสร้างภาพ (ภาษาไทย)")
                    st.info(st.session_state.generated_prompt_th)
                
                st.divider()
                st.info(f"🎉 AI สร้างสคริปต์มาให้เลือก {len(st.session_state.script_options)} แบบ:")
                tabs = st.tabs([f"ตัวเลือกที่ {i+1}" for i in range(len(st.session_state.script_options))])
                
                for i, tab in enumerate(tabs):
                    with tab:
                        st.text_area(f"เนื้อหาแบบที่ {i+1}", value=st.session_state.script_options[i], height=200, key=f"script_opt_{i}")
                        if st.button(f"✅ เลือกสคริปต์แบบที่ {i+1} และดำเนินการต่อ", key=f"btn_sel_{i}"):
                            st.session_state.generated_script = st.session_state.script_options[i]
                            st.session_state.step = 2 
                            st.rerun()
            
            elif st.session_state.step == 0:
                st.markdown("<div style='text-align: center; color: gray; padding: 20px;'>รอการกดปุ่ม 'เริ่มเขียนบท' ...</div>", unsafe_allow_html=True)
            
            if st.session_state.step >= 2:
                st.success("คุณได้เลือกสคริปต์แล้ว")
                new_script = st.text_area("บทสคริปต์ที่เลือก (Final Edit):", value=st.session_state.generated_script, height=150)
                if new_script != st.session_state.generated_script:
                    st.session_state.generated_script = new_script

                quotes_found = re.findall(r'"(.*?)"', new_script, re.DOTALL)
                radio_options = ["พากย์ทั้งหมด (All Text)"]
                if quotes_found:
                    for idx, q in enumerate(quotes_found): radio_options.append(f'ท่อนที่ {idx+1}: "{q}"')
                
                selected_voice_opt = st.radio("เลือกส่วนที่ต้องการพากย์:", radio_options)
                
                if st.button("🚀 ยืนยันสคริปต์ และ สร้างองค์ประกอบที่เหลือ (Audio/Image/Video)"):
                    with st.spinner("🎙️ กำลังสร้างเสียงพากย์..."):
                        final_text = new_script.replace('*', '')
                        if "พากย์ทั้งหมด" not in selected_voice_opt:
                            final_text = selected_voice_opt.split('"', 1)[1].rsplit('"', 1)[0]
                        
                        audio_path, err = generate_audio_universal(model_tts, final_text, opt_voice_gender)
                        if audio_path: st.session_state.generated_audio_file = audio_path
                        else: st.warning(f"Audio Error: {err}")

                    with st.spinner(f"🎨 กำลังสร้างภาพด้วย {model_image}..."):
                        dalle_size_param = "1024x1024"
                        if "16:9" in opt_aspect: dalle_size_param = "1792x1024"
                        elif "9:16" in opt_aspect: dalle_size_param = "1024x1792"

                        # Use the detailed Thai prompt generated in Step 1
                        base_prompt = st.session_state.generated_prompt_th if st.session_state.generated_prompt_th else new_script[:100]
                        full_img_prompt = f"Write a {model_image} image prompt based on description: '{base_prompt}'. Style: {opt_style}, Quality: {opt_resolution}. Photorealistic."
                        
                        img_prompt_res = generate_text_universal(model_chat, full_img_prompt)
                        img_url, err = generate_image_universal(model_image, img_prompt_res, dalle_size_param)
                        
                        if img_url:
                            st.session_state.generated_image_url = img_url
                            if img_url.startswith("http"):
                                try:
                                    img_data = requests.get(img_url).content
                                    with open("temp_image.png", 'wb') as h: h.write(img_data)
                                except: pass
                        else:
                            st.error(f"Image Gen Failed: {err}")

                    with st.spinner(f"🎞️ กำลังสร้าง Motion Video..."):
                        if os.path.exists("temp_image.png"):
                            vid_url, vid_err = generate_video_ai_universal(model_video, "temp_image.png")
                            if vid_url: st.session_state.generated_video_url = vid_url
                            else: 
                                st.warning(f"ไม่สามารถสร้าง Motion Video: {vid_err} (ใช้ภาพนิ่งแทน)")
                                st.session_state.generated_video_url = None
                    
                    st.session_state.process_complete = True 
                    st.success("✅ สร้างองค์ประกอบครบแล้ว!")
                    st.rerun()

    # --- STEP 2-5 ---
    if st.session_state.step >= 2:
        
        # Step 2
        with step_container:
            with st.expander(f"✅ Step 2: เสียงพากย์ (Model: {model_tts})", expanded=False):
                if st.session_state.generated_audio_file: st.audio(st.session_state.generated_audio_file)
                else: st.info("รอการสร้างเสียง...")

        # Step 3
        with step_container:
            with st.expander(f"✅ Step 3: ภาพประกอบ (Model: {model_image})", expanded=False):
                st.markdown("**1. อัปโหลดภาพเอง (ถ้าไม่ใช้ AI)**")
                manual_upload = st.file_uploader("เลือกไฟล์ภาพ (JPG, PNG)", type=['png', 'jpg', 'jpeg'], key="img_up")
                if manual_upload:
                    image = Image.open(manual_upload)
                    image.save("temp_image.png")
                    st.session_state.generated_image_url = "uploaded"
                    st.image(image, caption="Uploaded Image")
                    st.success("ใช้ภาพที่อัปโหลดแล้ว")

                st.markdown("---")
                st.markdown("**2. หรือ สร้างใหม่ด้วย AI**")
                if st.session_state.generated_image_url and not manual_upload:
                    st.image(st.session_state.generated_image_url, caption="AI Generated Image")
                
                regen_model = st.text_input("เปลี่ยน Model ภาพ:", value=model_image, key="regen_img_key")
                if st.button("🔄 สร้างภาพใหม่"):
                    is_valid, missing = validate_model_key(regen_model)
                    if not is_valid: st.error(get_thai_error_message(missing, regen_model))
                    else:
                        with st.spinner(f"กำลังสร้างภาพใหม่ด้วย {regen_model}..."):
                            dalle_size = "1024x1024"
                            if "16:9" in opt_aspect: dalle_size = "1792x1024"
                            elif "9:16" in opt_aspect: dalle_size = "1024x1792"
                            
                            base_p = st.session_state.generated_prompt_th if st.session_state.generated_prompt_th else selected_topic
                            img_res = generate_image_universal(regen_model, f"Scene: {base_p}, {opt_style}", dalle_size)
                            
                            if img_res[0]:
                                st.session_state.generated_image_url = img_res[0]
                                if img_res[0].startswith("http"):
                                    try:
                                        r = requests.get(img_res[0])
                                        with open("temp_image.png", 'wb') as f: f.write(r.content)
                                    except: pass
                                st.success("สำเร็จ!")
                                time.sleep(0.5)
                                st.rerun()
                            else: st.error(f"❌ ไม่สำเร็จ: {img_res[1]}")

        # Step 4
        with step_container:
            with st.expander(f"✅ Step 4: สร้างคลิปวีดีโอเคลื่อนไหว (Model: {model_video})", expanded=False):
                st.markdown("**1. อัปโหลดวิดีโอเอง (ถ้ามี)**")
                manual_vid = st.file_uploader("เลือกไฟล์วิดีโอ (MP4, MOV)", type=['mp4', 'mov'], key="vid_up")
                if manual_vid:
                    with open("temp_video.mp4", "wb") as f: f.write(manual_vid.read())
                    st.session_state.use_manual_video = True
                    st.video("temp_video.mp4")
                    st.success("ใช้วิดีโอที่อัปโหลดแล้ว")

                st.markdown("---")
                st.markdown("**2. หรือ สร้าง Motion Video ด้วย AI**")
                if st.session_state.generated_video_url and not manual_vid: 
                    st.success("มีไฟล์วิดีโอ AI แล้ว")
                else: st.info("ใช้ภาพนิ่งแทน (หากไม่มีวิดีโอ)")
                
                regen_video_model = st.text_input("เปลี่ยน Model วิดีโอ:", value=model_video, key="regen_vid_key")
                
                if st.button("🎞️ สร้าง Motion Video อีกครั้ง"):
                    is_valid, missing = validate_model_key(regen_video_model)
                    if not is_valid: st.error(get_thai_error_message(missing, regen_video_model))
                    else:
                        with st.spinner(f"กำลังสร้างวิดีโอด้วย {regen_video_model}..."):
                            vid_url, vid_err = generate_video_ai_universal(regen_video_model, "temp_image.png")
                            if vid_url:
                                st.session_state.generated_video_url = vid_url
                                st.session_state.use_manual_video = False
                                st.success("สำเร็จ!")
                            else: st.warning(f"ไม่สำเร็จ: {vid_err}")

        st.divider()
        
        # Step 5
        st.markdown(f"### 🎬 Final Video Generation")
        col_btn1, col_btn2 = st.columns([1.5, 1])
        with col_btn1:
            if st.button("🎥 สร้างวิดีโอ (Render Real Video)", type="primary", use_container_width=True):
                if os.path.exists("temp_image.png") and os.path.exists("generated_audio.mp3"):
                    with st.spinner("Rendering..."):
                        try:
                            audio_clip = AudioFileClip("generated_audio.mp3")
                            has_video = False
                            if st.session_state.use_manual_video and os.path.exists("temp_video.mp4"):
                                has_video = True
                            
                            if has_video:
                                visual_clip = VideoFileClip("temp_video.mp4")
                                if visual_clip.duration < audio_clip.duration:
                                    visual_clip = vfx.loop(visual_clip, duration=audio_clip.duration)
                                else:
                                    visual_clip = visual_clip.subclip(0, audio_clip.duration)
                            else:
                                visual_clip = ImageClip("temp_image.png").set_duration(audio_clip.duration)
                            
                            if "9:16" in opt_aspect: visual_clip = visual_clip.resize(height=1920)
                            
                            final_clip = visual_clip.set_audio(audio_clip)
                            final_clip.write_videofile("final_output.mp4", fps=24, codec="libx264", audio_codec="aac")
                            st.session_state.final_video_path = "final_output.mp4"
                            st.success("Done!")
                        except Exception as e: st.error(f"Render Error: {e}")
                else: st.error("Missing Assets")
        
        if st.session_state.final_video_path:
            st.video(st.session_state.final_video_path)
            with open(st.session_state.final_video_path, "rb") as f:
                st.download_button("⬇️ Download MP4", f, "video.mp4")

        with col_btn2:
            if st.button("🔄 เริ่มใหม่ทั้งหมด", use_container_width=True):
                st.session_state.clear()
                st.rerun()