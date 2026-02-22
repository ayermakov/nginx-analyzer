import re
import csv
import argparse
import os
import matplotlib.pyplot as plt
from collections import Counter
from datetime import datetime
from git import Repo

# Regex pattern for Nginx 'combined' log format
# Groups: ip, date, method, url, status, size
LOG_PATTERN = r'(?P<ip>\d+\.\d+\.\d+\.\d+) - - \[(?P<date>.*?)\] "(?P<method>\w+) (?P<url>.*?) HTTP/.*?" (?P<status>\d+) (?P<size>\d+)'

def parse_logs(file_path):
    """Reads the log file and extracts data using regex."""
    data = []
    if not os.path.exists(file_path):
        print(f"Error: File {file_path} not found.")
        return []
    
    with open(file_path, 'r') as f:
        for line in f:
            match = re.search(LOG_PATTERN, line)
            if match:
                entry = match.groupdict()
                # Convert Nginx date string to a Python datetime object for processing
                try:
                    # Example format: 22/Feb/2026:10:15:01
                    raw_date = entry['date'].split(' ')[0]
                    entry['dt_object'] = datetime.strptime(raw_date, '%d/%b/%Y:%H:%M:%S')
                except Exception:
                    entry['dt_object'] = None
                data.append(entry)
    return data

def generate_charts(data, chart_path):
    """Generates a combined visualization: Top IPs and Hourly Activity."""
    if not data:
        print("No data available to generate charts.")
        return

    # Prepare data for Top 10 IPs
    ips = [entry['ip'] for entry in data]
    ip_counts = Counter(ips).most_common(10)
    ips_labels, ip_vals = zip(*ip_counts)

    # Prepare data for Hourly Timeline
    hours = [entry['dt_object'].hour for entry in data if entry['dt_object']]
    hour_counts = Counter(hours)
    sorted_hours = range(24)
    sorted_counts = [hour_counts.get(h, 0) for h in sorted_hours]

    # Create plotting figure with two subplots
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))

    # Subplot 1: Horizontal Bar Chart for IPs
    ax1.barh(ips_labels, ip_vals, color='skyblue')
    ax1.set_title('Top 10 IP Addresses by Request Count')
    ax1.set_xlabel('Number of Requests')
    ax1.invert_yaxis() # Highest counts at the top

    # Subplot 2: Line Chart for Hourly Activity
    ax2.plot(sorted_hours, sorted_counts, marker='o', linestyle='-', color='orange')
    ax2.fill_between(sorted_hours, sorted_counts, alpha=0.2, color='orange')
    ax2.set_title('Server Activity by Hour (00:00 - 23:00)')
    ax2.set_xticks(sorted_hours)
    ax2.set_xlabel('Hour of Day')
    ax2.set_ylabel('Request Count')
    ax2.grid(True, linestyle='--', alpha=0.6)

    plt.tight_layout()
    plt.savefig(chart_path)
    print(f"Analytics chart saved to: {chart_path}")

def save_to_csv(data, output_path):
    """Saves the parsed log data into a CSV file."""
    if not data:
        return False
    
    # Remove the helper datetime object before saving to CSV
    clean_data = []
    for d in data:
        temp = d.copy()
        temp.pop('dt_object', None)
        clean_data.append(temp)

    keys = clean_data[0].keys()
    with open(output_path, 'w', newline='') as f:
        dict_writer = csv.DictWriter(f, fieldnames=keys)
        dict_writer.writeheader()
        dict_writer.writerows(clean_data)
    return True

def git_operations(repo_path, files, commit_msg):
    """Adds, commits, and pushes files to a Git repository."""
    try:
        repo = Repo(repo_path)
        repo.index.add(files)
        repo.index.commit(commit_msg)
        origin = repo.remote(name='origin')
        origin.push()
        print("Successfully pushed updates to Git repository.")
    except Exception as e:
        print(f"Git Error: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Nginx Log Analyzer with CSV, Charts, and Git integration.")
    parser.add_argument("--input", required=True, help="Path to the Nginx access.log file")
    parser.add_argument("--output", default="report.csv", help="Filename for the output CSV")
    parser.add_argument("--chart", default="analytics.png", help="Filename for the analytics chart")
    parser.add_argument("--git-repo", help="Local path to the Git repository")
    parser.add_argument("--push", action="store_true", help="Flag to push changes to Git")

    args = parser.parse_args()

    # Process logs
    parsed_data = parse_logs(args.input)
    
    if parsed_data:
        # Save CSV
        if save_to_csv(parsed_data, args.output):
            print(f"CSV report generated: {args.output}")
        
        # Generate Analytics
        generate_charts(parsed_data, args.chart)
        
        # Git Integration
        if args.push and args.git_repo:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
            git_operations(args.git_repo, [args.output, args.chart], f"Log Analysis Update: {timestamp}")