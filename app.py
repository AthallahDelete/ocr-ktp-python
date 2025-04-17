from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import requests
import base64
import os
import uuid
import time

app = Flask(__name__)
CORS(app)

# Path penyimpanan gambar KTP
UPLOAD_FOLDER = r'./storage/file'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Path penyimpanan cap jempol
FINGERPRINT_FOLDER = r'./storage/capJempol'
os.makedirs(FINGERPRINT_FOLDER, exist_ok=True)

def ocr_ktp(image_data, api_key):
    """
    Mengirim gambar KTP ke API OCR dan mengambil hasilnya.
    """
    url = 'https://api.ekycpro.com/v1/id_ocr/general'
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'X-API-Key': api_key
    }
    data = {'img': image_data}
    
    try:
        response = requests.post(url, headers=headers, data=data)
        if response.status_code == 200:
            return response.json()
        else:
            return {"status": "INNER_ERROR", "message": "Service is not available right now, please try again later"}
    except Exception as e:
        return {"status": "ERROR", "message": f"Exception occurred: {str(e)}"}

@app.route('/process-ocr', methods=['POST'])
def process_ocr():
    try:
        data = request.json
        image_data = data.get('image', '').split(',')[1]
        api_key = os.getenv('API_KEY') or 'XAenIDLIyaELTeasy001LLyoheIDueasyMwIkQAhFweNbLVBRjzwVbNqa001'

        unique_id = str(uuid.uuid4())

        # Simpan gambar KTP
        ktp_image_path = os.path.join(UPLOAD_FOLDER, f'ktp_{unique_id}.jpg')
        with open(ktp_image_path, 'wb') as f:
            f.write(base64.b64decode(image_data))

        # Kirim ke OCR API
        result = ocr_ktp(image_data, api_key)

        if 'message' in result:
            ktp_data = result['message']
            ktp_data['pathfile'] = f"/storage/public/file/ktp_{unique_id}.jpg"
            return jsonify({"status": "success", "ktp_data": ktp_data})
        return jsonify(result)
    except Exception as e:
        return jsonify({"status": "ERROR", "message": str(e)})

@app.route('/process-fingerprint', methods=['POST'])
def process_fingerprint():
    try:
        data = request.json
        fingerprint_data = data.get('fingerprint', '')

        if not fingerprint_data:
            print("[DEBUG] Tidak ada data fingerprint yang diterima.")
            return jsonify({"status": "ERROR", "message": "Fingerprint data is missing"}), 400

        # Debugging panjang data Base64 sebelum decoding
        fingerprint_base64 = fingerprint_data.split(',')[1] if ',' in fingerprint_data else fingerprint_data
        print(f"[DEBUG] Panjang Base64 Fingerprint: {len(fingerprint_base64)} karakter")

        timestamp = int(time.time())
        fingerprint_filename = f'capJempol_{timestamp}.jpg'
        fingerprint_image_path = os.path.join(FINGERPRINT_FOLDER, fingerprint_filename)

        # Debugging path penyimpanan file
        print(f"[DEBUG] Path Penyimpanan Fingerprint: {fingerprint_image_path}")

        # Menyimpan gambar fingerprint
        with open(fingerprint_image_path, 'wb') as f:
            f.write(base64.b64decode(fingerprint_base64))

        print("[DEBUG] Fingerprint berhasil disimpan!")

        return jsonify({
            "status": "success",
            "fingerprint_image_url": f"/storage/public/capJempol/{fingerprint_filename}"
        })
    
    except Exception as e:
        print(f"[DEBUG] ERROR saat memproses fingerprint: {str(e)}")
        return jsonify({"status": "ERROR", "message": str(e)}), 500

@app.route('/uploads/<filename>', methods=['GET'])
def get_uploaded_image(filename):
    return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=True)

@app.route('/fingerprint/<filename>', methods=['GET'])
def get_fingerprint_image(filename):
    return send_from_directory(FINGERPRINT_FOLDER, filename, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)