import csv
import numpy as np

from utils import CsvReader
from utils import Plotter

def main():
    # reader = CsvReader()
    # filename = "/media/jetxeberria/linux_storage/data/documents/besteak/egunean_behin_results.txt.csv"
    # target_columns = ["Aciertos", "time", "Puntuacion"]
    # contents = reader.raw_read(filename)
    # cols_index, subcontents = reader.extract_columns(contents, target_columns)
    # print(f"cols_index: {cols_index}")
    # print(f"subcontents: {subcontents}")
    reader = CsvReader()

    reader.load_csv("/media/jetxeberria/linux_storage/data/documents/besteak/egunean_behin_results.csv")
    reader.select_columns_by_name(["Aciertos", "time", "Puntuacion"])

    plotter = Plotter()

    x = np.array(reader.selection[1:, 0], dtype=np.float)
    y = np.array(reader.selection[1:, 1], dtype=np.float)
    z = np.array(reader.selection[1:, 2], dtype=np.float)
    print(type(reader.selection))
    print(x)
    print(y)
    print(z)
    title = "Egunean Behin lehiaketa puntuatioiak"
    plot = plotter.plot_3d(x, y, z, suptitle=title, xlabel="Aciertos", ylabel="Tiempo [min]", zlabel="Puntuacion")
    outpath = "/media/jetxeberria/linux_storage/data/documents/besteak/egunean_behin_graph.png"
    # save_plot(plot, outpath)

    print(reader.selection)




if __name__ == "__main__":
    main()