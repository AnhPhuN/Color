from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium import webdriver

from flask import Flask, render_template, request
import os
import requests
import json
import re
from PIL import Image
import pyheif


# $ git add .
# $ git commit -am "make it better"
# $ git push heroku master
# $ heroku git:clone -a anhphu



# Configure application
app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        fileupload = request.files['file']

        def filesubmitted():
            fileuploadname = fileupload.filename

            # check if HEIC or JPEG
            if fileuploadname.endswith(".HEIC") or fileuploadname.endswith(".heic"):

                filename = "file.jpeg"

                heif_file = pyheif.read(fileupload)
                image = Image.frombytes(
                    heif_file.mode, 
                    heif_file.size, 
                    heif_file.data,
                    "raw",
                    heif_file.mode,
                    heif_file.stride,
                    )
                image.save(filename, format="JPEG", optimize=True, quality=50)
            else:
                filename = fileupload.filename
                image = Image.open(fileupload)
                if filename != '':
                    image.save(filename, optimize=True, quality=50)

            #filehandler function takes in the name of an image file, and returns the barcode and accession number
            def filehandler(filename):


                payload = {'isOverlayRequired': True,
                'apikey': 'e080d39d5d88957',
                'language': 'eng',
                'OCREngine': 2,
                }

                with open(filename, 'rb') as f:
                    r = requests.post('https://api.ocr.space/parse/image',
                                        files={filename: f},
                                        data=payload,
                                        )
                m = r.content.decode()
                # get json from OCR
                jsonstr = json.loads(m)
                # get barcode and accession 
                try:
                    text = jsonstr["ParsedResults"][0]["ParsedText"]
                    posacc = text.find('C-')
                    posbar = text.find('D-')

                    if posbar == -1 or posacc == -1:
                        rotated = image.rotate(270)
                        rotated.save(filename)
                        text = filehandler(filename)
                    return text
                except:
                    return render_template("message.html", title = "OCR error", message = "OCR API did not return text. please try again or try again later.")

            text = filehandler(filename)
            # remove file
            os.remove(filename)

            posacc = text.find('C-')
            posbar = text.find('D-')
            if posbar == -1 or posacc == -1:
                return render_template("message.html", title = "Image Error", message = "Accession number or Barcode could not successfully be found. Please try again with new picture. \n OCR could be down, try inputting values manually")

            accession = text[posacc + 2:posacc + 7]
            barcode = text[posbar + 2:posbar + 12]

            try:
                int(accession)
            except:
                return render_template("message.html", title = "Image Error", message = "Accession number could not successfully be found. Please try again with new picture.")
            try:
                int(barcode)
            except:
                return render_template("message.html", title = "Image Error", message = "Barcode number could not successfully be found. Please try again with new picture.")
            return barcode, accession

        # check if fileupload was submitted. takes precedence over manual input
        if fileupload.filename != '':
            baracc = filesubmitted()
            barcode = baracc[0]
            accession = baracc[1]
        else:
            barcode = request.form.get("barcode")
            accession = request.form.get("accession")
        


        if not barcode or not accession:
            return render_template("message.html", title = "Input Error", message = "Must upload an image or fill out barcode or accession")

        if len(str(barcode)) != 10:
            return render_template("message.html", title = "Input Error", message = "barcode must be 10 digits long")  

        if len(str(accession)) != 5:
            return render_template("message.html", title = "Input Error", message = "accession must be 5 digits long")

        #check email validity
        regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        if not (re.fullmatch(regex, email)):
            return render_template("message.html", title = "Input Error", message = "email is invalid")

        # when all info has been verified, run automator:   
        driver = webdriver.Chrome()
        
        # chrome_options = webdriver.ChromeOptions()
        # chrome_options.binary_location = os.environ.get("GOOGLE_CHROME_BIN")
        # chrome_options.add_argument("--headless")
        # chrome_options.add_argument("--disable-dev-shm-usage")
        # chrome_options.add_argument("--no-sandbox")
        # driver = webdriver.Chrome(executable_path=os.environ.get("CHROMEDRIVER_PATH"), chrome_options=chrome_options)

        # get website
        driver.get("https://home.color.com/covid/activation")
        element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "onetrust-accept-btn-handler"))
            )

        driver.find_element(By.ID, "onetrust-accept-btn-handler").click()

        driver.find_element(By.CLASS_NAME, "MuiButtonBase-root").click()

        element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "password-id"))
            )


        # get element 
        element = driver.find_element(By.ID, "email-id")
        element.click()
        # send keys 
        element.send_keys(email)

        #get pass
        password1 = driver.find_element(By.ID, "password-id")
        password1.click()

        # send keys 
        password1.send_keys(password)

        #sign in
        driver.find_element(By.CLASS_NAME, "MuiButtonBase-root").click()
        print("HERE2")
        try: 
            element = WebDriverWait(driver, 4).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "MuiButton-outlinedPrimary")))
        except TimeoutException:
            return render_template("message.html", title = "Sign In Error", message = "Could not sign into Color. Please try again and check your email and password")
        person = driver.find_element(By.CLASS_NAME, "MuiButton-outlinedPrimary").click()

        print("HERE1")
        element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//*[text()='Harvard']"))
        )
        program = driver.find_element(By.XPATH, "//*[text()='Harvard']").click()

        element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "MuiButton-containedPrimary"))
        )

        activate = driver.find_element(By.CLASS_NAME, "MuiButton-containedPrimary").click()

        element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//*[text()='Start Survey']"))
        )
        print("HERE")
        startsurvey = driver.find_element(By.CLASS_NAME, "MuiButton-root").click()

        element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//*[@data-testid='No']")))


        no = driver.find_element(By.XPATH, "//*[@data-testid='No']").click()

        submit = driver.find_element(By.XPATH, "//*[@data-testid='SubmitQuizAnswerButton']").click()


        #checkmarks:
        element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "additionalConsents[2]-id")))

        check2 = driver.find_elements(By.XPATH, "//*[@type='checkbox']")
        for i in range(4):
            check2[i].click()

        submit1 = driver.find_element(By.XPATH, "//*[@type='submit']")
        submit1.click()

        wait = WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.XPATH, "//*[text()='Samoan']")))

        submit2 = driver.find_element(By.XPATH, "//*[@type='submit']")
        submit2.click()

        waitconfirm = WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.XPATH, "//*[text()='Please confirm that this information is correct.']")))

        confirmcont = driver.find_element(By.XPATH, "//*[@data-testid='TwoButtonDialogPrimary']").click()


        barcodehtml = driver.find_element(By.ID, "CovidBarcodeField")
        barcodehtml.click()
        barcodehtml.send_keys(barcode)

        accessionhtml = driver.find_element(By.ID, "AccessionNumberField")
        accessionhtml.click()
        accessionhtml.send_keys(accession)

        submit3 = driver.find_element(By.XPATH, "//*[@data-testid='submit-sample-identifier-form-button']").click()

        confirm1 = driver.find_element(By.XPATH, "//*[@data-testid='TwoButtonDialogPrimary']").click()

 

        try: 
            element = WebDriverWait(driver, 4).until(
                    EC.presence_of_element_located((By.XPATH, "//*[text()='You’ve activated your kit! Now, collect a sample.']")))
        except TimeoutException:
            message = "Your Barcode: {} or Accession Number: {} is incorrect. Please retry the form and check your values are correct.".format(barcode, accession)
            return render_template("message.html", title = "Barcode/Accession Invalid", message = message)

        return render_template("message.html", title = "Form Complete", message = "Your kit activation is all done! :) Please make sure to confirm the activation email from Color arrives.")

    else:
        return render_template("index.html")