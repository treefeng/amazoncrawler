import pandas as pd
import re
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import time
from pymongo import MongoClient

class AmazonCrawler:
    def __init__(self):
        # crawl through simulating Chrome browser
        # self.driver = webdriver.Chrome(
        #      "/Users/665164/Documents/Sentiment_project/chromedriver")

        dcap = dict(DesiredCapabilities.PHANTOMJS)
        dcap["phantomjs.page.settings.userAgent"] = \
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36"

        # config the path of PhantomJS
        phantomjsPath = "/Users/665164/Documents/phantomjs/bin/phantomjs"

        # the first driver for crawling the goods' basic information in each category
        self.driver = webdriver.PhantomJS(executable_path=phantomjsPath, desired_capabilities=dcap)
        self.driver.implicitly_wait(20)

        # the second driver for crawling the goods' reviews information in each goods
        # self.goods_driver = webdriver.PhantomJS(executable_path=phantomjsPath, desired_capabilities=dcap)

        # crawl through simulating Chrome browser
        self.goods_driver = webdriver.Chrome(
             "/Users/665164/Documents/Sentiment_project/chromedriver")

        # connect the database
        self.client = MongoClient('localhost', 27017)
        self.db = self.client.amazon_crawler

    # def proxy(self, change_time):
    #     # set phantomJS's agent
    #     proxy_ip_list = []
    #     for proxy_ip in proxy_ip_list:
    #         service_args = [
    #             '--proxy=' + proxy_ip,
    #             '--proxy-type=socks5',
    #         ]
    #         driver = webdriver.PhantomJS(executable_path=self.phantomjsPath, desired_capabilities=self.dcap,
    #                                      service_args=service_args)
    #         driver.implicitly_wait(10)
    #     return driver

    # Get the categories

    def categories(self):
        data_storage_url = 'https://www.amazon.com/s/ref=sr_ex_n_1?srs=2530365011&rh=n%3A1292110011'
        # driver = self.proxy()
        self.driver.get(data_storage_url)

        category_num_pat = '<li style="margin-left: 22px">'
        category_num = len(re.compile(category_num_pat).findall(self.driver.page_source))
        # print(category_num)

        category = dict()
        for i in range(1, category_num + 1):
            category_name = self.driver.find_element_by_xpath(
                '//ul[@id="ref_1292110011"]/li[' + str(4 + i) + ']/a/span[1]').text.encode('ascii', 'ignore').decode(
                'ascii')
            category_link = self.driver.find_element_by_xpath(
                '//ul[@id="ref_1292110011"]/li[' + str(4 + i) + ']/a').get_attribute('href').encode('ascii',
                                                                                                    'ignore').decode(
                'ascii')
            # pat = 'rh=n%3A(\d+)'
            # category_id = '3A' + re.compile(pat).findall(category_link)[0]
            category[category_name] = category_link

        return category

    def single_category(self):
        category = self.categories()

        goods_id_list = []
        title_list = []
        link_list = []
        category_name_list = []
        category_link_list = []

        data_list = []

        for k, v in category.items():

            category_url = v
            category_name = k
            print('crawling ' + category_name + '\'s goods information')
            print(category_url)
            try:
                self.driver.get(category_url)
                WebDriverWait(self.driver, 10).until(lambda x: x.find_element_by_id('pagn').is_displayed())

                try:
                    total_page = self.driver.find_element_by_xpath('//span[@class="pagnDisabled"]').text.encode('ascii',
                                                                                                'ignore').decode('ascii')
                except NoSuchElementException:
                    total_page = 1

                total_page = int(total_page)

                if (total_page == 1 or total_page == 2):
                    for i in range(1, total_page + 1):

                        # Crawling the first page
                        print('---------crawling page ' + str(i) + '---------')
                        goods_id_list_selector = self.driver.find_elements_by_xpath(
                            '//li[@class="s-result-item celwidget "]')

                        if (len(goods_id_list_selector) == 0):
                            goods_id_list_selector = self.driver.find_elements_by_xpath(
                                '//li[@class="s-result-item  celwidget "]')
                        else:
                            goods_id_list_selector = goods_id_list_selector

                        title_list_selector = self.driver.find_elements_by_css_selector('.s-color-twister-title-link')
                        link_list_selector = self.driver.find_elements_by_css_selector('.s-color-twister-title-link')

                        for j in range(0, len(goods_id_list_selector)):
                            goods_id = goods_id_list_selector[j].get_attribute('data-asin')
                            goods_id_list.append(goods_id)
                            title = title_list_selector[j].get_attribute('title')
                            title_list.append(title)
                            link = link_list_selector[j].get_attribute('href')
                            link_list.append(link)
                            category_name_list.append(category_name)
                            category_link_list.append(category_url)

                            data = {
                                'category_name': category_name,
                                'category_link': category_url,
                                'goods_title': title,
                                'goods_link': link,
                                'goods_uniqueID': goods_id
                            }
                            data_list.append(data)

                        # Crawling the remaining page
                        if i < total_page:
                            next_url = WebDriverWait(self.driver, 30).until(
                                EC.element_to_be_clickable((By.XPATH, '//a/span[@id="pagnNextString"]')))
                            time.sleep(2)
                            next_url.click()
                            WebDriverWait(self.driver, 20).until(lambda x: x.find_element_by_id('pagn').is_displayed())
                            self.driver.implicitly_wait(10)

                        # Till the last page
                        else:
                            continue

                else:
                    # For multiple pages category, crawl three pages for testing
                    for i in range(1, 2):

                        # Crawling the first page
                        print('---------crawling page ' + str(i) + '---------')
                        goods_id_list_selector = self.driver.find_elements_by_xpath(
                            '//li[@class="s-result-item celwidget "]')

                        if (len(goods_id_list_selector) == 0):
                            goods_id_list_selector = self.driver.find_elements_by_xpath(
                                '//li[@class="s-result-item  celwidget "]')
                        else:
                            goods_id_list_selector = goods_id_list_selector

                        title_list_selector = self.driver.find_elements_by_css_selector('.s-color-twister-title-link')
                        link_list_selector = self.driver.find_elements_by_css_selector('.s-color-twister-title-link')

                        for j in range(0, len(goods_id_list_selector)):
                            goods_id = goods_id_list_selector[j].get_attribute('data-asin')
                            goods_id_list.append(goods_id)
                            title = title_list_selector[j].get_attribute('title')
                            title_list.append(title)
                            link = link_list_selector[j].get_attribute('href')
                            link_list.append(link)
                            category_name_list.append(category_name)
                            category_link_list.append(category_url)
                            data = {
                                'category_name': category_name,
                                'category_link': category_url,
                                'goods_title': title,
                                'goods_link': link,
                                'goods_uniqueID': goods_id
                            }
                            data_list.append(data)

                        # Crawling the remaining page
                        if i < total_page:
                            next_url = WebDriverWait(self.driver, 30).until(
                                EC.element_to_be_clickable((By.XPATH, '//a/span[@id="pagnNextString"]')))
                            time.sleep(2)
                            next_url.click()
                            WebDriverWait(self.driver, 20).until(lambda x: x.find_element_by_id('pagn').is_displayed())
                            self.driver.implicitly_wait(10)

                        # Till the last page
                        else:
                            continue

            except TimeoutException:
                print('This page takes too much time to be loaded.')
                self.quit_driver(self.driver)

            print(link_list)
            print(title_list)
            print(goods_id_list)
            print()

        self.quit_driver(self.driver)

        self.store_data(data_list, 'category')

        # output = pd.DataFrame({
        #     'category_name': category_name_list,
        #     'category_link': category_link_list,
        #     'goods_title': title_list,
        #     'goods_link': link_list,
        #     'goods_uniqueID': goods_id_list})
        #
        # return output

    def single_page(self, goods_url):

        print(goods_url)

        try:
            self.goods_driver.get(goods_url)

            total_page = self.goods_driver.find_element_by_xpath(
                '//*[@id="cm_cr-pagination_bar"]/ul/li[7]/a').text.encode('ascii', 'ignore').decode('ascii')

            total_page = int(total_page)

            for i in range(1, total_page + 1):
                print("page:" + str(i) + " (out of " + str(total_page) + ")")

                goods_id_list_selector = self.goods_driver.find_elements_by_xpath(
                    '//*[@class="a-section review"]')

                for j in range(0, len(goods_id_list_selector)):
                    goods_id = goods_id_list_selector[j].get_attribute('id')

                    customer_id = goods_id
                    page = self.goods_driver.find_element_by_xpath(
                        '//*[@id="cm_cr-review_list"]/div[1]/span[1]').text.encode(
                        'ascii',
                        'ignore').decode(
                        'ascii')
                    star = self.goods_driver.find_element_by_xpath(
                        '//*[@id="customer_review-' + goods_id + '"]/div[1]/a[1]/i/span').get_attribute(
                        "innerHTML").encode(
                        'ascii', 'ignore').decode('ascii').replace(" out of 5 stars", "")
                    title = self.goods_driver.find_element_by_xpath(
                        '//*[@id="customer_review-' + goods_id + '"]/div[1]/a[2]').text.encode(
                        'ascii', 'ignore').decode('ascii')
                    author = self.goods_driver.find_element_by_xpath(
                        '//*[@id="customer_review-' + goods_id + '"]/div[2]/span[1]/a').text.encode('ascii',
                                                                                                    'ignore').decode(
                        'ascii')
                    date = self.goods_driver.find_element_by_xpath(
                        '//*[@id="customer_review-' + goods_id + '"]/div[2]/span[4]').text.encode('ascii',
                                                                                                  'ignore').decode(
                        'ascii').replace("on ", "")

                    try:
                        cap_style = self.goods_driver.find_element_by_xpath(
                            '//*[@id="customer_review-' + goods_id + '"]/div[3]/a').text.encode('ascii',
                                                                                                'ignore').decode(
                            'ascii')
                        capacity = cap_style.partition('\n')[0].replace("Capacity: ", "")
                        style = cap_style.partition('\n')[-1].replace("Style Name: ", "")
                    except NoSuchElementException:
                        capacity = "NA"
                        style = "NA"

                    review = ''.join(self.goods_driver.find_element_by_xpath(
                        '//*[@id="customer_review-' + goods_id + '"]/div[4]/span').text).strip()

                    try:
                        useful = self.goods_driver.find_element_by_xpath(
                            '//*[@id="customer_review-' + goods_id + '"]/div[5]/div/span[3]/span/span[1]').text.encode(
                            'ascii',
                            'ignore').decode(
                            'ascii')
                    except NoSuchElementException:
                        try:
                            useful = self.goods_driver.find_element_by_xpath(
                                '//*[@id="customer_review-' + goods_id[j] + '"]/div[7]/div/span[3]/span/span[1]').text \
                                .encode('ascii', 'ignore').decode('ascii')
                        except NoSuchElementException:
                            useful = "NA"
                    if useful == "Was this review helpful to you?":
                        useful = "0"
                    else:
                        useful = useful.partition(' ')[0]
                        if useful == "One":
                            useful = "1"

                    data = {
                        'page': page,
                        'customerID': customer_id,
                        'star': star,
                        'title': title,
                        'author': author,
                        "date": date,
                        "capacity": capacity,
                        "style": style,
                        "raw_review": review,
                        "useful": useful
                    }

                    self.store_data(data, 'goods')

                    # data_list.append(data)

                # crawling the remaining page
                if i < total_page:
                    # if self.goods_driver.find_element_by_xpath('//*[@id="cm_cr-pagination_bar"]/ul/li[8]/a').text[0] == "N":
                    #     next_url = WebDriverWait(self.driver, 30).until(
                    #         EC.element_to_be_clickable((By.XPATH, '//*[@id="cm_cr-pagination_bar"]/ul/li[8]/a')))
                    #     time.sleep(2)
                    #     next_url.click()
                    # else:
                    #     next_url = WebDriverWait(self.driver, 30).until(
                    #         EC.element_to_be_clickable((By.XPATH, '//*[@id="cm_cr-pagination_bar"]/ul/li[9]/a')))
                    #     time.sleep(2)
                    #     next_url.click()
                    if self.goods_driver.find_element_by_xpath('//*[@id="cm_cr-pagination_bar"]/ul/li[8]/a').text[0] == "N":
                        self.goods_driver.find_element_by_xpath('//*[@id="cm_cr-pagination_bar"]/ul/li[8]/a').click()
                    else:
                        self.goods_driver.find_element_by_xpath('//*[@id="cm_cr-pagination_bar"]/ul/li[9]/a').click()
                else:
                    break

                    # self.store_data(data_list, 'goods')
        except TimeoutException:
            print('This page takes too much time to be loaded.')
            self.quit_driver(self.driver)

    def quit_driver(self, driver):
        driver.close()
        driver.quit()

    def store_data(self, data, flag):
        if (flag == 'category'):
            collection = self.db.Seagate_categories_info
            collection.insert_many(data)
        else:
            collection = self.db.Seagate_goods_info
            # collection.insert_many(data)
            collection.insert(data)
        print('------inserted-------')

    def crawling(self):
        if (self.db.Seagate_categories_info.find().count() == 0):
            print('------crawling categories\' information-------')
            self.single_category()

        else:
            print('------crawling single goods\' information-------')
            collection = self.db.Seagate_categories_info
            cursor = collection.find()
            for items in cursor:
                url = items['goods_link']
                goods_url = url.replace('dp', 'product-reviews')
                self.single_page(goods_url)

            self.goods_driver.quit()

def main():
    crawler = AmazonCrawler()
    crawler.crawling()
    # output.to_csv('/Users/665164/Documents/Sentiment_project/category_goods_info.csv', header=True)

if __name__ == '__main__':
    main()
