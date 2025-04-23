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
    
    # RLE 포맷인 경우 처리
    if isinstance(polygons, dict) and 'counts' in polygons:
        try:
            from pycocotools import mask as mask_utils
            rle = mask_utils.frPyObjects(polygons, height, width)
            mask = mask_utils.decode(rle)
            return mask
        except ImportError:
            raise ImportError("RLE 포맷을 처리하기 위해서는 pycocotools가 필요합니다. pip install pycocotools로 설치해주세요.")
    
    # 일반 polygon 처리
    img = Image.new('L', (width, height), 0)
    draw = ImageDraw.Draw(img)
    
    for polygon in polygons:
        # 좌표 타입 검증 및 변환
        try:
            # 좌표가 문자열인 경우 처리
            if isinstance(polygon, str):
                # 문자열을 리스트로 변환
                polygon = [float(x) for x in polygon.split(',')]
            
            # 좌표가 리스트인지 확인
            if not isinstance(polygon, list):
                raise TypeError(f"좌표가 리스트 타입이 아닙니다: {type(polygon)}")
            
            # 좌표를 float에서 int로 변환
            points = [(int(float(polygon[i])), int(float(polygon[i+1]))) for i in range(0, len(polygon), 2)]
            
            # 좌표가 이미지 크기를 벗어나지 않도록 제한
            points = [(max(0, min(x, width-1)), max(0, min(y, height-1))) for x, y in points]
            
            draw.polygon(points, fill=1)
        except (IndexError, ValueError, TypeError) as e:
            raise ValueError(f"잘못된 좌표 형식입니다: {e}")
    
    mask = np.array(img)
    return mask

def resize_keep_aspect(image: Image.Image, max_size: int) -> Image.Image:
    """이미지의 비율을 유지하면서 리사이즈합니다."""
    ratio = min(max_size / image.width, max_size / image.height)
    new_size = (int(image.width * ratio), int(image.height * ratio))
    return image.resize(new_size, Image.Resampling.LANCZOS) 