from urllib.parse import urlencode, urlparse, urlunparse, parse_qs
def remove_from_url(name, url):
    print (name)
    print(url)
    u = urlparse(url)
    query = parse_qs(u.query)
    query.pop(name, None)
    print ((u))
    u = u._replace(query=urlencode(query, True))
    print (u)
    print (urlunparse(u))
    return urlunparse(u)
