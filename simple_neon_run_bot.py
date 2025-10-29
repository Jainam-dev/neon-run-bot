"""
SIMPLE WhatsApp Chatbot for Neon Run (300 participants)
No barcode scanning needed - just simple registration numbers!
"""

from flask import Flask, request
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse
import json
import os
from datetime import datetime

app = Flask(__name__)

# ===== EDIT THESE 3 LINES WITH YOUR TWILIO CREDENTIALS =====
ACCOUNT_SID = 'AC112d4bff84d1103208a6612d05af2ae3'
AUTH_TOKEN = '1cf8cfe39f142fb8b6ccef1ee2e4db5c'
TWILIO_WHATSAPP_NUMBER = 'whatsapp:+14155238886'
# ===========================================================

client = Client(ACCOUNT_SID, AUTH_TOKEN)

# Simple storage
user_data = {}
registration_counter = 1

def get_next_registration_number():
    """Generate simple registration number: NR001, NR002, etc."""
    global registration_counter
    reg_num = f"NR{registration_counter:03d}"
    registration_counter += 1
    return reg_num

def save_registration(data):
    """Save registration to JSON file"""
    os.makedirs('registrations', exist_ok=True)
    
    # Save individual file
    filename = f"registrations/{data['reg_number']}.json"
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)
    
    # Add to master list
    master_file = 'registrations/all_registrations.json'
    all_regs = []
    if os.path.exists(master_file):
        with open(master_file, 'r') as f:
            all_regs = json.load(f)
    all_regs.append(data)
    with open(master_file, 'w') as f:
        json.dump(all_regs, f, indent=2)

@app.route('/webhook', methods=['POST'])
def webhook():
    """Handle incoming WhatsApp messages"""
    incoming_msg = request.values.get('Body', '').strip()
    from_number = request.values.get('From', '').replace('whatsapp:', '')
    
    resp = MessagingResponse()
    msg = resp.message()
    
    # Initialize user data if new
    if from_number not in user_data:
        user_data[from_number] = {'step': 0, 'data': {}}
    
    user = user_data[from_number]
    step = user['step']
    
    # Step 0: Welcome
    if step == 0:
        user['step'] = 1
        msg.body("🏃‍♂️ *Welcome to NEON RUN!* 🌟\n\nLet's register you!\n\nWhat's your *Name*?")
    
    # Step 1: Get Name
    elif step == 1:
        if len(incoming_msg) < 2:
            msg.body("Please enter a valid name (at least 2 characters)")
        else:
            user['data']['name'] = incoming_msg
            user['step'] = 2
            msg.body(f"Great, {incoming_msg}! 👍\n\nWhat's your *Age*?")
    
    # Step 2: Get Age
    elif step == 2:
        try:
            age = int(incoming_msg)
            if 16 <= age <= 45:
                user['data']['age'] = age
                user['step'] = 3
                msg.body("Perfect! ✅\n\nWhat's your *Phone Number*? (10 digits)")
            else:
                msg.body("Age must be between 16-45 years. Please enter your age:")
        except:
            msg.body("Please enter a valid age (numbers only)")
    
    # Step 3: Get Phone
    elif step == 3:
        phone = ''.join(filter(str.isdigit, incoming_msg))
        if len(phone) == 10:
            user['data']['phone'] = phone
            user['step'] = 4
            msg.body("Thanks! 📱\n\nSelect your *Gender*:\n1 = Male\n2 = Female\n3 = Other\n\nReply with just the number")
        else:
            msg.body("Please enter a valid 10-digit phone number")
    
    # Step 4: Get Gender
    elif step == 4:
        gender_map = {'1': 'Male', '2': 'Female', '3': 'Other'}
        if incoming_msg in gender_map:
            user['data']['gender'] = gender_map[incoming_msg]
            
            # Generate registration number
            reg_number = get_next_registration_number()
            user['data']['reg_number'] = reg_number
            user['data']['phone_number'] = from_number
            user['data']['registered_at'] = datetime.now().isoformat()
            
            # Save
            save_registration(user['data'])
            
            # Send confirmation
            confirmation = (
                f"✅ *REGISTRATION SUCCESSFUL!* ✅\n\n"
                f"🎉 Welcome, {user['data']['name']}!\n\n"
                f"📋 *Your Details:*\n"
                f"━━━━━━━━━━━━━━━\n"
                f"🆔 Registration: *{reg_number}*\n"
                f"👤 Name: {user['data']['name']}\n"
                f"🎂 Age: {user['data']['age']}\n"
                f"📞 Phone: {user['data']['phone']}\n"
                f"⚧ Gender: {user['data']['gender']}\n"
                f"━━━━━━━━━━━━━━━\n\n"
                f"💡 *IMPORTANT:* Remember your registration number: *{reg_number}*\n\n"
                f"Show this message at the event entrance!\n\n"
                f"See you at Neon Run! 🏃‍♂️💡"
            )
            msg.body(confirmation)
            
            user['step'] = 5  # Done
        else:
            msg.body("Please reply with 1, 2, or 3")
    
    # Step 5: Already registered
    elif step == 5:
        msg.body(f"You're already registered! 🎉\n\nYour number: *{user['data']['reg_number']}*\n\nSee you at the event!")
    
    return str(resp)

