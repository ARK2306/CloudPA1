import psycopg2
import time
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

conn = psycopg2.connect(
    dbname="team21_data",
    user="postgres",
    password="password",
    host="localhost"
)
cur = conn.cursor()

def monitor_db():
    last_count = 0
    last_inference_count = 0
    
    while True:
        try:
            # Check total count
            cur.execute("SELECT COUNT(*) FROM iot_image_data")
            current_count = cur.fetchone()[0]
            
            if current_count > last_count:
                new_entries = current_count - last_count
                logging.info(f"New entries detected. Total count: {current_count}, New entries: {new_entries}")
                
                # Check latest entries
                cur.execute("""
                    SELECT unique_id, ground_truth, inferred_value 
                    FROM iot_image_data 
                    ORDER BY id DESC 
                    LIMIT %s
                """, (new_entries,))
                latest_entries = cur.fetchall()
                
                for entry in latest_entries:
                    logging.info(f"New entry: {entry}")
            
            # Check for new inferences
            cur.execute("SELECT COUNT(*) FROM iot_image_data WHERE inferred_value IS NOT NULL")
            current_inference_count = cur.fetchone()[0]
            
            if current_inference_count > last_inference_count:
                new_inferences = current_inference_count - last_inference_count
                logging.info(f"New inferences detected. Total inferences: {current_inference_count}, New inferences: {new_inferences}")
                
                # Check latest inferences
                cur.execute("""
                    SELECT unique_id, ground_truth, inferred_value 
                    FROM iot_image_data 
                    WHERE inferred_value IS NOT NULL
                    ORDER BY id DESC 
                    LIMIT %s
                """, (new_inferences,))
                latest_inferences = cur.fetchall()
                
                for inference in latest_inferences:
                    logging.info(f"New inference: {inference}")
            
            last_count = current_count
            last_inference_count = current_inference_count
            
            time.sleep(60)  # Check every minute
        except Exception as e:
            logging.error(f"Error monitoring database: {e}")
            time.sleep(60)  # Wait before retrying

if __name__ == "__main__":
    monitor_db()
