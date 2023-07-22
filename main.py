import asyncio
from pyppeteer import launch
import pandas as pd
import datetime
import requests as rq
import imaplib
import email
from email.header import decode_header
from PIL import Image
import torch
from bs4 import BeautifulSoup
from io import BytesIO
import re
import time

dict = {
  "0": 0,
  "1": 1,
  "2": 2,
  "3": 3,
  "4": 4,
  "5": 5,
  "6": 6,
  "7": 7,
  "8": 8,
  "9": 9,
  "10": "A",
  "11": "B",
  "12": "C",
  "13": "D",
  "14": "E",
  "15": "F",
  "16": "G",
  "17": "H" ,
  "18": "I" ,
  "19": "J" ,
  "20": "K" ,
  "21": "L" ,
  "22": "M" ,
  "23": "N" ,
  "24": "O" ,
  "25": "P",
  "26": "Q" ,
  "27": "R" ,
  "28": "S",
  "29": "T" ,
  "30": "U" ,
  "31": "V" ,
  "32": "W" ,
  "33": "X" ,
  "34": "Y" ,
  "35": "Z" ,
}
# "C:\Users\Muhammad\Desktop\newPlatform\best (1).pt"
# Load the trained model
model = torch.hub.load('ultralytics/yolov5', 'custom', path="best.pt",
                         force_reload=True)
def ocr(url):
  response = rq.get(url)
  img_bytes = BytesIO(response.content)

  # Load the image
  img = Image.open(img_bytes)
  #img = Image.open(url)
  # Perform inference
  results = model(img)

  prediction = results.pred[0]
  sorted_boxes = sorted(prediction, key=lambda x: x[0])
  s = ''
  for *box, confidence, class_id in sorted_boxes:
    s += str(dict[str(int(class_id))])
  return s


def my_email(username,password):
    mail = imaplib.IMAP4_SSL('imap.gmail.com')
    mail.login(username, password)
    #mail.login('hrdrami@gmail.com', 'vjjflvtrphrnqlyz')
    mail.select('inbox')

    # search for the email you want to retrieve
    typ, data = mail.search(None, 'ALL')
    email_id = data[0].split()[-1]

    # fetch the email body (including attachments)
    typ, data = mail.fetch(email_id, '(BODY.PEEK[])')
    raw_email = data[0][1]
    message = email.message_from_bytes(raw_email)

    text = ""
    if message.is_multipart():
        for payload in message.get_payload():
            charset = 'utf-8'
            text = payload.get_payload(decode=True).decode(charset)
    else:
        charset = message.get_content_charset() or 'utf-8'
        text = message.get_payload(decode=True).decode(charset)

    # Decode the email subject

    subject = email.header.decode_header(message['Subject'])[0][0]
    if isinstance(subject, bytes):
        # If the email subject is encoded in bytes, decode it to string
        subject = subject.decode('utf-8')

    res = {
        'From': email.utils.parseaddr(message['From'])[1],
        'From name': email.utils.parseaddr(message['From'])[0],
        'To': message['To'],
        'Subject': subject,
        'Text': text
    }

    # Extract the HTML content from the email
    soup = BeautifulSoup(text, 'html.parser')
    paragraph_tags = soup.find_all('p')

    # Extract the text between <p> and </p> tags
    text_between_p_tags = [tag.get_text() for tag in paragraph_tags]

    # Print the result
    numbers = re.findall(r'\d+', str(text_between_p_tags[2]))

    # print all found numbers
    text = ''
    for number in numbers:
        text += number
    return text

pages = []

async def openPage(page,txtName,txtPassportNu,txtIDNumber,txtCarNumber,txtEmail,txtMobile,fileUpload2,password):
    try:
        await page.goto('https://visitjordan.gov.jo/travelcars/')
        await page.evaluate('''() => {
                    let radio = document.querySelector('#rbEntJor');
                    radio.click();
                }''')
        await page.type("#txtName", txtName)
        await page.select('[id=ddlNationality]', "192")
        await page.type("#txtPassportNu", txtPassportNu)
        await page.type("#txtIDNumber",txtIDNumber )
        await page.type("#txtCarNumber",txtCarNumber )
        await page.type("#txtEmail",txtEmail )
        await page.select('[id=ddlCountryCode]', "00963")
        await page.type("#txtMobile", txtMobile)
        await execute(page,txtName,txtPassportNu,txtIDNumber,txtCarNumber,txtEmail,txtMobile,fileUpload2,password)

    except Exception:
        await openPage(page,txtName,txtPassportNu,txtIDNumber,txtCarNumber,txtEmail,txtMobile,fileUpload2,password)


async def fill():
    browser = await launch({"headless": False, "args": ['--no-sandbox', '--disable-setuid-sandbox'],
    "ignoreDefaultArgs": ['--disable-extensions']})
    pages.clear()
    file = pd.read_csv('final.csv', header=0)
    # create new tabs
    for i in range(len(file.index)):
        page = await browser.newPage()
        await openPage(page,file['الاسم'][i],str(file['رقم جواز السفر'][i]),str(file['الرقم الوطني'][i]),
                       str(file['رقم السيارة'][i]),file['البريد الالكتروني'][i],'0' + str(file['رقم الاتصال'][i]),
                       file['جواز السفر'][i],file['كلمة المرور'][i])
        pages.append(page)


async def execute(page,txtName,txtPassportNu,txtIDNumber,txtCarNumber,txtEmail,txtMobile,fileUpload2,password):
    try:
        input_file = await page.querySelector('[id=FileUpload2]')
        file_path = fileUpload2 + '.jpg'
        await input_file.uploadFile(file_path)
        await page.click('body > form > section > div > div > div > div > div > div > input.checkboxbtn')
        image_elements = await page.xpath('//img')
        image_urls = ""
        for image_element in image_elements:
          image_url = await (await image_element.getProperty('src')).jsonValue()
          image_urls = image_url
        s= ocr(image_urls)
        await page.type("#txtCaptcha", s)

        await page.click('body > form > section > div > div > div > div  > div > input.cbtn')
    except Exception:
        await openPage(page,txtName,txtPassportNu,txtIDNumber,txtCarNumber,txtEmail,txtMobile,fileUpload2,password)

    time.sleep(10)
    text = my_email(txtEmail,password)
    try:
        await page.type("#txtSMSCode", text)
    except Exception:
        await execute(page,txtName,txtPassportNu,txtIDNumber,txtCarNumber,txtEmail,txtMobile,fileUpload2,password)



async def submit():
    counter =1000
    while counter > 0:
        counter-=1
        for i in range(len(pages)):
            try:
                await pages[i].click('body > form > section > div > div > div > div > div > input.cbtn')
            except Exception:
                pass



async def start():
  while True:
    now = datetime.datetime.now()

    if (now.hour == 21 and  now.minute == 30) :
        await fill()
    elif(now.hour == 21 and now.minute == 0 ) :
        await submit()




async def main():
   await start()
   #print(ocr(r"C:\Users\Muhammad\Desktop\test\2.jpeg"))


asyncio.get_event_loop().run_until_complete(main())












