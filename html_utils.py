from html.parser import HTMLParser
from urllib.parse import urljoin


def extract_page_resources(page, url):
    parser = HTMLResourceParser(baseurl=url)
    parser.feed(page)
    return parser.resources


def extract_page_tables(page):
    parser = HTMLTableParser()
    parser.feed(page)
    return parser.results


def extract_content_type(response):
    content_type = response.getheader('Content-Type')
    parts = content_type.split(';')
    mimetype = None
    encoding = None
    if len(parts) >= 1:
        mimetype = parts[0]
    if len(parts) == 2:
        # get charset
        encoding = parts[1].strip().split("=")[1]
    return mimetype, encoding


class HTMLResourceParser(HTMLParser):
    # Extract data of each tag which is relevant to us in resources
    def __init__(self, baseurl=None):
        self.resources = []
        self.baseurl = baseurl
        super().__init__()

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "img":
            url = attrs.get("src")
            type = "image"
        elif tag == "link":
            type = attrs.get("type")
            url = attrs.get("href")
        elif tag == "iframe":
            url = attrs.get("src")
            type = "iframe"
        elif tag == "embed":
            url = attrs.get("src")
            type = "embed"
        elif tag == "script":
            url = attrs.get("src")
            if url:
                type = attrs.get("type")
            else:
                return
        else:
            return

        try:
            self.resources.append((tag, type, urljoin(self.baseurl, url)))
        except Exception as e:
            pass


class HTMLTableParser(HTMLParser):
    # Extract tables
    # If tables are nested, then the nested table is a separate in the results list
    def __init__(self, ):
        self.tables = []
        super().__init__()
        self.extract_data = False
        self.results = []

    def handle_starttag(self, tag, attrs):
        if tag == "table":
            self.extract_data = False
            self.tables.append([])
        elif tag == "tr":
            self.tables[-1].append([])
        elif tag == "td":
            self.extract_data = True

    def handle_data(self, data):
        if self.extract_data:
            self.tables[-1][-1].append(data)

    def handle_endtag(self, tag):
        if tag == "td":
            self.extract_data = False
        elif tag == "tr":
            pass
        elif tag == "table":
            self.results.append(self.tables.pop())
