# -*- coding: utf-8 -*-
"""Автозагрузчик расширения IVI Admin Fill в Chrome/Edge/Яндекс/Opera/Firefox.

Запускает браузер с профилем, подключается по CDP pipe
(Extensions.loadUnpacked) и загружает расширение из папки ivi_ext.

Chrome/Edge/Opera — отдельный профиль (расширение сохраняется).
Яндекс — основной профиль браузера; т.к. Яндекс отключает unpacked
расширения при обычном старте (disable_reasons=[1]), loader при каждом
запуске делает uninstall + loadUnpacked, что даёт enabled=True в сессии.
Firefox — не Chromium (нет CDP), расширение загружается через web-ext
(`npx --yes web-ext run`), профиль создаётся отдельный.

Коды выхода:
  0 — расширение загружено (или браузер уже запущен с расширением)
  1 — браузер не найден / ошибка загрузки
"""

import ctypes
import ctypes.wintypes as wt
import json
import os
import re
import subprocess
import sys
import time


# ---------------------------------------------------------------- WinAPI ---

CreatePipe = ctypes.windll.kernel32.CreatePipe
CreatePipe.argtypes = [ctypes.POINTER(wt.HANDLE), ctypes.POINTER(wt.HANDLE),
                       ctypes.c_void_p, wt.DWORD]
CreatePipe.restype = wt.BOOL


class SECURITY_ATTRIBUTES(ctypes.Structure):
    _fields_ = [("nLength", wt.DWORD),
                ("lpSecurityDescriptor", wt.LPVOID),
                ("bInheritHandle", wt.BOOL)]


InitializeProcThreadAttributeList = ctypes.windll.kernel32.InitializeProcThreadAttributeList
InitializeProcThreadAttributeList.argtypes = [wt.LPVOID, wt.DWORD, wt.DWORD, ctypes.POINTER(ctypes.c_size_t)]
InitializeProcThreadAttributeList.restype = wt.BOOL

UpdateProcThreadAttribute = ctypes.windll.kernel32.UpdateProcThreadAttribute
UpdateProcThreadAttribute.argtypes = [wt.LPVOID, wt.DWORD, ctypes.c_ulonglong,
                                      wt.LPVOID, ctypes.c_size_t,
                                      wt.LPVOID, ctypes.POINTER(ctypes.c_size_t)]
UpdateProcThreadAttribute.restype = wt.BOOL

DeleteProcThreadAttributeList = ctypes.windll.kernel32.DeleteProcThreadAttributeList
DeleteProcThreadAttributeList.argtypes = [wt.LPVOID]


class STARTUPINFO(ctypes.Structure):
    _fields_ = [("cb", wt.DWORD), ("lpReserved", wt.LPWSTR), ("lpDesktop", wt.LPWSTR),
                ("lpTitle", wt.LPWSTR), ("dwX", wt.DWORD), ("dwY", wt.DWORD),
                ("dwXSize", wt.DWORD), ("dwYSize", wt.DWORD), ("dwXCountChars", wt.DWORD),
                ("dwYCountChars", wt.DWORD), ("dwFillAttribute", wt.DWORD),
                ("dwFlags", wt.DWORD), ("wShowWindow", wt.WORD), ("cbReserved2", wt.WORD),
                ("lpReserved2", ctypes.POINTER(wt.BYTE)), ("hStdInput", wt.HANDLE),
                ("hStdOutput", wt.HANDLE), ("hStdError", wt.HANDLE)]


class STARTUPINFOEX(ctypes.Structure):
    _fields_ = [("StartupInfo", STARTUPINFO), ("lpAttributeList", wt.LPVOID)]


class PROCESS_INFORMATION(ctypes.Structure):
    _fields_ = [("hProcess", wt.HANDLE), ("hThread", wt.HANDLE),
                ("dwProcessId", wt.DWORD), ("dwThreadId", wt.DWORD)]


