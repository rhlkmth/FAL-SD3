# app.py
import streamlit as st
import fal_client
import os
from PIL import Image
import requests
from io import BytesIO

# Set page config
st.set_page_config(
    page_title="AI Image Generator",
    page_icon="🎨",
    layout="wide"
)

# Initialize session state for API key
if 'api_key' not in st.session_state:
    st.session_state.api_key = ''

# Title and description
st.title("🎨 AI Image Generator")
st.markdown("Generate images using Stable Diffusion v3.5")

def on_queue_update(update):
    if isinstance(update, fal_client.InProgress):
        for log in update.logs:
            status_placeholder.markdown(f"🔄 {log['message']}")

def generate_image(prompt, image_size, num_steps, guidance_scale, api_key):
    # Temporarily set the API key for this request
    os.environ['FAL_KEY'] = api_key
    
    result = fal_client.subscribe(
        "fal-ai/stable-diffusion-v35-large",
        arguments={
            "prompt": prompt,
            "negative_prompt": "",
            "image_size": image_size,
            "num_inference_steps": num_steps,
            "guidance_scale": guidance_scale,
            "num_images": 1,
            "enable_safety_checker": False,
            "output_format": "jpeg"
        },
        with_logs=True,
        on_queue_update=on_queue_update,
    )
    return result

def display_image(image_url):
    response = requests.get(image_url)
    img = Image.open(BytesIO(response.content))
    st.image(img, use_column_width=True)

# API Key input in sidebar
with st.sidebar:
    st.header("API Configuration")
    api_key = st.text_input(
        "Enter your FAL API Key",
        type="password",
        value=st.session_state.api_key,
        help="Enter your FAL API key. Get one at fal.ai"
    )
    
    if api_key:
        st.session_state.api_key = api_key
        st.success("API Key set! ✅")
    
    st.markdown("---")
    
    st.header("Generation Settings")
    
    image_size = st.selectbox(
        "Image Size",
        ["landscape_4_3", "landscape_16_9", "portrait_4_3", "portrait_16_9", "square", "square_hd"],
        index=0
    )
    
    num_steps = st.slider(
        "Number of Steps",
        min_value=20,
        max_value=50,
        value=28,
        help="More steps = better quality but slower generation"
    )
    
    guidance_scale = st.slider(
        "Guidance Scale",
        min_value=1.0,
        max_value=20.0,
        value=3.5,
        step=0.5,
        help="How closely to follow the prompt"
    )
    
    st.markdown("---")
    st.markdown("### Tips for better results:")
    st.markdown("""
    - Be specific about style and details
    - Mention lighting and atmosphere
    - Include artistic references
    - Specify camera angles/shots
    """)
    
    # Add a "Clear API Key" button
    if st.button("Clear API Key"):
        st.session_state.api_key = ""
        st.rerun()

# Main content area
prompt = st.text_area(
    "Enter your prompt",
    height=100,
    placeholder="Example: A dreamlike Japanese garden in perpetual twilight, bathed in bioluminescent cherry blossoms..."
)

generate_button = st.button("🎨 Generate Image", disabled=not st.session_state.api_key)

# Show API key requirement if not set
if not st.session_state.api_key:
    st.warning("⚠️ Please enter your FAL API key in the sidebar to generate images")

# Create a placeholder for status messages
status_placeholder = st.empty()

# Create a placeholder for the image
image_placeholder = st.empty()

if generate_button and prompt and st.session_state.api_key:
    try:
        status_placeholder.markdown("🚀 Starting generation...")
        result = generate_image(prompt, image_size, num_steps, guidance_scale, st.session_state.api_key)
        
        if result and "images" in result and len(result["images"]) > 0:
            image_url = result["images"][0]["url"]
            status_placeholder.markdown("✨ Generation complete!")
            display_image(image_url)
            
            # Create columns for download button and share button
            col1, col2 = st.columns([1, 4])
            with col1:
                st.markdown(f"[Download Image]({image_url})")
            
            # Show generation parameters
            with st.expander("Generation Details"):
                st.json({
                    "image_size": image_size,
                    "steps": num_steps,
                    "guidance_scale": guidance_scale,
                    "prompt": prompt
                })
        else:
            st.error("No image was generated. Please try again.")
            
    except Exception as e:
        st.error(f"Error generating image: {e}")
        if "unauthorized" in str(e).lower():
            st.error("Invalid API key. Please check your API key and try again.")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center'>
    <p>Get your API key at <a href='https://fal.ai' target='_blank'>fal.ai</a></p>
</div>
""", unsafe_allow_html=True)
