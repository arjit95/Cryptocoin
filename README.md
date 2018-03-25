# Crypto Coin

A simple blockchain based wallet. The code is a python port of the awesome tutorial located [here](https://medium.com/programmers-blockchain/create-simple-blockchain-java-tutorial-from-scratch-6eeed3cb03fa) with some improvements.

It also features a small web interface to make transactions between 2 wallets. Currently there is no p2p support and mining is performed on the server itself. This implementation is just for educational purposes and is __not__ to be used in any real world use cases. 

## Dependencies:
- Python 3.x
- Flask (For running the webserver)

## Setup:
- Clone the repo using git.
- Install the above mentioned dependencies.
- Run the app with `python app.py`
- Open `127.0.0.1:8080` in your browser.

## Additional Notes:
- Whenever a new user is added he is credited with CC 50 to make any transactions.

- Information is updated every _1min_ for each transaction, because no fancy websockets are used.

- To increase the difficulty of the blockchain, set `BlockChain.difficulty = difficulty` in `app.js`

- For now there is no visual feedback for any user action performed on the web interface. Maybe that can be added at a later stage.

- Once logged in any other wallet id can be retrieved from anchor tag. This is meant for debugging purposes, so that you can login from that wallet id to check or transfer available funds.

- This repo is for educational purposes only and must not be used for any production environment.
