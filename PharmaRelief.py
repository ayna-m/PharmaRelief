import streamlit as st
import pymongo
import requests
import json
import pandas as pd
import datetime
import pyperclip

api_key = 'AIzaSyACaSZjgVJQ4H3kPFIlHE1A3YY7n5rv96w'

@st.cache_resource
@st.cache_data(ttl=600)

def get_data():
	client = pymongo.MongoClient(**st.secrets["mongo"])
	db = client.test
	pharmaDB = db.pharmacies.find()
	pharmaDB = list(pharmaDB)
	pharm_dict={}
	for item in pharmaDB:
		ID=str(item['_id'])
		pharm_dict[ID]={}
		pharm_dict[ID]["name"]=item['name']
		pharm_dict[ID]["location"]=item['location']
		pharm_dict[ID]["drugs"]={}
		for i in item["drugs"]:
			drug_ID=str(i["_id"])
			pharm_dict[ID]["drugs"][drug_ID]={}
			exp_lst=str(i["expirationDate"])[:10].split("-")
			exp_date=datetime.date(int(exp_lst[0]),int(exp_lst[1]), int(exp_lst[2]))
			today=datetime.date.today()
			days=(exp_date-today)
			day_num=int(str(days).split(" ")[0])
			if day_num<14:
				continue
			else:
				pharm_dict[ID]["drugs"][drug_ID]["name"]=i["name"]
				pharm_dict[ID]["drugs"][drug_ID]["dosage"]=i["dosage"]
				pharm_dict[ID]["drugs"][drug_ID]["days_until_expiry"]=day_num
	return pharm_dict
	


def get_dest_order(origin, pharm_dict, api_key):
	time = []

	destinations = []
	for key in pharm_dict.keys():
		destinations.append(pharm_dict[key]["location"])
	
	base_url = "https://maps.googleapis.com/maps/api/distancematrix/json"
	params = {
        "origins": origin,
        "destinations": "|".join(destinations),
        "key": api_key
    }
	try:
		response = requests.get(base_url, params=params)
		data = response.json()
		if data["status"] == "OK":
			rows = data["rows"][0]["elements"]
			distances = [row["distance"]["value"] for row in rows]
			sorted_destinations = [dest for _, dest in sorted(zip(distances, destinations))]
			return sorted_destinations
		else:
			print("Error: Unable to calculate distances.")
			return None
	except Exception as e:
		print(f"An error occurred: {str(e)}")
		return None


def filter_locations(drug, locations, pharmDB, dosage=None):
	pharm_dict={}
	for i in locations:
		for key in pharmDB.keys():
			if pharmDB[key]["location"]==i:
				for drug_key in pharmDB[key]["drugs"].keys():
					try:
						if drug.lower() in pharmDB[key]["drugs"][drug_key]["name"].lower():
							if dosage!=None:
								if dosage.lower() in pharmDB[key]["drugs"][drug_key]["dosage"].lower():
									pharm_dict[i]=pharmDB[key]["name"]
							else:
								pharm_dict[i]=pharmDB[key]["name"]
						else:
							pass
					except KeyError:
						pass

	return pharm_dict.values(), pharm_dict.keys()

def address_to_google_maps_link(address):
    address = address.replace(' ', '+')
    google_maps_link = f"https://www.google.com/maps/search/?q={address}"
    return google_maps_link

 
if "main" not in st.session_state:
	st.session_state.main=0
if "location" not in st.session_state:
	st.session_state.location = ""
if "drug" not in st.session_state:
	st.session_state.drug = ""
if "dosage" not in st.session_state:
	st.session_state.dosage = ""
if "pharmacies" not in st.session_state:
	st.session_state.pharmacies = []


def nextpage(): st.session_state.main += 1
def restart():	st.session_state.main = 0
def backpage():	st.session_state.main -=1


		

def main_page():
	st.title("Welcome to PharmaRelief!")
	st.subheader("Cennecting Sustainability and Accessability")
	st.write("Our purpose is increasing sustainability by reducing the pharmaceuitcal waste and increasing the accessibility of medicine for patients in financial need.")
	st.subheader("To start, please input: \n- Your location\n- Medicine name\n- Medicine dosage (optional)")
	text_placeholder1 = st.empty()
	text_placeholder2 = st.empty()
	text_placeholder3 = st.empty()
	location = text_placeholder1.text_input(label="Enter your location. Ex: 3700 O'Hara St, Pittsburgh, PA 15213", key="main_loc_input")
	drug = text_placeholder2.text_input(label = "Enter the drug name. Ex: Insulin", key="main_drug_input")
	dosage = text_placeholder3.text_input(label = "Enter the dosage (optional). Ex: 200mg", key="main_dosage_input")
	placeholder = st.empty()
	pharmDB=get_data()
	if location and drug:
		placeholder.success("Location and Drug name entered")
		st.session_state.location = location
		st.session_state.drug = drug
		st.session_state.dosage = dosage
		btn = placeholder.button("Search", key="main_search", on_click=nextpage, disabled=False)
		if btn:
			text_placeholder1.empty()
			text_placeholder2.empty()
			text_placeholder3.empty()
			placeholder.empty()

def results(text):
	user_location = st.session_state.location
	drug_name = st.session_state.drug
	dosage = st.session_state.dosage
	pharmDB=get_data()
	dest_list=get_dest_order(user_location, pharmDB, api_key)
	names, locations=filter_locations(drug_name, dest_list, pharmDB, dosage)
	if len(names)>0:
		placeholder = st.empty()
		placeholder.header("List of Pharmacies ordered by proximity to your location")
		col1, col2, col3 = st.columns(3, gap="large")
		links=[]
		for i in locations:
			links.append(address_to_google_maps_link(i))
			
		with col1:
			st.markdown('Names of Pharmacies. Hover over to copy')
			for n in names:
				nn = f'''{n}'''
				st.code(nn, language="python")
		with col2:
			st.markdown('Locations of Pharmacies. Hover over to copy')
			for l in locations:
				ll = f'''{l}'''
				st.code(ll, language="python")
		with col3:
			st.markdown('Links to Google Maps')
			for link in links:
				st.markdown(link)
	else:
		placeholder1= st.empty()
		placeholder1.header("Ooops! We could not find any pharmacies with the medication. Please try again with different medication or dosage!")
	
	placeholder2= st.empty()
	btn = placeholder2.button("Another Search", key="result_search", on_click=backpage, disabled=False)
	if btn:
		placeholder.empty()
		placeholder1.empty()
		placeholder2.empty()
		col1.empty()
		col2.empty()
		col3.empty()






def main():
	st.set_page_config(layout="wide")
	if st.session_state.main == 0:
		main_page()
	elif st.session_state.main == 1:
		results(st.session_state.location)

if __name__ == "__main__":
	main()
