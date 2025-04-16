"""
인코딩 관련 유틸리티 함수들을 제공하는 모듈입니다.
주요 기능:
- Binary mask를 RLE 인코딩
- 파일의 CRC32 값 계산

Author: injokim <injo1121@rtm.ai>
"""

import numpy as np
from typing import List
import zlib

def encode_rle(mask: np.ndarray) -> List[int]:
    """Binary mask를 RLE 인코딩합니다."""
    pixels = mask.flatten()
    rle = []
    current_val = int(pixels[0])  # uint8을 int로 변환
    count = 1
    
    for val in pixels[1:]:
        val = int(val)  # uint8을 int로 변환
        if val == current_val:
            count += 1
        else:
            rle.extend([current_val, count])
            current_val = val
            count = 1
    
    rle.extend([current_val, count])
    return rle

def calculate_crc(file_path: str) -> int:
    """파일의 CRC 값을 계산합니다."""
    with open(file_path, 'rb') as f:
        return zlib.crc32(f.read()) 