import urllib.request,urllib.parse,urllib.error
import socket
import http


def web_request(url):
    """Returns bytes of response for get request to url"""
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "http://" + url
    try:
        with urllib.request.urlopen(url) as response:
            response_data = response.read()
    except urllib.error.URLError as e:
        response_data = ''
    except socket.error:
        response_data = ''
    except socket.timeout:
        response_data = ''
    except socket.gaierror:
        response_data = ''
    except UnicodeEncodeError:
        response_data = ''
    except http.client.BadStatusLine:
        response_data = ''
    except http.client.IncompleteRead:
        response_data = ''
    except urllib.error.HTTPError:
            response_data = ''
    return response_data