# -*- coding: utf-8 -*-
"""
Created on Wed Aug  3 15:49:26 2022

@author: maomao
"""
import geopy.distance
import requests
import json

from flask import Flask, request, abort

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, LocationMessage, TextSendMessage,ImageMessage,ImageSendMessage,LocationSendMessage
)


import requests
app = Flask(__name__)

with open('token.json') as f:
    token = json.load(f)
line_bot_api = LineBotApi(token['api'])
handler = WebhookHandler(token['webhook'])

@app.route("/", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
    #print(body)
    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)

    return 'OK'

@handler.add(MessageEvent, message=LocationMessage)
def handle_message(event):
    lon = event.message.longitude
    lat = event.message.latitude
    msg = {'lat':lat,'lon':lon,'distance':5000}
    res = requests.post('https://car.hccepb.gov.tw/TMap/MapGISData.asmx/LoadNearCarData',json=msg)
    text = json.loads(json.loads(res.text)['d'])
    locMsgList = []
    dist = 99999999999
    for T in text:
        if T['status_name'] != '工作':
            continue
        cLat,cLon,region = T['lat'],T['lon'],T['run']
        distance = geopy.distance.geodesic((lat,lon), (cLat,cLon)).km
        if dist>distance:
            loc = LocationSendMessage(
                title='垃圾車位置',
                address=region,
                latitude=cLat,
                longitude=cLon
            )
            dist = distance
    
    if 'loc' in locals():
        line_bot_api.reply_message(
              event.reply_token,
              loc)
    else:
        line_bot_api.reply_message(
         event.reply_token,
         TextSendMessage(text='哭阿,附近沒有垃圾車啦'))

if __name__ == '__main__':
    from waitress import serve
    serve(app, host="0.0.0.0", port=5000)
    #app.run()
