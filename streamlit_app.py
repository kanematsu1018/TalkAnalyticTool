import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
# import matplotlib
import speech_recognition as sr
import pydub
import os
import json
import math
import time
import sys
from PIL import Image
from janome.analyzer import Analyzer
from janome.charfilter import *
# from apiclient.discovery import build
from wordcloud import WordCloud
from pytube import YouTube,Playlist

import youtube_dl

# from apiclient.errors import HttpError
# from oauth2client.tools import argparser
# if os.name == 'nt':
#     import _locale
#     _locale._getdefaultlocale_backup = _locale._getdefaultlocale
#     _locale._getdefaultlocale = (lambda *args: (_locale._getdefaultlocale_backup()[0], 'UTF-8'))
r = sr.Recognizer()

WAV_FILE_NAME = "tmp/tmp"
DIVISION_UNIT_SEC = 30
FONT_PATH = "ipaexg.ttf"

# Youtube API用のキーを入力
with open('secret.json') as f:
    secret = json.load(f)


st.title('トーク密度診断(仮)')


# 変数初期化
mp3_file = None
input_data = ""
is_input_file = False


# # フォントを全て読み込み
# fonts = set([f.name for f in matplotlib.font_manager.fontManager.ttflist])
 
# # 描画領域のサイズ調整
# plt.figure(figsize=(10,len(fonts)/4))
 
# # フォントの表示
# for i, font in enumerate(fonts):
#     st.write(plt.text(0, i, f"日本語：{font}", fontname=font))


# ラジオボタンの表示
selected_item = st.radio('音声ファイルの入力形式を指定してください',
                            ['Youtube', 'mp3'])
if selected_item == 'Youtube':
    input_data = st.text_input('URLを入力してください')
else:
    mp3_file = st.file_uploader("MP3ファイルアップロード", type="mp3")
    if mp3_file != None:
        tmp_sound = pydub.AudioSegment.from_mp3(mp3_file.name)
        tmp_sound.export(WAV_FILE_NAME + ".mp3", format="mp3")



# テキストデータ入力

def my_hook(d):
    if d['status'] == 'downloading':
        # st.write("downloading "+ str(math.floor(float(d['downloaded_bytes'])/float(d['total_bytes'])*100))+"%")
        dl_bar.progress(math.floor(float(d['downloaded_bytes'])/float(d['total_bytes'])*100))
    if d['status'] == 'finished':
        filename=d['filename']
        st.write(filename)


if input_data  != "":

    dl_bar = None
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl':  WAV_FILE_NAME + '.%(ext)s',
        'quiet': True,
        'progress_hooks': [my_hook],
        'postprocessors': [
            {'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192'},
            {'key': 'FFmpegMetadata'},
        ],
    }

    dl_bar = st.progress(0)

    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        ydl.download(sys.argv[1:])

    info_dict = ydl.extract_info(input_data, download=True)

    mp3_file_name = WAV_FILE_NAME + '.mp3' 
    is_input_file = True


# 音声解析クラス
class AudioAnalytic:
    
    noun_word_list = None
    filler_word_list = None
    verb_word_list = None
    adject_wort_list = None
    all_word_list = None
    noun_num = 0
    filler_num = 0
    verb_num = 0
    adject_num = 0
    all_num = 0
    other_num = 0

    def get_word_str(self, analytic_text):
        from janome.tokenizer import Tokenizer
        import re
    
        t = Tokenizer()
        tokens = t.tokenize(analytic_text)
        noun_word_list = []
        filler_word_list = []
        verb_word_list = []
        adject_word_list = []
        all_word_list = []

        for token in tokens:
            token_list = token.part_of_speech.split(",")
            all_word_list.append(token.surface)
            if token_list[0] == "フィラー" and token_list[1] != "非自立":
                filler_word_list.append(token.surface)
            if token_list[0] == "名詞" and token_list[1] != "非自立":
                noun_word_list.append(token.surface)
            if token_list[0] == "動詞" and token_list[1] != "非自立":
                verb_word_list.append(token.surface)
            if token_list[0] == "形容詞" and token_list[1] != "非自立":
                adject_word_list.append(token.surface)

        self.noun_word_list = " " . join(noun_word_list)
        self.noun_num = len(noun_word_list)
        self.verb_word_list = " " . join(verb_word_list)
        self.verb_num = len(verb_word_list)
        self.adject_word_list = " " . join(adject_word_list)
        self.adject_num = len(adject_word_list)
        self.filler_word_list = " " . join(filler_word_list)
        self.filler_num = len(filler_word_list)
        self.all_word_list = " " . join(all_word_list)
        self.all_num = len(all_word_list)
        self.other_num = self.all_num - self.noun_num - self.verb_num - self.adject_num - self.filler_num


