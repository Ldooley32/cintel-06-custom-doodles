import plotly.express as px
import seaborn as sns
from shiny.express import input, ui
from shiny import reactive, render  # Import render module
from shinywidgets import render_plotly, render_widget
import palmerpenguins  # provides the Palmer Penguin dataset
from faicons import icon_svg
import random
from datetime import datetime
from collections import deque
from scipy import stats
import pandas as pd
from shinyswatch import theme

# Use the built-in function to load the Palmer Penguins dataset
penguins_df = palmerpenguins.load_penguins()

# --------------------------------------------
# First, set a constant UPDATE INTERVAL for all live data
# Constants are usually defined in uppercase letters
# Use a type hint to make it clear that it's an integer (: int)
# --------------------------------------------

UPDATE_INTERVAL_SECS: int = 5

# --------------------------------------------
# Initialize a REACTIVE VALUE with a common data structure
# The reactive value is used to store state (information)
# Used by all the display components that show this live data.
# This reactive value is a wrapper around a DEQUE of readings
# --------------------------------------------

DEQUE_SIZE: int = 5
reactive_value_wrapper = reactive.value(deque(maxlen=DEQUE_SIZE))

@reactive.calc()
def reactive_calc_combined():
    # Invalidate this calculation every UPDATE_INTERVAL_SECS to trigger updates
    reactive.invalidate_later(UPDATE_INTERVAL_SECS)

    # Data generation logic
    temp = round(random.uniform(-20, 10 ), 1)
    penguin_activity = round(random.uniform(50,300))
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new_dictionary_entry = {"temp": temp, "penguin_activity": penguin_activity, "timestamp": timestamp}

    # get the deque and append the new entry
    reactive_value_wrapper.get().append(new_dictionary_entry)

    # Get a snapshot of the current deque for any further processing
    deque_snapshot = reactive_value_wrapper.get()

    # For Display: Convert deque to DataFrame for display
    df = pd.DataFrame(deque_snapshot)

    # For Display: Get the latest dictionary entry
    latest_dictionary_entry = new_dictionary_entry

    # Return a tuple with everything we need
    # Every time we call this function, we'll get all these values
    return deque_snapshot, df, latest_dictionary_entry


ui.page_opts(title="Mrs. Doodles Penguins", fillable=True)

#add color theme
theme.yeti()

# Define a dictionary mapping display names to original column names
column_mapping = {
    "Bill Length (mm)": "bill_length_mm",
    "Bill Depth (mm)": "bill_depth_mm",
    "Flipper Length (mm)": "flipper_length_mm",
    "Body Mass (g)": "body_mass_g"
}

# Add a Shiny UI sidebar for user interaction
with ui.sidebar(open="open"):

    # Use the ui.h2() function to add a 2nd level header to the sidebar
    # pass in a string argument (in quotes) to set the header text to "Sidebar"
    ui.h2("Sidebar")

    # Use ui.input_selectize() to create a dropdown input to choose a column
    ui.input_selectize("selected_attribute", "Selected Attribute",
                       list(column_mapping.keys()))

    # Use ui.input_slider() to create a slider input for the number of Seaborn bins
    ui.input_slider("seaborn_bin_count", "Seaborn Bin Count", 0, 100, 40)

    # Use ui.input_checkbox_group() to create a checkbox group input to filter the species
    ui.input_checkbox_group("selected_species_list", "Species",
                            ["Adelie", "Gentoo", "Chinstrap"], selected=["Adelie", "Gentoo", "Chinstrap"])
    
    #Use ui.input_checkbox_group() to create a checkbox group input to filter the islands
    ui.input_checkbox_group("selected_island_list", "Island",
                            ["Torgersen", "Biscoe", "Dream"], selected= ["Torgersen", "Biscoe", "Dream"])
    
    # Use ui.input_checkbox() to create a checkbox to show the sex
    ui.input_checkbox("show_sex", "Show Sex")

    # Use ui.hr() to add a horizontal rule to the sidebar
    ui.hr()

    # Use ui.a() to add a hyperlink to the sidebar
    ui.a("GitHub", href="https://github.com/Ldooley32/cintel03-reactive-doodles/blob/main/app.py", target="_blank")

with ui.layout_columns():
   with ui.value_box(
        showcase=icon_svg("snowflake"),
        theme="bg-gradient-blue-purple",
    ):
    "Current Anarctica Temperature"

    @render.text
    def display_temp():
        """Get the latest reading and return a temperature string"""
        deque_snapshot, df, latest_dictionary_entry = reactive_calc_combined()
        temperature = latest_dictionary_entry['temp']
        return f"{temperature} C"
    
    @render.text
    def temperature_status():
        """Update UI theme and text based on temperature"""
        deque_snapshot, df, latest_dictionary_entry = reactive_calc_combined()
        temperature = latest_dictionary_entry['temp']
        if temperature < 0:
            
            return "Colder than usual."
        else:
            
            return "Warmer than usual."  

# display timestamp and active penguins

with ui.layout_columns():
    with ui.card(full_screen=True):
        ui.card_header("Current Date and Time")

        @render.text
        def display_time():
            """Get the latest reading and return a timestamp string"""
            deque_snapshot, df, latest_dictionary_entry = reactive_calc_combined()
            return f"{latest_dictionary_entry['timestamp']}"

        @render.text
        def active_penguins():
          """Get the latest reading and return a active penguin string"""
          deque_snapshot, df, latest_dictionary_entry = reactive_calc_combined()
          activity = latest_dictionary_entry['penguin_activity']  
          return f"{activity} Active Penguins"


@reactive.calc
def filtered_data():
    return penguins_df[
        (penguins_df["species"].isin(input.selected_species_list())) &
        (penguins_df["island"].isin(input.selected_island_list()))
    ]

with ui.navset_card_tab(id="tab"):
    with ui.nav_panel("Most Recent Readings"):

        # Create a function to render the Plotly histogram
         @render.data_frame
         def display_df():
             """Get the latest reading and return a dataframe with current readings"""
             deque_snapshot, df, latest_dictionary_entry = reactive_calc_combined()
             pd.set_option('display.width', None)        # Use maximum width
             return render.DataGrid( df,width="100%")

    with ui.nav_panel("Seaborn Histogram"):
        # Create a function to render the Seaborn histogram
        @render.plot
        def seaborn_histogram():
            selected_attribute = input.selected_attribute()
            seaborn_bin_count = input.seaborn_bin_count()
            show_sex = input.show_sex()

            title = f"Seaborn Histogram for {selected_attribute}"
            if show_sex:
                title += " (Sex Included)"

            sns.set(style="whitegrid")  # Set Seaborn style
            seaborn_histogram = sns.histplot(
                filtered_data(),
                x=column_mapping[selected_attribute],
                hue="sex" if show_sex else "species",
                bins=seaborn_bin_count,
            )
            # Update titles and labels
            seaborn_histogram.set_title(title)

            return seaborn_histogram

    with ui.nav_panel("Scatterplot"):
        ui.card_header("Plotly Scatterplot: Species")

        @render_plotly
        def ploty_scatterplot():
            selected_species_list = input.selected_species_list()
            filtered_df = penguins_df[penguins_df["species"].isin(selected_species_list)]
            plotly_scatter = px.scatter(
                filtered_df,
                x="body_mass_g",
                y="bill_length_mm",
                color="species",
                size_max=7,
                labels={
                    "body_mass_g": "Body Mass (g)",
                    "bill_length_mm": "Bill Length(mm)",
                },
            )
            return plotly_scatter
