import os
import tempfile
import requests
# from dotenv import load_dotenv
from PIL import Image
import streamlit as st
import openai
from io import BytesIO
from huggingface_hub import from_pretrained_keras
import numpy as np
import tensorflow as tf
from keras import backend as K


# Function to load models
@st.cache(allow_output_mutation=True)
def load_models():
    models = {}
    # # K.set_image_data_format('channels_last')
    # model = from_pretrained_keras('scottlai/model_v2_fake_image_detection')
    # model.compile(optimizer='adam', loss='binary_crossentropy')
    # models["scottlai/model_v2_fake_image_detection"] = model
    
    model = from_pretrained_keras("Pinchu05/DeepFake_Detection")
    model.compile(optimizer='adam', loss='binary_crossentropy')
    models["Pinchu05/DeepFake_Detection"] = model

    return models

# Streamlit app


content_loaded = False
if "openai_api_key" not in st.session_state:
    st.markdown("### Input your OpenAI API Key here")
    api_key = st.text_input(label="", placeholder="Enter your API Key here", key="API_input_text")

    if st.button("Load API Key") and api_key.strip() != "":
        st.session_state.openai_api_key = api_key.strip()
        st.success("API Key loaded successfully.")
        content_loaded = True
else:
    content_loaded = True

if content_loaded:

    openai.api_key = st.session_state.openai_api_key

    # Function to generate AI image
    def generate_image(input_image):
        # Convert the input image to JPEG format
        input_image = input_image.convert("RGB")
        input_image_file = BytesIO()
        input_image.save(input_image_file, format="PNG")

        # Generate the AI image
        response = openai.Image.create_variation(
            image=input_image_file.getvalue(),
            n=1,
            size="1024x1024"
        )
        image_url = response['data'][0]['url']

        # Download the image from the URL
        image_data = requests.get(image_url).content

        return Image.open(BytesIO(image_data))

    # Update the get_prediction function to accept the model's input shape
    def get_prediction(image, model_key, models):
        model = models[model_key]

        # if model_key == "scottlai/model_v2_fake_image_detection":
        #     input_shape = (224, 224)
        #     channels_first = True
        #     model_key = "MobileNetV2 Model"
        # elif model_key == "poojakabber1997/ResNetDallE2Fakes":
        if model_key == "Pinchu05/DeepFake_Detection":
            input_shape = (150, 150)
            channels_first = False
            model_key = "ResNet Model"

        image = Image.fromarray(image.astype('uint8'), 'RGB').resize(input_shape)
        image = np.array(image).astype(np.float32)
        image = image / 255

        if channels_first:
            image = np.transpose(image, (2, 0, 1))

        image = np.expand_dims(image, axis=0)

        if channels_first:
            image = np.transpose(image, (0, 2, 3, 1))

        prediction = model.predict(image)
        print(f"Raw prediction output for {model_key}: {prediction}") 
        real_prob = prediction[0][0]
        fake_prob = 1 - real_prob

        if real_prob > fake_prob:
            return model_key, "Real Human Face", real_prob
        else:
            return model_key, "AI Generated Face", fake_prob




    # Load both models at the beginning
    K.set_image_data_format('channels_last')
    models = load_models()


    # Add a new sidebar option for model selection
    model_choice = st.sidebar.radio(
        "Select a model:",
        (
            "AI Human Face Generator",
            # "Real vs AI Human Face Detection - MobileNetV2 Model",
            "Real vs AI Human Face Detection"
        ),
    )


    if model_choice == "AI Human Face Generator":
        st.title("AI Human Face Generator") 
        uploaded_file = st.file_uploader("Choose an image file (png or jpg)", type=["png", "jpg"])

        if uploaded_file is not None:
            st.header("Input Image")
            col1, col2 = st.columns(2)

            # Resize the input image to have equal width and height
            input_image = Image.open(uploaded_file)
            width, height = input_image.size
            new_size = min(width, height)
            input_image = input_image.resize((new_size, new_size))
            col1.image(input_image, use_column_width=True)

            if st.button("Generate AI Image"):
                uploaded_file.seek(0)  # Reset the file pointer to the beginning
                ai_image = generate_image(input_image)
                st.header("AI Generated Image")
                col2.image(ai_image, use_column_width=True)

        # Update the elif clause for Real vs AI Human Face Detection
    elif model_choice.startswith("Real vs AI Human Face Detection"):
        # Determine the selected model and its input shape
        # if model_choice.endswith("MobileNetV2 Model"):
        #     model_key = "scottlai/model_v2_fake_image_detection"
        #     input_shape = (1, 3, 224, 224)
        # else:
        if model_choice.endswith("ResNet Model"):
            model_key = "Pinchu05/DeepFake_Detection"
            input_shape = (1, 3, 180, 180)


        # # Use the selected model for predictions
        # model_fake_detection = models[model_key]
       

        st.title("Real vs AI Human Face Detection")
        st.write("This is a demo of a real vs AI human face detection app using a MobileNetV2 model trained on the Real vs AI face detection dataset.")
        st.write("Upload an image to see if it's a real human face or an AI generated one.")
        st.write("")
        uploaded_file = st.file_uploader("Choose an image...", type=["png", "jpg"])
        
        if uploaded_file is not None:
            uploaded_array = np.array(Image.open(uploaded_file).convert("RGB"))
            input_image = Image.open(uploaded_file)
            width, height = input_image.size
            new_size = min(width, height)
            input_image = input_image.resize((new_size, new_size))
            col1, col2 = st.columns([2, 1])
            col1.image(input_image, use_column_width=True)
            col2.write("Prediction Results:")
            model_key = "Pinchu05/DeepFake_Detection"
            model_name, prediction, real_prob = get_prediction(uploaded_array, model_key, models)

            # Get the prediction probabilities
            real_prob = real_prob
            fake_prob = 1-real_prob
            
            real_accuracy = f"This is a Real Human Face ({model_name})"
            real_probability = real_prob 
                
            fake_accuracy = f"This is an AI Generated Face ({model_name})"
            fake_probability = fake_prob
                    
            if real_probability > 0.73:
                col2.markdown(f"### {real_accuracy}")
                col2.write(f"Real Probability: {real_probability}")
            else:
                col2.markdown(f"### {fake_accuracy}")
                col2.write(f"Real Probability: {fake_probability}")
