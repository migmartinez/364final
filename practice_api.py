from igdb_api_python.igdb import igdb
import time, os
import requests, json

igdb = igdb('a062d7e1124df2be5e3847535974b8cc')


## Based on a user's input to a form, this function will be invoked which will return input data on video games that are related to the same search term that the user enters. This data will be saved in the games.db table. Sample inputs include: Call of Duty, Fortnite, and Super Mario Galaxy.
def get_games_name():
	game_inp = input("Input a game to add to your list: ")
	result = igdb.games({
		'search': game_inp,
		'fields': 'name'
		})
	for game in result.body:
		print(game["name"])

def get_games_all():
	game_inp = input("Input a game to add to your list: ")
	result = igdb.games({
		'search': game_inp,
		'fields': 'name'
		})
	print(result.body)

if __name__ == "__main__":
	get_games()