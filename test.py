start_date = "2023-01-01T00:00"
end_date = "2023-12-31T23:59"

html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Time Picker</title>
</head>
<body>
    <h1>Time Picker with Predefined Start and End Date</h1>
    <label for="timePicker">Select a time:</label>
    <input type="datetime-local" id="timePicker" name="timePicker">
    
    <script>
        document.addEventListener("DOMContentLoaded", function() {{
            var timePicker = document.getElementById("timePicker");
            var startDate = new Date("{start_date}");
            var endDate = new Date("{end_date}");
            
            timePicker.min = startDate.toISOString().slice(0, 16);
            timePicker.max = endDate.toISOString().slice(0, 16);
        }});
    </script>
</body>
</html>
"""

with open("time_picker.html", "w") as file:
    file.write(html_content)

print("HTML file with time picker has been created: time_picker.html")
