import os
import sys
import argparse
from PIL import Image, ImageDraw, ImageFont, ExifTags
from datetime import datetime

# 支持的图片格式
SUPPORTED_FORMATS = ['.jpg', '.jpeg', '.png']

# 获取图片的拍摄日期
def get_date_taken(img):
    exif_data = img._getexif()
    if not exif_data:
        return None
    for tag, value in exif_data.items():
        decoded = ExifTags.TAGS.get(tag, tag)
        if decoded == 'DateTimeOriginal':
            try:
                dt = datetime.strptime(value, '%Y:%m:%d %H:%M:%S')
                return dt.strftime('%Y-%m-%d')
            except Exception:
                return None
    return None

# 计算水印位置
def get_position(pos, img_size, text_size, margin=20):
    W, H = img_size
    w, h = text_size
    if pos == 'left-top':
        return (margin, margin)
    elif pos == 'center':
        return ((W - w) // 2, (H - h) // 2)
    elif pos == 'right-bottom':
        return (W - w - margin, H - h - margin)
    else:
        return (margin, margin)

# 主处理函数

# 为单张图片添加水印并保存
def add_watermark(img_path, date_taken, save_path, font_size, font_color, position):
    try:
        img = Image.open(img_path)
        font_path = None
        if sys.platform.startswith('win'):
            font_path = 'C:/Windows/Fonts/arial.ttf'
        else:
            font_path = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
        try:
            font = ImageFont.truetype(font_path, font_size)
        except Exception:
            font = ImageFont.load_default()
        draw = ImageDraw.Draw(img)
        text = date_taken
        text_size = draw.textsize(text, font=font)
        pos_xy = get_position(position, img.size, text_size)
        draw.text(pos_xy, text, font=font, fill=font_color)
        img.save(save_path)
        print(f"已保存水印图片: {save_path}")
    except Exception as e:
        print(f"处理图片 {os.path.basename(img_path)} 时出错: {e}")



def run_watermark(args):
    folder = os.path.abspath(args.folder)
    suffixes = [s.strip().lower() for s in args.suffixes.split(',')]
    watermark_dir = os.path.join(folder, os.path.basename(folder) + '_watermark')
    os.makedirs(watermark_dir, exist_ok=True)

    for fname in os.listdir(folder):
        ext = os.path.splitext(fname)[1].lower()
        if ext not in suffixes:
            continue
        img_path = os.path.join(folder, fname)
        try:
            img = Image.open(img_path)
            date_taken = get_date_taken(img)
            if not date_taken:
                print(f"跳过无拍摄时间的图片: {fname}")
                continue
            save_path = os.path.join(watermark_dir, fname)
            add_watermark(img_path, date_taken, save_path, args.font_size, args.font_color, args.position)
        except Exception as e:
            print(f"处理图片 {fname} 时出错: {e}")

def main():
    parser = argparse.ArgumentParser(description='批量为图片添加拍摄日期水印')
    parser.add_argument('folder', help='图片文件夹路径')
    parser.add_argument('--font-size', type=int, default=32, help='字体大小，默认32')
    parser.add_argument('--font-color', type=str, default='#FFFFFF', help='字体颜色，默认白色')
    parser.add_argument('--position', type=str, choices=['left-top', 'center', 'right-bottom'], default='right-bottom', help='水印位置')
    parser.add_argument('--suffixes', type=str, default='.jpg,.jpeg,.png', help='图片后缀，逗号分隔，默认支持jpg,jpeg,png')
    args = parser.parse_args()

    run_watermark(args)

if __name__ == '__main__':
    main()
