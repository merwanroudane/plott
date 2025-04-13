import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import io
import base64
from datetime import datetime

# Set page configuration
st.set_page_config(layout="wide", page_title="Interactive Plotly Animations")

# App title and description
st.title("Interactive Data Visualization with Animations")
st.markdown("""
Upload your Excel file, select variables, and create interactive animated plots with this app.
You can visualize how your data changes over time or other sequences.
""")


# Function to download example data
def get_example_data():
	# Create example data similar to stocks data
	dates = pd.date_range(start='2020-01-01', periods=100)

	# Create several columns with random but trending data
	np.random.seed(42)
	data = {
		'date': dates,
		'Company A': 100 + np.cumsum(np.random.randn(100) * 3),
		'Company B': 150 + np.cumsum(np.random.randn(100) * 2),
		'Company C': 200 + np.cumsum(np.random.randn(100) * 4),
		'Company D': 120 + np.cumsum(np.random.randn(100) * 2.5),
		'Company E': 180 + np.cumsum(np.random.randn(100) * 3.2),
	}

	df = pd.DataFrame(data)
	return df


# Function to create a download link for dataframe
def get_download_link(df, filename="example_data.xlsx"):
	buffer = io.BytesIO()
	with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
		df.to_excel(writer, index=False)

	buffer.seek(0)
	b64 = base64.b64encode(buffer.read()).decode()
	href = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="{filename}">Download Example Excel File</a>'
	return href


# Sidebar for data upload and selections
with st.sidebar:
	st.header("Data Input")

	# Option to download example data
	st.subheader("Example Data")
	example_df = get_example_data()
	st.markdown(get_download_link(example_df), unsafe_allow_html=True)

	# File uploader
	st.subheader("Upload Your Data")
	uploaded_file = st.file_uploader("Choose an Excel file", type=['xlsx', 'xls'])

	if uploaded_file is not None:
		try:
			df = pd.read_excel(uploaded_file)
			st.success("File successfully loaded!")
		except Exception as e:
			st.error(f"Error: {e}")
			st.info("Please upload a valid Excel file.")
			df = None
	else:
		st.info("Or use example data below")
		if st.button("Load Example Data"):
			df = example_df.copy()
		else:
			df = None