CreateProcessW = ctypes.windll.kernel32.CreateProcessW
CreateProcessW.argtypes = [wt.LPCWSTR, wt.LPWSTR, ctypes.c_void_p, ctypes.c_void_p,
                           wt.BOOL, wt.DWORD, wt.LPVOID, wt.LPCWSTR,
                           ctypes.POINTER(STARTUPINFOEX), ctypes.POINTER(PROCESS_INFORMATION)]
CreateProcessW.restype = wt.BOOL

WriteFile = ctypes.windll.kernel32.WriteFile
WriteFile.argtypes = [wt.HANDLE, wt.LPVOID, wt.DWORD, ctypes.POINTER(wt.DWORD), wt.LPVOID]
WriteFile.restype = wt.BOOL

ReadFile = ctypes.windll.kernel32.ReadFile
ReadFile.argtypes = [wt.HANDLE, wt.LPVOID, wt.DWORD, ctypes.POINTER(wt.DWORD), wt.LPVOID]
ReadFile.restype = wt.BOOL

PeekNamedPipe = ctypes.windll.kernel32.PeekNamedPipe
PeekNamedPipe.argtypes = [wt.HANDLE, wt.LPVOID, wt.DWORD,
                          ctypes.POINTER(wt.DWORD), ctypes.POINTER(wt.DWORD),
                          ctypes.POINTER(wt.DWORD)]
PeekNamedPipe.restype = wt.BOOL

CloseHandle = ctypes.windll.kernel32.CloseHandle
CloseHandle.argtypes = [wt.HANDLE]

PROC_THREAD_ATTRIBUTE_HANDLE_LIST = 0x00020002
STARTF_USESTDHANDLES = 0x00000100
STD_INPUT_HANDLE = -10
STD_OUTPUT_HANDLE = -11
STD_ERROR_HANDLE = -12


def _nul_handle():
    import msvcrt
    fd = os.open(os.devnull, os.O_RDWR)
    handle = msvcrt.get_osfhandle(fd)
    return wt.HANDLE(handle)


def create_inheritable_pipe(peer_read):
    """Создать анонимный канал. Возвращает (наш_хэндл, хэндл_для_Chrome).
    peer_read=True  — Chrome читает, мы пишем.
    peer_read=False — Chrome пишет, мы читаем."""
    sa = SECURITY_ATTRIBUTES()
    sa.nLength = ctypes.sizeof(SECURITY_ATTRIBUTES)
    sa.bInheritHandle = True
    read_h = wt.HANDLE()
    write_h = wt.HANDLE()
    if not CreatePipe(ctypes.byref(read_h), ctypes.byref(write_h), ctypes.byref(sa), 0):
        raise OSError("CreatePipe failed")
    if peer_read:
        return int(write_h.value), int(read_h.value)
    return int(read_h.value), int(write_h.value)


def launch_browser_with_pipe(browser, profile_dir, io_pipes, url=None):
    args = [
        browser,
        "--remote-debugging-pipe",
        "--enable-unsafe-extension-debugging",
        "--no-first-run",
        "--no-default-browser-check",
        f"--user-data-dir={profile_dir}",
        "--window-size=1280,800",
        f"--remote-debugging-io-pipes={io_pipes}",
    ]
    if url:
        args.append(url)
    cmd = subprocess.list2cmdline(args)

    size = ctypes.c_size_t(0)
    InitializeProcThreadAttributeList(None, 1, 0, ctypes.byref(size))
    attr_list = ctypes.create_string_buffer(size.value)
    if not InitializeProcThreadAttributeList(ctypes.byref(attr_list), 1, 0, ctypes.byref(size)):
        raise OSError("InitializeProcThreadAttributeList failed")

    read_val, write_val = io_pipes.split(",")
    handle_array = (wt.HANDLE * 2)(wt.HANDLE(int(read_val)), wt.HANDLE(int(write_val)))
    if not UpdateProcThreadAttribute(
            ctypes.byref(attr_list), 0, PROC_THREAD_ATTRIBUTE_HANDLE_LIST,
            ctypes.byref(handle_array), ctypes.sizeof(handle_array), None, None):
        DeleteProcThreadAttributeList(ctypes.byref(attr_list))
        raise OSError("UpdateProcThreadAttribute failed")

    nul = _nul_handle()
    si = STARTUPINFOEX()
    si.StartupInfo.cb = ctypes.sizeof(STARTUPINFOEX)
    si.StartupInfo.dwFlags = STARTF_USESTDHANDLES
    si.StartupInfo.hStdInput = nul
    si.StartupInfo.hStdOutput = nul
    si.StartupInfo.hStdError = nul
    si.lpAttributeList = ctypes.cast(ctypes.byref(attr_list), wt.LPVOID)
    pi = PROCESS_INFORMATION()

    cmd_buf = ctypes.create_unicode_buffer(cmd)
    ok = CreateProcessW(None, cmd_buf, None, None, True, 0, None, None,
                        ctypes.byref(si), ctypes.byref(pi))
    DeleteProcThreadAttributeList(ctypes.byref(attr_list))
    if not ok:
        raise OSError(f"CreateProcessW failed: {ctypes.get_last_error()}")

    CloseHandle(wt.HANDLE(int(read_val)))
    CloseHandle(wt.HANDLE(int(write_val)))

    return {"pid": pi.dwProcessId, "proc_handle": pi.hProcess}


