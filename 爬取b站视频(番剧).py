import sys, requests, re, json, subprocess, os, threading, warnings, time, html
from lxml import etree
from prettytable import PrettyTable
from urllib import request
from icecream import ic

# 路径查找
# ===================================================================================================================================================================================
osPath = os.getcwd() + '/bilibili/'
if not os.path.exists(osPath):
    os.mkdir(osPath)
    os.mkdir(osPath + 'video/')
    os.mkdir(osPath + 'movie/')
    os.mkdir(osPath + 'audio/')

# 数据初始化
# ===================================================================================================================================================================================
# cookie配置
cookie = ""

# 多线程下载配置
maxThreads = int(2)
videoThreadsRatio = int(4)
audioThreadsRatio = int(1)

# 多线程下载
threading.BoundedSemaphore(maxThreads)
dlList = []
global isDl
isDl = None
ogThreadings = 1

sessdata = re.findall('SESSDATA=(.*?);', cookie)[0]
# ic(sessdata)
headersWithSessdata = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36',
    'Referer': 'https://www.bilibili.com/',
    'Origin': 'https://www.bilibili.com/',
    'Cookie': sessdata
}
headersOnlySessdata = {
    'Cookie': sessdata
}
headersOnlyCookie = {
    'Cookie': cookie
}
headersCommon = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36',
    'Referer': 'https://www.bilibili.com/'
}
# ic(type(headers_onlysessdata))

# 防止创建不合法的文件名
# ===================================================================================================================================================================================
def verify(name:str):
    """
    防止创建不合法的文件名

    返回规范的文件名
    """
    name = name.replace(':', '：')
    name = name.replace('<', '《')
    name = name.replace('>', '》')
    name = name.replace('"', '\'\'')
    name = name.replace('*', 'x')
    name = name.replace('?', '？')
    name = name.replace('|', ' ')
    name = name.replace('/', ' ')
    name = name.replace('|', ' ')
    # print(name)
    return name

# 附加功能
# ===================================================================================================================================================================================
def getUserInfo(url:str, headers):
    baseInfo = [['name', '名称'], ['sex', '性别'], ['level', '等级'], ['mid', 'mid'], ['face', '头像地址']]
    otherInfo = []
    text = ''
    data = requests.get(url, headers=headers)
    dataJson = json.loads(data.text)
    # ic(dataJson)
    text += '个人信息\n'
    for k in baseInfo:
        text = text + k[1] + '\t' + str(dataJson['data'][k[0]]) + '\n'
    ic(text)
    
    with open(osPath + 'text.txt', 'w') as txt:
        txt.write(text)


def getHistoryVideo(headers, inputList:list):
    historyMax = 0
    historyViewAt = 0
    def passTo(data):
        typeJudgment(data[0][0], data[0][1:-1] if len(data) > 3 else data[0][1])

    def getHistory(getMax:int=0, getViewAt:int=0):
        data = requests.get("https://api.bilibili.com/x/web-interface/history/cursor?max={}&view_at={}&business=".format(getMax, getViewAt), headers=headers)
        dataJson = json.loads(data.text)
        urlLink = []
        table = PrettyTable()
        table.field_names = ['序号', '标题', '长标题', 'UP主', '标签', 'bvid']
        num = 0
        # historyMax = dataJson['data']['cursor']['max']
        # historyViewAt = dataJson['data']['cursor']['view_at']
        for k in dataJson['data']['list']:
            bvid = k['history']['bvid']
            urlLink.append('https://www.bilibili.com/video/{}/'.format(bvid))
            table.add_row([num, k['title'], k['long_title'], k['author_name'], k['tag_name'], bvid])
            num += 1
        length = len(dataJson['data']['list'])
        print(table)
        chooseMore(passTo, [[urlLink[kChild], inputList] for kChild in range(length)], length=length)

    while True:
        getHistory(historyMax, historyViewAt)
        if input('是否继续获取(确认输入1):') != '1':
            break


