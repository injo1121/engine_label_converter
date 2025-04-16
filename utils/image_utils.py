"""
이미지 처리 관련 유틸리티 함수들을 제공하는 모듈입니다.
주요 기능:
- Polygon을 binary mask로 변환
- 이미지 비율 유지하며 리사이즈

Author: injokim <injo1121@rtm.ai>
"""

from PIL import Image, ImageDraw
import numpy as np
from typing import List

def polygon_to_mask(width: int, height: int, polygons: List[List[float]]) -> np.ndarray:
    """Polygon을 binary mask로 변환합니다."""
    mask = np.zeros((height, width), dtype=np.uint8)
    img = Image.new('L', (width, height), 0)
    draw = ImageDraw.Draw(img)
    
    for polygon in polygons:
        # COCO 포맷은 [x1,y1,x2,y2,...] 형식
        points = [(polygon[i], polygon[i+1]) for i in range(0, len(polygon), 2)]
        draw.polygon(points, fill=1)
    
    mask = np.array(img)
    return mask

def resize_keep_aspect(image: Image.Image, max_size: int) -> Image.Image:
    """이미지의 비율을 유지하면서 리사이즈합니다."""
    ratio = min(max_size / image.width, max_size / image.height)
    new_size = (int(image.width * ratio), int(image.height * ratio))
    return image.resize(new_size, Image.Resampling.LANCZOS) 