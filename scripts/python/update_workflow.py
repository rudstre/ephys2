#!/usr/bin/env python3
import os
import yaml
from datetime import datetime, timedelta

def generate_targeted_patterns(start_datetime, end_datetime, datetime_pattern, base_path):
    """
    Generate specific glob patterns using bracket notation to target the actual datetime range.
    Uses bracket patterns like [0-6] for efficient range matching.
    """
    patterns = set()
    
    # If range is within same day, create a targeted pattern
    if start_datetime.date() == end_datetime.date():
        # Same day - can be very specific
        pattern = datetime_pattern
        
        # Replace with specific values for parts that don't change
        pattern = pattern.replace('%Y', start_datetime.strftime('%Y'))
        pattern = pattern.replace('%y', start_datetime.strftime('%y'))
        pattern = pattern.replace('%m', start_datetime.strftime('%m'))
        pattern = pattern.replace('%d', start_datetime.strftime('%d'))
        
        # Create hour range pattern
        if start_datetime.hour == end_datetime.hour:
            pattern = pattern.replace('%H', start_datetime.strftime('%H'))
            # Same hour - create minute range
            if start_datetime.minute == end_datetime.minute:
                pattern = pattern.replace('%M', start_datetime.strftime('%M'))
                # Same minute - use wildcard for seconds (likely to vary)
                pattern = pattern.replace('%S', '??')
            else:
                # Different minutes - create range pattern
                if start_datetime.minute == 0 and end_datetime.minute == 59:
                    pattern = pattern.replace('%M', '??')
                else:
                    pattern = pattern.replace('%M', '??')  # Complex range, use wildcard
                pattern = pattern.replace('%S', '??')
        else:
            # Different hours - create hour range pattern
            start_h, end_h = start_datetime.hour, end_datetime.hour
            
            if start_h == 0 and end_h <= 9:
                pattern = pattern.replace('%H', f'0[0-{end_h}]')
            elif start_h == 0 and end_h == 23:
                pattern = pattern.replace('%H', '??')
            else:
                pattern = pattern.replace('%H', '??')  # Complex range
            
            pattern = pattern.replace('%M', '??')
            pattern = pattern.replace('%S', '??')
        
        # Ensure .rhd extension
        if not pattern.endswith('.rhd'):
            pattern += '.rhd'
            
        full_pattern = os.path.join(base_path, '**', pattern)
        patterns.add(full_pattern)
        
    else:
        # Multi-day range - need to handle different cases
        start_date = start_datetime.date()
        end_date = end_datetime.date()
        
        # If it's a simple case where we can use bracket notation efficiently
        if (end_date - start_date).days < 100:  # Reasonable range
            
            # Handle year range
            if start_datetime.year == end_datetime.year:
                year_pattern = start_datetime.strftime('%Y')
                year_pattern_2 = start_datetime.strftime('%y')
            else:
                # Multiple years - fall back to wildcards for now
                year_pattern = '????'
                year_pattern_2 = '??'
            
            # Handle month range
            if start_datetime.month == end_datetime.month:
                month_pattern = start_datetime.strftime('%m')
            elif start_datetime.year == end_datetime.year:
                start_m, end_m = start_datetime.month, end_datetime.month
                if start_m == 1 and end_m <= 9:
                    month_pattern = f'0[1-{end_m}]'
                elif start_m == 1 and end_m == 12:
                    month_pattern = '??'
                elif end_m - start_m == 1 and start_m <= 9 and end_m <= 9:
                    # Consecutive months in single digits
                    month_pattern = f'0[{start_m}-{end_m}]'
                elif end_m - start_m == 1 and start_m < 10 and end_m >= 10:
                    # Like March (03) to April (04) -> 0[34]
                    month_pattern = f'0[{start_m}{end_m%10}]'
                else:
                    month_pattern = '??'  # Complex range
            else:
                month_pattern = '??'
            
            # Handle day range - this gets complex, so let's be smart about it
            if start_datetime.month == end_datetime.month:
                # Same month - can be more specific about days
                start_d, end_d = start_datetime.day, end_datetime.day
                if start_d == 1 and end_d >= 28:
                    day_pattern = '??'  # Full month
                elif start_d == 1 and end_d <= 9:
                    day_pattern = f'0[1-{end_d}]'
                elif start_d <= 9 and end_d <= 9:
                    day_pattern = f'0[{start_d}-{end_d}]'
                else:
                    day_pattern = '??'  # Complex range
            elif abs((end_datetime.date() - start_datetime.date()).days) < 10:
                # Short range crossing months - create separate patterns
                # This will be handled by creating multiple patterns below
                day_pattern = '??'
            else:
                day_pattern = '??'
            
            # Handle time - use wildcards for multi-day unless end day has early cutoff
            if end_datetime.hour < 23:  # Any end time before end of day
                # Check if we need separate patterns for different date parts
                if start_datetime.month != end_datetime.month:
                    # Cross-month range - create separate patterns
                    
                    # Pattern 1: Start month from start_day to end of month
                    pattern1 = datetime_pattern
                    pattern1 = pattern1.replace('%Y', start_datetime.strftime('%Y'))
                    pattern1 = pattern1.replace('%y', start_datetime.strftime('%y'))
                    pattern1 = pattern1.replace('%m', start_datetime.strftime('%m'))
                    # Use wildcard for days in start month to avoid complex patterns
                    pattern1 = pattern1.replace('%d', '??')
                    pattern1 = pattern1.replace('%H', '??')
                    pattern1 = pattern1.replace('%M', '??')
                    pattern1 = pattern1.replace('%S', '??')
                    
                    if not pattern1.endswith('.rhd'):
                        pattern1 += '.rhd'
                    patterns.add(os.path.join(base_path, '**', pattern1))
                    
                    # Pattern 2: End month from start to end_day (excluding the final day if it has hour restriction)
                    if end_datetime.day > 1:
                        pattern2 = datetime_pattern
                        pattern2 = pattern2.replace('%Y', end_datetime.strftime('%Y'))
                        pattern2 = pattern2.replace('%y', end_datetime.strftime('%y'))
                        pattern2 = pattern2.replace('%m', end_datetime.strftime('%m'))
                        # Use specific day pattern for days before the end day
                        if end_datetime.day == 2:
                            pattern2 = pattern2.replace('%d', '01')  # Only day 1
                        elif end_datetime.day-1 <= 9:
                            pattern2 = pattern2.replace('%d', f'0[1-{end_datetime.day-1}]')
                        else:
                            pattern2 = pattern2.replace('%d', '??')
                        pattern2 = pattern2.replace('%H', '??')
                        pattern2 = pattern2.replace('%M', '??')
                        pattern2 = pattern2.replace('%S', '??')
                        
                        if not pattern2.endswith('.rhd'):
                            pattern2 += '.rhd'
                        patterns.add(os.path.join(base_path, '**', pattern2))
                    
                    # Pattern 3: Final day with hour restriction
                    pattern3 = datetime_pattern
                    pattern3 = pattern3.replace('%Y', end_datetime.strftime('%Y'))
                    pattern3 = pattern3.replace('%y', end_datetime.strftime('%y'))
                    pattern3 = pattern3.replace('%m', end_datetime.strftime('%m'))
                    pattern3 = pattern3.replace('%d', end_datetime.strftime('%d'))
                    
                    # Create hour range pattern for end day
                    if end_datetime.hour <= 9:
                        pattern3 = pattern3.replace('%H', f'0[0-{end_datetime.hour}]')
                    elif end_datetime.hour <= 19:
                        pattern3 = pattern3.replace('%H', f'[01][0-{end_datetime.hour%10}]')
                    else:
                        pattern3 = pattern3.replace('%H', f'[012][0-{end_datetime.hour%10}]')
                    
                    pattern3 = pattern3.replace('%M', '??')
                    pattern3 = pattern3.replace('%S', '??')
                    
                    if not pattern3.endswith('.rhd'):
                        pattern3 += '.rhd'
                    patterns.add(os.path.join(base_path, '**', pattern3))
                    
                else:
                    # Same month - create two patterns: normal days and final day
                    
                    # Pattern for all days except last
                    pattern1 = datetime_pattern
                    pattern1 = pattern1.replace('%Y', year_pattern)
                    pattern1 = pattern1.replace('%y', year_pattern_2)
                    pattern1 = pattern1.replace('%m', month_pattern)
                    if start_datetime.day <= 9 and end_datetime.day > start_datetime.day:
                        pattern1 = pattern1.replace('%d', f'0[{start_datetime.day}-{end_datetime.day-1}]')
                    else:
                        pattern1 = pattern1.replace('%d', day_pattern)
                    pattern1 = pattern1.replace('%H', '??')
                    pattern1 = pattern1.replace('%M', '??')
                    pattern1 = pattern1.replace('%S', '??')
                    
                    if not pattern1.endswith('.rhd'):
                        pattern1 += '.rhd'
                    patterns.add(os.path.join(base_path, '**', pattern1))
                    
                    # Pattern for last day with hour restriction
                    pattern2 = datetime_pattern
                    pattern2 = pattern2.replace('%Y', end_datetime.strftime('%Y'))
                    pattern2 = pattern2.replace('%y', end_datetime.strftime('%y'))
                    pattern2 = pattern2.replace('%m', end_datetime.strftime('%m'))
                    pattern2 = pattern2.replace('%d', end_datetime.strftime('%d'))
                    
                    # Create hour range pattern for end day
                    if end_datetime.hour <= 9:
                        pattern2 = pattern2.replace('%H', f'0[0-{end_datetime.hour}]')
                    elif end_datetime.hour <= 19:
                        pattern2 = pattern2.replace('%H', f'[01][0-{end_datetime.hour%10}]')
                    else:
                        pattern2 = pattern2.replace('%H', f'[012][0-{end_datetime.hour%10}]')
                    
                    pattern2 = pattern2.replace('%M', '??')
                    pattern2 = pattern2.replace('%S', '??')
                    
                    if not pattern2.endswith('.rhd'):
                        pattern2 += '.rhd'
                    patterns.add(os.path.join(base_path, '**', pattern2))
                    
            else:
                # End time is at end of day (hour 23) - regular multi-day pattern
                pattern = datetime_pattern
                pattern = pattern.replace('%Y', year_pattern)
                pattern = pattern.replace('%y', year_pattern_2)
                pattern = pattern.replace('%m', month_pattern)
                pattern = pattern.replace('%d', day_pattern)
                pattern = pattern.replace('%H', '??')
                pattern = pattern.replace('%M', '??')
                pattern = pattern.replace('%S', '??')
                
                if not pattern.endswith('.rhd'):
                    pattern += '.rhd'
                patterns.add(os.path.join(base_path, '**', pattern))
        
        else:
            # Very long range - fall back to wildcards
            pattern = datetime_pattern
            pattern = pattern.replace('%Y', '????')
            pattern = pattern.replace('%y', '??')
            pattern = pattern.replace('%m', '??')
            pattern = pattern.replace('%d', '??')
            pattern = pattern.replace('%H', '??')
            pattern = pattern.replace('%M', '??')
            pattern = pattern.replace('%S', '??')
            
            if not pattern.endswith('.rhd'):
                pattern += '.rhd'
            patterns.add(os.path.join(base_path, '**', pattern))
    
    return sorted(patterns)