def getLatestAnime():
    """
    获取番剧更新情况

    无返回值
    """
    url = 'https://www.bilibili.com/anime'
    data = requests.get(url, headers=headersWithSessdata)
    dataTree = etree.HTML(data.text)
    # ic(data)
    max_k = len(re.findall('timeline-item-title', data.text)) + 1
    info = []
    for k in range(1, max_k):
        anime_name = re.findall('\[\'(.*?)\']', str(dataTree.xpath('//*[@id="app"]/div[3]/div[2]/div[2]/div[1]/div[{}]/div[2]/a/text()'.format(k))))[0]
        anime_update_to = re.findall('\[\'(.*?)\']', str(dataTree.xpath('//*[@id="app"]/div[3]/div[2]/div[2]/div[1]/div[{}]/div[2]/div/div/text()'.format(k))))[0]
        anime_update_time = re.findall('\[\'(.*?)\']', str(dataTree.xpath('//*[@id="app"]/div[3]/div[2]/div[2]/div[1]/div[{}]/div[3]/text()'.format(k))))[0]
        anime_jmp = 'https:' + re.findall('\[\'(.*?)\']', str(dataTree.xpath('//*[@id="app"]/div[3]/div[2]/div[2]/div[1]/div[{}]/div[2]/a/@href'.format(k))))[0]
        # ic(anime_name, anime_update_to, anime_update_time, anime_jmp)
        if anime_name == '[]' or anime_update_to == '[]' or anime_update_time == '[]':
            break
        info.append([anime_name, anime_update_to, anime_update_time, anime_jmp])
    # ic(info)
    table = PrettyTable()
    table.field_names = ['序号', '新番名称', '更新范围', '更新时间', 'URL地址']
    for k in range(len(info)):
        table.add_row([k, info[k][0], info[k][1], info[k][2], info[k][3]])
    print(table, '\n以上是最近更新的新番,请根据编号打出需要下载的内容(格式要求*-*或*,中间以","隔开)')
    choose_range = input('请输入(-1退出):')
    if choose_range == '-1':
        print('已退出')
        return
    length = len(info)
    choose_list = choose_range.split(',')
    for k in range(len(choose_list)):
        k_list = choose_list[k].split('-')
        # ic(k_list)
        if len(k_list) == 1:
            if int(k_list[0]) < length:
                getBangumiData(info[int(k_list[0])][3], headers=headersOnlyCookie)
        elif len(k_list) == 2:
            for num in range(int(k_list[0]), int(k_list[1]) + 1):
                if num < length:
                    getBangumiData(info[num][3], headers=headersOnlyCookie)
        else:
            print('出现了错误!')
            return

def getTimezoneData():
    """
    获取关注列表UP主动态情况
    
    无返回值
    """
    url = 'https://api.bilibili.com/x/polymer/web-dynamic/v1/feed/all?timezone_offset=-480&type=all&page=1&features=itemOpusStyle'
    data = requests.get(url, headers=headersOnlyCookie)
    timezone_data = json.loads(data.text)
    info = PrettyTable()
    info.field_names = ['序号', '标题', 'URL地址']
    # ic(timezone_data['data']['items'][1])
    # ic(timezone_data['data']['items'][k]['modules']['module_author']['name'], timezone_data['data']['items'][k]['modules']['module_dynamic']['major']['archive']['title'])
    for k in range(len(timezone_data['data']['items'])):
        title = timezone_data['data']['items'][1]['modules']['module_dynamic']['major']['archive']['title']
        UP = timezone_data['data']['items'][k]['modules']['module_author']['name']
        url = 'https:' + timezone_data['data']['items'][k]['modules']['module_author']['jump_url']
        info.add_row(title, UP, url)
    print('您关注列表的UP主发布了以下动态!\n', info)

def getUpdateData():
    """
    获取关注列表UP主更新情况

    无返回值
    """
    url = 'https://api.bilibili.com/x/polymer/web-dynamic/v1/portal'
    data = requests.get(url, headers=headersOnlyCookie)
    updatedata = json.loads(data.text)
    updateinfo = []
    for k in range(len(updatedata['data']['up_list'])):
        updateinfo.append([updatedata['data']['up_list'][k]['uname'], updatedata['data']['up_list'][k]['has_update'], ''])
    # ic(dynamicdata, d+ynamicinfo)
    print('您关注的以下UP主更新了!')
    for k in range(0, len(updateinfo)):
        if updateinfo[k][1] == True:
            print(updateinfo[k][0])

