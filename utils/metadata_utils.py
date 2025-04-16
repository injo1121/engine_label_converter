"""
메타데이터 생성 관련 유틸리티 함수들을 제공하는 모듈입니다.
주요 기능:
- 컬렉션 메타데이터 JSON 파일 생성
- 카테고리 정보를 기반으로 라벨 목록 생성

Author: injokim <injo1121@rtm.ai>
"""

import json
import datetime
from pathlib import Path
from typing import Dict, List

def create_collection_metadata(output_dir: str, categories: List[Dict], album_name: str) -> None:
    """컬렉션 메타데이터 JSON 파일을 생성합니다."""
    now = datetime.datetime.now().isoformat()
    
    # 카테고리 이름 목록 추출
    labels = [cat['name'] for cat in categories]
    
    metadata = {
        "id": 11,
        "revision": 1,
        "base_revision": 1,
        "is_latest": True,
        "is_finalized": True,
        "labels": labels,
        "created_at": now,
        "updated_at": now,
        "collection": {
            "id": 11,
            "name": album_name,
            "task": "segment",
            "created_at": now,
            "updated_at": now
        }
    }
    
    # 메타데이터 파일 저장
    metadata_path = Path(output_dir) / "collection_revision.json"
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2) 