class PipeConn(object):
    def __init__(self, parent_write, parent_read):
        self.parent_write = parent_write
        self.parent_read = parent_read
        self._mid = 0

    def send(self, method, params=None):
        self._mid += 1
        msg = {"id": self._mid, "method": method}
        if params is not None:
            msg["params"] = params
        data = json.dumps(msg).encode("utf-8") + b"\0"
        written = wt.DWORD(0)
        buf = ctypes.create_string_buffer(data)
        if not WriteFile(self.parent_write, buf, len(data), ctypes.byref(written), None):
            raise OSError("WriteFile failed: broken pipe (browser already running?)")

    def read_msg(self, timeout=20):
        buf = b""
        deadline = time.time() + timeout
        while time.time() < deadline:
            avail = wt.DWORD(0)
            if not PeekNamedPipe(self.parent_read, None, 0, None, ctypes.byref(avail), None):
                raise OSError(f"pipe broken ({ctypes.get_last_error()})")
            if avail.value > 0:
                chunk = ctypes.create_string_buffer(min(avail.value, 8192))
                read_n = wt.DWORD(0)
                if not ReadFile(self.parent_read, chunk, len(chunk), ctypes.byref(read_n), None):
                    raise OSError(f"ReadFile failed: {ctypes.get_last_error()}")
                buf += chunk.raw[:read_n.value]
                if b"\0" in buf:
                    return json.loads(buf[:buf.index(b"\0")].decode("utf-8"))
            else:
                time.sleep(0.05)
        raise TimeoutError("no CDP response")

    def call(self, method, params=None, timeout=20):
        mid = self._mid + 1
        self._mid = mid
        msg = {"id": mid, "method": method}
        if params is not None:
            msg["params"] = params
        data = json.dumps(msg).encode("utf-8") + b"\0"
        written = wt.DWORD(0)
        buf = ctypes.create_string_buffer(data)
        if not WriteFile(self.parent_write, buf, len(data), ctypes.byref(written), None):
            raise OSError("WriteFile failed: broken pipe (browser already running?)")
        deadline = time.time() + timeout
        while time.time() < deadline:
            resp = self.read_msg(deadline - time.time() + 0.1)
            if resp.get("id") == mid:
                return resp
        raise TimeoutError(f"no response for {method}")


# ------------------------------------------------------------- поиск браузера ---

def _glob_opera_exe():
    """Найти настоящий opera.exe (лежит в версированной папке)."""
    for root in (r"C:\Program Files\Opera", r"C:\Program Files (x86)\Opera"):
        if os.path.isdir(root):
            for dirpath, _, files in os.walk(root):
                if "opera.exe" in files:
                    return os.path.join(dirpath, "opera.exe")
    return None


