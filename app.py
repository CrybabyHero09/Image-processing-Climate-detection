from flask import Flask, render_template, request, jsonify
import os
import rasterio
import numpy as np
from rasterio.windows import Window
from PIL import Image
import io
from werkzeug.utils import secure_filename

app = Flask(__name__)


@app.route('/')
def home():
    return render_template('homepage.html')  # Landing page


@app.route("/index")
def index():
    ndvi_path = os.path.join("data", "NDVI")
    water_path = os.path.join("data", "Water Bodies Fraction")

    ndvi_files = [f for f in os.listdir(ndvi_path) if f.lower().endswith(".tif")]
    water_files = [f for f in os.listdir(water_path) if f.lower().endswith(".tif")]

    return render_template("index.html", ndvi_files=ndvi_files, water_files=water_files)


@app.route('/preview_image')
def preview_image():
    filename = request.args.get('filename')
    if not filename:
        return jsonify({"error": "No filename provided"}), 400

    ndvi_path = os.path.join("data", "NDVI", filename)
    water_path = os.path.join("data", "Water Bodies Fraction", filename)

    if os.path.exists(ndvi_path):
        path = ndvi_path
    elif os.path.exists(water_path):
        path = water_path
    else:
        return jsonify({"error": f"File not found: {filename}"}), 404

    with rasterio.open(path) as src:
        count = src.count
        if count >= 3:
            red = src.read(1)
            green = src.read(2)
            blue = src.read(3)
            arr = np.stack([red, green, blue], axis=-1)
        elif count == 1:
            gray = src.read(1)
            arr = np.stack([gray] * 3, axis=-1)
        else:
            return jsonify({"error": "Unsupported band count for preview"}), 500

        arr = np.clip((arr / arr.max()) * 255, 0, 255).astype(np.uint8)
        img = Image.fromarray(arr)
        bounds = src.bounds

    filename_clean = secure_filename(filename.replace(".tif", ".png"))
    preview_filename = os.path.join('static', 'previews', filename_clean)
    os.makedirs(os.path.dirname(preview_filename), exist_ok=True)

    img.save(preview_filename, 'PNG')

    return jsonify({
        "url": f"/static/previews/{filename_clean}",
        "bounds": [bounds.left, bounds.bottom, bounds.right, bounds.top]
    })


@app.route('/submit_aoi', methods=['POST'])
def submit_aoi():
    try:
        data = request.json
        image1_path = os.path.join('data', 'NDVI', data['image1'])
        image2_path = os.path.join('data', 'NDVI', data['image2'])
        geojson = data['geojson']
        preview_width = data.get('previewWidth', 1000)

        coords = geojson['geometry']['coordinates'][0]
        xs, ys = zip(*coords)
        min_x, max_x = int(min(xs)), int(max(xs))
        min_y, max_y = int(min(ys)), int(max(ys))
        width = max_x - min_x
        height = max_y - min_y

        with rasterio.open(image1_path) as src:
            img_width = src.width

        scale = img_width / preview_width

        min_x = int(min_x * scale)
        max_x = int(max_x * scale)
        min_y = int(min_y * scale)
        max_y = int(max_y * scale)
        width = max_x - min_x
        height = max_y - min_y

        if width <= 0 or height <= 0:
            return jsonify({"error": "Invalid AOI dimensions."}), 400

        def calc_ndvi(path, x, y, w, h):
            with rasterio.open(path) as src:
                red = src.read(1, window=Window(x, y, w, h)).astype('float32')
                nir = src.read(3, window=Window(x, y, w, h)).astype('float32')
                return (nir - red) / (nir + red + 1e-6)

        ndvi1 = calc_ndvi(image1_path, min_x, min_y, width, height)
        ndvi2 = calc_ndvi(image2_path, min_x, min_y, width, height)

        diff = ndvi2 - ndvi1
        change_map = np.where(diff < -0.2, 1, 0)
        change_pixels = int(np.sum(change_map))
        total_pixels = width * height
        change_percent = (change_pixels / total_pixels) * 100

        return jsonify({
            "change_pixels": change_pixels,
            "change_percent": round(change_percent, 2)
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/submit_water_aoi', methods=['POST'])
def submit_water_aoi():
    try:
        data = request.get_json()
        path1 = os.path.join('data', 'Water Bodies Fraction', data['image1'])
        path2 = os.path.join('data', 'Water Bodies Fraction', data['image2'])
        geojson = data['geojson']
        preview_width = data.get('previewWidth', 1000)

        coords = geojson['geometry']['coordinates'][0]
        xs, ys = zip(*coords)
        min_x, max_x = int(min(xs)), int(max(xs))
        min_y, max_y = int(min(ys)), int(max(ys))
        width = max_x - min_x
        height = max_y - min_y

        with rasterio.open(path1) as src:
            img_width = src.width

        scale = img_width / preview_width
        min_x = int(min_x * scale)
        max_x = int(max_x * scale)
        min_y = int(min_y * scale)
        max_y = int(max_y * scale)
        width = max_x - min_x
        height = max_y - min_y

        def read_water(path, x, y, w, h):
            with rasterio.open(path) as src:
                return src.read(1, window=Window(x, y, w, h)).astype(np.float32)

        water1 = read_water(path1, min_x, min_y, width, height)
        water2 = read_water(path2, min_x, min_y, width, height)

        water_diff = water2 - water1
        change_map = (water_diff > 0.1).astype(np.uint8)
        change_pixels = int(np.sum(change_map))
        total_pixels = width * height
        percent_change = (change_pixels / total_pixels) * 100 if total_pixels else 0

        return jsonify({
            'change_pixels': change_pixels,
            'percent_change': round(percent_change, 2)
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)
