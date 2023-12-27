import pandas as pd
import streamlit as st
import numpy as np
from sklearn.neighbors import BallTree

from streamlit.logger import get_logger

LOGGER = get_logger(__name__)

st.set_page_config(page_title="SASEF Health App", page_icon=None, layout="wide", initial_sidebar_state="auto", menu_items=None)

final_or = 1

st.title("Your Child's Health Outcome")
st.write("Enter some basic information about yourself to determine the likelihood of your child developing allergic diseases in adolescence.")

st.text("Check the box that applies. For questions relating to mental state, check yes if you felt your health was impacted by distress.")

time = st.radio(
    "Has your child been born?",
    ["Yes", "No"],index=None)

if time == 'Yes':
    prenatal = False
    postnatal = True
elif time == "No":
    prenatal = True
    postnatal = False
else:
    st.write(" ")
    prenatal=False
    postnatal = False

if prenatal:
    pre_stress_input = st.radio("Have you experienced stress or depression during your pregnancy?",["I have experienced stress, depression, and/or negative life events that have impacted my mental health during pregnancy.","I have not experienced stress, depression, and/or negative life events that have impacted my mental health during pregnancy."],index=None)
    if pre_stress_input == "I have experienced stress, depression, and/or negative life events that have impacted my mental health during pregnancy.":
        final_or = final_or * 1.3845
    if pre_stress_input == "I have not experienced stress, depression, and/or negative life events that have impacted my mental health during pregnancy.":
        final_or = final_or * 1
    else:
        st.write(" ")

if postnatal:
    pre_stress_input_post = st.radio("Did you experience stress or depression during your pregnancy?",["I experienced stress, depression, and/or negative life events during pregnancy.","I did not experience stress, depression, and/or negative life events during pregnancy."],index=None)
    post_stress_input = st.radio("Have you experienced stress or depression since your child was born?",["I have experienced stress, depression, and/or negative life events since my child was born.","I have not experienced stress, depression, and/or negative life events since my child was born."],index=None)
    if pre_stress_input_post == "I experienced stress, depression, and/or negative life events during pregnancy.":
        final_or = final_or * 1.3845
    if pre_stress_input_post == "I did not experience stress, depression, and/or negative life events during pregnancy.":
        final_or = final_or * 1
    if post_stress_input == "I have experienced stress, depression, and/or negative life events since my child was born.":
        final_or = final_or * 1.2565
    if post_stress_input == "I have not experienced stress, depression, and/or negative life events since my child was born.":
        final_or = final_or * 1
    else:
        st.write(" ")

aq_data = pd.read_csv("uscities_aq - cbsa_trends.csv")
aq_data = aq_data.ffill(axis=0)
aq_data = aq_data.drop([1042,1041,1040,1039,1038,1037,1036,1035,1034,1033])

locs = pd.read_csv("cbsa_lat_long - cbsa.csv")
locs = locs.drop(['CBSA_TYPE',"ALAND","AWATER","ALAND_SQMI","AWATER_SQMI",'NAME','CSAFP'],axis=1)
locs = locs.rename(columns={"INTPTLAT": "Lat", "INTPTLONG": "Long"})
locs = locs.set_index("GEOID")
locs.Lat = locs.Lat.apply(np.radians)
locs.Long = locs.Long.apply(np.radians)

zip_cbsa = pd.read_csv("zip_cbsa - zipcodes_geoids.csv",dtype={'ZIP': str})
zip_cbsa = zip_cbsa.drop(["RES_RATIO","BUS_RATIO",'OTH_RATIO',"TOT_RATIO"],axis=1)

tree = BallTree(locs[['Lat', 'Long']].values, leaf_size=2, metric='haversine')

get_locs = st.text_input(label="Enter your zip code")
zip_to_geoid = zip_cbsa[zip_cbsa['ZIP'] == get_locs]
get_cbsa = zip_to_geoid["CBSA"]

if len(get_locs) == 0:
    st.text(" ")

if len(get_cbsa) == 1:
    geoid = int(get_cbsa.iloc[0])
    query_point = locs.loc[geoid][["Lat", "Long"]].values
    distances, indices = tree.query([query_point], k=10)
    result_df = locs.iloc[indices[0]]
elif len(get_cbsa) > 1:
    dfs=[]
    for loc in get_cbsa:
        geoid=int(loc)
        query_point = locs.loc[geoid][["Lat", "Long"]].values
        distances, indices = tree.query([query_point], k=10)
        result_part_df = locs.iloc[indices[0]]
        dfs.append(result_part_df)
    result_df = pd.concat(dfs) 
if len(get_locs) > 0:
    if len(get_cbsa)== 0:
        st.text("Sorry, we were unable to located a Core Based Statistical Area associated with that zip code. Try entering a different zip code near your area.")
        result_df = pd.DataFrame()

