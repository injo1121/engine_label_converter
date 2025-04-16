"""
파일 처리 관련 유틸리티 함수들을 제공하는 모듈입니다.
주요 기능:
- 출력 폴더를 압축하고 .egd 확장자로 변경
- 압축 파일명에 타임스탬프와 랜덤 문자열 추가

Author: injokim <injo1121@rtm.ai>
"""

import shutil
from pathlib import Path
import datetime
import random
import string

def compress_output(output_dir: str, album_name: str, remove_original: bool = True) -> None:
    """출력 폴더를 압축하고 .egd 확장자로 변경합니다."""
    # 6개 숫자 문자열 랜덤 생성 
    random_int_string = ''.join(random.choices(string.digits, k=6))
    zip_path = Path(output_dir).parent / f"segment-{album_name}-rev1-{datetime.datetime.now().strftime('%Y%m%d')}-{random_int_string}.zip"
    egd_path = Path(output_dir).parent / f"segment-{album_name}-rev1-{datetime.datetime.now().strftime('%Y%m%d')}-{random_int_string}.egd"
    
    # 기존 압축 파일이 있다면 삭제
    if zip_path.exists():
        zip_path.unlink()
    if egd_path.exists():
        egd_path.unlink()
    
    # 압축 수행
    shutil.make_archive(str(zip_path.with_suffix('')), 'zip', Path(output_dir))
    
    # .zip을 .egd로 변경
    zip_path.rename(egd_path)
    
    # 원본 폴더 삭제
    if remove_original:
        shutil.rmtree(Path(output_dir)) 