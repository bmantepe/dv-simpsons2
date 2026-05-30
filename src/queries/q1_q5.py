import streamlit as st
import pandas as pd
import altair as alt
import numpy as np 
import base64
import os

# Disable max rows for instant interactivity in the browser
alt.data_transformers.disable_max_rows()

def create_character_plot(df_all_faces: pd.DataFrame, df_agg: pd.DataFrame, df_dist: pd.DataFrame):
    
    all_character_names = sorted(df_all_faces['character'].unique().tolist())
    
    # ==========================================
    # SELECTIONS & PARAMETERS
    # ==========================================
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

    default_chars = [
        {"character": "Apu"}, {"character": "Bart"}, 
        {"character": "Lisa"}, {"character": "Homer"}, {"character": "Marge"}
    ]
    char_selector = alt.selection_point(
        name="char_selector", 
        fields=['character'], 
        value=default_chars,
        empty=False 
    )

    # ==========================================
    # CHART A: Visual Face Selector 
    # ==========================================
    char_base = alt.Chart(df_all_faces)

    heatmap = char_base.mark_rect(color='#0e33eb', cornerRadius=3).encode(
        x=alt.X('character:N', sort=all_character_names, title='Select Characters (Shift+Click)', axis=alt.Axis(labelAngle=0)),
        opacity=alt.condition(char_selector, alt.value(0.4), alt.value(0)) 
    )

    faces = char_base.mark_image(width=35, height=35).encode(
        x=alt.X('character:N', sort=all_character_names, axis=alt.Axis(labels=False, ticks=False, title=None)),
        url="image:N"
    )
    
    face_selector_chart = (heatmap + faces).properties(width=700, height=60, title="Selector")

    # ==========================================
    # SHARED Y-AXIS (Dynamic Resizing)
    # ==========================================
    y_enc = alt.Y(
        "character:N", 
        sort=all_character_names,
        axis=alt.Axis(domain=False, ticks=False, labels=False, title=None)
    )

    # ==========================================
    # CHART B: Bar Chart
    # ==========================================
    bars = alt.Chart(df_agg).mark_bar().encode(
        x=alt.X("count:Q", title="Total Count"), 
        y=y_enc,
        color=alt.Color("character:N", legend=None),
        tooltip=[
            alt.Tooltip("character:N", title="Character"), 
            alt.Tooltip("count:Q", title="Total Count"),
            alt.Tooltip("count_type:N", title="Count Type")
        ]
    ).transform_filter(
        metric_selector 
    ).transform_filter(
        char_selector 
    ).transform_window(
        # THE FIX: Mathematically rank the selected characters
        rank='dense_rank()',
        sort=[alt.SortField('character', order='ascending')]
    ).transform_filter(
        # THE FIX: Force the chart to slice off anything ranked above 5
        alt.datum.rank <= 5
    )

    flags = alt.Chart(df_agg).mark_image(width=25, height=25, clip=False, xOffset=-12).encode(
        y=y_enc,
        x=alt.value(0), 
        url="image:N"
    ).transform_filter(
        metric_selector
    ).transform_filter(
        char_selector
    ).transform_window(
        rank='dense_rank()',
        sort=[alt.SortField('character', order='ascending')]
    ).transform_filter(
        alt.datum.rank <= 5
    )
    
    barplot_final = (bars + flags).properties(width=300, height=alt.Step(40), title="Total Dialogue Count")

    # ==========================================
    # CHART C: Jitter Plot
    # ==========================================
    gaussian_jitter = alt.Chart(df_dist, title='Dialogue Distribution').mark_circle(size=8, opacity=0.7).encode(
        y=y_enc,
        x=alt.X("count:Q", title="Count"), 
        yOffset=alt.YOffset("jitter:Q", scale=alt.Scale(domain=[-10, 10])),
        color=alt.Color("character:N", legend=None)
    ).transform_filter(
        metric_selector 
    ).transform_filter(
        char_selector
    ).transform_window(
        rank='dense_rank()',
        sort=[alt.SortField('character', order='ascending')]
    ).transform_filter(
        alt.datum.rank <= 5
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
    ).transform_window(
        rank='dense_rank()',
        sort=[alt.SortField('character', order='ascending')]
    ).transform_filter(
        alt.datum.rank <= 5
    )
    
    jitter_final = (gaussian_jitter + mean_bar).properties(width=300, height=alt.Step(40))

    # ==========================================
    # NESTED CONCATENATION
    # ==========================================
    data_plots = alt.hconcat(barplot_final, jitter_final).resolve_scale(y='shared')
    
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
    
    def get_local_image_b64(char_name):
        name_lower = str(char_name).lower().strip()
        
        file_map = {
            "apu": "apu.png", "bart": "bart-simpson.png", "bart simpson": "bart-simpson.png",
            "homer": "homer-simpson.png", "homer simpson": "homer-simpson.png", "lisa": "lisa-simpson.png",
            "lisa simpson": "lisa-simpson.png", "marge": "marge-simpson.png", "marge simpson": "marge-simpson.png",
            "abraham simpson": "abraham-simpson.png", "grampa": "abraham-simpson.png", "barney": "barney-gumble.png",
            "barney gumble": "barney-gumble.png", "moe": "bartender-mo.png", "moe szyslak": "bartender-mo.png",
            "kent brockman": "brockman.png", "brockman": "brockman.png", "carl": "carl.png", "carl carlson": "carl.png",
            "mr. burns": "charles-montgomery-burns.png", "burns": "charles-montgomery-burns.png",
            "chief wiggum": "clancy-wiggum.png", "wiggum": "clancy-wiggum.png", "jimbo": "jimbo.png",
            "jimbo jones": "jimbo.png", "krusty": "krusty-the-clown.png", "krusty the clown": "krusty-the-clown.png",
            "lenny": "lenny.png", "lenny leonard": "lenny.png", "lou": "lou.png", "martin": "martin-prince.png",
            "martin prince": "martin-prince.png", "milhouse": "milhouse-van-houten.png", "milhouse van houten": "milhouse-van-houten.png",
            "ned flanders": "ned-flanders.png", "flanders": "ned-flanders.png", "nelson": "nelson.png",
            "nelson muntz": "nelson.png", "otto": "otto.png", "otto mann": "otto.png", "patty": "patty.png",
            "patty bouvier": "patty.png", "ralph": "ralf.png", "ralph wiggum": "ralf.png", "rev. lovejoy": "rev-lovejoy.png",
            "lovejoy": "rev-lovejoy.png", "selma": "selma.png", "selma bouvier": "selma.png", "smithers": "smithers.png",
            "waylon smithers": "smithers.png"
        }
        
        filename = file_map.get(name_lower, f"{name_lower.replace(' ', '-')}.png")
        paths_to_try = [f"src/static/{filename}", f"../src/static/{filename}", f"static/{filename}", f"../static/{filename}", filename]
        
        for p in paths_to_try:
            if os.path.exists(p):
                with open(p, "rb") as f:
                    return f"data:image/png;base64,{base64.b64encode(f.read()).decode('utf-8')}"
        return "data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7"

    unique_chars = q1_q5['character'].dropna().unique()
    char_to_b64_map = {char: get_local_image_b64(char) for char in unique_chars}
    q1_q5['image'] = q1_q5['character'].map(char_to_b64_map)
    
    q1_q5_agg = q1_q5.groupby(['character', 'count_type', 'image'], as_index=False)['count'].sum()
    unique_faces = q1_q5[['character', 'image']].drop_duplicates()
    
    return q1_q5, q1_q5_agg, unique_faces

data_q1_q5, data_q1_q5_agg, all_faces = load_data_q1_q5()

chart = create_character_plot(df_all_faces=all_faces, df_agg=data_q1_q5_agg, df_dist=data_q1_q5) 

st.altair_chart(chart, width="content", theme=None)