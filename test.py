import requests
from PIL import Image

resp = requests.get('https://i.pinimg.com/236x/e2/02/bf/e202bf481835d91851863044254cb647.jpg')
im = Image.open(resp.content)
width, height = im.size