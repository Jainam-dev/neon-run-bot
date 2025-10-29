"""
SIMPLE WhatsApp Chatbot for Neon Run (300 participants)
No barcode scanning needed - just simple registration numbers!
"""

from flask import Flask, request, send_file, make_response
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse
import json
import os
from datetime import datetime
import io
import csv

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
            msg.body("Thanks! 📱\n\nSelect your *Gender*:\n1 = Male\n2 = Female\n\nReply with just the number")
        else:
            msg.body("Please enter a valid 10-digit phone number")
    
    # Step 4: Get Gender
    elif step == 4:
        gender_map = {'1': 'Male', '2': 'Female'}
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
    
    # Calculate statistics
    total = len(all_regs)
    male_count = sum(1 for r in all_regs if r.get('gender') == 'Male')
    female_count = sum(1 for r in all_regs if r.get('gender') == 'Female')
    
    html = """
    <html>
    <head>
        <title>Neon Run Registrations</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            * { box-sizing: border-box; margin: 0; padding: 0; }
            body { 
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif; 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                padding: 20px;
                min-height: 100vh;
            }
            .container {
                max-width: 1400px;
                margin: 0 auto;
                background: white;
                border-radius: 16px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                overflow: hidden;
            }
            .header {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 30px;
                text-align: center;
            }
            .header h1 {
                font-size: 2.5em;
                margin-bottom: 10px;
            }
            .header p {
                font-size: 1.1em;
                opacity: 0.9;
            }
            .stats {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 15px;
                padding: 30px;
                background: #f8f9ff;
            }
            .stat-card {
                background: white;
                padding: 20px;
                border-radius: 12px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                text-align: center;
                transition: transform 0.2s;
            }
            .stat-card:hover {
                transform: translateY(-5px);
                box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            }
            .stat-number {
                font-size: 2.5em;
                font-weight: bold;
                color: #667eea;
                margin-bottom: 5px;
            }
            .stat-label {
                color: #666;
                font-size: 0.9em;
                text-transform: uppercase;
                letter-spacing: 1px;
            }
            .controls {
                padding: 30px;
                background: white;
                border-bottom: 2px solid #f0f0f0;
            }
            .export-section {
                display: flex;
                gap: 15px;
                margin-bottom: 20px;
                flex-wrap: wrap;
                align-items: center;
            }
            .export-btn {
                background: #10b981;
                color: white;
                padding: 14px 28px;
                border: none;
                border-radius: 10px;
                font-size: 16px;
                font-weight: 600;
                cursor: pointer;
                text-decoration: none;
                display: inline-flex;
                align-items: center;
                gap: 8px;
                transition: all 0.3s;
                box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
            }
            .export-btn:hover {
                background: #059669;
                transform: translateY(-2px);
                box-shadow: 0 6px 16px rgba(16, 185, 129, 0.4);
            }
            .export-btn.csv {
                background: #3b82f6;
                box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
            }
            .export-btn.csv:hover {
                background: #2563eb;
                box-shadow: 0 6px 16px rgba(59, 130, 246, 0.4);
            }
            .export-label {
                font-size: 14px;
                color: #666;
                margin-right: 10px;
                font-weight: 600;
            }
            input {
                flex: 1;
                min-width: 300px;
                padding: 14px 20px;
                border: 2px solid #e0e0e0;
                border-radius: 10px;
                font-size: 16px;
                transition: all 0.3s;
            }
            input:focus {
                outline: none;
                border-color: #667eea;
                box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
            }
            .table-container {
                padding: 0 30px 30px 30px;
                overflow-x: auto;
            }
            table {
                width: 100%;
                background: white;
                border-collapse: collapse;
                border-radius: 10px;
                overflow: hidden;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            }
            th {
                background: #667eea;
                color: white;
                padding: 16px;
                text-align: left;
                font-weight: 600;
                text-transform: uppercase;
                font-size: 0.85em;
                letter-spacing: 0.5px;
                position: sticky;
                top: 0;
                z-index: 10;
            }
            td {
                padding: 16px;
                border-bottom: 1px solid #f0f0f0;
            }
            tr:hover {
                background: #f8f9ff;
            }
            tr:last-child td {
                border-bottom: none;
            }
            .reg-number {
                font-weight: bold;
                color: #667eea;
                font-family: 'Courier New', monospace;
                font-size: 1.1em;
            }
            .no-results {
                text-align: center;
                padding: 40px;
                color: #999;
                font-size: 1.2em;
            }
            @media (max-width: 768px) {
                .header h1 { font-size: 1.8em; }
                .stats { grid-template-columns: repeat(2, 1fr); gap: 10px; padding: 20px; }
                .controls { padding: 20px; }
                .export-section { flex-direction: column; align-items: stretch; }
                .export-btn { width: 100%; justify-content: center; }
                input { min-width: 100%; }
                table { font-size: 0.9em; }
                th, td { padding: 12px 8px; }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🏃‍♂️ NEON RUN 2025</h1>
                <p>Registration Dashboard</p>
            </div>
            
            <div class="stats">
                <div class="stat-card">
                    <div class="stat-number">""" + str(total) + """</div>
                    <div class="stat-label">Total Registrations</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">""" + str(male_count) + """</div>
                    <div class="stat-label">Male</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">""" + str(female_count) + """</div>
                    <div class="stat-label">Female</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">""" + str(other_count) + """</div>
                    <div class="stat-label">Other</div>
                </div>
            </div>
            
            <div class="controls">
                <div class="export-section">
                    <span class="export-label">📥 EXPORT DATA:</span>
                    <a href="/export/excel" class="export-btn" download>
                        <span>📊</span> Download Excel
                    </a>
                    <a href="/export/csv" class="export-btn csv" download>
                        <span>📄</span> Download CSV
                    </a>
                </div>
                <input type="text" id="search" placeholder="🔍 Search by name, registration number, phone..." onkeyup="searchTable()">
            </div>
            
            <div class="table-container">
                <table id="regTable">
                    <thead>
                        <tr>
                            <th>Reg #</th>
                            <th>Name</th>
                            <th>Age</th>
                            <th>Phone</th>
                            <th>Gender</th>
                            <th>Registered At</th>
                        </tr>
                    </thead>
                    <tbody>
    """
    
    for reg in sorted(all_regs, key=lambda x: x['reg_number']):
        reg_time = datetime.fromisoformat(reg['registered_at']).strftime('%d %b, %I:%M %p')
        html += f"""
                        <tr>
                            <td><span class="reg-number">{reg['reg_number']}</span></td>
                            <td>{reg['name']}</td>
                            <td>{reg['age']}</td>
                            <td>{reg['phone']}</td>
                            <td>{reg['gender']}</td>
                            <td>{reg_time}</td>
                        </tr>
        """
    
    html += """
                    </tbody>
                </table>
            </div>
        </div>
        
        <script>
            function searchTable() {
                var input = document.getElementById("search");
                var filter = input.value.toUpperCase();
                var table = document.getElementById("regTable");
                var tr = table.getElementsByTagName("tr");
                var visibleCount = 0;
                
                for (var i = 1; i < tr.length; i++) {
                    var txtValue = tr[i].textContent || tr[i].innerText;
                    if (txtValue.toUpperCase().indexOf(filter) > -1) {
                        tr[i].style.display = "";
                        visibleCount++;
                    } else {
                        tr[i].style.display = "none";
                    }
                }
                
                // Show no results message if needed
                if (visibleCount === 0 && filter !== "") {
                    if (!document.getElementById("noResults")) {
                        var noResults = document.createElement("tr");
                        noResults.id = "noResults";
                        noResults.innerHTML = '<td colspan="6" class="no-results">No registrations found matching "' + input.value + '"</td>';
                        table.appendChild(noResults);
                    }
                } else {
                    var noResults = document.getElementById("noResults");
                    if (noResults) {
                        noResults.remove();
                    }
                }
            }
            
            // Auto-refresh every 30 seconds to show new registrations
            setTimeout(function() {
                location.reload();
            }, 30000);
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
        <head>
            <title>Registration Found</title>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    padding: 40px;
                    text-align: center;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                }}
                .card {{
                    background: white;
                    padding: 40px;
                    border-radius: 20px;
                    box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                    max-width: 500px;
                }}
                .success {{
                    color: #10b981;
                    font-size: 24px;
                    margin-bottom: 20px;
                }}
                .info {{
                    background: #f8f9ff;
                    padding: 30px;
                    margin: 20px 0;
                    border-radius: 15px;
                    border: 2px solid #667eea;
                }}
                h2 {{
                    color: #667eea;
                    margin-bottom: 20px;
                }}
                .detail {{
                    text-align: left;
                    margin: 15px 0;
                    padding: 10px;
                    border-bottom: 1px solid #e0e0e0;
                }}
                .detail:last-child {{
                    border-bottom: none;
                }}
                .label {{
                    font-weight: bold;
                    color: #666;
                }}
            </style>
        </head>
        <body>
            <div class="card">
                <h1 class="success">✅ Valid Registration!</h1>
                <div class="info">
                    <h2>{data['name']}</h2>
                    <div class="detail">
                        <span class="label">Registration #:</span> {data['reg_number']}
                    </div>
                    <div class="detail">
                        <span class="label">Age:</span> {data['age']}
                    </div>
                    <div class="detail">
                        <span class="label">Phone:</span> {data['phone']}
                    </div>
                    <div class="detail">
                        <span class="label">Gender:</span> {data['gender']}
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
    else:
        return f"""
        <html>
        <head>
            <title>Not Found</title>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    padding: 40px;
                    text-align: center;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                }}
                .card {{
                    background: white;
                    padding: 40px;
                    border-radius: 20px;
                    box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                    max-width: 500px;
                }}
                .error {{
                    color: #ef4444;
                    font-size: 24px;
                }}
            </style>
        </head>
        <body>
            <div class="card">
                <h1 class="error">❌ Registration Not Found</h1>
                <p>Number: <strong>{reg_number}</strong></p>
            </div>
        </body>
        </html>
        """

@app.route('/export/csv')
def export_csv():
    """Export registrations to CSV"""
    from flask import Response
    import io
    
    master_file = 'registrations/all_registrations.json'
    if not os.path.exists(master_file):
        return "No registrations yet", 404
    
    with open(master_file, 'r') as f:
        all_regs = json.load(f)
    
    # Create CSV in memory
    output = io.StringIO()
    output.write('Registration Number,Name,Age,Phone,Gender,Registration Date\n')
    
    for reg in sorted(all_regs, key=lambda x: x['reg_number']):
        reg_date = datetime.fromisoformat(reg['registered_at']).strftime('%Y-%m-%d %H:%M:%S')
        output.write(f"{reg['reg_number']},{reg['name']},{reg['age']},{reg['phone']},{reg['gender']},{reg_date}\n")
    
    # Create response
    response = Response(output.getvalue(), mimetype='text/csv')
    response.headers['Content-Disposition'] = f'attachment; filename=neon_run_registrations_{datetime.now().strftime("%Y%m%d")}.csv'
    
    return response

@app.route('/export/excel')
def export_excel():
    """Export registrations to Excel format (CSV that opens in Excel)"""
    from flask import Response
    import io
    
    master_file = 'registrations/all_registrations.json'
    if not os.path.exists(master_file):
        return "No registrations yet", 404
    
    with open(master_file, 'r') as f:
        all_regs = json.load(f)
    
    # Create CSV in memory with Excel-friendly formatting
    output = io.StringIO()
    # Add BOM for Excel to recognize UTF-8
    output.write('\ufeff')
    output.write('Registration Number,Name,Age,Phone,Gender,Registration Date\n')
    
    for reg in sorted(all_regs, key=lambda x: x['reg_number']):
        reg_date = datetime.fromisoformat(reg['registered_at']).strftime('%d-%b-%Y %I:%M %p')
        output.write(f"{reg['reg_number']},{reg['name']},{reg['age']},{reg['phone']},{reg['gender']},{reg_date}\n")
    
    # Create response
    response = Response(output.getvalue(), mimetype='text/csv')
    response.headers['Content-Disposition'] = f'attachment; filename=neon_run_registrations_{datetime.now().strftime("%Y%m%d")}.csv'
    
    return response


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
