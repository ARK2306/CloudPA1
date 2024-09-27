import tensorflow as tf
import numpy as np
import pickle
from kafka import KafkaProducer
import json
import base64
from PIL import Image
import io
import time
import logging
import cv2
BLURINESS_RATE = 0.239
DEFAULT_SIGMA_RANGE = 2.5
DEFAULT_KERNEL_MIN, DEFAULT_KERNEL_MAX  = 3, 7

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

meta_path = 'cifar-100-python/meta'
with open(meta_path, 'rb') as f:
    meta_data = pickle.load(f, encoding='latin1')

fine_label_names = meta_data['fine_label_names']

(x_train, y_train), (x_test, y_test) = tf.keras.datasets.cifar100.load_data()

bootstrap_servers = '192.168.5.227:9092'

producer = KafkaProducer(bootstrap_servers=bootstrap_servers,
                         value_serializer=lambda v: json.dumps(v).encode('utf-8'))

topic_name = 'team21'

def encode_image(image):
    pil_image = Image.fromarray(image.astype(np.uint8))
    buffered = io.BytesIO()
    pil_image.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

while True:
    random_index = np.random.randint(0, len(x_test))
    selected_image = x_test[random_index]
    # 23.9% of selected image will be reassigned as blurred images
    if np.random.rand() < BLURINESS_RATE:
      try:
        sigma = max(0.5, np.random.rand() * DEFAULT_SIGMA_RANGE)
        ketnet = np.random.randint(DEFAULT_KERNEL_MIN // 2, DEFAULT_KERNEL_MAX // 2) * 2 + 1
        selected_image = cv2.GaussianBlur(selected_image, (ketnet, ketnet), sigma, sigma)
      except cv2.error as e:
        logging.error(f"Error applying Gaussian blur: {e}")
        # Optionally, you could skip blurring for this image
        pass

    ground_truth = fine_label_names[y_test[random_index][0]]
    
    image_base64 = encode_image(selected_image)
    
    message = {
        'ID': str(random_index),
        'GroundTruth': str(ground_truth),
        'Data': image_base64
    }

    logging.debug(f"Sending message for image {random_index}")
    logging.debug(f"Ground Truth: {ground_truth}")
    logging.debug(f"Image shape: {selected_image.shape}")
    logging.debug(f"Base64 length: {len(image_base64)}")
    logging.debug(f"First 100 chars of base64: {image_base64[:100]}")

    producer.send(topic_name, value=message)
    producer.flush()
    
    logging.info(f"Sent message for image {random_index}")
    time.sleep(1)
