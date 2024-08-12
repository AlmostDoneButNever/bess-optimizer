import pandas as pd

# Sample DataFrame with dates
data = {
    'dates': pd.date_range(start='2024-01-01', end='2024-03-31')
}
df = pd.DataFrame(data)

# Extract dates and format them as strings
dates_list = df['dates'].dt.strftime('%Y-%m-%d').tolist()

# Create JavaScript array from the dates list
js_dates_array = ", ".join([f"'{date}'" for date in dates_list])

# HTML content with JavaScript to restrict date selection and calculate end date
html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Date Picker Example</title>
    <style>
        .container {{
            display: flex;
            align-items: center;
            margin-bottom: 20px;
        }}
        .datepicker {{
            height: 40px;
            margin-right: 10px;
        }}
        .duration-button {{
            height: 40px;
            margin-right: 10px;
            padding: 0 20px;
            cursor: pointer;
        }}
        .duration-button:hover {{
            background-color: #ddd;
        }}
        .label {{
            margin-right: 20px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1 class="label">Select a Start Date</h1>
        <input type="date" id="startDatePicker" class="datepicker">
        <button class="duration-button" data-duration="1day">1 Day</button>
        <button class="duration-button" data-duration="1week">1 Week</button>
        <button class="duration-button" data-duration="1month">1 Month</button>
        <button class="duration-button" data-duration="allafter">All After</button>
    </div>
    <h2 id="startDateText">Start Date: </h2>
    <h2 id="endDateText">End Date: </h2>
    <script>
        // List of allowed dates
        const allowedDates = [{js_dates_array}];

        // Function to check if a date is allowed
        function isDateAllowed(date) {{
            return allowedDates.includes(date);
        }}

        // Function to add days to a date
        function addDays(date, days) {{
            const result = new Date(date);
            result.setDate(result.getDate() + days);
            return result;
        }}

        // Function to add weeks to a date
        function addWeeks(date, weeks) {{
            return addDays(date, weeks * 7);
        }}

        // Function to add months to a date
        function addMonths(date, months) {{
            const result = new Date(date);
            result.setMonth(result.getMonth() + months);
            result.setDate(result.getDate() - 1);
            return result;
        }}

        // Function to get the nearest allowed date within the allowed range
        function getNearestAllowedDate(date) {{
            for (let i = 0; i < allowedDates.length; i++) {{
                if (new Date(allowedDates[i]) >= date) {{
                    return new Date(allowedDates[i]);
                }}
            }}
            return new Date(allowedDates[allowedDates.length - 1]);
        }}

        // Event listener to handle date and duration selection
        document.querySelectorAll('.duration-button').forEach(button => {{
            button.addEventListener('click', function() {{
                const startDateInput = document.getElementById('startDatePicker');
                if (startDateInput.value) {{
                    let startDate = new Date(startDateInput.value);
                    startDate.setHours(0, 0, 0, 0); // Set start time to 00:00:00
                    if (!isDateAllowed(startDateInput.value)) {{
                        alert('Selected date is not allowed. Please choose a valid date.');
                        startDateInput.value = '';
                        document.getElementById('startDateText').innerText = 'Start Date: ';
                        document.getElementById('endDateText').innerText = 'End Date: ';
                    }} else {{
                        let endDate;
                        switch (this.dataset.duration) {{
                            case '1day':
                                endDate = new Date(startDate); // Set end date to the same day
                                endDate.setHours(23, 30, 0, 0); // Set end time to 23:30:00
                                break;
                            case '1week':
                                endDate = addWeeks(startDate, 1);
                                endDate = getNearestAllowedDate(endDate);
                                endDate.setHours(23, 30, 0, 0); // Set end time to 23:30:00
                                break;
                            case '1month':
                                endDate = addMonths(startDate, 1);
                                endDate = getNearestAllowedDate(endDate);
                                endDate.setHours(23, 30, 0, 0); // Set end time to 23:30:00
                                break;
                            case 'allafter':
                                endDate = new Date(allowedDates[allowedDates.length - 1]);
                                endDate.setHours(23, 30, 0, 0); // Set end time to 23:30:00
                                break;
                        }}
                        document.getElementById('startDateText').innerText = 'Start Date: ' + startDate.toISOString().split('T')[0] + ' 00:00:00';
                        document.getElementById('endDateText').innerText = 'End Date: ' + endDate.toISOString().split('T')[0] + ' 23:30:00';
                        console.log('Start Date:', startDate.toISOString().split('T')[0] + ' 00:00:00');
                        console.log('End Date:', endDate.toISOString().split('T')[0] + ' 23:30:00');
                    }}
                }}
            }});
        }});

        // Set min and max date for the start date picker
        document.getElementById('startDatePicker').setAttribute('min', allowedDates[0]);
        document.getElementById('startDatePicker').setAttribute('max', allowedDates[allowedDates.length - 1]);

        // Set initial date to the earliest date in the list
        document.getElementById('startDatePicker').value = allowedDates[0];
    </script>
</body>
</html>
"""

# Write the HTML content to a file
with open("datepicker.html", "w") as file:
    file.write(html_content)

print("HTML file 'datepicker.html' has been created.")
