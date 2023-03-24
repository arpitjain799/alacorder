import cython
import pyximport; pyximport.install(pyimport=True)
from alacorder import alac

if __name__ == "__main__":
	alac.loadgui()