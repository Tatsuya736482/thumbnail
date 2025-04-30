#"streamlit run thumbnail_generator_v2.py"これで試せる。

import streamlit as st
from PIL import Image, ImageDraw, ImageFont
from streamlit_cropper import st_cropper
from io import BytesIO
import os
import requests

# フォント準備
FONT_PATH = "NotoSansCJKjp-Regular.otf"
FONT_URL = "https://github.com/googlefonts/noto-cjk/raw/main/Sans/OTF/Japanese/NotoSansCJKjp-Regular.otf"
if not os.path.exists(FONT_PATH):
    try:
        r = requests.get(FONT_URL)
        with open(FONT_PATH, "wb") as f:
            f.write(r.content)
    except:
        st.warning("フォントのダウンロードに失敗しました。")

# Streamlit設定
st.set_page_config(layout="centered")
st.title("留学サムネイル画像生成")

# 入力項目
portrait_file = st.file_uploader("人物画像（縦：横 = 3:2）", type=["jpg", "jpeg", "png"])
landscape_file = st.file_uploader("背景画像（縦：横 = 3:4）", type=["jpg", "jpeg", "png"])
name = st.text_input("名前")
location = st.text_input("留学先（国・都市）")
university = st.text_input("留学先大学")
period = st.text_input("留学期間")
affiliation = st.text_input("所属（出発時）")

# トリミング
cropped_portrait = None
cropped_landscape = None

if portrait_file:
    st.subheader("人物画像トリミング（縦：横 = 3:2）")
    portrait = Image.open(portrait_file)
    cropped_portrait = st_cropper(
        portrait,
        aspect_ratio=(2, 3),
        realtime_update=True
    )

if landscape_file:
    st.subheader("背景画像トリミング（縦：横 = 3:4）")
    landscape = Image.open(landscape_file)
    cropped_landscape = st_cropper(
        landscape,
        aspect_ratio=(4, 3),
        realtime_update=True
    )

if (
    cropped_portrait is not None
    and cropped_landscape is not None
    and all([name, location, university, period, affiliation])
):
    if st.button("画像を生成"):

        # RGBA変換
        p_img = cropped_portrait.convert("RGBA")
        l_img = cropped_landscape.convert("RGBA")

        # 背景画像の高さに合わせて人物画像を拡大
        target_height = l_img.height
        new_pw = int(p_img.width * target_height / p_img.height)
        p_img = p_img.resize((new_pw, target_height), Image.LANCZOS)

        # 背景画像の横幅を人物画像の2倍にリサイズ
        new_lw = p_img.width * 2
        l_img = l_img.resize((new_lw, target_height), Image.LANCZOS)

        # キャンバス作成と貼り付け
        canvas = Image.new("RGBA", (p_img.width + l_img.width, target_height), (255, 255, 255, 255))
        canvas.paste(p_img, (0, 0), mask=p_img)
        canvas.paste(l_img, (p_img.width, 0), mask=l_img)

        # 台形描画（背景側）
        right = canvas.width
        bg_width = l_img.width
        top_margin = int(target_height * 0.15)
        trapezoid_height = target_height - top_margin
        top_base = int(bg_width * 0.75)
        bottom_base = int(bg_width * 0.95)
        left_top = right - top_base
        left_bottom = right - bottom_base
        trapezoid_coords = [
            (left_top, top_margin),
            (right, top_margin),
            (right, target_height),
            (left_bottom, target_height),
        ]

        overlay = Image.new("RGBA", canvas.size, (255, 255, 255, 0))
        draw_overlay = ImageDraw.Draw(overlay)
        draw_overlay.polygon(trapezoid_coords, fill=(255, 255, 255, 180))
        canvas = Image.alpha_composite(canvas, overlay)

        # テキスト準備
        sections = [
            ("国/都市", location),
            ("留学先", university),
            ("期間", period),
            ("留学開始時所属", affiliation)
        ]
        section_count = len(sections)
        base_lines = 1 + section_count * 2
        line_spacing_ratio = 0.4
        section_gap = 10
        total_spacing_lines = base_lines + (base_lines - 1) * line_spacing_ratio + section_count
        base_font_size = int(trapezoid_height / (total_spacing_lines + 2))  # 上下1行分余白
        name_font_size = int(base_font_size * 1.5)

        try:
            font_base = ImageFont.truetype(FONT_PATH, base_font_size)
            font_name = ImageFont.truetype(FONT_PATH, name_font_size)
        except:
            font_base = ImageFont.load_default()
            font_name = ImageFont.load_default()

        draw = ImageDraw.Draw(canvas)
        text_x = left_top + 40
        y = top_margin + base_font_size  # 上に1行分余白

        draw.text((text_x, y), name, fill=(0, 0, 0, 255), font=font_name)
        y += int(name_font_size * (1 + line_spacing_ratio))

        for title, value in sections:
            draw.text((text_x, y), title, fill=(0, 0, 0, 255), font=font_base)
            y += int(base_font_size * (1 + line_spacing_ratio))
            draw.text((text_x, y), "\u3000" + value, fill=(0, 0, 0, 255), font=font_base)
            y += int(base_font_size * (1 + line_spacing_ratio))
            y += section_gap

        # 出力
        final_img = canvas.convert("RGB")
        output = BytesIO()
        final_img.save(output, format="JPEG")
        output.seek(0)

        st.image(final_img, caption="完成画像", use_container_width=True)
        st.download_button("画像をダウンロード", data=output, file_name="thumbnail.jpg", mime="image/jpeg")
