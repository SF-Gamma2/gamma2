import requests
import ftplib
import csv
import os
import json

def transfer_to_shutterstock(image_url, csv_data):
    debug_messages = {}
    image_filename = "image_to_shutterstock.jpg"  # Or determine from URL
    csv_filename = "metadata_for_shutterstock.csv"
    ftp_host = "ftp.shutterstock.com"  # Replace with Shutterstock's FTP host
    ftp_user = "etiennebertet@gmail.com"  # Replace with your Shutterstock FTP username
    ftp_password = "FFM1087"  # Replace with your Shutterstock FTP password

    # Retrieve Image
    try:
        debug_messages['image_url_retrieved'] = f"Attempting to retrieve image from: {image_url}"
        response = requests.get(image_url, stream=True)
        if response.status_code == 200:
            with open(image_filename, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            debug_messages['image_url_retrieved'] = "Image URL retrieved successfully."
        else:
            debug_messages['image_url_retrieved'] = f"Error retrieving image: Status code {response.status_code}"
            return debug_messages
    except Exception as e:
        debug_messages['image_url_retrieved'] = f"Error retrieving image: {str(e)}"
        return debug_messages

    # Retrieve Text Data (already received as argument)
    if csv_data:
        debug_messages['text_data_retrieved'] = "Text data retrieved successfully."
    else:
        debug_messages['text_data_retrieved'] = "Error: Text data is empty."
        return debug_messages

    # Export Text Data as CSV
    try:
        lines = csv_data.strip().split('\n')
        if len(lines) == 2:
            headers = [header.strip() for header in lines[0].split(',')]
            content = [content.strip() for content in lines[1].split(',')]
            if len(headers) == len(content):
                with open(csv_filename, 'w', newline='') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow(headers)
                    writer.writerow(content)
                debug_messages['text_data_exported'] = f"Text data exported to {csv_filename} successfully."
            else:
                debug_messages['text_data_exported'] = "Error: Number of headers does not match number of content fields."
                return debug_messages
        else:
            debug_messages['text_data_exported'] = "Error: Invalid CSV data format (expected two lines)."
            return debug_messages
    except Exception as e:
        debug_messages['text_data_exported'] = f"Error exporting text data to CSV: {str(e)}"
        return debug_messages

    # Establish FTP Connection
    ftp = None
    try:
        ftp = ftplib.FTP(ftp_host)
        ftp.login(ftp_user, ftp_password)
        debug_messages['ftp_connexion_established'] = f"FTP connection established successfully with {ftp_host}."
    except Exception as e:
        debug_messages['ftp_connexion_established'] = f"Error establishing FTP connection: {str(e)}"
        return debug_messages

    # Transfer Image
    image_transfer_success = False
    if ftp:
        try:
            with open(image_filename, 'rb') as file:
                ftp.storbinary(f'STOR {os.path.basename(image_filename)}', file)
            debug_messages['image_transferred'] = f"Image {os.path.basename(image_filename)} transferred successfully."
            image_transfer_success = True
        except Exception as e:
            debug_messages['image_transferred'] = f"Error transferring image: {str(e)}"

    # Transfer CSV File
    csv_transfer_success = False
    if ftp:
        try:
            with open(csv_filename, 'rb') as file:
                ftp.storbinary(f'STOR {os.path.basename(csv_filename)}', file)
            debug_messages['csv_file_transferred'] = f"CSV file {os.path.basename(csv_filename)} transferred successfully."
            csv_transfer_success = True
        except Exception as e:
            debug_messages['csv_file_transferred'] = f"Error transferring CSV file: {str(e)}"
        finally:
            ftp.quit()

    # Delete Local Files
    try:
        if image_transfer_success and os.path.exists(image_filename):
            os.remove(image_filename)
            debug_messages['image_deleted'] = f"Image {image_filename} deleted."
        else:
            debug_messages['image_deleted'] = f"Image {image_filename} not deleted (transfer failed or file not found)."
    except Exception as e:
        debug_messages['image_deleted'] = f"Error deleting image: {str(e)}"

    try:
        if csv_transfer_success and os.path.exists(csv_filename):
            os.remove(csv_filename)
            debug_messages['csv_file_deleted'] = f"CSV file {csv_filename} deleted."
        else:
            debug_messages['csv_file_deleted'] = f"CSV file {csv_filename} not deleted (transfer failed or file not found)."
    except Exception as e:
        debug_messages['csv_file_deleted'] = f"Error deleting CSV file: {str(e)}"

    return debug_messages

from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/', methods=['POST'])
def receive_data():
    data = request.get_json()
    image_url = data.get('imageUrl')
    csv_data = data.get('csvData')

    if image_url and csv_data:
        debug_messages = transfer_to_shutterstock(image_url, csv_data)
        return jsonify(debug_messages), 200
    else:
        return jsonify({"error": "Missing image URL or CSV data in the request."}), 400

if __name__ == '__main__':
    app.run(debug=True) # Use debug=False for production
