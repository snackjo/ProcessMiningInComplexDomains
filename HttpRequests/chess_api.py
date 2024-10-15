import requests


class ChessAPI:
    def __init__(self, player, year, month):
        self.player = player
        self.year = year
        self.month = month
        self.base_url = "https://api.chess.com/pub/player/{}/games/{}/{}/pgn"

    def get_games(self) -> str:
        url = self.base_url.format(self.player, self.year, self.month)
        headers = {
            'User-Agent': 'ChessAPIClient/1.0 (Python; contact: carlj0908@gmail.com)'
        }
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return response.text
        except requests.exceptions.RequestException as e:
            print(f"Error fetching data: {e}")
