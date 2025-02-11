import os
import subprocess  # nosec: B404
import win32crypt  # type: ignore
import codecs

try:
    import winreg as wreg
except ImportError:  # Python 2.7 fallback
    import _winreg as wreg  # type: ignore

from uds.log import logger  # type: ignore
from uds import tools  # type: ignore

thePass = sp['password'].encode('UTF-16LE')  # type: ignore

try:
    password = codecs.encode(
        win32crypt.CryptProtectData(thePass, None, None, None, None, 0x01), 'hex'
    ).decode()
except Exception:
    # logger.info('Cannot encrypt for user, trying for machine')
    password = codecs.encode(
        win32crypt.CryptProtectData(thePass, None, None, None, None, 0x05), 'hex'
    ).decode()

try:
    key = wreg.OpenKey(  # type: ignore
        wreg.HKEY_CURRENT_USER,  # type: ignore
        'Software\\Microsoft\\Terminal Server Client\\LocalDevices',
        0,
        wreg.KEY_SET_VALUE,  # type: ignore
    )
    wreg.SetValueEx(key, sp['ip'], 0, wreg.REG_DWORD, 255)  # type: ignore
    wreg.CloseKey(key)  # type: ignore
except Exception as e:  # nosec: Not really interested in the exception
    # logger.warn('Exception fixing redirection dialog: %s', e)
    pass  # Key does not exists, ok...

# The password must be encoded, to be included in a .rdp file, as 'UTF-16LE' before protecting (CtrpyProtectData) it in order to work with mstsc
theFile = sp['as_file'].format(password=password)  # type: ignore
filename = tools.saveTempFile(theFile)

if sp['optimize_teams'] == True:  # type: ignore
    try:
        # Very basic check for RDP client from Microsoft Store
        h = wreg.OpenKey(wreg.HKEY_CLASSES_ROOT, '.rdp\\OpenWithProgids', 0, wreg.KEY_READ)  # type: ignore
        h.Close()
    except Exception:
        raise Exception('Required Microsoft RDP Client is not found. Please, install it from Microsoft store.')
    # Add .rdp to filename for open with
    os.rename(filename, filename + '.rdp')
    filename = filename + '.rdp'
    os.startfile(filename)  # type: ignore  # nosec
else:
    executable = tools.findApp('mstsc.exe')
    if executable is None:
        raise Exception(
            'Unable to find mstsc.exe. Check that path points to your SYSTEM32 folder'
        )

    subprocess.Popen([executable, filename])  # nosec

tools.addFileToUnlink(filename)
