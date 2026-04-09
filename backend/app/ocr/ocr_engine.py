import easyocr
import cv2
import numpy as np

# Initialize EasyOCR once
reader = easyocr.Reader(['en'], gpu=False)

def preprocess(image_path):
    img = cv2.imread(image_path)

    if img is None:
        raise Exception("Image not readable")

    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # 🔥 Resize (CRITICAL for OCR)
    scale_percent = 150
    width = int(gray.shape[1] * scale_percent / 100)
    height = int(gray.shape[0] * scale_percent / 100)
    gray = cv2.resize(gray, (width, height), interpolation=cv2.INTER_CUBIC)

    print("[DEBUG] Resized shape:", gray.shape)

    # 🔥 Denoise
    gray = cv2.fastNlMeansDenoising(gray, None, 30, 7, 21)

    # 🔥 Sharpen
    kernel = np.array([[0, -1, 0],
                       [-1, 5,-1],
                       [0, -1, 0]])
    gray = cv2.filter2D(gray, -1, kernel)

    # 🔥 Threshold (strong)
    thresh = cv2.threshold(
        gray, 0, 255,
        cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )[1]

    # OPTIONAL: Save debug image
    debug_path = image_path.replace(".png", "_processed.png")
    cv2.imwrite(debug_path, thresh)
    print(f"[DEBUG] Processed image saved: {debug_path}")

    return thresh

def extract_text(image_path):
    try:
        print("\n================ OCR START ================")
        print(f"Processing: {image_path}")

        img = preprocess(image_path)

        result = reader.readtext(img)

        ocr_data = []

        print("\n[DEBUG] RAW OCR OUTPUT:")

        for bbox, text, conf in result:
            print(f"Text: {text} | Conf: {round(conf, 3)}")

            cleaned = text.strip()
            if not cleaned:
                continue

            x = int(bbox[0][0])
            y = int(bbox[0][1])

            ocr_data.append({
                "text": cleaned,
                "conf": conf,
                "x": x,
                "y": y
            })

        # ✅ SORT by position (top → bottom, left → right)
        ocr_data = sorted(ocr_data, key=lambda x: (x["y"], x["x"]))

        print("\n[DEBUG] SORTED OCR DATA:")
        for item in ocr_data[:20]:
            print(item)

        print("================ OCR END ==================\n")

        return {
            "ocr_data": ocr_data,
            "confidence": sum([i["conf"] for i in ocr_data]) / len(ocr_data) if ocr_data else 0,
            "engine": "easyocr"
        }

    except Exception as e:
        print("OCR failed:", e)

        return {
            "ocr_data": [],
            "confidence": 0,
            "engine": "failed"
        }
