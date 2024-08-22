import datetime
import time

from s3p_sdk.plugin.payloads.parsers import S3PParserBase
from s3p_sdk.types import S3PRefer, S3PDocument
from selenium.common import NoSuchElementException
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait


class OasisParser(S3PParserBase):
    """
    Парсер, использующий базовый класс парсера S3P
    """

    def __init__(self, refer: S3PRefer, driver: WebDriver, url: str, timeout: int = 20, max_count_documents: int = None,
                 last_document: S3PDocument = None):
        super().__init__(refer, max_count_documents, last_document)

        # Тут должны быть инициализированы свойства, характерные для этого парсера. Например: WebDriver
        self.URL = url
        self._driver = driver
        self._timeout = timeout
        self._wait = WebDriverWait(self._driver, timeout=self._timeout)

    def _parse(self) -> None:
        # HOST - это главная ссылка на источник, по которому будет "бегать" парсер
        self.logger.debug(F"Parser enter to {self._refer.to_logging}")

        self._driver.get(url=self.URL)

        details = self._driver.find_element(By.XPATH, '//*[@id="main"]/section').find_elements(By.TAG_NAME, 'details')

        documents = []

        for detail in details:

            standard_toggle_details = detail.find_element(By.CLASS_NAME, 'standard__toggle-details')
            global_title = standard_toggle_details.find_element(By.CLASS_NAME, 'standard__title').text

            try:
                global_annotation = standard_toggle_details.find_element(By.CLASS_NAME, 'standard__description').text
            except Exception as _ex:
                self.logger.warn('there is no global annotation')
                global_annotation = None
            try:
                date = datetime.datetime.strptime(
                    str(standard_toggle_details.find_element(By.CLASS_NAME, 'standard__date').text)
                    .split(':')[1].strip(), '%d %b %Y')
            except Exception as _ex:
                self.logger.warn('Nah, we don`t, want to check this news')
                date = None

            standard_details = detail.find_element(By.CLASS_NAME, 'standard__details')
            standard_grid = standard_details.find_element(By.CLASS_NAME, 'standard__grid')
            object_document = {
                "global_title": global_title,
                "global_annotation": global_annotation,
                "date": date,
                "local_documents": []
            }

            if date != None:
                try:
                    cite_as_elements = standard_grid.find_element(By.CLASS_NAME,
                                                                  'standard__grid-body.standard__grid--cite-as') \
                        .find_elements(By.TAG_NAME, 'p')
                except Exception as _ex:
                    self.logger.warn('There is no site_as')
                    cite_as_elements = []
                if not cite_as_elements:
                    try:
                        links = standard_grid.find_element(By.CLASS_NAME, 'standard__grid-body.standard__grid--links') \
                            .find_elements(By.TAG_NAME, "a")
                        for link_object in links:
                            have_attribute = link_object.get_attribute('href')
                            if have_attribute:
                                if have_attribute.endswith('.html'):
                                    link = link_object.get_attribute('href')
                                    local_document = {
                                        "local_link": link,
                                        "local_text": None,
                                    }
                                    object_document['local_documents'].append(local_document)
                    except Exception as _ex:
                        self.logger.warn(f'there is no links, so there is no page? {global_title}')
                else:
                    for cite_as_element in cite_as_elements:
                        try:
                            link = cite_as_element.find_element(By.TAG_NAME, "a").get_attribute('href')
                            if link.endswith('.html'):
                                local_document = {
                                    "local_link": link,
                                    "local_text": None,
                                }
                                object_document['local_documents'].append(local_document)
                        except Exception as _ex:
                            self.logger.warn('Fake `p` tag')
                if len(object_document["local_documents"]) != 0:
                    documents.append(object_document)
        self._end_work(documents)

    def _end_work(self, documents: list):
        for document in documents:
            for i in range(len(document["local_documents"])):
                self._driver.get(url=document["local_documents"][i]["local_link"])
                try:
                    try:
                        body_info = self._driver.find_element(By.TAG_NAME, 'body')
                    except Exception as _ex:
                        body_info = self._driver.find_element(By.XPATH, '//*[@id="topmenu-body"]')
                    local_text = body_info.text
                    document["local_documents"][i]["local_text"] = local_text

                    self._find(S3PDocument(
                        title=f"{document['global_title']} ({str(document['local_documents'][i]['local_link']).replace('http://docs.oasis-open.org/','')})",
                        abstract=document['global_annotation'],
                        link=document['local_documents'][i]['local_link'],
                        text=document['local_documents'][i]['local_text'],
                        other=None,
                        loaded=datetime.datetime.now(),
                        id=None,
                        published=document['date'],
                        storage=None
                    ))
                except Exception as _ex:
                    self.logger.warn('There is no title, text or annotation', document['local_documents'][i]['local_link'])

    def _parse_page(self, url: str) -> S3PDocument:
        doc = self._page_init(url)
        return doc

    def _page_init(self, url: str) -> S3PDocument:
        self._initial_access_source(url)
        return S3PDocument()

    def _encounter_pages(self) -> str:
        """
        Формирование ссылки для обхода всех страниц
        """
        _base = self.URL
        _param = f'&page='
        page = 0
        while True:
            url = str(_base) + _param + str(page)
            page += 1
            yield url

    def _collect_doc_links(self, _url: str) -> list[str]:
        """
        Формирование списка ссылок на материалы страницы
        """
        try:
            self._initial_access_source(_url)
            self._wait.until(ec.presence_of_all_elements_located((By.CLASS_NAME, '<class контейнера>')))
        except Exception as e:
            raise NoSuchElementException() from e
        links = []

        try:
            articles = self._driver.find_elements(By.CLASS_NAME, '<class контейнера>')
        except Exception as e:
            raise NoSuchElementException('list is empty') from e
        else:
            for article in articles:
                try:
                    doc_link = article.find_element(By.TAG_NAME, 'a').get_attribute('href')
                except Exception as e:
                    raise NoSuchElementException(
                        'Страница не открывается или ошибка получения обязательных полей') from e
                else:
                    links.append(doc_link)
        return links

    def _initial_access_source(self, url: str, delay: int = 2):
        self._driver.get(url)
        self.logger.debug('Entered on web page ' + url)
        time.sleep(delay)
