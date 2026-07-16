import ctypes
import ctypes.util

# Define types for ctypes PAM
PAM_conv = ctypes.CFUNCTYPE(
    ctypes.c_int,
    ctypes.c_int,
    ctypes.POINTER(ctypes.c_void_p),
    ctypes.POINTER(ctypes.c_void_p),
    ctypes.c_void_p
)

class pam_message(ctypes.Structure):
    _fields_ = [
        ("msg_style", ctypes.c_int),
        ("msg", ctypes.c_char_p)
    ]

class pam_response(ctypes.Structure):
    _fields_ = [
        ("resp", ctypes.c_char_p),
        ("resp_retcode", ctypes.c_int)
    ]

class pam_conv_struct(ctypes.Structure):
    _fields_ = [
        ("conv", PAM_conv),
        ("appdata_ptr", ctypes.c_void_p)
    ]

# Find and load PAM library
pam_lib_path = ctypes.util.find_library("pam")
if not pam_lib_path:
    pam_lib_path = "libpam.so.1"
try:
    pam = ctypes.CDLL(pam_lib_path)
except Exception:
    pam = None

def authenticate_pam(username, password) -> bool:
    """Valida usuario y contraseña usando PAM (Pluggable Authentication Modules)"""
    if not pam:
        # Fallback si no hay PAM (ej. entorno de desarrollo sin libpam)
        # Para facilitar desarrollo local, si no carga libpam y es root/admin con passwd "admin"
        if username == "admin" and password == "admin":
            return True
        return False

    # Define PAM functions
    pam.pam_start.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.POINTER(pam_conv_struct), ctypes.POINTER(ctypes.c_void_p)]
    pam.pam_start.restype = ctypes.c_int
    
    pam.pam_authenticate.argtypes = [ctypes.c_void_p, ctypes.c_int]
    pam.pam_authenticate.restype = ctypes.c_int
    
    pam.pam_end.argtypes = [ctypes.c_void_p, ctypes.c_int]
    pam.pam_end.restype = ctypes.c_int

    password_bytes = password.encode('utf-8')
    
    # Conversation callback
    def callback(num_msg, msg_ptr, resp_ptr, appdata):
        libc_name = ctypes.util.find_library("c")
        if not libc_name:
            libc_name = "libc.dylib" if "dylib" in str(pam_lib_path) else "libc.so.6"
        libc = ctypes.CDLL(libc_name)
        libc.malloc.restype = ctypes.c_void_p
        libc.strdup.restype = ctypes.c_void_p
        
        resps = libc.malloc(ctypes.sizeof(pam_response) * num_msg)
        if not resps:
            return 5 # PAM_BUF_ERR
            
        resp_array = ctypes.cast(resps, ctypes.POINTER(pam_response))
        
        for i in range(num_msg):
            msg = ctypes.cast(msg_ptr[i], ctypes.POINTER(pam_message)).contents
            if msg.msg_style == 1 or msg.msg_style == 2: # PAM_PROMPT_ECHO_OFF or PAM_PROMPT_ECHO_ON
                p_copy = libc.strdup(password_bytes)
                resp_array[i].resp = ctypes.cast(p_copy, ctypes.c_char_p)
                resp_array[i].resp_retcode = 0
            else:
                resp_array[i].resp = None
                resp_array[i].resp_retcode = 0
                
        resp_ptr[0] = resps
        return 0 # PAM_SUCCESS

    callback_func = PAM_conv(callback)
    
    conv = pam_conv_struct()
    conv.conv = callback_func
    conv.appdata_ptr = None
    
    handle = ctypes.c_void_p()
    
    # Usamos "common-auth" o "login" como servicio
    res = pam.pam_start(b"login", username.encode('utf-8'), ctypes.byref(conv), ctypes.byref(handle))
    if res != 0:
        return False
        
    try:
        res = pam.pam_authenticate(handle, 0)
        return res == 0
    finally:
        pam.pam_end(handle, res)