def getDanmaku(url:str, path:str):
    # ic(url)
    data = requests.get(url)
    with open(path + '.xml', 'wb') as xml:
        xml.write(data.content)
    cmd = f'danmaku2ass "{path}.xml"'
    subprocess.run(cmd, shell=True)
    os.remove(path + '.xml')


# 其他
# ===================================================================================================================================================================================
def chooseMore(func, *send:list, length:int, **kwds):
    chooseWhat = input('请输入(-1退出):').replace(' ', '')
    if chooseWhat == '-1':
        print('已退出')
        return
    chooseList = chooseWhat.split(',')
    for k in range(len(chooseList)):
        kList = chooseList[k].split('-')
        if len(kList) == 1:
            if 'all' in kList:
                for num in range(length):
                    func(list(singleList[num] for singleList in send))
            elif int(kList[0]) < length:
                func([singleList[int(kList[0])] for singleList in send])
            else:
                print('超出可下载范围!')
        elif len(kList) == 2:
            for num in range(int(kList[0]), int(kList[1]) + 1):
                if num < length:
                    func(list(k[num] for k in send))
                else:
                    print('超出可下载范围!')
        else:
            print('出现了错误!')
            return
    print('已成功加载至下载队列!')

def Input(message, inputList:list, defaultJudgement:str=None):
    if inputList == [] or inputList == None:
        return input(message) if defaultJudgement == None else input(message) == str(defaultJudgement)
    else:
        for k in inputList:
            if k == 'simple' or k == 'noInput':
                return True
        else:
            return input(message) if defaultJudgement == None else input(message) == str(defaultJudgement)


# 类型判断
# ===================================================================================================================================================================================
def typeJudgment(url:str, inputList:list, *args:tuple):
    """
    判断下载类型并调用相对应下载函数

    url: 网页网址
    
    无返回值
    """
    if url == 'history':
        getHistoryVideo(headers=headersOnlyCookie, inputList=inputList)
        return
    typeKwds = re.findall('BV(.*?)$', url)
    if typeKwds != []:
        getDataUrl = 'https://www.bilibili.com/video/BV' + re.findall('^(.*?)\W', typeKwds[0] + '/')[0]
        if getDataUrl[-1] != '/':
            getDataUrl += '/'
        getData(getDataUrl, headers=headersOnlyCookie, inputList=inputList)
    else:
        typeKwds = re.findall('audio/au(.*?)$', url[0])
        if typeKwds != []:
            seed = typeKwds[0].split('?')[0]
            getAudioData(seed=seed, headers=headersOnlyCookie, inputList=inputList)
        else:
            ifDownload = input('由于URL特殊性无法准确判断,取消下载输入-1,下载视频输入0,下载番剧输入1:')
            if ifDownload == '-1':
                print('成功取消下载!')
            elif ifDownload == '0':
                print('开始下载视频')
                getData(url, headers=headersOnlyCookie, inputList=inputList)
            elif ifDownload == '1':
                getBangumiData(url, headers=headersOnlyCookie, inputList=inputList)

