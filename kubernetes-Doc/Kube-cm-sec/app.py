# This file creates a simple Flask-based address book application for Kubernetes learning.
# Import the Flask framework and the helper tools needed for form handling.
from flask import Flask, request, redirect, url_for
# Import the Flask class and request, redirect, and url_for helpers for web routes.

import os
# Import the operating-system module so the app can read Kubernetes environment variables.

app = Flask(__name__)
# Create the Flask application object that will handle incoming HTTP requests.

contacts = [
    # Store a list of sample contacts inside memory for the address book demo.
    {"name": "Asha Kumar", "phone": "+91-9876543210", "email": "asha@example.com"},
    # Add a first sample contact to show the page on startup.
    {"name": "Ravi Sharma", "phone": "+91-9123456780", "email": "ravi@example.com"},
    # Add a second sample contact to show multiple entries.
]

app_title = os.getenv("APP_TITLE", "Address Book Kubernetes Demo")
# Read the title from the environment, with a default value if Kubernetes does not provide one.

app_secret = os.getenv("APP_SECRET", "demo-secret")
# Read the secret from the environment, with a default value for local testing.


def build_page():
    # Create the HTML page that shows the address book form and contact list.
    html = "<html><head><title>Address Book App</title></head><body>"
    # Start the HTML document and define the browser page title.
    html += "<h1>Address Book</h1>"
    # Add the page heading for the address-book view.
    html += f"<p>App title: {app_title}</p>"
    # Show the application title that comes from the environment.
    html += f"<p>Secret status: {app_secret}</p>"
    # Display the secret value as a simple demonstration for Kubernetes configuration.
    html += "<p>Add a new contact to the address book.</p>"
    # Explain that the app is used as a Kubernetes learning example.
    html += "<form method='post' action='/'>"
    # Create a form that submits new contacts to the home route.
    html += "<input name='name' placeholder='Name' required />"
    # Add a name input field to the form.
    html += "<input name='phone' placeholder='Phone' required />"
    # Add a phone input field to the form.
    html += "<input name='email' placeholder='Email' required />"
    # Add an email input field to the form.
    html += "<button type='submit'>Add Contact</button></form>"
    # Add a submit button so new contacts can be added.
    html += "<h2>Contacts</h2><ul>"
    # Create a section heading for the contact list.
    for contact in contacts:
        # Loop through every stored contact and render it as a list item.
        html += f"<li>{contact['name']} | {contact['phone']} | {contact['email']}</li>"
        # Add the contact details to the HTML page.
    html += "</ul></body></html>"
    # Close the list and HTML document structure.
    return html
    # Return the complete HTML page to the browser.


@app.route("/", methods=["GET", "POST"])
# Register the home route for both reading and submitting contacts.
def home():
    # Define the handler for the home page.
    if request.method == "POST":
        # Check whether the user submitted a new contact with a POST request.
        name = request.form.get("name", "").strip()
        # Read the submitted name and remove extra spaces.
        phone = request.form.get("phone", "").strip()
        # Read the submitted phone number and remove extra spaces.
        email = request.form.get("email", "").strip()
        # Read the submitted email address and remove extra spaces.
        if name and phone and email:
            # Only save the contact if all required values exist.
            contacts.append({"name": name, "phone": phone, "email": email})
            # Add the new contact to the in-memory list.
        return redirect(url_for("home"))
        # Redirect the browser back to the same page after the form submission.
    return build_page()
    # Return the rendered address book page for a GET request.


@app.route("/health")
# Register a simple health endpoint for Kubernetes probes.
def health():
    # Define the health-check route.
    return "OK"
    # Return a simple success message to show the container is healthy.


if __name__ == "__main__":
    # Run the Flask app when the file is executed directly.
    app.run(host="0.0.0.0", port=8080)
    # Start the server on port 8080 so the container can be reached by Kubernetes.
