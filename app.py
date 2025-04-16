"""
COCO-Segmentation to Custom Format 변환기의 웹 인터페이스입니다.
파일 업로드를 통해 변환 작업을 수행할 수 있습니다.

Author: injokim <injo1121@rtm.ai>
"""

import streamlit as st
from pathlib import Path
import os
import shutil
import tempfile
import zipfile
import json
from utils import convert_coco_to_custom, compress_output

def extract_zip(zip_path: str, extract_path: str) -> None:
    """ZIP 파일을 지정된 경로에 압축 해제합니다."""
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_path)

def validate_coco_json(coco_path: str) -> dict:
    """COCO JSON 파일을 검증하고 필요한 정보를 반환합니다."""
    with open(coco_path, 'r') as f:
        coco_data = json.load(f)
    
    # 필수 필드 확인
    required_fields = ['images', 'annotations', 'categories']
    for field in required_fields:
        if field not in coco_data:
            raise ValueError(f"COCO JSON 파일에 필수 필드 '{field}'가 없습니다.")
    
    return coco_data

def find_image_files(image_dir: str) -> dict:
    """이미지 디렉토리에서 모든 이미지 파일을 찾아 매핑을 생성합니다."""
    image_files = {}
    for ext in ['.jpg', '.jpeg', '.png', '.bmp']:
        for img_path in Path(image_dir).rglob(f'*{ext}'):
            # 파일명만 사용하여 매핑
            image_files[img_path.name] = str(img_path)
            # 파일명에서 확장자를 제외한 이름도 매핑
            image_files[img_path.stem] = str(img_path)
    return image_files

def update_coco_image_paths(coco_data: dict, image_mapping: dict) -> dict:
    """COCO JSON의 이미지 경로를 실제 파일 경로로 업데이트합니다."""
    updated_images = []
    missing_images = []
    
    for img in coco_data['images']:
        file_name = Path(img['file_name']).name
        if file_name in image_mapping:
            img['file_name'] = image_mapping[file_name]
            updated_images.append(img)
        else:
            missing_images.append(file_name)
    
    if missing_images:
        st.warning(f"다음 이미지 파일들을 찾을 수 없습니다: {', '.join(missing_images)}")
    
    coco_data['images'] = updated_images
    return coco_data

