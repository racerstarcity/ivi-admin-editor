import subprocess, time, os, sys

CHROME = r"C:\Program Files (x86)\Google\Chrome\chrome.exe"

print("Killing Chrome...")
os.system("taskkill /f /im chrome.exe 2>nul")
time.sleep(2)

print("Starting Chrome with remote debugging...")
proc = subprocess.Popen([CHROME, "--remote-debugging-port=9222"],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

# Wait for port
for i in range(15):
    time.sleep(1)
    try:
        import urllib.request, json
        r = urllib.request.urlopen("http://localhost:9222/json", timeout=2)
        tabs = json.loads(r.read())
        print(f"\nPort 9222 OK. {len(tabs)} tab(s):")
        for t in tabs:
            print(f"  {t['title'][:50]} → {t['url'][:70]}")
        print("\nGo to your admin page in Chrome, then come back here and press Enter.")
        input()
        # Read again
        r = urllib.request.urlopen("http://localhost:9222/json", timeout=2)
        tabs = json.loads(r.read())
        for t in tabs:
            url = t.get("url", "")
            print(f"\nPage: {t['title']}")
            print(f"URL: {url}")
        break
    except Exception as e:
        print(f".", end="", flush=True)
else:
    print("\nFailed. Manually start Chrome with:")
    print('  chrome.exe --remote-debugging-port=9222')
    sys.exit(1)

input("\nPress Enter to get FULL HTML...")

import urllib.request, json
r = urllib.request.urlopen("http://localhost:9222/json", timeout=2)
tabs = json.loads(r.read())
for t in tabs:
    url = t.get("url", "")
    if "ivi" in url.lower() or "admin" in url.lower() or not url:
        continue
    print(f"\nReading: {t['title']}")
    ws_url = t["webSocketDebuggerUrl"]
    import websocket
    ws = websocket.create_connection(ws_url, timeout=10)
    ws.send(json.dumps({"id": 1, "method": "Runtime.evaluate", "params": {
        "expression": "document.body.innerText",
        "returnByValue": True
    }}))
    resp = json.loads(ws.recv())
    text = resp.get("result", {}).get("result", {}).get("value", "")
    print(text[:15000])
    ws.close()

print("\nDone")