try:
    result_df = result_df.reset_index()
    new_lst = result_df["GEOID"]
    new_lst = new_lst.drop_duplicates()
    aq_data["CBSA"] = aq_data["CBSA"].astype(int)
    filtered_aqs = aq_data[aq_data['CBSA'].isin(new_lst)]
    filtered_aqs = filtered_aqs.drop(['2000','2001','2002','2003','2004','2005','2006','2007','2008','2009','2010','2011','2012','2013','2014','2015','2016','2017','2018','2019','2020','2021'],axis=1)
  
    co_df = filtered_aqs[filtered_aqs['Pollutant'] == "CO"]
    no2_df = filtered_aqs[filtered_aqs['Pollutant'] == "NO2"]
    o3_df = filtered_aqs[filtered_aqs['Pollutant'] == "O3"]
    pm10_df = filtered_aqs[filtered_aqs['Pollutant'] == "PM10"]
    pm25_df = filtered_aqs[filtered_aqs['Pollutant'] == "PM2.5"]
    so2_df = filtered_aqs[filtered_aqs['Pollutant'] == "SO2"]
    indiv_dfs = [co_df,no2_df,o3_df,pm10_df,pm25_df,so2_df]

    pre_lims_lst = []
    post_lims_lst = []

    def naaq_pre_lims(df):
        poll_vals = df['2022']
        base_or = 1
        name = "blank"
        for index, row in df.iterrows():
            if row['Pollutant'] == "O3":
                limit = 0.07
                name = "O3"
                ratio = 1
            elif row['Pollutant'] == "CO":
                limit = 9.0
                name = "CO"
                ratio = 1
            elif row['Pollutant'] == "NO2":
                name = "NO2"
                ratio = 1.2959
                if row['Trend Statistic'] == 'Annual Mean':
                    limit = 53.0
                elif row['Trend Statistic'] == '98th Percentile':
                    limit = 100.0
            elif row['Pollutant'] == "PM10":
                name = "PM10"
                limit = 150.0
                ratio = 1.2341
            elif row['Pollutant'] == "PM2.5":
                name = "PM2.5"
                ratio = 1.1656
                if row['Trend Statistic'] == 'Weighted Annual Mean':
                    limit = 12.0
                elif row['Trend Statistic'] == '98th Percentile':
                    limit = 35.0
            elif row['Pollutant'] == "SO2":
                name = "SO2"
                limit = 75.0
                ratio = 1.515     
                
        counts_above = 0
        counts_below = 0
            
        for val in poll_vals:
            if float(val) >= limit:
                counts_above = counts_above + 1
            else:
                counts_below = counts_below + 1   
    
        # st.write(name, ":", counts_above, "above,", counts_below, "below")
        
        if counts_above > counts_below:
            # st.write("Dangerous levels of pollutant")
            base_or = base_or * ratio
            pre_lims_lst.append(base_or)
        else:
            # st.write("Safe")
            pre_lims_lst.append(base_or)


    def naaq_post_lims(df):
        poll_vals = df['2022']
        base_or = 1
        name = "blank"
        for index, row in df.iterrows():
            if row['Pollutant'] == "O3":
                limit = 0.07
                name = "O3"
                ratio = 1.0228
            elif row['Pollutant'] == "CO":
                limit = 9.0
                name = "CO"
                ratio = 1.1063
            elif row['Pollutant'] == "NO2":
                name = "NO2"
                ratio = 1.2588
                if row['Trend Statistic'] == 'Annual Mean':
                    limit = 53.0
                elif row['Trend Statistic'] == '98th Percentile':
                    limit = 100.0
            elif row['Pollutant'] == "PM10":
                name = "PM10"
                limit = 150.0
                ratio = 1.2701
            elif row['Pollutant'] == "PM2.5":
                name = "PM2.5"
                ratio = 1.4844
                if row['Trend Statistic'] == 'Weighted Annual Mean':
                    limit = 12.0
                elif row['Trend Statistic'] == '98th Percentile':
                    limit = 35.0
            elif row['Pollutant'] == "SO2":
                name = "SO2"
                limit = 75.0
                ratio = 1.515
                
        counts_above = 0
        counts_below = 0
            
        for val in poll_vals:
            if float(val) >= limit:
                counts_above = counts_above + 1
            else:
                counts_below = counts_below + 1
            
        # st.write(name, ":", counts_above, "above,", counts_below, "below")
        
        if counts_above > counts_below:
            # st.write("Dangerous levels of pollutant")
            base_or = base_or * ratio
            post_lims_lst.append(base_or)
        else:
            # st.write("Safe")
            post_lims_lst.append(base_or)


    if prenatal:  
        url1 = "https://www.epa.gov/children/promoting-good-prenatal-health-air-pollution-and-pregnancy-january-2010"
        url2 = "https://mchb.hrsa.gov/national-maternal-mental-health-hotline"
        
        for df in indiv_dfs:
            if len(df) > 0:
                naaq_pre_lims(df)
        # st.write(pre_lims_lst)
        for val in pre_lims_lst:
            final_or = final_or * val
        rounded_final = str(round((final_or-1)*100))
        if int(rounded_final) > 0:
            st.write("There is a " + rounded_final + "% increase in the odds of your child developing allergies.")
            st.markdown("[Environmental protection resources](%s)" % url1)
            st.markdown("[Distress resources](%s)" % url2)
        elif int(rounded_final) == 0:
            st.write("Based on exposure to environmental pollution and psychological distress, your child likely will not have an increased risk of atopy.")
        else:
            st.write(" ")
        
    if postnatal:   
        url3 = "https://www.epa.gov/children"
        url4 = "https://www.womenshealth.gov/mental-health/mental-health-conditions/postpartum-depression"
        
        for df in indiv_dfs:
            if len(df) > 0:
                naaq_post_lims(df)
        # st.write(post_lims_lst)
        for val in post_lims_lst:
            final_or = final_or * val
            
        rounded_final = str(round((final_or-1)*100))
        
        if int(rounded_final) > 0:
            st.write("There is a " + rounded_final + "% increase in the odds of your child developing allergies.")
            st.markdown("[Environmental protection resources](%s)" % url3)
            st.markdown("[Distress resources](%s)" % url4)
        elif int(rounded_final) == 0:
            st.write("Based on exposure to environmental pollution and psychological distress, your child does not have an increased risk of atopy.")
        else:
            st.write(" ")


except:
    st.text(" ")
