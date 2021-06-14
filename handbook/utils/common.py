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
        if is_iterable(v):
            for subv in v:
                if subv not in new:
                    new[subv] = set()
                new[subv].add(k)    
        else:
            if v not in new:
                new[v] = set()
            new[v].add(k)
    return new

def flatten_sequence(seq):
    flatten = []
    if is_iterable(seq):
        for s in seq:
            if is_iterable(s):
                for i in range(len(list(s))):
                    flatten.append(list(s)[i])
            else:
                flatten.append(s)
    return flatten

def is_iterable(item):
    try:
        iterator = iter(item)
    except TypeError:
        return False
    else:
        return True