def find_browser(which=None):
    candidates = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Edge\Application\msedge.exe"),
        r"C:\Program Files\Yandex\YandexBrowser\Application\browser.exe",
        r"C:\Program Files (x86)\Yandex\YandexBrowser\Application\browser.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Yandex\YandexBrowser\Application\browser.exe"),
        r"C:\Program Files\Opera\launcher.exe",
        r"C:\Program Files (x86)\Opera\launcher.exe",
        r"C:\Program Files\Mozilla Firefox\firefox.exe",
        r"C:\Program Files (x86)\Mozilla Firefox\firefox.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Mozilla Firefox\firefox.exe"),
    ]
    opera_exe = _glob_opera_exe()
    if opera_exe:
        candidates.insert(0, opera_exe)
    aliases = {
        "chrome": lambda p: "chrome.exe" in p.lower(),
        "edge": lambda p: "msedge.exe" in p.lower(),
        "yandex": lambda p: "browser.exe" in p.lower() and "yandex" in p.lower(),
        "opera": lambda p: "opera.exe" in p.lower() or
                           ("launcher.exe" in p.lower() and "opera" in p.lower()),
        "firefox": lambda p: "firefox.exe" in p.lower(),
    }
    if which:
        if os.path.isfile(which):
            return which
        match = aliases.get(which.lower())
        if match:
            for p in candidates:
                if os.path.isfile(p) and match(p):
                    return p
        return None
    for p in candidates:
        if os.path.isfile(p):
            return p
    return None


def log(msg):
    try:
        log_dir = os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")),
                               "IVI Admin Editor")
        os.makedirs(log_dir, exist_ok=True)
        with open(os.path.join(log_dir, "loader.log"), "a", encoding="utf-8") as f:
            f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n")
    except Exception:
        pass
    print(msg)


def show_error(msg):
    log(msg)
    if getattr(sys, "frozen", False):
        ctypes.windll.user32.MessageBoxW(None, msg, "IVI Admin Editor", 0x10)


def is_profile_running(profile_dir):
    """Браузер уже запущен с нашим профилем?"""
    names = "Name='chrome.exe' or Name='msedge.exe' or Name='browser.exe' or Name='opera.exe'"
    esc = re.escape(profile_dir)
    ps = (f"(Get-CimInstance Win32_Process -Filter \"{names}\") | "
          f"Where-Object {{ $_.CommandLine -match '{esc}' }} | "
          f"Select-Object -First 1")
    try:
        r = subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                           capture_output=True, text=True, timeout=15)
    except Exception:
        return False
    return bool(r.stdout and r.stdout.strip())


def yandex_default_profile():
    """Путь к основному профилю Яндекса."""
    return os.path.expandvars(r"%LOCALAPPDATA%\Yandex\YandexBrowser\User Data")


def yandex_is_running(profile_dir):
    """Яндекс уже запущен с данным профилем (в любой форме)."""
    names = "Name='browser.exe'"
    esc = re.escape(profile_dir)
    ps = (f"(Get-CimInstance Win32_Process -Filter \"{names}\") | "
          f"Where-Object {{ $_.CommandLine -match '{esc}' }} | "
          f"Select-Object -First 1")
    try:
        r = subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                           capture_output=True, text=True, timeout=15)
    except Exception:
        return False
    return bool(r.stdout and r.stdout.strip())


def yandex_running_with_pipe(profile_dir):
    """Яндекс запущен с данным профилем И c CDP-pipe (т.е. через наш loader,
    расширение уже загружено)."""
    names = "Name='browser.exe'"
    esc = re.escape(profile_dir)
    ps = (f"(Get-CimInstance Win32_Process -Filter \"{names}\") | "
          f"Where-Object {{ $_.CommandLine -match '{esc}' -and "
          f"$_.CommandLine -match 'remote-debugging-io-pipes' }} | "
          f"Select-Object -First 1")
    try:
        r = subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                           capture_output=True, text=True, timeout=15)
    except Exception:
        return False
    return bool(r.stdout and r.stdout.strip())


