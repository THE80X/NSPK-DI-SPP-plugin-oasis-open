from selenium import webdriver
from oasis import OasisParser
from s3p_sdk.types import S3PDocument, S3PRefer


def driver():
    """
    Selenium web driver
    """
    options = webdriver.EdgeOptions()

    # Параметр для того, чтобы браузер не открывался.
    # options.add_argument('headless')
    #
    # options.add_argument('window-size=1920x1080')
    # options.add_argument("disable-gpu")
    # options.add_argument('--start-maximized')
    # options.add_argument('disable_infobars')

    return webdriver.Edge(options)


url = 'https://www.oasis-open.org/standards/'


parser = OasisParser(driver=driver(), url=url, refer=S3PRefer(name='oasis', id=0, type=None, loaded=None))
docs: list[S3PDocument] = parser.content()

print(*docs, sep='\n\r\n')
