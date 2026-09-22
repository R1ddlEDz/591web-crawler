from sqlalchemy import create_engine, Column, Integer, String, Float, func, text
from sqlalchemy.orm import declarative_base, sessionmaker
from urllib.parse import quote_plus


safe_password = quote_plus(password)
engine = create_engine(f"postgresql+psycopg2://{db_user}:{db_safe_password}@localhost:5433/{database_name}")

with engine.connect() as connection:
    result = connection.execute(text("SELECT column_name, data_type, character_maximum_length, is_nullable, column_default FROM information_schema.columns WHERE table_name = 'listing' ORDER BY ordinal_position;"))
    for row in result:
        print(row)
    
