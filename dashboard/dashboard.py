import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
from babel.numbers import format_currency
import folium
from streamlit_folium import folium_static


sns.set(style='dark')

# Helper function 
# Penjualan Bulanan
def create_monthly_sales(df):
    df['order_purchase_timestamp'] = pd.to_datetime(df['order_purchase_timestamp'])
    monthly_sales_df = df.groupby(df['order_purchase_timestamp'].dt.to_period('M')).size().reset_index(name='sales_count')
    monthly_sales_df['order_purchase_timestamp'] = monthly_sales_df['order_purchase_timestamp'].dt.to_timestamp()
    return monthly_sales_df



# Jumlah Pelanggan berdasarkan State
def create_state_counts(df):
    state_counts = df['customer_state'].value_counts().reset_index(name='customer_count')
    state_counts.rename(columns={'index': 'customer_state'}, inplace=True)
    return state_counts



# Top 10 Kota dengan Jumlah Pelanggan Terbanyak
def create_city_counts(df):
    city_counts = df['customer_city'].value_counts().head(10).reset_index(name='customer_count')
    city_counts.rename(columns={'index': 'customer_city'}, inplace=True)
    return city_counts



# Top 10 Best Selling Produk berdasarkan Kategori Produk
def create_topselling_categories(df):
    product_category_sales = df.groupby('product_category_name')['order_id'].count().reset_index()  # Menghitung jumlah produk terjual
    product_category_sales.columns = ['product_category_name', 'total_sold']  # Mengubah nama kolom untuk lebih jelas
    top_selling_categories = product_category_sales.sort_values(by='total_sold', ascending=False).head(10)
    return top_selling_categories
# Format angka
def format_k(value):
    return f"{value / 1000:.1f}k" if value >= 1000 else str(value)



# Distribusi Penjualan Produk berdasarkan Demografi Pelanggan
def create_sales_by_state(df):
    sales_by_state = df.groupby('customer_state')['price'].sum().reset_index()
    return sales_by_state
# Format angka
def format_number(value):
    """Format number to display in thousands or millions with currency."""
    if value >= 1_000_000:
        return f"Rp.{value / 1_000_000:.1f}M"  # Format in millions
    elif value >= 1_000:
        return f"Rp.{value / 1_000:.1f}k"  # Format in thousands
    else:
        return f"Rp.{value:.0f}"  # Format as is if less than 1,000



# Load cleaned data
all_df = pd.read_csv("all_data.csv")
datetime_columns = ["order_purchase_timestamp", "order_approved_at", "order_delivered_carrier_date", "order_delivered_customer_date", "order_estimated_delivery_date", "review_answer_timestamp"]
all_df.sort_values(by="order_purchase_timestamp", inplace=True)
all_df.reset_index(drop=True, inplace=True)

for column in datetime_columns:
    all_df[column] = pd.to_datetime(all_df[column])



# Filter data
with st.sidebar:
    start_date, end_date = st.date_input(
        label='Filter Rentang Waktu',
        min_value=all_df['order_purchase_timestamp'].min().date(),
        max_value=all_df['order_purchase_timestamp'].max().date(),
        value=[all_df['order_purchase_timestamp'].min().date(), all_df['order_purchase_timestamp'].max().date()]
    )

main_df = all_df[(all_df['order_purchase_timestamp'] >= pd.to_datetime(start_date)) & (all_df['order_purchase_timestamp'] <= pd.to_datetime(end_date))]


# Dashboard Layout
st.markdown("<h2 style='text-align: center;'>E-commerce Dashboard 🛍️</h2>", unsafe_allow_html=True)
start_date = start_date.strftime('%B %Y')
end_date = end_date.strftime('%B %Y')
st.markdown(f"<h4 style='text-align: center; margin-bottom: 50px;'>Period {start_date} - {end_date}</h4>", unsafe_allow_html=True)


# Create responsive columns for the donut chart and pie chart
col1, col2 = st.columns([1, 1])  # Equal width columns

# Top 10 Best Selling Products by Category - Donut Chart
with col1:
    st.markdown("<p style='text-align: center;'>Top 10 Best Selling Products by Category</p>", unsafe_allow_html=True)
    top_selling_df = create_topselling_categories(main_df)

    # Donut Chart
    fig, ax = plt.subplots(figsize=(8, 8))
    wedges, texts, autotexts = ax.pie(
        top_selling_df['total_sold'],
        labels=top_selling_df['product_category_name'],
        autopct=lambda p: f"{format_k(int(p / 100 * top_selling_df['total_sold'].sum()))} sold",
        startangle=90,
        colors=sns.color_palette('Blues_r', len(top_selling_df))
    )
    centre_circle = plt.Circle((0, 0), 0.70, fc='white')
    fig.gca().add_artist(centre_circle)

    for text in texts:
        text.set_fontsize(12)
    for autotext in autotexts:
        autotext.set_fontsize(12)
        autotext.set_color('black')
    ax.axis('equal')
    st.pyplot(fig)

