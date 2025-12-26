"""
Script to reorganize detector rules into categorized folders
"""
import os
import shutil

# Define the categorization
CATEGORIES = {
    'access_control': [
        'AccessControlActorsDetector.py',
        'AccessControlDetector.py',
        'AccessControlFunctionDetector.py',
        'EOAContractCallerDetector.py',
    ],
    'security': [
        'SelfDestructDetector.py',
        'FrontRunningDetector.py',
        'CommitRevealDetector.py',
        'DustAttackDetector.py',
        'BalanceCheckDetector.py',
        'ArbitraryUserInputDetector.py',
    ],
    'validation': [
        'InputsValidationDetector.py',
        'OutputsValidationDetector.py',
        'EdgeCaseInputDetector.py',
    ],
    'code_quality': [
        'VisibilityStrictnessDetector.py',
        'CommentsCoherenceDetector.py',
        'StateVariableInitializationDetector.py',
        'StateVariableInitializerDetector.py',
        'UninitializedStateVariableDetector.py',
        'StaleValueDetector.py',
    ],
    'inheritance': [
        'InheritanceExpectationsDetector.py',
        'InheritanceVisibilityDetector.py',
        'MissingFuncInheritanceDetector.py',
    ],
    'defi': [
        'PriceManipulationDetector.py',
        'PriceRatioManipulationDetector.py',
    ],
}

def reorganize_rules(rules_dir='rules', dry_run=True):
    """
    Reorganize detector rules into categorized folders
    
    Args:
        rules_dir: Path to the rules directory
        dry_run: If True, only print what would be done without actually moving files
    """
    print(f"{'='*80}")
    print(f"Reorganizing detector rules into categories")
    print(f"Mode: {'DRY RUN (no files will be moved)' if dry_run else 'LIVE (files will be moved)'}")
    print(f"{'='*80}\n")
    
    moved_count = 0
    skipped_count = 0
    
    for category, files in CATEGORIES.items():
        category_path = os.path.join(rules_dir, category)
        
        print(f"\n[{category.upper().replace('_', ' ')}]")
        print(f"-" * 40)
        
        for filename in files:
            source = os.path.join(rules_dir, filename)
            destination = os.path.join(category_path, filename)
            
            if os.path.exists(source):
                if dry_run:
                    print(f"  Would move: {filename}")
                    print(f"    From: {source}")
                    print(f"    To:   {destination}")
                else:
                    try:
                        shutil.move(source, destination)
                        print(f"  ✓ Moved: {filename}")
                        moved_count += 1
                    except Exception as e:
                        print(f"  ✗ Error moving {filename}: {e}")
                        skipped_count += 1
            else:
                print(f"  ⚠ Not found: {filename}")
                skipped_count += 1
    
    # Handle uncategorized files
    print(f"\n[UNCATEGORIZED FILES]")
    print(f"-" * 40)
    
    all_categorized = []
    for files in CATEGORIES.values():
        all_categorized.extend(files)
    
    for filename in os.listdir(rules_dir):
        filepath = os.path.join(rules_dir, filename)
        
        # Skip directories, __pycache__, and __init__.py
        if os.path.isdir(filepath) or filename.startswith('__') or filename == '__init__.py':
            continue
        
        if filename.endswith('.py') and filename not in all_categorized:
            print(f"  ⚠ Uncategorized: {filename}")
            print(f"    (This file will remain in the root rules directory)")
    
    print(f"\n{'='*80}")
    if dry_run:
        print(f"DRY RUN COMPLETE - No files were actually moved")
        print(f"Run with dry_run=False to perform the actual reorganization")
    else:
        print(f"REORGANIZATION COMPLETE")
        print(f"  Files moved: {moved_count}")
        print(f"  Files skipped: {skipped_count}")
    print(f"{'='*80}\n")

if __name__ == "__main__":
    import sys
    
    # Check if user wants to actually move files
    if len(sys.argv) > 1 and sys.argv[1] == '--execute':
        reorganize_rules(dry_run=False)
    else:
        print("Running in DRY RUN mode...")
        print("To actually move files, run: python reorganize_rules.py --execute\n")
        reorganize_rules(dry_run=True)
