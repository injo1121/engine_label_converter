import argparse
from utils import convert_coco_to_custom, compress_output

def main():
    parser = argparse.ArgumentParser(description='COCO-Segmentation to Custom Format Converter')
    parser.add_argument('--coco_json', default='data/raw/label.json', help='Path to COCO JSON file')
    parser.add_argument('--image_dir', default='data/raw/images', help='Directory containing images')
    parser.add_argument('--album_name', default='injo_test', help='Album name')
    parser.add_argument('--output_dir', default='data/custom', help='Output directory')
    
    args = parser.parse_args()
    
    # COCO 형식을 Custom 형식으로 변환
    convert_coco_to_custom(args.coco_json, args.image_dir, args.output_dir, args.album_name)
    
    # 출력 폴더 압축
    compress_output(args.output_dir, args.album_name, remove_original=False)

if __name__ == "__main__":
    main() 