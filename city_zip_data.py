import argparse
from uszipcode import SearchEngine
import requests
import pandas as pd
from math import radians, sin, cos, sqrt, atan2
import os

def city_zip_coordinates(city, state):
  search = SearchEngine()
  result = search.by_city_and_state(city, state,returns=1000)
  zip_codes_info = [{"zipcode": zipcode.zipcode, "latitude": zipcode.lat, "longitude": zipcode.lng} for zipcode in result]

  return pd.DataFrame(zip_codes_info)

def haversine_distance(lat1, lon1, lat2, lon2):
    # Convert latitude and longitude from degrees to radians
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

    # Haversine formula
    d_lat = lat2 - lat1
    d_lon = lon2 - lon1
    a = sin(d_lat/2)**2 + cos(lat1) * cos(lat2) * sin(d_lon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))

    # Earth's radius in meters
    R = 6371000

    # Calculate the distance in meters
    distance = R * c
    return distance

def get_nearest_places(place_type,latitude, longitude,google_maps_api_key):
    url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    params = {
        "key": google_maps_api_key,
        "location": f"{latitude},{longitude}",
        "radius": 2000,  # 2km radius. Hard coded for now. Deal with it.
        "types": place_type,
        "keyword": place_type.replace("_"," ")
    }

    response = requests.get(url, params=params)
    data = response.json()
    results = data.get("results", [])

    places_with_coordinates = []
    for place in results:
        place_name = place["name"]
        place_latitude = place["geometry"]["location"]["lat"]
        place_longitude = place["geometry"]["location"]["lng"]

        places_with_coordinates.append({
            "place_type":place_type,
            "name": place_name,
            f"{place_type.split('_')[0]}_latitude": place_latitude,
            f"{place_type.split('_')[0]}_longitude": place_longitude,
            "distance": haversine_distance(latitude,longitude, place_latitude, place_longitude),
            "source_latitude": latitude,
            "source_longitude": longitude
        })
    # Ensure that the DataFrame always has the required columns
    if not places_with_coordinates:
        places_with_coordinates.append({
            "place_type": place_type,
            "name": None,
            f"{place_type.split('_')[0]}_latitude": None,
            f"{place_type.split('_')[0]}_longitude": None,
            "distance": None,
            "source_latitude": latitude,
            "source_longitude": longitude
        })
    return pd.DataFrame(places_with_coordinates)


def ycg_zip(city, state,google_maps_api_key):
  ygc_dict = {state: {city:{}}}
  zip_df = city_zip_coordinates(city, state)
  for row in zip_df.to_dict(orient="records"):
    zipcode = row["zipcode"]
    latitude = row["latitude"]
    longitude = row["longitude"]
    ygc_dict[state][city][zipcode] = {
        "yoga": get_nearest_places("yoga_studio", latitude, longitude, google_maps_api_key),
        "coffee": get_nearest_places("cafe", latitude, longitude, google_maps_api_key),
        "grocery": get_nearest_places("grocery_or_supermarket", latitude, longitude, google_maps_api_key)
    }
     
  return ygc_dict

def data2dir(data_dir, ycg_data):
    for state, cities in ycg_data.items():
        state_dir = os.path.join(data_dir, state)
        
        if not os.path.exists(state_dir):
            os.makedirs(state_dir)
            
        for city, zips in cities.items():
            city_dir = os.path.join(state_dir, city)
            
            if not os.path.exists(city_dir):
                os.makedirs(city_dir)
            
            for zipcode, dfs in zips.items():
                zip_dir = os.path.join(city_dir, zipcode)
                
                if not os.path.exists(zip_dir):
                    os.makedirs(zip_dir)                
                for place_type, df in dfs.items():
                    csv_path = os.path.join(zip_dir, f'{place_type}.csv')
                    if not os.path.exists(csv_path):
                        df.to_csv(csv_path, index=False,columns=df.columns)



def dir2data(data_dir):
    data_dict = {}
    
    for state in os.listdir(data_dir):
        state_dir = os.path.join(data_dir, state)
        
        if os.path.isdir(state_dir):
            data_dict[state] = {}
            
            for city in os.listdir(state_dir):
                city_dir = os.path.join(state_dir, city)
                
                if os.path.isdir(city_dir):
                    data_dict[state][city] = {}
                    
                    for zipcode in os.listdir(city_dir):
                        zip_dir = os.path.join(city_dir, zipcode)
                        if os.path.isdir(zip_dir):
                            data_dict[state][city][zipcode] = {}
                            
                            for label in ['yoga', 'coffee', 'grocery']:
                                csv_path = os.path.join(zip_dir, f'{label}.csv')
                                
                                if os.path.exists(csv_path):
                                    df = pd.read_csv(csv_path)
                                    data_dict[state][city][zipcode][label] = df
                                    
    return data_dict




def main():
    parser = argparse.ArgumentParser(description="Run ycg_zip function with Google Maps API key")
    parser.add_argument("api_key", help="Google Maps API key")

    args = parser.parse_args()
    # Load existing data from the data directory
    existing_data = dir2data("data")

    # Read cities.csv
    cities_df = pd.read_csv('cities.csv')

    # Initialize data_dict for new cities
    new_data_dict = {}

    # Iterate through cities in cities.csv
    for index, row in cities_df.iterrows():
        state = row['state']
        city = row['city']

        if state not in new_data_dict:
            new_data_dict[state] = {}

        if city not in existing_data.get(state, {}):
            new_data_dict = ycg_zip(city, state, args.api_key)
            data2dir("data",new_data_dict)

    # Merge new_data_dict with existing_data
    # for state, cities in new_data_dict.items():
    #     if state not in existing_data:
    #         existing_data[state] = {}

    #     for city, zips in cities.items():
    #         if city not in existing_data[state]:
    #             existing_data[state][city] = {}

    #         existing_data[state][city].update(zips)

    # Save the updated data using data2dir
    # data2dir("data",existing_data)




if __name__ == "__main__":
    main()