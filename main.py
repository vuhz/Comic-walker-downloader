import requests
from io import BytesIO
import numpy as np
import re, os
from sys import argv
from pathlib import Path

def decrypt_image(drm_hash, content):
    if drm_hash is None:
        return BytesIO(content)
    return BytesIO(xor(np.frombuffer(content, dtype=np.uint8), np.array([int(drm_hash[:16][i : i + 2], 16) for i in range(0, len(drm_hash[:16]), 2)],dtype=np.uint8,)).tobytes())

def xor(content, key):
    key_length = len(key)
    result = np.bitwise_xor(
        content, np.tile(key, len(content) // key_length + 1)[: len(content)]
    )
    return result

def sanitize_filename(filename):
    return re.sub(r'[<>:"/\\|?*]', '_', filename)
    
def initDir(baseDir, mangaName, chapterName):
    try:
        Path(f"{baseDir}\\{mangaName}").mkdir(parents=True, exist_ok=True)
        Path(f"{baseDir}\\{mangaName}\\{chapterName}").mkdir(parents=True, exist_ok=True)
    except Exception as e:
        print(e)
    
def getData(url):
    _re = re.search(r"https:\/\/comic-walker\.com\/detail\/(.+)\/episodes\/(.+)\?", url)
    workCode = _re.group(1)
    episode = _re.group(2)

    headers = {
        "Accept": "*/*",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": url,
        "Sec-Ch-Ua": '"Microsoft Edge";v="123", "Not:A-Brand";v="8", "Chromium";v="123"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"Windows"',
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 Edg/123.0.0.0",
        "X-Nextjs-Data": "1",
    }
    _url = f"https://comic-walker.com/_next/data/aQ8BqIS6zBVzAFAJoIJhK/detail/{workCode}/episodes/{episode}.json?workCode={workCode}&episodeCode={episode}&episodeType=first"

    result = requests.get(url=_url, headers=headers)
    return result.json()


def comicWalkerFindAllPages(url):
    data = getData(url)
    return [(x["id"], x["title"]) for x in data["pageProps"]["dehydratedState"]["queries"][0]["state"]["data"]["firstEpisodes"]["result"] if x["isActive"] is True], data["pageProps"]["dehydratedState"]["queries"][0]["state"]["data"]["work"]["title"]

def comicWalkerDownloader(url, baseDir):
    urlList, mangaName = comicWalkerFindAllPages(url)
    rawContentList = [
        (f"https://comic-walker.com/api/contents/viewer?episodeId={x[0]}&imageSizeType=width%3A1284", x[1])
        for x in urlList
    ]

    for i, item in enumerate(rawContentList):
        a = requests.get(
            item[0],
            headers={
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                "Accept-Encoding": "gzip, deflate, br",
                "Accept-Language": "en-US,en;q=0.9",
                "Cache-Control": "no-cache",
                "Pragma": "no-cache",
                "Sec-Ch-Ua": '"Chromium";v="122", "Not(A:Brand";v="24", "Microsoft Edge";v="122"',
                "Sec-Ch-Ua-Mobile": "?0",
                "Sec-Ch-Ua-Platform": '"Windows"',
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Sec-Fetch-User": "?1",
                "Upgrade-Insecure-Requests": "1",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0",
            },
        )

        for i, image in enumerate(a.json()["manuscripts"]):
            initDir(baseDir, mangaName, item[1])
            filename = sanitize_filename(f"image_{str(i + 1).zfill(3)}") + re.search( r'(.+)(\.png|\.webp|\.jpg)', image["drmImageUrl"]).group(2)
            filepath = os.path.join(baseDir, mangaName, item[1], filename)
            file = commicWalkerGetFile(image["drmHash"], image["drmImageUrl"])

            print(f"Downloading chapter {item[1]}, image {str(i + 1).zfill(3)}")
            with open(filepath, "wb") as f:
                f.write(file.read())

def commicWalkerGetFile(drm_hash, url) -> BytesIO:
    content = requests.get(url).content
    decrypted_image = decrypt_image(drm_hash, content)
    return decrypted_image

if __name__ == "__main__":
    if len(argv) < 3:
        print("Usage: main.py <dir> <url>")
    else:
        dir = argv[1]
        url = argv[2]
        comicWalkerDownloader(url, dir)
