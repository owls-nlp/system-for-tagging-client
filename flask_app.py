from flask import Flask, render_template, url_for, request, send_from_directory, make_response
import os, json, requests as api_req
from werkzeug.utils import secure_filename
from gevent.pywsgi import WSGIServer

app = Flask(__name__)

with open('client_config.json', 'r') as f:
    config = json.load(f)

URL = config['URL_server']
RESULT_FOLDER = './output/'
TOKEN_MAX_AGE = 60*60*24*365
FILE_MAX_AGE = 60*60*24*365
ERROR = 'Вы выбрали неверный формат файла, пожалуйста, повторите загрузку.'
ERROR_TOKEN = 'Этот токен не существует, пожалуйста, проверьте ваш токен или свяжитесь с администратором системы.'

app.config['RESULT_FOLDER'] = RESULT_FOLDER
app.config['TOKEN_MAX_AGE'] = TOKEN_MAX_AGE
app.config['FILE_MAX_AGE'] = FILE_MAX_AGE

APP_ROOT = os.path.dirname(os.path.abspath(__file__))


def transliterate(text):
    translate = "a b v g d e yo zh z i y k l m n o p \
                 r s t u f h ts ch sh shch y y ' e yu ya"
    # lower chars
    dic = { chr(ru):translate for ru, translate in zip( \
        list(range(1072, 1078)) + [1105] + list(range(1078, 1104)), translate.split()) }
 
    # upper chars
    dic.update({ chr(ru):translate for ru, translate in zip( \
        list(range(1040, 1046)) + [1025] + list(range(1046, 1072)), translate.title().split()) })
 
    new_text = ''
    for char in text:
        if char in dic:
            new_text += dic[char]
        else:
            new_text += char
 
    return new_text

@app.route("/")
def index():
    if not request.cookies.get('token_name'):
        return render_template('setcookie.html')
    else:
        return render_template('home.html')

@app.route('/setcookie', methods = ['POST', 'GET'])
def setcookie():
    if request.method == 'POST':
        token = request.form['token'] 
        ans = api_req.post(f'{URL}verifytoken', data={'token': token}, verify='store.ca-bundle')
        if ans.text == 'YES':
            resp = make_response(render_template('home.html'))
            resp.set_cookie('token_name', token, max_age=app.config['TOKEN_MAX_AGE'])
            return resp
        else:
            return render_template('setcookie.html', error = ERROR_TOKEN) 
    else:
        if request.cookies.get('token_name'):
            return render_template('home.html')
        else:
            return render_template('setcookie.html')           

@app.route("/deletecookie")
def deletecookie():
    if request.cookies.get('token_name'):
        token = request.cookies.get('token_name')
        resp = make_response(render_template('setcookie.html'))
        resp.set_cookie('token_name', token, max_age=0)   
        return resp
    else:
        return render_template('setcookie.html')

@app.route("/home")
def home():
    if not request.cookies.get('token_name'):
        return render_template('setcookie.html')
    else:
        return render_template('home.html')

@app.route("/about")
def about():
    return render_template('about.html')

@app.route("/contacts")
def contacts():
    return render_template('contacts.html')

@app.route("/loaded", methods=["POST", "GET"])
def loaded(): 
    if not request.cookies.get('token_name'):
        return render_template('setcookie.html')
    else:
        token = request.cookies.get('token_name')
        if request.method == 'POST':        
            target = os.path.join(APP_ROOT, 'files/')
            if not os.path.isdir(target):
                os.mkdir(target)
            for upload in request.files.getlist("file"):
                filename = secure_filename(transliterate(upload.filename))
                ext = filename.split('.')[-1]
                if (ext != "pdf"):
                    return render_template('home.html', error=ERROR, section='section')
                destination = "/".join([target, filename])
                upload.save(destination) 

            format_layout = request.form['format']
            if format_layout == 'format_1':
                column_type = 0
            elif format_layout == 'format_2':
                column_type = 1
            else:
                column_type = 2   

            file_type = request.form['file_type']
            if file_type == 'scan':
                file_type = 0
            else:
                file_type = 2                
            
            simple_data = { 'column_type': column_type, 'langs': 'rus+eng+lat', 'file_type': file_type}      
            files = {'file': open(destination,'rb')}            
            file_id = api_req.post(URL, files=files, data=simple_data, headers={'Authorization': token}, verify='store.ca-bundle')
            file_id = int(file_id.text)        
            resp = make_response(render_template('loaded.html'))
            resp.set_cookie('file_id', value=str(file_id), max_age=app.config['FILE_MAX_AGE'])
            return resp 
        else:        
            file_id = int(request.cookies.get('file_id'))
            url_isfileready = f'{URL}isfileready/{file_id}'
            file_ready = api_req.post(url_isfileready, files=None, data=None, headers={'Authorization': token}, verify='store.ca-bundle')
            file_ready = file_ready.text      
            if file_ready == 'YES':
                url_getfilename = f'{URL}getfilename/{file_id}'
                file_name = api_req.post(url_getfilename, files=None, data=None, headers={'Authorization': token}, verify='store.ca-bundle')
                file_name = file_name.text           
                url_download = f'{URL}download/{file_id}'
                file = api_req.post(url_download, files=None, data=None, headers={'Authorization': token}, stream=True, verify='store.ca-bundle')
                with open(app.config['RESULT_FOLDER'] + file_name, 'wb') as fd:
                    for chunk in file.iter_content(chunk_size=128):
                        fd.write(chunk)
                return send_from_directory(app.config['RESULT_FOLDER'], file_name, as_attachment=True, mimetype='application/zip')  
            else:
                return render_template('loaded.html')

if __name__ == '__main__':
    app.config["SECRET_KEY"] = 'o)zredhb@u97m)53wx_$j7(h*%_u3-x58zpsxw_fjnjr1n9g'
    http_server = WSGIServer(('0.0.0.0', 443), app, keyfile='key.pem', certfile='cert.pem')
    http_server.serve_forever()