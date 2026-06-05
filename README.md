# Smart City Analyzer 🏙️

Smart City Analyzer is an end-to-end data engineering pipeline designed to analyze urban data (specifically in Alexandria, Egypt). It collects data from various sources, processes it, and loads it into a Data Warehouse to provide insights into real estate property suitability based on surrounding businesses, demographics, and services.

## 🚀 Project Architecture

The project is divided into several phases:

### 1. Phase 1: Scraping & Data Ingestion (Bronze Layer)
- Collects raw data from various sources (Aqarmap for real estate, OpenStreetMap for businesses/services).
- Utilizes **Apache Kafka** for streaming data between producers and consumers.
- Stores the raw, ingested data into a **PostgreSQL** database (Bronze Layer).
- Managed using Docker Compose.

### 2. Phase 2: Transformation & Processing (Silver to Gold Layer)
- Uses **Apache Spark (PySpark)** to process and clean the raw data.
- Calculates distances between properties and nearby services (using vectorized Haversine formula for performance).
- Computes suitability scores for different business types in various areas.
- Filters out irrelevant data (e.g., standardizing Education Centers) and ensures proper categorization.
- Exports the refined data into Gold Tables (Excel formats ready for DWH).

### 3. Phase 3: Data Warehouse (SQL Server)
- Loads the Gold Tables into a **Microsoft SQL Server** Data Warehouse.
- Implements a **Star Schema** with the following tables:
  - **Dimensions:** `Dim_Area`, `Dim_Business_Type`, `Dim_Property`
  - **Facts:** `Fact_Area_Business_Score`, `Fact_Property_Suitability`
- Enforces Primary Key (PK) and Foreign Key (FK) constraints for data integrity.

### 4. Orchestration
- The entire workflow can be orchestrated using **Apache Airflow** to ensure automated, scheduled, and reliable execution.

## 🛠️ Tech Stack
- **Languages:** Python, SQL
- **Data Processing:** PySpark, Pandas, NumPy
- **Message Broker:** Apache Kafka
- **Databases:** PostgreSQL (Bronze), SQL Server (Data Warehouse)
- **Containerization:** Docker, Docker Compose
- **Orchestration:** Apache Airflow

## 📊 Output Insights
The final Data Warehouse allows analysts and decision-makers to query:
- The suitability score of a specific property for opening a new business (e.g., a Cafe or an Education Center).
- Market saturation and competitor counts within 500m/1km radii.
- Area demographics (population) and average rental prices.

## ⚙️ How to Run
1. Start the Kafka brokers and PostgreSQL database using Docker Compose in `phase1_scraping`.
2. Run the scraping pipelines to populate the Bronze DB.
3. Execute the PySpark transformation script (`run_phase2.py`) in `phase2_transform` to generate Gold Tables.
4. Run the load script (`run_load.py` & `apply_and_verify.py`) in `phase3_dwh` to move the data into SQL Server and apply constraints.
