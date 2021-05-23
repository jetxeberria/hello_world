from matplotlib import pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

class Plotter():

    def __init__(self):
        self.data = None


    def plot_3d(self, x, y, z, **kwargs):
        fig = plt.figure()
        print(kwargs)
        print(kwargs.keys())
        suptitle = kwargs["suptitle"]
        print(type(suptitle))
        print(kwargs["xlabel"])
        print(kwargs["ylabel"])
        ax = fig.add_subplot(projection='3d')
        fig.suptitle(kwargs.pop("suptitle"))
        ax.set_xlabel(kwargs.pop("xlabel"))
        ax.set_ylabel(kwargs.pop("ylabel"))
        ax.set_zlabel(kwargs.pop("zlabel"))
        ax.scatter(x, y, z, **kwargs)
        plt.show()