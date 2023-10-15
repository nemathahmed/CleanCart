import streamlit as st
import pandas as pd
# from streamlit_card import card
import random
from sklearn.metrics.pairwise import euclidean_distances
import json 
image_cache = {}
selected_product = None

# Function to calculate the similarity score for products with lower 'f_FPro' in the same category
def calculate_similarity(data,original_ID):

    # Find the 'f_FPro' score and category of the selected product
    selected_product = data[data['original_ID'] == original_ID]
    if selected_product.empty:
        return "Product not found"

    selected_f_FPro = selected_product.iloc[0]['f_FPro']
    selected_category = selected_product.iloc[0]['harmonized single category']

    # Filter products with 'f_FPro' lower than the selected product and the same category
    lower_fpro_same_category_products = data[
        (data['f_FPro'] < selected_f_FPro) & (data['harmonized single category'] == selected_category)
    ]

    # Exclude the original product from the search space
    lower_fpro_same_category_products = lower_fpro_same_category_products[lower_fpro_same_category_products['original_ID'] != original_ID]

    # Filter out products with no 'f_FPro' score
    lower_fpro_same_category_products = lower_fpro_same_category_products.dropna(subset=['f_FPro'])

    if lower_fpro_same_category_products.empty:
        return "No lower Fpro products in the same category found"

    # Select the specific fields for similarity calculation
    selected_fields = ['Protein', 'Total Fat', 'Carbohydrate', 'Sugars, total',
                       'Fiber, total dietary', 'Calcium', 'Iron', 'Sodium', 'Vitamin C',
                       'Cholesterol', 'Fatty acids, total saturated', 'Total Vitamin A']

    # Calculate the median values for each selected field within the same category
    median_values = lower_fpro_same_category_products.groupby('harmonized single category')[selected_fields].median()

    # Impute missing values with the calculated median values
    for field in selected_fields:
        lower_fpro_same_category_products[field].fillna(
            median_values.loc[selected_category][field],
            inplace=True
        )

    # Calculate cosine similarity based on the selected fields
    print(lower_fpro_same_category_products[selected_fields],
        selected_product[selected_fields])
   
    similarity_scores = euclidean_distances(
        lower_fpro_same_category_products[selected_fields],
        selected_product[selected_fields]
    )

    # Add similarity scores to the filtered DataFrame
    lower_fpro_same_category_products['similarity_score'] = similarity_scores

    # Exclude the original product from the search space
    lower_fpro_same_category_products['old_FPro'] = selected_f_FPro


    # Sort by similarity score in descending order
    lower_fpro_same_category_products = lower_fpro_same_category_products.sort_values(by='similarity_score', ascending=False)

    return lower_fpro_same_category_products

# Function to extract and return product recommendations with percentage changes
def extract_recommendations(similarity_scores, n, original_product):
    # Filter products with the same store as the original product
    same_store_products = similarity_scores
    print('M',same_store_products)

    # Select the top 'n' products with the highest similarity scores
    top_n_recommendations = same_store_products.head(n)

    # Calculate percentage changes for the specified fields
    fields_to_change = ['f_FPro', 'Total Fat', 'Sugars, total', 'Cholesterol',
                        'Fatty acids, total saturated', 'Fiber, total dietary', 'Protein', 'Carbohydrate']

    for field in fields_to_change:
        top_n_recommendations[f'change in {field}'] = ((top_n_recommendations[field] - original_product[field]) / original_product[field]) * 100

    # Select and return the desired columns
    selected_columns = ['name','f_FPro'] + [f'change in {field}' for field in fields_to_change]
    return top_n_recommendations[selected_columns]

# def get_product_image_url(product_name):
#     # Check if the image URL is already cached
#     if product_name in image_cache:
#         return image_cache[product_name]

#     try:
#         # Perform a Google search for the product name and get the first image result
#         search_results = search(product_name + " product", num=1, stop=1, pause=2)
        
#         # Extract the URL of the first image result
#         for url in search_results:
#             if url.endswith(('.jpg', '.png', '.jpeg', '.gif', '.bmp', '.webp')):
#                 # Cache the image URL
#                 image_cache[product_name] = url
#                 return url
#     except Exception as e:
#         print("Error:", e)
    
#     # Return None if no image URL is found
#     return None




# Function to load cart data from a JSON file
# Function to load cart data from a JSON file
def load_cart():
    try:
        with open("cart.json", "r") as file:
            data = file.read()
            if data:  # Check if the file is not empty
                return json.loads(data)
            else:
                return {}  # Return an empty cart if the file is empty
    except (FileNotFoundError, json.JSONDecodeError):
        return {}  # Return an empty cart if the file is not found or corrupted

# Function to save cart data to a JSON file
def save_cart(cart):
    with open("cart.json", "w") as file:
        json.dump(cart, file)

# Load cart data from the file
cart = load_cart()
# Load CSV data
# @st.cache  # This will cache the data for better performance
def load_data():
    data = pd.read_csv('GroceryDB_foods.csv')  # Replace 'GroceryDB_foods.csv' with your CSV file
    return data

products_data = load_data()

# Get unique categories from the 'store' column
categories = products_data['store'].unique()

# Streamlit app
st.title('Clean Cart')

# Search bar
search_query = st.text_input('Search for a product:')
selected_category = st.selectbox('Select a store:', ['All'] + list(categories))