def kill_yandex(profile_dir):
    """Завершить все процессы Яндекса с данным профилем."""
    names = "Name='browser.exe'"
    esc = re.escape(profile_dir)
    ps = (f"Get-CimInstance Win32_Process -Filter \"{names}\" | "
          f"Where-Object {{ $_.CommandLine -match '{esc}' }} | "
          f"ForEach-Object {{ Stop-Process -Id $_.ProcessId -Force }}")
    try:
        subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                       capture_output=True, text=True, timeout=30)
        return True
    except Exception:
        return False


def ensure_extension_enabled(conn, ext_id, ext_path, attempts=3):
    """Убедиться, что расширение загружено и включено.
    Яндекс отключает unpacked расширения (disable_reasons=[1]) при
    обычном старте, поэтому нужен uninstall + loadUnpacked."""
    for attempt in range(attempts):
        ext = conn.call("Extensions.getExtensions", timeout=15)
        for e in ext.get("result", {}).get("extensions", []):
            if e.get("path", "").lower().replace("\\", "/") == ext_path.lower().replace("\\", "/"):
                if e.get("enabled"):
                    return True
                # расширение есть, но отключено — переустановим
                try:
                    conn.call("Extensions.uninstall", {"id": e.get("id")}, timeout=10)
                except Exception:
                    pass
                break
        res = conn.call("Extensions.loadUnpacked", {"path": ext_path}, timeout=15)
        if "error" in res:
            continue
        # ждём, пока расширение активируется
        time.sleep(1.5)
        ext2 = conn.call("Extensions.getExtensions", timeout=15)
        for e in ext2.get("result", {}).get("extensions", []):
            if e.get("path", "").lower().replace("\\", "/") == ext_path.lower().replace("\\", "/"):
                if e.get("enabled"):
                    return True
    return False


def launch_firefox(browser, ext_path, profile_dir, url=None):
    """Firefox не поддерживает CDP-pipe — расширение грузим через web-ext.

    Используется установленный web-ext либо `npx --yes web-ext` (скачает
    при первом запуске). Профиль создаётся отдельный, аддон ставится как
    временный и переустанавливается при каждом запуске."""
    import shutil
    cmd = None
    web_ext = shutil.which("web-ext")
    if web_ext:
        cmd = [web_ext]
    else:
        npx = shutil.which("npx")
        if npx:
            cmd = [npx, "--yes", "web-ext"]
    if not cmd:
        show_error("Для Firefox нужен web-ext (Node.js/npm). Установите:\n"
                   "npm install -g web-ext\n\n"
                   "Или запустите Firefox и загрузите расширение вручную:\n"
                   "about:debugging#/runtime/this-firefox → Load Temporary Add-on → "
                   f"{ext_path}\\manifest.json")
        return 1
    run_args = cmd + [
        "run",
        "--source-dir", ext_path,
        "--firefox", browser,
        "--firefox-profile", profile_dir,
        "--profile-create-if-missing",
        "--keep-profile-changes",
        "--no-input",
    ]
    if url:
        run_args += ["--start-url", url]
    log("Запуск Firefox: " + subprocess.list2cmdline(run_args))
    try:
        subprocess.Popen(run_args, creationflags=subprocess.CREATE_NO_WINDOW)
        return 0
    except Exception as e:
        show_error(f"Не удалось запустить Firefox: {e}")
        return 1


