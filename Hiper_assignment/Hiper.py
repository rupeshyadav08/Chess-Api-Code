import requests
import pandas as pd
import matplotlib.pyplot as plt
from statistics import median
import lichess.api
import berserk
import configparser

config = configparser.ConfigParser()
config.read('config.cfg')

API_TOKEN = config['APIDetails']['Api_token']
session = berserk.TokenSession(API_TOKEN)
client = berserk.Client(session=session)


class HiChessDataAnalyzer:
    def __init__(self, ):
        pass

    def fetch_user_details(self, user_count, game_type):
        """
           Fetch user details from the 'bullet' chess time control leaderboard using the berserk API.

           Parameters:
           - user_count (int): The number of users to fetch and include in the details.
           - game_type (str): The type of game for which you want the details.

           Returns:
           - pd.DataFrame: A DataFrame containing user details, including 'id', 'username',
           'rating', and 'title'.
           """
        # Fetch the leaderboard data for the 'bullet' chess time control
        leaderBoard = client.users.get_leaderboard(perf_type='bullet')

        # Create an empty DataFrame to store user details
        user_details = pd.DataFrame(columns=['id', 'username', 'rating', 'title'])

        # Loop through the specified number of users to gather details
        for i in range(user_count):
            detail_dict = {}
            detail_dict['id'] = leaderBoard[i]['id']
            detail_dict['username'] = leaderBoard[i]['username']
            prefs = leaderBoard[i]['perfs']
            detail_dict['rating'] = prefs['bullet']['rating']
            if 'title' in leaderBoard[i].keys():
                detail_dict['title'] = leaderBoard[i]['title']
            else:
                detail_dict['title'] = None
            # Convert the user details dictionary to a DataFrame
            detail_dict = pd.DataFrame([detail_dict])
            # Concatenate the current user's details to the overall DataFrame
            user_details = pd.concat([user_details, detail_dict], ignore_index=True)

        return user_details

    def users_detils_number_of_games(self, user_details, number_of_game):
        """
            Fetch and compile game details for a specified number of games played by users.

            Parameters:
            - user_details (pd.DataFrame): DataFrame containing user details with columns 'id', 'username', 'rating', and 'title'.
            - number_of_game (int): The number of games to fetch for each user.

            Returns:
            - pd.DataFrame: A DataFrame containing game details, including 'game_id', 'rated', 'variant', 'status',
              'winner_piece', 'moves', 'white_piece_player', 'black_piece_player', 'winner', and 'result'.
            """

        # Create an empty DataFrame to store game details
        game_details_df = pd.DataFrame(
            columns=['game_id', 'rated', 'variant', 'status', 'winner_piece', 'moves'])

        # Loop through each user in the provided user_details DataFrame
        for index, row in user_details.iterrows():
            # Fetch game details for the user using the lichess API
            game_details = lichess.api.user_games(row['username'])
            gen = game_details
            # Loop through the specified number of games (or until the generator is exhausted)
            for j in range(number_of_game):
                try:
                    game_dict = {}
                    data = next(gen)
                    # Extract relevant game details
                    game_dict['game_id'] = data['id']
                    game_dict['rated'] = data['rated']
                    game_dict['variant'] = data['variant']
                    game_dict['status'] = data['status']
                    game_dict['white_piece_player'] = data['players']['white']['user']['name']
                    game_dict['black_piece_player'] = data['players']['black']['user']['name']
                    game_dict['moves'] = data['moves'].split()
                    # Check for the winner and determine the result for the user
                    if 'winner' in data:
                        game_dict['winner'] = data['winner']
                    else:
                        game_dict['winner'] = None
                    winner = game_dict['winner']
                    black_piece_player = data['players']['black']['user']['name']
                    white_piece_player = data['players']['white']['user']['name']
                    if winner == 'black' and black_piece_player == row['username']:
                        game_dict['result'] = 'won'
                    elif winner == 'white' and white_piece_player == row['username']:
                        game_dict['result'] = 'won'
                    else:
                        game_dict['result'] = 'lost'
                    # Convert the user details dictionary to a DataFrame
                    game_dict = pd.DataFrame([game_dict])
                    # Concatenate the current user's details to the overall DataFrame
                    game_details_df = pd.concat([game_details_df, game_dict], ignore_index=True)
                except StopIteration:
                    break
        return game_details_df

    def win_percentage_with_color(self, user_game_details, colour):
        """
          Calculate the win percentage for players with the given color pieces in chess games.

          Parameters:
          - user_game_details (pd.DataFrame): DataFrame containing game details with columns
            'game_id', 'rated', 'variant', 'status', 'winner_piece', 'moves', 'white_piece_player', 'black_piece_player',
            'winner', and 'result'.
          - colour (str):  Colour of piece

          Returns:
          - pd.Series: A Series containing the win percentages for players with the given color piece pieces.
          """
        color_y = colour  # Change this to 'black' if needed
        filtered_df = user_game_details[user_game_details['winner'] == color_y]

        # Calculate the win percentage for each player
        win_counts = filtered_df['white_piece_player'].value_counts()
        total_games = user_game_details[user_game_details['white_piece_player'].isin(win_counts.index)][
                          'white_piece_player'].value_counts() + \
                      user_game_details[user_game_details['black_piece_player'].isin(win_counts.index)][
                          'black_piece_player'].value_counts()
        win_percentages = win_counts / total_games * 100

        # Choose the top 'x' players based on win percentage
        x = 5  # Change this to the desired number of top players
        top_players = win_percentages.nlargest(x)
        print('Top player by win percentage ')
        print(top_players)

    def first_move_e4(self, moves_data):
        """
            Filter and retrieve chess games where the first move is 'e4'.

            Parameters:
            - moves_data (pd.DataFrame): DataFrame containing game details with columns
              'game_id', 'rated', 'variant', 'status', 'winner_piece', 'moves', 'white_piece_player', 'black_piece_player',
              'winner', and 'result'.

            Returns:
            - pd.DataFrame: A DataFrame containing game details where the first move is 'e4'.
            """

        # Filter the DataFrame to include only games where the first move is 'e4'
        games_with_e4 = moves_data[moves_data['moves'].apply(lambda moves: len(moves) > 0 and
                                                                           moves[0] == 'e4')]
        print("Player made e4 as first move", len(games_with_e4))

    def median(self, moves_data):
        median_moves = moves_data['moves'].apply(len).median()

        # Print or use the result
        print(f"Median number of moves for all games: {median_moves}")

    def visualisation_to_show_distribution(self, user_game_details):
        # Assuming your DataFrame is named df

        # Calculate the number of moves for each game
        user_game_details['num_moves'] = user_game_details['moves'].apply(len)

        # Plot the distribution of the number of moves
        plt.figure(figsize=(10, 6))
        plt.hist(user_game_details['num_moves'], bins=20, color='skyblue', edgecolor='black')
        plt.title('Distribution of Number of Moves in Chess Games')
        plt.xlabel('Number of Moves')
        plt.ylabel('Frequency')
        plt.grid(axis='y', alpha=0.75)
        # Save the plot as an image (adjust the filename and format as needed)
        plt.savefig('Output/number_of_moves_distribution.png')
        plt.show()


if __name__ == "__main__":
    # Set the number of users, number of games, and chess category
    number_of_user = int(input('input number of user = '))
    number_of_games = int(input('number of games = '))
    category = input('category of game "example bullet" =  ')

    # Create an instance of the HiChessDataAnalyzer class
    game_class = HiChessDataAnalyzer()

    # Fetch user details for the specified number of users in the specified chess category
    user_details = game_class.fetch_user_details(number_of_user, category)
    print()
    # Fetch and compile game details for the specified number of games played by each user
    user_game_details = game_class.users_detils_number_of_games(user_details, number_of_games)

    # Save the user game details to a CSV file
    user_game_details.to_csv('Output/user_details.csv', index=False)
    print()
    # Calculate and display win percentage for users with the specified color (e.g., 'black')
    game_class.win_percentage_with_color(user_game_details, 'black')  # change the colour if you need
    print()

    # Filter and retrieve chess games where the first move is 'e4'
    game_class.first_move_e4(user_game_details)

    # Median of moves data
    game_class.median(user_game_details)
    print()

    # Create a visualization to show the distribution of the number of moves in chess games
    game_class.visualisation_to_show_distribution(user_game_details)
