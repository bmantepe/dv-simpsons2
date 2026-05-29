import streamlit as st
import pandas as pd
import altair as alt
import numpy as np 
import requests
import base64

# 1. Disable VegaFusion! VegaFusion causes network lag on clicks.
# Using disable_max_rows makes the interactivity run instantly in the browser.
alt.data_transformers.disable_max_rows()

def create_character_plot(df_all_faces: pd.DataFrame, df_agg: pd.DataFrame, df_dist: pd.DataFrame):
    
    # Extract and SORT the list so both the faces and the bars match perfectly
    all_character_names = sorted(df_all_faces['character'].unique().tolist())
    
    # 1. ALTAIR NATIVE FILTER: Metric Dropdown
    metric_dropdown = alt.binding_radio(
        options=['word_count', 'sentence_count'], 
        labels=['Word', 'Sentence'],              
        name='Analysis Metric: '
    )
    metric_selector = alt.selection_point(
        name="metric_selector",
        fields=['count_type'], 
        bind=metric_dropdown, 
        value=[{'count_type': 'word_count'}] 
    )

    # 2. CHARACTER SELECTION: Set default 5 selected characters
    default_chars = [
        {"character": "Apu"}, {"character": "Bart"}, 
        {"character": "Lisa"}, {"character": "Homer"}, {"character": "Marge"}
    ]
    char_selector = alt.selection_point(
        name="char_selector", 
        fields=['character'], 
        value=default_chars
    )

    # ==========================================
    # CHART A: Visual Face Selector (HORIZONTAL)
    # ==========================================
    char_base = alt.Chart(df_all_faces)

    heatmap = char_base.mark_rect(color='#0e33eb', cornerRadius=3).encode(
        x=alt.X('character:N', sort=all_character_names, title='Select Characters (Shift+Click)', axis=alt.Axis(labelAngle=0)),
        opacity=alt.condition(char_selector, alt.value(0.4), alt.value(0)) 
    )

    # Because these are now Base64 strings, they load instantly with zero blinking!
    faces = char_base.mark_image(width=35, height=35).encode(
        x=alt.X('character:N', sort=all_character_names, axis=alt.Axis(labels=False, ticks=False, title=None)),
        url="image:N"
    )
    
    face_selector_chart = (heatmap + faces).properties(width=700, height=60, title="Selector")

    # ==========================================
    # CHART B: Bar Chart
    # ==========================================
    y_enc = alt.Y(
        "character:N", 
        sort=all_character_names,
        axis=alt.Axis(domain=False, ticks=False, labels=False, title=None)
    )
    
    bars = alt.Chart(df_agg).mark_bar().encode(
        x=alt.X("count:Q", title="Total Count"), 
        y=y_enc,
        tooltip=[
            alt.Tooltip("character:N", title="Character"), 
            alt.Tooltip("count:Q", title="Total Count"),
            alt.Tooltip("count_type:N", title="Count Type")
        ]
    ).transform_filter(
        metric_selector 
    ).transform_filter(
        char_selector 
    )

    flags = alt.Chart(df_agg).mark_image(width=25, height=25, clip=False, xOffset=-12).encode(
        y=y_enc,
        x=alt.value(0), 
        url="image:N"
    ).transform_filter(
        metric_selector
    ).transform_filter(
        char_selector
    )
    
    barplot_final = (bars + flags).properties(width=300, height=alt.Step(40), title="Total Dialogue Count")

    # ==========================================
    # CHART C: Jitter Plot
    # ==========================================
    gaussian_jitter = alt.Chart(df_dist, title='Dialogue Distribution').mark_circle(size=8).encode(
        y=y_enc,
        x=alt.X("count:Q", title="Count"), 
        yOffset=alt.YOffset("jitter:Q", scale=alt.Scale(domain=[-10, 10]))
    ).transform_filter(
        metric_selector 
    ).transform_filter(
        char_selector
    )

    mean_bar = alt.Chart(df_dist).mark_tick(color='red', size=30, thickness=3).transform_aggregate(
        mean_val="mean(count)",               
        groupby=["character", "count_type"]   
    ).encode(
        x=alt.X("mean_val:Q"),
        y=y_enc
    ).transform_filter(
        metric_selector 
    ).transform_filter(
        char_selector
    )
    
    jitter_final = (gaussian_jitter + mean_bar).properties(width=300, height=alt.Step(40))

    # ==========================================
    # NESTED CONCATENATION
    # ==========================================
    data_plots = alt.hconcat(barplot_final, jitter_final).resolve_scale(y='shared')
    
    # 2. Add both parameters exactly ONCE here to stop console warnings and loop bugs
    final_layout = alt.vconcat(
        face_selector_chart, 
        data_plots
    ).add_params(
        char_selector, 
        metric_selector 
    ).configure_view(
        stroke=None
    )

    return final_layout

# ==========================================
# STREAMLIT APP DASHBOARD
# ==========================================

st.set_page_config(layout="wide", page_title="The Simpsons Dialogue")

st.title("The Simpsons: Character Dialogue Analysis")
st.markdown("Use the radio buttons to switch metrics. **Shift-Click** the faces in the selector menu to add or remove characters from the comparison graphs.")

@st.cache_data
def load_data_q1_q5():    
    q1_q5 = pd.read_csv('../data/data_Q1_Q5.csv')
    
    np.random.seed(42)
    q1_q5['jitter'] = np.random.normal(0, 3, size=len(q1_q5)) 
    
    # ========================================================
    # 3. BASE 64 IMAGE ENCODER (Fixes CORS and Disappearing Images)
    # ========================================================
    def fetch_image_as_base64(url):
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(url, headers=headers, timeout=5)
            if response.status_code == 200:
                b64 = base64.b64encode(response.content).decode('utf-8')
                return f"data:image/png;base64,{b64}"
        except:
            pass
        return url

    # Fetch and map the images to Base64 strings
    unique_urls = q1_q5['image'].dropna().unique()
    url_to_b64_map = {url: fetch_image_as_base64(url) for url in unique_urls}
    q1_q5['image'] = q1_q5['image'].map(url_to_b64_map)
    
    q1_q5_agg = q1_q5.groupby(['character', 'count_type', 'image'], as_index=False)['count'].sum()
    unique_faces = q1_q5[['character', 'image']].drop_duplicates()
    
    return q1_q5, q1_q5_agg, unique_faces

data_q1_q5, data_q1_q5_agg, all_faces = load_data_q1_q5()

chart = create_character_plot(df_all_faces=all_faces, df_agg=data_q1_q5_agg, df_dist=data_q1_q5) 

# 4. Use theme=None to stop Streamlit CSS from fighting Altair's instant layout updates
st.altair_chart(chart, width="content", theme=None)