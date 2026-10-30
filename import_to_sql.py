import pandas as pd          #Import the Python libraries
from pathlib import Path
from sqlalchemy import create_engine, URL
from getpass import getpass
import re

csv_folder = Path(r"D:\VScode\TMDB_csv_cleaned_file.csv")  #Specify the CSV folder


connection_url = URL.create(                    #Connect to MySQL
drivername="mysql+pymysql",
username="root",
password="Vijay@0204",
host="localhost",
port=3306,
database="movie_analysis"
)

engine = create_engine(connection_url)

csv_files = list(csv_folder.glob("*.csv"))          #Find all CSV files

print(f"CSV files found: {len(csv_files)}")

if not csv_files:                                   #Check whether files exist
 print("No CSV files found. Check the folder path.")

else:
    try:
        with engine.connect() as connection:
            print("MySQL connection successful!")
        for file in csv_files:                          #Read each CSV file
            print(f"\nreading:{file.name}")
            df = pd.read_csv(file)
            table_name = re.sub(                       #Create a valid SQL table name - This section converts a filename into a table name.
                r"[^a-zA-Z0-9_]",
                "_",
                file.stem
            ).lower()

            df.to_sql(                             #Import the data into MySQL
                name=table_name,                       #	Specifies the destination table name
                con=engine,                            #Specifies the database connection interface
                if_exists="replace",                    #Replaces an existing table with the same name
                index=False                           #Prevents Pandas from adding its DataFrame index as an extra SQL column
            )

            print(f"Imported {len(df)} rows into table '{table_name}'")  #Print the import result

        print("\nAll CSV files imported successfully!")
    except Exception as error:                    #Handle errors and close the engine
        print("\nImport failed:")                 
        print(error)

    finally:
        engine.dispose()
  