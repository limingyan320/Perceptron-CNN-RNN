from pathlib import Path
import aiohttp
import asyncio
import time
import csv


CONCURRENCY = 5
TARGET_COUNT = 1000
REQUEST_TIMEOUT_SECONDS = 10
BASE_URL = "http://192.168.0.56:8080/portal/api/v1/getIdentityCode.do"
OUT_DIR = Path("captchas")
RETRY_COUNT = 2
MANIFEST_PATH = Path("manifest.csv")

def guess_extension(content_type):
    if "png" in content_type:
        return ".png"
    if "gif" in content_type:
        return ".gif"
    if "jpeg" in content_type or "jpg" in content_type:
        return ".jpg"
    return ".bin"

async def fetch_one(session: aiohttp.ClientSession, index: int, sem: asyncio.Semaphore):
    async with sem:
        timestamp = int(time.time() * 1000) + index
        params = {
            "timestamp": timestamp
        }
        
        for attempt in range(1,RETRY_COUNT + 2):
            try:
               async with session.get(BASE_URL,params = params) as resp:
                   body = await resp.read()
                   content_type = resp.headers.get("content-type","")
                   ext = guess_extension(content_type)

                   if resp.status != 200:
                       raise RuntimeError(f"HTTP {resp.status}")
                   if not content_type.lower().startswith("image/"):
                       raise RuntimeError(f"unexpected content-type:{content_type}")
                   
                   filename = f"captchas_{index:04d}{ext}"
                   path = OUT_DIR / Path(filename)
                   path.write_bytes(body)
                   return {
                       "index": index,
                       "ok": "yes",
                       "filename": filename,
                       "status": resp.status,
                       "bytes": len(body),
                       "content_type": content_type,
                       "timestamp": timestamp,
                       "attempt": attempt,
                       "error": "",
                   }

                   
            except Exception as e:
                if attempt > RETRY_COUNT:
                    return {
                        "index": index,
                        "ok": "no",
                        "filename": "",
                        "status": "",
                        "bytes": "",
                        "content_type": "",
                        "timestamp": timestamp,
                        "attempt": attempt,
                        "error": str(e),
                    }
                await asyncio.sleep(0.5 * attempt)

def write_manifest(rows: list[dict]) -> None:
    fieldnames = [
        "index",
        "ok",
        "filename",
        "status",
        "bytes",
        "content_type",
        "timestamp",
        "attempt",
        "error",
    ]
    with MANIFEST_PATH.open("w",newline = "",encoding = "UTF-8") as f:
        writer = csv.DictWriter(f,fieldnames = fieldnames)
        writer.writeheader()
        writer.writerows(rows)


async def main():
    OUT_DIR.mkdir(exist_ok = True)
    sem = asyncio.Semaphore(CONCURRENCY)
    timeout = aiohttp.ClientTimeout(total = REQUEST_TIMEOUT_SECONDS)
    connector = aiohttp.TCPConnector(limit = CONCURRENCY)

    headers = {
        "User-Agent": "captcha-collector-learning/0.3"
    }

    async with aiohttp.ClientSession(
        connector = connector,
        timeout = timeout,
        headers = headers
    ) as session:
        tasks = [
            fetch_one(session,i,sem) for i in range(1, TARGET_COUNT + 1)
        ]
        
        rows = await asyncio.gather(*tasks)


    rows.sort(key = lambda row: row["index"])
    write_manifest(rows)
    
    ok_count = sum(1 for row in rows if row["ok"] == "yes")
    fail_count = len(rows) - ok_count

    print(f"donw: ok = {ok_count},failed = {fail_count}")
    print(f"images:{OUT_DIR}")
    print(f"manifest: {MANIFEST_PATH}")
    






if __name__ == "__main__":
    asyncio.run(main())
