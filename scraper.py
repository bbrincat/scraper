from collections import namedtuple, defaultdict
from urllib import request
from urllib.error import  HTTPError
from urllib.parse import  quote, urlsplit, urlunsplit
from html_utils import extract_page_resources, extract_page_tables, extract_content_type


def get_url_resources(tag,resource_url):
    # url might have spaces, so path needs to be encoded
    us = urlsplit(resource_url)
    resource_url = urlunsplit((us.scheme, us.netloc, quote(us.path), us.query, us.fragment))
    try:
        response = request.urlopen(resource_url)
    except HTTPError as e:
        return [Resource(tag, resource_url, None, 0, None)]
    mimetype, encoding = extract_content_type(response)
    response_data = response.readall()

    resources = []
    # if we have an iframe, then recursively extract
    if mimetype == "text/html" and (tag=="iframe" or tag is None):
        page = response_data.decode(encoding=encoding)
        page_resources = get_page_resources(page, resource_url)
        resources.extend(page_resources)
        resources.append(Resource(tag, resource_url, mimetype, len(response_data), page))
    else:
        resources.append(Resource(tag, resource_url, mimetype, len(response_data), response_data))

    return resources


def get_page_resources(page, url):
    # Decodes the html page and returns a list of Resources

    Resources = []
    page_resources = extract_page_resources(page, url)
    num_resources = len(page_resources)

    print("{} resources in {}".format(num_resources, url))
    for num, (tag, type, resource_url) in enumerate(page_resources):
        print("Downloading {}/{}".format(num, num_resources))
        Resources.extend(get_url_resources(tag, resource_url))

    return Resources

Resource  = namedtuple('Resource', ['tag','url','mimetype', 'length','data'])


if __name__ == "__main__":

    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("url", help="Url to scrape", type=str)

    parser.add_argument("--tables", action="store_true", help="Extract table data from html files", )
    args = parser.parse_args()
    url = args.url

    kb = lambda x: "{0:.2f} KB".format(x /1024)


    resources = get_url_resources(None, url)

    if len(resources) ==1:
        print("{} {}  Size {}".format(resources[0].url, resources[0].mimetype, kb(resources[0].length)))
    else :
        print("Total number of http requests: {}".format(len(resources)))

    by_tag = defaultdict(list)
    by_mime = defaultdict(list)
    total_size = 0

    for res in resources:
        by_tag[res.tag].append(res)
        by_mime[res.mimetype].append(res)
        total_size = total_size+res.length

    print("Total download size {}\n".format(kb(total_size)))

    print("Breakdown by mimetype:")
    for key, list_resources in by_mime.items():
        size = sum([r.length for r in list_resources])
        print("Mimetype: {}. Download size: {}. Number of requests: {}".format(key, kb(size) ,len(list_resources)))

    print("\nBreakdown by tag:")

    for key, list_resources in by_tag.items():
        size = sum([r.length for r in list_resources])
        print("Tag: {}. Download size: {}. Number of requests: {}".format(key, kb(size) ,len(list_resources)))

    if args.tables:
        pages  = [ res.data for res in resources if res.mimetype == "text/html" and type(res.data) is str]
        for page in pages:
            tables = extract_page_tables(page)
            print("\n")
            for table in tables:
                for row in table:
                    row_format = "{:>25}" * (len(row))
                    print(row_format.format(*[datum[0:20] for datum in row]))
