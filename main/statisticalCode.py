from bs4 import BeautifulSoup
import logging
import requests
import pymysql
import pickle

###
# 读取所有省市区街道地址并存取到文件里
###
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s [line:%(lineno)d] %(levelname)s %(message)s',
                    datefmt='%a, %d %b %Y %H:%M:%S')


# 输入网址 获得网页的soup
def getsoup(url):
    try:
        logging.info("获取soup url:%s", url)
        res = requests.get(url, timeout=5)  # 以get方法访问目标网址获取网页信息
        res.encoding = 'gbk'  # 该网页是以gb2312的编码形式显示的
        logging.info("获取res url:%s res:%s", url, res)
        soup = BeautifulSoup(res.text, 'html.parser')  # 使用美丽汤解析网页内容
        logging.info("获取soup成功 url:%s", url)
        return soup
    except Exception:
        return getsoup(url)


def getsoupYear(soup):
    logging.info("获取最新区划和城乡划分代码")
    next_year = soup.select('.center_list_contlist a');
    url = next_year[0]['href']
    soup = getsoup(url)
    url = url.replace("index.html", "");
    logging.info("获取最新区划和城乡划分代码完成 url:%s", url)
    return soup, url


def getsecondhtml(soup, url):
    logging.info("获取省级网址和对应的内容")
    secondhtml = []  # 存放二级网址
    province = []  # 存放省、直辖市的名称
    for provincetr in soup.select('.provincetr a'):  # 观察目标网页构造发现想要获取的内容在class provincetr的 a 下
        provincetrUrl = url + provincetr['href']
        provincetrText = provincetr.text
        logging.info("获取省:%s 对应url:%s 开始", provincetrText, provincetrUrl)
        secondhtml.append(provincetrUrl)
        province.append(provincetrText)
        logging.info("获取省:%s 对应url:%s 完成", provincetrText, provincetrUrl)

    logging.info("获取省级网址和对应的内容完成")
    return secondhtml, province


# 输入list形式网址，以list获得网址的soup
def getlistsoup(listhtml, province):
    listsoup = []
    for i, html in enumerate(listhtml):
        logging.info("获取省级网址内容url:%s", html)
        listsoup.append({
            'soup': getsoup(html),
            'province': {
                'name': province[i]
            }
        })
        logging.info("获取省级网址内容url完成:%s", html)
    return listsoup


# 输入二层列表soup，输出二层统计用区划代码和名称,和第三层的url
def gettext2(soup2th, urlbase):
    logging.info("获取市级网址和对应的内容")
    soup2s = []
    soup_province = []
    citysoups=[]
    for soup2 in soup2th:
        soup2s.append(soup2['soup'])
        soup_province.append(soup2['province'])
    for i, soup2 in enumerate(soup2s):
        province_sin = soup_province[i];
        province_sin['city'] = []
        for temp in soup2.select('.citytr'):
            abqs=temp.findAll('a')
            t = abqs[1].text
            u = urlbase + abqs[1]['href']
            logging.info("获取市:%s 对应url:%s 开始", t, u)
            ubase=u.split('/');
            ubase.pop();
            obj={
                'name': t,
                'soup': getsoup(u),
                'code':abqs[0].text,
                'urlbase':'/'.join(ubase)+"/",
            }
            province_sin['city'].append(obj)
            citysoups.append(obj)
            logging.info("获取市:%s 对应url:%s 完成", t, u)
    logging.info("获取市级网址和对应的内容完成")
    return citysoups

# 获取区县级别内容
def gettext3(soup2th):
    city_objs = []
    logging.info("获取区级网址和对应的内容")
    for soup2_province in soup2th:
        for soup2_city in soup2_province['province']['city']:
            city_objs.append(soup2_city)
    for item in city_objs:
        item['area']=[]
        for temp in item['soup'].select('.countytr'):
            abqs=temp.findAll('a');
            if(len(abqs)==0):
                abqs = temp.findAll('td');

            la = lambda x: [x['href'],None][x.has_key('href')==False]
            soup=None
            ubase=''
            if(abqs[1].has_key('href')==True):
                soup=getsoup(item['urlbase']+abqs[1]['href'])
                ubase = abqs[1]['href'].split('/');
                ubase.pop();
                ubase="".join(ubase)+"/";
            obj = {
                'name': abqs[1].text,
                'soup':soup,
                'code': abqs[0].text,
                'urlbase':item['urlbase']+ubase
            }
            item['area'].append(obj)
    logging.info("获取区级网址和对应的内容 完成")

def gettext4(soup2th):
    areas=[]
    for item in soup2th:
        for itempro in item['province']:
            for itemCity in item['province']['city']:
                for itemArea in itemCity['area']:
                    areas.append(itemArea)
    for item in areas:
        item['street']=[]
        if(item['soup'] is None):
            continue
        for temp in item['soup'].select('.towntr'):
            abqs = temp.findAll('a');
            if (len(abqs) == 0):
                abqs = temp.findAll('td');
            obj = {
                'name': abqs[1].text,
                'code': abqs[0].text,
            }
            item['street'].append(obj)



if __name__ == '__main__':
    aimurl = "http://www.stats.gov.cn/tjsj/tjbz/tjyqhdmhcxhfdm/"  # 爬虫目标网址
    firstsoup = getsoup(aimurl)  # 获得首页的soup
    (soup, url) = getsoupYear(firstsoup);
    (secondhtml, province) = getsecondhtml(soup, url)
    soup2th = getlistsoup(secondhtml, province)
    citysoups = gettext2(soup2th, url)  # 获得第二层市级统计用区划代码与名称和第三层的url
    gettext3(soup2th)  # 获得第二层市级统计用区划代码与名称和第三层的url
    gettext4(soup2th)

    for item in soup2th:
        for itempro in item['province']:
            item['soup']=None
            print('省',item['province']['name'])

            for itemCity in item['province']['city']:
                itemCity['soup'] = None
                print('---市',itemCity['name'],itemCity['code'])
                for itemArea in itemCity['area']:
                    itemArea['soup'] = None
                    print('------区',itemArea['name'],itemArea['code'])
                    for itemStreet in itemArea['street']:
                        itemStreet['soup'] = None
                        print('---------街道',itemStreet['name'],itemStreet['code'])

    with open('abc.pkl', 'wb') as f:
        pickle.dump(soup2th, f)