# Number of Customers by State - Pie Chart
with col2:
    st.markdown("<p style='text-align: center;'>Top 10 Cities with the Most Customers</p>", unsafe_allow_html=True)
    city_counts_df = create_city_counts(main_df)

    # Pie Chart
    fig, ax = plt.subplots(figsize=(8, 8))
    wedges, texts, autotexts = ax.pie(
        city_counts_df['customer_count'],
        labels=city_counts_df['customer_city'],
        autopct='',  
        startangle=90,
        colors=sns.color_palette('Purples_r', len(city_counts_df))
    )

    highlight_color = 'white'  
    for i, autotext in enumerate(autotexts):
        percentage = city_counts_df['customer_count'].iloc[i] / city_counts_df['customer_count'].sum() * 100
        autotext.set_text(f'{percentage:.1f}%')
        autotext.set_bbox(dict(facecolor=highlight_color, edgecolor='none', boxstyle='round,pad=0.3')) 
        autotext.set_fontsize(8)

    for text in texts:
        text.set_fontsize(12)
    ax.axis('equal')
    st.pyplot(fig)

# Create responsive columns for the bar chart and monthly sales chart
col3, col4 = st.columns([1, 1])  # Equal width columns

# Total Sales by Country - Bar Chart
with col3:
    st.markdown("<p style='text-align: center; margin-top: 50px;'>Total Sales by State</p>", unsafe_allow_html=True)
    sales_by_state_df = create_sales_by_state(main_df)
    fig, ax = plt.subplots(figsize=(16, 10))  # Adjusted height
    sns.barplot(x=sales_by_state_df['customer_state'], y=sales_by_state_df['price'], palette='Purples', ax=ax)
    ax.yaxis.set_visible(False)
    for index, value in enumerate(sales_by_state_df['price']):
        ax.text(index, value + 50000, format_number(value), ha='center', va='bottom', fontsize=12, rotation=90)
    ax.set_xlabel('State', fontsize=15)
    ax.tick_params(axis='x', rotation=45)
    st.pyplot(fig)

# Monthly Sales - Line Chart
with col4:
    st.markdown("<p style='text-align: center; margin-top: 50px;'>Monthly Sales</p>", unsafe_allow_html=True)
    monthly_sales_df = create_monthly_sales(main_df)
    fig, ax = plt.subplots(figsize=(16, 10))  # Set the same height here
    ax.fill_between(monthly_sales_df['order_purchase_timestamp'], monthly_sales_df['sales_count'], color='#90CAF9', alpha=0.5)
    ax.plot(monthly_sales_df['order_purchase_timestamp'], monthly_sales_df['sales_count'], marker='o', linewidth=2, color='#90CAF9')
    ax.set_xlabel('Month, Year', fontsize=15)
    ax.yaxis.set_visible(False)
    ax.tick_params(axis='x', rotation=45)
    ax.set_xticks(monthly_sales_df['order_purchase_timestamp'])
    ax.set_xticklabels(monthly_sales_df['order_purchase_timestamp'].dt.strftime('%b %Y'), rotation=45)
    for i in range(len(monthly_sales_df)):
        sales_count = monthly_sales_df['sales_count'].iloc[i]
        formatted_sales = f"{sales_count / 1000:.1f}k" if sales_count >= 1000 else str(sales_count)
        ax.text(monthly_sales_df['order_purchase_timestamp'].iloc[i], sales_count + 2, formatted_sales, ha='center', va='bottom', fontsize=12)
    st.pyplot(fig)

# Number of Customers by State - Map
st.markdown("<p style='text-align: center; margin-top: 50px;'>Number of Customers by State</p>", unsafe_allow_html=True)
state_counts_df = create_state_counts(main_df)
state_locations = {
    'SP': [-23.5505, -46.6333], 'RJ': [-22.9068, -43.1729], 'MG': [-19.9167, -43.9345],
    'RS': [-30.0346, -51.2177], 'PR': [-25.4284, -49.2733], 'SC': [-27.5954, -48.5480],
}
m = folium.Map(location=[-14.2350, -51.9253], zoom_start=4)
for idx, row in state_counts_df.iterrows():
    state = row['customer_state']
    count = row['customer_count']
    formatted_count = f"{count / 1000:.1f}k" if count >= 1000 else str(count)
    if state in state_locations:
        folium.CircleMarker(
            location=state_locations[state],
            radius=count / 1000,
            color='blue',
            fill=True,
            fill_opacity=0.6,
            popup=f'{state}: {formatted_count} pelanggan',
            tooltip=f'{state}: {formatted_count} pelanggan'
        ).add_to(m)
        folium.Marker(
            location=state_locations[state],
            icon=None,
            popup=f'{state}: {formatted_count} pelanggan',
            tooltip=f'{state}: {formatted_count} pelanggan'
        ).add_to(m)
folium_static(m)

# Footer
st.markdown("<p style='text-align: center; margin-top:50px;'>Created by Maryam Hasnaa Syamila - m156b4kx2424@bangkit.academy</p>", unsafe_allow_html=True)