from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
import qrcode
import socket
import random
import os


app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'

roomList = {}
userRoom = {}

app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100 MB

socketio = SocketIO(app, max_http_buffer_size=100 * 1024 * 1024)  # 100 MB for HTTP

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/receive')
def receive():
    return render_template('receive.html')

@app.route('/about')
def about():
    return render_template('aboutu.html')

@app.route('/project')
def project():
    return render_template('Aboutpro.html')

@app.route('/support')
def support():
    return render_template('Support.html')

@socketio.on('connect')
def handle_connect():
    referer_url = request.headers.get('Referer')
    url=referer_url.split(":")
    newurl=url[0]+":"+url[1]
    print(referer_url)
    print(newurl)
    roomId = ""
    if(referer_url.startswith(newurl+":5000/?id=")):
        roomId = referer_url.split("=")[1]
        roomList[roomId].append(request.sid)
        emit("x",roomId,to=roomList[roomId][0])
    elif(referer_url== (newurl+":5000/")):
        roomId = generate_random_16_digit_number()
        url_to_qrcode(get_server_ip()+":5000/?id="+roomId,roomId)
        userRoom[request.sid] = roomId
        roomList[roomId] = list([request.sid])
        emit("qr_code",roomId)
    print(roomList)
    emit('connected', {'message': 'Connected to the server! ', "roomId":roomId})

@socketio.on('send_file')
def handle_send_file(data):
    print(data["roomId"])
    for id in roomList[data["roomId"]]:
        if(id != request.sid):
            emit('receive_file', data, to=id)
        else:
            emit("sent-done")


@socketio.on("disconnect")
def handle_disconnect():
    curId = request.sid
    roomId = userRoom[curId]
    roomList.pop(roomId)
    userRoom.pop(curId)
    file_path = './static/'+roomId+'.png'
    os.remove(file_path)


# Helper Funtions
def url_to_qrcode(url, roomId):
    """
    Converts a URL into a QR code and saves it as an image.

    :param url: The URL to convert into a QR code.
    :param filename: The filename for the generated QR code image (default is 'qrcode.png').
    :return: None
    """
    # filename='./static/qr.png'
    filename='./static/'+roomId+'.png'

    # Generate the QR code
    qr = qrcode.QRCode(
        version=1,  # Controls the size of the QR Code (1 is for the smallest size)
        error_correction=qrcode.constants.ERROR_CORRECT_L,  # Error correction level
        box_size=10,  # Size of each box
        border=4,  # Thickness of the border
    )
    
    # Add data to the QR code
    qr.add_data(url)
    qr.make(fit=True)

    # Create an image from the QR code
    img = qr.make_image(fill='black', back_color='white')

    # Save the image
    img.save(filename)

    print(f"QR code generated and saved as {filename}")


def get_server_ip():
    """Get the server's IP address."""
    hostname = socket.gethostname()
    print("hostname:"+hostname)
    server_ip = socket.gethostbyname(hostname)
    return server_ip

def generate_random_16_digit_number():
    # Generate a random number between 10^15 and 10^16 - 1
    return str(random.randint(10**15, 10**16 - 1))


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)
