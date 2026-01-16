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


def get_info(request):
    global version
    return json.dumps([version,os.environ.get('RENDER_EXTERNAL_URL'),str(request.scope["headers"]),str(request.scope['router'])[39:-2]])
    
def get_data(videoid):
    global logs
    
    # YouTube APIを使って動画データを取得
    url = f"https://www.googleapis.com/youtube/v3/videos?id={videoid}&key={API_KEY}&part=snippet"
    response = requests.get(url)
    t = response.json()
    
    # 動画が見つからない場合のエラーチェック
    if "items" not in t or len(t["items"]) == 0:
        return {"error": "Video not found"}
    
    video_data = t["items"][0]["snippet"]
    
    # 必要な情報を抽出
    title = video_data["title"]
    author = video_data["channelTitle"]
    author_id = video_data["channelId"]
    author_thumbnails = video_data.get("thumbnails", {}).get("high", {}).get("url", "")
    
    # 関連動画情報を取得するためにsearch APIを使用
    search_url = f"https://www.googleapis.com/youtube/v3/search?relatedToVideoId={videoid}&key={API_KEY}&type=video&part=snippet"
    search_response = requests.get(search_url)
    search_data = search_response.json()

    recommended_videos = []
    
    # 関連動画の情報をリストに追加
    for item in search_data.get("items", []):
        related_video = item["snippet"]
        recommended_videos.append({
            "id": item["id"]["videoId"],
            "title": related_video["title"],
            "authorId": related_video["channelId"],
            "author": related_video["channelTitle"]
        })
    
    return {
        "title": title,
        "author": author,
        "authorId": author_id,
        "authorThumbnails": author_thumbnails,
        "recommendedVideos": recommended_videos
    }

def get_search(q,page):
    global logs
    t = json.loads(apirequest(fr"api/v1/search?q={urllib.parse.quote(q)}&page={page}&hl=jp"))
    def load_search(i):
        if i["type"] == "video":
            return {"title":i["title"],"id":i["videoId"],"authorId":i["authorId"],"author":i["author"],"length":str(datetime.timedelta(seconds=i["lengthSeconds"])),"published":i["publishedText"],"type":"video"}
        elif i["type"] == "playlist":
            return {"title":i["title"],"id":i["playlistId"],"thumbnail":i["videos"][0]["videoId"],"count":i["videoCount"],"type":"playlist"}
        else:
            if i["authorThumbnails"][-1]["url"].startswith("https"):
                return {"author":i["author"],"id":i["authorId"],"thumbnail":i["authorThumbnails"][-1]["url"],"type":"channel"}
            else:
                return {"author":i["author"],"id":i["authorId"],"thumbnail":r"https://"+i["authorThumbnails"][-1]["url"],"type":"channel"}
    return [load_search(i) for i in t]

def get_channel(channelid):
    global apichannels
    t = json.loads(apichannelrequest(r"api/v1/channels/"+ urllib.parse.quote(channelid)))
    if t["latestVideos"] == []:
        print("APIがチャンネルを返しませんでした")
        apichannels.append(apichannels[0])
        apichannels.remove(apichannels[0])
        raise APItimeoutError("APIがチャンネルを返しませんでした")
    return [[{"title":i["title"],"id":i["videoId"],"authorId":t["authorId"],"author":t["author"],"published":i["publishedText"],"type":"video"} for i in t["latestVideos"]],{"channelname":t["author"],"channelicon":t["authorThumbnails"][-1]["url"],"channelprofile":t["descriptionHtml"]}]

def get_playlist(listid,page):
    t = json.loads(apirequest(r"/api/v1/playlists/"+ urllib.parse.quote(listid)+"?page="+urllib.parse.quote(page)))["videos"]
    return [{"title":i["title"],"id":i["videoId"],"authorId":i["authorId"],"author":i["author"],"type":"video"} for i in t]

def get_comments(videoid):
    t = json.loads(apicommentsrequest(r"api/v1/comments/"+ urllib.parse.quote(videoid)+"?hl=jp"))["comments"]
    return [{"author":i["author"],"authoricon":i["authorThumbnails"][-1]["url"],"authorid":i["authorId"],"body":i["contentHtml"].replace("\n","<br>")} for i in t]

def get_replies(videoid,key):
    t = json.loads(apicommentsrequest(fr"api/v1/comments/{videoid}?hmac_key={key}&hl=jp&format=html"))["contentHtml"]



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





@app.get("/", response_class=HTMLResponse)
def home(response: Response,request: Request,yuki: Union[str] = Cookie(None)):
    if check_cokie(yuki):
        response.set_cookie("yuki","True",max_age=60 * 60 * 24 * 7)
        return template("home.html",{"request": request})
    return redirect("/blog")

