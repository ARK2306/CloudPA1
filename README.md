# CloudPA1

Readme file

1. Introduction

This Pipeline is designed to process and analyze image data in real-time using a distributed architecture. The system simulates IoT devices sending image data, processes this data through a machine learning model for classification, and stores both the raw data and inference results in a centralized database.

Key features:
• Distributed processing across multiple virtual machines
• Real-time data ingestion and processing using Apache Kafka
• Machine learning inference using a pre-trained ResNet50 model
• Centralized data storage in a PostgreSQL database
• Scalable architecture designed for high throughput and low latency

2. Components

2.1. IoT Data Simulator (VM1)

Purpose: Simulates IoT devices sending image data
Technology: Python script using CIFAR-100 dataset
Key Features:
• Generates random images from CIFAR-100
• Encodes images in base64 format
• Sends data to Kafka topic 'team21'

2.2 Kafka Broker (VM2)

Purpose: Message queuing and data streaming
Technology: Apache Kafka 2.8.0
Configuration:
• Single topic named 'team21'
• 3 partitions (configurable)
• Replication factor: 1 (can be increased for fault tolerance)

2.3. Database Consumer (VM3)

Purpose: Consumes messages from Kafka and stores in database
Technology: Python script with psycopg2 for PostgreSQL interaction
Key Features:
• Handles both original image data and inference results
• Uses UPSERT operations for data consistency
• Logs operations for monitoring

2.4. ML Inference Engine (VM4)

Purpose: Processes images and generates classification results
Technology: Python with TensorFlow/Keras, Flask for API
Model: Pre-trained ResNet50
Key Features:
• RESTful API for receiving image data
• Sends inference results back to Kafka

3. Data Flow

1. IoT Simulator (VM1) generates image data and publishes to Kafka topic 'team21'.
2. Database Consumer (VM3) reads data from 'team21' topic and inserts into PostgreSQL.
3. ML Inference Consumer (VM4) reads data from 'team21' topic.
4. ML Inference Engine processes the image and generates classification results.
5. Inference results are published back to 'team21' topic.
6. Database Consumer reads inference results and updates corresponding database records.

4. Setup and Installation

4.1. Prerequisites

• Python 3.8+
• Apache Kafka 2.8.0
• PostgreSQL 13+
• TensorFlow 

4.2. VM1 Setup

1. Install required Python packages:
   pip install tensorflow numpy kafka-python Pillow

2. Copy the IoT simulator script to VM1.
3. Update Kafka bootstrap servers in the script.
4. Run the script:
   python iot_simulator.py

4.3. VM2 Setup

1. Install Apache Kafka 2.8.0.
2. Configure server.properties:
   num.partitions=3
   default.replication.factor=1

3. Start Zookeeper and Kafka server:
   bin/zookeeper-server-start.sh config/zookeeper.properties
   bin/kafka-server-start.sh config/server.properties

4. Create 'team21' topic:
   bin/kafka-topics.sh --create --topic team21 --bootstrap-server localhost:9092 --partitions 3 --replication-factor 1

4.4. VM3 Setup

1. Install PostgreSQL 13+.
2. Create database and table:
   CREATE DATABASE team21_data;
   \c team21_data
   CREATE TABLE iot_image_data (
       id SERIAL PRIMARY KEY,
       unique_id TEXT UNIQUE,
       ground_truth TEXT,
       data BYTEA,
       inferred_value TEXT
   );

3. Install required Python packages:
   pip install kafka-python psycopg2-binary

4. Copy the database consumer script to VM3.
5. Update Kafka bootstrap servers and database connection details in the script.
6. Run the script:
   python db_consumer.py

4.5. VM4 Setup

1. Install required Python packages:
   pip install tensorflow keras flask kafka-python requests

2. Copy the ML inference engine and consumer scripts to VM4.
3. Update Kafka bootstrap servers in the scripts.
4. Run the Flask app:
   python ml_server.py

5. In a separate terminal, run the inference consumer:
   python inference_consumer.py

5. Operation

1. Start all components in the following order:
   • Kafka (VM2)
   • Database Consumer (VM3)
   • ML Inference Engine (VM4)
   • IoT Simulator (VM1)
2. Monitor logs on each VM for operation status.
3. Use Kafka console consumer to verify message flow:
   bin/kafka-console-consumer.sh --bootstrap-server localhost:9092 --topic team21 --from-beginning

4. Query the PostgreSQL database to verify data insertion and updates.
