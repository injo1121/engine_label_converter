# COCO-Segmentation to Custom Format 변환기

이 프로그램은 COCO Segmentation 형식의 JSON 데이터와 이미지 파일들을 입력으로 받아, 사용자 정의(Custom) 포맷으로 변환된 라벨 및 리사이즈된 이미지 파일을 출력하는 변환기입니다.

## 설치 방법

1. 저장소를 클론합니다:
```bash
git clone <repository-url>
cd engine_label_converter
```

2. 필요한 패키지를 설치합니다:
```bash
pip install -r requirements.txt
```

## 사용 방법

```bash
python main.py --coco_json <path_to_coco_json> --image_dir <path_to_images> --output_dir <path_to_output>
```

### 매개변수 설명

- `--coco_json`: COCO 형식의 JSON 파일 경로
- `--image_dir`: 이미지 파일들이 있는 디렉토리 경로
- `--output_dir`: 변환된 결과를 저장할 디렉토리 경로

## 출력 구조

```
output/
  └─ <image_name>/
       ├─ image.json
       ├─ image_map.json
       ├─ original/
       │    └─ <image_name>.png
       ├─ icon/
       │    └─ <image_name>.png  (최대 64px, 비율 유지)
       └─ thumbnail/
            └─ <image_name>.png (최대 512px, 비율 유지)
```

## 요구사항

- Python 3.10+
- Pillow
- numpy
- tqdm
