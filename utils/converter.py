"""
COCO Segmentation 및 Object Detection 형식을 Custom 형식으로 변환하는 모듈입니다.
주요 기능:
- COCO JSON 데이터 파싱
- 이미지 및 어노테이션 매핑
- Custom 형식의 JSON 파일 생성
- 이미지 리사이징 및 저장

Author: injokim <injo1121@rtm.ai>
"""

import json
import os
from pathlib import Path
from typing import Callable, Optional
import numpy as np
from PIL import Image
import datetime
from tqdm import tqdm

from .image_utils import polygon_to_mask, resize_keep_aspect
from .encoding_utils import encode_rle, calculate_crc
from .metadata_utils import create_collection_metadata

def convert_coco_to_custom(
    coco_json_path: str,
    image_dir: str,
    output_dir: str,
    album_name: str,
    is_object_detection: bool = False,
    progress_callback: Optional[Callable[[int], None]] = None):
    """COCO 포맷을 Custom 포맷으로 변환합니다."""
    # 출력 디렉토리 생성
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)
    
    # COCO JSON 로드
    with open(coco_json_path, 'r') as f:
        coco_data = json.load(f)
    
    # 컬렉션 메타데이터 생성
    create_collection_metadata(output_dir=output_dir, 
                               categories=coco_data['categories'], 
                               album_name=album_name,
                               is_object_detection=is_object_detection
                               )
    
    # 이미지와 어노테이션 매핑
    image_map = {img['id']: img for img in coco_data['images']}
    annotations_map = {}

    for ann in coco_data['annotations']:
        if ann['image_id'] not in annotations_map:
            annotations_map[ann['image_id']] = []
        annotations_map[ann['image_id']].append(ann)
    
    # 카테고리 매핑
    category_map = {cat['id']: cat['name'] for cat in coco_data['categories']}
    
    # 각 이미지에 대해 처리
    for count, (image_id, image_info) in enumerate(image_map.items(), start=1):
        image_name = image_info['file_name']
        image_path = Path(image_dir) / image_name
        
        # 이미지 로드
        img = Image.open(image_path)
        width, height = img.size
        
        # 출력 디렉토리 구조 생성
        image_output_dir = output_dir / 'images' / album_name / Path(image_name).name
        image_output_dir.mkdir(exist_ok=True, parents=True)
        (image_output_dir / 'original').mkdir(exist_ok=True, parents=True)
        (image_output_dir / 'icon').mkdir(exist_ok=True, parents=True)
        (image_output_dir / 'thumbnail').mkdir(exist_ok=True, parents=True)
        
        # 이미지 저장
        original_path = image_output_dir / 'original' / image_name
        img.save(original_path)
        
        # icon과 thumbnail 생성
        icon = resize_keep_aspect(img, 64)
        thumbnail = resize_keep_aspect(img, 512)
        icon.save(image_output_dir / 'icon' / image_name)
        thumbnail.save(image_output_dir / 'thumbnail' / image_name)
        
        # image.json 생성
        image_json = {
            "id": image_id,
            "album_id": 7,  # 임시 값
            "filename": image_name,
            "path": str(Path('original') / image_name),
            "crc": calculate_crc(str(original_path)),
            "size": os.path.getsize(original_path),
            "is_deleted": False,
            "created_at": datetime.datetime.now().isoformat(),
            "updated_at": datetime.datetime.now().isoformat()
        }
        
        # image_map.json 생성
        annotations = []
        
        if image_id in annotations_map:
            if is_object_detection:
                # Object Detection 처리
                for ann in annotations_map[image_id]:
                    # bbox 좌표 변환 (COCO → VOC)
                    x, y, w, h = [int(c) for c in ann['bbox']]
                    x_min = x
                    y_min = y
                    x_max = x + w
                    y_max = y + h
                    
                    # 라벨
                    label = category_map[ann['category_id']]
                    
                    annotations.append({
                        "type": "box",
                        "bbox": [x_min, y_min, x_max, y_max],
                        "label": label,
                        "data": [[x_min, y_min], [x_max, y_max]]
                    })
            else:
                # Segmentation 처리
                mask = np.zeros((height, width), dtype=np.uint8)
                for idx, ann in enumerate(annotations_map[image_id], start=1):
                    # segmentation mask 생성 (0 또는 1 값)
                    seg_mask = polygon_to_mask(width, height, ann['segmentation'])
                    
                    # 객체별 idx 값을 마스크에 할당 (덮어쓰기 방식)
                    mask[seg_mask == 1] = idx
                    
                    # 라벨과 bbox
                    label = category_map[ann['category_id']]
                    x, y, w, h = [int(c) for c in ann['bbox']]

                    # COCO → VOC
                    x_min = x
                    y_min = y
                    x_max = x + w
                    y_max = y + h
                    
                    annotations.append({
                        "type": "seg",
                        "bbox": [x_min, y_min, x_max, y_max],
                        "label": label,
                        "data": idx,  # mask 상의 ID와 매칭
                    })

            # 공통 JSON 구조 생성
            image_map_json = {
                "id": image_id * 1000,  # 임시 값
                "collection_revision_id": 11,  # 임시 값
                "is_label_confirmed": True,
                "data": {
                    "annotations": annotations,
                    "imageClass": "",
                    "imageHeight": height,
                    "imageWidth": width,
                    "mask": []
                },
                "image": image_json,
                "split": "default",
                "created_at": datetime.datetime.now().isoformat(),
                "updated_at": datetime.datetime.now().isoformat()
            }

            # Segmentation인 경우에만 mask 데이터 추가
            if not is_object_detection:
                image_map_json["data"]["mask"] = encode_rle(mask)

        if progress_callback:
            progress_callback(count)
        
        # JSON 파일 저장
        with open(image_output_dir / 'image.json', 'w') as f:
            json.dump(image_json, f, indent=2)
        
        with open(image_output_dir / 'image_map.json', 'w') as f:
            json.dump(image_map_json, f, indent=2)

        