# Filter products based on search query and selected category
filtered_data = products_data.copy()
filtered_data = filtered_data.dropna(subset=['f_FPro'])
if selected_category != 'All':
    filtered_data = filtered_data[filtered_data['store'] == selected_category]
if search_query:
    filtered_data = filtered_data.dropna(subset=['name']) 
    filtered_data = filtered_data[filtered_data['name'].str.contains(search_query, case=False)]

# Display random products as cards
st.write(f"Found {len(filtered_data)} results:")
col1, col2= st.columns(2)
col3, col4= st.columns(2)
cols=[col1, col2,col3,col4 ]


i=0
rows=[]
num_products_displayed = 4
i=0
for index, row in filtered_data.head(num_products_displayed).iterrows():
    product_name = row['name']
    f_FPro = round(row['f_FPro'], 2)
    add_to_cart_button = cols[i].button(f"Select",key=product_name)

    # If "Add to Cart" button is clicked, add the product to the cart
    if add_to_cart_button:
        selected_product = row  

    if add_to_cart_button:
        
        if product_name in cart:
            cart[product_name] += 1
        else:
            cart[product_name] = 1
        st.success(f"{product_name} added to cart!")
        print(cart)
    # Display product details
    cols[i].subheader(product_name)
    num_products_displayed -= 1
    i += 1
save_cart(cart)
# # Button to load more products
# if st.button("Load More"):
#     num_products_displayed += 4
#     for index, row in filtered_data.iloc[num_products_displayed:num_products_displayed+4].iterrows():
#         # Display new products
#         add_to_cart_button = cols[num_products_displayed % 4].button(f"Select My Product",key=row['name'])
#         cols[num_products_displayed % 4].subheader(row['name'])
#         num_products_displayed += 1
        

# else:
#     st.warning('No results found.')


try:
    st.title('Info On Selected Product')
    st.write(f"Detailed Information about {selected_product['name']}:")

    # Display important information in Markdown format
    # Display important information in Markdown format
    markdown_info = f"""
    **Protein:** {selected_product['Protein']:.2f} g  
    **Total Fat:** {selected_product['Total Fat']:.2f} g  
    **Carbohydrate:** {selected_product['Carbohydrate']:.2f} g  
    **Sugars:** {selected_product['Sugars, total']:.2f} g  
    **Fiber:** {selected_product['Fiber, total dietary']:.2f} g  
    **Fatty Acids (Saturated):** {selected_product['Fatty acids, total saturated']:.2f} g
    """
    st.markdown(markdown_info)
   
    st.write(f"Food Processing Score: {round(selected_product['f_FPro'],2)}")

    add_to_cart_button2=st.button(f"Add to cart",key=product_name+'xcx')
    cart = load_cart()
    if add_to_cart_button2:
        if product_name in cart:
            cart[product_name] += 1
        else:
            cart[product_name] = 1
        st.success(f"{product_name} added to cart!")
        print(cart)
    else:
        print('NULL')
        save_cart(cart)

except:
    st.title('Eat Healthy')
    # Save the cart data to the file

save_cart(cart)

if selected_product is not None:
    st.title('Eat Healthy')
    n = 5  # Replace with the desired number of recommendations
    original_ID = selected_product['original_ID']  # Replace with the desired 'original_ID'
    similarity_scores = calculate_similarity(filtered_data,original_ID)

    original_product = filtered_data[filtered_data['original_ID'] == original_ID].iloc[0]  # Replace with the original product's details
    recommendations_with_percent_changes = extract_recommendations(similarity_scores, n, original_product)

    col1, col2= st.columns(2)
    col3, col4= st.columns(2)
    cols=[col1, col2,col3,col4 ]


    i=0
    rows=[]
    num_products_displayed = 4
    i=0
    for index, row in recommendations_with_percent_changes.head(num_products_displayed).iterrows():
        product_name = row['name']
        f_FPro = round(row['f_FPro'], 2)
        f_FPro_diff = round(row["change in f_FPro"], 2)
        cols[i].metric(product_name, f_FPro,-f_FPro_diff)
        add_to_cart_button2 = cols[i].button(f"Add to cart",key=product_name+'xpcd')

        if add_to_cart_button2:
            
            if product_name in cart:
                cart[product_name] += 1
            else:
                cart[product_name] = 1
            save_cart(cart)
            st.success(f"{product_name} added to cart!")
            print(cart)
        num_products_displayed -= 1
        i += 1


st.title('Your Cart')
# When "Remove" button is clicked, remove the item from the cart
for product in list(cart.keys()):
    quantity = cart[product]
    remove_button = st.button(f"Remove {product} from Cart ({quantity} in cart)")
    if remove_button:
        if quantity > 1:
            cart[product] -= 1
        else:
            del cart[product]
        st.success(f"{product} removed from cart!")

# Save the cart data to the file
save_cart(cart)

# Calculate and display the average f_FPro for all products in the cart
if cart:
    total_f_FPro = 0
    total_products = 0
    for product, quantity in cart.items():
        # Assuming products_data is your original data source containing 'f_FPro' values
        # You need to replace it with your actual data source.
        f_FPro = filtered_data.loc[filtered_data['name'] == product, 'f_FPro'].values[0]
        total_f_FPro += f_FPro * quantity
        total_products += quantity
    avg_f_FPro = total_f_FPro / total_products

    st.metric("Average Processed Score Of Your Cart", round(avg_f_FPro,2), min(0,f_FPro-0.25))

else:
    st.warning("Your cart is empty.")

# Save the cart data to the file
save_cart(cart)