# 其他下载功能
# ===================================================================================================================================================================================
def getBangumiData(url:str, headers:dict, inputList:list):
    """
    url: 网页网址
    headers: 请求头格式
    
    无返回值
    """
    def passTo(data):
        downloadData = requests.get(data[0][0], headers=headersOnlyCookie)
        # ic(downloadData.text)
        getInfo(data=downloadData, specialPath=titleBangumi + '/', vTitle=urlFileName[data[0][2]], vTitleInfo='', cid=data[0][1], inputList=inputList)

    data = requests.get(url, headers=headers)
    # ic(data.text)
    titleBangumi = re.findall('<meta property="og:title" content="(.*?)">', data.text)[0]
    # ic(titleBangumi)
    print('下载的番剧是:', titleBangumi)
    # ic(data.text)
    ep = re.findall('<link rel="canonical" href="//www.bilibili.com/bangumi/play/ep(.*?)">', data.text)
    # ic(ep)
    if ep == []:
        epJson = json.loads(re.findall('<script>window.__INITIAL_STATE__=(.*?);(.*?)</script>', data.text)[0][0])
        # ic(epJson)
        ep = epJson['mediaInfo']['episodes'][0]['link']
        ep = re.findall('https://www.bilibili.com/bangumi/play/ep(.*?)\?', ep)
    dataBangumi = requests.get('https://api.bilibili.com/pgc/view/web/season?ep_id=' + ep[0], headers=headers)
    urlFileName = re.findall('"share_copy":"(.*?)"', dataBangumi.text)
    urlLink = re.findall('"link":"(.*?)"', dataBangumi.text)
    cid = re.findall('"cid":(.*?),', data.text)
    badge = re.findall('"badge":"(.*?)"', dataBangumi.text)
    table = PrettyTable()
    table.field_names = ['序号', '标题', '备注']
    for k in range(0, min(len(urlLink), len(urlFileName), len(badge))):
        # ic([k, url_filename[k], badge[k]])
        table.add_row([k, urlFileName[k], badge[k]])
    print(table, '\n请根据编号打出需要下载的内容(格式要求<*-*>或<*>,中间以<,>隔开,需求可增加)')
    if not os.path.exists(osPath + 'video/' + titleBangumi):
        os.mkdir(osPath + 'video/' + titleBangumi)
    chooseMore(passTo, [[urlLink[k], cid[k], k] for k in range(len(urlLink))], length=len(urlLink))

def getCollectionsData(data:list, hasTitle:bool, headers:dict, inputList:list):
    """
    下载合集

    data: 网页页面信息
    path: 下载总文件夹位置
    headers: 请求头格式
    
    无返回值
    """
    def passTo(data):
        downloadData = requests.get(data[0][0], headers=headers)
        getInfo(data=downloadData, specialPath=collectionsName + '/', vTitle=None, vTitleInfo=' ({} - {})'.format(str(data[0][2]), totalLength), cid=data[0][1], inputList=inputList)

    collectionsName = ''
    totalLength = 0
    if hasTitle:
        seasonId = data[0].split('=')[1]
        pageNum = 1
        table = PrettyTable()
        table.field_names = ['序号', '标题', 'bvid']
        urlLink = []
        while True:
            data = requests.get('https://api.bilibili.com/x/polymer/web-space/seasons_archives_list?&season_id={}&sort_reverse=false&page_num={}&page_size=30'.format(seasonId, str(pageNum)), headers=headersOnlyCookie)
            # ic(data.text)
            dataJson = json.loads(data.text)
            collectionsName = dataJson['data']['meta']['name']
            for k in range(len(dataJson['data']['archives'])):
                bvid = dataJson['data']['archives'][k]['bvid']
                urlLink.append('https://www.bilibili.com/video/' + bvid + '/')
                table.add_row([(pageNum - 1 )* 30 + k, dataJson['data']['archives'][k]['title'], bvid])
            if dataJson['data']['page']['total'] <= pageNum * 30:
                break
            else:
                pageNum += 1
        totalLength = str(len(urlLink))
        print(table)
        # print(table, '\n请根据编号打出需要下载的内容(格式要求*-*或*,中间以","隔开)')
        if 'onlyaudio' in inputList:
            if not os.path.exists(osPath + 'audio/' + collectionsName):
                os.mkdir(osPath + 'audio/' + collectionsName)
        elif not os.path.exists(osPath + 'video/' + collectionsName):
            os.mkdir(osPath + 'video/' + collectionsName)
        chooseMore(passTo, [[urlLink[k], None, k + 1] for k in range(int(totalLength))], length=int(totalLength))
    else:
        totalLength = re.findall('<span class="cur-page">\((.*?)\)</span>', data[1].text)[0].split('/')[1]
        collectionsName = re.findall('<title data-vue-meta="true">(.*?)_哔哩哔哩_bilibili</title>', data[1].text)[0]
        view = requests.get('https://api.bilibili.com/x/web-interface/wbi/view?aid=' + re.findall('<script>window.__INITIAL_STATE__={"aid":(.*?),', data[1].text)[0])
        cid = re.findall('"cid":(.*?),', view.text)
        # ic(cid)
        print('范围为1~{}集请打出需要下载的内容(格式要求*-*或*,中间以","隔开)'.format(totalLength))
        if 'onlyaudio' in inputList:
            if not os.path.exists(osPath + 'audio/' + collectionsName):
                os.mkdir(osPath + 'audio/' + collectionsName)
        elif not os.path.exists(osPath + 'video/' + collectionsName):
            os.mkdir(osPath + 'video/' + collectionsName)
        chooseMore(passTo, [['https://www.bilibili.com/video/{}?p={}'.format(data[0], str(k)), cid[k], k] for k in range(int(totalLength) + 1)], length=int(totalLength) + 1)

