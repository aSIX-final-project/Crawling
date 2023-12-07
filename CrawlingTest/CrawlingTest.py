from selenium import webdriver
from selenium.webdriver.common.by import By
from flask import Flask
import pymysql
import time
from datetime import datetime

def get_db_connection():
    return pymysql.connect(host='svc.sel5.cloudtype.app', port=32668, user='root',
                           passwd='0000', db='sonagi', charset='utf8')

app = Flask(__name__)

def job1():
    driver = webdriver.Chrome()
    url = 'https://ols.sbiz.or.kr/ols/man/SMAN051M/page.do'
    driver.get(url)
    div_elements = driver.find_elements(By.XPATH, "//div[@class='board_list s_form']")

    current_date = datetime.now().strftime('%Y-%m')

    for divE in div_elements:
        a_elements = divE.find_elements(By.XPATH, ".//a[@class='ga_link ta_l']")
        td_elements = divE.find_elements(By.XPATH, ".//td[@class='nt_04 bd_37']")
        
        for a, td in zip(a_elements, td_elements):
            td_date = datetime.strptime(td.text, '%Y-%m-%d').strftime('%Y-%m')
            if '접수마감' in a.text:
                a.click()
                content_element = driver.find_element(By.CSS_SELECTOR, "div.bv_c#cntnDiv")
                driver.back()
            if current_date == td_date:
                print(f"제목 {a.text}, 작성일 {td.text}")
                db = get_db_connection()
                cursor = db.cursor()
                sql = "SELECT * FROM CrawlingNoticeGive WHERE title=%s AND date=%s"
                cursor.execute(sql, (a.text, td.text))
                result = cursor.fetchone()
                if result is None:
                    sql = "INSERT INTO CrawlingNoticeGive (title, date) VALUES (%s, %s)"
                    cursor.execute(sql, (a.text, td.text))
                    db.commit()
                db.close()
    driver.quit()
    
def job2():
    driver = webdriver.Chrome()
    url = 'https://finsupport.naver.com/subvention/search'
    driver.get(url)

    span_element = driver.find_element(By.XPATH, "//span[text()='공고특성을 선택해 주세요']")
    span_element.click()
    time.sleep(1)

    a_element = driver.find_element(By.XPATH, "//a[text()='소상공인']")
    a_element.click()
    time.sleep(1)

    button_element = driver.find_element(By.XPATH, '//*[@id="root"]/div[3]/div[3]/div[4]/div/div[2]/div[14]/div[3]/button[2]')
    button_element.click()
    time.sleep(1)

    a_element = driver.find_element(By.XPATH, '//*[@id="root"]/div[3]/div[3]/div[4]/div/div[2]/div[17]/a')
    a_element.click()
    time.sleep(5)

    list_elements = driver.find_elements(By.XPATH, "//a[@class='guide_list_link ']")


    for listE in list_elements:
        theme_olive_elements = listE.find_elements(By.XPATH, ".//div[@class='category_list_box']/ul/li")
        theme_olive = theme_olive_elements[0].text if theme_olive_elements else None
        guide_list_desc = listE.find_element(By.XPATH, ".//p[@class='guide_list_desc']").text
        guide_list_title = listE.find_element(By.XPATH, ".//h3[@class='guide_list_title ellipsis']").text
        dl_values = listE.find_elements(By.XPATH, ".//dl")
        
        dt_dd_pairs = [(dl.find_element(By.XPATH, ".//dt").text, dl.find_element(By.XPATH, ".//dd").text) for dl in dl_values]
        
        region = next((dd for dt, dd in dt_dd_pairs if dt == '지역'), None)

        hashtag_list = listE.find_elements(By.XPATH, ".//ul[@class='hashtag_area']/li")
        hashtags = [hashtag.text for hashtag in hashtag_list]
        
        db = get_db_connection()
        cursor = db.cursor()   
        
        check_query = "SELECT * FROM CrawlingNaverGive WHERE title=%s AND region=%s"
        cursor.execute(check_query, (guide_list_title, region))
        result = cursor.fetchone()
        print(result)

        if result is None:
            insert_query = "INSERT INTO CrawlingNaverGive (theme, department, title, region, hashtags) VALUES (%s, %s, %s, %s, %s)"
            values = (theme_olive, guide_list_desc, guide_list_title, region, ", ".join(hashtags))
            cursor.execute(insert_query, values)
            db.commit()

    driver.quit()

def job3():
    driver = webdriver.Chrome()

    url = 'https://www.donorscamp.org/culSupportProgList_P.do'
    driver.get(url)

    div_elements = driver.find_elements(By.XPATH, "//div[@class='slide']")

    db = get_db_connection()
    cursor = db.cursor()

    for divE in div_elements:
        evt_wraps = divE.find_elements(By.XPATH, ".//div[@class='evt-wrap']")
        for evt in evt_wraps:
            span_elements = evt.find_elements(By.XPATH, ".//span[@class='badge-txt type-recru']")
            for span in span_elements:
                if span.text == '모집중':
                    img_elements = divE.find_elements(By.XPATH, ".//div[@class='img']//img")
                    pre_element = evt.find_element(By.XPATH,".//pre[@class='evt-tit']")
                    for img in img_elements:
                        img_src = img.get_attribute('src')
                    edu_wraps = divE.find_elements(By.XPATH, ".//div[@class='cc-edu-wrap']//span")
                    for edu in edu_wraps:
                        edu_text = edu.text
                    check_query = "SELECT * FROM CrawlingDonorsCampGiveP WHERE title=%s AND date=%s"
                    cursor.execute(check_query, (pre_element.text, edu_text))
                    result = cursor.fetchone()
                    if result is None:
                        print(f"'{pre_element.text}' 가 db에 추가됨")
                        insert_query = "INSERT INTO CrawlingDonorsCampGiveP (status, title, imageSrc, date) VALUES (%s, %s, %s, %s)"
                        values = (span.text, pre_element.text, img_src, edu_text)
                        cursor.execute(insert_query, values)
                        db.commit()
                    else:
                        print(f"'{pre_element.text}' 가 이미 db에 있어서 추가 안됨")

    driver.quit()


def run_jobs():
    job1()
    job2()
    job3()
    print("job1,2,3 함수가 완료 되었습니다. 다음 함수 실행은 24시간 뒤에 실행됩니다.")
    time.sleep(24 * 60 * 60) 

while True:
    run_jobs()