def main():
    base_dir = os.path.dirname(sys.executable) if getattr(sys, "frozen", False) else os.path.dirname(os.path.abspath(__file__))
    ext_path = os.path.join(base_dir, "ivi_ext")
    profile_dir = os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")),
                               "IVI Admin Editor", "chrome_profile")

    url = None
    which = None
    for arg in sys.argv[1:]:
        if arg.lower().startswith(("http://", "https://")):
            url = arg
        elif arg.lower().startswith("--browser="):
            which = arg.split("=", 1)[1].strip()
        elif arg.lower() in ("chrome", "edge", "yandex", "opera", "firefox"):
            which = arg.lower()

    browser = find_browser(which)
    if not browser:
        show_error("Браузер Chrome/Edge/Яндекс/Opera/Firefox не найден.")
        return 1
    if not os.path.isdir(ext_path):
        show_error(f"Папка расширения не найдена: {ext_path}")
        return 1

    bname = os.path.basename(browser).lower()
    is_yandex = bool(which and "yandex" in which.lower()) or "browser.exe" in bname
    is_firefox = "firefox.exe" in bname or bool(which and "firefox" in which.lower())
    is_opera = "opera.exe" in bname or ("launcher.exe" in bname and "opera" in browser.lower())

    if is_yandex:
        profile_dir = yandex_default_profile()
    elif is_opera:
        profile_dir = os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")),
                                   "IVI Admin Editor", "opera_profile")

    if is_firefox:
        if url is None:
            url = "https://b2b.ivi.ru"
        os.makedirs(profile_dir, exist_ok=True)
        log(f"Firefox: браузер={browser}, профиль={profile_dir}")
        return launch_firefox(browser, ext_path, profile_dir, url)

    os.makedirs(profile_dir, exist_ok=True)
    log(f"Запуск: браузер={browser}, профиль={profile_dir}")

    if is_profile_running(profile_dir):
        log("Браузер уже запущен с профилем IVI — расширение уже загружено.")
        return 0

    if is_yandex and yandex_running_with_pipe(profile_dir):
        log("Яндекс уже запущен с pipe — расширение уже загружено.")
        return 0

    # Яндекс: если профиль занят обычным экземпляром (без CDP-pipe),
    # pipe-запуск не сработает — нужно закрыть существующий браузер.
    if is_yandex and yandex_is_running(profile_dir):
        log("Яндекс уже запущен без pipe — закрываю для перезапуска с расширением.")
        kill_yandex(profile_dir)
        time.sleep(2)

    parent_write, chrome_read = create_inheritable_pipe(peer_read=True)
    parent_read, chrome_write = create_inheritable_pipe(peer_read=False)

    # URL для открытия: аргумент командной строки, для Яндекс/Opera — b2b.ivi.ru
    if url is None and (is_yandex or is_opera):
        url = "https://b2b.ivi.ru"

    try:
        conn_holder = launch_browser_with_pipe(browser, profile_dir,
                                               f"{chrome_read},{chrome_write}", url)
    except OSError as e:
        show_error(f"Не удалось запустить браузер: {e}")
        return 1

    conn = PipeConn(wt.HANDLE(parent_write), wt.HANDLE(parent_read))

    try:
        # ждём готовности браузера
        r = None
        for i in range(20):
            try:
                r = conn.call("Target.getTargets", timeout=2)
                log(f"getTargets ok (попытка {i + 1})")
                break
            except OSError:
                # pipe оборвался — команда ушла в уже запущенный экземпляр
                log("Браузер уже запущен с профилем IVI — расширение уже загружено.")
                return 0
            except TimeoutError:
                log(f"getTargets таймаут (попытка {i + 1})")
                time.sleep(0.5)
        if r is None:
            log("Браузер не ответил. Возможно, он уже запущен с этим профилем — расширение уже загружено.")
            return 0

        # уже загружено?
        ext = conn.call("Extensions.getExtensions")
        for e in ext.get("result", {}).get("extensions", []):
            if e.get("path", "").lower().replace("\\", "/") == ext_path.lower().replace("\\", "/"):
                if e.get("enabled"):
                    log("Расширение уже загружено и включено.")
                    return 0
                # для Яндекса unpacked расширение может быть отключено —
                # переустановим через ensure_extension_enabled ниже.
                log("Расширение найдено, но отключено — переустанавливаю.")

        ok = ensure_extension_enabled(conn, None, ext_path)
        if not ok:
            show_error("Не удалось включить расширение IVI Admin Fill "
                       "(Яндекс отключает unpacked-расширения).")
            return 1
        log("Расширение IVI Admin Fill активно.")
        return 0
    finally:
        try:
            CloseHandle(wt.HANDLE(parent_write))
            CloseHandle(wt.HANDLE(parent_read))
        except Exception:
            pass


if __name__ == "__main__":
    sys.exit(main())
