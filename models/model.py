from sqlalchemy import create_engine, Column, Integer, String, Float, func, text
from sqlalchemy.orm import declarative_base, sessionmaker
from urllib.parse import quote_plus
from dotenv import load_dotenv
import os

load_dotenv()
db_name = os.getenv("POSTGRES_DB")
db_user = os.getenv("POSTGRES_USER")
db_password = os.getenv("POSTGRES_PASSWORD")
db_ip = os.getenv("POSTGRES_IP")
encoded_password = quote_plus(db_password)

engine = create_engine(f"postgresql+psycopg2://{db_user}:{encoded_password}@{db_ip}:5433/{db_name}")

with engine.connect() as connection:
    result = connection.execute(text("SELECT column_name, data_type, character_maximum_length, is_nullable, column_default FROM information_schema.columns WHERE table_name = 'listing' ORDER BY ordinal_position;"))
    for row in result:
        print(row)
    
