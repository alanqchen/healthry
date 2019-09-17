import copy
import requests, json, csv
from flask import Flask, redirect, render_template, request
app = Flask(__name__)

response = requests.get("https://data.medicare.gov/resource/rbry-mqwu.json?$select=*,hospital_overall_rating_footnote,mortality_national_comparison_footnote&$$app_token=wm4gzEKEeeDSLI5XOC8BvMgB8")

data = response.json()
hospitalDB = []
hospitalListTmp = []
name = "";
pagenum = 0
lastnum = 110

count = 0

for hospital in data:
    hospitalDB.append({'source': 'medicare.gov',
                       'id': count, 'name': hospital["hospital_name"], 'address': hospital["address"],
                       'city': hospital["city"], 'state': hospital["state"], 'zip': hospital["zip_code"],
                       'phone_number': hospital["phone_number"], 'hospital_type': hospital["hospital_type"],
                       'hospital_ownership': hospital["hospital_ownership"],
                       'emergency_services': hospital["emergency_services"],
                       'meets_criteria_for_meaningful_use_of_ehrs': hospital.get("meets_criteria_for_meaningful_use_of_ehrs"),
                       'hospital_overall_rating': hospital["hospital_overall_rating"],
                       'hospital_overall_rating_footnote': hospital.get("hospital_overall_rating_footnote", "None"),
                       'mortality_national_comparison': hospital["mortality_national_comparison"],
                       'mortality_national_comparison_footnote': hospital.get("mortality_national_comparison_footnote", "None"),
                       'safety_of_care_national_comparison': hospital["safety_of_care_national_comparison"],
                       'safety_of_care_national_comparison_footnote': hospital.get("safety_of_care_national_comparison_footnote", "None"),
                       'readmission_national_comparison': hospital["readmission_national_comparison"],
                       'readmission_national_comparison_footnote': hospital.get("readmission_national_comparison_footnote", "None"),
                       'patient_experience_national_comparison': hospital["patient_experience_national_comparison"],
                       'patient_experience_national_comparison_footnote': hospital.get("patient_experience_national_comparison_footnote", "None"),
                       'effectiveness_of_care_national_comparison': hospital["effectiveness_of_care_national_comparison"],
                       'effectiveness_of_care_national_comparison_footnote': hospital.get("effectiveness_of_care_national_comparison_footnote", "None"),
                       'timeliness_of_care_national_comparison': hospital["timeliness_of_care_national_comparison"],
                       'timeliness_of_care_national_comparison_footnote': hospital.get("timeliness_of_care_national_comparison_footnote", "None"),
                       'efficient_use_of_medical_imaging_national_comparison': hospital["efficient_use_of_medical_imaging_national_comparison"],
                       'efficient_use_of_medical_imaging_national_comparison_footnote': hospital.get("efficient_use_of_medical_imaging_national_comparison_footnote", "None"),
                       'insurance': []})
    count = count+1

with open("data/govhospitals.csv", "r", encoding="ISO-8859-1") as file:
    reader = csv.reader(file, delimiter=',')
    line_count = 0
    for row in reader:
        if line_count == 0:
            line_count += 1
        else:
            hospitalDB.append({'source': 'arcgis.com', 'id': count,
                               'uid': row[1], 'name': row[2], 'address': row[3],
                               'city': row[4], 'state': row[5], 'zip': row[6],
                               'phone_number': row[7], 'hospital_type': row[8],
                               'population': row[9], 'county': row[10], 'countyfips': row[11],
                               'country': row[12], 'latitude': row[13], 'longitude': row[14],
                               'naics_code': row[15], 'naics_desc': row[16],
                               'source': row[17], 'sourcedate': row[18], 'val_method': row[19],
                               'val_date': row[20], 'website': row[21], 'state_id': row[22],
                               'alt_name': row[23], 'st_fips': row[24],
                               'hospital_ownership': row[25], 'ttl_staff': row[26],
                               'beds': row[27], 'trauma': row[28], 'helipad': row[29]})
            count += 1;


@app.route("/")
@app.route("/home")
def home():
    try:
        pagenum = int(request.args.get("page"))
    except:
        pagenum = 0

    result = hospitalDB
    if request.args.get("stars") is not None and request.args.get("stars") != "":
        temp = result
        result = []
        stars = int(request.args.get("stars"))
        for res in temp:
            if res.get("hospital_overall_rating") == "" or res.get("hospital_overall_rating") is None or res.get("hospital_overall_rating") == "Not Available" or int(res.get("hospital_overall_rating")) < stars:
                pass
            else:
                result.append(res)

    if request.args.get("name") is not None and request.args.get("name")!= "":
        temp = result
        result = []
        name = request.args.get("name")
        for res in temp:
            if res.get("name") == "" or res.get("name") == "Not Available" or name.lower() not in res.get("name").lower():
                pass
            else:
                result.append(res)

    if request.args.get("zip") is not None and request.args.get("zip") != "":
        temp = result
        result = []
        zip = int(request.args.get("zip"))
        for res in temp:
            if (res.get("zip") == "" or res.get("zip") == "Not Available" or int(zip) != int(res.get("zip"))) or str(zip)[:3] != res.get("zip")[:3]:
                pass
            else:
                result.append(res)

        if len(result) == 0:
            for res in temp:
                if str(zip)[:2] != res.get("zip")[:2]:
                    pass
                else:
                    result.append(res)


    return render_template('home.html', hospitalDB=result[pagenum * 100: min((pagenum+1)*100, len(result))], lastnum=len(result) // 100, pagenum=pagenum)


@app.route("/detail")
def detail():
    firmid = request.args.get("firm")
    response = requests.get("https://maps.googleapis.com/maps/api/place/findplacefromtext/json?key=AIzaSyAW3eWeUx3Myf69knSvb6z41nkjNZoTqqE&inputtype=textquery&fields=place_id&input=" + hospitalDB[int(firmid)]["name"])
    try:
        placeid = json.loads(response.text)["candidates"][0]["place_id"]
    except:
        return redirect("/")
    finalresponse = json.loads(requests.get(
        "https://maps.googleapis.com/maps/api/place/details/json?key=AIzaSyAW3eWeUx3Myf69knSvb6z41nkjNZoTqqE&placeid=" + placeid).text)[
        "result"]
    return render_template('detail.html', hospitalDB=hospitalDB, firmid=int(firmid), finalresponse=finalresponse,
                           lat=finalresponse["geometry"]["location"]["lat"],
                           long=finalresponse["geometry"]["location"]["lng"],
                           title=hospitalDB[int(firmid)]["name"])

@app.route("/about")
def about():
    return render_template('about.html', title="About")

if __name__ == '__main__':
    app.run(debug=False)