@app.route('/watch')
def watch():
    """動画情報を取得してvideolinkを代入"""
    videoid = request.args.get('v')  # ?v=videoidの形式でvideoidを取得
    if not videoid:
        return "Error: videoid not provided", 400
    # 取得した情報をテンプレートに渡してレンダリング
    return render_template(
        'video.html', 
        videoid=videoid,
        videotitle=video_data["title"],
        author=video_data["author"],
        authorid=video_data["authorId"],
        authoricon=video_data["authorThumbnails"],
        description=video_data["description"],
        res=video_data["recommendedVideos"]
        
@app.get("/search", response_class=HTMLResponse,)
def search(q:str,response: Response,request: Request,page:Union[int,None]=1,yuki: Union[str] = Cookie(None),proxy: Union[str] = Cookie(None)):
    if not(check_cokie(yuki)):
        return redirect("/")
    response.set_cookie("yuki","True",max_age=60 * 60 * 24 * 7)
    return template("search.html", {"request": request,"results":get_search(q,page),"word":q,"next":f"/search?q={q}&page={page + 1}","proxy":proxy})

@app.get("/hashtag/{tag}")
def search(tag:str,response: Response,request: Request,page:Union[int,None]=1,yuki: Union[str] = Cookie(None)):
    if not(check_cokie(yuki)):
        return redirect("/")
    return redirect(f"/search?q={tag}")


@app.get("/channel/{channelid}", response_class=HTMLResponse)
def channel(channelid:str,response: Response,request: Request,yuki: Union[str] = Cookie(None),proxy: Union[str] = Cookie(None)):
    if not(check_cokie(yuki)):
        return redirect("/")
    response.set_cookie("yuki","True",max_age=60 * 60 * 24 * 7)
    t = get_channel(channelid)
    return template("channel.html", {"request": request,"results":t[0],"channelname":t[1]["channelname"],"channelicon":t[1]["channelicon"],"channelprofile":t[1]["channelprofile"],"proxy":proxy})

@app.get("/answer", response_class=HTMLResponse)
def set_cokie(q:str):
    if q.count() > 10:
        return "ランダム"
    return "文章"

@app.get("/playlist", response_class=HTMLResponse)
def playlist(list:str,response: Response,request: Request,page:Union[int,None]=1,yuki: Union[str] = Cookie(None),proxy: Union[str] = Cookie(None)):
    if not(check_cokie(yuki)):
        return redirect("/")
    response.set_cookie("yuki","True",max_age=60 * 60 * 24 * 7)
    return template("search.html", {"request": request,"results":get_playlist(list,str(page)),"word":"","next":f"/playlist?list={list}","proxy":proxy})

@app.get("/info", response_class=HTMLResponse)
def viewlist(response: Response,request: Request,yuki: Union[str] = Cookie(None)):
    global apis,apichannels,apicomments
    if not(check_cokie(yuki)):
        return redirect("/")
    response.set_cookie("yuki","True",max_age=60 * 60 * 24 * 7)
    return template("info.html",{"request": request,"Youtube_API":apis[0],"Channel_API":apichannels[0],"Comments_API":apicomments[0]})

@app.get("/suggest")
def suggest(keyword:str):
    return [i[0] for i in json.loads(requests.get(r"http://www.google.com/complete/search?client=youtube&hl=ja&ds=yt&q="+urllib.parse.quote(keyword)).text[19:-1])[1]]

@app.get("/comments")
def comments(request: Request,v:str):
    return template("comments.html",{"request": request,"comments":get_comments(v)})

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
    return template("APIwait.html",{"request": request},status_code=500)get('/watch', response_class=HTMLResponse)
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

from flask import Flask, request, jsonify
import requests
import json


# --- YouTubei 突撃関数 ---
def fetch_youtubei_data(video_id):
    # 1. ターゲットURLの設定
    url = "https://www.youtube.com/youtubei/v1/player"
    print(f"url:{url}")

    # 2. ヘッダーの構築（iOSアプリからのアクセスに擬装）
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
        "Origin": "https://www.youtube.com",
        "Referer": "https://www.youtube.com/"
    }
    print(f"headers:{headers}")

    # 3. ペイロードの構築
    # YouTubeiが要求する最低限のコンテキスト情報だよ！
    payload = {
        "context": {
            "client": {
                "clientName": "IOS",
                "clientVersion": "19.29.1",
                "deviceModel": "iPhone15,2",
                "osName": "iOS",
                "osVersion": "17.0.0",
                "hl": "ja",
                "gl": "JP"
            }
        },
        "videoId": video_id
    }
    print(f"payload:{payload}")

    try:
        # 4. 運命のリクエスト実行
        print(f"status:Fetching data for video_id {video_id}...")
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        
        status_code = response.status_code
        print(f"status_code:{status_code}")

        if status_code == 200:
            result_data = response.json()
            # 取得できたタイトルをデバッグ出力
            video_details = result_data.get("videoDetails", {})
            title = video_details.get("title", "Unknown Title")
            print(f"video_title:{title}")
            return result_data
        else:
            # 失敗した時のボディも確認できるようにしておくよ
            error_body = response.text
            print(f"error_body:{error_body}")
            return {"error": "YouTubei API returned an error", "status": status_code}

    except Exception as e:
        error_msg = str(e)
        print(f"exception:{error_msg}")
        return {"error": error_msg}

# --- 指定されたエンドポイント: /api/video/ ---
@app.route('/api/video/', methods=['GET'])
def get_video_info():
    # クエリパラメータ 'id' から動画IDを取得
    video_id = request.args.get('id')
    print(f"requested_id:{video_id}")
    
    if not video_id:
        print("status:Error - No video ID provided")
        return jsonify({"error": "Missing 'id' parameter"}), 400
    
    # 実行！
    data = fetch_youtubei_data(video_id)
    
    return jsonify(data)

# ローカル環境でのテスト用
if __name__ == '__main__':
    print("status:Starting local Flask server...")
    app.run(port=5000, debug=True)
