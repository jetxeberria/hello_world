import numpy as np

def extract_columns_by_index(data, columns):
    return data[:, columns]

def extract_columns_indexes(data, columns):
    try:
        print(f"columns: {columns}")
        col_index = [np.where(data[0] == colname)[0][0] for colname in columns]
        print(f"col_index: {col_index}")
    except ValueError as exc:
        col_index = []
        print("ValueError. ", exc)
    return col_index

def are_int(sequence):
    return all([is_int(value) for value in sequence])

def is_int(value):
    try:
        int(value)
    except ValueError:
        return False
    else:
        return True

def swap_keys_and_values(d):
    new = {}
    for k,v in d.items():
        if v not in new:
            new[v] = set()
        new[v].add(k)
    return new