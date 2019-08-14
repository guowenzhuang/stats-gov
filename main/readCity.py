import pickle

import pymysql


###
# 读取文件里的城市区街道信息并存取到数据库
###
if __name__ == '__main__':
    db = pymysql.connect("192.168.1.253", "root", "dev@253.MySql", "base_demo", charset='utf8')


    obj = None
    with open('abc.pkl', 'rb') as f:
        obj = pickle.load(f)

    # 插入省sql
    sql_prov = "INSERT INTO ddic_geo_province(prov_code, prov_code_name, country_code) VALUES (%s,%s,%s)"
    sql_city = "INSERT INTO ddic_geo_city(city_code, city_code_name, prov_code, country_code) VALUES (%s,%s,%s,%s)"
    sql_area = "INSERT INTO ddic_geo_area(area_code, area_code_name, city_code, prov_code, country_code) VALUES (%s,%s,%s,%s,%s)"
    sql_street = "INSERT INTO ddic_geo_street(street_code, street_code_name, area_code, city_code, prov_code, country_code) VALUES (%s,%s,%s,%s,%s,%s)"
    prov_params = [];
    city_params = [];
    area_params = [];
    street_params = [];
    country = '1'
    for item in obj:
        item['soup'] = None
        provinceCode = item['province']['city'][0]['code'][0:2] + '0000'
        # print('省',item['province']['name'],provinceCode)
        prov_params.append([provinceCode, item['province']['name'], country])
        for itemCity in item['province']['city']:
            itemCity['soup'] = None
            # print('---市',itemCity['name'],itemCity['code'])
            city_params.append([itemCity['code'], itemCity['name'], provinceCode, country])
            for itemArea in itemCity['area']:
                itemArea['soup'] = None
                # print('------区',itemArea['name'],itemArea['code'])
                area_params.append([itemArea['code'],itemArea['name'],itemCity['code'],provinceCode,country])
                for itemStreet in itemArea['street']:
                    itemStreet['soup'] = None
                    # print('---------街道',itemStreet['name'],itemStreet['code'])
                    street_params.append([itemStreet['code'],itemStreet['name'],itemArea['code'],itemCity['code'],provinceCode,country])


    try:
        cursor = db.cursor()
        # 执行sql语句
        cursor.executemany(sql_prov, prov_params)
        cursor.executemany(sql_city, city_params)
        cursor.executemany(sql_area, area_params)
        cursor.executemany(sql_street, street_params)
        # 提交到数据库执行
        db.commit()
    except Exception:
        # 如果发生错误则回滚
        print('错误')
        db.rollback()
    # 关闭游标
    cursor.close()
    # 关闭数据库连接
    db.close()