# mp3を読み込ませた後の処理
if mp3_file  != None:
    is_input_file = True
    mp3_file_name = WAV_FILE_NAME + ".mp3"
    # mp3_file_name = mp3_file.name


if is_input_file == True:
    # st.write(mp3_file_name)
    latest_iteration = st.empty()
    bar = st.progress(0)
    text = ""

    # 指定したファイル名のWAVファイルに変換して出力
    sound = pydub.AudioSegment.from_mp3(mp3_file_name)

    # ファイルを分割
    file_num = math.ceil(sound.duration_seconds / DIVISION_UNIT_SEC)

    # st.write(file_num)

    col1, col2 = st.columns(2)
    audio_analytic = AudioAnalytic()

    label = [
        "Noun 名詞",
        "Verv 動詞",
        "abject 形容詞",
        "filler フィラー",
        "other その他"
    ]


    for i in range(file_num):
        # mp3ファイルを切り出す
        tmp_sound = sound[i * (DIVISION_UNIT_SEC * 1000): (i + 1) * (DIVISION_UNIT_SEC * 1000)]
        tmp_file_name = WAV_FILE_NAME + str(i) + '.wav'
        
        # wav形式へ変換する
        tmp_sound.export(tmp_file_name, format="wav")

        # wavファイルの音声解析
        with sr.AudioFile(tmp_file_name) as source:
            audio = r.record(source)
        tmp_text = r.recognize_google(audio, language='ja-JP')

        #wavファイル削除
        os.remove(tmp_file_name)

        # プログレスバー処理
        status_num = math.floor((100 / file_num) * (i+1))
        latest_iteration.text(f'{status_num}％')
        bar.progress(status_num)

        # 出来上がった分割データからワードクラウドを作成する
        audio_analytic.get_word_str(tmp_text)
        tmp_word = audio_analytic.noun_word_list
        tmp_wordcloud = WordCloud(font_path=FONT_PATH,max_font_size=40).generate(tmp_word)
        png_file_name = "tmp/sample.png"
        tmp_wordcloud.to_file(png_file_name)
        image = Image.open(png_file_name)

        with col1:
            st.image(image, caption='Word Cloud', use_column_width=True)
        with col2:
            plt.clf()
            pie_chart = np.array([
                audio_analytic.noun_num,
                audio_analytic.verb_num,
                audio_analytic.adject_num,
                audio_analytic.filler_num,
                audio_analytic.other_num
            ])
            plt.pie(pie_chart, counterclock=False, startangle=90)
            plt.legend(label, fontsize=12, loc='lower right', prop={"family":"DejaVu Sans"})
            plt_file_name = "tmp/plt.png"
            plt.savefig(plt_file_name)
            plt_image = Image.open(plt_file_name)
            plt_resize = plt_image.resize((400,200))
            st.image(plt_resize, caption='円グラフ', use_column_width=True)


        text += tmp_text


    # st.write(text)


    st.write('解析完了！')

    # 最終データからワードクラウドを作成する
    audio_analytic.get_word_str(text)
    word = audio_analytic.noun_word_list
    wordcloud = WordCloud(font_path=FONT_PATH,max_font_size=40).generate(word)
    wordcloud.to_file("sample.png")
    image = Image.open('sample.png')
    st.image(image, caption='Word Cloud', use_column_width=True)

    plt.clf()
    pie_chart = np.array([
        audio_analytic.noun_num,
        audio_analytic.verb_num,
        audio_analytic.adject_num,
        audio_analytic.filler_num,
        audio_analytic.other_num
    ])
    plt.pie(pie_chart, counterclock=False, startangle=90)
    plt.legend(label, fontsize=12, loc='lower right', prop={"family":"DejaVu Sans"})
    plt_file_name = "plt.png"
    plt.savefig(plt_file_name)
    plt_image = Image.open(plt_file_name)
    plt_resize = plt_image.resize((400,200))
    st.image(plt_resize, caption='円グラフ', use_column_width=True)

    


    # この後に フィラーの解析処理を行う




DEVELOPER_KEY = secret['KEY']
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"

#def youtube_search(options):
# APIの認証
# youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION,developerKey=DEVELOPER_KEY)

# q = 'Python'
# max_results = 50

# response = youtube.search().list(
#     q=q,
#     part="id,snippet",
#     maxResults=max_results
# ).execute()

 


# 入力したテキストデータを判定



 # Youtube AIzaSyANw4flpUMprt0814xKv8evWlslZ2cN80Q