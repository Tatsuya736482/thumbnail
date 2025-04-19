import streamlit as st
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import os
import requests

st.set_page_config(layout="centered")
st.title("留学サムネイル画像ジェネレーター")

# 入力
portrait = st.file_uploader("縦画像（人物）をアップロード", type=["jpg", "jpeg", "png"])
landscape = st.file_uploader("横画像（背景）をアップロード", type=["jpg", "jpeg", "png"])
name = st.text_input("名前")
location = st.text_input("留学先（国・都市）")
university = st.text_input("留学先大学")
period = st.text_input("留学期間")
affiliation = st.text_input("所属（出発時）")

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

if portrait and landscape and name and location and university and period and affiliation:
    if st.button("画像を生成"):
        # 画像読み込みとサイズ調整
        img1 = Image.open(portrait).convert("RGBA")
        img2 = Image.open(landscape).convert("RGBA")
        target_height = min(img1.height, img2.height)
        img1 = img1.resize((int(img1.width * target_height / img1.height), target_height))
        img2 = img2.resize((int(img2.width * target_height / img2.height), target_height))

        total_width = img1.width + img2.width
        canvas = Image.new("RGBA", (total_width, target_height))
        canvas.paste(img1, (0, 0))
        canvas.paste(img2, (img1.width, 0))

        # 台形サイズ設定
        bg_width = img2.width
        top_base = int(bg_width * 0.75)
        bottom_base = int(bg_width * 0.95)
        trapezoid_height = int(target_height * 0.85)
        top_margin = target_height - trapezoid_height
        right = total_width
        left_top = right - top_base
        left_bottom = right - bottom_base

        # 台形座標
        trapezoid_coords = [
            (left_top, top_margin),
            (right, top_margin),
            (right, target_height),
            (left_bottom, target_height)
        ]

        # 台形描画（白＋透明度180）
        overlay = Image.new("RGBA", canvas.size, (255, 255, 255, 0))
        draw_overlay = ImageDraw.Draw(overlay)
        draw_overlay.polygon(trapezoid_coords, fill=(255, 255, 255, 180))
        canvas = Image.alpha_composite(canvas.copy(), overlay)

        # テキスト構成
        sections = [
            ("国/都市", location),
            ("留学先", university),
            ("期間", period),
            ("留学開始時所属", affiliation)
        ]

        section_count = len(sections)
        base_lines = 1 + section_count * 2  # 名前1 + セクション2行×n
        section_gap = 10
        line_spacing_ratio = 0.4

        # 上下に1行分ずつ空けて → 使用可能高さ
        total_spacing_lines = base_lines + (base_lines - 1) * line_spacing_ratio + section_count  # セクション間10pxは別
        effective_height = trapezoid_height - 2 * 1  # 1行分ずつ（行間比率でカバー）

        # フォントサイズを逆算
        base_font_size = int(trapezoid_height / (total_spacing_lines + 2))  # +2: 上下余白分
        name_font_size = int(base_font_size * 1.5)

        try:
            font_base = ImageFont.truetype(FONT_PATH, base_font_size)
            font_name = ImageFont.truetype(FONT_PATH, name_font_size)
        except:
            font_base = ImageFont.load_default()
            font_name = ImageFont.load_default()

        # 描画開始位置（上余白 = 1行分）
        start_y = top_margin + int(base_font_size)

        # 描画処理
        draw = ImageDraw.Draw(canvas)
        text_x = left_top + 40
        y = start_y

        # 名前
        draw.text((text_x, y), name, fill=(0, 0, 0, 255), font=font_name)
        y += int(name_font_size + name_font_size * line_spacing_ratio)

        # セクション
        for title, value in sections:
            draw.text((text_x, y), title, fill=(0, 0, 0, 255), font=font_base)
            y += int(base_font_size + base_font_size * line_spacing_ratio)
            draw.text((text_x, y), value, fill=(0, 0, 0, 255), font=font_base)
            y += int(base_font_size + base_font_size * line_spacing_ratio)
            y += section_gap

        # 出力
        final_img = canvas.convert("RGB")
        output = BytesIO()
        final_img.save(output, format="JPEG")
        output.seek(0)

        st.image(output, caption="完成画像", use_container_width=True)
        st.download_button("画像をダウンロード", data=output, file_name="poster_output.jpg", mime="image/jpeg")
