from kafka import KafkaConsumer
import json
import requests
import time
import logging
import base64

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class InferenceConsumer:
    def __init__(self, topic_name, bootstrap_servers, ml_server_url, max_retries=3, retry_delay=5):
        self.consumer = KafkaConsumer(
            topic_name,
            bootstrap_servers=bootstrap_servers,
            value_deserializer=lambda x: json.loads(x.decode('utf-8'))
        )
        self.ml_server_url = ml_server_url
        self.max_retries = max_retries
        self.retry_delay = retry_delay

    def process_messages(self):
        for message in self.consumer:
            data = message.value
            if 'Data' in data:
                image_id = data['ID']
                image_data = data['Data']
                self.process_image(image_id, image_data)

    def process_image(self, image_id, image_data):
        logging.debug(f"Received image data for ID {image_id}. First 100 chars: {image_data[:100]}")
        
        try:
            # Try to decode the base64 string
            image_bytes = base64.b64decode(image_data)
            logging.debug(f"Successfully decoded base64. First 20 bytes: {image_bytes[:20]}")
        except:
            logging.error(f"Failed to decode base64 for image {image_id}")
            return

        for attempt in range(self.max_retries):
            try:
                payload = {'image_id': image_id, 'image': image_data}
                response = requests.post(
                    self.ml_server_url, 
                    json=payload,
                    timeout=30
                )
                response.raise_for_status()
                
                result = response.json()
                logging.info(f"Processed image {image_id} successfully")
                logging.info(f"Inferred value: {result.get('inferred_value')}")
                return
            
            except requests.exceptions.RequestException as e:
                logging.error(f"Attempt {attempt + 1} failed for image {image_id}: {str(e)}")
                if attempt < self.max_retries - 1:
                    logging.info(f"Retrying in {self.retry_delay} seconds...")
                    time.sleep(self.retry_delay)
                else:
                    logging.error(f"Failed to process image {image_id} after {self.max_retries} attempts")

    def close(self):
        self.consumer.close()

if __name__ == "__main__":
    topic_name = 'team21'
    bootstrap_servers = ['192.168.5.227:9092']
    ml_server_url = 'http://localhost:5000/predict'  # Update this with the actual ML server URL
    
    consumer = InferenceConsumer(topic_name, bootstrap_servers, ml_server_url)
    try:
        logging.info("Starting the inference consumer...")
        consumer.process_messages()
    except KeyboardInterrupt:
        logging.info("Stopping the consumer...")
    finally:
        consumer.close()
