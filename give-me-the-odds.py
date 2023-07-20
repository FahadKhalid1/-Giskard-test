import flask
from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import json
from collections import defaultdict, deque
import heapq


def load_json_file(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)

def shortest_path(routes, start, end):
    # Implementing Dijkstra's algorithm
    queue, distances = [(0, start, [])], {start: 0}
    while queue:
        (distance, node, path) = heapq.heappop(queue)
        if distance != distances[node]:
            continue
        path = path + [node]
        if node == end:
            return (distance, path)
        for neighbor, distance_to_neighbor in routes[node].items():
            old_distance = distances.get(neighbor, None)
            new_distance = distances[node] + distance_to_neighbor
            if old_distance is None or new_distance < old_distance:
                distances[neighbor] = new_distance
                heapq.heappush(queue, (new_distance, neighbor, path))
    return None

def calculate_odds(millennium_data, empire_data):
    autonomy = millennium_data['autonomy']
    departure = millennium_data['departure']
    arrival = millennium_data['arrival']
    routes_db = millennium_data['routes_db']
    countdown = empire_data['countdown']
    bounty_hunters = {bh['planet']: bh['day'] for bh in empire_data['bounty_hunters']}

    # Load routes from db
    conn = sqlite3.connect(routes_db)
    cursor = conn.cursor()
    routes = defaultdict(dict)
    for origin, destination, travel_time in cursor.execute("SELECT ORIGIN, DESTINATION, TRAVEL_TIME FROM ROUTES"):
        routes[origin][destination] = travel_time
        routes[destination][origin] = travel_time
    cursor.close()
    conn.close()

    # Simulate the journey
    journey_length, path = shortest_path(routes, departure, arrival)
    current_day = 0
    current_planet = departure
    fuel = autonomy
    capture_attempts = 0
    for planet in path[1:]:
        # Refuel if necessary
        while fuel < routes[current_planet][planet]:
            current_day += 1
            fuel = autonomy
            if bounty_hunters.get(current_planet, -1) == current_day:
                capture_attempts += 1
        # Travel
        current_day += routes[current_planet][planet]
        fuel -= routes[current_planet][planet]
        current_planet = planet
        if bounty_hunters.get(current_planet, -1) == current_day:
            capture_attempts += 1
    # Fail if we don't make it in time
    if current_day > countdown:
        return 0

    # Calculate capture probability
    capture_probability = 1.0 - (9 / 10) ** capture_attempts
    success_probability = 1 - capture_probability

    return round(success_probability * 100, 2)

def main():
    if len(sys.argv) != 3:
        print("Usage: give-me-the-odds <millennium_falcon_file_path> <empire_file_path>")
        return

    millennium_falcon_file_path = sys.argv[1]
    empire_file_path = sys.argv[2]

    millennium_data = load_json_file(millennium_falcon_file_path)
    empire_data = load_json_file(empire_file_path)

    odds = calculate_odds(millennium_data, empire_data)
    print(odds)

if __name__ == '__main__':
    main()