@app.route('/registrations')
def view_registrations():
    """Simple page to view all registrations"""
    master_file = 'registrations/all_registrations.json'
    
    if not os.path.exists(master_file):
        return "<h1>No registrations yet</h1>"
    
    with open(master_file, 'r') as f:
        all_regs = json.load(f)
    
    html = """
    <html>
    <head>
        <title>Neon Run Registrations</title>
        <style>
            body { font-family: Arial; margin: 20px; background: #f5f5f5; }
            h1 { color: #667eea; }
            table { width: 100%; background: white; border-collapse: collapse; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            th { background: #667eea; color: white; padding: 12px; text-align: left; }
            td { padding: 12px; border-bottom: 1px solid #eee; }
            tr:hover { background: #f8f9ff; }
            .count { background: #667eea; color: white; padding: 10px 20px; border-radius: 5px; display: inline-block; margin: 20px 0; }
            input { width: 300px; padding: 10px; margin: 10px 0; border: 2px solid #ddd; border-radius: 5px; font-size: 16px; }
        </style>
    </head>
    <body>
        <h1>🏃‍♂️ Neon Run Registrations</h1>
        <div class="count">Total Registrations: """ + str(len(all_regs)) + """</div>
        <input type="text" id="search" placeholder="🔍 Search by name or registration number..." onkeyup="searchTable()">
        <table id="regTable">
            <tr>
                <th>Reg #</th>
                <th>Name</th>
                <th>Age</th>
                <th>Phone</th>
                <th>Gender</th>
                <th>Registered At</th>
            </tr>
    """
    
    for reg in sorted(all_regs, key=lambda x: x['reg_number']):
        reg_time = datetime.fromisoformat(reg['registered_at']).strftime('%d %b, %I:%M %p')
        html += f"""
            <tr>
                <td><strong>{reg['reg_number']}</strong></td>
                <td>{reg['name']}</td>
                <td>{reg['age']}</td>
                <td>{reg['phone']}</td>
                <td>{reg['gender']}</td>
                <td>{reg_time}</td>
            </tr>
        """
    
    html += """
        </table>
        <script>
            function searchTable() {
                var input = document.getElementById("search");
                var filter = input.value.toUpperCase();
                var table = document.getElementById("regTable");
                var tr = table.getElementsByTagName("tr");
                
                for (var i = 1; i < tr.length; i++) {
                    var txtValue = tr[i].textContent || tr[i].innerText;
                    if (txtValue.toUpperCase().indexOf(filter) > -1) {
                        tr[i].style.display = "";
                    } else {
                        tr[i].style.display = "none";
                    }
                }
            }
        </script>
    </body>
    </html>
    """
    
    return html

@app.route('/search/<reg_number>')
def search_registration(reg_number):
    """Quick search for a registration number"""
    filename = f"registrations/{reg_number}.json"
    
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            data = json.load(f)
        return f"""
        <html>
        <head><title>Registration Found</title>
        <style>body{{font-family:Arial; padding:40px; text-align:center;}}
        .success{{color:green; font-size:24px;}}
        .info{{background:#f0f0f0; padding:20px; margin:20px auto; max-width:400px; border-radius:10px;}}</style>
        </head>
        <body>
            <h1 class="success">✅ Valid Registration!</h1>
            <div class="info">
                <h2>{data['name']}</h2>
                <p><strong>Reg #:</strong> {data['reg_number']}</p>
                <p><strong>Age:</strong> {data['age']}</p>
                <p><strong>Phone:</strong> {data['phone']}</p>
                <p><strong>Gender:</strong> {data['gender']}</p>
            </div>
        </body>
        </html>
        """
    else:
        return f"""
        <html>
        <head><title>Not Found</title>
        <style>body{{font-family:Arial; padding:40px; text-align:center;}}
        .error{{color:red; font-size:24px;}}</style>
        </head>
        <body>
            <h1 class="error">❌ Registration Not Found</h1>
            <p>Number: {reg_number}</p>
        </body>
        </html>
        """

if __name__ == '__main__':
    os.makedirs('registrations', exist_ok=True)
    
    # Load existing registrations to continue numbering
    master_file = 'registrations/all_registrations.json'
    if os.path.exists(master_file):
        with open(master_file, 'r') as f:
            existing = json.load(f)
            if existing:
                last_num = max([int(r['reg_number'].replace('NR', '')) for r in existing])
                registration_counter = last_num + 1
    
    print("=" * 50)
    print("🏃‍♂️ NEON RUN BOT - SIMPLE VERSION")
    print("=" * 50)
    
    # Get port from environment (for Render) or use 5000 for local
    port = int(os.environ.get('PORT', 5000))
    print(f"Bot starting on port {port}")
    print("=" * 50)
    
    app.run(host='0.0.0.0', port=port, debug=False)
