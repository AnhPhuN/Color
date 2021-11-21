from flask import Flask, redirect, render_template, request
from backbone import selenium


# Configure application
app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        email = "anhphunguyen5@gmail.com"
        password = "mirqo7-vyxreg-haHrut"
        # email = request.form.get("username")
        # password = request.form.get("password")
        barcode = request.form.get("barcode")
        accession = request.form.get("accession")
        error = selenium(email, password, barcode, accession)
        if not error or error != "finished": 
            return render_template("apology.html", error_message = error)
        else:
            return redirect("/")
 
    else:
        return render_template("index.html")