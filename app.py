from flask_cors import CORS, cross_origin
from flask import Flask, jsonify, make_response, request
from threading import Thread
import requests
import json
import time, copy
from TicTacToeAi import TicTacToeAI

app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

HOST = 'http://localhost:5000'  # Địa chỉ server trọng tài
game_info = {}  # Thông tin trò chơi để hiển thị trên giao diện
move_info = {}  # Thông tin nước đi để gửi đến server trọng tài
stop_thread = False  # Biến dùng để dừng thread lắng nghe

ai = TicTacToeAI('X')  # Khởi tạo AI chạy mặc định với đội X

class GameClient:
    def __init__(self, server_url, team_id):
        self.server_url = server_url
        self.match_id = None
        self.board = None
        self.team_id = team_id
        self.init = None
        self.size = None
        self.ai = None

    def listen(self):
        # Lắng nghe yêu cầu từ server trọng tài
        # và cập nhật thông tin trò chơi
        while not stop_thread:
            # Thời gian lắng nghe giữa các lần
            time.sleep(3)

            if game_info.get("room_id") == None:
                continue

            print(self.init)

            # Nếu chưa kết nối thì gửi yêu cầu kết nối
            if not self.init:
                response = self.send_init()
            else:
                response = requests.post(self.server_url)

            # Lấy thông tin trò chơi từ server trọng tài và cập nhật vào game_info
            data = json.loads(response.content)
            global game_info
            game_info = data.copy()

            # Khởi tạo trò chơi
            if data.get("init"):
                self.init = True
                print("Connection established")
                print(data)
                self.team_id = "xx1"
                self.init = True
                self.send_game_info()

            # Nhận thông tin trò chơi
            elif data.get("board"):
                # Nếu là lượt đi của đội của mình thì gửi nước đi
                if data.get("turn") == self.team_id:
                    self.size = int(data.get("size"))
                    self.board = copy.deepcopy(data.get("board"))
                    # Lấy nước đi từ AI, nước đi là một tuple (i, j)
                    move = ai.get_move(self.board, self.size)
                    print("Move: ", move)
                    # Kiểm tra nước đi hợp lệ
                    valid_move = self.check_valid_move(move)
                    # Nếu hợp lệ thì gửi nước đi
                    if valid_move:
                        self.board[int(move[0]) * self.size + int(move[1])][0] = "X"
                        self.send_move()
                    else:
                        print("Invalid move")

            # Kết thúc trò chơi
            elif data.get("status"):
                print("Game over")
                break

    # Gửi thông tin trò chơi đến server trọng tài
    def send_game_info(self):
        headers = {"Content-Type": "application/json"}
        requests.post(self.server_url, json=game_info, headers=headers)

    def send_move(self):
        # Gửi nước đi đến server trọng tài
        move_info = {
            "match_id": self.match_id,
            "board": self.board
        }
        headers = {"Content-Type": "application/json"}
        requests.post(self.server_url + "/move", json=move_info, headers=headers)

    def send_init(self):
        # Gửi yêu cầu kết nối đến server trọng tài
        init_info = {
            "room_id": game_info.get("room_id"),
            "team_id": self.team_id,
            "init": True
        }
        headers = {"Content-Type": "application/json"}
        return requests.post(self.server_url + "/init", json=init_info, headers=headers)
    
    def fetch_game_info(self):
        # Lấy thông tin trò chơi từ server trọng tài
        response = requests.post(self.server_url)
        data = json.loads(response.content)
        global game_info
        game_info = data.copy()

    def check_valid_move(self, new_move_pos):
        # Kiểm tra nước đi hợp lệ
        # Điều kiện đơn giản là ô trống mới có thể đánh vào
        i, j = int(new_move_pos[0]), int(new_move_pos[1])

        if self.board[i * self.size + j][0] == " ":
            return True
        return False


# API trả về thông tin trò chơi cho frontend
@app.route('/')
@cross_origin()
def get_data():
    print(game_info)
    response = make_response(jsonify(game_info))
    return response

@app.route('/init')
@cross_origin
def init():
    data = request.data
    game_info.update(json.loads(data.decode('utf-8')))
    response = make_response(jsonify(game_info))
    return response


if __name__ == "__main__":
    # Lấy địa chỉ server trọng tài từ người dùng
    host = input("Enter server url: ")
    team_id = input("Enter team id: ")

    # Khởi tạo game client
    gameClient = GameClient(host, team_id)
    game_thread = Thread(target=gameClient.listen)
    game_thread.start()
    app.run(host="0.0.0.0", port="3005")
    try:
        while game_thread.is_alive():
            game_thread.join(1)
    except KeyboardInterrupt:
        stop_thread = True
        game_thread.join()
        print("Game client stopped")
