from flask import Flask, request, jsonify
import tensorflow as tf
from tensorflow.keras.applications.resnet50 import ResNet50, preprocess_input, decode_predictions
import numpy as np
from PIL import Image
import io
import base64
from kafka import KafkaProducer
import json
import logging

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)

model = ResNet50(weights='imagenet')

producer = KafkaProducer(
    bootstrap_servers=['192.168.5.227:9092'],
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

def process_image(image_base64):
    try:
        logging.debug(f"Received image data. Length: {len(image_base64)}")
        logging.debug(f"First 100 chars: {image_base64[:100]}")
        
        image_bytes = base64.b64decode(image_base64)
        logging.debug(f"Decoded base64. Length: {len(image_bytes)}")
        
        image = Image.open(io.BytesIO(image_bytes))
        logging.debug(f"Opened image. Size: {image.size}, Mode: {image.mode}")
        
        image = image.resize((224, 224))  # ResNet50 input size
        image_array = np.array(image)
        image_array = np.expand_dims(image_array, axis=0)
        return preprocess_input(image_array)
    except Exception as e:
        logging.error(f"Error in process_image: {str(e)}")
        raise

@app.route('/predict', methods=['POST'])
def predict():
    try:
        data = request.json
        image_id = data['image_id']
        image_data = data['image']
        
        logging.debug(f"Received request for image {image_id}")
        
        processed_image = process_image(image_data)
        predictions = model.predict(processed_image)
        decoded_predictions = decode_predictions(predictions, top=1)[0]
        
        inferred_value = decoded_predictions[0][1]
        
        kafka_message = {
            'image_id': image_id,
            'inferred_value': inferred_value
        }
        producer.send('team21', kafka_message)
        
        logging.info(f"Processed image {image_id}. Inferred value: {inferred_value}")
        
        return jsonify(kafka_message)
    except Exception as e:
        logging.error(f"Error in predict: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