def getAudioData(seed:str, headers:dict, inputList:list):
    """
    seed: 音频序列编码
    headers: 请求头格式
    
    无返回值
    """
    if inputList == None or not ('onlyaudio' in inputList):
        getDataUrl = 'https://www.bilibili.com/audio/music-service-c/web/url?sid=' + seed
        getInfoUrl = 'https://www.bilibili.com/audio/music-service-c/web/song/info?sid=' + seed
        data = requests.get(getDataUrl, headers=headers)
        info = requests.get(getInfoUrl, headers=headers)
        playDataDict = json.loads(data.text)
        playInfoDict = json.loads(info.text)
        # ic(playdata_dict, playinfo_dict)
        audioUrl = playDataDict['data']['cdns'][0]
        dataInfo = [playInfoDict['data']['title'], playInfoDict['data']['uname']]
        # ic(dataurl, datainfo)
        # request.urlretrieve(dataurl, os_path + '/audio/' + datainfo[0] + '-' + datainfo[1] + '.mp3', callbackfunc)
        vTitle = verify(html.unescape(dataInfo[0] + '-' +  dataInfo[1]))
        print('\n已完成!')
    else:
        audioUrl = seed
        vTitle = headers['vTitle']
    audioFileSize = int(requests.head(audioUrl, headers=headersCommon).headers['Content-Length'])
    dlList.append(queueItem(vTitle=vTitle, namePath=osPath + '/audio/' + vTitle, fakeName=osPath + '/audio/' + vTitle + '_fake', videoUrl=None, audioUrl=audioUrl, videoFileSize=None, audioFileSize=audioFileSize))

# 下载功能
# ===================================================================================================================================================================================
def getData(url:str, headers:dict, inputList:list):
    # ic(headers)
    """
    url: 网页网址
    headers: 请求头格式
    
    无返回值
    """
    # ic(url)
    # url = ''
    data = requests.get(url, headers=headers)
    dataTree = etree.HTML(data.text)
    dataPass = dataTree.xpath('//*[@id="app"]/div[2]/div[2]/div/div[7]/div[1]/div[1]/div[1]/a/@href')
    if dataPass != [] and Input('检测到为合集,是否下载合集(确认输入1):', inputList=inputList, defaultJudgement=1):
        getCollectionsData(dataPass, True, headers, inputList)
    else:
        isCollections = re.findall('multi_page', data.text)
        if isCollections != [] and Input('检测到为合集,是否下载合集(确认输入1):', inputList=inputList, defaultJudgement=1):
            getCollectionsData([re.findall('BV.*?$', url)[0], data], False, headers, inputList)
        else:
            getInfo(data, None, None, None, cid=None, inputList=inputList)
                 

