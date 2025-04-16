"""
COCO-Segmentation to Custom Format 변환기의 유틸리티 패키지입니다.
이 패키지는 변환 과정에 필요한 다양한 유틸리티 함수들을 제공합니다.

Author: injokim <injo1121@rtm.ai>
"""

from .image_utils import polygon_to_mask, resize_keep_aspect
from .encoding_utils import encode_rle, calculate_crc
from .file_utils import compress_output
from .metadata_utils import create_collection_metadata
from .converter import convert_coco_to_custom

__all__ = [
    'polygon_to_mask',
    'resize_keep_aspect',
    'encode_rle',
    'calculate_crc',
    'compress_output',
    'create_collection_metadata',
    'convert_coco_to_custom'
] 