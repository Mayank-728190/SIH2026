import os
import re
from pathlib import Path

import pandas as pd
from pymongo import MongoClient
from pymongo.errors import BulkWriteError


# ============================================================
# CONFIGURATION
# ============================================================

# Root folder
CSV_FOLDER = Path(
    r"C:\Users\user\Downloads\SIH26\Personal Finance Agent\Personal Finance Agent\Synthetic Data"
)

DATABASE_NAME = "aml_database"
BATCH_SIZE = 5000


# ============================================================
# MONGODB
# ============================================================

# IMPORTANT:
# Do NOT hard-code your Atlas password in the script.
#
# PowerShell:
# $env:MONGO_URI="mongodb+srv://USERNAME:PASSWORD@cluster.mongodb.net/?appName=SIH2026"
#
# Then run:
# python upload_csv_mongodb.py

MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://mayank091827_db_user:L8Iemg7rp3BKsgIG@sih2026.o47fmf8.mongodb.net/?appName=SIH2026")


# ============================================================
# CHECK FOLDER
# ============================================================

print("=" * 70)
print("AML CSV -> MongoDB Importer")
print("=" * 70)

print(f"\nChecking folder:")
print(CSV_FOLDER)

print(f"\nExists: {CSV_FOLDER.exists()}")
print(f"Is directory: {CSV_FOLDER.is_dir()}")

if not CSV_FOLDER.exists():

    print("\nERROR: Folder does not exist.")

    # Show the parent directories to help identify the problem
    parent = CSV_FOLDER.parent

    print("\nParent folder:")
    print(parent)

    if parent.exists():

        print("\nItems found in parent folder:")

        for item in parent.iterdir():
            print("  ", item)

    raise FileNotFoundError(
        f"\nFolder not found:\n{CSV_FOLDER}\n\n"
        "Check the path carefully."
    )

if not CSV_FOLDER.is_dir():

    raise NotADirectoryError(
        f"This path exists but is not a directory:\n{CSV_FOLDER}"
    )


# ============================================================
# FIND CSV FILES RECURSIVELY
# ============================================================

print("\nSearching for CSV files...")

csv_files = list(CSV_FOLDER.rglob("*.csv"))

# Also handle .CSV / mixed case on Windows explicitly
csv_files += [
    p for p in CSV_FOLDER.rglob("*")
    if p.is_file() and p.suffix.lower() == ".csv"
]

# Remove duplicates
csv_files = sorted(set(csv_files))


if not csv_files:

    print("\nNo CSV files found.")

    print("\nFiles/directories immediately inside the folder:")

    for item in CSV_FOLDER.iterdir():
        print(
            f"  {'[DIR]' if item.is_dir() else '[FILE]'} "
            f"{item.name}"
        )

    raise FileNotFoundError(
        "\nNo CSV files were found inside the specified folder."
    )


print(f"\nFound {len(csv_files)} CSV file(s):")

for file in csv_files:

    size_mb = file.stat().st_size / (1024 * 1024)

    print(
        f"  {file.relative_to(CSV_FOLDER)} "
        f"({size_mb:.2f} MB)"
    )


# ============================================================
# CONNECT TO MONGODB
# ============================================================

print("\nConnecting to MongoDB...")

client = MongoClient(
    MONGO_URI,
    serverSelectionTimeoutMS=10000
)

# Test connection
client.admin.command("ping")

print("MongoDB connection successful.")

db = client[DATABASE_NAME]

print(f"Database: {DATABASE_NAME}")


# ============================================================
# COLLECTION NAME
# ============================================================

def clean_collection_name(filename):

    name = Path(filename).stem

    # Replace spaces/special characters
    name = re.sub(
        r"[^a-zA-Z0-9_]",
        "_",
        name
    )

    name = name.lower()

    if not name:
        name = "collection"

    return name[:120]


# ============================================================
# CLEAN VALUES
# ============================================================

def clean_value(value):

    # Handle pandas NaN / NaT
    if pd.isna(value):
        return None

    # Convert numpy scalar → Python scalar
    if hasattr(value, "item"):

        try:
            return value.item()

        except Exception:
            pass

    return value


# ============================================================
# IMPORT ONE CSV
# ============================================================

def import_csv(csv_path):

    filename = csv_path.name

    collection_name = clean_collection_name(filename)

    collection = db[collection_name]

    print("\n")
    print("=" * 70)
    print(f"FILE        : {filename}")
    print(f"COLLECTION  : {collection_name}")
    print("=" * 70)

    total_inserted = 0
    total_rows = 0

    try:

        # Read in chunks
        for chunk_number, chunk in enumerate(
            pd.read_csv(
                csv_path,
                chunksize=BATCH_SIZE,
                low_memory=False
            ),
            start=1
        ):

            total_rows += len(chunk)

            # Convert NaN → None
            chunk = chunk.astype(object)
            chunk = chunk.where(
                pd.notnull(chunk),
                None
            )

            records = []

            for row in chunk.to_dict(
                orient="records"
            ):

                cleaned_row = {
                    str(key): clean_value(value)
                    for key, value in row.items()
                }

                records.append(cleaned_row)

            if not records:
                continue

            try:

                result = collection.insert_many(
                    records,
                    ordered=False
                )

                inserted = len(
                    result.inserted_ids
                )

                total_inserted += inserted

                print(
                    f"Chunk {chunk_number:>4} | "
                    f"Rows: {len(records):>6,} | "
                    f"Inserted: {inserted:>6,} | "
                    f"Total: {total_inserted:>10,}"
                )

            except BulkWriteError as e:

                inserted = e.details.get(
                    "nInserted",
                    0
                )

                total_inserted += inserted

                print(
                    f"Chunk {chunk_number:>4} | "
                    f"Inserted: {inserted:>6,} | "
                    f"Bulk write warning"
                )

    except Exception as e:

        print(
            f"\nERROR processing {filename}"
        )

        print(
            f"Reason: {e}"
        )

        return False

    print("\nCompleted:")
    print(f"  File           : {filename}")
    print(f"  Rows processed : {total_rows:,}")
    print(f"  Inserted       : {total_inserted:,}")

    return True


# ============================================================
# IMPORT ALL FILES
# ============================================================

successful = 0
failed = 0

for csv_file in csv_files:

    success = import_csv(csv_file)

    if success:
        successful += 1
    else:
        failed += 1


# ============================================================
# DATABASE SUMMARY
# ============================================================

print("\n")
print("=" * 70)
print("IMPORT COMPLETE")
print("=" * 70)

print(f"Database       : {DATABASE_NAME}")
print(f"Files found    : {len(csv_files)}")
print(f"Successful     : {successful}")
print(f"Failed         : {failed}")

print("\nMongoDB collections:")

collections = sorted(
    db.list_collection_names()
)

for collection_name in collections:

    count = db[
        collection_name
    ].count_documents({})

    print(
        f"  {collection_name:<40}"
        f"{count:>12,} documents"
    )


client.close()

print("\nMongoDB connection closed.")
print("Done.")