def getInfo(data, specialPath:str, vTitle:str, vTitleInfo:str, cid:str, inputList:list):
    """
    data: 网页页面信息
    
    无返回值
    """
    # ic(data)
    vTitle = re.findall('<title(.*?)>(.*?)</title>', data.text)[0][1] if vTitle == None else vTitle
    vTitle = verify(html.unescape(vTitle if vTitleInfo == None else vTitle + vTitleInfo))
    playInfo = re.findall('__playinfo__=', data.text)
    if playInfo != []:
        playInfo = re.findall('window.__playinfo__=(.*?)</script>', data.text)[0]
    else:
        playInfo = re.findall('window.__INITIAL_STATE__=(.*?);\(function\(\).*?</script>', data.text)[0]
    # ic(vTitle, playinfo)
    print('下载的内容是:', vTitle)
    if Input('输入1确认下载:', inputList=inputList, defaultJudgement=1):
        cid = re.findall('"cid":(.*?),', data.text)[0] if cid == None else cid
        # ic(cid)
        getDict(vTitle, playInfo, specialPath, inputList, kwds={'cid':cid})
    else:
        print('已退出!')
        return

def getDict(vTitle:str, playInfo:str, specialPath:str=None, inputList:list=None, **kwds):
    """
    vTitle: 文件名称(不含下载位置)
    playinfo: 'window.__playinfo__'中的信息(包含视音链接)
    args: 负载信息(元组)
    
    无返回值
    """
    dataJson = json.loads(playInfo)
    len_accept_description = len(dataJson['data']['support_formats'])
    len_url = len(dataJson['data']['dash']['video'])
    accept_description = []
    for k in range(len_accept_description):
        accept_description.append(dataJson['data']['support_formats'][k]['quality'])
    # ic(accept_description)
    # ic(len_url)
    audioUrl = dataJson['data']['dash']['audio'][0]['baseUrl']
    vTitle = verify(html.unescape(vTitle))
    urlTable = []
    if inputList == None or not ('onlyaudio' in inputList):
        table = PrettyTable()
        table.field_names = ['序号', '支持的清晰度']
        for k in range(len(accept_description)):
            # ic(accept_description)
            urlTable.append('')
            urlType = accept_description[k]
            for childK in range(len_url):
                videoHeight = dataJson['data']['dash']['video'][childK]['id']
                # ic(video_height, url_type)
                if videoHeight == urlType:
                    table.add_row([k, dataJson['data']['support_formats'][k]['new_description']])
                    urlTable[k] = dataJson['data']['dash']['video'][childK]['baseUrl']
                    break
        # ic(urlTable)
        chose = Input('{}\n最高清晰度是:{}\n请选择清晰度(单选,-1退出):'.format(table, dataJson['data']['support_formats'][0]['new_description']), inputList=inputList)
        if chose == True:
            for k in range(len(urlTable)):
                if urlTable[k] != '':
                    chose = k
                    break
        else:
            if chose == '-1':
                return
        getVideoData(specialPath + verify(html.unescape(vTitle)) if specialPath != None else vTitle, urlTable[int(chose)] if (inputList == None or not ('onlyaudio' in inputList or 'onlydanmaku' in inputList)) else None, audioUrl if (inputList == None or not ('onlyvideo' in inputList or 'onlydanmaku' in inputList)) else None, 'https://comment.bilibili.com/{}.xml'.format(kwds['kwds']['cid']) if (inputList != None and ('withdanmaku' in inputList or 'onlydanmaku' in inputList)) else None)
    else:
        getAudioData(seed=audioUrl, headers={'vTitle':specialPath + vTitle if specialPath != None else vTitle}, inputList=inputList)

def getVideoData(vTitle:str, videoUrl:str, audioUrl:str, barrageUrl:str):
    """
    vTitle: 文件名称(不含下载位置)
    video_url: 文件中的视频链接
    audio_url: 文件中的音频链接
    
    无返回值
    """
    namePath = osPath + 'video/' + vTitle
    fakeName = namePath + '_fake'
    videoFileSize = int(requests.head(videoUrl, headers=headersCommon).headers['Content-Length']) if videoUrl != None else None
    audioFileSize = int(requests.head(audioUrl, headers=headersCommon).headers['Content-Length']) if audioUrl != None else None
    # ic(video_filesize, audio_filesize)
    dlList.append(queueItem(vTitle=vTitle, namePath=namePath, fakeName=fakeName, videoUrl=videoUrl, audioUrl=audioUrl, barrageUrl=barrageUrl, videoFileSize=videoFileSize, audioFileSize=audioFileSize))

