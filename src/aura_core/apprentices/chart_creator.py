# src/aura_core/apprentices/chart_creator.py
import os
import matplotlib.pyplot as plt
import traceback

def run(payload):
    """
    Generates a chart image (.png) from data and saves it.
    """
    try:
        filename = payload.get("filename")
        chart_type = payload.get("type", "bar").lower()
        chart_data = payload.get("data") # e.g., [["Label1", 10], ["Label2", 20]]
        title = payload.get("title", "Chart")
        xlabel = payload.get("xlabel")
        ylabel = payload.get("ylabel")

        if not filename:
            return "Error: Missing 'filename' for the chart."
        if not chart_data or not isinstance(chart_data, list) or len(chart_data) < 1:
            return "Error: Invalid or empty 'data'. Must be a list of lists (e.g., [['Label', 10], ...])."
        if not filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            print(f"--- Chart Creator Warning: Filename '{filename}' has no image extension. Appending '.png'. ---")
            filename += '.png'

        print(f"--- Chart Creator: Generating '{chart_type}' chart titled '{title}' ---")

        # --- Data Preparation ---
        # Expects data like [["Item A", 25], ["Item B", 40], ["Item C", 30]]
        try:
            labels = [str(row[0]) for row in chart_data]
            values = [float(row[1]) for row in chart_data]
        except (ValueError, TypeError, IndexError) as e:
            return f"Error: Data format is invalid. Expected list of [label, value] pairs. Reason: {e}"

        plt.figure(figsize=(8, 4.5)) # Create a new figure with a good aspect ratio

        # --- Chart Type Logic ---
        if chart_type == "bar":
            plt.bar(labels, values)
            if xlabel: plt.xlabel(xlabel)
            if ylabel: plt.ylabel(ylabel)

        elif chart_type == "line":
            plt.plot(labels, values, marker='o') # Line chart with markers
            if xlabel: plt.xlabel(xlabel)
            if ylabel: plt.ylabel(ylabel)

        elif chart_type == "pie":
            if len(values) > 8: # Limit pie chart slices to avoid clutter
                 print(f"--- Chart Creator Warning: Pie chart has >8 slices. Consider a bar chart. ---")
            plt.pie(values, labels=labels, autopct='%1.1f%%', startangle=90)
            plt.axis('equal') # Equal aspect ratio ensures that pie is drawn as a circle.

        else:
            return f"Error: Unknown chart type '{chart_type}'. Supported types: bar, line, pie."

        plt.title(title)
        plt.tight_layout() # Adjusts plot to prevent labels from overlapping

        # --- Save the chart ---
        chart_dir = os.path.dirname(filename)
        if chart_dir and not os.path.exists(chart_dir):
            try:
                os.makedirs(chart_dir, exist_ok=True)
                print(f"--- Chart Creator: Created directory '{chart_dir}' ---")
            except Exception as e:
                return f"Error: Could not create directory '{chart_dir}'. Reason: {e}"

        plt.savefig(filename)
        plt.close() # Close the plot to free up memory

        # Return the path for the next step
        return filename 

    except Exception as e:
        print(traceback.format_exc())
        return f"Error creating chart '{filename}'. Reason: {e}"