# Main content area
if df is not None:
	# Display raw data
	st.subheader("Raw Data Preview")
	st.dataframe(df.head())

	# Data columns analysis
	numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns.tolist()
	datetime_cols = [col for col in df.columns if pd.api.types.is_datetime64_any_dtype(df[col])]
	if not datetime_cols:
		# Try to convert string columns to datetime
		for col in df.columns:
			if df[col].dtype == 'object':
				try:
					test_conversion = pd.to_datetime(df[col])
					# If conversion was successful, convert column in dataframe
					df[col] = test_conversion
					datetime_cols.append(col)
				except:
					pass

	st.subheader("Data Visualization Settings")

	# Create columns for settings
	col1, col2 = st.columns(2)

	with col1:
		# Plot type selection
		plot_type = st.selectbox(
			"Select Plot Type",
			["Line Chart", "Scatter Plot", "Bar Chart", "Area Chart"],
			index=0
		)

		# X-axis selection
		if datetime_cols:
			x_col = st.selectbox("Select X-axis (Time/Date Column)", datetime_cols)
		else:
			x_col = st.selectbox("Select X-axis", df.columns.tolist())

	with col2:
		# Y-axis selection (multiple)
		if numeric_cols:
			selected_y_cols = st.multiselect(
				"Select Y-axis Variables (Numeric Columns)",
				numeric_cols,
				default=numeric_cols[:min(5, len(numeric_cols))]
			)
		else:
			st.warning("No numeric columns detected for Y-axis")
			selected_y_cols = []

		# Animation settings
		animation_frame = st.selectbox(
			"Select Animation Frame Column (typically date or period)",
			["None"] + df.columns.tolist(),
			index=0
		)

	# Validate selections
	if not selected_y_cols:
		st.warning("Please select at least one Y-axis variable")
	else:
		# Animation settings
		st.subheader("Animation Settings")
		col1, col2 = st.columns([1, 1])

		with col1:
			start_point = st.slider(
				"Starting point for animation",
				min_value=5,
				max_value=max(10, len(df) - 1),
				value=min(20, len(df) - 1)
			)

		with col2:
			animation_speed = st.slider(
				"Animation Speed (milliseconds per frame)",
				min_value=100,
				max_value=2000,
				value=500,
				step=100
			)

		# Generate the visualization
		st.subheader("Interactive Visualization")

		# Handle different animation cases
		if animation_frame != "None":
			# Use the selected animation frame
			animation_col = animation_frame
			plot_ready_df = df.copy()
		else:
			# Create animation based on data points (like the example)
			if pd.api.types.is_datetime64_any_dtype(df[x_col]):
				# Sort by date
				df = df.sort_values(by=x_col)

			# Create animation frames based on data index
			start = start_point
			obs = len(df)

			# Create a new dataframe for animation
			plot_ready_df = pd.DataFrame()
			for i in np.arange(start, obs + 1):
				dfa = df.head(i).copy()
				dfa['animation_frame'] = i
				plot_ready_df = pd.concat([plot_ready_df, dfa])

			animation_col = 'animation_frame'

		# Create the appropriate plot based on selection
		try:
			if plot_type == "Line Chart":
				fig = px.line(
					plot_ready_df,
					x=x_col,
					y=selected_y_cols,
					animation_frame=animation_col,
					width=1000,
					height=600,
					markers=True
				)
			elif plot_type == "Scatter Plot":
				fig = px.scatter(
					plot_ready_df,
					x=x_col,
					y=selected_y_cols[0] if len(selected_y_cols) == 1 else selected_y_cols,
					animation_frame=animation_col,
					width=1000,
					height=600,
					size_max=15
				)
			elif plot_type == "Bar Chart":
				fig = px.bar(
					plot_ready_df,
					x=x_col,
					y=selected_y_cols,
					animation_frame=animation_col,
					width=1000,
					height=600
				)
			elif plot_type == "Area Chart":
				fig = px.area(
					plot_ready_df,
					x=x_col,
					y=selected_y_cols,
					animation_frame=animation_col,
					width=1000,
					height=600
				)

			# Adjust animation settings
			if hasattr(fig.layout, 'updatemenus') and fig.layout.updatemenus:
				fig.layout.updatemenus[0].buttons[0]['args'][1]['frame']['redraw'] = True
				fig.layout.updatemenus[0].buttons[0]['args'][1]['transition']['duration'] = animation_speed
				fig.layout.updatemenus[0].buttons[0]['args'][1]['frame']['duration'] = animation_speed

			# Add title and labels
			fig.update_layout(
				title=f"{plot_type} of {', '.join(selected_y_cols)} over {x_col}",
				xaxis_title=x_col,
				yaxis_title="Value",
				legend_title="Variables"
			)

			# Display plot
			st.plotly_chart(fig, use_container_width=True)

			# Add description for controls
			st.info("""
            **Animation Controls:**
            - Use the play button to start the animation
            - Use the slider to scrub through animation frames
            - Hover over data points for details
            - Click and drag to zoom, double-click to reset the view
            """)

		except Exception as e:
			st.error(f"Error creating plot: {e}")
			st.info("Try different column selections or check your data format.")
else:
	# Display instructions when no data is loaded
	st.markdown("""
    ## How to use this app:

    1. Upload your Excel file using the sidebar (or use the example data)
    2. Select your plot type from the available options
    3. Choose the x-axis (typically a date or category)
    4. Select one or more y-axis variables to plot
    5. Configure animation settings
    6. Use the play button to see how your data changes over time

    The app supports line charts, scatter plots, bar charts, and area charts with animation features.
    """)

	st.image("https://user-images.githubusercontent.com/1415058/76470427-01cd2d80-63b6-11ea-8148-c2dd9be11144.gif",
			 caption="Example of Plotly animation (illustrative, not generated by this app)")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center">
    <p>Created with Streamlit, Plotly, and Pandas</p>
    <p>© 2025 Data Visualization App</p>
</div>
""", unsafe_allow_html=True)