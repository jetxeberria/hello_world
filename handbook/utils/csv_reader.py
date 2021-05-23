import csv

class CsvReader():

    def __init__(self):
        self.contents = None
        self.selection = None

    def load_csv(self, filename):
        contents = []
        with open(filename) as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            for row in csv_reader:
                contents.append(row)
        self.contents = contents
        return self

    def select_columns_by_name(self, columns):
        data = np.array(self.contents)
        if not are_int(columns):
            columns = extract_columns_indexes(data, columns)
        self.selection = extract_columns_by_index(data, columns)
        return self