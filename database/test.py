import pandas as pd
from fuzzywuzzy import process

def find_unmatched_names(file_path, column1, column2, threshold=80):
    df = pd.read_csv(file_path)
    
    if column1 not in df.columns or column2 not in df.columns:
        raise ValueError("One or both specified columns do not exist in the CSV file.")
    
    names1 = df[column1].dropna().astype(str).tolist()
    names2 = df[column2].dropna().astype(str).tolist()
    
    unmatched_names = []
    
    for name in names1:
        match, score = process.extractOne(name, names2, score_cutoff=threshold) or (None, 0)
        if score < threshold:
            unmatched_names.append(name)
    
    return unmatched_names

# Example usage
file_path = "new1.csv"  # Change this to your CSV file name
column1 = "NAME1"  # Change this to your first column name
column2 = "NAME2"  # Change this to your second column name

unmatched = find_unmatched_names(file_path, column1, column2)
print("Names not found in the other column:")
print(unmatched)
