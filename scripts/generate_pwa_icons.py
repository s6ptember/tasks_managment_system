#!/usr/bin/env python3
"""
Filename: generate_pwa_icons.py
Path: scripts/generate_pwa_icons.py
Description: Генерация иконок PWA из одного изображения
Usage: python scripts/generate_pwa_icons.py <input_image>
"""

import os
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter

# Размеры иконок для PWA
ICON_SIZES = [
    72, 96, 128, 144, 152, 192, 384, 512
]

# Размеры maskable иконок (с отступами)
MASKABLE_SIZES = [
    192, 512
]

def create_rounded_icon(img, size, corner_radius_percent=0.2):
    """
    Создать иконку с закругленными углами

    Args:
        img: PIL Image объект
        size: размер итоговой иконки
        corner_radius_percent: процент закругления углов (0.0 - 1.0)
    """
    # Создаем квадратное изображение нужного размера
    icon = img.resize((size, size), Image.Resampling.LANCZOS)

    # Создаем маску с закругленными углами
    mask = Image.new('L', (size, size), 0)
    draw = ImageDraw.Draw(mask)

    corner_radius = int(size * corner_radius_percent)
    draw.rounded_rectangle(
        [(0, 0), (size, size)],
        radius=corner_radius,
        fill=255
    )

    # Применяем маску
    output = Image.new('RGBA', (size, size), (255, 255, 255, 0))
    output.paste(icon, (0, 0))
    output.putalpha(mask)

    return output

def create_maskable_icon(img, size, safe_zone_percent=0.8):
    """
    Создать maskable иконку с безопасной зоной

    Args:
        img: PIL Image объект
        size: размер итоговой иконки
        safe_zone_percent: процент безопасной зоны (0.0 - 1.0)
    """
    # Создаем фон
    background = Image.new('RGBA', (size, size), (139, 92, 246, 255))  # Purple

    # Вычисляем размер безопасной зоны
    safe_size = int(size * safe_zone_percent)
    padding = (size - safe_size) // 2

    # Ресайзим основное изображение
    icon = img.resize((safe_size, safe_size), Image.Resampling.LANCZOS)

    # Накладываем на фон
    background.paste(icon, (padding, padding), icon if icon.mode == 'RGBA' else None)

    return background

def create_favicon(img):
    """Создать favicon.ico с несколькими размерами"""
    sizes = [16, 32, 48]
    icons = []

    for size in sizes:
        icon = img.resize((size, size), Image.Resampling.LANCZOS)
        icons.append(icon)

    return icons

def generate_icons(input_path, output_dir):
    """
    Генерация всех необходимых иконок

    Args:
        input_path: путь к исходному изображению
        output_dir: директория для сохранения иконок
    """
    # Создаем директорию если её нет
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Открываем исходное изображение
    try:
        img = Image.open(input_path)

        # Конвертируем в RGBA если нужно
        if img.mode != 'RGBA':
            img = img.convert('RGBA')

        print(f"✓ Загружено изображение: {input_path}")
        print(f"  Размер: {img.size}")
        print(f"  Режим: {img.mode}")

    except Exception as e:
        print(f"✗ Ошибка при загрузке изображения: {e}")
        return False

    # Генерируем обычные иконки
    print("\nГенерация обычных иконок:")
    for size in ICON_SIZES:
        try:
            icon = create_rounded_icon(img, size)
            output_file = output_path / f"icon-{size}x{size}.png"
            icon.save(output_file, 'PNG', optimize=True)
            print(f"  ✓ {output_file.name}")
        except Exception as e:
            print(f"  ✗ Ошибка при создании {size}x{size}: {e}")

    # Генерируем maskable иконки
    print("\nГенерация maskable иконок:")
    for size in MASKABLE_SIZES:
        try:
            icon = create_maskable_icon(img, size)
            output_file = output_path / f"icon-maskable-{size}x{size}.png"
            icon.save(output_file, 'PNG', optimize=True)
            print(f"  ✓ {output_file.name}")
        except Exception as e:
            print(f"  ✗ Ошибка при создании maskable {size}x{size}: {e}")

    # Генерируем Apple Touch Icon
    print("\nГенерация Apple Touch Icon:")
    try:
        apple_icon = create_rounded_icon(img, 180)
        output_file = output_path / "apple-touch-icon.png"
        apple_icon.save(output_file, 'PNG', optimize=True)
        print(f"  ✓ {output_file.name}")
    except Exception as e:
        print(f"  ✗ Ошибка при создании Apple Touch Icon: {e}")

    # Генерируем favicon.ico
    print("\nГенерация favicon.ico:")
    try:
        favicon_icons = create_favicon(img)
        output_file = output_path.parent / "favicon.ico"
        favicon_icons[0].save(
            output_file,
            format='ICO',
            sizes=[(16, 16), (32, 32), (48, 48)]
        )
        print(f"  ✓ {output_file.name}")
    except Exception as e:
        print(f"  ✗ Ошибка при создании favicon.ico: {e}")

    print(f"\n✓ Генерация завершена! Файлы сохранены в: {output_dir}")
    return True

def main():
    """Главная функция"""
    if len(sys.argv) < 2:
        print("Usage: python generate_pwa_icons.py <input_image>")
        print("\nПример:")
        print("  python scripts/generate_pwa_icons.py logo.png")
        sys.exit(1)

    input_path = sys.argv[1]

    # Проверяем существование файла
    if not os.path.exists(input_path):
        print(f"✗ Файл не найден: {input_path}")
        sys.exit(1)

    # Определяем директорию для иконок
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    output_dir = project_root / "src" / "static" / "icons"

    print("=" * 60)
    print("PWA Icons Generator")
    print("=" * 60)

    success = generate_icons(input_path, output_dir)

    if success:
        print("\n" + "=" * 60)
        print("Следующие шаги:")
        print("=" * 60)
        print("1. Проверьте сгенерированные иконки в:", output_dir)
        print("2. При необходимости создайте скриншоты для PWA:")
        print("   - Десктоп: 1280x720")
        print("   - Мобильный: 750x1334")
        print("3. Запустите collectstatic:")
        print("   python src/manage.py collectstatic")
        print("=" * 60)
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
