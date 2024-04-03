import requests

url = 'https://prodapi.phot.ai/external/api/v2/user_activity/remove-background'
headers = {
    'x-api-key': '65e83308ef3281fa7f218476_d66d2523ef9fc722c05f_apyhitools',
    'Content-Type': 'application/json'
}
data = {
    'file_name': '/home/jetxeberria/downloads/chaotic_bike.jpeg',  # Replace with the actual input file name as a string
    'input_image_link': 'file:///home/jetxeberria/downloads/chaotic_bike.jpeg'  # Replace with the URL of your input image
}


response = requests.post(url, headers=headers, json=data)

if response.status_code == 200:
    print(response.json())
else:
    print(f"Error: {response.status_code} - {response.text}")