# 多线程下载函数
# ===================================================================================================================================================================================
def download(url:str, name:str, minLeng:int, maxLeng:int):
    """
    url: 下载的链接
    name: 下载的位置 + 下载文件的名称(需要包含后缀)
    {min_leng} - {max_leng}: 下载从{min_leng} - {max_leng}字节段的文件
    
    无返回值
    """
    leng = f'bytes={str(minLeng)}-{str(maxLeng - 1)}' if minLeng != None and maxLeng != None else None
    opener = request.build_opener()
    opener.addheaders = ([('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36'), ('Referer', 'https://www.bilibili.com/'), ('Range', leng) if leng != None else ()])
    request.install_opener(opener)
    request.urlretrieve(url, name)

def startDownload():
    """
    无参数
    以多线程方式运行
    
    无返回值
    """
    while True:
        global isDl
        if isDl == None and dlList != []:
            dlList[0]()
            isDl = dlList.pop(0)
        if isDl != None and len(threading.enumerate()) <= ogThreadings:
            if isDl.videoUrl != None and isDl.videoFileSize != None:
                with open(isDl.fakeName + '.mp4', 'wb') as videoFileData:
                    for k in range(maxThreads * videoThreadsRatio):
                        with open(isDl.fakeName + str(k) + '.mp4', 'rb') as videoFileDataFake:
                            videoFileData.write(videoFileDataFake.read())
                        os.remove(isDl.fakeName + str(k) + '.mp4')
            if isDl.audioUrl != None and isDl.audioFileSize != None:
                with open(isDl.fakeName + '.mp3', 'wb') as audioFileData:
                    for k in range(maxThreads * audioThreadsRatio):
                        with open(isDl.fakeName + str(k) + '.mp3', 'rb') as audioFileDataFake:
                            audioFileData.write(audioFileDataFake.read())
                        os.remove(isDl.fakeName + str(k) + '.mp3')
            if isDl.videoUrl != None and isDl.audioUrl != None:
                cmd = f'ffmpeg -i "{isDl.fakeName}.mp4" -i "{isDl.fakeName}.mp3" -c copy "{isDl.namePath}.mp4"'
                subprocess.run(cmd, shell=True)
                os.remove(isDl.fakeName + '.mp4')
                os.remove(isDl.fakeName + '.mp3')
            elif isDl.videoUrl != None:
                os.rename(isDl.fakeName + '.mp4', isDl.namePath + '.mp4')
            elif isDl.audioUrl != None:
                os.rename(isDl.fakeName + '.mp3', isDl.namePath + '.mp3')
            print(f'已完成下载\'{isDl.vTitle}\'的任务,耗时{(time.time() - isDl.startTime):.2f}s')
            isDl = None
        time.sleep(3)

