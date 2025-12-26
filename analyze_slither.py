"""
Script to analyze Slither detectors and extract useful patterns for our tool
"""
import os
import json

def analyze_slither_detectors(slither_dir='slither/detectors'):
    """
    Analyze Slither's detector structure and categorize them
    """
    if not os.path.exists(slither_dir):
        print(f"[ERROR] Slither directory not found: {slither_dir}")
        return
    
    print(f"{'='*80}")
    print(f"ANALYZING SLITHER DETECTORS")
    print(f"{'='*80}\n")
    
    detectors_info = {
        'categories': {},
        'total_detectors': 0,
        'detector_list': []
    }
    
    # Walk through the detectors directory
    for root, dirs, files in os.walk(slither_dir):
        # Skip __pycache__ and hidden directories
        dirs[:] = [d for d in dirs if not d.startswith('__') and not d.startswith('.')]
        
        for filename in files:
            if filename.endswith('.py') and not filename.startswith('__'):
                filepath = os.path.join(root, filename)
                relative_path = os.path.relpath(filepath, slither_dir)
                
                # Get category from directory structure
                path_parts = relative_path.split(os.sep)
                if len(path_parts) > 1:
                    category = path_parts[0]
                else:
                    category = 'root'
                
                # Read file to extract detector info
                detector_info = analyze_detector_file(filepath, filename)
                
                if detector_info:
                    detector_info['category'] = category
                    detector_info['relative_path'] = relative_path
                    
                    # Add to category
                    if category not in detectors_info['categories']:
                        detectors_info['categories'][category] = []
                    
                    detectors_info['categories'][category].append(detector_info)
                    detectors_info['detector_list'].append(detector_info)
                    detectors_info['total_detectors'] += 1
    
    # Print summary
    print(f"\n{'='*80}")
    print(f"SUMMARY")
    print(f"{'='*80}\n")
    print(f"Total detectors found: {detectors_info['total_detectors']}\n")
    
    print(f"Detectors by category:")
    for category, detectors in sorted(detectors_info['categories'].items()):
        print(f"  {category}: {len(detectors)} detectors")
    
    # Save to JSON for further analysis
    output_file = 'slither_detectors_analysis.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(detectors_info, f, indent=2)
    
    print(f"\n✓ Analysis saved to: {output_file}")
    
    # Print detailed list
    print(f"\n{'='*80}")
    print(f"DETAILED DETECTOR LIST")
    print(f"{'='*80}\n")
    
    for category in sorted(detectors_info['categories'].keys()):
        print(f"\n[{category.upper()}]")
        print(f"{'-'*40}")
        
        for detector in sorted(detectors_info['categories'][category], key=lambda x: x['name']):
            print(f"  • {detector['name']}")
            if detector.get('description'):
                print(f"    Description: {detector['description'][:100]}...")
            if detector.get('impact'):
                print(f"    Impact: {detector['impact']}")
            if detector.get('confidence'):
                print(f"    Confidence: {detector['confidence']}")
    
    return detectors_info

def analyze_detector_file(filepath, filename):
    """
    Analyze a single detector file to extract metadata
    """
    detector_info = {
        'name': filename[:-3],  # Remove .py
        'filename': filename,
        'description': None,
        'impact': None,
        'confidence': None,
        'has_check_function': False,
        'has_detect_function': False,
    }
    
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            
            # Look for common patterns
            if 'def _check(' in content or 'def check(' in content:
                detector_info['has_check_function'] = True
            
            if 'def _detect(' in content or 'def detect(' in content:
                detector_info['has_detect_function'] = True
            
            # Try to extract metadata from class definition
            lines = content.split('\n')
            for i, line in enumerate(lines):
                # Look for IMPACT
                if 'IMPACT =' in line:
                    detector_info['impact'] = line.split('=')[1].strip().strip('"\'')
                
                # Look for CONFIDENCE
                if 'CONFIDENCE =' in line:
                    detector_info['confidence'] = line.split('=')[1].strip().strip('"\'')
                
                # Look for HELP or description
                if 'HELP =' in line or 'DESCRIPTION =' in line:
                    desc = line.split('=')[1].strip().strip('"\'')
                    if len(desc) > 10:
                        detector_info['description'] = desc
                
                # Look for docstring
                if i < len(lines) - 1 and '"""' in line and not detector_info['description']:
                    # Try to get docstring
                    docstring_lines = []
                    for j in range(i, min(i + 10, len(lines))):
                        docstring_lines.append(lines[j])
                        if j > i and '"""' in lines[j]:
                            break
                    docstring = ' '.join(docstring_lines).replace('"""', '').strip()
                    if len(docstring) > 10:
                        detector_info['description'] = docstring[:200]
        
        return detector_info
    
    except Exception as e:
        print(f"  [WARNING] Error analyzing {filename}: {e}")
        return None

if __name__ == "__main__":
    analyze_slither_detectors()