def modify_workflow_yaml(workflow_file, base_path, start_datetime, end_datetime):
    try:
        with open(workflow_file, 'r') as f:
            workflow_data = yaml.safe_load(f)
    except Exception as e:
        print(f"Error reading workflow file: {e}")
        return False

    updated = False
    for section in workflow_data:
        if isinstance(section, dict) and 'input.rhd2000' in section:
            input_section = section['input.rhd2000']

            datetime_pattern = input_section.get('datetime_pattern')
            if not datetime_pattern:
                print("Error: datetime_pattern not found in input.rhd2000 section")
                return False

            glob_patterns = generate_targeted_patterns(start_datetime, end_datetime, datetime_pattern, base_path)
            
            # Create sessions with the glob patterns
            if len(glob_patterns) == 1:
                # Single pattern - create one session
                session = [{'path': glob_patterns[0], 'start': 0, 'stop': 'inf'}]
                input_section['sessions'] = [session]
                print(f"Successfully updated {workflow_file} with glob pattern: {glob_patterns[0]}")
            else:
                # Multiple patterns - create multiple session entries
                session = []
                for pattern in glob_patterns:
                    session.append({'path': pattern, 'start': 0, 'stop': 'inf'})
                input_section['sessions'] = [session]
                print(f"Successfully updated {workflow_file} with {len(glob_patterns)} glob patterns:")
                for pattern in glob_patterns:
                    print(f"  - {pattern}")
            
            updated = True
            break

    if not updated:
        print("Error: input.rhd2000 section not found")
        return False

    try:
        with open(workflow_file, 'w') as f:
            yaml.dump(workflow_data, f, default_flow_style=False)
        return True
    except Exception as e:
        print(f"Error writing workflow file: {e}")
        return False