# 回调信息显示
# ===================================================================================================================================================================================
def callbackfunc(blocknum:int, blocksize:int, totalsize:int):
    # 目前存在亿点点的小bug,会刷屏,建议关闭函数
    percentage = round(blocknum * blocksize / totalsize * 100)
    print('下载进度: {}%: '.format(percentage), '▓' * (percentage // 2))
    sys.stdout.flush()

# 队列构造
# ===================================================================================================================================================================================
class queueItem:
    def __init__(self, vTitle, namePath, fakeName, videoUrl=None, audioUrl=None, barrageUrl=None, videoFileSize=None, audioFileSize=None) -> None:
        self.vTitle = vTitle
        self.namePath = namePath
        self.fakeName = fakeName
        self.videoUrl = videoUrl
        self.audioUrl = audioUrl
        self.barrageUrl = barrageUrl
        self.videoFileSize = videoFileSize if videoFileSize != 18 else None
        self.audioFileSize = audioFileSize if audioFileSize != 18 else None
        '''
        '不带格式的vTitle'
        '不带格式的namePath'
        '不带格式的namePath_fake'
        'url'
        'url'
        整形videoFileSize
        整形audioFileSize
        '''
    
    def __call__(self, *args, **kwds) -> None:
        self.startTime = time.time()
        videoFileLengs = [k * (self.videoFileSize // (maxThreads * videoThreadsRatio)) for k in range(0, maxThreads * videoThreadsRatio) if self.videoUrl != None] + [self.videoFileSize] if self.videoFileSize != None else None
        audioFileLengs = [k * (self.audioFileSize // (maxThreads * audioThreadsRatio)) for k in range(0, maxThreads * videoThreadsRatio) if self.audioUrl != None] + [self.audioFileSize] if self.audioFileSize != None else None
        # ic(videoFileLengs, audioFileLengs)
        if self.videoUrl != None and self.videoFileSize != None:
            for k in range(maxThreads * videoThreadsRatio):
                dlVideoTask = threading.Thread(target=download, name=self.vTitle + str(k), args=(self.videoUrl, self.fakeName + f'{k}.mp4', videoFileLengs[k], videoFileLengs[k + 1]))
                dlVideoTask.start()
        elif self.videoUrl != None:
            dlVideoTask = threading.Thread(target=queueItem.requestsDownload, name='video', args=(self.videoUrl, self.fakeName + '.mp4'))
            dlVideoTask.start()
        if self.audioUrl != None and self.audioFileSize != None:
            for k in range(maxThreads * audioThreadsRatio):
                dlAudioTask = threading.Thread(target=download, name=self.vTitle + str(k), args=(self.audioUrl, self.fakeName + f'{k}.mp3', audioFileLengs[k], audioFileLengs[k + 1]))
                dlAudioTask.start()
        elif self.audioUrl != None:
            data = requests.get(self.audioUrl)
            with open(self.fakeName + '.mp3', 'wb') as audio:
                audio.write(data.content)
            dlAudioTask = threading.Thread(target=queueItem.requestsDownload, name='audio', args=(self.audioUrl, self.fakeName + '.mp3'))
            dlAudioTask.start()
        if self.barrageUrl != None:
            dlBarrageTask = threading.Thread(target=getDanmaku, name=self.vTitle + 'Barrage', args=(self.barrageUrl, self.namePath))
            dlBarrageTask.start()

    def requestsDownload(url, fakeName) -> None:
        data = requests.get(url)
        with open(fakeName, 'wb') as file:
            file.write(data.content)    

# 主函数(入口点)
# ===================================================================================================================================================================================
if __name__ == '__main__':
    def func_(func, inputList:list):
        """
        func: 调用函数名称
        args: 负载信息(元组)
        
        无返回值
        """
        if func == 'dl':
            typeJudgment(inputList[0][1], inputList=inputList[1])
        elif func == 'help':
            print(eval(inputList[0][1]).__annotations__, eval(inputList[0][1]).__doc__, sep='\n')
        elif func == 'exit':
            if (len(threading.enumerate()) <= ogThreadings) | (input('是否强制性结束所有下载进程并退出(输入1):') == '1'):
                print('已退出!')
                sys.exit()
        elif func == 'showtasks':
            tasksList = threading.enumerate()
            # ic(len(tasks_list), type(tasks_list))
            for k in range(len(tasksList)):
                print(k + 1, '\t', tasksList[k])
        elif func == 'clean':
            dlList.clear()
            print('已成功清空下载列表!')
        elif func == 'kill':
            pass
        elif func == 'dbg':
            pass
        elif func == 'test':
            pass
        elif func == 'root':
            pass
        else:
            print(f'ERROR-> \'{func}\' 不是一个有效的命令')
    # 获取最新番剧更新
    # get_latest_anime()
    # 获取动态更新,无法识别多种类型,运行会报错
    # get_timezone_data()
    # 获取关注UP主是否更新,似乎没什么用~
    # get_update_data()
    compositionTask = threading.Thread(target=startDownload, name='startThreading')
    compositionTask.start()
    ogThreadings = len(threading.enumerate())
    while True:
        inputList = input('Controlpanel ?-> ').split(',')
        authorInput = inputList[1].split() if len(inputList) > 1 else None
        authorInputList = [inputList[0].split() if len(inputList[0].split()) > 1 else []]
        authorInputList.append(authorInput)
        func_(inputList[0].split()[0], authorInputList)
