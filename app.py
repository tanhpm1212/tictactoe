from flask_cors import CORS, cross_origin
from flask import Flask, jsonify, make_response
from threading import Thread
import requests
import json
import time
from TicTacToeAi import TicTacToeAI

app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

HOST = 'http://localhost:5000' # Địa chỉ server trọng tài
game_info = {}
stop_thread = False

ai = TicTacToeAI('X')

class GameClient:
    def __init__(self, server_url):
        self.server_url = server_url
        self.match_id = None
        self.board = None
        self.team_id = None
        self.init = None
        self.size = None
        self.ai = None
    
    def listen(self):
        # Lắng nghe yêu cầu từ server trọng tài
        # và cập nhật thông tin trò chơi
        while not stop_thread:
            time.sleep(3)
            print(self.init)
            if not self.init:
                response = requests.get(self.server_url + "/init")
            else:
                response = requests.post(self.server_url)
            
            data = json.loads(response.content)
            global game_info
            game_info = data.copy()

            if data.get("init"):
                #có thể input game match_id
                self.init = True
                print("Connection established")
                print(data)
                self.team_id = "xx1"       
                self.init = True      
                self.send_game_info()
                
            elif data.get("board"):
                # Kiểm tra nước đi hợp lệ trước khi gửi yêu cầu
                if data.get("turn") == self.team_id:
                    self.size = int(data.get("size"))   
                    self.board = data["board"]
                    move = ai.get_move(data.get("board"), data.get("size"))
                    print("Move: ", move)
                    valid_move = self.check_valid_move(move)
                    if valid_move:
                        self.board[int(move[0]) * self.size + int(move[1])] = "X"
                        self.send_move()
                    else:
                        print("Invalid move")
                    
            elif data.get("status"):
                print("Game over")
                break
        
    def send_game_info(self):
        headers = {"Content-Type": "application/json"}
        requests.post(self.server_url, json=game_info, headers=headers)
    
    def send_move(self):
        #Gửi nước đi đến server trọng tài
        move_info = {
            "match_id": self.match_id,
            "board": self.board
        }
        headers = {"Content-Type": "application/json"}
        requests.post(self.server_url, json=move_info, headers=headers)
    
    def check_valid_move(self, new_move_pos):
        # Kiểm tra nước đi hợp lệ
        # Điều kiện đơn giản là ô trống mới có thể đánh vào
        i, j  = int(new_move_pos[0]), int(new_move_pos[1])
        
        if self.board[i*self.size + j][0] == " ":
            return True
        return False

@app.route('/')
@cross_origin()
def get_data():
    global game_info
    response = make_response(jsonify(game_info))
    return response


if __name__ == "__main__":
    # HOST = input("Enter server url: ")
    gameClient = GameClient(HOST)
    game_thread = Thread(target=gameClient.listen)
    game_thread.start()
    # gameClient.listen()
    # print('hello')
    app.run(host="0.0.0.0", port="3005")    
    try:
        while game_thread.is_alive():
            game_thread.join(1)
    except KeyboardInterrupt:
        stop_thread = True
        game_thread.join()
        print("Game client stopped")


    