def extract_base_path_from_sessions(workflow_data):
    """
    Extract the base path from existing sessions in the workflow file.
    """
    for section in workflow_data:
        if isinstance(section, dict) and 'input.rhd2000' in section:
            input_section = section['input.rhd2000']
            sessions = input_section.get('sessions', [])
            
            if sessions and len(sessions) > 0 and len(sessions[0]) > 0:
                # Get the first session path
                first_path = sessions[0][0].get('path', '')
                if first_path:
                    # Remove the glob pattern parts to get base path
                    # Split on /** to get the base directory
                    if '/**/' in first_path:
                        base_path = first_path.split('/**/')[0]
                        return base_path
                    else:
                        # Fallback: try to extract directory from full path
                        import os
                        return os.path.dirname(first_path)
    
    return None

def main():
    workflow_file = input("Enter path to workflow.yaml [default: workflow.yaml]: ").strip() or "workflow.yaml"
    workflow_file = workflow_file.strip("'\"")

    if not os.path.exists(workflow_file):
        print(f"Error: {workflow_file} not found")
        return

    # Read the workflow file to extract base path
    try:
        with open(workflow_file, 'r') as f:
            workflow_data = yaml.safe_load(f)
    except Exception as e:
        print(f"Error reading workflow file: {e}")
        return

    # Extract base path from existing sessions
    base_path = extract_base_path_from_sessions(workflow_data)
    if not base_path:
        print("Error: Could not extract base path from workflow file. Please ensure the workflow has existing sessions.")
        return
    
    print(f"Using base path from workflow: {base_path}")

    start_datetime_str = input("Enter start datetime (YYYY-MM-DD HH:MM:SS): ").strip()
    end_datetime_str = input("Enter end datetime (YYYY-MM-DD HH:MM:SS): ").strip()

    try:
        start_datetime = datetime.strptime(start_datetime_str, "%Y-%m-%d %H:%M:%S")
        end_datetime = datetime.strptime(end_datetime_str, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        print("Datetimes must be in YYYY-MM-DD HH:MM:SS format")
        return

    if start_datetime > end_datetime:
        print("Start datetime must be before end datetime")
        return

    modify_workflow_yaml(workflow_file, base_path, start_datetime, end_datetime)

if __name__ == "__main__":
    main()