def main():
    st.set_page_config(
        page_title="COCO-Segmentation 변환기",
        page_icon="🔄",
        layout="wide"
    )
    
    st.title("COCO-Segmentation to Custom Format 변환기")
    st.markdown("""
    이 앱은 COCO Segmentation 형식의 JSON 데이터와 이미지 파일들을 입력으로 받아,
    Custom 포맷으로 변환된 라벨 및 리사이즈된 이미지 파일을 출력합니다.
    """)
    
    # 사이드바 설정
    with st.sidebar:
        st.header("설정")
        album_name = st.text_input("앨범 이름", value="injo_test")
    
    # 파일 업로드 섹션
    st.subheader("파일 업로드")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**COCO JSON 파일**")
        coco_file = st.file_uploader(
            "COCO JSON 파일을 업로드하세요",
            type=['json'],
            key="coco_file",
            help="COCO 형식의 JSON 파일을 선택하세요."
        )
    
    with col2:
        st.markdown("**이미지 ZIP 파일**")
        image_zip = st.file_uploader(
            "이미지가 포함된 ZIP 파일을 업로드하세요",
            type=['zip'],
            key="image_zip",
            help="이미지 파일들이 포함된 ZIP 파일을 선택하세요."
        )
    
    # 변환 버튼
    if st.button("변환 시작", type="primary"):
        if not all([coco_file, image_zip, album_name]):
            st.error("모든 파일을 업로드해주세요.")
            return
        
        try:
            with st.spinner("변환 중..."):
                # 임시 디렉토리 생성
                with tempfile.TemporaryDirectory() as temp_dir:
                    temp_dir = Path(temp_dir)
                    st.info(f"임시 디렉토리 생성: {temp_dir}")
                    
                    # COCO JSON 파일 저장
                    coco_path = temp_dir / "label.json"
                    with open(coco_path, "wb") as f:
                        f.write(coco_file.getvalue())
                    st.info(f"COCO JSON 파일 저장 완료: {coco_path}")
                    
                    # COCO JSON 검증
                    coco_data = validate_coco_json(str(coco_path))
                    st.info(f"COCO JSON 검증 완료: {len(coco_data['images'])}개의 이미지, {len(coco_data['annotations'])}개의 어노테이션")
                    
                    # 이미지 ZIP 파일 저장 및 압축 해제
                    zip_path = temp_dir / "images.zip"
                    with open(zip_path, "wb") as f:
                        f.write(image_zip.getvalue())
                    st.info(f"ZIP 파일 저장 완료: {zip_path}")
                    
                    image_dir = temp_dir / "images"
                    image_dir.mkdir(exist_ok=True)
                    extract_zip(str(zip_path), str(image_dir))
                    st.info(f"ZIP 파일 압축 해제 완료: {image_dir}")
                    
                    # 이미지 파일 매핑 생성
                    image_mapping = find_image_files(str(image_dir))
                    st.info(f"이미지 파일 매핑 생성 완료: {len(image_mapping)}개의 이미지 파일 발견")
                    
                    # COCO JSON의 이미지 경로 업데이트
                    updated_coco_data = update_coco_image_paths(coco_data, image_mapping)
                    st.info(f"COCO JSON 이미지 경로 업데이트 완료: {len(updated_coco_data['images'])}개의 이미지 경로 업데이트됨")
                    
                    # 업데이트된 COCO JSON 저장
                    with open(coco_path, 'w') as f:
                        json.dump(updated_coco_data, f)
                    
                    # 출력 디렉토리 설정
                    output_dir = temp_dir / "output"
                    output_dir.mkdir(exist_ok=True)
                    st.info(f"출력 디렉토리 생성: {output_dir}")
                    
                    # 변환 수행
                    st.info("변환 작업 시작...")
                    convert_coco_to_custom(str(coco_path), str(image_dir), str(output_dir), album_name)
                    st.info("변환 작업 완료")
                    
                    # 압축 수행
                    st.info("압축 작업 시작...")
                    compress_output(str(output_dir), album_name, remove_original=False)
                    st.info("압축 작업 완료")
                    
                    # 생성된 .egd 파일 찾기
                    egd_files = list(temp_dir.glob(f"segment-{album_name}-rev1-*.egd"))
                    st.info(f"생성된 .egd 파일 검색: {len(egd_files)}개의 파일 발견")
                    
                    if egd_files:
                        latest_file = max(egd_files, key=os.path.getctime)
                        st.success("변환이 완료되었습니다!")
                        
                        # 다운로드 버튼 생성
                        with open(latest_file, "rb") as f:
                            st.download_button(
                                label=".egd 파일 다운로드",
                                data=f,
                                file_name=latest_file.name,
                                mime="application/octet-stream"
                            )
                    else:
                        st.error("출력 파일이 생성되지 않았습니다.")
                        st.error("문제 해결을 위한 확인사항:")
                        st.markdown(f"""
                        1. 출력 디렉토리 확인:
                           - `output_dir` 경로: {output_dir}
                           - 디렉토리 존재 여부: {output_dir.exists()}
                           - 디렉토리 내용: {list(output_dir.glob('*'))}
                        
                        2. 압축 파일 검색 경로 확인:
                           - 검색 패턴: segment-{album_name}-rev1-*.egd
                           - 검색 위치: {temp_dir}
                           - 전체 파일 목록: {list(temp_dir.glob('*'))}
                        
                        3. 임시 디렉토리 권한 확인:
                           - 쓰기 권한: {os.access(temp_dir, os.W_OK)}
                           - 읽기 권한: {os.access(temp_dir, os.R_OK)}
                        """)
        
        except Exception as e:
            st.error(f"변환 중 오류가 발생했습니다: {str(e)}")
            st.error("오류 해결을 위한 팁:")
            st.markdown("""
            1. COCO JSON 파일의 이미지 경로가 실제 이미지 경로와 일치하는지 확인하세요.
            2. 이미지 파일명이 COCO JSON에 기록된 파일명과 일치하는지 확인하세요.
            3. 이미지 파일의 확장자가 일치하는지 확인하세요 (대소문자 구분).
            4. ZIP 파일이 올바르게 압축되어 있는지 확인하세요.
            """)

if __name__ == "__main__":
    main() 