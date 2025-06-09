"""
COCO to Hubble Engine 변환기의 웹 인터페이스입니다.
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

# 파일 업로드 크기 제한을 5GB로 설정
st.set_page_config(
    page_title="COCO to Hubble Engine 변환기",
    page_icon="🔄",
    layout="wide",
    initial_sidebar_state="expanded"
)

def extract_zip(zip_path: str, extract_path: str) -> None:
    """ZIP 파일을 지정된 경로에 압축 해제합니다."""
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        # 모든 파일 목록을 가져옵니다
        file_list = zip_ref.namelist()
        
        # 이미지 파일만 필터링
        image_files = [f for f in file_list if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp'))]
        
        # 각 이미지 파일을 지정된 경로에 압축 해제
        for image_file in image_files:
            # ZIP 내부 경로에서 파일명만 추출
            file_name = Path(image_file).name
            # 압축 해제 시 파일명만 사용하여 평면화된 구조로 저장
            with zip_ref.open(image_file) as source, open(Path(extract_path) / file_name, 'wb') as target:
                shutil.copyfileobj(source, target)

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
    image_dir_path = Path(image_dir)
    st.info(f"이미지 디렉토리 검색 중: {image_dir_path}")
    
    for ext in ['.jpg', '.jpeg', '.png', '.bmp']:
        for img_path in image_dir_path.rglob(f'*{ext}'):
            # 파일명만 사용하여 매핑 (실제 경로 저장)
            image_files[img_path.name] = str(img_path)
            # 파일명에서 확장자를 제외한 이름도 매핑
            image_files[img_path.stem] = str(img_path)
    
    return image_files

def update_coco_image_paths(coco_data: dict, image_mapping: dict, use_relative_path: bool = False) -> dict:
    """COCO JSON의 이미지 경로를 업데이트합니다."""
    updated_images = []
    missing_images = []
    
    st.info(f"COCO 이미지 경로 업데이트 중 (use_relative_path: {use_relative_path})")
    
    for img in coco_data['images']:
        # 기존 경로에서 'images/' 접두사 제거
        file_name = Path(img['file_name']).name
        original_path = img['file_name']
        
        if file_name in image_mapping:
            if use_relative_path:
                # 최종 JSON 파일에는 상대 경로로 저장
                img['file_name'] = file_name
            else:
                # 실제 파일 경로 사용 (변환 과정)
                img['file_name'] = image_mapping[file_name]
            updated_images.append(img)
        else:
            missing_images.append(file_name)
            st.warning(f"이미지를 찾을 수 없음: {file_name}")
    
    if missing_images:
        st.warning(f"다음 이미지 파일들을 찾을 수 없습니다: {', '.join(missing_images)}")
    
    coco_data['images'] = updated_images
    return coco_data

def main():
    st.title("COCO to Hubble Engine 변환기")
    
    # 탭 생성
    tab1, tab2 = st.tabs(["Segmentation Label", "Object Detection Label"])
    
    with tab1:
        st.markdown("""
        ## Segmentation Label 변환
        이 앱은 COCO Segmentation 형식의 JSON 데이터와 이미지 파일들을 입력으로 받아,
        Custom 포맷으로 변환된 라벨 및 리사이즈된 이미지 파일을 출력합니다.
        """)
        
        # 사이드바 설정
        with st.sidebar:
            st.header("설정")
            album_name = st.text_input("앨범 이름", value="parmi_coco_converter")
        
        # 파일 업로드 섹션
        st.subheader("파일 업로드")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**COCO JSON 파일**")
            coco_file = st.file_uploader(
                "COCO JSON 파일을 업로드하세요",
                type=['json'],
                key="coco_file_seg",
                help="COCO 형식의 JSON 파일을 선택하세요."
            )
        
        with col2:
            st.markdown("**이미지 ZIP 파일**")
            image_zip = st.file_uploader(
                "이미지가 포함된 ZIP 파일을 업로드하세요",
                type=['zip'],
                key="image_zip_seg",
                help="이미지 파일들이 포함된 ZIP 파일을 선택하세요. (최대 5GB)",
            )
        
        # 변환 버튼
        if st.button("변환 시작", type="primary", key="convert_seg"):
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
                        
                        # COCO JSON의 이미지 경로 업데이트 (실제 경로 사용)
                        updated_coco_data = update_coco_image_paths(coco_data, image_mapping)
                        st.info(f"COCO JSON 이미지 경로 업데이트 완료: {len(updated_coco_data['images'])}개의 이미지 경로 업데이트됨")
                        
                        # 변환 수행
                        st.info("변환 작업 시작...")
                        # 변환 전 디렉토리 구조 확인
                        st.info(f"현재 디렉토리 구조:")
                        st.info(f"- 임시 디렉토리: {temp_dir}")
                        st.info(f"- 이미지 디렉토리: {image_dir}")
                        st.info("egd 형식으로 변환중..")
                                
                        total_images = len(updated_coco_data['images'])
                        # 진행률 바 초기화
                        progress_bar = st.progress(0.0)
                        percent_text = st.empty()

                        def progress_callback(processed):
                            frac = processed / total_images
                            frac = min(max(frac, 0.0), 1.0)
                            progress_bar.progress(frac)
                            percent_text.text(f"{processed}/{total_images} 처리됨 ({frac*100:.1f}%)")
                        
                        output_dir = temp_dir / "output"
                        output_dir.mkdir(exist_ok=True)
                        
                        # COCO JSON 파일 내용 확인
                        with open(coco_path, 'r') as f:
                            current_coco = json.load(f)
                            # 기존 이미지 경로에서 'images/' 접두사 제거
                            for img in current_coco['images']:
                                img['file_name'] = Path(img['file_name']).name
                            # 업데이트된 내용 저장
                            with open(coco_path, 'w') as f:
                                json.dump(current_coco, f)
                        
                        # 변환 함수 호출
                        convert_coco_to_custom(
                            str(coco_path),
                            str(image_dir),
                            str(output_dir),
                            album_name,
                            progress_callback=progress_callback
                        )
                        st.info("변환 작업 완료")
                        
                        # 최종 JSON 파일에는 상대 경로로 업데이트
                        final_json_path = temp_dir / "output" / "images" / album_name / "image.json"
                        if final_json_path.exists():
                            with open(final_json_path, 'r') as f:
                                final_data = json.load(f)
                            # 상대 경로로 업데이트 (images/ 접두사 제거)
                            final_data = update_coco_image_paths(final_data, {}, use_relative_path=True)
                            with open(final_json_path, 'w') as f:
                                json.dump(final_data, f)
                            st.info("최종 JSON 파일의 이미지 경로를 상대 경로로 업데이트 완료")
                        
                        # 압축 수행
                        st.info("압축 작업 시작...")
                        compress_output(str(temp_dir / "output"), album_name, remove_original=False)
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
                               - `output_dir` 경로: {temp_dir / "output"}
                               - 디렉토리 존재 여부: {temp_dir / "output".exists()}
                               - 디렉토리 내용: {list(temp_dir / "output".glob('*'))}
                            
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

    with tab2:
        st.markdown("""
        ## Object Detection Label 변환
        이 앱은 COCO Object Detection 형식의 JSON 데이터와 이미지 파일들을 입력으로 받아,
        Custom 포맷으로 변환된 라벨 및 리사이즈된 이미지 파일을 출력합니다.
        """)
        
        # 사이드바 설정
        with st.sidebar:
            st.header("설정")
            album_name_od = st.text_input("앨범 이름", value="parmi_coco_converter", key="album_name_od")
        
        # 파일 업로드 섹션
        st.subheader("파일 업로드")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**COCO JSON 파일**")
            coco_file_od = st.file_uploader(
                "COCO JSON 파일을 업로드하세요",
                type=['json'],
                key="coco_file_od",
                help="COCO 형식의 JSON 파일을 선택하세요."
            )
        
        with col2:
            st.markdown("**이미지 ZIP 파일**")
            image_zip_od = st.file_uploader(
                "이미지가 포함된 ZIP 파일을 업로드하세요",
                type=['zip'],
                key="image_zip_od",
                help="이미지 파일들이 포함된 ZIP 파일을 선택하세요. (최대 5GB)",
            )
        
        # 변환 버튼
        if st.button("변환 시작", type="primary", key="convert_od"):
            if not all([coco_file_od, image_zip_od, album_name_od]):
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
                            f.write(coco_file_od.getvalue())
                        st.info(f"COCO JSON 파일 저장 완료: {coco_path}")
                        
                        # COCO JSON 검증
                        coco_data = validate_coco_json(str(coco_path))
                        st.info(f"COCO JSON 검증 완료: {len(coco_data['images'])}개의 이미지, {len(coco_data['annotations'])}개의 어노테이션")
                        
                        # 이미지 ZIP 파일 저장 및 압축 해제
                        zip_path = temp_dir / "images.zip"
                        with open(zip_path, "wb") as f:
                            f.write(image_zip_od.getvalue())
                        st.info(f"ZIP 파일 저장 완료: {zip_path}")
                        
                        image_dir = temp_dir / "images"
                        image_dir.mkdir(exist_ok=True)
                        extract_zip(str(zip_path), str(image_dir))
                        st.info(f"ZIP 파일 압축 해제 완료: {image_dir}")
                        
                        # 이미지 파일 매핑 생성
                        image_mapping = find_image_files(str(image_dir))
                        st.info(f"이미지 파일 매핑 생성 완료: {len(image_mapping)}개의 이미지 파일 발견")
                        
                        # COCO JSON의 이미지 경로 업데이트 (실제 경로 사용)
                        updated_coco_data = update_coco_image_paths(coco_data, image_mapping)
                        st.info(f"COCO JSON 이미지 경로 업데이트 완료: {len(updated_coco_data['images'])}개의 이미지 경로 업데이트됨")
                        
                        # 변환 수행
                        st.info("변환 작업 시작...")
                        # 변환 전 디렉토리 구조 확인
                        st.info(f"현재 디렉토리 구조:")
                        st.info(f"- 임시 디렉토리: {temp_dir}")
                        st.info(f"- 이미지 디렉토리: {image_dir}")
                        st.info("egd 형식으로 변환중..")
                                
                        total_images = len(updated_coco_data['images'])
                        # 진행률 바 초기화
                        progress_bar = st.progress(0.0)
                        percent_text = st.empty()

                        def progress_callback(processed):
                            frac = processed / total_images
                            frac = min(max(frac, 0.0), 1.0)
                            progress_bar.progress(frac)
                            percent_text.text(f"{processed}/{total_images} 처리됨 ({frac*100:.1f}%)")
                        
                        output_dir = temp_dir / "output"
                        output_dir.mkdir(exist_ok=True)
                        
                        # COCO JSON 파일 내용 확인
                        with open(coco_path, 'r') as f:
                            current_coco = json.load(f)
                            # 기존 이미지 경로에서 'images/' 접두사 제거
                            for img in current_coco['images']:
                                img['file_name'] = Path(img['file_name']).name
                            # 업데이트된 내용 저장
                            with open(coco_path, 'w') as f:
                                json.dump(current_coco, f)
                        
                        # 변환 함수 호출
                        convert_coco_to_custom(
                            str(coco_path),
                            str(image_dir),
                            str(output_dir),
                            album_name_od,
                            progress_callback=progress_callback
                        )
                        st.info("변환 작업 완료")
                        
                        # 최종 JSON 파일에는 상대 경로로 업데이트
                        final_json_path = temp_dir / "output" / "images" / album_name_od / "image.json"
                        if final_json_path.exists():
                            with open(final_json_path, 'r') as f:
                                final_data = json.load(f)
                            # 상대 경로로 업데이트 (images/ 접두사 제거)
                            final_data = update_coco_image_paths(final_data, {}, use_relative_path=True)
                            with open(final_json_path, 'w') as f:
                                json.dump(final_data, f)
                            st.info("최종 JSON 파일의 이미지 경로를 상대 경로로 업데이트 완료")
                        
                        # 압축 수행
                        st.info("압축 작업 시작...")
                        compress_output(str(temp_dir / "output"), album_name_od, remove_original=False)
                        st.info("압축 작업 완료")
                        
                        # 생성된 .egd 파일 찾기
                        egd_files = list(temp_dir.glob(f"segment-{album_name_od}-rev1-*.egd"))
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
                               - `output_dir` 경로: {temp_dir / "output"}
                               - 디렉토리 존재 여부: {temp_dir / "output".exists()}
                               - 디렉토리 내용: {list(temp_dir / "output".glob('*'))}
                            
                            2. 압축 파일 검색 경로 확인:
                               - 검색 패턴: segment-{album_name_od}-rev1-*.egd
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