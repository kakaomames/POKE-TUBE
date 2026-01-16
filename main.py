import json
import requests
import urllib.parse
import time
import datetime
import random
import subprocess
import os
from cache import cache


API_KEY = "AIzaSyCfLrK2FPzEZllvwhjmugZ8Bwvzp6GRVpU"  # 取得したAPIキーをここに入れる
max_api_wait_time = 3
max_time = 10
apis = ["https://invidious.jing.rocks"]
url = requests.get(r'https://raw.githubusercontent.com/mochidukiyukimi/yuki-youtube-instance/main/instance.txt').text.rstrip()
version = "1.0"

os.system("chmod 777 ./yukiverify")

apichannels = []
apicomments = []
[[apichannels.append(i),apicomments.append(i)] for i in apis]
class APItimeoutError(Exception):
    pass

def is_json(json_str):
    result = False
    try:
        json.loads(json_str)
        result = True
    except json.JSONDecodeError as jde:
        pass
    return result

def apirequest(url):
    global apis
    global max_time
    starttime = time.time()
    for api in apis:
        if  time.time() - starttime >= max_time -1:
            break
        try:
            res = requests.get(api+url,timeout=max_api_wait_time)
            if res.status_code == 200 and is_json(res.text):
                return res.text
            else:
                print(f"エラー:{api}")
                apis.append(api)
                apis.remove(api)
        except:
            print(f"タイムアウト:{api}")
            apis.append(api)
            apis.remove(api)
    raise APItimeoutError("APIがタイムアウトしました")

def apichannelrequest(url):
    global apichannels
    global max_time
    starttime = time.time()
    for api in apichannels:
        if  time.time() - starttime >= max_time -1:
            break
        try:
            res = requests.get(api+url,timeout=max_api_wait_time)
            if res.status_code == 200 and is_json(res.text):
                return res.text
            else:
                print(f"エラー:{api}")
                apichannels.append(api)
                apichannels.remove(api)
        except:
            print(f"タイムアウト:{api}")
            apichannels.append(api)
            apichannels.remove(api)
    raise APItimeoutError("APIがタイムアウトしました")

def apicommentsrequest(url):
    global apicomments
    global max_time
    starttime = time.time()
    for api in apicomments:
        if  time.time() - starttime >= max_time -1:
            break
        try:
            res = requests.get(api+url,timeout=max_api_wait_time)
            if res.status_code == 200 and is_json(res.text):
                return res.text
            else:
                print(f"エラー:{api}")
                apicomments.append(api)
                apicomments.remove(api)
        except:
            print(f"タイムアウト:{api}")
            apicomments.append(api)
            apicomments.remove(api)
    raise APItimeoutError("APIがタイムアウトしました")

def check_cokie(cookie):
    if cookie == "True":
        return True
    return False

def get_verifycode():
    try:
        result = subprocess.run(["./yukiverify"], encoding='utf-8', stdout=subprocess.PIPE)
        hashed_password = result.stdout.strip()
        return hashed_password
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
        return None





from fastapi import FastAPI, Depends
from fastapi import Response,Cookie,Request
from fastapi.responses import HTMLResponse,PlainTextResponse
from fastapi.responses import RedirectResponse as redirect
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Union


app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
app.mount("/css", StaticFiles(directory="./css"), name="static")
app.mount("/blog", StaticFiles(directory="./blog", html=True), name="static")
app.add_middleware(GZipMiddleware, minimum_size=1000)

from fastapi.templating import Jinja2Templates
template = Jinja2Templates(directory='templates').TemplateResponse


@app.get("/suggest")
def suggest(keyword:str):
    return [i[0] for i in json.loads(requests.get(r"http://www.google.com/complete/search?client=youtube&hl=ja&ds=yt&q="+urllib.parse.quote(keyword)).text[19:-1])[1]]


@app.get("/thumbnail")
def thumbnail(v:str):
    return Response(content = requests.get(fr"https://img.youtube.com/vi/{v}/0.jpg").content,media_type=r"image/jpeg")

@app.get("/bbs",response_class=HTMLResponse)
def view_bbs(request: Request,name: Union[str, None] = "",seed:Union[str,None]="",channel:Union[str,None]="main",verify:Union[str,None]="false",yuki: Union[str] = Cookie(None)):
    if not(check_cokie(yuki)):
        return redirect("/")
    res = HTMLResponse(requests.get(fr"{url}bbs?name={urllib.parse.quote(name)}&seed={urllib.parse.quote(seed)}&channel={urllib.parse.quote(channel)}&verify={urllib.parse.quote(verify)}",cookies={"yuki":"True"}).text)
    return res

@cache(seconds=5)
def bbsapi_cached(verify,channel):
    return requests.get(fr"{url}bbs/api?t={urllib.parse.quote(str(int(time.time()*1000)))}&verify={urllib.parse.quote(verify)}&channel={urllib.parse.quote(channel)}",cookies={"yuki":"True"}).text

@app.get("/bbs/api",response_class=HTMLResponse)
def view_bbs(request: Request,t: str,channel:Union[str,None]="main",verify: Union[str,None] = "false"):
    print(fr"{url}bbs/api?t={urllib.parse.quote(t)}&verify={urllib.parse.quote(verify)}&channel={urllib.parse.quote(channel)}")
    return bbsapi_cached(verify,channel)

