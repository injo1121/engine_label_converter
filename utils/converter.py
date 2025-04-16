"""
COCO Segmentation 형식을 Custom 형식으로 변환하는 모듈입니다.
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
import numpy as np
from PIL import Image
import datetime
from tqdm import tqdm

from .image_utils import polygon_to_mask, resize_keep_aspect
from .encoding_utils import encode_rle, calculate_crc
from .metadata_utils import create_collection_metadata

def convert_coco_to_custom(coco_json_path: str, image_dir: str, output_dir: str, album_name: str):
    """COCO 포맷을 Custom 포맷으로 변환합니다."""
    # 출력 디렉토리 생성
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)
    
    # COCO JSON 로드
    with open(coco_json_path, 'r') as f:
        coco_data = json.load(f)
    
    # 컬렉션 메타데이터 생성
    create_collection_metadata(output_dir, coco_data['categories'], album_name)
    
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
    for image_id, image_info in tqdm(image_map.items(), desc="Converting images"):
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
        mask = np.zeros((height, width), dtype=np.uint8)
        
        # 라벨별 데이터 카운터 초기화
        label_counter = {}
        
        if image_id in annotations_map:
            for ann in annotations_map[image_id]:
                # segmentation mask 생성
                seg_mask = polygon_to_mask(width, height, ann['segmentation'])
                mask = np.maximum(mask, seg_mask)
                
                # 라벨 가져오기
                label = category_map[ann['category_id']]
                
                # 라벨별 카운터 증가
                if label not in label_counter:
                    label_counter[label] = 1
                else:
                    label_counter[label] += 1
                
                # bbox를 정수형으로 변환
                bbox = [int(coord) for coord in ann['bbox']]
                
                annotations.append({
                    "type": "seg",
                    "bbox": bbox,
                    "label": label,
                    "data": label_counter[label]
                })
        
        image_map_json = {
            "id": image_id * 1000,  # 임시 값
            "collection_revision_id": 11,  # 임시 값
            "is_label_confirmed": True,
            "data": {
                "annotations": annotations,
                "imageClass": "",
                "imageHeight": height,
                "imageWidth": width,
                "mask": encode_rle(mask)
            },
            "image": image_json,
            "split": "default",
            "created_at": datetime.datetime.now().isoformat(),
            "updated_at": datetime.datetime.now().isoformat()
        }
        
        # JSON 파일 저장
        with open(image_output_dir / 'image.json', 'w') as f:
            json.dump(image_json, f, indent=2)
        
        with open(image_output_dir / 'image_map.json', 'w') as f:
            json.dump(image_map_json, f, indent=2) 