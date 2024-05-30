import numpy as np
import ctypes


def inv(q0,pos):
    so_file = "./invarm.so"

    lib = ctypes.CDLL(so_file)

    lib.invarm.argtypes = (ctypes.POINTER(ctypes.c_double), 
                       ctypes.POINTER(ctypes.c_double), 
                       ctypes.POINTER(ctypes.c_double), 
                       ctypes.POINTER(ctypes.c_int))
    lib.invarm.restype = None

    q0_tmp = np.array(q0, dtype=np.float64)
    pos_tmp = np.array(pos, dtype=np.float64)

    newpos_data = np.zeros(3, dtype=np.float64)
    newpos_size = np.zeros(2, dtype=np.int32)

    q0_tmp_ctypes = q0_tmp.ctypes.data_as(ctypes.POINTER(ctypes.c_double))
    pos_tmp_ctypes = pos_tmp.ctypes.data_as(ctypes.POINTER(ctypes.c_double))
    newpos_data_ctypes = newpos_data.ctypes.data_as(ctypes.POINTER(ctypes.c_double))
    newpos_size_ctypes = newpos_size.ctypes.data_as(ctypes.POINTER(ctypes.c_int))

    lib.invarm(q0_tmp_ctypes, pos_tmp_ctypes, newpos_data_ctypes, newpos_size_ctypes)
    return newpos_data