@app.get("/bbs/result")
def write_bbs(request: Request,name: str = "",message: str = "",seed:Union[str,None] = "",channel:Union[str,None]="main",verify:Union[str,None]="false",yuki: Union[str] = Cookie(None)):
    if not(check_cokie(yuki)):
        return redirect("/")
    t = requests.get(fr"{url}bbs/result?name={urllib.parse.quote(name)}&message={urllib.parse.quote(message)}&seed={urllib.parse.quote(seed)}&channel={urllib.parse.quote(channel)}&verify={urllib.parse.quote(verify)}&info={urllib.parse.quote(get_info(request))}&serververify={get_verifycode()}",cookies={"yuki":"True"}, allow_redirects=False)
    if t.status_code != 307:
        return HTMLResponse(t.text)
    return redirect(f"/bbs?name={urllib.parse.quote(name)}&seed={urllib.parse.quote(seed)}&channel={urllib.parse.quote(channel)}&verify={urllib.parse.quote(verify)}")

@cache(seconds=30)
def how_cached():
    return requests.get(fr"{url}bbs/how").text

@app.get("/bbs/how",response_class=PlainTextResponse)
def view_commonds(request: Request,yuki: Union[str] = Cookie(None)):
    if not(check_cokie(yuki)):
        return redirect("/")
    return how_cached()

@app.get("/load_instance")
def home():
    global url
    url = requests.get(r'https://raw.githubusercontent.com/mochidukiyukimi/yuki-youtube-instance/main/instance.txt').text.rstrip()


@app.exception_handler(500)
def page(request: Request,__):
    return template("APIwait.html",{"request": request},status_code=500)

@app.exception_handler(APItimeoutError)
def APIwait(request: Request,exception: APItimeoutError):
    return template("APIwait.html",{"request": request},status_code=500)
    
@app.get('/watch', response_class=HTMLResponse)
def video(v: str, response: Response, request: Request):
    videoid = v
    t = get_data(videoid)
    
    return template('video.html', {
        "request": request,
        "videoid": videoid,
        "videourls": t[1],
        "res": t[0],
        "description": t[2],
        "videotitle": t[3],
        "authorid": t[4],
        "authoricon": t[6],
        "author": t[5],
        "proxy": None
    })

import json
import requests
from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import JSONResponse

#¥app = FastAPI()

# カカオマメ隊員が見つけた「勝利の鍵」URL
# keyが含まれているので、これをベースにするよ！
SUCCESS_URL_BASE = "https://youtubei.googleapis.com/youtubei/v1"
YOUTUBE_API_KEY = "AIzaSyAO_FJ2SlqU8Q4STEHLGCilw_Y9_11qcW8"
print(f"system:Using Success Route with Key: {YOUTUBE_API_KEY}")

# --- 勝利の方程式リクエスト関数 ---
def call_youtubei_success_route(endpoint, id):
    # エンドポイントにkeyを付与
    url = f"{SUCCESS_URL_BASE}/{endpoint}?key={YOUTUBE_API_KEY}"
    print(f"target_url:{url}")
    # --- 究極の変装ヘッダーセット ---
    # ショートカット実行時のヘッダーを再現するよ！
    headers = {
        "User-Agent": "BackgroundShortcutRunner/3607.0.2 CFNetwork/3826.500.131 Darwin/24.5.0",
        "Accept": "*/*",
        "Accept-Language": "ja",
        "Content-Type": "application/json",
        "Origin": "https://www.youtube.com",
        "Referer": "https://www.youtube.com/",
        # Vercelであることを隠すために、あえて偽装用のIPヘッダーを上書き試行
        "X-Forwarded-For": "27.121.41.19",
        "X-Real-Ip": "27.121.41.19"
    }
    print(f"headers_used:{headers}")
    id = "I-5GnMD26a4"
    # 成功例に基づいた最小限のコンテキスト
    payload = {"context":{"client":{"clientName":"WEB","clientVersion":"2.20250721.00.00"}},"videoId": id}

    print(f"final_payload:{payload}")

    try:
        print(f"status:Launching POST request to {endpoint}...")
        # 成功例に従い、ヘッダーを極限まで削って突撃！
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        
        status_code = response.status_code
        print(f"status_code:{status_code}")

        if status_code == 200:
            result = response.json()
            # ログには少しだけ中身を出すよ
            if "videoDetails" in result:
                print(f"video_title:{result['videoDetails'].get('title')}")
            return result
        else:
            print(f"error_response:{response.text}")
            return {"error": "YouTubei error", "status": status_code, "detail": response.text}
            
    except Exception as e:
        print(f"exception:{str(e)}")
        return {"error": str(e)}

# --- 統合エンドポイント ---
@app.get("/api/youtubei/")
async def youtubei_api(
    type: str = Query(..., description="video, channel, comment, search, home, 関連"),
    id: str = Query(...),# description="動画IDまたはチャンネルID"), #,
    q: str = Query(None)
):
    print(f"routing_type:{type}")
    
    if type == "video":
        # 動画詳細
        return call_youtubei_success_route("player", id)

    elif type == "channel":
        # チャンネル情報
        return call_youtubei_success_route("browse", {"browseId": id})

    elif type == "search":
        # 検索
        return call_youtubei_success_route("search", {"query": q})

    elif type == "comment" or type == "関連":
        # コメント・関連動画
        return call_youtubei_success_route("next", {"videoId": id})

    elif type == "home":
        # ホーム画面
        return call_youtubei_success_route("browse", {"browseId": "FEwhat_to_watch"})

    else:
        print(f"error:Invalid type {type}")
        raise HTTPException(status_code=400, detail="Invalid type")

if __name__ == "__main__":
    import uvicorn
    print("status:Starting local squad server...")
    uvicorn.run(app, host="0.0.0.0", port=5000)
