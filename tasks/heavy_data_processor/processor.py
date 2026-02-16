import csv
import sys


def process_data(file_path):
    """
    BUG: This reads the entire file into a list of dictionaries.
    For a 10GB file, this will crash with MemoryError.
    TASK: Refactor this to use a generator or streaming approach
    to calculate the average 'price' without loading everything.
    """
    total_price = 0
    count = 0

    with open(file_path, mode="r") as f:
        reader = csv.DictReader(f)
        data = list(reader)  # THE PROBLEM IS HERE

        for row in data:
            total_price += float(row["price"])
            count += 1

    return total_price / count if count > 0 else 0


if __name__ == "__main__":
    if len(sys.argv) > 1:
        print(f"Average: {process_data(sys.argv[1])}")
