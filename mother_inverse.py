import os
import sys
import ctypes
import serial
from ik import inv

# Define the DiffDriveStatus struct
class DiffDriveStatus(ctypes.Structure):
    _fields_ = [
        ("x", ctypes.c_float),
        ("y", ctypes.c_float),
        ("heading", ctypes.c_float),
        ("linear", ctypes.c_float),
        ("angular", ctypes.c_float),
    ]


# Define the DiffDriveTwist struct
class DiffDriveTwist(ctypes.Structure):
    _fields_ = [("linear_x", ctypes.c_float), ("angular_z", ctypes.c_float)]


# Define the mother_cmd_msg struct
class mother_cmd_msg(ctypes.Structure):
    _fields_ = [
        ("drive_cmd", DiffDriveTwist),
        ("arm_joint", ctypes.c_float * 3),
        ("adaptive_sus_cmd", ctypes.c_uint8 * 4),
    ]


# Define the mother_status_msg struct
class mother_status_msg(ctypes.Structure):
    _fields_ = [("odom", DiffDriveStatus), ("arm_joint_status", ctypes.c_float * 3), ("timestamp", ctypes.c_uint64)]


# Define the mother_msg struct
class mother_msg(ctypes.Structure):
    _fields_ = [
        ("type", ctypes.c_uint16),
        ("status", mother_status_msg),
        ("cmd", mother_cmd_msg),
        ("info", ctypes.c_char * 100),
        ("crc", ctypes.c_uint32),
    ]


class CobsDecodeStatus(ctypes.c_int):
    COBS_DECODE_OK = 0x00
    COBS_DECODE_NULL_POINTER = 0x01
    COBS_DECODE_OUT_BUFFER_OVERFLOW = 0x02
    COBS_DECODE_ZERO_BYTE_IN_INPUT = 0x04
    COBS_DECODE_INPUT_TOO_SHORT = 0x08


# Define the cobs_decode_result struct
class CobsDecodeResult(ctypes.Structure):
    _fields_ = [("out_len", ctypes.c_size_t), ("status", CobsDecodeStatus)]


# Load the shared library
lib_path = os.path.join(os.path.dirname(__file__), "libcobs.so.2.0.0")
cobs_lib = ctypes.CDLL(lib_path)

# Prototype for cobs_encode
cobs_lib.cobs_encode.argtypes = [
    ctypes.POINTER(ctypes.c_uint8),
    ctypes.c_size_t,
    ctypes.POINTER(ctypes.c_uint8),
]
cobs_lib.cobs_encode.restype = None

# Prototype for cobs_decode
cobs_lib.cobs_decode.argtypes = [
    ctypes.POINTER(ctypes.c_uint8),
    ctypes.c_size_t,
    ctypes.POINTER(ctypes.c_uint8),
    ctypes.c_size_t,
]
cobs_lib.cobs_decode.restype = CobsDecodeResult


def read_from_serial(port):
    try:
        # Open the serial port
        ser = serial.Serial(port, 921600, timeout=5)
        print(f"Opened serial port {port}")
        
        while True:

            # Read 66 bytes from the serial port
            data = ser.read(178)

            # Check if we got enough bytes
            if len(data) == 178:
                # Prepare input and output buffers for decoding
                input_buffer = (ctypes.c_uint8 * len(data)).from_buffer_copy(data)
                output_buffer = (ctypes.c_uint8 * 178)()

                # Call the cobs_decode function
                result = cobs_lib.cobs_decode(
                    output_buffer, 178, input_buffer, len(data) - 1
                )

                if result.status.value == CobsDecodeStatus.COBS_DECODE_OK:
                    decoded_data = bytes(output_buffer[: result.out_len])
                    decoded_msg = ctypes.cast(decoded_data, ctypes.POINTER(mother_msg))

                    if decoded_msg.contents.type == 3:
                        print(
                            "[STATUS] [{}] | Odom: x: {}, y: {}, heading: {}° | Arm Joint Status: {} {} {}".format(
                                decoded_msg.contents.status.timestamp,
                                decoded_msg.contents.status.odom.x,
                                decoded_msg.contents.status.odom.y,
                                decoded_msg.contents.status.odom.heading,
                                decoded_msg.contents.status.arm_joint_status[0],
                                decoded_msg.contents.status.arm_joint_status[1], 
                                decoded_msg.contents.status.arm_joint_status[2] 
                            )
                        )
                        tr=np.array([[1,0,0,0.7495],[0,1,0,0.0131],[0,0,1,-0.1],[0,0,0,1]])
                        pos=np.array([-1.3,0,0.3,1])
                        npos=list(np.dot(tr*pos))[:3]
                        print(f'[CMD] | Arm Joint States: {inv(decoded_msg.contents.status.arm_joint_status,npos)}')
                    if decoded_msg.contents.type == 4:
                        print(f"[ERROR]: {decoded_msg.contents.info.decode()}")
                    if decoded_msg.contents.type == 5:
                        print(f"[INFO]: {decoded_msg.contents.info.decode()}")
                else:
                    print(f"COBS decode error: {result.status.value}")
            else:
                print(f"Read {len(data)} bytes, which is less than expected.")

            # Close the serial port
        ser.close()
    except serial.SerialException as e:
        print(f"Error opening or reading from serial port: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script.py <serial_port>")
        sys.exit(1)

    serial_port = sys.argv[1]
    read_from_serial(serial_port)
