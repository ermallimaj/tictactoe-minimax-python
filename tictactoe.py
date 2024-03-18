from flask import Flask, render_template, jsonify, request, session
from game import Game
import json
import threading
import os

app = Flask(__name__)

# Generate a secret key for Flask sessions
app.secret_key = os.urandom(24)

games = {}

def handle_client_connection(client_socket, addr):
    try:
        while True:
            data = client_socket.recv(1024).decode('utf-8')
            if not data:
                break
            data = json.loads(data)
            game = games.get(addr)
            if not game:
                game = Game()
                games[addr] = game

            if 'board' in data:
                game.board = data['board']
            if 'player' in data:
                game.player = data['player']
            if 'computer' in data:
                game.computer = data['computer']

            if game.has_won(game.player):
                response = {'tied': False, 'computer_wins': False, 'player_wins': True, 'board': game.board}
            elif game.is_board_full():
                response = {'tied': True, 'computer_wins': False, 'player_wins': False, 'board': game.board}
            else:
                computer_move = game.calculate_move()
                game.make_computer_move(computer_move['row'], computer_move['col'])
                if game.has_won(game.computer):
                    response = {'computer_row': computer_move['row'], 'computer_col': computer_move['col'],
                                'computer_wins': True, 'player_wins': False, 'tied': False, 'board': game.board}
                elif game.is_board_full():
                    response = {'computer_row': computer_move['row'], 'computer_col': computer_move['col'],
                                'computer_wins': False, 'player_wins': False, 'tied': True, 'board': game.board}
                else:
                    response = {'computer_row': computer_move['row'], 'computer_col': computer_move['col'],
                                'computer_wins': False, 'player_wins': False, 'board': game.board}
            client_socket.send(json.dumps(response).encode('utf-8'))
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        client_socket.close()

@app.route('/')
def index():
    # Retrieve client IP address
    client_address = request.remote_addr
    client_port = request.environ.get('REMOTE_PORT')

    # Print user joined message
    print(f"User {client_address}:{client_port} joined.")
    return render_template('index.html')

@app.route('/move', methods=['POST'])
def move():
    post = request.get_json()
    player_name = post.get('player')
    difficulty = post.get('difficulty')
    # Get client address from session
    addr = session.get('client_address')  
    game = games.get(addr)
    if not game:
        game = Game(difficulty=difficulty)
        games[addr] = game

    if 'board' in post:
        game.board = post['board']
    if 'player' in post:
        game.player = post['player']
    if 'computer' in post:
        game.computer = post['computer']

    # Check if player won
    if game.has_won(game.player):
        return jsonify(tied=False, computer_wins=False, player_wins=True, board=game.board)
    elif game.is_board_full():
        return jsonify(tied=True, computer_wins=False, player_wins=False, board=game.board)

    # Calculate computer move
    computer_move = game.calculate_move()
    game.make_computer_move(computer_move['row'], computer_move['col'])

    if game.has_won(game.computer):
        return jsonify(computer_row=computer_move['row'], computer_col=computer_move['col'],
                       computer_wins=True, player_wins=False, tied=False, board=game.board)
    elif game.is_board_full():
        return jsonify(computer_row=computer_move['row'], computer_col=computer_move['col'],
                       computer_wins=False, player_wins=False, tied=True, board=game.board)

    return jsonify(computer_row=computer_move['row'], computer_col=computer_move['col'],
                   computer_wins=False, player_wins=False, board=game.board)

# Redirect to 404 page if the URL is invalid
@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404

def start_server():
    app.run(host='0.0.0.0')

if __name__ == '__main__':
    server_thread = threading.Thread(target=start_server)
    server_thread.start()
